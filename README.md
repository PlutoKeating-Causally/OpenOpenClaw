# OpenClaw Manager

一个轻量化的 **OpenClaw 多实例群组化部署管理系统**，帮助你在本地服务器上轻松管理多个 OpenClaw 容器实例。

## ✨ 特性

- **多实例管理**：一键创建、启动、停止、重启、删除 OpenClaw 容器实例
- **群组化部署**：按业务/场景将实例分组管理，实现数据与网络隔离
- **可视化配置**：通过 Web UI 管理 .env 环境变量和 openclaw.json 配置文件
- **数据迁移**：支持实例/群组的导入导出，"灵魂文件"一键迁移
- **资源监控**：实时查看 CPU、内存使用情况
- **终端访问**：点击按钮直接跳转到 OpenClaw 内置终端
- **批量操作**：批量启动、停止、删除实例

## 🏗️ 技术架构

| 组件 | 技术栈 | 说明 |
|------|--------|------|
| 后端 | FastAPI | 高性能 Python Web 框架 |
| 前端 | Vue3 + Vite | 现代前端工程化 |
| UI组件 | Element Plus | 简洁的管理后台组件 |
| 数据库 | SQLite | 轻量级文件数据库 |
| 容器管理 | Docker Engine API | 原生 Docker 操作封装 |

## 🚀 快速开始

### 前置要求

- **操作系统**：macOS / Linux (Ubuntu/Debian/CentOS) / Windows
- **Docker**：已安装并运行 Docker Engine
- **端口**：确保 8080 端口可用（Web UI 默认端口）

### 安装步骤

#### 1. 克隆项目

```bash
git clone <项目地址>
cd Project.OpenOpenClaw
```

#### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 3. 构建前端

```bash
cd frontend
npm install
npm run build
```

#### 4. 启动服务

```bash
# 回到项目根目录
cd ..

# 启动后端服务
python -m backend.main
```

#### 5. 访问 Web UI

打开浏览器访问：http://localhost:8080

## 📖 使用指南

### 1. 创建群组

首次使用时，需要先创建一个群组来管理实例：

1. 点击左侧菜单 **群组管理**
2. 点击 **创建群组** 按钮
3. 填写群组信息：
   - **群组名称**：如 `dev-group`
   - **根目录**：实例数据存储路径，如 `/data/openclaw/groups/dev-group`
   - **Docker 网络**：如 `openclaw_network_dev`
   - **端口范围**：如 `18980-18990`
4. 点击 **确定** 创建

### 2. 创建实例

群组创建完成后，可以在该群组下创建 OpenClaw 实例：

1. 点击左侧菜单 **实例管理**
2. 点击 **创建实例** 按钮
3. 选择所属群组，输入实例名称
4. 系统会自动分配一个可用端口
5. 点击 **确定** 创建

### 3. 启动实例

新创建的实例默认为 **已停止** 状态，需要手动启动：

1. 在实例列表中找到目标实例
2. 点击 **启动** 按钮
3. 等待实例启动完成（状态变为绿色 running）

### 4. 配置 API Key

实例启动前，需要配置你的模型 API Key：

1. 点击实例的 **详情** 按钮
2. 点击 **编辑配置**
3. 在 **配置中心** 页面：
   - 选择 **实例配置**
   - 选择目标实例
   - 在环境变量标签页填写 `OPENAI_API_KEY`、`ANTHROPIC_API_KEY` 等
   - 或使用右侧的 BYOK 配置模板快速填充
4. 点击 **保存配置**

支持的模型服务商：
- OpenAI (GPT-4/GPT-4o)
- Anthropic (Claude)
- Google AI (Gemini)
- Azure OpenAI
- DeepSeek
- MiniMax
- Ollama (本地模型)
- OpenRouter
- Hugging Face
- Groq
- xAI (Grok)
- Cohere
- Mistral
- Voyage AI

### 5. 访问 OpenClaw 终端

实例启动后，可以直接跳转到 OpenClaw 的 Web 界面：

1. 在实例列表中，点击 **终端** 按钮
2. 浏览器会打开新标签页，跳转到 OpenClaw Gateway

### 6. 数据迁移

#### 导出实例

1. 点击左侧菜单 **数据迁移**
2. 在 **导出** 标签页选择要导出的实例
3. 点击 **导出实例**，下载 ZIP 文件

导出的内容包括：
- `openclaw.json` - 主配置文件
- `workspace/` - AI 工作区
- `agents/{cid}/` - 智能体状态与认证
- `memory/` - 记忆数据
- `skills/` - 技能配置

#### 导入实例

1. 在 **导入** 标签页
2. 选择 ZIP 文件或指定目录路径
3. 选择目标群组，输入新实例名称
4. 点击 **上传并导入**

### 7. 批量操作

在实例列表中：

1. 勾选多个实例
2. 使用底部的批量操作按钮：
   - **批量启动**
   - **批量停止**
   - **批量删除**

## ⚙️ 系统设置

点击左侧菜单 **系统设置**，可以配置：

- **Docker Socket 路径**：Docker daemon 连接地址
- **Web UI 端口**：默认 8080
- **数据存储根目录**：默认 `/data/openclaw`
- **默认 Docker 镜像**：默认 `openclaw/openclaw:latest`
- **镜像加速器**：可配置阿里云等镜像源
- **环境检测**：查看系统、Docker 状态信息

## 🔧 常见问题

### Q: 实例启动失败怎么办？

A: 检查以下事项：
1. Docker 是否正常运行
2. 端口是否被占用（可在群组设置中修改端口范围）
3. 查看实例日志排查具体错误

### Q: 如何访问运行中的 OpenClaw？

A: 点击实例的 **终端** 按钮，或直接访问 `http://localhost:{端口号}`

### Q: 实例数据存储在哪里？

A: 在群组根目录下的实例目录中，例如：`/data/openclaw/groups/{群组名}/{实例名}/.openclaw/`

### Q: 如何迁移到新服务器？

A:
1. 导出群组或实例为 ZIP 文件
2. 将 ZIP 文件复制到新服务器
3. 在新系统中导入 ZIP 文件

## 📝 API 文档

后端提供 RESTful API，主要端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/groups | 获取群组列表 |
| POST | /api/groups | 创建群组 |
| DELETE | /api/groups/{id} | 删除群组 |
| GET | /api/instances | 获取实例列表 |
| POST | /api/instances | 创建实例 |
| POST | /api/instances/{id}/start | 启动实例 |
| POST | /api/instances/{id}/stop | 停止实例 |
| DELETE | /api/instances/{id} | 删除实例 |
| GET | /api/system/stats | 获取系统统计 |

## 📄 许可证

MIT License
