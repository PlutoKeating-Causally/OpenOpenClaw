# OpenClaw 配置问题解决方案

## 问题描述

OpenClaw 实例启动失败，报错信息：
```
Invalid config at /root/.openclaw/openclaw.json:
- agents.defaults: Unrecognized key: "tools"
- tools: Unrecognized keys: "file", "webFetch"
```

## 根本原因

配置文件中包含**非法字段**，这些字段在 OpenClaw 2026.3.2 版本中不被识别，导致实例无法启动。

## 非法字段清单

| 非法字段 | 位置 | 说明 |
|---------|------|------|
| `agents.defaults.tools` | agents.defaults | ❌ 该位置不允许 tools 字段 |
| `tools.file` | tools | ❌ 字段名错误 |
| `tools.webFetch` | tools | ❌ 字段名错误，应为 `tools.web.fetch` |
| `tools.exec` | tools | ❌ 位置错误，exec 配置应在其他位置 |

## 解决方案

### 方案 1：使用 Web UI 一键修复（推荐）

1. 打开 OpenOpenClaw 管理界面：http://localhost:8080
2. 进入「实例管理」
3. 找到报错的实例，点击「详情」
4. 点击「修复配置」按钮
5. 系统自动移除非法字段并添加缺失的配置段

### 方案 2：使用 API 修复

```bash
# 验证配置
curl http://localhost:8080/api/instances/{instance_id}/config/validate

# 修复配置
curl -X POST http://localhost:8080/api/instances/{instance_id}/config/fix
```

### 方案 3：手动修复

编辑 `openclaw.json` 文件，删除以下字段：

```json
{
  "agents": {
    "defaults": {
      // 删除这一行
      "tools": { "execAllowed": true, ... }
    }
  },
  "tools": {
    // 删除这些字段
    "file": { ... },
    "webFetch": { ... },
    "exec": { "host": "...", "security": "..." }
  }
}
```

## 正确的配置结构

```json
{
  "agents": {
    "defaults": {
      "model": { "primary": "..." },
      "models": {},
      "workspace": "/root/.openclaw/workspace"
      // ❌ 不要在这里添加 tools
    }
  },
  "tools": {
    "profile": "full",
    "web": {
      "search": { "enabled": true, "apiKey": "" },
      "fetch": { "enabled": true }
    },
    "agentToAgent": { "enabled": true }
    // ❌ 不要添加 file, webFetch, exec
  }
}
```

## 预防措施

### 1. 使用 OpenOpenClaw 创建实例

OpenOpenClaw 已更新默认配置模板，确保生成的配置符合 OpenClaw 2026.3.2 规范。

### 2. 配置验证

创建实例后，运行验证检查：
```bash
curl http://localhost:8080/api/instances/{instance_id}/config/validate
```

### 3. 自动修复

在启动实例前，系统会自动检测并提示修复配置问题。

## 技术实现

### 后端代码更新

**文件**: `backend/config_manager.py`

1. **默认配置模板** (`_get_default_openclaw_config`)
   - 移除了所有非法字段
   - 添加了详细的注释说明

2. **配置验证** (`validate_config`)
   - 检测非法字段
   - 返回详细的错误和警告信息

3. **配置修复** (`migrate_config_to_latest`)
   - 自动移除非法字段
   - 添加缺失的必需配置段

4. **非法字段清理** (`_remove_illegal_config_fields`)
   - 清理已知的非法字段
   - 保留合法配置

**文件**: `backend/main.py`

新增 API 端点：
- `GET /api/instances/{id}/config/validate` - 验证配置
- `POST /api/instances/{id}/config/fix` - 一键修复配置

## 测试验证

运行测试脚本验证修复效果：

```bash
cd /Users/causally/OpenOpenclaw
python3 test_setup.py
```

## 相关链接

- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenOpenClaw 文档](./OPENCLAW_CONFIG.md)
