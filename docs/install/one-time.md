# 一次性试用

[English backup](one-time_en.md)

一次性试用不会更新 `PATH` 中已有的 `specify`：

```bash
uvx --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.3 \
  specify init . --integration codex
```

它适合临时样例，不适合团队长期环境。正式团队应固定同一 commit、tag 或内部 wheel，
避免成员在不同时间得到不同 Skills。
