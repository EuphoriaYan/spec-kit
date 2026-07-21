# 安装与环境诊断

[English backup](installation_en.md)

本指南只负责把 AI Team Skills 安装进一个真实代码仓。完成后，使用者应回到
Codex、Claude Code、Cursor 或 Trae 的聊天框工作，而不是手工串联命令行工作流。

## 1. 准备基础环境

| 依赖 | 要求 | 用途 |
|---|---|---|
| Python | 3.11+ | 运行 `specify` |
| uv | 推荐当前稳定版 | 隔离安装 CLI |
| Git | 当前稳定版 | 识别代码仓、分支和变更 |
| CodeGraph | `>=1.0.0,<2.0.0` | Plan 和 Assess 的源码影响分析 |
| AI 工具 | 四选一 | 承载 Skills 和聊天入口 |

安装 CodeGraph：

```bash
npm install -g @colbymchenry/codegraph@^1
codegraph --version
```

Codex 和 Claude Code integration 需要对应 CLI 可执行文件在 `PATH` 中。Cursor 和
Trae 可以只使用 IDE Skills；只有进行无界面调度时才额外需要 Cursor CLI。

## 2. 安装 Specify CLI

当前六技能版本固定为 `v0.12.5+teamwork.2`：

```bash
uv tool install specify-cli --force \
  --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.2
specify --version
```

企业离线环境可以从已审核源码构建 wheel，再放入内部制品库。不要安装 PyPI 上同名、
但来源不明的 `specify-cli` 包。

## 3. 初始化真实代码仓

进入需要开发的代码仓根目录，只执行一次初始化：

```bash
cd <coding-repository>
specify init . --integration <integration>
```

可选值：

```text
codex | claude | cursor-agent | trae
```

示例：

```bash
specify init . --integration codex
specify init . --integration claude
specify init . --integration cursor-agent
specify init . --integration trae
```

默认 `team` profile 不安装原生 Spec Kit 的大量 Skills、templates 和 workflow。
确实需要上游完整能力时才使用：

```bash
specify init . --integration codex --skill-profile full
```

## 4. 安装后会发生什么

初始化会自动完成以下操作：

1. 安装六个主 Team Skills 和高级扩展入口到所选 AI 工具的 Skills 目录；
2. 每个 Skill 只携带自己需要的 references 和 scripts；
3. 写入 `.specify/team/context-bootstrap.md` 和可编辑配置；
4. 在 `AGENTS.md` 以及当前工具规则入口写入一段受管理的自然语言路由；
5. 把 Feature/Bugfix 工作包、`.codegraph/` 索引及生成的 `speckit-team-*`
   Skills 加入 `.gitignore`；不会整目录忽略 `.agents/` 或 `.specify/`；
6. 不要求初始化时已经安装 CodeGraph；第一次进入 Plan 或 Assess 时才检查
   CodeGraph 版本和索引状态，也不会擅自执行第三方远程安装脚本。

不同工具的主要安装位置：

| 工具 | Skills | 规则入口 |
|---|---|---|
| Codex | `.agents/skills/` | `AGENTS.md` |
| Claude Code | `.claude/skills/` | `CLAUDE.md` 导入 `AGENTS.md` |
| Cursor | `.cursor/skills/` | `.cursor/rules/specify-rules.mdc` |
| Trae | `.trae/skills/` | `.trae/rules/project_rules.md` |

扩展源码本身不会复制进业务仓，也不会随业务代码提交。

## 5. 验证安装

检查六个主 Skill 和高级扩展入口是否存在：

```text
speckit-team-specify
speckit-team-plan-and-task
speckit-team-assess
speckit-team-fix
speckit-team-implement
speckit-team-review
speckit-team-memory-consolidate
```

然后在 AI 工具聊天框输入：

```text
请告诉我当前安装了哪些 AI Team Skills，以及新 Feature 和 Bugfix 分别从哪里开始。
```

正确结果应引用仓内规则，说明 Feature 从 Specify 开始，Bugfix 从 Assess 开始。

## 6. 已有项目的 CodeGraph

在已有代码仓第一次做 Plan 或 Assess 前初始化索引：

```bash
codegraph init
codegraph status
```

AI Skill 会在分析前检查索引是否可用和新鲜。索引缺失时会先征得同意，不会用一次
源码搜索冒充完整影响分析。

## 7. 常见问题

| 现象 | 处理 |
|---|---|
| “已安装 Codex”，但初始化找不到 | 确认安装的是可执行 CLI，而非只有商店/桌面入口，并检查 `codex --version` |
| Cursor 或 Trae 没有 CLI | IDE Skills 模式可继续；不要启动依赖 CLI 的无界面调度 |
| CodeGraph 被阻断 | 安装 1.x 并确认 `codegraph --version` 可执行 |
| AI 没有自动选中 Skill | 重新打开项目聊天，确认规则入口和 Skills 目录已经生成 |
| GitCode 等平台无法自动发 Issue/PR | Skill 会输出完整可粘贴文本；人工发布只是平台传输步骤 |
| 业务仓出现 Team 扩展源码 | 安装方式不正确；业务仓只应留下生成的 Skills、规则入口和 `.specify/team/` 状态 |

下一步阅读[六技能快速上手](quickstart.md)。
