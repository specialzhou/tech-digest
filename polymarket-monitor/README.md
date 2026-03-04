# Polymarket 组合交易监控系统

## 📋 已安装组件

| 组件 | 用途 | 状态 |
|------|------|------|
| `polymarket-paper-trader` | 模拟交易 + 胜率统计 | ✅ 已安装 |
| `polyclaw` | 实盘交易 + 对冲发现 | ✅ 已安装 |
| `polymarket-monitor` | 统一监控 + 简报集成 | ✅ 已创建 |

---

## 🔧 配置步骤

### 1️⃣ 配置 polyclaw（实盘）

编辑 `~/.openclaw/openclaw.json`，添加：

```json
"skills": {
  "entries": {
    "polyclaw": {
      "enabled": true,
      "env": {
        "CHAINSTACK_NODE": "https://polygon-mainnet.core.chainstack.com/YOUR_KEY",
        "POLYCLAW_PRIVATE_KEY": "0x...",
        "OPENROUTER_API_KEY": "sk-or-v1-..."
      }
    }
  }
}
```

**密钥获取：**
- **Chainstack Node**: https://console.chainstack.com（免费）
- **OpenRouter API**: https://openrouter.ai/settings/keys
- **私钥**: 生成新钱包（建议只放少量资金）

**首次使用需要授权合约：**
```bash
cd /root/.openclaw/skills/polyclaw
uv sync
uv run python scripts/polyclaw.py wallet approve
```

---

### 2️⃣ 配置 polymarket-paper-trader（模拟）

编辑 `~/.openclaw/openclaw.json`，添加：

```json
"skills": {
  "entries": {
    "polymarket-paper-trader": {
      "enabled": true,
      "env": {
        "PAPER_TRADING_INITIAL_CAPITAL": "10000",
        "PAPER_TRADING_STRATEGY": "momentum"
      }
    }
  }
}
```

---

### 3️⃣ 重启 Gateway

```bash
openclaw gateway restart
```

---

## 📊 使用方式

### 查看统计
```bash
python3 /root/.openclaw/workspace/polymarket-monitor/monitor.py stats
```

### 生成每日报告
```bash
python3 /root/.openclaw/workspace/polymarket-monitor/monitor.py report
```

### 检查异常
```bash
python3 /root/.openclaw/workspace/polymarket-monitor/monitor.py warnings
```

---

## 📰 集成到每日简报

在 tech-news-digest 生成流程中，添加：

```bash
python3 /root/.openclaw/workspace/polymarket-monitor/digest-integration.py >> /tmp/polymarket-section.html
```

然后将生成的 HTML 片段插入到简报模板中。

---

## 🎯 自然语言命令

配置好后可以用自然语言与 OpenClaw 交互：

```
"Polymarket 模拟交易胜率多少？"
"显示我的实盘持仓"
"运行今日交易报告"
"帮我找 Polymarket 对冲机会"
"在 <market_id> 买入$50 YES（模拟）"
"卖出我的 <market_id> 持仓（实盘）"
```

---

## ⚠️ 安全提醒

1. **私钥安全**：
   - 仅存放可承受损失的资金
   - 定期将盈利转移到安全钱包
   - 不要将私钥提交到 git

2. **模拟优先**：
   - 新策略先在模拟交易测试
   - 胜率>60% 再考虑实盘
   - 每日检查模拟 vs 实盘差异

3. **Gas 费用**：
   - Polygon Gas 约 $0.01-0.1/笔
   - 避免频繁小额交易
   - 批量操作更划算

---

## 📈 信心分数说明

| 分数 | 含义 | 建议 |
|------|------|------|
| 70-100 | 高信心 | 可以继续执行策略 |
| 50-69 | 中等 | 观察调整 |
| 0-49 | 低信心 | 暂停策略，检查问题 |

**计算逻辑：**
- 基础分 50
- 模拟胜率>60% → 加分（最多加 30）
- 模拟胜率<40% → 减分（最多减 30）
- 实盘盈利>$100 → +10
- 实盘亏损<$-100 → -10

---

## 🔍 故障排查

**Q: polyclaw 命令找不到**
```bash
cd /root/.openclaw/skills/polyclaw
uv sync
```

**Q: CLOB 订单失败**
设置代理：
```bash
export HTTPS_PROXY="http://user:pass@proxy-server:port"
export CLOB_MAX_RETRIES=10
```

**Q: 模拟交易数据库不存在**
先执行几笔模拟交易，数据库会自动创建。

---

## 📞 支持

- polyclaw 文档：https://github.com/chainstacklabs/polyclaw
- polymarket-paper-trader: https://github.com/agent-next/polymarket-paper-trader
- 监控脚本：/root/.openclaw/workspace/polymarket-monitor/
