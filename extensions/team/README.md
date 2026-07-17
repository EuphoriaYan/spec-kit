# Team 扩展维护说明

[English backup](README_en.md)

`team` 扩展提供六个面向交付阶段的 Skills，不修改原生 Spec Kit commands。
本页面向扩展维护者；普通使用者请阅读[六技能快速上手](../../docs/quickstart.md)。

## 职责边界

| Skill | 角色 | 读取 | 产出 |
|---|---|---|---|
| `speckit.team.specify` | 业务 / 产品 | 一句话 Feature 或新项目需求 | Feature Issue；不落本地 Spec 草稿 |
| `speckit.team.plan-and-task` | 架构 / 模块负责人 | 已接受 Issue、源码、CodeGraph | `spec.md`、Issue 级 HLD、模块 Tasks、自测和检查 |
| `speckit.team.assess` | 缺陷分析 | 现象、Issue 或 Review finding | `assessment.md` 和风险路由 |
| `speckit.team.fix` | 缺陷修复 | ready/approved Assessment | 最小修复、`fix.md`、`test.md` 和 Review handoff |
| `speckit.team.implement` | 开发 | checked Plan/Tasks 和 Permission Envelope | 代码、实现证据和自动质量循环 |
| `speckit.team.review` | 评审 | PR 或本地 diff | findings、修复路由和合入建议 |

## 高级扩展入口

高级扩展会随默认 Team 安装提供，但不是交付角色，不参与 Feature 或 Bugfix 自动路由。

| 入口 | 使用者 | 读取 | 产出 |
|---|---|---|---|
| `speckit.team.memory-consolidate` | Contributor / Maintainer | 已完成工作、证据或已审核决定 | 建议性 Memory，或经人工批准的项目 Knowledge |

该入口仅在明确提出交付后维护请求时调用。本地和部门 Memory 保持建议性并进入
Git ignore；只有带负责人、批准、证据和作用域的内容，才能晋升到
`docs/ai-team/knowledge/rules/` 并约束后续角色。

角色之间不依赖隐藏聊天。Feature 由 Issue 承担需求事实，Plan/Task handoff 承担架构与
实现边界，PR 和测试承担交付事实。Bugfix 保留原始现象和 Assessment，避免在自动修复
循环中错误归因。

## 安装模型

默认 `team` profile 直接从已安装的 Specify CLI 包注册六个主 Skill 和按需使用的高级入口：

```text
speckit-team-<role>/
|-- SKILL.md
|-- references/   # 仅该角色需要的渐进上下文
`-- scripts/      # 仅该角色需要的确定性检查
```

扩展实现不会复制到业务仓。业务仓只保留：

```text
.<tool>/skills/...
.specify/team/context-bootstrap.md
.specify/team/ai-team-config.yml
AGENTS.md 和工具规则中的受管理入口
```

`init_role_context.py` 在初始化时执行，合并而非替换项目已有规则。Claude Code 的
`CLAUDE.md` 只导入 `AGENTS.md`；Cursor 和 Trae 写入各自规则入口。

## 本地工作包

```text
.specify/feature/<work_id>/
|-- spec.md
|-- plan-and-task.md
|-- plan-and-task-check.md
|-- work-context.yml
|-- context-pack.md
|-- permission-envelope.yml
|-- codegraph/
`-- evidence/

.specify/bugfix/<bug_slug>/
|-- assessment.md
|-- fix.md
|-- test.md
|-- work-context.yml
|-- context-pack.md
`-- evidence/
```

两个工作根默认进入 `.gitignore`。跨成员事实通过 Issue、PR、源码、测试和明确晋升的
HLD/项目知识共享，不通过提交本地工作包共享。

## 关键 Gate

- Plan-and-Task 必须使用 CodeGraph，并运行安装到 Skill 内的
  `check_plan_and_task.py`；模型不得手写通过报告。
- Permission Envelope 是风险边界，不是运行时沙箱；单仓单模块、无永久 Gate 的批次可
  自动 ready。
- Implement 后自动进入 Review；可修复 blocker/major 最多自动循环三轮。
- Review 只给 `GO`、`GO-WITH-RISK` 或 `NO-GO`，不替人 approve/merge。
- 永久人工决定只有需求接受、HLD/跨模块/公共接口、依赖安全许可证与不兼容变化、
  超 Plan 扩围和最终合入。

## 修改扩展

`extension.yml` 是 Skill 与资源安装清单。每个命令引用的文件必须显式列在自己的
`resources` 中，Skill 内路径必须相对自身目录可解析。不要让 Skill 读取扩展源码仓中的
隐式相对路径。

在临时项目中调试本地扩展时可以使用：

```bash
specify extension add extensions/team --dev
```

验证：

```bash
PYTHONPATH=src python -m pytest -q tests/extensions
PYTHONPATH=src python -m pytest -q tests/unit/test_bundled_bundle.py
```

面向人的使用说明放在中文主文档及 `_en` 备用文档；Skill、references、bootstrap、
模板和脚本契约保持英文。详见[文档管理](../../docs/README.md)。
