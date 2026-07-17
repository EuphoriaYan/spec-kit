# AI Team Spec Kit

[English backup](README_en.md)

AI Team Spec Kit 是一个面向团队协作的 Spec-Driven Development（SDD）工具。
它基于 Spec Kit `v0.12.5`，但默认不安装原生 Spec Kit 的整套命令，而是为
Codex、Claude Code、Cursor 和 Trae 安装六个职责清晰的主 Team Skills，并提供
按需使用的高级扩展入口。

它解决的不是“让 AI 多写代码”，而是让不同成员、不同 AI 工具在同一套需求、
架构边界、任务范围和验证证据下协作。

## 为什么需要它

AI Coding 降低了实现功能的成本，也带来了新的团队风险：模型可能没有读全代码、
重复实现已有能力、绕过模块边界、扩大修改范围，或者只凭一次运行成功就宣布完成。

本项目用以下方式收敛这些风险：

- 需求、架构、实现和评审由不同角色 Skill 承担，以 Issue 和文档交接；
- CodeGraph 在 Plan 和缺陷分析阶段提供源码影响范围；
- Feature 和 Bugfix 使用不同但可续接的路径；
- 实现后自动进入 Review -> Assess -> Fix 质量循环；
- 只有需求接受、HLD/公共接口、敏感依赖与安全决策、超范围变更和最终合入长期保留人工责任；
- 本地过程文件默认不进入 Git，Issue、PR、源码、测试和经批准的架构文档承担跨人协作。

## 六个 Team Skills

用户可以直接在聊天框描述当前要做的事，不必记住 Skill 名称。

| Skill | 什么时候使用 | 主要输出 |
|---|---|---|
| `speckit.team.specify` | 有一个新 Feature 或新项目想法 | 完整 User Stories，以及可发布或可复制的 Feature Issue |
| `speckit.team.plan-and-task` | Feature Issue 已被接受 | CodeGraph 支撑的 HLD、模块 Tasks、最小自测和确定性检查 |
| `speckit.team.assess` | 发现缺陷、异常现象或 Review 问题 | 根因假设、影响范围、修复边界和测试策略 |
| `speckit.team.fix` | Assessment 已 ready 或风险已批准 | 最小修复、回归测试、进度说明并自动回到 Review |
| `speckit.team.implement` | Feature Tasks 已通过检查 | 代码、自测证据和自动质量循环后的 PR 准备结果 |
| `speckit.team.review` | 需要评审 PR 或本地 diff | 分级问题、自动修复路由以及 `GO` / `GO-WITH-RISK` / `NO-GO` |

## 高级扩展入口

高级扩展不参与 Feature 或 Bugfix 的自动路由，仅在用户明确提出维护需求时调用：

| 入口 | 什么时候使用 | 主要输出 |
|---|---|---|
| `speckit.team.memory-consolidate` | 交付后需要沉淀经验或复用已批准的决定 | 建议性 Memory，或经人工批准的项目 Knowledge |

```text
Feature: 一句话需求 -> Specify -> Issue 接受 -> Plan-and-Task
         -> Implement -> Review/Assess/Fix -> PR -> 人工决定合入

Bugfix: 现象或问题 -> Assess -> Fix -> Review/Assess/Fix
        -> 可选 PR -> 人工决定合入
```

## 安装

准备 Python 3.11+、Git、uv，以及 CodeGraph CLI 1.x：

```bash
npm install -g @colbymchenry/codegraph@^1
uv tool install specify-cli --force \
  --from git+https://github.com/EuphoriaYan/spec-kit.git@main
```

在真实代码仓根目录执行一次初始化：

```bash
specify init . --integration codex
```

可选 integration：`codex`、`claude`、`cursor-agent`、`trae`。默认
`team` profile 安装六个主 Team Skills、可选高级扩展入口及其必要资源，并把主流程的
自然语言路由写入当前工具的规则入口。需要原生 Spec Kit 全部能力时才使用：

```bash
specify init . --integration codex --skill-profile full
```

> 当前六技能版本从本仓 `main` 安装。历史 tag
> `v0.12.5+teamwork.1` 不包含当前六技能版本；待维护者发布新的审核 tag 后，
> 安装指南会重新固定到 tag。

## 从聊天开始

新 Feature 可以直接说：

```text
请给当前系统增加 CSV 导出。导出字段要和列表展示一致，先帮我把需求澄清完整。
```

Bugfix 可以直接说：

```text
登录会话过期后接口返回 500。请先分析根因和影响范围，再决定如何修复。
```

中断后可以用 Issue URL、`work_id`、`bug_slug` 或 PR URL 继续当前阶段。详细示例见
[快速上手](docs/quickstart.md)。

## 文档

- [安装与环境诊断](docs/installation.md)
- [六技能快速上手与用户旅程](docs/quickstart.md)
- [版本升级与项目刷新](docs/upgrade.md)
- [本仓开发与测试](docs/local-development.md)
- [Team 扩展维护说明](extensions/team/README.md)
- [文档分层与语言规范](docs/README.md)

AI 运行契约位于 `extensions/team/commands/`、`extensions/team/references/`
以及被 `extensions/team/extension.yml` 安装的资源中。这些文件保持英文和稳定路径，
不与面向人的双语文档混在一起。
