#!/usr/bin/env python3
"""
导入原有的 OpenClaw 实例到 OpenOpenClaw 管理系统
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models import SessionLocal, Group, Instance, init_db
from config_manager import ConfigManager

def import_existing_instances():
    """Import existing Angela, James, Michel instances"""
    
    print("导入原有的 OpenClaw 实例...")
    
    db = SessionLocal()
    config_mgr = ConfigManager()
    
    # Source directory with existing instances
    source_dir = os.getenv("SOURCE_OPENCLAW_DIR", "./openclaws")
    
    # Check if group exists, create if not
    group_name = os.getenv("IMPORT_GROUP_NAME", "Imported-Group")
    group = db.query(Group).filter(Group.name == group_name).first()
    if not group:
        print(f"创建群组: {group_name}")
        group = Group(
            name=group_name,
            root_dir=f"groups/{group_name.lower().replace(' ', '-')}",
            docker_network=f"openclaw_network_{group_name.lower().replace(' ', '_')}",
            port_range_start=18791,
            port_range_end=18800,
            description=f"从 {source_dir} 导入的群组"
        )
        db.add(group)
        db.commit()
        db.refresh(group)
    
    # Instance configurations (can be overridden by environment variable JSON string)
    import_config_json = os.getenv("IMPORT_INSTANCES_JSON")
    if import_config_json:
        try:
            instances_config = json.loads(import_config_json)
        except json.JSONDecodeError:
            print("警告: IMPORT_INSTANCES_JSON 格式错误，使用默认配置")
            instances_config = [
                {"name": "Angela", "port": 18781},
                {"name": "James", "port": 18782},
                {"name": "Michel", "port": 18783},
            ]
    else:
        instances_config = [
            {"name": "Angela", "port": 18781},
            {"name": "James", "port": 18782},
            {"name": "Michel", "port": 18783},
        ]
    
    data_dir = os.getenv("OPENCLAW_DATA_DIR", "./data")
    group_dir = os.path.join(data_dir, group.root_dir)
    os.makedirs(group_dir, exist_ok=True)
    
    for config in instances_config:
        name = config["name"]
        port = config["port"]
        
        # Check if instance already exists
        existing = db.query(Instance).filter(Instance.name == name).first()
        if existing:
            print(f"实例 {name} 已存在，跳过")
            continue
        
        print(f"导入实例: {name} (端口: {port})")
        
        # Create instance record
        container_name = f"openclaw-{name.lower()}-{port}"
        instance = Instance(
            group_id=group.id,
            name=name,
            container_name=container_name,
            host_port=port,
            container_port=18789,
            status="stopped"
        )
        db.add(instance)
        
        # Copy instance data
        source_instance_dir = os.path.join(source_dir, name)
        target_instance_dir = os.path.join(group_dir, name)
        
        if os.path.exists(source_instance_dir):
            if os.path.exists(target_instance_dir):
                shutil.rmtree(target_instance_dir)
            shutil.copytree(source_instance_dir, target_instance_dir)
            print(f"  复制数据: {source_instance_dir} -> {target_instance_dir}")
        else:
            print(f"  警告: 源目录不存在 {source_instance_dir}")
            # Create default config
            os.makedirs(target_instance_dir, exist_ok=True)
            config_mgr.create_default_config(target_instance_dir, gateway_port=18789)
    
    db.commit()
    print("\n导入完成！")
    print(f"群组: {group.name}")
    print(f"实例: Angela (18781), James (18782), Michel (18783)")
    print(f"\n请访问 http://localhost:8080 查看")

if __name__ == "__main__":
    import_existing_instances()
