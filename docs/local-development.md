# 本仓开发与验证

[English backup](local-development_en.md)

本指南面向维护 AI Team Spec Kit 本身的贡献者，不是业务仓使用者。

## 本地环境

```bash
git clone git@github.com:EuphoriaYan/spec-kit.git
cd spec-kit
git checkout -b <your-branch>

uv venv
uv pip install -e .
specify --help
```

也可以不安装入口，直接从当前源码运行：

```bash
PYTHONPATH=src python -m specify_cli --help
```

## 在临时业务仓验证安装

不要直接用本仓目录模拟业务仓。创建临时目录并安装本地构建：

```bash
mkdir <temporary-project>
cd <temporary-project>
uvx --from <path-to-spec-kit> specify init . --integration codex
```

至少检查：

- 安装六个主 Team Skills 和声明的高级扩展入口；
- 每个 Skill 只有自己声明的 references/scripts；
- AGENTS 和工具规则入口可读且幂等；
- Feature/Bugfix 本地目录被忽略；
- 项目既有规则和配置未被覆盖；
- Cursor/Trae IDE-only 与 Codex/Claude CLI 检查符合预期。

## 测试

```bash
PYTHONPATH=src python -m pytest -q tests/extensions
PYTHONPATH=src python -m pytest -q tests/unit/test_bundled_bundle.py
python -m ruff check src extensions tests
```

修改安装、integration 或打包逻辑时，扩大到对应 integration 和 CLI 测试。测试环境存在
另一个 editable install 时，显式设置 `PYTHONPATH=src`，避免加载错误工作树。

## 文档规则

- 面向人的 AI Team 文档：中文文件是主文档，英文使用 `_en` 后缀；
- AI Skills、references、脚本契约和 AGENTS 规则：保持英文、稳定路径和简短表达；
- 一项事实只在一个主文档详细说明，其他页面使用链接；
- 修改 Skill 输入、输出或停止条件时，同步更新快速上手和对应安装测试；
- 不把课程 HTML 当作运行契约，也不让 AI Skill 依赖课程材料。

## 提交前

确认 diff 不包含临时项目、`.specify/feature/`、`.specify/bugfix/`、CodeGraph 数据库、
本地记忆或凭据。PR 应说明影响的是 CLI、安装、某个 Skill、AI 契约还是人类文档。
