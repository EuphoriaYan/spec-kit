# Team Extension 改造方案

**状态**: 草案  
**范围**: `team` extension 下的 `implement`、`review`（及后续 `plan-task`）；暂不改造 workflow  
**前提**: 所有 spec / plan / task / work context 文件统一放在 `.specify/specs/{feature-slug}/`

---

## 1. 背景与目标

### 1.1 现状问题

当前 AI Team SDD 能力分散在多处，实施与审查强依赖长 workflow：

| 能力 | 当前位置 |
|------|----------|
| Work context 加载 | workflow step `context-open` → `speckit.ai-team.context` |
| Plan / tasks 就绪检查 | `plan-check`、`analyze` + 多个 workflow gate |
| 实施权限 | `permissions` + gate + `enforce-implementation-permission.py` |
| 写代码 | core `speckit.implement`（与 ai-team 治理脱节） |
| 测试与验收 | `converge` preset wrap + `finalize-work-evidence.py` |
| 创建 PR | `speckit.ai-team.pr`（与 implement 分离） |
| PR 代码 review | `speckit.ai-team.review`（无 PR 一等输入，绑在文档流程里） |

artifact 路径也不统一：SDD 文件在 repo-root `specs/{slug}/`，work context 在 `.specify/ai-team/work/{slug}/`。

### 1.2 改造目标

1. **新建 `team` extension**，与现有 `ai-team` 并列；`ai-team` 保留协作基础设施，本次不删改其既有命令。
2. **收敛两个执行层命令**，职责边界清晰：

   | 命令 | 输入 | 输出 |
   |------|------|------|
   | **`speckit.team.implement`** | `feature_slug` + **`tasks.md`**（及 plan/spec 上下文） | **代码** + **测试结果**；**PR 可选**（用户确认后才创建） |
   | **`speckit.team.review`** | **PR**（URL 或 number） | 审查报告 + merge recommendation |

3. **统一 artifact 根路径**：`.specify/specs/{feature-slug}/`（其他命令的路径迁移后续单独做）。
4. **第一版不改造 workflow**；两个命令独立可用，验证通过后再精简 workflow。

### 1.3 非目标（本阶段）

- 不修改 `workflows/ai-team-sdd/workflow.yml` 等 workflow 文件
- 不删除 `ai-team` 中的 `speckit.ai-team.pr` / `speckit.ai-team.review`（迁移完成后另开 PR）
- 不改造 `specify` / `plan` / `tasks` 等核心命令的路径（由后续任务完成）
- 不实现完整的 evidence board / codegraph 生成（implement 写简化 implementation-report）

---

## 2. 目标架构

### 2.1 执行层契约（核心）

```text
                    ┌──────────────────────────────────────┐
  输入               │     speckit.team.implement           │  必需输出
                     │                                      │
  feature_slug       │  Context → Readiness → Permission    │  ① 代码变更（仓库 diff）
  tasks.md  ────────►│  → Execute → Verify                  │  ② 测试结果（Verification Report）
  (+ plan/spec)      │           │                          │
                     │           ▼ 询问用户是否提交 PR       │  可选输出
                     │     [是] → 渐进加载 implement-pr.md  │  ③ PR（URL + description）
                     └──────────────────────────────────────┘
                                          │
                                          │ PR URL（若已创建）
                                          ▼
                     ┌──────────────────────────────────────┐
  输入               │     speckit.team.review              │  输出
  PR URL/number ────►│  Fetch → Code review → SDD align     │  findings + merge recommendation
                     └──────────────────────────────────────┘
```

**上游**（本方案不实现）：`plan-task` 或核心 `plan`/`tasks` 命令产出/修订 `tasks.md`。  
**下游**：用户选择提交 PR 后，可调用 `review` 审查；未提交 PR 时 implement 仍以代码 + 测试为完成态。

### 2.2 组件分层

