# OpenClaw 配置文档

本文档详细说明 `openclaw.json` 的配置结构和各字段含义。

> **重要**：OpenOpenClaw 所有实例均以 **root 用户**在 Docker 容器内运行，家目录为 `/root`，配置目录为 `/root/.openclaw`。

## 配置结构概览

```json
{
  "env": {},
  "meta": {},
  "wizard": {},
  "auth": {},
  "models": {},
  "agents": {},
  "tools": {},
  "commands": {},
  "session": {},
  "hooks": {},
  "channels": {},
  "gateway": {},
  "skills": {},
  "plugins": {}
}
```

## 详细配置说明

### 1. meta - 元数据

记录配置文件的版本和时间戳信息。

```json
{
  "meta": {
    "lastTouchedVersion": "2026.3.2",
    "lastTouchedAt": "2026-03-12T08:00:00.000Z"
  }
}
```

### 2. wizard - 向导配置

预填充向导信息，使新实例无需运行 `openclaw onboard` 即可直接启动。

```json
{
  "wizard": {
    "lastRunAt": "2026-03-12T08:00:00.000Z",
    "lastRunVersion": "2026.3.2",
    "lastRunCommand": "configure",
    "lastRunMode": "local"
  }
}
```

### 3. gateway - 网关配置

配置 OpenClaw 网关服务。默认绑定 LAN（`0.0.0.0`），使用 **password 认证模式**。

```json
{
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "enabled": true,
      "allowedOrigins": [
        "http://localhost:18789",
        "http://127.0.0.1:18789",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
      ]
    },
    "auth": {
      "mode": "password",
      "rateLimit": {
        "maxAttempts": 10,
        "windowMs": 60000,
        "lockoutMs": 300000,
        "exemptLoopback": true
      }
    },
    "tailscale": {
      "mode": "off",
      "resetOnExit": false
    }
  }
}
```

**认证说明**：
- `gateway.auth.mode: "password"`：密码认证模式，密码通过 `OPENCLAW_GATEWAY_PASSWORD` 环境变量注入
- 密码在 OpenOpenClaw 系统设置中全局配置，启动实例时自动注入
- `controlUi.allowedOrigins` 由环境变量 `OPENCLAW_GATEWAY_CONTROL_UI_ALLOWED_ORIGINS=*` 覆盖，支持任意 LAN 来源访问

### 4. channels - 渠道配置

配置消息渠道（Telegram、飞书等）。

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "your-bot-token"
    },
    "feishu": {
      "enabled": true,
      "appId": "cli_xxx",
      "appSecret": "xxx"
    }
  }
}
```

### 5. tools - 工具配置

默认使用 `"full"` 配置文件，启用全部 LLM 工具能力：

| 能力 | 工具组 | 说明 |
|------|--------|------|
| **文件读写** | `group:fs` | read, write, edit, apply_patch |
| **终端执行** | `group:runtime` | exec, process, bash |
| **网络搜索** | `group:web` | web_search (Brave Search), web_fetch |
| **会话管理** | `group:sessions` | sessions_list, sessions_history, sessions_send |
| **记忆系统** | `group:memory` | memory_search, memory_get |
| **UI 工具** | `group:ui` | browser, canvas |
| **自动化** | `group:automation` | cron, gateway |
| **消息发送** | `group:messaging` | message |

```json
{
  "tools": {
    "profile": "full",
    "web": {
      "search": {
        "enabled": true,
        "maxResults": 5,
        "timeoutSeconds": 30,
        "cacheTtlMinutes": 15
      },
      "fetch": {
        "enabled": true,
        "maxChars": 50000,
        "maxCharsCap": 50000,
        "timeoutSeconds": 30,
        "cacheTtlMinutes": 15
      }
    },
    "agentToAgent": {
      "enabled": true
    },
    "exec": {
      "backgroundMs": 10000,
      "timeoutSec": 1800,
      "cleanupMs": 1800000,
      "notifyOnExit": true,
      "notifyOnExitEmptySuccess": false
    }
  }
}
```

**Brave Search 配置**：
- 搜索功能默认启用，使用 Brave Search API
- API Key 通过 `BRAVE_API_KEY` 环境变量提供（在群组级别 `.env` 中设置）
- 官方参考：https://docs.openclaw.ai/gateway/configuration-reference#tools-web

### 6. agents - 智能体配置

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": ""
      },
      "models": {},
      "workspace": "/root/.openclaw/workspace"
    }
  }
}
```

