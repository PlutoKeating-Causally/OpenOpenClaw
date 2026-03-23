import os
import json
import re
import shutil
import zipfile
import copy
from pathlib import Path
from typing import Dict, Optional

class ConfigManager:
    def __init__(self, docker_manager=None):
        self.data_dir = os.getenv("OPENCLAW_DATA_DIR", "./data")
        self.settings_file = os.path.join(self.data_dir, "settings.json")
        self.templates_file = os.path.join(self.data_dir, "templates.json")
        self.docker_manager = docker_manager
        self._init_default_settings()
        self._init_default_templates()
    
    def _init_default_settings(self):
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.settings_file):
            default_settings = {
                "docker_socket": "/var/run/docker.sock",
                "web_port": 8080,
                "data_root": self.data_dir,
                "default_image": "ghcr.io/openclaw/openclaw:latest",
                "gateway_password": ""
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
                        "GEMINI_API_KEY": ""
                    },
                    "deepseek": {
                        "DEEPSEEK_API_KEY": ""
                    },
                    "minimax": {
                        "MINIMAX_API_KEY": ""
                    },
                    "ollama": {
                        "OLLAMA_API_KEY": ""
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
                    "mistral": {
                        "MISTRAL_API_KEY": ""
                    },
                    "voyage": {
                        "VOYAGE_API_KEY": ""
                    },
                    "zai": {
                        "ZAI_API_KEY": ""
                    },
                    "cerebras": {
                        "CEREBRAS_API_KEY": ""
                    },
                    "together": {
                        "TOGETHER_API_KEY": ""
                    },
                    "moonshot": {
                        "MOONSHOT_API_KEY": ""
                    },
                    "kimi": {
                        "KIMI_API_KEY": ""
                    },
                    "venice": {
                        "VENICE_API_KEY": ""
                    },
                    "nvidia": {
                        "NVIDIA_API_KEY": ""
                    },
                    "synthetic": {
                        "SYNTHETIC_API_KEY": ""
                    },
                    "kilocode": {
                        "KILOCODE_API_KEY": ""
                    },
                    "ai_gateway": {
                        "AI_GATEWAY_API_KEY": ""
                    }
                },
                "channels": {
                    "telegram": {
                        "TELEGRAM_BOT_TOKEN": ""
                    },
                    "discord": {
                        "DISCORD_BOT_TOKEN": ""
                    },
                    "feishu": {
                        "FEISHU_APP_ID": "",
                        "FEISHU_APP_SECRET": ""
                    },
                    "slack": {
                        "SLACK_BOT_TOKEN": "",
                        "SLACK_APP_TOKEN": ""
                    },
                    "signal": {
                        "SIGNAL_PHONE_NUMBER": ""
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

    def _resolve_storage_path(self, path: str) -> str:
        expanded_path = os.path.expanduser(path)
        if os.path.isabs(expanded_path):
            return os.path.abspath(expanded_path)
        return os.path.abspath(os.path.join(self.data_dir, expanded_path))

    def _resolve_instance_dir(self, instance_dir: str) -> str:
        return self._resolve_storage_path(instance_dir)

    def _resolve_group_root_dir(self, group_root_dir: str) -> str:
        return self._resolve_storage_path(group_root_dir)
    
    def update_settings(self, settings: dict):
        os.makedirs(self.data_dir, exist_ok=True)
        persisted_settings = dict(settings)
        persisted_settings.pop("effective_data_dir", None)
        with open(self.settings_file, "w") as f:
            json.dump(persisted_settings, f, indent=2)
    
    def get_preset_templates(self) -> dict:
        if os.path.exists(self.templates_file):
            with open(self.templates_file, "r") as f:
                return json.load(f)
        return {}
    
    def save_templates(self, templates: dict):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.templates_file, "w") as f:
            json.dump(templates, f, indent=2)
    
    def create_default_config(self, instance_dir: str, gateway_port: int = 18789):
        instance_dir = self._resolve_instance_dir(instance_dir)
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
    
    def _get_default_env(self, gateway_port: int = 18789) -> dict:
        """Get default .env content using official OpenClaw environment variable names.
        
        Official env var reference: https://docs.openclaw.ai/help/environment
        Official provider list: https://docs.openclaw.ai/concepts/model-providers
        Official .env.example: https://github.com/openclaw/openclaw/blob/main/.env.example
        
        NOTE: All instances run as root inside Docker containers.
        Home directory is /root, config dir is /root/.openclaw.
        """
        return {
            # --- Gateway / paths (root user in Docker) ---
            "HOME": "/root",
            "OPENCLAW_HOME": "/root",
            "OPENCLAW_STATE_DIR": "/root/.openclaw",
            "OPENCLAW_CONFIG_DIR": "/root/.openclaw",
            "OPENCLAW_WORKSPACE_DIR": "/root/.openclaw/workspace",
            "OPENCLAW_GATEWAY_PORT": str(gateway_port),
            "OPENCLAW_GATEWAY_BIND": "lan",
            "OPENCLAW_DISABLE_BONJOUR": "1",
            "OPENCLAW_GATEWAY_CONTROL_UI_ALLOWED_ORIGINS": "*",
            # --- Gateway auth (password mode, global setting) ---
            "OPENCLAW_GATEWAY_PASSWORD": "",
            # --- Web search (Brave Search, group-level API key) ---
            "BRAVE_API_KEY": "",
            # --- Model provider API keys (official names) ---
            # Precedence: OPENCLAW_LIVE_<PROVIDER>_KEY > <PROVIDER>_API_KEYS > <PROVIDER>_API_KEY
            "OPENAI_API_KEY": "",
            "ANTHROPIC_API_KEY": "",
            "GEMINI_API_KEY": "",
            "OPENROUTER_API_KEY": "",
            "DEEPSEEK_API_KEY": "",
            "MINIMAX_API_KEY": "",
            "MISTRAL_API_KEY": "",
            "GROQ_API_KEY": "",
            "XAI_API_KEY": "",
            "HUGGINGFACE_HUB_TOKEN": "",
            "VOYAGE_API_KEY": "",
            "ZAI_API_KEY": "",
            "CEREBRAS_API_KEY": "",
            "TOGETHER_API_KEY": "",
            "MOONSHOT_API_KEY": "",
            "KIMI_API_KEY": "",
            "VENICE_API_KEY": "",
            "NVIDIA_API_KEY": "",
            "SYNTHETIC_API_KEY": "",
            "KILOCODE_API_KEY": "",
            "AI_GATEWAY_API_KEY": "",
            "OLLAMA_API_KEY": "",
        }
    
    def _get_default_openclaw_config(self, gateway_port: int = 18789) -> dict:
        import datetime
        now = datetime.datetime.utcnow().isoformat() + "Z"
        
        return {
            "env": {
                "vars": {},
                "shellEnv": {
                    "enabled": False,
                    "timeoutMs": 15000
                }
            },
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
                    "imageModel": {
                        "primary": ""
                    },
                    "imageGenerationModel": {
                        "primary": ""
                    },
                    "pdfModel": {
                        "primary": ""
                    },
                    "models": {},
                    "workspace": "/root/.openclaw/workspace",
                    "pdfMaxBytesMb": 10,
                    "pdfMaxPages": 20,
                    "thinkingDefault": "low",
                    "verboseDefault": "off",
                    "elevatedDefault": "on",
                    "timeoutSeconds": 600,
                    "mediaMaxMb": 5,
                    "contextTokens": 200000,
                    "maxConcurrent": 3
                }
            },
            "tools": {
                "profile": "full",
                "allow": [],
                "deny": [],
                "byProvider": {},
                "media": {},
                "web": {
                    "search": {
                        "enabled": True,
                        "maxResults": 5,
                        "timeoutSeconds": 30,
                        "cacheTtlMinutes": 15
                    },
                    "fetch": {
                        "enabled": True,
                        "maxChars": 50000,
                        "maxCharsCap": 50000,
                        "timeoutSeconds": 30,
                        "cacheTtlMinutes": 15
                    }
                },
                "agentToAgent": {
                    "enabled": True
                },
                "exec": {
                    "backgroundMs": 10000,
                    "timeoutSec": 1800,
                    "cleanupMs": 1800000,
                    "notifyOnExit": True,
                    "notifyOnExitEmptySuccess": False,
                    "host": "gateway",
                    "security": "full",
                    "ask": "off"
                },
                "elevated": {
                    "enabled": True,
                    "allowFrom": {}
                }
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
                    "enabled": True,
                    "basePath": "/openclaw",
                    "allowedOrigins": [
                        f"http://localhost:{gateway_port}",
                        f"http://127.0.0.1:{gateway_port}",
                        "http://localhost:8080",
                        "http://127.0.0.1:8080"
                    ]
                },
                "auth": {
                    "mode": "password",
                    "allowTailscale": True,
                    "rateLimit": {
                        "maxAttempts": 10,
                        "windowMs": 60000,
                        "lockoutMs": 300000,
                        "exemptLoopback": True
                    }
                },
                "tailscale": {
                    "mode": "off",
                    "resetOnExit": False
                },
                "tools": {
                    "deny": ["browser"],
                    "allow": ["gateway"]
                }
            },
            "skills": {
                "install": {
                    "nodeManager": "npm"
                },
                "entries": {}
            },
            "plugins": {
                "enabled": []
            },
            "model_knowledge": {
                "providers": [
                    {
                        "id": "openai",
                        "name": "OpenAI",
                        "models": ["gpt-5.4", "gpt-5.4-pro", "gpt-4o", "gpt-4o-mini", "o1", "o1-mini", "o3-mini"]
                    },
                    {
                        "id": "anthropic",
                        "name": "Anthropic",
                        "models": ["claude-opus-4-6", "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest"]
                    },
                    {
                        "id": "google",
                        "name": "Google Gemini",
                        "models": ["gemini-3.1-pro-preview", "gemini-3-flash-preview", "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
                    },
                    {
                        "id": "moonshot",
                        "name": "Moonshot AI (Kimi)",
                        "models": ["kimi-k2.5", "kimi-k2-0905-preview", "kimi-k2-turbo-preview", "kimi-k2-thinking", "kimi-k2-thinking-turbo"]
                    },
                    {
                        "id": "deepseek",
                        "name": "DeepSeek",
                        "models": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]
                    },
                    {
                        "id": "volcengine",
                        "name": "Volcano Engine (Doubao)",
                        "models": ["doubao-seed-1-8-251228", "doubao-seed-code-preview-251028", "kimi-k2-5-260127", "glm-4-7-251222", "deepseek-v3-2-251201"]
                    },
                    {
                        "id": "openrouter",
                        "name": "OpenRouter",
                        "models": ["anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-001", "deepseek/deepseek-chat", "meta-llama/llama-3.3-70b-instruct"]
                    },
                    {
                        "id": "ollama",
                        "name": "Ollama (Local)",
                        "models": ["llama3.3", "qwen2.5-coder", "deepseek-v3", "phi4"]
                    }
                ]
            }
        }

    def _enforce_docker_execution_policy(self, config: dict) -> dict:
        normalized = copy.deepcopy(config or {})

        tools = normalized.setdefault("tools", {})
        exec_config = tools.setdefault("exec", {})
        exec_config["host"] = "gateway"
        exec_config["security"] = "full"
        exec_config["ask"] = "off"

        tools.setdefault("media", {})

        env = normalized.setdefault("env", {})
        shell_env = env.setdefault("shellEnv", {})
        shell_env["enabled"] = False
        shell_env.setdefault("timeoutMs", 15000)

        agents = normalized.setdefault("agents", {})
        defaults = agents.setdefault("defaults", {})
        if "sandbox" in defaults:
            del defaults["sandbox"]

        if "sandbox" in normalized:
            del normalized["sandbox"]

        return normalized

    def get_default_config_bundle(self, gateway_port: int = 18789) -> dict:
        return {
            "env": self._get_default_env(gateway_port),
            "openclaw": self._enforce_docker_execution_policy(self._get_default_openclaw_config(gateway_port))
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
        2. Migrate /home/node paths to /root (root user Docker deployment)
        3. Add missing required sections
        4. Update version info
        5. Ensure gateway auth mode is password
        
        Args:
            config: The existing configuration dictionary
            target_version: Target schema version
            
        Returns:
            Updated configuration dictionary
        """
        # Step 1: Remove illegal fields that cause startup failures
        config = self._remove_illegal_config_fields(config)
        
        # Step 2: Migrate /home/node paths to /root for root user deployment
        config = self._migrate_paths_to_root(config)
        
        # Step 3: Ensure meta section exists
        if "meta" not in config:
            config["meta"] = {}
        
        # Step 4: Update version info
        import datetime
        config["meta"]["lastTouchedVersion"] = target_version
        config["meta"]["lastTouchedAt"] = datetime.datetime.utcnow().isoformat() + "Z"
        
        # Step 5: Ensure all required sections exist with defaults
        default_config = self._get_default_openclaw_config(config.get("gateway", {}).get("port", 18789))
        
        for key in default_config:
            if key not in config:
                config[key] = default_config[key]
            elif isinstance(default_config[key], dict) and isinstance(config[key], dict):
                # Deep merge for nested dicts
                self._deep_merge(config[key], default_config[key])
        
        # Step 6: Ensure gateway auth is password mode
        if "gateway" in config and isinstance(config["gateway"], dict):
            if "auth" not in config["gateway"]:
                config["gateway"]["auth"] = {}
            if config["gateway"]["auth"].get("mode") == "none":
                config["gateway"]["auth"]["mode"] = "password"
        
        return config
    
    def _migrate_paths_to_root(self, config: dict) -> dict:
        """Migrate all /home/node paths to /root for root user Docker deployment."""
        if "agents" in config and isinstance(config["agents"], dict):
            if "defaults" in config["agents"] and isinstance(config["agents"]["defaults"], dict):
                workspace = config["agents"]["defaults"].get("workspace", "")
                if isinstance(workspace, str) and "/home/node" in workspace:
                    config["agents"]["defaults"]["workspace"] = workspace.replace("/home/node", "/root")
        return config
    
    def _remove_illegal_config_fields(self, config: dict) -> dict:
        if "agents" in config and isinstance(config["agents"], dict):
            if "defaults" in config["agents"] and isinstance(config["agents"]["defaults"], dict):
                if "tools" in config["agents"]["defaults"]:
                    del config["agents"]["defaults"]["tools"]
        
        if "tools" in config and isinstance(config["tools"], dict):
            illegal_tool_fields = ["file", "webFetch"]
            for field in illegal_tool_fields:
                if field in config["tools"]:
                    del config["tools"][field]
        
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
            if "exec" in config["tools"] and isinstance(config["tools"]["exec"], dict):
                exec_host = config["tools"]["exec"].get("host")
                if exec_host and exec_host not in ["sandbox", "gateway", "node"]:
                    errors.append("tools.exec.host: Must be one of sandbox, gateway, node")
                exec_security = config["tools"]["exec"].get("security")
                if exec_security and exec_security not in ["deny", "allowlist", "full"]:
                    errors.append("tools.exec.security: Must be one of deny, allowlist, full")
                exec_ask = config["tools"]["exec"].get("ask")
                if exec_ask and exec_ask not in ["off", "on-miss", "always"]:
                    errors.append("tools.exec.ask: Must be one of off, on-miss, always")
        
        # Check required sections
        required_sections = ["meta", "gateway", "agents", "tools"]
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        # Check gateway port
        if "gateway" in config:
            if "port" not in config["gateway"]:
                warnings.append("gateway.port: Not specified, will use default")
            # Check gateway auth mode
            auth_mode = config.get("gateway", {}).get("auth", {}).get("mode", "")
            if auth_mode == "none":
                warnings.append("gateway.auth.mode: 'none' is insecure for LAN-bound gateway. Use 'password' instead.")
        
        # Check for legacy /home/node paths (should be /root)
        workspace = config.get("agents", {}).get("defaults", {}).get("workspace", "")
        if isinstance(workspace, str) and "/home/node" in workspace:
            warnings.append("agents.defaults.workspace: Contains /home/node path. Should be /root for root user deployment.")
        
        # Check tools profile
        tools_profile = config.get("tools", {}).get("profile", "")
        if tools_profile and tools_profile != "full":
            warnings.append(f"tools.profile: '{tools_profile}' does not provide full LLM capabilities. Use 'full' for complete access.")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def update_gateway_port(self, instance_dir: str, gateway_port: int, host_port: int = None, old_port: int = None, container_name: str = None):
        """Update the gateway port in both .env and openclaw.json for an instance."""
        instance_dir = self._resolve_instance_dir(instance_dir)
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
            env_content = "".join(lines)
            # Parse into dict for _write_env_file
            env_vars = {}
            for line in lines:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_vars[key] = value
            self._write_env_file(env_path, env_vars, container_name=container_name)
        
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
                    f"http://127.0.0.1:{host_port}"
                ]
            
            self._write_json_file(config_path, config, container_name=container_name)

    def sync_allowed_origins(self, instance_dir: str, container_port: int, host_port: int, container_name: str = None):
        """Synchronize allowedOrigins within openclaw.json strictly following user requirements."""
        self.update_gateway_port(instance_dir, container_port, host_port=host_port, container_name=container_name)

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
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def _write_env_file(self, env_path: str, env_vars: dict, container_name: str = None):
        """Write env file, with fallback to writing via Docker if file is owned by container."""
        os.makedirs(os.path.dirname(env_path), exist_ok=True)
        content = "\n".join(f"{k}={v}" for k, v in env_vars.items())
        
        # Try normal write first
        try:
            if os.path.exists(env_path):
                try:
                    os.chmod(env_path, 0o644)
                except (OSError, PermissionError):
                    pass
            with open(env_path, "w") as f:
                f.write(content)
            return
        except PermissionError:
            pass  # Fall through to Docker fallback
        
        # Try Docker fallback if available
        if self.docker_manager and container_name:
            # Convert host path to container path (container sees /root for its bind mount)
            container_path = env_path.replace(self.data_dir, "/root")
            try:
                if self.docker_manager.write_file_in_container(container_name, container_path, content):
                    return
            except Exception as e:
                print(f"Docker fallback failed: {e}")
        
        # If we get here, all methods failed
        raise PermissionError(
            f"Cannot write to {env_path}. The file is owned by a Docker container user. "
            f"Solutions: (1) Stop the container and run: sudo chown -R $(whoami) {os.path.dirname(os.path.dirname(env_path))} "
            f"(2) Or edit config inside the container directly"
        )

    def _write_json_file(self, file_path: str, payload: dict, container_name: str = None):
        """Write JSON file, with fallback to writing via Docker if file is owned by container."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        content = json.dumps(payload, indent=2)
        
        # Try normal write first
        try:
            if os.path.exists(file_path):
                try:
                    os.chmod(file_path, 0o644)
                except (OSError, PermissionError):
                    pass
            with open(file_path, "w") as f:
                f.write(content)
            return
        except PermissionError:
            pass  # Fall through to Docker fallback
        
        # Try Docker fallback if available
        if self.docker_manager and container_name:
            # Convert host path to container path (container sees /root for its bind mount)
            container_path = file_path.replace(self.data_dir, "/root")
            try:
                if self.docker_manager.write_file_in_container(container_name, container_path, content):
                    return
            except Exception as e:
                print(f"Docker fallback failed: {e}")
        
        # If we get here, all methods failed
        raise PermissionError(
            f"Cannot write to {file_path}. The file is owned by a Docker container user. "
            f"Solutions: (1) Stop the container and run: sudo chown -R $(whoami) {os.path.dirname(file_path)} "
            f"(2) Or edit config inside the container directly"
        )

    
    def load_config(self, instance_dir: str) -> dict:
        instance_dir = self._resolve_instance_dir(instance_dir)
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
    
    def update_env_file(self, instance_dir: str, env_vars: dict, replace: bool = True, container_name: str = None):
        instance_dir = self._resolve_instance_dir(instance_dir)
        openclaw_dir = os.path.join(instance_dir, ".openclaw")
        env_path = os.path.join(openclaw_dir, ".env")
        if replace:
            self._write_env_file(env_path, env_vars, container_name=container_name)
            return

        existing_vars = {}
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        existing_vars[key] = value

        existing_vars.update(env_vars)
        self._write_env_file(env_path, existing_vars, container_name=container_name)

    def update_openclaw_json(self, instance_dir: str, config: dict, replace: bool = True, container_name: str = None):
        instance_dir = self._resolve_instance_dir(instance_dir)
        openclaw_dir = os.path.join(instance_dir, ".openclaw")
        config_path = os.path.join(openclaw_dir, "openclaw.json")
        if replace:
            self._write_json_file(config_path, self._enforce_docker_execution_policy(config), container_name=container_name)
            return

        existing_config = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                existing_config = json.load(f)

        self._deep_merge(existing_config, config)
        existing_config = self._enforce_docker_execution_policy(existing_config)
        self._write_json_file(config_path, existing_config, container_name=container_name)
    
    def load_group_config(self, group_root_dir: str) -> dict:
        group_root_dir = self._resolve_group_root_dir(group_root_dir)
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
    
    def update_group_env_file(self, group_root_dir: str, env_vars: dict, replace: bool = True, container_name: str = None):
        group_root_dir = self._resolve_group_root_dir(group_root_dir)
        group_env_path = os.path.join(group_root_dir, ".env")
        if replace:
            self._write_env_file(group_env_path, env_vars, container_name=container_name)
            return

        existing_vars = {}
        if os.path.exists(group_env_path):
            with open(group_env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        existing_vars[key] = value

        existing_vars.update(env_vars)
        self._write_env_file(group_env_path, existing_vars, container_name=container_name)

    def update_group_openclaw_json(self, group_root_dir: str, config: dict, replace: bool = True, container_name: str = None):
        group_root_dir = self._resolve_group_root_dir(group_root_dir)
        group_config_path = os.path.join(group_root_dir, "openclaw.json")
        if replace:
            self._write_json_file(group_config_path, self._enforce_docker_execution_policy(config), container_name=container_name)
            return

        existing_config = {}
        if os.path.exists(group_config_path):
            with open(group_config_path, "r") as f:
                existing_config = json.load(f)

        self._deep_merge(existing_config, config)
        existing_config = self._enforce_docker_execution_policy(existing_config)
        self._write_json_file(group_config_path, existing_config, container_name=container_name)
    
    def export_instance(self, instance_id: str, instance_name: str, group_root_dir: str) -> str:
        group_root_dir = self._resolve_group_root_dir(group_root_dir)
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
        from datetime import datetime
        extract_dir = os.path.join(self.data_dir, "temp", f"import_{name}_{int(datetime.now().timestamp())}")
        group_root_dir = self._resolve_group_root_dir(group_root_dir)
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
        group_root_dir = self._resolve_group_root_dir(group.root_dir)
        
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
        
        if os.path.exists(group_root_dir):
            for item in os.listdir(group_root_dir):
                item_path = os.path.join(group_root_dir, item)
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
        
        group_root_dir = self._resolve_group_root_dir(group_root_dir)
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
