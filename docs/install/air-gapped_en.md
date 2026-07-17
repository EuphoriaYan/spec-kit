# Enterprise and Air-Gapped Installation

[中文主文档](air-gapped.md)

On a connected build machine, pin a reviewed commit, build the wheel and
dependencies, and publish them to an internal artifact repository:

```bash
git clone git@github.com:EuphoriaYan/spec-kit.git
cd spec-kit
git checkout <reviewed-commit>
uv build
```

Also provide approved internal packages for Python, uv or pipx, CodeGraph CLI
1.x, the selected AI tool, Git credentials, proxies, and certificates. Validate
the six Skills and managed rules using the
[installation guide](../installation_en.md). Never package credentials, private
requirements, or local work packages.
