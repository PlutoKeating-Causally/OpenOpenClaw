# OpenClaw Manager 快速入门指南

一份详细的上手指南，帮助你快速部署和使用 OpenClaw Manager 多实例管理系统。

---

## 目录

1. [环境配置](#1-环境配置)
2. [安装部署](#2-安装部署)
3. [快速开始](#3-快速开始)
4. [功能详解](#4-功能详解)
5. [配置说明](#5-配置说明)
6. [常见问题](#6-常见问题)

---

## 1. 环境配置

### 1.1 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | macOS / Linux / Windows | macOS (Apple Silicon/Intel) / Ubuntu 20.04+ |
| CPU | 2 核心 | 4 核心或更多 |
| 内存 | 4 GB | 8 GB 或更多 |
| 磁盘空间 | 20 GB | 50 GB 或更多 |
| Docker | Docker Engine 20.10+ | Docker Desktop 最新版 |

### 1.2 安装 Docker

#### macOS

推荐使用 Docker Desktop：

```bash
# 使用 Homebrew 安装
brew install --cask docker

# 或从官网下载：https://www.docker.com/products/docker-desktop
```

#### Linux (Ubuntu/Debian)

```bash
# 更新软件包索引
sudo apt update

# 安装依赖
sudo apt install -y ca-certificates curl gnupg lsb-release

# 添加 Docker GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker APT 源
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户加入 docker 组（可选）
sudo usermod -aG docker $USER
```

#### Linux (CentOS/RHEL)

```bash
# 安装依赖
sudo yum install -y yum-utils

# 添加 Docker 源
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### Windows

推荐使用 Docker Desktop：

1. 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. 启动 Docker Desktop
3. 确保 WSL2 后端已启用（Hyper-V 也可）

### 1.3 安装 Python (后端)

#### macOS / Linux

```bash
# 检查 Python 版本
python3 --version

# 推荐 Python 3.8+
# 如未安装，使用包管理器安装
# macOS
brew install python3

# Ubuntu/Debian
sudo apt install -y python3 python3-pip
```

#### Windows

```bash
# 下载 Python: https://www.python.org/downloads/
# 安装时勾选 "Add Python to PATH"
```

### 1.4 安装 Node.js (前端构建)

#### macOS

```bash
# 使用 Homebrew
brew install node

# 或使用 nvm（推荐）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.zshrc
nvm install 18
nvm use 18
```

#### Linux

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 或使用 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18
```

#### Windows

从官网下载并安装 [Node.js 18 LTS](https://nodejs.org/)。

### 1.5 验证环境

```bash
# 验证 Docker
docker --version
docker ps

# 验证 Python
python3 --version

# 验证 Node.js
node --version
npm --version
```

---

## 2. 安装部署

### 2.1 获取项目代码

```bash
# 克隆项目
git clone <项目仓库地址>
cd Project.OpenOpenClaw

# 查看项目结构
ls -la
```

项目结构：

```
Project.OpenOpenClaw/
├── backend/               # 后端代码
│   ├── main.py           # FastAPI 主入口
│   ├── models.py         # 数据库模型
│   ├── docker_manager.py # Docker 操作封装
│   ├── config_manager.py # 配置管理
│   └── requirements.txt  # Python 依赖
├── frontend/             # 前端代码
│   ├── src/             # Vue 源码
│   ├── package.json     # NPM 依赖
│   └── vite.config.js   # Vite 配置
├── Dockerfile           # Docker 部署文件
└── README.md           # 项目说明
```

### 2.2 安装后端依赖

```bash
cd backend

# 创建虚拟环境（推荐）
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

后端依赖包括：

- **fastapi**: Web 框架
- **uvicorn**: ASGI 服务器
- **sqlalchemy**: ORM
- **pydantic**: 数据验证
- **docker**: Docker SDK for Python
- **python-multipart**: 文件上传

### 2.3 构建前端

```bash
cd ../frontend

# 安装 NPM 依赖
npm install

# 构建生产版本
npm run build
```

构建完成后，前端资源会生成在 `dist/` 目录。

### 2.4 配置数据目录

```bash
# 创建数据目录（根据需要修改路径）
mkdir -p /data/openclaw
```

### 2.5 启动服务

#### 方式一：直接运行

```bash
# 回到项目根目录
cd ..

# 启动后端服务
# 默认端口 8080
python -m backend.main
```

#### 方式二：使用 uvicorn

```bash
# 安装 uvicorn（如未安装）
pip install uvicorn

# 启动服务
uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
```

#### 方式三：使用 Docker 运行（推荐）

项目已提供 Dockerfile，可一键部署：

```bash
# 构建镜像
docker build -t openclaw-manager:latest .

# 运行容器
docker run -d \
  --name openclaw-manager \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /data/openclaw:/data/openclaw \
  openclaw-manager:latest
```

### 2.6 验证服务

```bash
# 检查服务是否启动
curl http://localhost:8080/

# 预期输出：{"message":"OpenClaw Manager API","version":"1.0.0"}

# 访问 Web UI
# 打开浏览器：http://localhost:8080
```

---

## 3. 快速开始

### 3.1 首次使用流程

```
1. 打开浏览器 → http://localhost:8080
2. 创建群组 → 创建实例 → 启动实例 → 配置 API Key → 使用
```

### 3.2 创建第一个群组

1. 在左侧菜单点击 **群组管理**
2. 点击 **创建群组** 按钮
3. 填写表单：

| 字段 | 示例值 | 说明 |
|------|--------|------|
| 群组名称 | `dev-team` | 便于识别的名称 |
| 根目录 | `/data/openclaw/groups/dev-team` | 实例数据存储路径 |
| Docker 网络 | `openclaw_network_dev` | 容器网络名称 |
| 端口范围起始 | `18980` | 可用端口起始值 |
| 端口范围结束 | `18990` | 可用端口结束值 |
| 描述 | `开发团队专用` | 可选描述 |

4. 点击 **确定**

> **注意**：端口范围应根据实例数量规划，每个实例占用一个端口。

### 3.3 创建第一个实例

1. 在左侧菜单点击 **实例管理**
2. 点击 **创建实例** 按钮
3. 填写表单：

| 字段 | 示例值 | 说明 |
|------|--------|------|
| 所属群组 | `dev-team` | 选择上一步创建的群组 |
| 实例名称 | `assistant-01` | 实例唯一标识 |

4. 点击 **确定**

系统会自动从群组的端口范围中分配一个可用端口。

### 3.4 配置 API Key

1. 在实例列表中，点击目标实例的 **详情** 按钮
2. 点击 **编辑配置** 按钮，跳转到配置中心
3. 或直接在左侧菜单点击 **配置中心**
4. 选择 **实例配置**，选择目标实例
5. 在环境变量标签页填写 API Key：

```bash
# 以 OpenAI 为例
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

或使用右侧的 BYOK 配置模板：
1. 展开模板列表（如 OpenAI）
2. 填写 API Key
3. 点击 **应用模板**

### 3.5 启动实例

1. 返回 **实例管理** 页面
2. 找到目标实例，点击 **启动** 按钮
3. 等待状态变为 **running**（绿色标签）

### 3.6 访问 OpenClaw

1. 实例启动后，点击 **终端** 按钮
2. 浏览器打开新标签页，跳转到 OpenClaw Gateway
3. 开始使用 OpenClaw！

---

## 4. 功能详解

### 4.1 仪表盘 (Dashboard)

**功能**：
- 系统概览：实例总数、运行中/已停止数量、群组数量
- Docker 状态：容器数、镜像数、CPU/内存信息
- 资源监控：运行中实例的 CPU、内存使用率
- 快速操作：一键启动/停止全部实例

### 4.2 群组管理

**功能**：
- 创建/编辑/删除群组
- 查看群组详情（实例列表、存储使用量）
- 群组级配置管理

**群组配置**：
- 根目录：实例数据存储位置
- Docker 网络：群组内实例的网络隔离
- 端口范围：实例端口分配

### 4.3 实例管理

**功能**：
- 创建/删除实例
- 启动/停止/重启实例
- 克隆实例（复制完整数据）
- 批量操作（启动/停止/删除多个实例）
- 查看实例详情：
  - 容器信息
  - 资源使用（CPU/内存）
  - 运行日志
  - 配置文件预览

**实例操作**：
| 操作 | 说明 |
|------|------|
| 启动 | 创建并运行 Docker 容器 |
| 停止 | 停止 Docker 容器 |
| 重启 | 重启 Docker 容器 |
| 详情 | 查看实例详细信息 |
| 终端 | 跳转到 OpenClaw Web 界面 |
| 克隆 | 复制实例及所有数据 |
| 删除 | 删除容器和数据（不可恢复） |

### 4.4 配置中心

**功能**：
- 实例配置管理
- 群组配置管理
- BYOK 配置模板
- 渠道配置（Telegram、Discord 等）
- openclaw.json 可视化编辑
- 配置对比（与默认模板的差异）

**配置类型**：

#### 4.4.1 环境变量 (.env)

| 变量 | 说明 | 示例 |
|------|------|------|
| OPENAI_API_KEY | OpenAI API 密钥 | sk-xxx |
| ANTHROPIC_API_KEY | Anthropic API 密钥 | sk-ant-xxx |
| DEEPSEEK_API_KEY | DeepSeek API 密钥 | sk-xxx |
| AZURE_OPENAI_* | Azure OpenAI 配置 | - |
| OLLAMA_BASE_URL | Ollama 本地地址 | http://localhost:11434 |

#### 4.4.2 openclaw.json

主要配置项：

```json
{
  "tools": {
    "exec": {
      "security": "full",    // full/policies/local
      "host": "host"        // host/container
    },
    "file": {
      "allowedDirectories": ["/root"]
    },
    "webFetch": {
      "enabled": true
    }
  },
  "gateway": {
    "bind": "0.0.0.0",
    "port": 18987
  }
}
```

#### 4.4.3 渠道配置

支持的 IM 渠道：
- Telegram Bot
- Discord Bot
- 飞书 (Feishu)
- WhatsApp
- Slack
- Signal

### 4.5 数据迁移

**功能**：
- 导出实例为 ZIP 文件
- 导入 ZIP 文件恢复实例
- 从目录导入已有 OpenClaw 数据
- 群组整体导出/导入

**灵魂文件说明**：

导出时包含以下"灵魂文件"：
- `openclaw.json` - 主配置文件
- `workspace/` - AI 工作区全部内容
- `agents/{cid}/` - 各会话的智能体状态与认证
- `memory/` - 记忆数据（向量索引 + 对话日志）
- `skills/` - 技能配置

### 4.6 系统设置

**功能**：
- Docker Socket 路径配置
- Web UI 端口配置
- 数据存储目录配置
- Docker 镜像选择与预拉取
- 镜像加速器配置
- 环境信息查看
- Docker 网络/镜像列表

---

## 5. 配置说明

### 5.1 数据目录结构

```
{data_root}/
├── groups/
│   └── {group_name}/
│       ├── {instance_1}/
│       │   ├── .openclaw/      # OpenClaw 配置
│       │   │   ├── openclaw.json
│       │   │   ├── .env
│       │   │   ├── workspace/
│       │   │   ├── memory/
│       │   │   ├── skills/
│       │   │   └── logs/
│       │   └── data/            # 业务数据
│       └── {instance_2}/
│           └── ...
├── data/                        # 系统数据
│   ├── openclaw.db             # SQLite 数据库
│   ├── settings.json            # 系统设置
│   ├── templates.json           # 配置模板
│   ├── exports/                 # 导出文件
│   └── uploads/                 # 上传文件
```

### 5.2 端口分配

- **Web UI**：默认 8080（可在系统设置中修改）
- **OpenClaw Gateway**：每个实例一个端口，从群组端口范围分配

### 5.3 Docker 网络

每个群组创建独立的 Docker Bridge 网络：
- 实现群组内实例互通
- 实现群组间网络隔离

---

## 6. 常见问题

### Q1: 实例启动失败，提示端口占用

**解决方案**：
1. 检查端口是否被其他程序占用：`netstat -an | grep <端口>`
2. 修改群组端口范围，避免冲突
3. 删除已停止的实例释放端口

### Q2: 无法连接 Docker

**解决方案**：
1. 确认 Docker 已启动：`docker ps`
2. 检查 Docker Socket 路径配置（系统设置 → Docker Socket）
3. Linux 用户检查是否已加入 docker 组

### Q3: 访问 OpenClaw 提示跨域错误

**解决方案**：
1. 在配置中心修改 `OPENCLAW_GATEWAY_CONTROL_UI_ALLOWED_ORIGINS` 为 `*`
2. 或设置为具体的 IP 地址

### Q4: 导入实例失败

**解决方案**：
1. 确认 ZIP 文件格式正确
2. 检查目标群组是否存在
3. 确保有足够磁盘空间

### Q5: 如何查看实例日志

**解决方案**：
1. 在实例列表点击 **详情**
2. 在详情页面查看运行日志
3. 可点击刷新按钮获取最新日志

### Q6: 批量启动/停止失败

**解决方案**：
1. 检查 Docker 资源是否充足
2. 查看单个实例的错误信息
3. 确保端口可用

### Q7: 如何备份数据

**解决方案**：
1. 定期在 **数据迁移** 页面导出重要实例
2. 或直接备份整个数据目录

---

## 技术支持

如遇问题，请检查：
1. Docker 是否正常运行
2. 端口是否被占用
3. 磁盘空间是否充足
4. 查看服务日志排查错误
