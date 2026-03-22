# OpenOpenClaw

**OpenOpenClaw**：智启未来，重塑 AI 容器集群管理。

这是一款专为 **OpenClaw** 打造的下一代全栈式多实例集群协同系统。通过卓越的群组化架构与极简的可视化运维，OpenOpenClaw 为开发者与团队提供了从自动化部署、多维配置到资产流转的闭环管理体验，让 AI 实例的规模化运营变得优雅而高效。

## ✨ 核心特性

- **🚀 极速集群调度**：秒级创建、编排与生命周期管理，支持一键批量启动与智能资源分配。
- **📂 维度化群组架构**：首创业务维度分组，支持群组级环境变量继承与网络隔离。
- **🎨 沉浸式视觉配置**：全图形化管理 `.env` 与 `openclaw.json`，内置 OpenClaw 2026.3.2 规范验证与一键修复。
- **♻️ 资产全周期流转**：业界领先的"灵魂文件"热迁移技术，支持实例与群组的无缝导入导出。
- **📊 实时洞察矩阵**：毫秒级系统资源监控，可视化展示 CPU 与内存消耗。
- **⌨️ 原生终端集成**：深度打通内置终端，实现管理与交互的零距离转换。
- **⚡ 规模化并行处理**：强大的批处理引擎，支持海量实例同步状态变更与配置同步。

## 🏗️ 精选技术架构

| 组件 | 技术栈 | 卓越之处 |
|------|--------|----------|
| **核心引擎** | FastAPI (Python 3.8+) | 异步高性能架构，极致响应速度 |
| **交互界面** | Vue 3 + Vite | 极简主义设计，现代工程化标准 |
| **美学套件** | Element Plus | 严谨的 B 端视觉语言，极致交互体验 |
| **存储中枢** | SQLite | 零配置轻量化存储，数据随拷随走 |
| **容器协同** | Docker Engine API | 原生级驱动封装，支持 Root 用户模式部署 |

## 🚀 快速开始

本项目采用 **管理端 (Host)** + **执行端 (Docker)** 的混合架构。管理端直接运行在你的宿主机上，通过桥接方式管理 Docker 容器中的 OpenClaw 实例。

### 1. 前置要求

- **操作系统**：macOS / Linux / Windows
- **Python**: 3.8+ (后端运行)
- **Node.js**: 18+ (前端构建)
- **Docker**: 已安装并在宿主机运行 (用于运行 OpenClaw 实例)

### 2. 部署流程 (从零开始)

#### 第一步：克隆项目
```bash
git clone <项目地址>
cd OpenOpenClaw
```

#### 第二步：部署后端
```bash
cd backend
# 建议创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 第三步：构建前端
```bash
cd ../frontend
npm install
npm run build
```
> **提示**：构建完成后，静态文件将生成在 `frontend/dist` 目录，后端会自动识别并托管。

#### 第四步：启动管理系统
```bash
cd ../backend
# 可选：设置自定义数据存放路径
export OPENCLAW_DATA_DIR=./data
# 运行主程序
python3 main.py
```

### 3. 开始使用
打开浏览器访问：**http://localhost:8080**
现在你可以创建群组和 OpenClaw 实例了！

## 📖 使用指南

详细使用指南请参考 [QUICK_START.md](./QUICK_START.md)。

### 关键配置项
- **环境变量**: 建议在群组级别配置 `BRAVE_API_KEY` 以启用全局搜索。
- **配置修复**: 若实例启动失败，请使用详情页的「修复配置」功能，自动适配 OpenClaw 最新规范。

## 📄 许可证

MIT License
