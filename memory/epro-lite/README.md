# epro-lite for OpenClaw

轻量级记忆增强系统，适用于低配置 VPS（2GB 内存）。

## 特性

- ✅ **6 类记忆分类**：profile, preferences, entities, events, cases, patterns
- ✅ **L0/L1/L2 层级结构**：从一句话摘要到完整叙述
- ✅ **LLM 驱动提取**：使用 qwen3.5-plus 自动提取记忆
- ✅ **智能去重**：LLM 判断是否重复（无需向量数据库）
- ✅ **关键词召回**：关键词匹配 + LLM 重排序
- ✅ **零额外依赖**：只需 `openai` Python 包

## 安装

```bash
# 已安装，位于：
/root/.openclaw/workspace/memory/epro-lite/

# 依赖（如未安装）：
pip3 install openai --break-system-packages
```

## 用法

### 1. 捕获记忆（会话结束后调用）

```bash
# 准备会话消息
cat > /tmp/messages.json << 'EOF'
[
  {"role": "user", "content": "我叫舟哥，喜欢用 Python 做量化交易"},
  {"role": "assistant", "content": "好的舟哥，我记住了"},
  {"role": "user", "content": "别忘了我不喜欢复杂的配置"}
]
EOF

# 捕获记忆
cd /root/.openclaw/workspace/memory/epro-lite
python3 openclaw_integration.py capture /tmp/messages.json
```

### 2. 召回记忆（会话开始时调用）

```bash
# 根据查询召回相关记忆
python3 openclaw_integration.py recall "舟哥喜欢什么编程语言"
```

### 3. 查看所有记忆

```bash
# 全部
python3 openclaw_integration.py get

# 按类别
python3 openclaw_integration.py get profile
python3 openclaw_integration.py get preferences
```

### 4. 清空记忆

```bash
python3 openclaw_integration.py clear
```

## 与 OpenClaw 集成

### 方案 A：在会话结束时捕获

在 OpenClaw 会话结束钩子中调用：

```python
import subprocess
import json

def on_session_end(messages):
    # 保存消息到临时文件
    with open('/tmp/oc_messages.json', 'w') as f:
        json.dump(messages, f)
    
    # 调用 epro-lite 捕获
    result = subprocess.run(
        ['python3', '/root/.openclaw/workspace/memory/epro-lite/openclaw_integration.py', 'capture', '/tmp/oc_messages.json'],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)
```

### 方案 B：在会话开始时召回

在系统提示中注入召回的记忆：

```python
def on_session_start(user_message):
    # 召回相关记忆
    result = subprocess.run(
        ['python3', '/root/.openclaw/workspace/memory/epro-lite/openclaw_integration.py', 'recall', user_message],
        capture_output=True,
        text=True
    )
    memories = json.loads(result.stdout)
    
    # 构建系统提示
    context = ""
    for mem in memories:
        context += f"- [{mem['category']}] {mem['l0']}\n"
    
    return context
```

## 记忆类别

| 类别 | 说明 | 合并策略 |
|------|------|----------|
| profile | 用户身份、静态属性 | 总是合并 |
| preferences | 用户倾向、习惯、偏好 | 按主题合并 |
| entities | 项目、人物、组织 | 支持合并 |
| events | 决策、里程碑、发生的事 | 仅追加 |
| cases | 问题 + 解决方案对 | 仅追加 |
| patterns | 可复用的流程和方法 | 支持合并 |

## 配置

编辑 `/root/.openclaw/workspace/memory/epro-lite/config.json`：

```json
{
  "llm": {
    "baseUrl": "https://coding.dashscope.aliyuncs.com/v1",
    "apiKey": "sk-xxx",
    "model": "qwen3.5-plus"
  },
  "extraction": {
    "triggerKeywords": ["记住", "别忘了", "注意", "重要", "偏好"]
  },
  "recall": {
    "maxResults": 5
  }
}
```

## 存储

- **记忆文件**: `/root/.openclaw/workspace/memory/epro-lite/memories.json`
- **备份文件**: `/root/.openclaw/workspace/memory/epro-lite/memories.backup.json.0`

## 示例输出

```json
{
  "id": "9de74b3d-0d0c-41af-a9fc-429fb4ed57e2",
  "category": "profile",
  "l0": "用户的名字是舟哥",
  "l1": {"name": "舟哥"},
  "l2": "用户在对话开始时明确说明自己的名字叫舟哥。",
  "keywords": ["舟哥", "名字", "身份"],
  "created_at": "2026-02-24T21:03:24.447765",
  "access_count": 0
}
```

## 资源占用

- **内存**: ~50MB（运行时）
- **磁盘**: <1MB（每 100 条记忆）
- **CPU**: 仅在提取/召回时使用（LLM API 调用）

## 限制

- 无向量检索（关键词 + LLM 排序）
- 去重精度略低于向量方案
- 适合 1000 条以下记忆场景

## 升级路径

如需更强大的功能，可迁移到完整版 epro-memory（需要 LanceDB + 向量检索）。
