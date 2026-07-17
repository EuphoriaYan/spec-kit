# 文档管理

[English backup](README_en.md)

本目录同时包含 AI Team 的面向人文档、上游 Spec Kit 高级参考和课程材料。三类内容
用途不同，不应互相复制或被 AI Skill 无差别加载。

## 面向人的 AI Team 主文档

| 主题 | 中文主文档 | 英文备用 |
|---|---|---|
| 项目入口 | [`../README.md`](../README.md) | [`../README_en.md`](../README_en.md) |
| 文档首页 | [`index.md`](index.md) | [`index_en.md`](index_en.md) |
| 安装 | [`installation.md`](installation.md) | [`installation_en.md`](installation_en.md) |
| 六技能旅程 | [`quickstart.md`](quickstart.md) | [`quickstart_en.md`](quickstart_en.md) |
| 升级 | [`upgrade.md`](upgrade.md) | [`upgrade_en.md`](upgrade_en.md) |
| 本仓开发 | [`local-development.md`](local-development.md) | [`local-development_en.md`](local-development_en.md) |
| Team 扩展维护 | [`../extensions/team/README.md`](../extensions/team/README.md) | [`../extensions/team/README_en.md`](../extensions/team/README_en.md) |

规则：

- 中文无后缀文件是事实主源；英文 `_en` 是备用阅读版本；
- 安装参数只在安装指南详细维护；
- 六个 Skill 的输入、输出和用户旅程只在快速上手详细维护；
- 首页和扩展 README 只保留摘要与链接；
- 中文主文档变化时，同一个 PR 必须同步英文备用文档。

## AI 运行契约

以下内容直接影响模型或安装行为，因此保持英文、短小、稳定路径，不创建 `_en` 副本：

- `extensions/team/commands/` 下的 Skill 主体；
- `extensions/team/references/` 下的按需引用；
- 被 `extensions/team/extension.yml` 安装的 `docs/*.md`；
- `.specify/team/context-bootstrap.md` 的源文件；
- 检查脚本、模板字段和 AGENTS 受管理入口。

不要因为“给人看起来更友好”而翻译这些运行契约。需要解释时，在人类文档中用中文
概述并链接，不复制完整规则。

## 上游参考与课程材料

`concepts/`、`reference/`、`guides/`、`community/` 和 `install/` 保留上游 Spec Kit
高级参考，默认不作为 AI Team 新用户主路径。课程 HTML 是培训材料，也不是 Skill 契约。

## 构建 DocFX

```bash
dotnet tool install -g docfx
cd docs
docfx docfx.json --serve
```

打开 `http://localhost:8080`，检查中文主导航、代码块、表格和中英文链接。
