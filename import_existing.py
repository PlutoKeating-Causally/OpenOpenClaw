#!/usr/bin/env python3
"""
导入原有的 OpenClaw 实例到 OpenOpenclaw 管理系统
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
    source_dir = "/Users/causally/openclaws"
    
    # Check if group exists, create if not
    group = db.query(Group).filter(Group.name == "PKs-Intern-Group").first()
    if not group:
        print("创建群组: PKs-Intern-Group")
        group = Group(
            name="PKs-Intern-Group",
            root_dir="groups/pks-intern",
            docker_network="PKs-Causally-Intern-Group",
            port_range_start=18781,
            port_range_end=18790,
            description="原有的 PKs Intern Group"
        )
        db.add(group)
        db.commit()
        db.refresh(group)
    
    # Instance configurations
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
            container_port=18987,
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
            config_mgr.create_default_config(target_instance_dir, gateway_port=18987)
    
    db.commit()
    print("\n导入完成！")
    print(f"群组: {group.name}")
    print(f"实例: Angela (18781), James (18782), Michel (18783)")
    print(f"\n请访问 http://localhost:8080 查看")

if __name__ == "__main__":
    import_existing_instances()