```text
┌─────────────────────────────────────────────────────────────┐
│  ai-team extension（保留，后续逐步瘦身）                      │
│  workspace / context / permissions / codegraph / handoff /  │
│  plan-check / feature-review / workflows / ...                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  team extension（新建）                                       │
│  speckit.team.plan-task   ← 后续：修订 plan + tasks         │
│  speckit.team.implement   ← 五段式核心 + 可选 PR（渐进加载）  │
│  prompts/implement-pr.md  ← PR 专用 prompt，按需加载           │
│  speckit.team.review      ← PR 代码审查                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
              .specify/specs/{feature-slug}/   ← 唯一 artifact 根
```

### 2.3 终局 workflow 形态（参考，本阶段不实施）

```text
上游（artifact 生产）
  specify → plan → tasks   （或 plan-task 修订）
        ↓
执行层（team extension）
  speckit.team.implement   → 代码 + 测试；（可选）PR
        ↓
  speckit.team.review      → 审查 PR（若已创建）
```

---

## 3. 统一路径约定

### 3.1 Feature 根目录

```text
FEATURE_ROOT = {repo}/.specify/specs/{feature-slug}/
```

`feature-slug` 与历史 `work_slug` 同义（例如 `003-search-export`）。

### 3.2 目录布局

```text
.specify/specs/{feature-slug}/
├── spec.md                      # 行为规格
├── spec.override.md             # handoff 覆盖（可选，优先于 spec）
├── plan.md                      # 技术方案
├── tasks.md                     # 任务列表 ← implement 的核心输入
├── work-context.yml             # phase、work item、pr_url、命令索引
├── context-pack.md              # 人类可读的 resume 摘要
├── permission-envelope.yml      # 实施权限 envelope
├── handoffs/                    # 角色 handoff（可选）
├── evidence/
│   ├── implementation-report.md # implement Phase 5 产出（含测试结果）
│   └── review-report.md         # review 产出（可选）
└── codegraph/                   # 影响分析（可选，有则读）
```

### 3.3 解析 `feature-slug`

两命令共用，优先级：

1. 用户输入 `feature_slug=<slug>`
2. 读 `.specify/feature.json` 的 `feature_directory`，取 basename（期望值为 `.specify/specs/{slug}`）

**硬规则（写进 command prompt）**：

- 禁止读写 repo-root `specs/` 与 `.specify/ai-team/work/`（旧路径）
- 所有路径相对于 `FEATURE_ROOT` 或使用绝对路径

### 3.4 `work-context.yml` 最小字段

```yaml
feature_slug: 003-search-export
feature_root: .specify/specs/003-search-export
phase: specified | planned | tasks-ready | implementing | verified | pr-open | review | done
coding_issue_url: ""
handoff_requirement_url: ""
pr_url: ""                        # 用户确认提交 PR 后写入（可选）
artifacts:
  spec: spec.md
  plan: plan.md
  tasks: tasks.md
last_completed_command: ""
next_command: ""                  # 有 pr_url 时可建议 speckit.team.review
updated_at: ""
```

---

## 4. Team Extension 包结构

```text
extensions/team/
├── extension.yml
├── README.md
├── commands/
│   ├── speckit.team.implement.md   # Phase 1–5 + 询问是否 PR（不含 PR 细则）
│   ├── speckit.team.review.md
│   └── prompts/
│       └── implement-pr.md         # PR 预检、description 模板、gh 命令（按需加载）
└── scripts/                        # 可选，后续
    └── fetch-pr-context.py
```

**渐进式加载**：主命令 `speckit.team.implement.md` 保持精简，避免常驻 PR 相关 prompt 占用 context。仅在 Verify 完成后、且用户同意（或传入 `submit_pr=true`）时，**读取并执行** `commands/prompts/implement-pr.md` 中的 Phase 6 指令。

### 4.1 `extension.yml` 要点

```yaml
extension:
  id: team
  name: "Team Implement & Review"
  version: "0.1.0"

requires:
  speckit_version: ">=0.12.4"
  tools:
    - name: gh
      required: false   # 可选 PR 与 review 需要；缺失时跳过 PR 或降级为 manual checklist

provides:
  commands:
    - name: speckit.team.implement
      file: commands/speckit.team.implement.md
    - name: speckit.team.review
      file: commands/speckit.team.review.md
```

**平台约束**：extension 命令名必须为 `speckit.{extension-id}.{command}`。workflow 迁移前可用 alias `speckit.implement` 作过渡（可选）。

