# OpenClaw 配置文档

本文档详细说明 `openclaw.json` 的配置结构和各字段含义。

## 配置结构概览

```json
{
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

### 2. gateway - 网关配置

配置 OpenClaw 网关服务。

```json
{
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "allowedOrigins": [
        "http://localhost:18789",
        "http://127.0.0.1:18789"
      ]
    },
    "auth": {
      "mode": "password",
      "password": "your-password"
    }
  }
}
```

### 3. channels - 渠道配置

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

### 4. tools - 工具配置

```json
{
  "tools": {
    "profile": "full",
    "web": {
      "search": {
        "enabled": true,
        "apiKey": "your-api-key"
      },
      "fetch": {
        "enabled": true
      }
    }
  }
}
```

## 环境变量配置 (.env)

```bash
# AI 服务商 API 密钥
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_GENERATIVE_AI_API_KEY=xxx
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
