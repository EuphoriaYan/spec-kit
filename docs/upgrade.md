# 版本升级与项目刷新

[English backup](upgrade_en.md)

AI Team 发行版不会自动跟随上游 Spec Kit 更新。CLI 版本、Team Skills 和项目内生成文件
是三个不同层次，升级时必须分别确认。

## 当前版本策略

- 上游代码基线固定为 Spec Kit `v0.12.5`；
- 当前六技能发行版固定为 `v0.12.5+teamwork.3`；
- 历史 tag `v0.12.5+teamwork.1` 和 `v0.12.5+teamwork.2` 仅用于版本追溯；
- 不使用 `specify self check` 或 `specify self upgrade` 自动漂移到其他版本。

## 更新本机 CLI

```bash
uv tool install specify-cli --force \
  --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.3
specify --version
```

企业环境应把审核过的 commit 或 wheel 固定在内部制品库，不要让每台开发机在不同时间
直接追踪变化中的 `main`。

## 刷新项目安装

更新 CLI 不会自动覆盖业务仓文件。进入代码仓，先提交或暂存当前改动，然后执行：

```bash
specify init . --integration <codex|claude|cursor-agent|trae>
git diff
```

重点检查：

- 六个 Team Skills 是否更新；
- `AGENTS.md` 和工具规则中只有一段受管理入口；
- 项目自有规则没有被覆盖；
- `.specify/team/ai-team-config.yml` 的项目配置仍被保留；
- `.gitignore` 继续忽略 Feature/Bugfix 本地工作包；
- 没有突然安装 `full` profile 的原生命令。

不要在已有项目中随意使用破坏性 `--force` 覆盖项目自有文件。出现冲突时，应先比较
生成文件与项目规则，再决定迁移方式。

## 发布新固定版本

`teamwork.3` 的发布顺序是：合并实现 PR，在合并提交上创建
`v0.12.5+teamwork.3` tag，然后从该 tag 执行上述安装命令和四种 integration
冒烟验证。tag 创建前不得对外宣称该安装命令已经可用。

维护者发布后续 Teamwork tag 时，需要同时完成：

1. 六技能安装和四种 integration 的样例验证；
2. 更新中文与英文安装文档中的版本来源；
3. 记录 CodeGraph 和 Python 最低版本；
4. 说明生成文件变化和项目刷新步骤；
5. 提供从上一审核版本升级的回滚方式。