---

## 5. `speckit.team.implement`

### 5.1 输入 / 输出契约

| | 内容 |
|---|------|
| **输入（必需）** | `feature_slug`；`{FEATURE_ROOT}/tasks.md`（及 Readiness 所需的 plan.md、spec） |
| **输入（可选）** | `only=T001-T010` 限定 task 范围；`submit_pr=true` 跳过询问、直接走 PR 流程 |
| **输出（必需）** | ① 仓库中的**代码变更**；② **测试结果**（Verification Report） |
| **输出（可选）** | ③ **PR**（URL + description）— 仅当用户确认或 `submit_pr=true` |
| **输出（写入 artifact）** | `tasks.md`（`[x]`）、`evidence/implementation-report.md`、`work-context.yml`、`context-pack.md`；`pr_url` 仅 PR 成功时写入 |

**implement 完成定义**：Phase 5 Verify 通过即视为完成（代码 + 测试就绪）。**不强制创建 PR**。

Verify 失败后不算完成，不进入 PR 询问或 PR 流程。

### 5.2 职责：五 Phase 核心 + 可选 PR

主命令包含 **Phase 1–5**；**Phase 6 PR 为可选**，逻辑放在独立文件 `commands/prompts/implement-pr.md`，按需加载。

| Phase | 吸收的原能力 | 说明 | 所在文件 |
|-------|-------------|------|----------|
| 1 Context | `ai-team.context` 的 load/resume | 定位 FEATURE_ROOT，读 context / envelope | `implement.md` |
| 2 Readiness | `plan-check` + `analyze` | **只读**检查 plan / tasks / spec；失败 → plan-task | `implement.md` |
| 3 Permission | `permissions mode=implementation` + enforce | 读 envelope，校验 write paths | `implement.md` |
| 4 Execute | core `implement` | 按 **tasks.md** 写代码，标记 `[x]` | `implement.md` |
| 5 Verify | `converge` checks 精华 | 跑 build/test，写 implementation-report | `implement.md` |
| 6 Pull Request（**可选**） | `ai-team.pr` | 用户确认后加载 `implement-pr.md` 执行 | `prompts/implement-pr.md` |

参考底稿：`templates/commands/implement.md`（checklist / ignore / hooks **不搬**）；PR 段参考 `ai-team.pr`，**全部**放入 `implement-pr.md`。

### 5.3 输入示例

```text
/speckit.team.implement feature_slug=003-search-export
/speckit.team.implement feature_slug=003-search-export only=T001-T010
/speckit.team.implement feature_slug=003-search-export submit_pr=true
```

### 5.4 读写矩阵

| Phase | 读 | 写 |
|-------|----|----|
| 1 Context | `work-context.yml`, `context-pack.md`, `permission-envelope.yml` | `work-context.yml`（`phase: implementing`） |
| 2 Readiness | `spec.override.md` → `spec.md`, `plan.md`, **`tasks.md`**, `handoffs/*`, `codegraph/*` | `context-pack.md`（Readiness 段） |
| 3 Permission | `permission-envelope.yml`, `plan.md` | envelope status/timestamp |
| 4 Execute | **`tasks.md`**, `plan.md` | **`tasks.md`（`[x]`）**、源码 |
| 5 Verify | git diff, `plan.md` change-scope | `evidence/implementation-report.md`, `work-context.yml`（`phase: verified`）, `context-pack.md` |
| 6 PR（可选） | 见 `implement-pr.md` | `pr_url`, `phase: pr-open`（仅 PR 成功时） |

**禁止**：Phase 2–4 修改 `plan.md` / `spec.md` 正文；Phase 4 之外不改 tasks 内容（仅 checkbox）。

### 5.5 Verify 完成后的 PR 询问（主命令内，简短）

Phase 5 通过后，在主命令中**仅输出简短询问**（不嵌入 PR 细则）：

```text
Implementation and verification complete.

Submit a pull request for this feature? (yes/no)
```

