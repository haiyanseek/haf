# 🏗️ HAF — Haiyan Agent Framework

**Filesystem-first Multi-Agent Framework** · 文件系统优先的多 Agent 框架

HAF 是海燕生态在 7×24 生产环境中打磨出的多 Agent 框架核心。它用最朴素的文件系统作为 Agent 之间的事实同步层，让复杂多 Agent 协作变得可审计、可恢复、可演化。

> **HaiyanSeek** · 北京未名水木合成科技有限公司

## ✨ 设计理念

```
传统 Agent 框架:  内存/消息队列  →  状态易失、难审计
HAF:              文件系统       →  天然持久化、可审计、可恢复
```

- 📁 **Filesystem-first** — 文件即状态，目录即上下文
- 🧠 **分层组件** — 从单 Agent 循环到多 Agent 编排的渐进式架构
- 🛡️ **安全闭环** — 内置 AgentShield 防护、命令门禁、Verifier 验证
- 🔄 **可演化** — 经验自动沉淀为技能与记忆，越用越强
- ⚡ **零依赖核心** — 核心逻辑纯 Python 标准库

## 🚀 Quick Start

```bash
git clone https://github.com/haiyanseek/haf.git
cd haf
python3 -m haf --help
```

## 📂 架构

```
haf/
├── core/          # 核心循环：Model → Tool → Observation → 反思
├── agents/        # 角色化 Agent 定义
├── memory/        # 文件系统记忆（TypedGraphMemory）
├── safety/        # AgentShield 安全层
├── tools/         # 工具系统
└── harness/       # Master Harness 全量管理
```

## 📜 License

Apache License 2.0 — see [LICENSE](LICENSE)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)
