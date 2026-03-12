import os
import json
import re
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
    
    def create_default_config(self, instance_dir: str, gateway_port: int = 18987):
        openclaw_dir = os.path.join(instance_dir, ".openclaw")
        os.makedirs(openclaw_dir, exist_ok=True)
        
        env_path = os.path.join(openclaw_dir, ".env")
        if not os.path.exists(env_path):
            default_env = self._get_default_env(gateway_port)
            with open(env_path, "w") as f:
                for key, value in default_env.items():
                    f.write(f"{key}={value}\n")
        
        config_path = os.path.join(openclaw_dir, "openclaw.json")
        if not os.path.exists(config_path):
            default_config = self._get_default_openclaw_config(gateway_port)
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
    
    def _get_default_env(self, gateway_port: int = 18987) -> dict:
        return {
            "OPENCLAW_HOME": "/root",
            "OPENCLAW_DATA_DIR": "/root/.openclaw",
            "OPENCLAW_GATEWAY_PORT": str(gateway_port),
            "OPENCLAW_DISABLE_BONJOUR": "1",
            "OPENCLAW_GATEWAY_CONTROL_UI_ALLOWED_ORIGINS": "*",
            "OPENAI_API_KEY": "",
            "GOOGLE_GENERATIVE_AI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "DEEPSEEK_API_KEY": "",
            "MINIMAX_API_KEY": "",
            "VOYAGE_API_KEY": "",
            "MISTRAL_API_KEY": "",
            "AZURE_OPENAI_API_KEY": "",
            "AZURE_OPENAI_ENDPOINT": "",
            "AZURE_OPENAI_DEPLOYMENT": ""
        }
    
    def _get_default_openclaw_config(self, gateway_port: int = 18987) -> dict:
        """Get the latest default openclaw.json configuration based on OpenClaw official schema.
        
        IMPORTANT: This configuration follows strict OpenClaw 2026.3.2 specification.
        DO NOT add fields that are not in the official schema, or the instance will fail to start.
        
        Forbidden fields (will cause startup failure):
        - agents.defaults.tools
        - tools.file
        - tools.webFetch
        - tools.exec.host/security (wrong location)
        
        Valid configuration sections:
        - Meta information
        - Wizard configuration
        - Authentication profiles
        - Model providers
        - Agent defaults (model, models, workspace ONLY)
        - Tools configuration (profile, web.search/fetch, agentToAgent ONLY)
        - Commands settings
        - Session management
        - Hooks configuration
        - Channels (Telegram, Feishu)
        - Gateway settings with proper CORS
        - Skills configuration
        - Plugins management
        """
        import datetime
        now = datetime.datetime.utcnow().isoformat() + "Z"
        
        return {
            "meta": {
                "lastTouchedVersion": "2026.3.2",
                "lastTouchedAt": now
            },
            "wizard": {
                "lastRunAt": now,
                "lastRunVersion": "2026.3.2",
                "lastRunCommand": "configure",
                "lastRunMode": "local"
            },
            "auth": {
                "profiles": {}
            },
            "models": {
                "mode": "merge",
                "providers": {}
            },
            "agents": {
                "defaults": {
                    "model": {
                        "primary": ""
                    },
                    "models": {},
                    "workspace": "/root/.openclaw/workspace"
                    # NOTE: Do NOT add "tools" here - it's not allowed in agents.defaults
                }
            },
            "tools": {
                "profile": "full",
                "web": {
                    "search": {
                        "enabled": True,
                        "apiKey": ""
                    },
                    "fetch": {
                        "enabled": True
                    }
                },
                "agentToAgent": {
                    "enabled": True
                }
                # NOTE: Do NOT add "file", "webFetch", or "exec" here
                # These are not valid fields in OpenClaw 2026.3.2
            },
            "commands": {
                "native": "auto",
                "nativeSkills": "auto",
                "restart": True,
                "ownerDisplay": "raw"
            },
            "session": {
                "dmScope": "per-channel-peer"
            },
            "hooks": {
                "internal": {
                    "enabled": True,
                    "entries": {
                        "boot-md": {
                            "enabled": True
                        },
                        "bootstrap-extra-files": {
                            "enabled": True
                        },
                        "command-logger": {
                            "enabled": True
                        },
                        "session-memory": {
                            "enabled": True
                        }
                    }
                }
            },
            "channels": {
                "telegram": {
                    "enabled": False,
                    "dmPolicy": "pairing",
                    "botToken": "",
                    "groupPolicy": "open",
                    "streaming": "partial"
                },
                "feishu": {
                    "enabled": False,
                    "appId": "",
                    "appSecret": "",
                    "connectionMode": "websocket",
                    "domain": "feishu",
                    "groupPolicy": "open"
                }
            },
            "gateway": {
                "port": gateway_port,
                "mode": "local",
                "bind": "lan",
                "controlUi": {
                    "allowedOrigins": [
                        f"http://localhost:{gateway_port}",
                        f"http://127.0.0.1:{gateway_port}",
                        "http://localhost:8080",
                        "http://127.0.0.1:8080"
                    ]
                },
                "auth": {
                    "mode": "password",
                    "password": ""
                },
                "tailscale": {
                    "mode": "off",
                    "resetOnExit": False
                },
                "nodes": {
                    "denyCommands": [
                        "camera.snap",
                        "camera.clip",
                        "screen.record",
                        "contacts.add",
                        "calendar.add",
                        "reminders.add",
                        "sms.send"
                    ]
                }
            },
            "skills": {
                "install": {
                    "nodeManager": "npm"
                },
                "entries": {}
            },
            "plugins": {
                "entries": {},
                "installs": {}
            }
        }
    
    def check_latest_config_schema(self) -> dict:
        """Check and fetch the latest OpenClaw configuration schema from official sources.
        
        Returns:
            dict containing:
                - latest_version: str
                - schema_url: str
                - changelog: str
                - update_available: bool
                - current_version: str
        """
        import urllib.request
        import urllib.error
        
        result = {
            "latest_version": "2026.3.2",
            "schema_url": "https://github.com/openclaw/openclaw/releases",
            "changelog": "",
            "update_available": False,
            "current_version": "2026.3.2",
            "error": None
        }
        
        try:
            # Try to fetch latest release info from GitHub API
            req = urllib.request.Request(
                "https://api.github.com/repos/openclaw/openclaw/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "OpenOpenClaw-Manager"}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                latest_tag = data.get('tag_name', '').lstrip('v')
                result['latest_version'] = latest_tag or result['latest_version']
                result['changelog'] = data.get('body', '')
                
                # Compare versions (simple string comparison for now)
                if latest_tag and latest_tag != result['current_version']:
                    result['update_available'] = True
                    
        except urllib.error.HTTPError as e:
            result['error'] = f"HTTP {e.code}: Unable to fetch latest version"
        except urllib.error.URLError as e:
            result['error'] = f"Network error: {str(e.reason)}"
        except Exception as e:
            result['error'] = f"Error checking updates: {str(e)}"
        
        return result
    
    def migrate_config_to_latest(self, config: dict, target_version: str = "2026.3.2") -> dict:
        """Migrate an existing configuration to the latest schema version.
        
        This method will:
        1. Remove illegal fields that cause startup failures
        2. Add missing required sections
        3. Update version info
        
        Args:
            config: The existing configuration dictionary
            target_version: Target schema version
            
        Returns:
            Updated configuration dictionary
        """
        # Step 1: Remove illegal fields that cause startup failures
        config = self._remove_illegal_config_fields(config)
        
        # Step 2: Ensure meta section exists
        if "meta" not in config:
            config["meta"] = {}
        
        # Step 3: Update version info
        import datetime
        config["meta"]["lastTouchedVersion"] = target_version
        config["meta"]["lastTouchedAt"] = datetime.datetime.utcnow().isoformat() + "Z"
        
        # Step 4: Ensure all required sections exist with defaults
        default_config = self._get_default_openclaw_config(config.get("gateway", {}).get("port", 18987))
        
        for key in default_config:
            if key not in config:
                config[key] = default_config[key]
            elif isinstance(default_config[key], dict) and isinstance(config[key], dict):
                # Deep merge for nested dicts
                self._deep_merge(config[key], default_config[key])
        
        return config
    
    def _remove_illegal_config_fields(self, config: dict) -> dict:
        """Remove illegal fields that cause OpenClaw startup failures.
        
        Illegal fields found in production:
        - agents.defaults.tools
        - tools.file
        - tools.webFetch
        - tools.exec (with host/security)
        """
        # Remove agents.defaults.tools
        if "agents" in config and isinstance(config["agents"], dict):
            if "defaults" in config["agents"] and isinstance(config["agents"]["defaults"], dict):
                if "tools" in config["agents"]["defaults"]:
                    del config["agents"]["defaults"]["tools"]
        
        # Remove illegal fields from tools
        if "tools" in config and isinstance(config["tools"], dict):
            illegal_tool_fields = ["file", "webFetch"]
            for field in illegal_tool_fields:
                if field in config["tools"]:
                    del config["tools"][field]
            
            # Remove tools.exec if it has host/security (these belong elsewhere)
            if "exec" in config["tools"] and isinstance(config["tools"]["exec"], dict):
                # exec with host/security is wrong location, remove it
                if "host" in config["tools"]["exec"] or "security" in config["tools"]["exec"]:
                    del config["tools"]["exec"]
        
        return config
    
    def validate_config(self, config: dict) -> dict:
        """Validate configuration and return validation report.
        
        Returns:
            dict with validation results:
                - valid: bool
                - errors: list of error messages
                - warnings: list of warning messages
        """
        errors = []
        warnings = []
        
        # Check for illegal fields
        if "agents" in config and isinstance(config["agents"], dict):
            if "defaults" in config["agents"] and isinstance(config["agents"]["defaults"], dict):
                if "tools" in config["agents"]["defaults"]:
                    errors.append("agents.defaults.tools: Illegal field, will cause startup failure")
        
        if "tools" in config and isinstance(config["tools"], dict):
            if "file" in config["tools"]:
                errors.append("tools.file: Illegal field, use tools.fileEdit or remove")
            if "webFetch" in config["tools"]:
                errors.append("tools.webFetch: Illegal field, use tools.web.fetch instead")
            if "exec" in config["tools"]:
                errors.append("tools.exec: Wrong location, move to top-level or remove")
        
        # Check required sections
        required_sections = ["meta", "gateway", "agents", "tools"]
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        # Check gateway port
        if "gateway" in config:
            if "port" not in config["gateway"]:
                warnings.append("gateway.port: Not specified, will use default")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def update_gateway_port(self, instance_dir: str, gateway_port: int, host_port: int = None, old_port: int = None):
        """Update the gateway port in both .env and openclaw.json for an instance."""
        openclaw_dir = os.path.join(instance_dir, ".openclaw")
        
        # Update .env file
        env_path = os.path.join(openclaw_dir, ".env")
        if os.path.exists(env_path):
            lines = []
            found = False
            with open(env_path, "r") as f:
                for line in f:
                    if line.strip().startswith("OPENCLAW_GATEWAY_PORT="):
                        lines.append(f"OPENCLAW_GATEWAY_PORT={gateway_port}\n")
                        found = True
                    else:
                        lines.append(line)
            if not found:
                lines.append(f"OPENCLAW_GATEWAY_PORT={gateway_port}\n")
            with open(env_path, "w") as f:
                f.writelines(lines)
        
        # Update openclaw.json strictly following user requirements
        config_path = os.path.join(openclaw_dir, "openclaw.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
            
            if "gateway" not in config:
                config["gateway"] = {}
            
            config["gateway"]["port"] = gateway_port
            config["gateway"]["bind"] = config["gateway"].get("bind", "lan")
            
            # Apply strict allowedOrigins if host_port is available
            if host_port:
                # Handle both controlUI and controlUi casing
                control_key = "controlUi"
                for key in ["controlUI", "controlUi"]:
                    if key in config["gateway"]:
                        control_key = key
                        break
                
                if control_key not in config["gateway"]:
                    config["gateway"][control_key] = {}
                
                config["gateway"][control_key]["allowedOrigins"] = [
                    f"http://localhost:{gateway_port}",
                    f"http://127.0.0.1:{gateway_port}",
                    f"http://localhost:{host_port}",
                    f"http://127.0.0.1:{host_port}",
                    f"http://192.168.13.13:{host_port}"
                ]
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

    def sync_allowed_origins(self, instance_dir: str, container_port: int, host_port: int):
        """Synchronize allowedOrigins within openclaw.json strictly following user requirements."""
        self.update_gateway_port(instance_dir, container_port, host_port=host_port)

    def _sync_origins_in_dict(self, config: dict, old_port: int, new_port: int) -> dict:
        if "gateway" not in config:
            return config
            
        # Handle both controlUI and controlUi casing
        control_key = None
        for key in ["controlUI", "controlUi"]:
            if key in config["gateway"]:
                control_key = key
                break
        
        if control_key:
            origins = config["gateway"][control_key].get("allowedOrigins")
            if isinstance(origins, list):
                new_origins = []
                # Use regex to match exact port (ensure :port is followed by non-digit)
                pattern = f":{old_port}(?![0-9])"
                replacement = f":{new_port}"
                for origin in origins:
                    if isinstance(origin, str):
                        new_origins.append(re.sub(pattern, replacement, origin))
                    else:
                        new_origins.append(origin)
                config["gateway"][control_key]["allowedOrigins"] = new_origins
        return config

    def _deep_merge(self, base: dict, update: dict) -> dict:
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    
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
        
        self._deep_merge(existing_config, config)
        
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
        
        self._deep_merge(existing_config, config)
        
        with open(group_config_path, "w") as f:
            json.dump(existing_config, f, indent=2)
    
    def export_instance(self, instance_id: str, instance_name: str, group_root_dir: str) -> str:
        instance_dir = os.path.join(group_root_dir, instance_name)
        export_root = os.path.join(self.data_dir, "exports")
        os.makedirs(export_root, exist_ok=True)
        
        zip_path = os.path.join(export_root, f"{instance_name}.zip")
        
        # Package the entire instance directory (maps to /root)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(instance_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, instance_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def import_instance(self, source_path: str, group_id: str, name: str, group_root_dir: str) -> dict:
        extract_dir = os.path.join(self.data_dir, "temp", f"import_{name}_{int(datetime.now().timestamp())}")
        instance_dir = os.path.join(group_root_dir, name)
        
        # Clear destination to avoid Errno 17 (File exists) on retries/overwrites
        if os.path.exists(instance_dir):
            shutil.rmtree(instance_dir, ignore_errors=True)
            
        os.makedirs(extract_dir, exist_ok=True)
        os.makedirs(instance_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(source_path, "r") as zipf:
                zipf.extractall(extract_dir)
            
            # Legacy Compatibility: If there is a 'soul' folder, promote its contents
            soul_dir = os.path.join(extract_dir, "soul")
            if os.path.exists(soul_dir) and os.path.isdir(soul_dir):
                # Check for nested .openclaw in soul (legacy structure)
                legacy_openclaw = os.path.join(soul_dir, ".openclaw")
                if os.path.exists(legacy_openclaw):
                    # Move everything from soul/.openclaw to instance_dir/.openclaw
                    shutil.copytree(legacy_openclaw, os.path.join(instance_dir, ".openclaw"), symlinks=True, ignore_dangling_symlinks=True, dirs_exist_ok=True)
                
                # Move everything else from soul to instance_dir
                for item in os.listdir(soul_dir):
                    if item == ".openclaw": continue
                    src = os.path.join(soul_dir, item)
                    dst = os.path.join(instance_dir, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, symlinks=True, ignore_dangling_symlinks=True, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
            else:
                # Normal Import: Copy everything from extract_dir to instance_dir
                shutil.copytree(extract_dir, instance_dir, symlinks=True, ignore_dangling_symlinks=True, dirs_exist_ok=True)
            
            # Ensure basic required configs exist
            self.create_default_config(instance_dir)
            
        finally:
            if os.path.exists(extract_dir):
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
        
        # Clear destination to avoid Errno 17 (File exists) on retries/overwrites
        if os.path.exists(instance_dir):
            shutil.rmtree(instance_dir, ignore_errors=True)
            
        os.makedirs(instance_dir, exist_ok=True)
        
        # Perform full copy from source to instance_dir (maps to /root)
        shutil.copytree(source_dir, instance_dir, symlinks=True, ignore_dangling_symlinks=True, dirs_exist_ok=True)
        
        # Ensure it has basic environment and config
        self.create_default_config(instance_dir)
        
        return {
            "instance_name": name,
            "instance_dir": instance_dir,
            "message": "Instance imported from directory successfully"
        }
