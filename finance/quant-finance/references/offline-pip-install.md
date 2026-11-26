# Offline Python Package Installation

Use when you need to prepare offline pip packages for a machine without internet access,
or when PyPI downloads are slow from the local network.

## Workflow

### 1. Identify missing packages
```python
# Check what's installed vs. what code imports
import importlib
for pkg in ['catboost', 'umap-learn', 'ngboost']:
    try:
        m = importlib.import_module(pkg.replace('-', '_'))
        print(f'OK  {pkg}')
    except ImportError:
        print(f'MISSING  {pkg}')
```

### 2. Find correct wheel files via PyPI JSON API
```bash
# Query PyPI for available wheels, filter by platform/tag
curl -sL "https://pypi.org/pypi/<package>/json" | python3 -c "
import json,sys
d=json.load(sys.stdin)
latest=d['info']['version']
for u in d['urls']:
    fn=u['filename']
    # Windows x64 + Python 3.12: 'win_amd64' + 'cp312'
    # Pure Python (platform-independent): 'py3-none-any'
    if 'win_amd64' in fn and 'cp312' in fn:
        print(f'{fn}  ({u[\"size\"]//1024} KB)')
        print(f'URL: {u[\"url\"]}')
    elif 'py3-none-any' in fn:
        print(f'{fn}  ({u[\"size\"]//1024} KB)')
        print(f'URL: {u[\"url\"]}')
"
```

### 3. Download with mirrors for speed (China)
Default PyPI (`files.pythonhosted.org`) can be very slow from China. Use mirrors:

- **Tsinghua**: `https://pypi.tuna.tsinghua.edu.cn/packages/<hash>/<filename>`
  - The hash path is the same as the official URL — just swap the hostname.
- **Aliyun**: `https://mirrors.aliyun.com/pypi/packages/<hash>/<filename>`

```bash
curl -L -o "<filename>" "https://pypi.tuna.tsinghua.edu.cn/packages/<hash>/<filename>"
```

### 4. Write batch install script (Windows)
```batch
@echo off
cd /d "%~dp0"
pip install --no-index --find-links=. package1 package2 ...
```
- `--no-index`: don't contact PyPI, use local files only
- `--find-links=.`: search current directory for wheel files
- Transitive deps must also be in the folder (check with `pip show <pkg>` or PyPI `requires_dist`)

### 5. Check transitive dependencies
Each package's PyPI JSON includes `requires_dist` — check it before preparing:
```python
d = json.loads(response)
for req in d['info'].get('requires_dist', []):
    print(req)
```
Example: `ngboost` requires `lifelines>=0.25`, which itself needs `autograd`, `formulaic`, etc.

## Common Pitfalls
- A `py3-none-any.whl` works on ANY platform (pure Python) — no need to match OS/arch
- A `cp312-win_amd64.whl` is specific to CPython 3.12 on Windows x64
- The file might look like a valid zip (small file from interrupted download) — verify SIZE matches expected
- `pip install --no-index` will fail silently if transitive deps are missing in the folder
