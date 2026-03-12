#!/usr/bin/env python3
"""
OpenOpenClaw 初始化脚本

这个脚本帮助用户：
1. 检查系统环境（Python、Node.js、Docker）
2. 安装后端依赖
3. 构建前端
4. 初始化数据库
5. 启动服务
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_step(msg):
    print(f"\n{Colors.BLUE}▶ {msg}{Colors.END}")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Command failed: {cmd}")
            print_error(f"Error: {e.stderr}")
            sys.exit(1)
        return e

def check_python():
    """Check Python version"""
    print_step("检查 Python 环境...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error("需要 Python 3.8+，当前版本: {}.{}.{}".format(version.major, version.minor, version.micro))
        sys.exit(1)
    print_success(f"Python {version.major}.{version.minor}.{version.micro} ✓")

def check_nodejs():
    """Check Node.js version"""
    print_step("检查 Node.js 环境...")
    result = run_command("node --version", check=False)
    if result.returncode != 0:
        print_error("Node.js 未安装，请先安装 Node.js 18+")
        print_error("下载地址: https://nodejs.org/")
        sys.exit(1)
    
    version_str = result.stdout.strip().lstrip('v')
    major_version = int(version_str.split('.')[0])
    if major_version < 18:
        print_error(f"需要 Node.js 18+，当前版本: {version_str}")
        sys.exit(1)
    print_success(f"Node.js {version_str} ✓")

def check_docker():
    """Check Docker installation"""
    print_step("检查 Docker 环境...")
    result = run_command("docker --version", check=False)
    if result.returncode != 0:
        print_error("Docker 未安装或未启动")
        print_error("请安装 Docker Desktop: https://www.docker.com/products/docker-desktop")
        sys.exit(1)
    
    # Check if Docker daemon is running
    result = run_command("docker ps", check=False)
    if result.returncode != 0:
        print_error("Docker 守护进程未运行，请启动 Docker")
        sys.exit(1)
    
    print_success("Docker 已安装并运行 ✓")

def install_backend_deps():
    """Install Python dependencies"""
    print_step("安装后端依赖...")
    backend_dir = Path(__file__).parent / "backend"
    
    # Check if virtual environment exists
    venv_path = backend_dir / "venv"
    if not venv_path.exists():
        print_step("创建 Python 虚拟环境...")
        run_command(f"{sys.executable} -m venv venv", cwd=backend_dir)
    
    # Determine pip path
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:  # Unix/Linux/macOS
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    # Install requirements
    run_command(f"{pip_path} install -r requirements.txt", cwd=backend_dir)
    print_success("后端依赖安装完成 ✓")
    
    return str(python_path)

def build_frontend():
    """Build frontend"""
    print_step("构建前端...")
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Install npm dependencies
    if not (frontend_dir / "node_modules").exists():
        print_step("安装 NPM 依赖...")
        run_command("npm install", cwd=frontend_dir)
    
    # Build production
    print_step("构建生产版本...")
    run_command("npm run build", cwd=frontend_dir)
    print_success("前端构建完成 ✓")

def init_database(python_path):
    """Initialize database"""
    print_step("初始化数据库...")
    backend_dir = Path(__file__).parent / "backend"
    
    # Set data directory
    data_dir = Path(__file__).parent / "data"
    os.environ["OPENCLAW_DATA_DIR"] = str(data_dir)
    
    # Create data directory
    data_dir.mkdir(exist_ok=True)
    
    # Initialize database by importing models
    result = run_command(
        f'{python_path} -c "from models import init_db; init_db(); print(\'Database initialized\')"',
        cwd=backend_dir
    )
    print_success("数据库初始化完成 ✓")

def create_default_configs():
    """Create default configuration files"""
    print_step("创建默认配置文件...")
    data_dir = Path(__file__).parent / "data"
    
    # Create settings.json if not exists
    settings_file = data_dir / "settings.json"
    if not settings_file.exists():
        import json
        default_settings = {
            "docker_socket": "/var/run/docker.sock",
            "web_port": 8080,
            "data_root": str(data_dir),
            "default_image": "openclaw/openclaw:latest",
            "docker_mirror": ""
        }
        with open(settings_file, 'w') as f:
            json.dump(default_settings, f, indent=2)
        print_success("创建设置文件 ✓")
    
    # Create templates.json if not exists
    templates_file = data_dir / "templates.json"
    if not templates_file.exists():
        import json
        default_templates = {
            "byok": {
                "openai": {"OPENAI_API_KEY": ""},
                "anthropic": {"ANTHROPIC_API_KEY": ""},
                "google": {"GOOGLE_GENERATIVE_AI_API_KEY": ""},
                "azure": {
                    "AZURE_OPENAI_API_KEY": "",
                    "AZURE_OPENAI_ENDPOINT": "",
                    "AZURE_OPENAI_DEPLOYMENT": ""
                },
                "deepseek": {"DEEPSEEK_API_KEY": ""},
                "minimax": {"MINIMAX_API_KEY": ""},
                "ollama": {"OLLAMA_BASE_URL": "http://localhost:11434"},
                "openrouter": {"OPENROUTER_API_KEY": ""},
                "huggingface": {"HUGGINGFACE_HUB_TOKEN": ""},
                "groq": {"GROQ_API_KEY": ""},
                "xai": {"XAI_API_KEY": ""},
                "cohere": {"COHERE_API_KEY": ""},
                "mistral": {"MISTRAL_API_KEY": ""},
                "voyage": {"VOYAGE_API_KEY": ""}
            },
            "channels": {
                "telegram": {"TELEGRAM_BOT_TOKEN": ""},
                "discord": {
                    "DISCORD_BOT_TOKEN": "",
                    "DISCORD_GUILD_ID": "",
                    "DISCORD_USER_ID": ""
                },
                "feishu": {
                    "FEISHU_APP_ID": "",
                    "FEISHU_APP_SECRET": ""
                },
                "whatsapp": {"WHATSAPP_SESSION_PATH": "/root/.openclaw/credentials/whatsapp"},
                "slack": {
                    "SLACK_BOT_TOKEN": "",
                    "SLACK_TEAM_ID": ""
                },
                "signal": {"SIGNAL电话号码": ""}
            }
        }
        with open(templates_file, 'w') as f:
            json.dump(default_templates, f, indent=2)
        print_success("创建模板文件 ✓")

def start_server(python_path):
    """Start the server"""
    print_step("启动 OpenOpenClaw 服务...")
    backend_dir = Path(__file__).parent / "backend"
    data_dir = Path(__file__).parent / "data"
    
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}  OpenOpenClaw 启动成功！{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"\n  访问地址: http://localhost:8080")
    print(f"  数据目录: {data_dir}")
    print(f"\n  按 Ctrl+C 停止服务")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
    
    # Start server
    try:
        os.environ["OPENCLAW_DATA_DIR"] = str(data_dir)
        subprocess.run(
            [python_path, "main.py"],
            cwd=backend_dir,
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n服务已停止")
        sys.exit(0)

def main():
    """Main initialization flow"""
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}  OpenOpenClaw 初始化脚本{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    
    # Check environment
    check_python()
    check_nodejs()
    check_docker()
    
    # Setup
    python_path = install_backend_deps()
    build_frontend()
    init_database(python_path)
    create_default_configs()
    
    # Start server
    start_server(python_path)

if __name__ == "__main__":
    main()
