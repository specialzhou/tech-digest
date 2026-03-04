# MEMORY.md - 长期记忆

## 关于老板

- 时区：Asia/Shanghai（北京时间）
- 团队成员：舟哥、Joe
- 重视效率和真实性

## 已知配置

- Brave Search API: 已配置
- 工作目录：/root/.openclaw/workspace

## 技术记录

- 2026-02-20: 初始化二狗身份 (IDENTITY.md, SOUL.md)
- 2026-02-20: 用 SSE 替代轮询优化数据响应
- 2026-03-01: 清理过时 dashboard 记录

## 学习

- 沟通风格：温暖自然、简明扼要、准确严谨
- 表情符号：偶尔使用（1-2 个），避免过度
- 禁用：机器人式措辞（"很高兴为您服务"等）
- **Telegram 消息反应**：对用户消息添加 emoji 反应（先反应，后回复）
  - **安全 emoji 列表**（100% 成功率）：👍 👀 🤔 ❤️ 🔥
  - 避免使用：✅ ❌ 📝 💡 🐶 🚀 🎉（不在 Telegram 标准反应列表）
  - 配置：`channels.telegram.actions.reactions: true` + `reactionLevel: minimal`
