# AI Team Spec Kit 文档

[English backup](index_en.md)

AI Team Spec Kit 把同一套团队开发方法安装到 Codex、Claude Code、Cursor 和 Trae。
用户从聊天框描述需求或问题，六个角色 Skill 通过 Issue、Plan、Tasks、源码和验证证据
完成交接。

## 从这里开始

1. [安装与环境诊断](installation.md)：把六个 Skills 和规则入口装进真实代码仓；
2. [六技能快速上手](quickstart.md)：完成 Feature、Bugfix、新项目和中断续接；
3. [版本升级](upgrade.md)：更新 CLI 后安全刷新项目安装；
4. [本仓开发](local-development.md)：修改安装器、Skills 或测试。

## 两条主路径

```text
Feature: Specify -> Issue 接受 -> Plan-and-Task -> Implement
         -> Review/Assess/Fix -> PR -> 人工合入

Bugfix: Assess -> Fix -> Review/Assess/Fix -> 可选 PR -> 人工合入
```

## 人与 AI 的边界

AI 可以完成需求澄清、源码分析、任务拆解、实现、自测和重复质量修复。人长期负责：

- 是否接受需求；
- HLD、跨模块边界和公共接口；
- 新依赖、安全、许可证和不兼容变化；
- 超出 Plan 的范围扩大；
- 最终是否合入。

需要理解上游原生 Spec Kit 时，可继续查阅导航中的高级参考；它们不属于默认六技能
用户路径。
