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
import platform
import socket
import sys

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

app = FastAPI(title="OpenOpenClaw API", version="1.0.0", lifespan=lifespan)

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
config_mgr = ConfigManager(docker_manager=docker_mgr)

# --- Utils ---

DEFAULT_OPENCLAW_IMAGE = "ghcr.io/openclaw/openclaw:latest"
LEGACY_OPENCLAW_IMAGES = {
    "openclaw/openclaw",
    "openclaw/openclaw:latest",
}

def get_effective_image(image: str = None) -> str:
    settings = config_mgr.get_settings()
    default_image = settings.get("default_image", DEFAULT_OPENCLAW_IMAGE)
    img = image or default_image
    if img in LEGACY_OPENCLAW_IMAGES:
        img = DEFAULT_OPENCLAW_IMAGE
    
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

def get_directory_size(path: str) -> int:
    total_size = 0
    if not os.path.exists(path):
        return total_size

    for root, _, files in os.walk(path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                if not os.path.islink(file_path):
                    total_size += os.path.getsize(file_path)
            except OSError:
                continue
    return total_size

def resolve_storage_path(path: str) -> str:
    expanded_path = os.path.expanduser(path)
    if os.path.isabs(expanded_path):
        return os.path.abspath(expanded_path)
    return os.path.abspath(os.path.join(config_mgr.data_dir, expanded_path))

def get_group_root_dir(group: Group) -> str:
    return resolve_storage_path(group.root_dir)

def get_instance_root_dir(group: Group, instance_name: str) -> str:
    return os.path.join(get_group_root_dir(group), instance_name)

def require_group(db: Session, group_id: str) -> Group:
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

def require_instance(db: Session, instance_id: str) -> Instance:
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    return inst

def validate_instance_port_assignment(db: Session, group: Group, instance_id: Optional[str], host_port: int):
    if host_port < group.port_range_start or host_port > group.port_range_end:
        raise HTTPException(status_code=400, detail="Host port is outside group port range")

    query = db.query(Instance).filter(Instance.group_id == group.id, Instance.host_port == host_port)
    if instance_id:
        query = query.filter(Instance.id != instance_id)

    if query.first():
        raise HTTPException(status_code=400, detail="Port in use")

def validate_group_port_range(port_range_start: int, port_range_end: int):
    if port_range_start < 1 or port_range_end > 65535:
        raise HTTPException(status_code=400, detail="Group port range must be within 1-65535")
    if port_range_start > port_range_end:
        raise HTTPException(status_code=400, detail="Group port range start must be less than or equal to end")

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
    root_dir: Optional[str] = None
    docker_network: Optional[str] = None
    description: Optional[str] = None
    port_range_start: Optional[int] = None
    port_range_end: Optional[int] = None

class InstanceCreate(BaseModel):
    group_id: str
    name: str
    container_port: Optional[int] = 18789
    host_port: Optional[int] = None

class ConfigUpdate(BaseModel):
    env_vars: Optional[dict] = None
    openclaw_json: Optional[dict] = None
    replace: bool = True

class PortUpdate(BaseModel):
    host_port: Optional[int] = None
    container_port: Optional[int] = None

class DirectoryImport(BaseModel):
    source_dir: str
    group_id: str
    name: Optional[str] = None

def propagate_host_env(environment: dict) -> dict:
    """Propagate AI API keys from host environment to container if not already set.
    
    Uses official OpenClaw env var names.
    Ref: https://docs.openclaw.ai/concepts/model-providers
    Ref: https://github.com/openclaw/openclaw/blob/main/.env.example
    """
    keys_to_check = [
        # --- Model provider API keys (official OpenClaw names) ---
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "OPENROUTER_API_KEY",
        "DEEPSEEK_API_KEY",
        "MINIMAX_API_KEY",
        "MISTRAL_API_KEY",
        "GROQ_API_KEY",
        "XAI_API_KEY",
        "HUGGINGFACE_HUB_TOKEN",
        "VOYAGE_API_KEY",
        "ZAI_API_KEY",
        "CEREBRAS_API_KEY",
        "TOGETHER_API_KEY",
        "MOONSHOT_API_KEY",
        "KIMI_API_KEY",
        "OLLAMA_API_KEY",
        "VENICE_API_KEY",
        "NVIDIA_API_KEY",
        "SYNTHETIC_API_KEY",
        "KILOCODE_API_KEY",
        "AI_GATEWAY_API_KEY",
        # --- Key rotation / multi-key support ---
        "OPENAI_API_KEYS",
        "ANTHROPIC_API_KEYS",
        "GEMINI_API_KEYS",
        "GOOGLE_API_KEY",
        # --- Gateway auth ---
        "OPENCLAW_GATEWAY_TOKEN",
        "OPENCLAW_GATEWAY_PASSWORD",
        # --- Channel tokens ---
        "TELEGRAM_BOT_TOKEN",
        "DISCORD_BOT_TOKEN",
        "SLACK_BOT_TOKEN",
        "SLACK_APP_TOKEN",
        # --- Tools ---
        "BRAVE_API_KEY",
        "PERPLEXITY_API_KEY",
        "FIRECRAWL_API_KEY",
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
    return {"message": "OpenOpenClaw API", "version": "1.0.0"}

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
    if not group.name.strip():
        raise HTTPException(status_code=400, detail="Group name cannot be empty")
    if not group.root_dir.strip():
        raise HTTPException(status_code=400, detail="Group root directory cannot be empty")
    if not group.docker_network.strip():
        raise HTTPException(status_code=400, detail="Docker network cannot be empty")
    if db.query(Group).filter(Group.root_dir == group.root_dir).first():
        raise HTTPException(status_code=400, detail="Group root directory already exists")
    validate_group_port_range(group.port_range_start, group.port_range_end)
    
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
    
    created_network = False
    try:
        created_network = docker_mgr.create_network(group.docker_network)
        os.makedirs(resolve_storage_path(group.root_dir), exist_ok=True)
    except Exception as e:
        db.delete(db_group)
        db.commit()
        if created_network:
            try:
                docker_mgr.remove_network(group.docker_network)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to initialize group resources: {e}")
    
    return {"id": db_group.id, "name": db_group.name}

@app.get("/api/groups/{group_id}")
def get_group(group_id: str, db: Session = Depends(get_db)):
    group = require_group(db, group_id)
    group_root_dir = get_group_root_dir(group)
    
    instances = db.query(Instance).filter(Instance.group_id == group_id).all()
    return {
        "id": group.id, "name": group.name, "root_dir": group.root_dir,
        "docker_network": group.docker_network, "port_range_start": group.port_range_start,
        "port_range_end": group.port_range_end, "description": group.description,
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "storage_used": get_directory_size(group_root_dir),
        "instances": [{"id": i.id, "name": i.name, "status": i.status, 
                        "host_port": i.host_port, "container_port": i.container_port or 18789,
                        "created_at": i.created_at.isoformat() if i.created_at else None} 
                       for i in instances]
    }

@app.put("/api/groups/{group_id}")
def update_group(group_id: str, group: GroupUpdate, db: Session = Depends(get_db)):
    db_group = require_group(db, group_id)
    instances = db.query(Instance).filter(Instance.group_id == group_id).all()

    new_name = group.name.strip() if group.name is not None else db_group.name
    new_root_dir = group.root_dir.strip() if group.root_dir is not None else db_group.root_dir
    new_docker_network = group.docker_network.strip() if group.docker_network is not None else db_group.docker_network
    new_port_range_start = group.port_range_start if group.port_range_start is not None else db_group.port_range_start
    new_port_range_end = group.port_range_end if group.port_range_end is not None else db_group.port_range_end

    if not new_name:
        raise HTTPException(status_code=400, detail="Group name cannot be empty")
    if not new_root_dir:
        raise HTTPException(status_code=400, detail="Group root directory cannot be empty")
    if not new_docker_network:
        raise HTTPException(status_code=400, detail="Docker network cannot be empty")

    validate_group_port_range(new_port_range_start, new_port_range_end)

    name_conflict = db.query(Group).filter(Group.name == new_name, Group.id != group_id).first()
    if name_conflict:
        raise HTTPException(status_code=400, detail="Group name already exists")

    root_dir_conflict = db.query(Group).filter(Group.root_dir == new_root_dir, Group.id != group_id).first()
    if root_dir_conflict:
        raise HTTPException(status_code=400, detail="Group root directory already exists")

    root_dir_changed = new_root_dir != db_group.root_dir
    docker_network_changed = new_docker_network != db_group.docker_network
    has_running_instances = any(inst.status == "running" for inst in instances)

    if (root_dir_changed or docker_network_changed) and has_running_instances:
        raise HTTPException(status_code=400, detail="Stop all group instances before changing root directory or Docker network")

    for inst in instances:
        if inst.host_port < new_port_range_start or inst.host_port > new_port_range_end:
            raise HTTPException(status_code=400, detail=f"Instance {inst.name} uses port {inst.host_port}, which is outside the new group port range")

    old_root_dir = get_group_root_dir(db_group)
    new_root_dir_path = resolve_storage_path(new_root_dir)

    if root_dir_changed:
        if os.path.exists(new_root_dir_path) and os.path.abspath(new_root_dir_path) != os.path.abspath(old_root_dir):
            raise HTTPException(status_code=400, detail="Target group root directory already exists on disk")

        if os.path.exists(old_root_dir) and os.path.abspath(old_root_dir) != os.path.abspath(new_root_dir_path):
            parent_dir = os.path.dirname(new_root_dir_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            shutil.move(old_root_dir, new_root_dir_path)
        else:
            os.makedirs(new_root_dir_path, exist_ok=True)

    if docker_network_changed:
        try:
            docker_mgr.create_network(new_docker_network)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create Docker network: {e}")

    db_group.name = new_name
    db_group.root_dir = new_root_dir
    db_group.docker_network = new_docker_network
    db_group.description = group.description if group.description is not None else db_group.description
    db_group.port_range_start = new_port_range_start
    db_group.port_range_end = new_port_range_end

    db.commit()
    return {"message": "Group updated"}

@app.delete("/api/groups/{group_id}")
def delete_group(group_id: str, db: Session = Depends(get_db)):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    group_root_dir = get_group_root_dir(db_group)
    
    instances = db.query(Instance).filter(Instance.group_id == group_id).all()
    for inst in instances:
        try:
            docker_mgr.stop_container(inst.container_name)
            docker_mgr.remove_container(inst.container_name)
        except:
            pass
        inst_path = os.path.join(group_root_dir, inst.name)
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
            "container_port": inst.container_port or 18789,
            "status": container_status, "created_at": inst.created_at.isoformat() if inst.created_at else None
        })
    return result

@app.post("/api/instances")
def create_instance(instance: InstanceCreate, db: Session = Depends(get_db)):
    group = require_group(db, instance.group_id)
    
    existing = db.query(Instance).filter(Instance.name == instance.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Instance name already exists")
    
    used_ports = [i.host_port for i in db.query(Instance).filter(Instance.group_id == instance.group_id).all()]
    if instance.host_port:
        validate_instance_port_assignment(db, group, None, instance.host_port)
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
    
    container_port = instance.container_port or 18789
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
    
    instance_dir = get_instance_root_dir(group, instance.name)
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
                group_root_dir = get_group_root_dir(group)
                instance_dir = os.path.join(group_root_dir, inst.name)
                openclaw_dir = os.path.join(instance_dir, ".openclaw")
                
                # 1. Load Group Env
                group_env_path = os.path.join(group_root_dir, ".env")
                environment = docker_mgr.load_env_file(group_env_path)
                
                # 2. Merge Instance Env (Instance wins)
                inst_env_path = os.path.join(openclaw_dir, ".env")
                environment.update(docker_mgr.load_env_file(inst_env_path))
                
                # 3. Propagate selected Host keys
                environment = propagate_host_env(environment)
                
                # 4. Enforce essential container paths for root user in Docker
                # Ref: https://docs.openclaw.ai/help/environment
                environment["HOME"] = "/root"
                environment["OPENCLAW_HOME"] = "/root"
                environment["OPENCLAW_STATE_DIR"] = "/root/.openclaw"
                environment["OPENCLAW_CONFIG_DIR"] = "/root/.openclaw"
                environment["OPENCLAW_WORKSPACE_DIR"] = "/root/.openclaw/workspace"
                environment["OPENCLAW_GATEWAY_BIND"] = "lan"
                
                # 5. Inject global gateway password from system settings
                settings = config_mgr.get_settings()
                global_password = settings.get("gateway_password", "")
                if global_password and not environment.get("OPENCLAW_GATEWAY_PASSWORD"):
                    environment["OPENCLAW_GATEWAY_PASSWORD"] = global_password
                
                docker_mgr.run_container(
                    name=inst.container_name,
                    network=group.docker_network,
                    ports={f"{inst.container_port or 18789}/tcp": inst.host_port},
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
            
            instance_dir = get_instance_root_dir(group, inst.name)
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
    effective_image = get_effective_image()
    for inst in instances:
        if inst.status != "running":
            group = db.query(Group).filter(Group.id == inst.group_id).first()
            if not group:
                continue
            try:
                group_root_dir = get_group_root_dir(group)
                instance_dir = os.path.join(group_root_dir, inst.name)
                openclaw_dir = os.path.join(instance_dir, ".openclaw")
                
                group_env_path = os.path.join(group_root_dir, ".env")
                environment = docker_mgr.load_env_file(group_env_path)
                
                inst_env_path = os.path.join(openclaw_dir, ".env")
                environment.update(docker_mgr.load_env_file(inst_env_path))
                
                environment = propagate_host_env(environment)
                
                environment["HOME"] = "/root"
                environment["OPENCLAW_HOME"] = "/root"
                environment["OPENCLAW_STATE_DIR"] = "/root/.openclaw"
                environment["OPENCLAW_CONFIG_DIR"] = "/root/.openclaw"
                environment["OPENCLAW_WORKSPACE_DIR"] = "/root/.openclaw/workspace"
                environment["OPENCLAW_GATEWAY_BIND"] = "lan"
                
                settings = config_mgr.get_settings()
                global_password = settings.get("gateway_password", "")
                if global_password and not environment.get("OPENCLAW_GATEWAY_PASSWORD"):
                    environment["OPENCLAW_GATEWAY_PASSWORD"] = global_password
                
                docker_mgr.run_container(
                    name=inst.container_name,
                    network=group.docker_network,
                    ports={f"{inst.container_port or 18789}/tcp": inst.host_port},
                    volumes={
                        instance_dir: {"bind": "/root", "mode": "rw"}
                    },
                    environment=environment,
                    image=effective_image
                )
                inst.status = "running"
                results.append({"id": inst.id, "status": "success"})
            except:
                results.append({"id": inst.id, "status": "failed"})
    db.commit()
    return {"results": results}

# --- Import/Migration ---

@app.post("/api/instances/import-directory")
def import_instances_from_directory(data: DirectoryImport, db: Session = Depends(get_db)):
    group = require_group(db, data.group_id)
    group_root_dir = get_group_root_dir(group)
    
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
            source_port = source_config.get("openclaw", {}).get("gateway", {}).get("port", 18789)
            
            config_mgr.import_from_directory(src_dir, data.group_id, name, group_root_dir)
            target_dir = os.path.join(group_root_dir, name)
            
            # Sync ports to configuration strictly following user requirements
            # Here assigned_port is the host port and 18789 is the default container port if not found
            config_mgr.sync_allowed_origins(target_dir, source_port, assigned_port)
            
            db_instance = Instance(
                group_id=data.group_id,
                name=name,
                container_name=f"openclaw-{name.lower().replace(' ', '-')}-{assigned_port}",
                host_port=assigned_port,
                container_port=source_port,
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
    inst = require_instance(db, instance_id)
    group = require_group(db, inst.group_id)
    instance_dir = get_instance_root_dir(group, inst.name)
    
    container_info = {}
    logs = ""
    try:
        container_info = docker_mgr.get_container_info(inst.container_name)
        logs = docker_mgr.get_container_logs(inst.container_name, tail=100)
    except:
        pass
    
    config = config_mgr.load_config(instance_dir)
    
    return {
        "id": inst.id, 
        "group_id": inst.group_id,
        "group_name": group.name if group else "Unknown",
        "name": inst.name,
        "container_name": inst.container_name,
        "host_port": inst.host_port,
        "container_port": inst.container_port or 18789,
        "status": container_info.get("state", "stopped"),
        "created_at": inst.created_at.isoformat() if inst.created_at else None,
        "container_info": container_info,
        "logs": logs,
        "config": config
    }

@app.post("/api/instances/{instance_id}/start")
def start_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = require_instance(db, instance_id)
    group = require_group(db, inst.group_id)
    
    group_root_dir = get_group_root_dir(group)
    instance_dir = os.path.join(group_root_dir, inst.name)
    openclaw_dir = os.path.join(instance_dir, ".openclaw")
    
    # Environment Merging: Group -> Instance -> Host
    group_env_file = os.path.join(group_root_dir, ".env")
    environment = docker_mgr.load_env_file(group_env_file)
    
    inst_env_file = os.path.join(openclaw_dir, ".env")
    environment.update(docker_mgr.load_env_file(inst_env_file))
    
    environment = propagate_host_env(environment)
    
    # Enforce essential container paths for root user in Docker
    # Ref: https://docs.openclaw.ai/help/environment
    environment["HOME"] = "/root"
    environment["OPENCLAW_HOME"] = "/root"
    environment["OPENCLAW_STATE_DIR"] = "/root/.openclaw"
    environment["OPENCLAW_CONFIG_DIR"] = "/root/.openclaw"
    environment["OPENCLAW_WORKSPACE_DIR"] = "/root/.openclaw/workspace"
    environment["OPENCLAW_GATEWAY_BIND"] = "lan"
    
    # Inject global gateway password from system settings
    settings = config_mgr.get_settings()
    global_password = settings.get("gateway_password", "")
    if global_password and not environment.get("OPENCLAW_GATEWAY_PASSWORD"):
        environment["OPENCLAW_GATEWAY_PASSWORD"] = global_password
    
    effective_image = get_effective_image()
    
    docker_mgr.run_container(
        name=inst.container_name, network=group.docker_network,
        ports={f"{inst.container_port or 18789}/tcp": inst.host_port},
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
    inst = require_instance(db, instance_id)
    docker_mgr.stop_container(inst.container_name)
    inst.status = "stopped"
    db.commit()
    return {"message": "Stopped"}

@app.post("/api/instances/{instance_id}/restart")
def restart_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = require_instance(db, instance_id)
    docker_mgr.restart_container(inst.container_name)
    inst.status = "running"
    db.commit()
    return {"message": "Restarted"}

@app.put("/api/instances/{instance_id}/ports")
def update_instance_ports(instance_id: str, data: PortUpdate, db: Session = Depends(get_db)):
    inst = require_instance(db, instance_id)
    group = require_group(db, inst.group_id)
    instance_dir = get_instance_root_dir(group, inst.name)
    
    # Capture old values for syncing allowedOrigins
    old_host_port = inst.host_port
    old_container_port = inst.container_port or 18789
    
    # Use new unified sync logic for both host and container port updates
    new_host_port = data.host_port or old_host_port
    new_container_port = data.container_port or old_container_port

    if data.host_port:
        validate_instance_port_assignment(db, group, inst.id, data.host_port)
    if data.container_port and data.container_port < 1:
        raise HTTPException(status_code=400, detail="Container port must be greater than 0")
    
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
        "container_port": inst.container_port or 18789
    }

@app.delete("/api/instances/{instance_id}")
def delete_single_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = require_instance(db, instance_id)
    group = require_group(db, inst.group_id)
    try:
        docker_mgr.stop_container(inst.container_name)
        docker_mgr.remove_container(inst.container_name)
    except: pass
    instance_dir = get_instance_root_dir(group, inst.name)
    if os.path.exists(instance_dir):
        shutil.rmtree(instance_dir)
    db.delete(inst)
    db.commit()
    return {"message": "Deleted"}

@app.get("/api/instances/{instance_id}/logs")
def get_instance_logs(instance_id: str, tail: int = 100, db: Session = Depends(get_db)):
    inst = require_instance(db, instance_id)
    logs = docker_mgr.get_container_logs(inst.container_name, tail=tail)
    return {"logs": logs}

@app.get("/api/instances/{instance_id}/config")
def get_instance_config(instance_id: str, db: Session = Depends(get_db)):
    inst = require_instance(db, instance_id)
    group = require_group(db, inst.group_id)
    return config_mgr.load_config(get_instance_root_dir(group, inst.name))

@app.put("/api/instances/{instance_id}/config")
def update_instance_config(instance_id: str, data: ConfigUpdate, db: Session = Depends(get_db)):
    inst = require_instance(db, instance_id)
    group = require_group(db, inst.group_id)
    wdir = get_instance_root_dir(group, inst.name)
    if data.env_vars is not None:
        config_mgr.update_env_file(wdir, data.env_vars, replace=data.replace, container_name=inst.container_name)
    if data.openclaw_json is not None:
        config_mgr.update_openclaw_json(wdir, data.openclaw_json, replace=data.replace, container_name=inst.container_name)
    return {"message": "Saved"}

@app.get("/api/instances/{instance_id}/terminal")
def get_instance_terminal(instance_id: str, db: Session = Depends(get_db)):
    inst = require_instance(db, instance_id)
    return {"terminal_url": f"http://localhost:{inst.host_port}/terminal", "gateway_url": f"http://localhost:{inst.host_port}"}

@app.get("/api/instances/{instance_id}/stats")
def get_instance_stats(instance_id: str, db: Session = Depends(get_db)):
    inst = require_instance(db, instance_id)
    return docker_mgr.get_container_stats(inst.container_name)

# --- System Routes ---

@app.get("/api/system/stats")
def get_system_stats(db: Session = Depends(get_db)):
    total_instances = db.query(Instance).count()
    running_instances = db.query(Instance).filter(Instance.status == "running").count()
    stopped_instances = total_instances - running_instances
    
    docker_info = {}
    try:
        docker_info = docker_mgr.get_system_info()
    except:
        pass
        
    return {
        "total_instances": total_instances,
        "running_instances": running_instances,
        "stopped_instances": stopped_instances,
        "total_groups": db.query(Group).count(),
        "docker": docker_info
    }

@app.get("/api/system/browse-directory")
def browse_directory():
    """
    Returns a directory path for selection. 
    Note: osascript is only applicable on macOS. For Linux, 
    we return a default path or handle via frontend directory browser.
    """
    try:
        import platform
        if platform.system() == "Darwin":
            prompt = "请选择实例根目录（该目录将完整映射为容器内 /root）"
            script = f'POSIX path of (choose folder with prompt "{prompt}")'
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                if path: return {"path": path}
        
        # Fallback for Linux or failed osascript
        return {"path": os.getcwd()}
    except: 
        return {"path": os.getcwd()}

@app.get("/api/system/settings")
def get_settings():
    return config_mgr.get_settings()

@app.put("/api/system/settings")
def update_settings(settings: dict):
    config_mgr.update_settings(settings)
    return {"message": "Settings updated"}

@app.get("/api/system/networks")
def get_networks():
    return {"networks": docker_mgr.list_networks()}

@app.get("/api/system/images")
def get_images():
    return {"images": docker_mgr.list_images()}

@app.post("/api/system/pull-image")
def pull_image(image: str = DEFAULT_OPENCLAW_IMAGE):
    effective_image = get_effective_image(image)
    docker_mgr.pull_image(effective_image)
    return {"message": "Pulled"}

@app.get("/api/system/pull-image-stream")
def pull_image_stream(image: str = DEFAULT_OPENCLAW_IMAGE):
    return StreamingResponse(docker_mgr.pull_image_stream(get_effective_image(image)), media_type="text/event-stream")

@app.post("/api/instances/{instance_id}/clone")
def clone_instance(instance_id: str, new_name: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter(Instance.id == instance_id).first()
    if not inst: raise HTTPException(status_code=404, detail="Instance not found")
    
    group = db.query(Group).filter(Group.id == inst.group_id).first()
    group_root_dir = get_group_root_dir(group)
    source_dir = os.path.join(group_root_dir, inst.name)
    
    # 1. Check if new name exists
    if db.query(Instance).filter(Instance.name == new_name).first():
        raise HTTPException(status_code=400, detail="New instance name already exists")
    
    # 2. Assign Port
    used_ports = [i.host_port for i in db.query(Instance).filter(Instance.group_id == inst.group_id).all()]
    assigned_port = next((p for p in range(group.port_range_start, group.port_range_end + 1) if p not in used_ports), None)
    if not assigned_port:
        raise HTTPException(status_code=400, detail="No ports available in this group")
    
    # 3. Copy files
    target_dir = os.path.join(group_root_dir, new_name)
    try:
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        shutil.copytree(source_dir, target_dir)
        
        # 4. Sync ports in config
        container_port = inst.container_port or 18789
        config_mgr.sync_allowed_origins(target_dir, container_port, assigned_port)
        
        # 5. Create DB entry
        new_inst = Instance(
            group_id=inst.group_id,
            name=new_name,
            container_name=f"openclaw-{new_name.lower().replace(' ', '-')}-{assigned_port}",
            host_port=assigned_port,
            container_port=container_port,
            status="stopped"
        )
        db.add(new_inst)
        db.commit()
        return {"id": new_inst.id, "name": new_inst.name}
    except Exception as e:
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/env-check")
def env_check():
    settings = config_mgr.get_settings()
    docker_socket = settings.get("docker_socket", "/var/run/docker.sock")
    data_dir = settings.get("effective_data_dir") or config_mgr.data_dir
    docker_info = docker_mgr.get_system_info() if docker_mgr.client is not None else {}

    data_dir_writable = False
    try:
        os.makedirs(data_dir, exist_ok=True)
        probe_file = os.path.join(data_dir, ".openopenclaw-write-test")
        with open(probe_file, "w") as f:
            f.write("ok")
        os.remove(probe_file)
        data_dir_writable = True
    except OSError:
        data_dir_writable = False

    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": sys.version.split()[0],
        "hostname": socket.gethostname(),
        "docker_available": docker_mgr.client is not None,
        "docker_version": docker_info.get("docker_version", "unknown"),
        "docker_socket_exists": os.path.exists(os.path.expanduser(docker_socket)),
        "data_dir_writable": data_dir_writable,
        "effective_data_dir": data_dir
    }

@app.get("/api/config/templates")
def get_templates():
    return config_mgr.get_preset_templates()

@app.put("/api/config/templates")
def save_templates(templates: dict):
    config_mgr.save_templates(templates)
    return {"message": "Templates saved"}

@app.get("/api/config/defaults")
def get_default_config_bundle(gateway_port: int = 18789):
    return config_mgr.get_default_config_bundle(gateway_port)

@app.get("/api/groups/{group_id}/config")
def get_group_config(group_id: str, db: Session = Depends(get_db)):
    group = require_group(db, group_id)
    return config_mgr.load_group_config(get_group_root_dir(group))

@app.put("/api/groups/{group_id}/config")
def update_group_config(group_id: str, data: ConfigUpdate, db: Session = Depends(get_db)):
    group = require_group(db, group_id)
    group_root_dir = get_group_root_dir(group)
    if data.env_vars is not None:
        config_mgr.update_group_env_file(group_root_dir, data.env_vars, replace=data.replace)
    if data.openclaw_json is not None:
        config_mgr.update_group_openclaw_json(group_root_dir, data.openclaw_json, replace=data.replace)
    return {"message": "Group config updated"}

# --- Export/Import Routes ---

@app.post("/api/instances/{instance_id}/export")
def export_instance(instance_id: str, db: Session = Depends(get_db)):
    inst = require_instance(db, instance_id)
    group = require_group(db, inst.group_id)
    
    zip_path = config_mgr.export_instance(inst.id, inst.name, get_group_root_dir(group))
    return {"export_path": zip_path}

@app.post("/api/instances/upload")
def upload_instance(group_id: str, name: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    group = require_group(db, group_id)
    group_root_dir = get_group_root_dir(group)
    
    # Check for name collision
    if db.query(Instance).filter(Instance.name == name).first():
        raise HTTPException(status_code=400, detail=f"Instance name '{name}' already exists")

    temp_path = os.path.join("/tmp", f"upload_{name}.zip")
    with open(temp_path, "wb") as f:
        f.write(file.file.read())
    
    try:
        config_mgr.import_instance(temp_path, group_id, name, group_root_dir)
        target_dir = os.path.join(group_root_dir, name)
        
        # Port Assignment
        used_ports = [i.host_port for i in db.query(Instance).filter(Instance.group_id == group_id).all()]
        assigned_port = next((p for p in range(group.port_range_start, group.port_range_end + 1) if p not in used_ports), None)
        if not assigned_port:
             raise HTTPException(status_code=400, detail="No ports available in this group")
             
        # Detect actual port from source before syncing
        source_config = config_mgr.load_config(target_dir)
        source_port = source_config.get("openclaw", {}).get("gateway", {}).get("port", 18789)

        # Sync ports to configuration strictly following user requirements
        config_mgr.sync_allowed_origins(target_dir, source_port, assigned_port)
             
        db_instance = Instance(
            group_id=group_id,
            name=name,
            container_name=f"openclaw-{name.lower().replace(' ', '-')}-{assigned_port}",
            host_port=assigned_port,
            container_port=source_port,
            status="stopped"
        )
        db.add(db_instance)
        db.commit()
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)
            
    return {"message": "Instance uploaded and imported successfully"}

@app.post("/api/groups/{group_id}/export")
def export_group(group_id: str, db: Session = Depends(get_db)):
    group = require_group(db, group_id)
    
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
    normalized_path = os.path.abspath(path)
    exports_dir = os.path.abspath(os.path.join(config_mgr.data_dir, "exports"))
    if not normalized_path.startswith(exports_dir + os.sep) and normalized_path != exports_dir:
        raise HTTPException(status_code=403, detail="Download path not allowed")
    if os.path.exists(normalized_path):
        return FileResponse(normalized_path, filename=os.path.basename(normalized_path))
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
    instance_dir = get_instance_root_dir(group, inst.name)
    
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
    instance_dir = get_instance_root_dir(group, inst.name)
    
    # Load current config
    current_config = config_mgr.load_config(instance_dir)
    openclaw_config = current_config.get("openclaw", {})
    
    # Use new validation method
    validation_result = config_mgr.validate_config(openclaw_config)
    
    # Check for missing sections
    default_config = config_mgr._get_default_openclaw_config(
        openclaw_config.get("gateway", {}).get("port", 18789)
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
    instance_dir = get_instance_root_dir(group, inst.name)
    
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