| 用户响应 | 行为 |
|----------|------|
| `yes` / `submit_pr=true` | **读取** `{extension}/commands/prompts/implement-pr.md`，继续 Phase 6 |
| `no` / 未确认 | 结束；`work-context.yml` 保持 `phase: verified`；Completion Report 不含 PR |
| Verify 未通过 | **不询问** PR，直接 Completion Report + 修复建议 |

主命令中通过相对路径加载 PR prompt（安装后位于 `.specify/extensions/team/commands/prompts/implement-pr.md`）。

### 5.6 Phase 6 — Pull Request（`prompts/implement-pr.md`）

**独立文件**，仅在用户确认或 `submit_pr=true` 时加载，用于**减少主命令常驻 token**。

Verify 已通过；本阶段失败**不影响** implement 核心完成态（代码 + 测试仍有效），仅 PR 未创建。

**Pre-submit 检查**（路径均相对 FEATURE_ROOT / 仓库根）：

1. `git status` — 当前分支非 default branch
2. diff 仅含 intended 变更；不含 `.ai-local/`、scratch、`spec.override.md`、private drafts
3. PR 关联 work item：`work-context.yml` 中 `coding_issue_url` 或 `handoff_requirement_url`（feature 至少其一）
4. diff 文件 ⊆ `permission-envelope.yml` allowed paths
5. `evidence/implementation-report.md` 中测试结果已记录

**PR description 模板**、**`gh pr create` 步骤**、**Stop Conditions** 均写在此文件中（从原 5.5 节迁入，不在此方案正文重复）。

**Phase 6 成功**：`pr_url` 写入 `work-context.yml`，`phase: pr-open`，建议 `/speckit.team.review {pr_url}`。

**Phase 6 失败或跳过**：不更新 `pr_url`；`phase` 保持 `verified`；输出失败原因或 manual PR checklist。

### 5.7 Readiness 失败策略（已拍板）

存在 **blocker** 时：

1. 输出 **Readiness Report**（`Status: BLOCKED`）
2. **立即 STOP**，不进入 Phase 3–5（及 PR 流程）
3. **不建议** “是否仍继续实施”
4. 固定提示：

```text
Revise artifacts with:
  /speckit.team.plan-task feature_slug={feature-slug}

Then re-run:
  /speckit.team.implement feature_slug={feature-slug}
```

#### Readiness Report 模板

```markdown
## Readiness Report

- **Feature slug**:
- **Feature root**: `.specify/specs/{feature-slug}/`
- **Status**: BLOCKED | PASS

### Plan issues
- [blocker/major/minor] ...

### Tasks issues
- [blocker/major/minor] ...

### Cross-artifact gaps
- ...

### Recommended action

（BLOCKED 时）
Readiness blocked. Do not proceed with implementation.
Run `/speckit.team.plan-task feature_slug={feature-slug}` using the issues above,
then re-run `/speckit.team.implement feature_slug={feature-slug}`.
```

### 5.8 一次调用的输出结构

```text
## Context Summary
## Readiness Report           ← Phase 2；BLOCKED 则 Phase 3–5 不执行
## Permission Check           ← Phase 3
## Implementation Progress    ← Phase 4（代码）
## Verification Report        ← Phase 5（测试结果）
## Pull Request               ← 仅用户确认 PR 且加载 implement-pr.md 后
```

**Completion Report（Done When）— 核心完成态**：

- [ ] `{FEATURE_ROOT}/tasks.md` 中目标 task 均已 `[x]`
- [ ] Verification Report 记录 build/test 结果
- [ ] `work-context.yml` 更新为 `phase: verified`

**若用户确认并成功提交 PR（可选）**：

- [ ] PR URL 写入 `work-context.yml`
- [ ] 建议下一步：`/speckit.team.review {pr_url} feature_slug={feature-slug}`

---

## 6. `speckit.team.review`

### 6.1 输入 / 输出契约

| | 内容 |
|---|------|
| **输入** | **PR**（URL 或 number）；可选 `feature_slug` 加速 SDD 对照 |
| **输出** | Review findings + merge recommendation；可选 `evidence/review-report.md` |

implement 在用户选择提交 PR 后可产出 PR → review 审查该 PR；**review 不创建 PR**。无 PR 时可仅做本地 commit，不调用 review。

