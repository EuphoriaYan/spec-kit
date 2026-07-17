# 六技能快速上手

[English backup](quickstart_en.md)

安装完成后，日常使用只需要聊天框。系统会根据“现在处于哪个阶段”选择六个主 Team
Skills；Skill 名称是可观察入口，不是用户必须背诵的口令。

## 先认识三个协作原则

1. **角色上下文隔离**：需求、架构、开发和评审不依赖隐藏聊天，以 Issue、文档和代码交接。
2. **事实有优先级**：当前源码与测试、当前 Issue/Plan、人类决策，高于模型记忆和推测。
3. **人工只守关键 Gate**：需求接受、HLD/跨模块/公共接口、依赖安全许可证与不兼容变化、超 Plan 扩围、最终合入。

## Skill 输入输出

| Skill | 最小输入 | 输出或停止条件 |
|---|---|---|
| Specify (`speckit.team.specify`) | 一句话 Feature / 新项目需求 | 澄清 User Stories；用户选择发布 Issue 或输出可复制文本 |
| Plan-and-Task (`speckit.team.plan-and-task`) | 已接受的 Feature Issue URL | 先产生 Issue 级 HLD 并等待确认，再拆单模块 Tasks 和最小自测 |
| Assess (`speckit.team.assess`) | 缺陷现象、Issue、Review finding 或 `bug_slug` | Assessment；清晰单仓单模块问题自动 `ready`，高风险才找人 |
| Fix (`speckit.team.fix`) | ready/approved Assessment | 最小修复、`fix.md`、`test.md`、进度文本并进入 Review |
| Implement (`speckit.team.implement`) | `work_id` 或 Feature Issue URL，可选 Task 范围 | 实现、证据、自动质量循环；准备 PR 前才询问 |
| Review (`speckit.team.review`) | PR URL 或本地 diff，可选工作标识 | findings、自动 Assess/Fix 重试和最终结论 |

## 高级扩展入口

`speckit.team.memory-consolidate` 不属于 Feature/Bugfix 主流程。完成工作后，只有在明确
要求沉淀经验、保存决定或把已批准规范晋升为项目 Knowledge 时才调用。普通研发请求不会
自动进入该入口。

## 旅程一：从一句话开始新 Feature

用户输入：

```text
请给当前系统增加 CSV 导出。导出字段和列表保持一致，先帮我把需求梳理清楚。
```

系统执行：

```text
Specify
-> 自然对话澄清用户、场景、User Stories 和可验证结果
-> 用户选择“创建 Issue”或“只输出 Issue 文本”
-> Issue 使用 type/feature + status/new-issue
-> 技术委员会在 Issue 中决定是否接受
```

需求被接受后，用户只需继续说：

```text
这个 Feature Issue 已经接受，请基于它做架构 Plan：<Issue URL>
```

Plan-and-Task 会读取 Issue 正文、已接受讨论、源码和 CodeGraph，先形成 HLD。此时用户
决定继续拆 Tasks、暂停讨论或修改 Plan。Tasks 默认单模块、可并行，并带最小自验证。

之后输入：

```text
Plan 和 Tasks 已确认，请实现这个 work：<work_id>
```

Implement 完成自测后会自动进入 Review；可修复的 blocker/major 问题自动走
Assess -> Fix -> Re-review，最多三轮。最终只有提交 PR 和合入决定需要用户处理。

## 旅程二：从一个现象开始 Bugfix

用户输入：

```text
登录会话过期后接口返回 500。请先定位根因，不要直接改代码。
```

系统执行：

```text
Assess
-> 保留原始现象和期望行为
-> 使用源码、测试和 CodeGraph 定位影响范围
-> 生成修复边界、根因假设和测试策略
-> 清晰的单仓单模块修复直接 ready
-> Fix -> Review -> 必要时继续 Assess/Fix
```

独立 Bugfix 不强制先有 Issue。需要团队跟踪时，Assess 可以协助创建或输出
`type/bugfix + status/new-issue` 的 Issue；如果提供了 Issue，Fix 会检查它是否进入
`status/working`。

## 旅程三：从零开始新项目

新项目仍从 Specify 开始，但 Plan 必须额外明确：

- 技术选型和依赖最小集；
- 模块、公共接口和状态所有权；
- 第一条可运行主链路；
- 部署、回滚和首个端到端验证；
- 哪些内容属于核心代码，哪些只是 examples。

一句话示例：

```text
我要新建一个内部知识问答服务，先从使用者和最小可用场景开始梳理，不要直接生成代码。
```

## 旅程四：从中间继续

| 已知信息 | 可以怎么说 |
|---|---|
| Feature Issue URL | “这个 Issue 已接受，请继续 Plan-and-Task：<URL>” |
| `work_id` | “继续实现 work_id=123，只做 T003-T005” |
| `bug_slug` | “继续修复 bug_slug=session-expiry” |
| PR URL | “评审这个 PR，并按允许范围自动修复 blocker/major：<URL>” |

本机过程目录可能不存在于另一位同事的电脑。Skill 会从 Issue/PR、当前源码和已发布交接
重建必要上下文；不会用聊天记忆补造缺失事实。

## 本地文件和 Git

```text
.specify/feature/<work_id>/   # Feature 本地工作包，默认忽略
.specify/bugfix/<bug_slug>/   # Bugfix 本地工作包，默认忽略
.specify/team/                # 稳定安装配置和上下文入口
AGENTS.md / 工具规则文件       # 受管理的自然语言路由
```

跨成员长期共享的是 Issue、PR、源码、测试，以及经过评审后明确晋升的架构或项目知识。
不要把本地工作包、原始客户隐私、临时提示词和聊天记录提交进业务仓。

## 平台自动化不可用时

GitHub 可以使用集成或 `gh` 自动读取和发布。GitCode 等平台没有可用 API/CLI 时，
Skill 会在聊天输出完整的 Issue、Plan handoff、PR 描述或 Review 评论。用户只需把文本
粘贴到平台；这属于传输操作，不是新增技术审批。
