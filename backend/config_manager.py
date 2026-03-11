import os
import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Optional

class ConfigManager:
    def __init__(self):
        self.data_dir = os.getenv("OPENCLAW_DATA_DIR", "./data")
        self.settings_file = os.path.join(self.data_dir, "settings.json")
        self.templates_file = os.path.join(self.data_dir, "templates.json")
        self._init_default_settings()
        self._init_default_templates()
    
    def _init_default_settings(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.settings_file):
            default_settings = {
                "docker_socket": "/var/run/docker.sock",
                "web_port": 8080,
                "data_root": self.data_dir,
                "default_image": "openclaw/openclaw:latest"
            }
            with open(self.settings_file, "w") as f:
                json.dump(default_settings, f, indent=2)
    
    def _init_default_templates(self):
        if not os.path.exists(self.templates_file):
            templates = {
                "byok": {
                    "openai": {
                        "OPENAI_API_KEY": ""
                    },
                    "anthropic": {
                        "ANTHROPIC_API_KEY": ""
                    },
                    "google": {
                        "GOOGLE_GENERATIVE_AI_API_KEY": ""
                    },
                    "azure": {
                        "AZURE_OPENAI_API_KEY": "",
                        "AZURE_OPENAI_ENDPOINT": "",
                        "AZURE_OPENAI_DEPLOYMENT": ""
                    },
                    "deepseek": {
                        "DEEPSEEK_API_KEY": ""
                    },
                    "minimax": {
                        "MINIMAX_API_KEY": ""
                    },
                    "ollama": {
                        "OLLAMA_BASE_URL": "http://localhost:11434"
                    },
                    "openrouter": {
                        "OPENROUTER_API_KEY": ""
                    },
                    "huggingface": {
                        "HUGGINGFACE_HUB_TOKEN": ""
                    },
                    "groq": {
                        "GROQ_API_KEY": ""
                    },
                    "xai": {
                        "XAI_API_KEY": ""
                    },
                    "cohere": {
                        "COHERE_API_KEY": ""
                    },
                    "mistral": {
                        "MISTRAL_API_KEY": ""
                    },
                    "voyage": {
                        "VOYAGE_API_KEY": ""
                    }
                },
                "channels": {
                    "telegram": {
                        "TELEGRAM_BOT_TOKEN": ""
                    },
                    "discord": {
                        "DISCORD_BOT_TOKEN": "",
                        "DISCORD_GUILD_ID": "",
                        "DISCORD_USER_ID": ""
                    },
                    "feishu": {
                        "FEISHU_APP_ID": "",
                        "FEISHU_APP_SECRET": ""
                    },
                    "whatsapp": {
                        "WHATSAPP_SESSION_PATH": "/root/.openclaw/credentials/whatsapp"
                    },
                    "slack": {
                        "SLACK_BOT_TOKEN": "",
                        "SLACK_TEAM_ID": ""
                    },
                    "signal": {
                        "SIGNAL电话号码": ""
                    }
                },
                "other_llm": {
                    "google": {
                        "GOOGLE_GENERATIVE_AI_API_KEY": ""
                    },
                    "huggingface": {
                        "HUGGINGFACE_HUB_TOKEN": ""
                    },
                    "groq": {
                        "GROQ_API_KEY": ""
                    },
                    "xai": {
                        "XAI_API_KEY": ""
                    },
                    "cohere": {
                        "COHERE_API_KEY": ""
                    },
                    "mistral": {
                        "MISTRAL_API_KEY": ""
                    },
                    "voyage": {
                        "VOYAGE_API_KEY": ""
                    }
                }
            }
            with open(self.templates_file, "w") as f:
                json.dump(templates, f, indent=2)
    
    def get_settings(self) -> dict:
        settings = {}
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
        
        # Ensure we always return the effective data_root from environment if not in settings
        if "data_root" not in settings or settings["data_root"] == "/data/openclaw":
            settings["data_root"] = self.data_dir
            
        # Add effective env info for UI display
        settings["effective_data_dir"] = self.data_dir
        return settings
    
    def update_settings(self, settings: dict):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.settings_file, "w") as f:
            json.dump(settings, f, indent=2)
    
    def get_preset_templates(self) -> dict:
        if os.path.exists(self.templates_file):
            with open(self.templates_file, "r") as f:
                return json.load(f)
        return {}
    
    def save_templates(self, templates: dict):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.templates_file, "w") as f:
            json.dump(templates, f, indent=2)
    
    def create_default_config(self, instance_dir: str):
        openclaw_dir = os.path.join(instance_dir, ".openclaw")
        
        env_path = os.path.join(openclaw_dir, ".env")
        if not os.path.exists(env_path):
            default_env = self._get_default_env()
            with open(env_path, "w") as f:
                for key, value in default_env.items():
                    f.write(f"{key}={value}\n")
        
        config_path = os.path.join(openclaw_dir, "openclaw.json")
        if not os.path.exists(config_path):
            default_config = self._get_default_openclaw_config()
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=2)
        
        workspace_dir = os.path.join(openclaw_dir, "workspace")
        os.makedirs(workspace_dir, exist_ok=True)
        
        memory_dir = os.path.join(openclaw_dir, "memory")
        os.makedirs(memory_dir, exist_ok=True)
        
        skills_dir = os.path.join(openclaw_dir, "skills")
        os.makedirs(skills_dir, exist_ok=True)
        
        logs_dir = os.path.join(openclaw_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
    
    def _get_default_env(self) -> dict:
        return {
            "OPENCLAW_HOME": "/root/.openclaw",
            "OPENCLAW_GATEWAY_PORT": "18987",
            "OPENCLAW_DISABLE_BONJOUR": "1",
            "OPENCLAW_GATEWAY_CONTROL_UI_ALLOWED_ORIGINS": "*",
            "AZURE_OPENAI_API_KEY": "",
            "AZURE_OPENAI_ENDPOINT": "",
            "AZURE_OPENAI_DEPLOYMENT": ""
        }
    
    def _get_default_openclaw_config(self) -> dict:
        return {
            "tools": {
                "exec": {
                    "security": "full",
                    "host": "host"
                },
                "file": {
                    "allowedDirectories": ["/root"]
                },
                "webFetch": {
                    "enabled": True
                }
            },
            "agents": {
                "defaults": {
                    "tools": {
                        "execAllowed": True,
                        "fileAllowed": True,
                        "webFetchAllowed": True
                    }
                }
            },
            "gateway": {
                "bind": "0.0.0.0",
                "port": 18987
            }
        }
    
    def load_config(self, instance_dir: str) -> dict:
        openclaw_dir = os.path.join(instance_dir, ".openclaw")
        
        env_vars = {}
        env_path = os.path.join(openclaw_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key] = value
        
        openclaw_json = {}
        config_path = os.path.join(openclaw_dir, "openclaw.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                openclaw_json = json.load(f)
        
        return {
            "env": env_vars,
            "openclaw": openclaw_json
        }
    
    def update_env_file(self, instance_dir: str, env_vars: dict):
        openclaw_dir = os.path.join(instance_dir, ".openclaw")
        env_path = os.path.join(openclaw_dir, ".env")
        
        existing_vars = {}
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        existing_vars[key] = value
        
        existing_vars.update(env_vars)
        
        with open(env_path, "w") as f:
            for key, value in existing_vars.items():
                f.write(f"{key}={value}\n")
    
    def update_openclaw_json(self, instance_dir: str, config: dict):
        openclaw_dir = os.path.join(instance_dir, ".openclaw")
        config_path = os.path.join(openclaw_dir, "openclaw.json")
        
        existing_config = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                existing_config = json.load(f)
        
        existing_config.update(config)
        
        with open(config_path, "w") as f:
            json.dump(existing_config, f, indent=2)
    
    def load_group_config(self, group_root_dir: str) -> dict:
        group_env_path = os.path.join(group_root_dir, ".env")
        group_config_path = os.path.join(group_root_dir, "openclaw.json")
        
        env_vars = {}
        if os.path.exists(group_env_path):
            with open(group_env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key] = value
        
        openclaw_json = {}
        if os.path.exists(group_config_path):
            with open(group_config_path, "r") as f:
                openclaw_json = json.load(f)
        
        return {
            "env": env_vars,
            "openclaw": openclaw_json
        }
    
    def update_group_env_file(self, group_root_dir: str, env_vars: dict):
        group_env_path = os.path.join(group_root_dir, ".env")
        
        existing_vars = {}
        if os.path.exists(group_env_path):
            with open(group_env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        existing_vars[key] = value
        
        existing_vars.update(env_vars)
        
        with open(group_env_path, "w") as f:
            for key, value in existing_vars.items():
                f.write(f"{key}={value}\n")
    
    def update_group_openclaw_json(self, group_root_dir: str, config: dict):
        group_config_path = os.path.join(group_root_dir, "openclaw.json")
        
        existing_config = {}
        if os.path.exists(group_config_path):
            with open(group_config_path, "r") as f:
                existing_config = json.load(f)
        
        existing_config.update(config)
        
        with open(group_config_path, "w") as f:
            json.dump(existing_config, f, indent=2)
    
    def export_instance(self, instance_id: str, instance_name: str, group_root_dir: str) -> str:
        instance_dir = os.path.join(group_root_dir, instance_name)
        export_root = os.path.join(self.data_dir, "exports")
        export_dir = os.path.join(export_root, instance_name)
        
        os.makedirs(export_dir, exist_ok=True)
        
        soul_files = [
            ".openclaw/openclaw.json",
            ".openclaw/workspace",
            ".openclaw/memory",
            ".openclaw/skills"
        ]
        
        soul_dir = os.path.join(export_dir, "soul")
        os.makedirs(soul_dir, exist_ok=True)
        
        for soul_file in soul_files:
            src = os.path.join(instance_dir, soul_file)
            if os.path.exists(src):
                dst = os.path.join(soul_dir, soul_file)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
        
        agents_src = os.path.join(instance_dir, ".openclaw", "agents")
        if os.path.exists(agents_src):
            agents_dst = os.path.join(soul_dir, "agents")
            shutil.copytree(agents_src, agents_dst, dirs_exist_ok=True)
        
        zip_path = os.path.join(export_root, f"{instance_name}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, export_dir)
                    zipf.write(file_path, arcname)
        
        shutil.rmtree(export_dir)
        
        return zip_path
    
    def import_instance(self, source_path: str, group_id: str, name: str, group_root_dir: str) -> dict:
        extract_dir = os.path.join(self.data_dir, "temp", f"import_{name}")
        instance_dir = os.path.join(group_root_dir, name)
        
        os.makedirs(extract_dir, exist_ok=True)
        os.makedirs(instance_dir, exist_ok=True)
        
        with zipfile.ZipFile(source_path, "r") as zipf:
            zipf.extractall(extract_dir)
        
        soul_dir = os.path.join(extract_dir, "soul")
        
        if os.path.exists(os.path.join(soul_dir, "openclaw.json")):
            dst_openclaw_dir = os.path.join(instance_dir, ".openclaw")
            os.makedirs(dst_openclaw_dir, exist_ok=True)
            
            src_config = os.path.join(soul_dir, "openclaw.json")
            dst_config = os.path.join(dst_openclaw_dir, "openclaw.json")
            shutil.copy2(src_config, dst_config)
        
        dirs_to_copy = ["workspace", "memory", "skills", "agents"]
        for dir_name in dirs_to_copy:
            src_dir = os.path.join(soul_dir, dir_name)
            if os.path.exists(src_dir):
                dst_dir = os.path.join(instance_dir, ".openclaw", dir_name)
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
        
        self.create_default_config(instance_dir)
        
        shutil.rmtree(extract_dir)
        
        return {"instance_name": name, "instance_dir": instance_dir, "message": "Instance imported successfully"}
    
    def export_group(self, group) -> str:
        export_root = os.path.join(self.data_dir, "exports")
        export_dir = os.path.join(export_root, f"group_{group.name}")
        
        os.makedirs(export_dir, exist_ok=True)
        
        group_config = {
            "name": group.name,
            "root_dir": group.root_dir,
            "docker_network": group.docker_network,
            "port_range_start": group.port_range_start,
            "port_range_end": group.port_range_end,
            "description": group.description
        }
        
        with open(os.path.join(export_dir, "group_config.json"), "w") as f:
            json.dump(group_config, f, indent=2)
        
        if os.path.exists(group.root_dir):
            for item in os.listdir(group.root_dir):
                item_path = os.path.join(group.root_dir, item)
                if os.path.isdir(item_path):
                    dst = os.path.join(export_dir, item)
                    shutil.copytree(item_path, dst, dirs_exist_ok=True)
        
        zip_path = os.path.join(export_root, f"group_{group.name}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, export_dir)
                    zipf.write(file_path, arcname)
        
        shutil.rmtree(export_dir)
        
        return zip_path
    
    def import_group(self, file_path: str) -> dict:
        extract_dir = os.path.join(self.data_dir, "temp", "import_group")
        
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(file_path, "r") as zipf:
            zipf.extractall(extract_dir)
        
        config_path = os.path.join(extract_dir, "group_config.json")
        if not os.path.exists(config_path):
            shutil.rmtree(extract_dir)
            raise Exception("Invalid group export file: missing group_config.json")
        
        with open(config_path, "r") as f:
            group_config = json.load(f)
        
        shutil.rmtree(extract_dir)
        
        return {
            "group_name": group_config.get("name"),
            "root_dir": group_config.get("root_dir"),
            "group_config": group_config,
            "message": f"群组配置已加载: {group_config.get('name')}"
        }
    
    def import_from_directory(self, source_dir: str, target_group_id: str, name: str, group_root_dir: str) -> dict:
        if not os.path.exists(source_dir):
            raise Exception(f"Source directory does not exist: {source_dir}")
        
        instance_dir = os.path.join(group_root_dir, name)
        os.makedirs(instance_dir, exist_ok=True)
        
        openclaw_dir = os.path.join(instance_dir, ".openclaw")
        os.makedirs(openclaw_dir, exist_ok=True)
        
        soul_files = {
            "openclaw.json": os.path.join(openclaw_dir, "openclaw.json"),
            "workspace": os.path.join(openclaw_dir, "workspace"),
            "memory": os.path.join(openclaw_dir, "memory"),
            "skills": os.path.join(openclaw_dir, "skills"),
            "agents": os.path.join(openclaw_dir, "agents")
        }
        
        for key, dst in soul_files.items():
            src = os.path.join(source_dir, key)
            if os.path.exists(src):
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
        
        self.create_default_config(instance_dir)
        
        return {
            "instance_name": name,
            "instance_dir": instance_dir,
            "message": "Instance imported from directory successfully"
        }
