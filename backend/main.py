from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import json
import shutil
from pathlib import Path

from models import Group, Instance, SessionLocal, init_db, engine, Base
from docker_manager import DockerManager
from config_manager import ConfigManager
import contextlib

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_db()
    data_dir = os.getenv("OPENCLAW_DATA_DIR", "./data")
    os.makedirs(data_dir, exist_ok=True)
    
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
    if os.path.exists(static_dir):
        app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
        # Also mount other static files if they exist (favicons, etc.)
        for item in os.listdir(static_dir):
            if item != "assets" and item != "index.html" and os.path.isfile(os.path.join(static_dir, item)):
                app.mount(f"/{item}", StaticFiles(directory=static_dir, html=False), name=item)
    
    yield
    # Shutdown logic (if any)

app = FastAPI(title="OpenClaw Manager API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

docker_mgr = DockerManager()
config_mgr = ConfigManager()

def get_effective_image(image: str = None) -> str:
    """Resolve the Docker image name using the configured mirror registry.
    
    If a docker_mirror is configured in settings, it will be used as the
    registry prefix for the image. For example:
      mirror = 'https://docker.m.daocloud.io'
      image  = 'openclaw/openclaw:latest'
      result = 'docker.m.daocloud.io/openclaw/openclaw:latest'
    """
    settings = config_mgr.get_settings()
    default_image = settings.get("default_image", "openclaw/openclaw:latest")
    img = image or default_image
    
    # Get the configured mirror URL
    mirror = settings.get("docker_mirror", "") or settings.get("docker_registry", "")
    if not mirror:
        return img
    
    # Strip protocol prefix (https://, http://)
    mirror_host = mirror.replace("https://", "").replace("http://", "").rstrip("/")
    
    # Don't double-prefix if the image already starts with the mirror host
    if img.startswith(mirror_host):
        return img
    
    # Don't apply mirror to images that already have a custom registry prefix
    # (e.g., ghcr.io/xxx, registry.example.com/xxx)
    # Only apply to Docker Hub images (no dot in the first segment or library images)
    first_segment = img.split("/")[0]
    if "." in first_segment or ":" in first_segment:
        return img  # Already has a registry prefix
    
    return f"{mirror_host}/{img}"


class GroupCreate(BaseModel):
    name: str
    root_dir: str
    docker_network: str
    port_range_start: int
    port_range_end: int
    description: Optional[str] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    port_range_start: Optional[int] = None
    port_range_end: Optional[int] = None

class InstanceCreate(BaseModel):
    group_id: str
    name: str

class ConfigUpdate(BaseModel):
    env_vars: Optional[dict] = None
    openclaw_json: Optional[dict] = None


@app.get("/")
def root():
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist", "index.html")
    if os.path.exists(static_dir):
        return FileResponse(static_dir)
    return {"message": "OpenClaw Manager API", "version": "1.0.0", "note": "Frontend not built. Run 'npm run build' in frontend directory."}

@app.get("/api/groups")
def get_groups(db: Session = Depends(get_db)):
    groups = db.query(Group).all()
    return [{"id": g.id, "name": g.name, "root_dir": g.root_dir, 
             "docker_network": g.docker_network, "port_range_start": g.port_range_start,
             "port_range_end": g.port_range_end, "description": g.description,
             "created_at": g.created_at.isoformat() if g.created_at else None,
             "instance_count": len(g.instances)} for g in groups]

@app.post("/api/groups")
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    existing = db.query(Group).filter(Group.name == group.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Group name already exists")
    
    db_group = Group(
        name=group.name,
        root_dir=group.root_dir,
        docker_network=group.docker_network,
        port_range_start=group.port_range_start,
        port_range_end=group.port_range_end,
        description=group.description
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    try:
        docker_mgr.create_network(group.docker_network)
        os.makedirs(group.root_dir, exist_ok=True)
    except Exception as e:
        pass
    
    return {"id": db_group.id, "name": db_group.name, "message": "Group created successfully"}

@app.get("/api/groups/{group_id}")
def get_group(group_id: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    instances = db.query(Instance).filter(Instance.group_id == group_id).all()
    total_size = 0
    for inst in instances:
        inst_path = os.path.join(group.root_dir, inst.name)
        if os.path.exists(inst_path):
            total_size += sum(f.stat().st_size for f in Path(inst_path).rglob('*') if f.is_file())
    
    return {
        "id": group.id, "name": group.name, "root_dir": group.root_dir,
        "docker_network": group.docker_network, "port_range_start": group.port_range_start,
        "port_range_end": group.port_range_end, "description": group.description,
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "instances": [{"id": i.id, "name": i.name, "status": i.status, 
                        "host_port": i.host_port, "created_at": i.created_at.isoformat() if i.created_at else None} 
                       for i in instances],
        "storage_used": total_size
    }

@app.put("/api/groups/{group_id}")
def update_group(group_id: str, group: GroupUpdate, db: Session = Depends(get_db)):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if group.name:
        db_group.name = group.name
    if group.description is not None:
        db_group.description = group.description
    if group.port_range_start is not None:
        db_group.port_range_start = group.port_range_start
    if group.port_range_end is not None:
        db_group.port_range_end = group.port_range_end
    
    db.commit()
    return {"message": "Group updated successfully"}

@app.delete("/api/groups/{group_id}")
def delete_group(group_id: str, db: Session = Depends(get_db)):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    instances = db.query(Instance).filter(Instance.group_id == group_id).all()
    for inst in instances:
        try:
            docker_mgr.stop_container(inst.container_name)
            docker_mgr.remove_container(inst.container_name)
        except:
            pass
        
        inst_path = os.path.join(db_group.root_dir, inst.name)
        if os.path.exists(inst_path):
            import shutil
            shutil.rmtree(inst_path)
    
    try:
        docker_mgr.remove_network(db_group.docker_network)
    except:
        pass
    
    db.delete(db_group)
    db.commit()
    return {"message": "Group deleted successfully"}

@app.get("/api/instances")
def get_instances(group_id: Optional[str] = None, db: Session = Depends(get_db)):
    if group_id:
        instances = db.query(Instance).filter(Instance.group_id == group_id).all()
    else:
        instances = db.query(Instance).all()
    
    result = []
    for inst in instances:
        group = db.query(Group).filter(Group.id == inst.group_id).first()
        container_status = "unknown"
        try:
            info = docker_mgr.get_container_info(inst.container_name)
            container_status = info.get("state", "unknown")
        except:
            pass
        
        result.append({
            "id": inst.id, "group_id": inst.group_id, "group_name": group.name if group else "Unknown",
            "name": inst.name, "container_name": inst.container_name, "host_port": inst.host_port,
            "status": container_status, "created_at": inst.created_at.isoformat() if inst.created_at else None
        })
    return result

@app.post("/api/instances")
def create_instance(instance: InstanceCreate, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == instance.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    existing = db.query(Instance).filter(Instance.name == instance.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Instance name already exists")
    
    used_ports = [i.host_port for i in db.query(Instance).filter(Instance.group_id == instance.group_id).all()]
    assigned_port = None
    for port in range(group.port_range_start, group.port_range_end + 1):
        if port not in used_ports:
            assigned_port = port
            break
    
    if not assigned_port:
        raise HTTPException(status_code=400, detail="No available ports in group range")
    
    container_name = f"openclaw-{instance.name.lower().replace(' ', '-')}-{assigned_port}"
    
    db_instance = Instance(
        group_id=instance.group_id,
        name=instance.name,
        container_name=container_name,
        host_port=assigned_port,
        status="stopped"
    )
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    
    steps = []
    steps.append({"message": f"数据库记录已创建: {instance.name} (端口 {assigned_port})", "type": "output"})
    
    instance_dir = os.path.join(group.root_dir, instance.name)
    os.makedirs(os.path.join(instance_dir, ".openclaw"), exist_ok=True)
    os.makedirs(os.path.join(instance_dir, "data"), exist_ok=True)
    steps.append({"message": f"实例目录已创建: {instance_dir}", "type": "output"})
    
    config_mgr.create_default_config(instance_dir)
    steps.append({"message": "默认配置文件已生成", "type": "output"})
    
    return {"id": db_instance.id, "name": db_instance.name, "host_port": assigned_port, "message": "Instance created successfully", "steps": steps}

@app.get("/api/instances/{instance_id}")
def get_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    
    container_info = {}
    logs = ""
    try:
        container_info = docker_mgr.get_container_info(inst.container_name)
        logs = docker_mgr.get_container_logs(inst.container_name, tail=100)
    except:
        pass
    
    config_data = config_mgr.load_config(os.path.join(group.root_dir, inst.name))
    
    return {
        "id": inst.id, "group_id": inst.group_id, "group_name": group.name if group else "Unknown",
        "name": inst.name, "container_name": inst.container_name, "host_port": inst.host_port,
        "status": container_info.get("state", "stopped"), "created_at": inst.created_at.isoformat() if inst.created_at else None,
        "container_info": container_info, "logs": logs, "config": config_data
    }

@app.post("/api/instances/{instance_id}/start")
def start_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    
    openclaw_dir = os.path.join(group.root_dir, inst.name, ".openclaw")
    env_file_path = os.path.join(openclaw_dir, ".env")
    environment = docker_mgr.load_env_file(env_file_path)
    
    steps = []
    effective_image = get_effective_image()
    steps.append({"message": f"加载环境变量: {env_file_path}", "type": "output"})
    steps.append({"message": f"使用镜像: {effective_image}", "type": "output"})
    steps.append({"message": f"docker run --name {inst.container_name} --network {group.docker_network} -p {inst.host_port}:18987 ...", "type": "output"})
    try:
        docker_mgr.run_container(
            name=inst.container_name,
            network=group.docker_network,
            ports={"18987/tcp": inst.host_port},
            volumes={
                os.path.join(group.root_dir, inst.name, ".openclaw"): {"bind": "/root/.openclaw", "mode": "rw"},
                os.path.join(group.root_dir, inst.name, "data"): {"bind": "/root/data", "mode": "rw"}
            },
            environment=environment,
            image=effective_image
        )
        inst.status = "running"
        db.commit()
        steps.append({"message": f"容器 {inst.container_name} 启动成功", "type": "output"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start instance: {str(e)}")
    
    return {"message": "Instance started successfully", "steps": steps}

@app.post("/api/instances/{instance_id}/stop")
def stop_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    steps = [{"message": f"docker stop {inst.container_name}", "type": "output"}]
    try:
        docker_mgr.stop_container(inst.container_name)
        inst.status = "stopped"
        db.commit()
        steps.append({"message": f"容器 {inst.container_name} 已停止", "type": "output"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop instance: {str(e)}")
    
    return {"message": "Instance stopped successfully", "steps": steps}

@app.post("/api/instances/{instance_id}/restart")
def restart_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    steps = [{"message": f"docker restart {inst.container_name}", "type": "output"}]
    try:
        docker_mgr.restart_container(inst.container_name)
        steps.append({"message": f"容器 {inst.container_name} 已重启", "type": "output"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart instance: {str(e)}")
    
    return {"message": "Instance restarted successfully", "steps": steps}

@app.delete("/api/instances/{instance_id}")
def delete_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    
    steps = []
    try:
        steps.append({"message": f"docker stop {inst.container_name}", "type": "output"})
        docker_mgr.stop_container(inst.container_name)
        steps.append({"message": f"docker rm {inst.container_name}", "type": "output"})
        docker_mgr.remove_container(inst.container_name)
        steps.append({"message": "容器已移除", "type": "output"})
    except:
        steps.append({"message": "容器不存在或已被移除", "type": "output"})
    
    instance_dir = os.path.join(group.root_dir, inst.name)
    if os.path.exists(instance_dir):
        import shutil
        shutil.rmtree(instance_dir)
        steps.append({"message": f"实例目录已清理: {instance_dir}", "type": "output"})
    
    db.delete(inst)
    db.commit()
    steps.append({"message": "数据库记录已删除", "type": "output"})
    return {"message": "Instance deleted successfully", "steps": steps}

@app.get("/api/instances/{instance_id}/stats")
def get_instance_stats(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    try:
        stats = docker_mgr.get_container_stats(inst.container_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
    
    return stats

@app.post("/api/instances/{instance_id}/clone")
def clone_instance(instance_id: str, new_name: str = None, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    if not new_name:
        new_name = inst.name + "-clone"
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    
    used_ports = [i.host_port for i in db.query(Instance).filter(Instance.group_id == inst.group_id).all()]
    assigned_port = None
    for port in range(group.port_range_start, group.port_range_end + 1):
        if port not in used_ports:
            assigned_port = port
            break
    
    if not assigned_port:
        raise HTTPException(status_code=400, detail="No available ports in group range")
    
    container_name = f"openclaw-{new_name.lower().replace(' ', '-')}-{assigned_port}"
    
    db_instance = Instance(
        group_id=inst.group_id,
        name=new_name,
        container_name=container_name,
        host_port=assigned_port,
        status="stopped"
    )
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    
    source_dir = os.path.join(group.root_dir, inst.name)
    target_dir = os.path.join(group.root_dir, new_name)
    
    if os.path.exists(source_dir):
        import shutil
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
    
    return {"id": db_instance.id, "name": db_instance.name, "host_port": assigned_port, "message": "Instance cloned successfully"}

@app.get("/api/instances/{instance_id}/terminal")
def get_instance_terminal(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    
    container_info = docker_mgr.get_container_info(inst.container_name)
    if container_info.get("state") != "running":
        raise HTTPException(status_code=400, detail="Instance is not running")
    
    return {
        "terminal_url": f"http://localhost:{inst.host_port}/terminal",
        "gateway_url": f"http://localhost:{inst.host_port}"
    }

@app.post("/api/instances/batch/start")
def batch_start_instances(instance_ids: List[str], db: Session = Depends(get_db)):
    results = []
    for instance_id in instance_ids:
        inst = db.query(Instance).filter(Instance.id == instance_id).first()
        if inst:
            group = db.query(Group).filter(Group.id == inst.group_id).first()
            try:
                openclaw_dir = os.path.join(group.root_dir, inst.name, ".openclaw")
                env_file_path = os.path.join(openclaw_dir, ".env")
                environment = docker_mgr.load_env_file(env_file_path)
                
                docker_mgr.run_container(
                    name=inst.container_name,
                    network=group.docker_network,
                    ports={"18987/tcp": inst.host_port},
                    volumes={
                        os.path.join(group.root_dir, inst.name, ".openclaw"): {"bind": "/root/.openclaw", "mode": "rw"},
                        os.path.join(group.root_dir, inst.name, "data"): {"bind": "/root/data", "mode": "rw"}
                    },
                    environment=environment
                )
                inst.status = "running"
                db.commit()
                results.append({"id": instance_id, "status": "success"})
            except:
                results.append({"id": instance_id, "status": "failed"})
    return results

@app.post("/api/instances/batch/stop")
def batch_stop_instances(instance_ids: List[str], db: Session = Depends(get_db)):
    results = []
    for instance_id in instance_ids:
        inst = db.query(Instance).filter(Instance.id == instance_id).first()
        if inst:
            try:
                docker_mgr.stop_container(inst.container_name)
                inst.status = "stopped"
                db.commit()
                results.append({"id": instance_id, "status": "success"})
            except:
                results.append({"id": instance_id, "status": "failed"})
    return results

@app.post("/api/instances/batch/delete")
def batch_delete_instances(instance_ids: List[str], db: Session = Depends(get_db)):
    results = []
    for instance_id in instance_ids:
        inst = db.query(Instance).filter(Instance.id == instance_id).first()
        if inst:
            group = db.query(Group).filter(Group.id == inst.group_id).first()
            try:
                docker_mgr.stop_container(inst.container_name)
                docker_mgr.remove_container(inst.container_name)
            except:
                pass
            
            instance_dir = os.path.join(group.root_dir, inst.name)
            if os.path.exists(instance_dir):
                import shutil
                shutil.rmtree(instance_dir)
            
            db.delete(inst)
            results.append({"id": instance_id, "status": "success"})
    db.commit()
    return results

@app.get("/api/instances/{instance_id}/logs")
def get_instance_logs(instance_id: str, tail: int = 100, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    try:
        logs = docker_mgr.get_container_logs(inst.container_name, tail=tail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")
    
    return {"logs": logs}

@app.get("/api/system/stats")
def get_system_stats(db: Session = Depends(get_db)):
    total_instances = db.query(Instance).count()
    running_instances = 0
    try:
        containers = docker_mgr.list_containers()
        running_instances = sum(1 for c in containers if c.get("state") == "running")
    except:
        pass
    
    total_groups = db.query(Group).count()
    
    docker_stats = {}
    try:
        docker_stats = docker_mgr.get_system_info()
    except:
        pass
    
    return {
        "total_instances": total_instances,
        "running_instances": running_instances,
        "stopped_instances": total_instances - running_instances,
        "total_groups": total_groups,
        "docker": docker_stats
    }

@app.get("/api/config/templates")
def get_config_templates():
    return config_mgr.get_preset_templates()

@app.put("/api/config/templates")
def save_config_templates(templates: dict):
    config_mgr.save_templates(templates)
    return {"message": "Templates saved successfully"}

@app.get("/api/instances/{instance_id}/config")
def get_instance_config(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    config = config_mgr.load_config(os.path.join(group.root_dir, inst.name))
    return config

@app.put("/api/instances/{instance_id}/config")
def update_instance_config(instance_id: str, config: ConfigUpdate, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    instance_dir = os.path.join(group.root_dir, inst.name)
    
    if config.env_vars:
        config_mgr.update_env_file(instance_dir, config.env_vars)
    
    if config.openclaw_json:
        config_mgr.update_openclaw_json(instance_dir, config.openclaw_json)
    
    return {"message": "Configuration updated successfully"}

@app.get("/api/groups/{group_id}/config")
def get_group_config(group_id: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    config = config_mgr.load_group_config(group.root_dir)
    return config

@app.put("/api/groups/{group_id}/config")
def update_group_config(group_id: str, config: ConfigUpdate, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if config.env_vars:
        config_mgr.update_group_env_file(group.root_dir, config.env_vars)
    
    if config.openclaw_json:
        config_mgr.update_group_openclaw_json(group.root_dir, config.openclaw_json)
    
    return {"message": "Group configuration updated successfully"}

@app.get("/api/system/settings")
def get_settings():
    return config_mgr.get_settings()

@app.put("/api/system/settings")
def update_settings(settings: dict):
    config_mgr.update_settings(settings)
    return {"message": "Settings updated successfully"}

@app.post("/api/instances/{instance_id}/export")
def export_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    
    export_path = config_mgr.export_instance(instance_id, inst.name, group.root_dir)
    return {"export_path": export_path, "message": "Instance exported successfully"}

@app.post("/api/instances/import")
def import_instance(source_path: str, group_id: str, name: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    result = config_mgr.import_instance(source_path, group_id, name, group.root_dir)
    
    used_ports = [i.host_port for i in db.query(Instance).filter(Instance.group_id == group_id).all()]
    assigned_port = None
    for port in range(group.port_range_start, group.port_range_end + 1):
        if port not in used_ports:
            assigned_port = port
            break
    
    if not assigned_port:
        raise HTTPException(status_code=400, detail="No available ports in group range")
    
    container_name = f"openclaw-{name.lower().replace(' ', '-')}-{assigned_port}"
    
    db_instance = Instance(
        group_id=group_id,
        name=name,
        container_name=container_name,
        host_port=assigned_port,
        status="stopped"
    )
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    
    return {"id": db_instance.id, "name": name, "host_port": assigned_port, "message": "Instance imported successfully"}

@app.post("/api/instances/import-directory")
def import_instance_from_directory(source_dir: str, group_id: str, name: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    result = config_mgr.import_from_directory(source_dir, group_id, name, group.root_dir)
    
    used_ports = [i.host_port for i in db.query(Instance).filter(Instance.group_id == group_id).all()]
    assigned_port = None
    for port in range(group.port_range_start, group.port_range_end + 1):
        if port not in used_ports:
            assigned_port = port
            break
    
    if not assigned_port:
        raise HTTPException(status_code=400, detail="No available ports in group range")
    
    container_name = f"openclaw-{name.lower().replace(' ', '-')}-{assigned_port}"
    
    db_instance = Instance(
        group_id=group_id,
        name=name,
        container_name=container_name,
        host_port=assigned_port,
        status="stopped"
    )
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    
    return {"id": db_instance.id, "name": name, "host_port": assigned_port, "message": "Instance imported successfully"}

@app.post("/api/groups/{group_id}/export")
def export_group(group_id: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    export_path = config_mgr.export_group(group)
    return {"export_path": export_path, "message": "Group exported successfully"}

@app.post("/api/groups/import")
def import_group_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    upload_dir = os.path.join(config_mgr.data_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    result = config_mgr.import_group(file_path)
    
    os.remove(file_path)
    
    if "group_config" in result and "group_name" in result:
        group_config = result["group_config"]
        
        existing = db.query(Group).filter(Group.name == group_config.get("name")).first()
        if existing:
            return {"message": "群组已存在", "group_id": existing.id, "status": "exists"}
        
        db_group = Group(
            name=group_config.get("name"),
            root_dir=group_config.get("root_dir"),
            docker_network=group_config.get("docker_network"),
            port_range_start=group_config.get("port_range_start"),
            port_range_end=group_config.get("port_range_end"),
            description=group_config.get("description")
        )
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        
        try:
            docker_mgr.create_network(group_config.get("docker_network"))
            os.makedirs(group_config.get("root_dir"), exist_ok=True)
        except:
            pass
        
        return {
            "message": f"群组 '{group_config.get('name')}' 导入并创建成功",
            "group_id": db_group.id,
            "status": "created"
        }
    
    return result

@app.post("/api/instances/upload")
async def upload_instance_file(
    group_id: str,
    name: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    upload_dir = os.path.join(config_mgr.data_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    result = config_mgr.import_instance(file_path, group_id, name, group.root_dir)
    
    used_ports = [i.host_port for i in db.query(Instance).filter(Instance.group_id == group_id).all()]
    assigned_port = None
    for port in range(group.port_range_start, group.port_range_end + 1):
        if port not in used_ports:
            assigned_port = port
            break
    
    if not assigned_port:
        raise HTTPException(status_code=400, detail="No available ports in group range")
    
    container_name = f"openclaw-{name.lower().replace(' ', '-')}-{assigned_port}"
    
    db_instance = Instance(
        group_id=group_id,
        name=name,
        container_name=container_name,
        host_port=assigned_port,
        status="stopped"
    )
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    
    os.remove(file_path)
    
    return {"id": db_instance.id, "name": name, "host_port": assigned_port, "message": "Instance uploaded and imported successfully"}

@app.post("/api/groups/upload")
async def upload_group_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    upload_dir = os.path.join(config_mgr.data_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    result = config_mgr.import_group(file_path)
    
    os.remove(file_path)
    
    return result

@app.get("/api/system/networks")
def get_docker_networks():
    try:
        networks = docker_mgr.list_networks()
        return {"networks": networks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get networks: {str(e)}")

@app.get("/api/system/images")
def get_docker_images():
    try:
        images = docker_mgr.list_images()
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get images: {str(e)}")

@app.get("/api/download")
def download_file(path: str):
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(path, filename=os.path.basename(path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.post("/api/system/pull-image")
def pull_image(image: str = "openclaw/openclaw:latest"):
    effective_image = get_effective_image(image)
    try:
        success = docker_mgr.pull_image(effective_image)
        if success:
            return {"message": "Image pulled successfully", "image": effective_image,
                    "steps": [{"message": f"docker pull {effective_image}", "type": "output"},
                              {"message": "镜像拉取成功", "type": "output"}]}
        else:
            raise HTTPException(status_code=500, detail="Failed to pull image")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pull image: {str(e)}")

@app.get("/api/system/pull-image-stream")
def pull_image_stream(image: str = "openclaw/openclaw:latest"):
    """SSE endpoint that streams real-time docker pull progress."""
    effective_image = get_effective_image(image)
    
    def event_generator():
        has_error = False
        for line in docker_mgr.pull_image_stream(effective_image):
            if line.startswith("ERROR:"):
                has_error = True
                yield f"data: {json.dumps({'type': 'error', 'message': line})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'output', 'message': line})}\n\n"
        
        if has_error:
            yield f"data: {json.dumps({'type': 'done', 'success': False})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'done', 'success': True})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    })

@app.get("/api/system/env-check")
def check_environment():
    import platform
    import subprocess
    import shutil
    
    result = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": platform.python_version(),
        "docker_available": docker_mgr.client is not None,
        "docker_version": None,
        "docker_socket_exists": os.path.exists("/var/run/docker.sock") or os.path.exists(os.path.expanduser("~/.docker/run/docker.sock")) or (platform.system() == "Windows"),
        "has_docker": shutil.which("docker") is not None,
        "data_dir_writable": os.access("./data", os.W_OK) if os.path.exists("./data") else True,
        "architecture": platform.machine()
    }
    
    if docker_mgr.client:
        try:
            info = docker_mgr.client.info()
            result["docker_version"] = info.get("ServerVersion")
        except:
            pass
    
    return result

@app.post("/api/instances/start-all")
def start_all_instances(db: Session = Depends(get_db)):
    instances = db.query(Instance).all()
    results = []
    for inst in instances:
        if inst.status == "running":
            results.append({"id": inst.id, "name": inst.name, "status": "already_running"})
            continue
            
        group = db.query(Group).filter(Group.id == inst.group_id).first()
        if not group:
            results.append({"id": inst.id, "name": inst.name, "status": "group_not_found"})
            continue
        
        try:
            openclaw_dir = os.path.join(group.root_dir, inst.name, ".openclaw")
            env_file_path = os.path.join(openclaw_dir, ".env")
            environment = docker_mgr.load_env_file(env_file_path)
            
            docker_mgr.run_container(
                name=inst.container_name,
                network=group.docker_network,
                ports={"18987/tcp": inst.host_port},
                volumes={
                    os.path.join(group.root_dir, inst.name, ".openclaw"): {"bind": "/root/.openclaw", "mode": "rw"},
                    os.path.join(group.root_dir, inst.name, "data"): {"bind": "/root/data", "mode": "rw"}
                },
                environment=environment
            )
            inst.status = "running"
            db.commit()
            results.append({"id": inst.id, "name": inst.name, "status": "success"})
        except Exception as e:
            results.append({"id": inst.id, "name": inst.name, "status": "failed", "error": str(e)})
    
    success_count = sum(1 for r in results if r.get("status") == "success")
    return {"message": f"启动完成: {success_count}/{len(results)}", "results": results}

@app.post("/api/instances/stop-all")
def stop_all_instances(db: Session = Depends(get_db)):
    instances = db.query(Instance).all()
    results = []
    for inst in instances:
        if inst.status != "running":
            results.append({"id": inst.id, "name": inst.name, "status": "already_stopped"})
            continue
            
        try:
            docker_mgr.stop_container(inst.container_name)
            inst.status = "stopped"
            db.commit()
            results.append({"id": inst.id, "name": inst.name, "status": "success"})
        except Exception as e:
            results.append({"id": inst.id, "name": inst.name, "status": "failed", "error": str(e)})
    
    success_count = sum(1 for r in results if r.get("status") == "success")
    return {"message": f"停止完成: {success_count}/{len(results)}", "results": results}

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API route not found")
        
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
    index_path = os.path.join(static_dir, "index.html")
    
    # Check if the path is an actual file in dist (like favicon.ico)
    file_path = os.path.join(static_dir, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
        
    # Otherwise, fall back to index.html for SPA routing
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
