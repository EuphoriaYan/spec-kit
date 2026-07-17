# 使用 pipx 安装

[English backup](pipx_en.md)

uv 是默认方案。组织已标准化 pipx 时，可以安装当前六技能版本：

```bash
pipx install --force \
  git+https://github.com/EuphoriaYan/spec-kit.git@main
specify --version
```

然后按[安装指南](../installation.md)初始化真实代码仓。新审核 tag 发布后，应把
`@main` 替换为固定 tag。