> **注意**：`workspace` 路径必须为 `/root/.openclaw/workspace`（root 用户）。不要在 `agents.defaults` 中添加 `tools` 字段（非法字段，会导致启动失败）。

### 7. models - 模型配置

```json
{
  "models": {
    "mode": "merge",
    "providers": {}
  }
}
```

### 8. env - 配置级环境变量

```json
{
  "env": {
    "SOME_VAR": "value"
  }
}
```

## 环境变量配置 (.env)

OpenOpenClaw 支持通过环境变量直接注入配置。

### 实例级 .env（位于 `{instance}/.openclaw/.env`）

```bash
# --- 路径配置 (root 用户) ---
HOME=/root
OPENCLAW_HOME=/root
OPENCLAW_STATE_DIR=/root/.openclaw
OPENCLAW_CONFIG_DIR=/root/.openclaw
OPENCLAW_WORKSPACE_DIR=/root/.openclaw/workspace

# --- 核心网关配置 ---
OPENCLAW_GATEWAY_PORT=18789
OPENCLAW_GATEWAY_BIND=lan
OPENCLAW_DISABLE_BONJOUR=1
OPENCLAW_GATEWAY_CONTROL_UI_ALLOWED_ORIGINS=*

# --- 网关认证 (由系统全局设置注入) ---
OPENCLAW_GATEWAY_PASSWORD=

# --- Web 搜索 (由群组级 .env 注入) ---
BRAVE_API_KEY=

# --- 主流模型服务商 (官方标准变量名) ---
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
GEMINI_API_KEY=xxx
DEEPSEEK_API_KEY=sk-xxx
OPENROUTER_API_KEY=sk-or-xxx
GROQ_API_KEY=gsk-xxx
XAI_API_KEY=xxx
MISTRAL_API_KEY=xxx
MINIMAX_API_KEY=xxx
HUGGINGFACE_HUB_TOKEN=hf_xxx

# --- 其他支持 (部分) ---
TOGETHER_API_KEY=xxx
VOYAGE_API_KEY=xxx
CEREBRAS_API_KEY=xxx
MOONSHOT_API_KEY=xxx
OLLAMA_API_KEY=xxx
```

### 群组级 .env（位于 `{group}/.env`）

群组级环境变量会被所有该群组下的实例继承（实例级优先）。

```bash
# 群组共享的 Brave Search API Key
BRAVE_API_KEY=your-brave-api-key-here

# 群组共享的模型 API Key
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
```

### 环境变量优先级

```
系统全局设置 (gateway_password) → 宿主机环境变量 → 群组级 .env → 实例级 .env
```

更多官方支持的环境变量请参考：[OpenClaw 官方文档 - Environment](https://docs.openclaw.ai/help/environment)

## 目录挂载结构

每个实例目录完整挂载到 Docker 容器的 `/root` 家目录：

```
宿主机: {dataRoot}/groups/{group}/{instance}/  →  容器内: /root/
    ├── .openclaw/                              →  /root/.openclaw/
    │   ├── openclaw.json                       →  /root/.openclaw/openclaw.json
    │   ├── .env                                →  /root/.openclaw/.env
    │   ├── workspace/                          →  /root/.openclaw/workspace/
    │   ├── memory/                             →  /root/.openclaw/memory/
    │   ├── skills/                             →  /root/.openclaw/skills/
    │   └── logs/                               →  /root/.openclaw/logs/
    └── data/                                   →  /root/data/
```

## 配置更新 API

### 检查配置更新
```bash
curl http://localhost:8080/api/config/check-update
```

### 迁移实例配置
```bash
curl -X POST http://localhost:8080/api/instances/{instance_id}/migrate-config
```

### 验证配置
```bash
curl http://localhost:8080/api/instances/{instance_id}/config/validate
```
