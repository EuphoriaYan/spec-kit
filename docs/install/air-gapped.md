# 企业离线安装

[English backup](air-gapped_en.md)

离线环境应由维护者在联网构建机上固定审核 commit，构建 wheel 和依赖包，再发布到内部
制品库。不要把个人虚拟环境整体复制给团队。

```bash
git clone git@github.com:EuphoriaYan/spec-kit.git
cd spec-kit
git checkout <reviewed-commit>
uv build
```

同时准备：

- Python 3.11+ 和 uv/pipx 的内部安装源；
- CodeGraph CLI 1.x 的已审核内部安装包；
- Codex/Claude CLI 或 Cursor/Trae IDE 的企业安装方式；
- Git 远端、代理、证书和 Issue/PR 平台访问配置。

离线安装完成后，仍按[安装指南](../installation.md)验证六个 Skills、规则入口、
CodeGraph 和 `.gitignore`。禁止把 API key、客户需求正文或本地工作包打进 wheel。
