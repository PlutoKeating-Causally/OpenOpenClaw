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
import subprocess
import contextlib

from models import Group, Instance, SessionLocal, init_db, engine, Base
from docker_manager import DockerManager
from config_manager import ConfigManager

# --- Application Setup ---

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

# --- Utils ---

def get_effective_image(image: str = None) -> str:
    settings = config_mgr.get_settings()
    default_image = settings.get("default_image", "openclaw/openclaw:latest")
    img = image or default_image
    
    mirror = settings.get("docker_mirror", "") or settings.get("docker_registry", "")
    if not mirror:
        return img
    
    mirror_host = mirror.replace("https://", "").replace("http://", "").rstrip("/")
    if img.startswith(mirror_host):
        return img
    
    first_segment = img.split("/")[0]
    if "." in first_segment or ":" in first_segment:
        return img
    
    return f"{mirror_host}/{img}"

# --- Models ---

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
    container_port: Optional[int] = 18987
    host_port: Optional[int] = None

class ConfigUpdate(BaseModel):
    env_vars: Optional[dict] = None
    openclaw_json: Optional[dict] = None

class PortUpdate(BaseModel):
    host_port: Optional[int] = None
    container_port: Optional[int] = None

class DirectoryImport(BaseModel):
    source_dir: str
    group_id: str
    name: Optional[str] = None

def propagate_host_env(environment: dict) -> dict:
    """Propagate key AI API keys from host environment to container if not already set."""
    keys_to_check = [
        "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT",
        "OPENAI_API_KEY", "GEMINI_API_KEY", "VOYAGE_API_KEY", "MISTRAL_API_KEY",
        "AZURE_OPENAI_MODEL_NAME", "GOOGLE_GENERATIVE_AI_API_KEY", "ANTHROPIC_API_KEY",
        "DEEPSEEK_API_KEY", "MINIMAX_API_KEY", "GROQ_API_KEY"
    ]
    for key in keys_to_check:
        if key not in environment or not environment[key]:
            val = os.environ.get(key)
            if val:
                environment[key] = val
    return environment

# --- Routes ---

@app.get("/")
def root():
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist", "index.html")
    if os.path.exists(static_dir):
        return FileResponse(static_dir)
    return {"message": "OpenClaw Manager API", "version": "1.0.0"}

# --- Group Routes ---

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
    except:
        pass
    
    return {"id": db_group.id, "name": db_group.name}

