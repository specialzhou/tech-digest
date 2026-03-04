# epro-lite Memory - OpenClaw 集成指南

## 快速开始

### 1. 测试集成

```bash
# 测试召回（会话开始）
cd /root/.openclaw/workspace/memory/epro-lite
./openclaw_hook.sh start "舟哥喜欢什么"

# 测试捕获（会话结束）
cat > /tmp/messages.json << 'EOF'
[
  {"role": "user", "content": "记住我喜欢用 VSCode"},
  {"role": "assistant", "content": "好的"}
]
EOF
./openclaw_hook.sh end /tmp/messages.json
```

---

## OpenClaw 配置

### 方案 A：手动调用（推荐用于测试）

在 OpenClaw 会话中：

**会话开始时：**
```bash
# 召回相关记忆
MEMORY_CONTEXT=$(./openclaw_hook.sh start "$USER_MESSAGE")
echo "$MEMORY_CONTEXT"  # 注入到系统提示
```

**会话结束时：**
```bash
# 保存会话消息
echo '$SESSION_MESSAGES' > /tmp/oc_session.json

# 捕获记忆
./openclaw_hook.sh end /tmp/oc_session.json
```

---

### 方案 B：配置自动钩子

OpenClaw 支持通过配置自动调用钩子脚本。

**步骤：**

1. **编辑 OpenClaw 配置**（位置取决于你的安装）：
   ```bash
   # 可能的配置文件位置
   /root/.openclaw/config.json
   /root/.openclaw/agents/main/config.json
   ```

2. **添加钩子配置**：
   ```json
   {
     "hooks": {
       "sessionStart": {
         "enabled": true,
         "command": "/root/.openclaw/workspace/memory/epro-lite/openclaw_hook.sh start {{message}}",
         "injectOutput": true,
         "injectLocation": "systemPrompt"
       },
       "sessionEnd": {
         "enabled": true,
         "command": "/root/.openclaw/workspace/memory/epro-lite/openclaw_hook.sh end /tmp/oc_session_{{sessionId}}.json",
         "saveMessages": true
       }
     }
   }
   ```

3. **重启 OpenClaw Gateway**：
   ```bash
   openclaw gateway restart
   ```

---

### 方案 C：使用 cron 定时捕获

如果你使用 OpenClaw 的 cron 功能，可以在 cron 任务中调用：

```json
{
  "name": "Memory Capture",
  "schedule": "*/30 * * * *",
  "command": "python3 /root/.openclaw/workspace/memory/epro-lite/session_hooks.py end /tmp/latest_session.json"
}
```

---

## 系统提示模板

在系统提示中注入记忆上下文：

```markdown
# 角色
你是二狗，舟哥的全栈技术助手。

# 长期记忆
{{EPRO_LITE_MEMORIES}}

# 当前对话
{{USER_MESSAGE}}
```

---

## API 参考

### 召回记忆

```bash
python3 openclaw_integration.py recall "<查询>" [类别]
```

示例：
```bash
python3 openclaw_integration.py recall "Python 编程"
python3 openclaw_integration.py recall "部署" preferences
```

### 捕获记忆

```bash
python3 openclaw_integration.py capture <messages.json>
```

messages.json 格式：
```json
[
  {"role": "user", "content": "消息内容"},
  {"role": "assistant", "content": "回复内容"}
]
```

### 查看所有记忆

```bash
python3 openclaw_integration.py get [类别]
```

### 清空记忆

```bash
python3 openclaw_integration.py clear
```

---

## 记忆文件

- **主文件**: `/root/.openclaw/workspace/memory/epro-lite/memories.json`
- **备份**: `/root/.openclaw/workspace/memory/epro-lite/memories.backup.json.0`

---

## 故障排查

### 召回不到记忆

1. 检查关键词是否匹配
2. 查看记忆文件是否存在：
   ```bash
   cat /root/.openclaw/workspace/memory/epro-lite/memories.json
   ```

### 捕获超时

LLM 调用可能超时，增加 timeout 值：
```python
# 在 session_hooks.py 中调整 timeout 参数
timeout=120  # 从 30 增加到 120 秒
```

### 记忆不提取

检查触发关键词：
```bash
cat /root/.openclaw/workspace/memory/epro-lite/config.json | grep triggerKeywords
```

---

## 性能优化

### 减少 LLM 调用

1. 增加 `extraction.minMessages`（默认 3）
2. 使用触发关键词过滤

### 加快召回速度

1. 减少 `recall.maxResults`（默认 5）
2. 禁用 LLM 重排序（使用纯关键词匹配）

---

## 备份与恢复

### 备份
```bash
cp /root/.openclaw/workspace/memory/epro-lite/memories.json \
   /root/.openclaw/workspace/memory/epro-lite/memories.backup.$(date +%Y%m%d).json
```

### 恢复
```bash
cp /root/.openclaw/workspace/memory/epro-lite/memories.backup.20260224.json \
   /root/.openclaw/workspace/memory/epro-lite/memories.json
```

---

## 下一步

1. **测试集成**：先用手动调用测试
2. **配置自动钩子**：根据 OpenClaw 文档配置自动调用
3. **监控效果**：定期检查记忆文件，确保正常捕获

有任何问题，查看日志：
```bash
tail -f /tmp/epro-lite.log
```