### 6.2 职责

| Phase | 说明 |
|-------|------|
| 1 Fetch PR | `gh pr view` / `gh pr diff` |
| 2 Code review | diff 正确性、测试、安全、最小改动、兼容性 |
| 3 SDD alignment | 对照 FEATURE_ROOT 下 spec/plan/tasks/evidence/envelope；对照 implement 产出的 PR description |
| 4 Verdict | findings + merge recommendation |

### 6.3 输入示例

```text
/speckit.team.review https://github.com/org/repo/pull/123
/speckit.team.review pr=123 feature_slug=003-search-export
```

推荐：implement 结束后直接使用 `work-context.yml` 中的 `pr_url`。

### 6.4 关联 PR → feature-slug

1. 用户输入 `feature_slug=`
2. `work-context.yml` 的 `pr_url` 同 feature 目录
3. PR body 中的 `Feature slug:` / `Feature root:`
4. PR branch 名匹配 `{feature-slug}`

### 6.5 读写

| Phase | 读 | 写 |
|-------|----|----|
| 1–2 | PR metadata + diff | — |
| 3 | `FEATURE_ROOT` 下 artifacts + `evidence/implementation-report.md` | — |
| 4 | 汇总 | `evidence/review-report.md`（可选）, `work-context.yml`（`phase: review`） |

---

## 7. 后续命令：`speckit.team.plan-task`

本方案仅定义接口，**第一版不实现**。

| 项 | 说明 |
|----|------|
| 职责 | 根据 Readiness Report 或用户输入修订 `plan.md`、`tasks.md` |
| 路径 | 仅读写 `.specify/specs/{feature-slug}/` |
| 触发 | implement Readiness BLOCKED 后用户手动调用 |
| 不写 | 不改源代码、不跑测试、不创建 PR |

---

## 8. 与 ai-team 的关系

| 组件 | 本阶段 | 后续 |
|------|--------|------|
| `ai-team` extension | 保持不动 | 删除迁走的 `speckit.ai-team.pr`、`speckit.ai-team.review`；路径文档更新 |
| `ai-team-sdd-governance` preset | 保持不动 | 路径改指向 `.specify/specs/` 后调整 prepend/wrap |
| `bundles/ai-team/bundle.yml` | 暂不加入 `team` | 验证通过后增加 `team` extension |
| core `speckit.implement` | 保持 fallback | 未装 team 时仍可用 |

---

## 9. 实施计划

### Phase A — 文档与 scaffold

- [x] 本改造方案（`docs/plans/team-extension-refactor.md`）
- [x] `extensions/team/extension.yml`
- [x] `extensions/team/README.md`
- [x] `extensions/team/commands/speckit.team.implement.md`（Phase 1–5 + PR 询问）
- [x] `extensions/team/commands/prompts/implement-pr.md`（Phase 6，按需加载）
- [x] `extensions/team/commands/speckit.team.review.md`

### Phase B — 本地验证

- [x] `specify extension add team --dev extensions/team`
- [ ] 准备 `.specify/specs/{slug}/` 测试 fixture（plan/tasks/context/envelope）
- [ ] implement：Verify 通过 → 代码 + 测试报告，`phase: verified`（不强制 PR）
- [ ] implement：用户确认 PR → 加载 implement-pr.md → PR URL
- [ ] implement：Readiness BLOCKED → 提示 plan-task
- [ ] review：对已创建的 PR 做审查

### Phase C — 路径迁移（与其他命令协同）

- [ ] 核心命令与脚本改为 `.specify/specs/{slug}/`
- [ ] 更新 `feature.json` 写入路径

### Phase D — 集成与清理

- [ ] bundle 加入 `team`
- [ ] workflow 精简为 `implement` → `review` 两步
- [ ] 实现 `speckit.team.plan-task`
- [ ] 废弃 `ai-team.pr` / `ai-team.review`

---

## 10. 验证清单

### implement