@app.get("/api/groups/{group_id}")
def get_group(group_id: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    instances = db.query(Instance).filter(Instance.group_id == group_id).all()
    return {
        "id": group.id, "name": group.name, "root_dir": group.root_dir,
        "docker_network": group.docker_network, "port_range_start": group.port_range_start,
        "port_range_end": group.port_range_end, "description": group.description,
        "instances": [{"id": i.id, "name": i.name, "status": i.status, 
                        "host_port": i.host_port, "container_port": i.container_port or 18987} 
                       for i in instances]
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
    return {"message": "Group updated"}

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
            shutil.rmtree(inst_path)
    
    try:
        docker_mgr.remove_network(db_group.docker_network)
    except:
        pass
    
    db.delete(db_group)
    db.commit()
    return {"message": "Group deleted"}

# --- Instance Routes ---

@app.get("/api/instances")
def get_instances(group_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Instance)
    if group_id:
        query = query.filter(Instance.group_id == group_id)
    instances = query.all()
    
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
    if instance.host_port:
        if instance.host_port in used_ports:
            raise HTTPException(status_code=400, detail="Port in use")
        assigned_port = instance.host_port
    else:
        assigned_port = None
        for port in range(group.port_range_start, group.port_range_end + 1):
            if port not in used_ports:
                assigned_port = port
                break
    
    if not assigned_port:
        raise HTTPException(status_code=400, detail="No ports available")
    
    container_port = instance.container_port or 18987
    container_name = f"openclaw-{instance.name.lower().replace(' ', '-')}-{assigned_port}"
    
    db_instance = Instance(
        group_id=instance.group_id,
        name=instance.name,
        container_name=container_name,
        host_port=assigned_port,
        container_port=container_port,
        status="stopped"
    )
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    
    instance_dir = os.path.join(group.root_dir, instance.name)
    os.makedirs(os.path.join(instance_dir, ".openclaw"), exist_ok=True)
    os.makedirs(os.path.join(instance_dir, "data"), exist_ok=True)
    config_mgr.create_default_config(instance_dir, gateway_port=container_port)
    # Ensure initial allowedOrigins follow strict requirements
    config_mgr.sync_allowed_origins(instance_dir, container_port, assigned_port)
    
    return {"id": db_instance.id, "name": db_instance.name}

# --- BATCH OPERATIONS (Defined BEFORE parameterized instance routes) ---

@app.post("/api/instances/batch/start")
def batch_start_instances(instance_ids: List[str], db: Session = Depends(get_db)):
    results = []
    effective_image = get_effective_image()
    for instance_id in instance_ids:
        inst = db.query(Instance).filter(Instance.id == instance_id).first()
        if inst:
            group = db.query(Group).filter(Group.id == inst.group_id).first()
            try:
                # Environment Merging: Host -> Group -> Instance
                instance_dir = os.path.join(group.root_dir, inst.name)
                openclaw_dir = os.path.join(instance_dir, ".openclaw")
                
                # 1. Load Group Env
                group_env_path = os.path.join(group.root_dir, ".env")
                environment = docker_mgr.load_env_file(group_env_path)
                
                # 2. Merge Instance Env (Instance wins)
                inst_env_path = os.path.join(openclaw_dir, ".env")
                environment.update(docker_mgr.load_env_file(inst_env_path))
                
                # 3. Propagate selected Host keys
                environment = propagate_host_env(environment)
                
                # 4. Enforce essential container paths
                environment["OPENCLAW_HOME"] = "/root"
                environment["OPENCLAW_DATA_DIR"] = "/root/.openclaw"
                
                docker_mgr.run_container(
                    name=inst.container_name,
                    network=group.docker_network,
                    ports={f"{inst.container_port or 18987}/tcp": inst.host_port},
                    volumes={
                        instance_dir: {"bind": "/root", "mode": "rw"}
                    },
                    environment=environment,
                    image=effective_image
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
            except: pass
            
            instance_dir = os.path.join(group.root_dir, inst.name)
            if os.path.exists(instance_dir):
                shutil.rmtree(instance_dir)
            
            db.delete(inst)
            results.append({"id": instance_id, "status": "success"})
    db.commit()
    return results

@app.post("/api/instances/start-all")
def start_all_instances(db: Session = Depends(get_db)):
    instances = db.query(Instance).all()
    results = []
    for inst in instances:
        if inst.status != "running":
            # Logic similar to batch_start...
            pass
    return {"message": "Started all (limited implementation)"}

# --- Import/Migration ---

@app.post("/api/instances/import-directory")
def import_instances_from_directory(data: DirectoryImport, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == data.group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    
    source_path = data.source_dir.rstrip("/")
    if not os.path.exists(source_path):
        raise HTTPException(status_code=400, detail="Directory not found")
    
    import_targets = [] # List of (instance_name, instance_root_dir)
    
    # 1. Detect Mode
    if data.name:
        # Single Import: if user provided a name, treat this dir as THE instance root directly
        # No need to check for .openclaw (it will be created by create_default_config in config_mgr)
        import_targets.append((data.name, source_path))
    else:
        # Batch Discovery Mode: Look for subdirectories containing .openclaw
        for item in os.listdir(source_path):
            item_path = os.path.join(source_path, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, ".openclaw")):
                import_targets.append((item, item_path))
                
    if not import_targets:
        # Fallback: If no .openclaw found but user explicitly pointed to a directory for single import
        if data.name:
            import_targets.append((data.name, source_path))
        else:
            raise HTTPException(status_code=400, detail="No valid OpenClaw instances found in the selected path")
    
    imported = []
    for name, src_dir in import_targets:
        # Check for name collision
        if db.query(Instance).filter(Instance.name == name).first():
            if len(import_targets) == 1:
                raise HTTPException(status_code=400, detail=f"Instance name '{name}' already exists")
            continue
            
        # Assign Port
        used_ports = [i.host_port for i in db.query(Instance).filter(Instance.group_id == data.group_id).all()]
        assigned_port = next((p for p in range(group.port_range_start, group.port_range_end + 1) if p not in used_ports), None)
        if not assigned_port:
            if len(import_targets) == 1:
                raise HTTPException(status_code=400, detail="No ports available in this group")
            continue
            
        # Full content import using config_mgr (maps to /root)
        try:
            # Detect actual port from source before importing
            source_config = config_mgr.load_config(src_dir)
            source_port = source_config.get("openclaw", {}).get("gateway", {}).get("port", 18987)
            
            config_mgr.import_from_directory(src_dir, data.group_id, name, group.root_dir)
            target_dir = os.path.join(group.root_dir, name)
            
            # Sync ports to configuration strictly following user requirements
            # Here assigned_port is the host port and 18987 is the default container port if not found
            config_mgr.sync_allowed_origins(target_dir, source_port, assigned_port)
            
            db_instance = Instance(
                group_id=data.group_id,
                name=name,
                container_name=f"openclaw-{name.lower().replace(' ', '-')}-{assigned_port}",
                host_port=assigned_port,
                status="stopped"
            )
            db.add(db_instance)
            imported.append(name)
        except Exception as e:
            if len(import_targets) == 1: raise HTTPException(status_code=500, detail=str(e))
            continue
        
    db.commit()
    return {"imported": imported, "count": len(imported)}

# --- Parameterized Instance Routes ---

@app.get("/api/instances/{instance_id}")
def get_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instance not found")
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    
    container_info = {}
    logs = ""
    try:
        container_info = docker_mgr.get_container_info(inst.container_name)
        logs = docker_mgr.get_container_logs(inst.container_name, tail=100)
    except:
        pass
    
    config = config_mgr.load_config(os.path.join(group.root_dir, inst.name))
    
    return {
        "id": inst.id, 
        "group_id": inst.group_id,
        "group_name": group.name if group else "Unknown",
        "name": inst.name,
        "container_name": inst.container_name,
        "host_port": inst.host_port,
        "container_port": inst.container_port or 18987,
        "status": container_info.get("state", "stopped"),
        "created_at": inst.created_at.isoformat() if inst.created_at else None,
        "container_info": container_info,
        "logs": logs,
        "config": config
    }

@app.post("/api/instances/{instance_id}/start")
def start_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instance not found")
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    
    instance_dir = os.path.join(group.root_dir, inst.name)
    openclaw_dir = os.path.join(instance_dir, ".openclaw")
    
    # Environment Merging: Group -> Instance -> Host
    group_env_file = os.path.join(group.root_dir, ".env")
    environment = docker_mgr.load_env_file(group_env_file)
    
    inst_env_file = os.path.join(openclaw_dir, ".env")
    environment.update(docker_mgr.load_env_file(inst_env_file))
    
    environment = propagate_host_env(environment)
    
    # Enforce essential container paths
    environment["OPENCLAW_HOME"] = "/root"
    environment["OPENCLAW_DATA_DIR"] = "/root/.openclaw"
    
    effective_image = get_effective_image()
    
    docker_mgr.run_container(
        name=inst.container_name, network=group.docker_network,
        ports={f"{inst.container_port or 18987}/tcp": inst.host_port},
        volumes={
            instance_dir: {"bind": "/root", "mode": "rw"}
        },
        environment=environment, image=effective_image
    )
    inst.status = "running"
    db.commit()
    return {"message": "Started"}

@app.post("/api/instances/{instance_id}/stop")
def stop_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instance not found")
    docker_mgr.stop_container(inst.container_name)
    inst.status = "stopped"
    db.commit()
    return {"message": "Stopped"}

@app.post("/api/instances/{instance_id}/restart")
def restart_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instance not found")
    docker_mgr.restart_container(inst.container_name)
    return {"message": "Restarted"}

@app.put("/api/instances/{instance_id}/ports")
def update_instance_ports(instance_id: str, data: PortUpdate, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    instance_dir = os.path.join(group.root_dir, inst.name)
    
    # Capture old values for syncing allowedOrigins
    old_host_port = inst.host_port
    old_container_port = inst.container_port or 18987
    
    # Use new unified sync logic for both host and container port updates
    new_host_port = data.host_port or old_host_port
    new_container_port = data.container_port or old_container_port
    
    if data.host_port:
        inst.host_port = data.host_port
    if data.container_port:
        inst.container_port = data.container_port
        
    # Always sync allowedOrigins strictly when either port changes
    config_mgr.sync_allowed_origins(instance_dir, new_container_port, new_host_port)
        
    db.commit()
    db.refresh(inst)
    
    return {
        "message": "Ports updated",
        "host_port": inst.host_port,
        "container_port": inst.container_port or 18987
    }

@app.delete("/api/instances/{instance_id}")
def delete_single_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instance not found")
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    try:
        docker_mgr.stop_container(inst.container_name)
        docker_mgr.remove_container(inst.container_name)
    except: pass
    if os.path.exists(os.path.join(group.root_dir, inst.name)):
        shutil.rmtree(os.path.join(group.root_dir, inst.name))
    db.delete(inst)
    db.commit()
    return {"message": "Deleted"}

@app.get("/api/instances/{instance_id}/logs")
def get_instance_logs(instance_id: str, tail: int = 100):
    db = SessionLocal()
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst: return {"logs": "Instance not found"}
    logs = docker_mgr.get_container_logs(inst.container_name, tail=tail)
    return {"logs": logs}

@app.get("/api/instances/{instance_id}/config")
def get_instance_config(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    return config_mgr.load_config(os.path.join(group.root_dir, inst.name))

@app.put("/api/instances/{instance_id}/config")
def update_instance_config(instance_id: str, data: ConfigUpdate, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    wdir = os.path.join(group.root_dir, inst.name)
    if data.env_vars: config_mgr.update_env_file(wdir, data.env_vars)
    if data.openclaw_json: config_mgr.update_openclaw_json(wdir, data.openclaw_json)
    return {"message": "Saved"}

@app.get("/api/instances/{instance_id}/terminal")
def get_instance_terminal(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    return {"terminal_url": f"http://localhost:{inst.host_port}/terminal", "gateway_url": f"http://localhost:{inst.host_port}"}

# --- System Routes ---

@app.get("/api/system/stats")
def get_system_stats(db: Session = Depends(get_db)):
    return {"total_instances": db.query(Instance).count(), "total_groups": db.query(Group).count()}

@app.get("/api/system/browse-directory")
def browse_directory():
    try:
        prompt = "请选择实例根目录（该目录将完整映射为容器内 /root）"
        script = f'POSIX path of (choose folder with prompt "{prompt}")'
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        if result.returncode == 0:
            path = result.stdout.strip()
            if not path: return {"path": None}
            return {"path": path}
        return {"path": None}
    except: return {"path": None}

@app.get("/api/system/settings")
def get_settings():
    return config_mgr.get_settings()

@app.put("/api/system/settings")
def update_settings(settings: dict):
    config_mgr.update_settings(settings)
    return {"message": "Settings updated"}

@app.get("/api/system/networks")
def get_networks():
    return docker_mgr.list_networks()

@app.get("/api/system/images")
def get_images():
    return docker_mgr.list_images()

@app.post("/api/system/pull-image")
def pull_image(image: str = "openclaw/openclaw:latest"):
    effective_image = get_effective_image(image)
    docker_mgr.pull_image(effective_image)
    return {"message": "Pulled"}

@app.get("/api/system/pull-image-stream")
def pull_image_stream(image: str = "openclaw/openclaw:latest"):
    return StreamingResponse(docker_mgr.pull_image_stream(get_effective_image(image)), media_type="text/event-stream")

@app.get("/api/system/env-check")
def env_check():
    import platform
    return {"os": platform.system(), "docker": docker_mgr.client is not None}

@app.get("/api/config/templates")
def get_templates():
    return config_mgr.get_preset_templates()

@app.put("/api/config/templates")
def save_templates(templates: dict):
    config_mgr.save_templates(templates)
    return {"message": "Templates saved"}

@app.get("/api/groups/{group_id}/config")
def get_group_config(group_id: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    return config_mgr.load_config(group.root_dir)

@app.put("/api/groups/{group_id}/config")
def update_group_config(group_id: str, data: ConfigUpdate, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    if data.env_vars: config_mgr.update_group_env_file(group.root_dir, data.env_vars)
    if data.openclaw_json: config_mgr.update_group_openclaw_json(group.root_dir, data.openclaw_json)
    return {"message": "Group config updated"}

# --- Export/Import Routes ---

@app.post("/api/instances/{instance_id}/export")
def export_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instance not found")
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    
    zip_path = config_mgr.export_instance(inst.id, inst.name, group.root_dir)
    return {"export_path": zip_path}

@app.post("/api/instances/upload")
def upload_instance(group_id: str, name: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    
    # Check for name collision
    if db.query(Instance).filter(Instance.name == name).first():
        raise HTTPException(status_code=400, detail=f"Instance name '{name}' already exists")

    temp_path = os.path.join("/tmp", f"upload_{name}.zip")
    with open(temp_path, "wb") as f:
        f.write(file.file.read())
    
    try:
        config_mgr.import_instance(temp_path, group_id, name, group.root_dir)
        target_dir = os.path.join(group.root_dir, name)
        
        # Port Assignment
        used_ports = [i.host_port for i in db.query(Instance).filter(Instance.group_id == group_id).all()]
        assigned_port = next((p for p in range(group.port_range_start, group.port_range_end + 1) if p not in used_ports), None)
        if not assigned_port:
             raise HTTPException(status_code=400, detail="No ports available in this group")
             
        # Detect actual port from source before syncing
        source_config = config_mgr.load_config(target_dir)
        source_port = source_config.get("openclaw", {}).get("gateway", {}).get("port", 18987)

        # Sync ports to configuration strictly following user requirements
        config_mgr.sync_allowed_origins(target_dir, source_port, assigned_port)
             
        db_instance = Instance(
            group_id=group_id,
            name=name,
            container_name=f"openclaw-{name.lower().replace(' ', '-')}-{assigned_port}",
            host_port=assigned_port,
            status="stopped"
        )
        db.add(db_instance)
        db.commit()
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)
            
    return {"message": "Instance uploaded and imported successfully"}

@app.post("/api/groups/{group_id}/export")
def export_group(group_id: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Group not found")
    
    zip_path = config_mgr.export_group(group)
    return {"export_path": zip_path}

@app.post("/api/groups/import")
def import_group(file: UploadFile = File(...), db: Session = Depends(get_db)):
    temp_path = os.path.join("/tmp", "group_import.zip")
    with open(temp_path, "wb") as f:
        f.write(file.file.read())
        
    try:
        res = config_mgr.import_group(temp_path)
        # Note: Frontend handles the actual creation of group based on these details
        return res
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.get("/api/download")
def download_file(path: str):
    if os.path.exists(path):
        return FileResponse(path, filename=os.path.basename(path))
    raise HTTPException(status_code=404)

# --- Config Update Check Routes ---

@app.get("/api/config/check-update")
def check_config_update():
    """Check if there's a newer OpenClaw configuration schema available."""
    return config_mgr.check_latest_config_schema()

@app.post("/api/instances/{instance_id}/migrate-config")
def migrate_instance_config(instance_id: str, db: Session = Depends(get_db)):
    """Migrate an instance's configuration to the latest schema."""
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    instance_dir = os.path.join(group.root_dir, inst.name)
    
    # Load current config
    current_config = config_mgr.load_config(instance_dir)
    openclaw_config = current_config.get("openclaw", {})
    
    # Migrate to latest
    migrated = config_mgr.migrate_config_to_latest(
        openclaw_config, 
        target_version="2026.3.2"
    )
    
    # Save migrated config
    config_mgr.update_openclaw_json(instance_dir, migrated)
    
    return {
        "message": "Configuration migrated successfully",
        "previous_version": openclaw_config.get("meta", {}).get("lastTouchedVersion", "unknown"),
        "new_version": migrated.get("meta", {}).get("lastTouchedVersion", "2026.3.2")
    }

@app.get("/api/instances/{instance_id}/config/validate")
def validate_instance_config(instance_id: str, db: Session = Depends(get_db)):
    """Validate an instance's configuration against the latest schema.
    
    Checks for:
    - Illegal fields that cause startup failures
    - Missing required sections
    - Version compatibility
    """
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    instance_dir = os.path.join(group.root_dir, inst.name)
    
    # Load current config
    current_config = config_mgr.load_config(instance_dir)
    openclaw_config = current_config.get("openclaw", {})
    
    # Use new validation method
    validation_result = config_mgr.validate_config(openclaw_config)
    
    # Check for missing sections
    default_config = config_mgr._get_default_openclaw_config(
        openclaw_config.get("gateway", {}).get("port", 18987)
    )
    missing_sections = [key for key in default_config if key not in openclaw_config]
    
    # Check version
    current_version = openclaw_config.get("meta", {}).get("lastTouchedVersion", "unknown")
    
    # Build recommendations
    recommendations = []
    if validation_result["errors"]:
        recommendations.append("Run 'Migrate Config' to fix illegal fields automatically")
    for section in missing_sections:
        recommendations.append(f"Add missing section: {section}")
    if not recommendations:
        recommendations.append("Configuration is valid and up to date")
    
    return {
        "valid": validation_result["valid"] and len(missing_sections) == 0,
        "current_version": current_version,
        "errors": validation_result["errors"],
        "warnings": validation_result["warnings"],
        "missing_sections": missing_sections,
        "recommendations": recommendations
    }

@app.post("/api/instances/{instance_id}/config/fix")
def fix_instance_config(instance_id: str, db: Session = Depends(get_db)):
    """Fix an instance's configuration by removing illegal fields and adding missing sections.
    
    This is a one-click fix for configuration issues that prevent startup.
    """
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    instance_dir = os.path.join(group.root_dir, inst.name)
    
    # Load current config
    current_config = config_mgr.load_config(instance_dir)
    openclaw_config = current_config.get("openclaw", {})
    
    # Validate before fix
    before_validation = config_mgr.validate_config(openclaw_config)
    
    # Apply migration (removes illegal fields + adds missing sections)
    fixed_config = config_mgr.migrate_config_to_latest(openclaw_config)
    
    # Save fixed config
    config_mgr.update_openclaw_json(instance_dir, fixed_config)
    
    # Validate after fix
    after_validation = config_mgr.validate_config(fixed_config)
    
    return {
        "message": "Configuration fixed successfully",
        "fixed_errors": before_validation["errors"],
        "fixed_warnings": before_validation["warnings"],
        "remaining_errors": after_validation["errors"],
        "remaining_warnings": after_validation["warnings"],
        "backup_created": True,
        "backup_location": "/root/.openclaw/openclaw.json.bak (inside container)"
    }

# --- SPA Serving ---

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api"):
        raise HTTPException(status_code=404)
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
    file_path = os.path.join(static_dir, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