- [ ] 以 `tasks.md` 为执行输入，完成后 task 均为 `[x]`
- [ ] Readiness blocker → STOP + plan-task 提示
- [ ] Verify 失败 → 不询问 PR、不加载 implement-pr.md
- [ ] Verify 通过 → 完成态为代码 + 测试；**不强制 PR**
- [ ] 用户拒绝 PR → `phase: verified`，无 `pr_url`
- [ ] 用户确认 PR → 加载 `implement-pr.md`，成功则写入 `pr_url`
- [ ] 主命令不含 PR 细则（token 精简）
- [ ] 仅使用 `.specify/specs/{slug}/` 路径

### review

- [ ] 输入为 implement 产出的 PR
- [ ] SDD alignment 对照 FEATURE_ROOT artifacts
- [ ] 输出 merge recommendation

---

## 11. 风险与缓解

| 风险 | 缓解 |
|------|------|
| implement 主命令仍过长 | Phase 1–5 精简；PR 拆到 `implement-pr.md` |
| 渐进加载失败（找不到 implement-pr.md） | 安装路径写死在 extension 内；README 说明 dev 布局 |
| 用户跳过 PR 后不知如何 review | Completion Report 说明：有 PR 时再调用 review |
| 无 `gh` CLI | implement-pr.md 内降级：manual checklist + 待粘贴 description |
| Verify 通过但 PR 预检失败 | PR 失败不影响 `phase: verified`；单独报告 PR 错误 |

---

## 12. 决策记录

| 日期 | 决策 |
|------|------|
| — | 新建 `team` extension，不并入 `ai-team` |
| — | artifact 统一至 `.specify/specs/{feature-slug}/` |
| — | **implement 输入 = tasks；必需输出 = 代码 + 测试结果** |
| — | **PR 可选**：Verify 后询问用户；`submit_pr=true` 可跳过询问 |
| — | **PR prompt 渐进加载**：细则在 `commands/prompts/implement-pr.md` |
| — | review 输入 = PR；在用户选择提交 PR 后使用 |
| — | plan/tasks 有问题：STOP + plan-task，不自动修订 |
| — | 第一版不改造 workflow |

---

## 附录 A：旧路径 → 新路径

| 旧路径 | 新路径 |
|--------|--------|
| `specs/{slug}/spec.md` | `.specify/specs/{slug}/spec.md` |
| `specs/{slug}/plan.md` | `.specify/specs/{slug}/plan.md` |
| `specs/{slug}/tasks.md` | `.specify/specs/{slug}/tasks.md` |
| `.specify/ai-team/work/{slug}/work-context.yml` | `.specify/specs/{slug}/work-context.yml` |
| `.specify/ai-team/work/{slug}/permission-envelope.yml` | `.specify/specs/{slug}/permission-envelope.yml` |
| `.specify/ai-team/work/{slug}/evidence/` | `.specify/specs/{slug}/evidence/` |

## 附录 B：workflow 节点合并对照（implement）

```text
context-open (读)           → Phase 1 Context
plan-check + analyze        → Phase 2 Readiness
review-plan/tasks gates     → Phase 2 BLOCKED + plan-task
permissions + enforce       → Phase 3 Permission
implement (写代码)          → Phase 4 Execute
converge checks + 测试      → Phase 5 Verify
ai-team.pr (创建 PR)        → 可选 Phase 6（implement-pr.md，用户确认后）
finalize-work-evidence      → Phase 5 implementation-report（简化）

下游（可选）：
speckit.team.review         → 用户提交 PR 后审查
```

## 附录 C：三命令 I/O 总览

```text
plan-task    输入: feature_slug + 修订意图          输出: 修订后的 plan.md, tasks.md

implement    输入: feature_slug + tasks.md (+上下文)  必需输出: 代码, 测试报告
                                                    可选输出: PR（用户确认后）

review       输入: PR (+ feature_slug)               输出: 审查报告, merge 建议
```

## 附录 D：`implement-pr.md` 应包含的内容（ checklist）

独立文件，不在主命令中重复：

- Pre-submit 检查清单（branch、diff 排除项、work item、envelope）
- PR title / body 模板
- `gh pr create` 命令示例
- Stop Conditions（缺 gh、private leak、无 issue 链接等）
- 成功后更新 `work-context.yml`（`pr_url`, `phase: pr-open`）
- 失败时的 manual PR fallback
