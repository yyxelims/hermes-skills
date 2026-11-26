---
name: python-env
description: Python environment and package management skill. Use when user needs to create/manage virtual environments, install/upgrade/uninstall packages, fix dependency issues, manage pip/poetry/uv, check Python versions, or deal with SSL/certificate problems on macOS. Covers venv, pip, poetry, uv, pipx, requirements.txt freezing, and common troubleshooting (trusted-host, certificate errors, broken deps).
argument-hint: "[create|install|fix|list|freeze|upgrade|clean]"
---

# Python Environment & Package Management

Manage Python virtual environments and packages on macOS. Covers the full lifecycle: creating envs, installing packages, resolving dependency issues, and cleaning up.

## Quick Reference

| User says | Action |
|---|---|
| "create a venv" / "new python project" | `python3 -m venv .venv && source .venv/bin/activate` |
| "install X" / "add package X" | `pip install X` (inside venv) |
| "freeze" / "export requirements" | `pip freeze > requirements.txt` |
| "install from requirements" | `pip install -r requirements.txt` |
| "what's installed?" | `pip list` or `pip list --outdated` |
| "upgrade everything" | `pip list --outdated --format=freeze \| cut -d= -f1 \| xargs -n1 pip install -U` |
| "remove package X" | `pip uninstall X` |
| "pip fails with SSL error" | See SSL Troubleshooting section |
| "clean cache" | `pip cache purge` |
| "install with poetry" | `poetry add X` |
| "fast install with uv" | `uv pip install X` |
| "which Python am I using?" | `which python3 && python3 --version` |
| "where is this venv?" | `echo $VIRTUAL_ENV` |

## Workflows

### 1. Create & Activate a Virtual Environment

```bash
# Create (always in project root)
python3 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Verify
which python3    # should show .venv/bin/python3
python3 --version
```

**Do NOT use `virtualenv` or `conda` unless user explicitly requests them.** `python3 -m venv` is built-in and sufficient for 95% of use cases.

### 2. Install Packages

```bash
# Inside activated venv
pip install pandas numpy matplotlib

# With version pin
pip install pandas==2.1.4

# From requirements file
pip install -r requirements.txt

# Editable install (for local dev packages)
pip install -e .
```

### 3. SSL / Certificate Errors on macOS

This is the #1 issue on macOS corporate networks. When you see:

```
SSL: CERTIFICATE_VERIFY_FAILED
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Fix #1: trusted-host (quickest)**

```bash
pip install X --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

**Fix #2: Permanent config**

```bash
pip config set global.trusted-host "pypi.org files.pythonhosted.org"
```

**Fix #3: Install certifi certificates (for brew Python)**

```bash
# If using brew's Python
/Applications/Python\ 3.x/Install\ Certificates.command
# Or
pip install --upgrade certifi
```

### 4. Freeze & Share Requirements

```bash
# Standard freeze (all packages with exact versions)
pip freeze > requirements.txt

# Minimal freeze (only direct deps, uses pip-chill)
pip install pip-chill
pip-chill > requirements.txt

# Check what's actually used (pipreqs)
pip install pipreqs
pipreqs . --force
```

### 5. Clean & Reset

```bash
# Full venv reset (nuclear option)
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Just clear pip cache
pip cache purge

# Remove unused packages
pip autoremove X   # removes X and its unused deps (pip 23.3+)
```

### 6. Upgrade Everything

```bash
# See what's outdated
pip list --outdated

# Upgrade all (POSIX)
pip list --outdated --format=freeze | cut -d= -f1 | xargs -n1 pip install -U

# Upgrade pip itself
pip install --upgrade pip
```

### 7. Multiple Python Versions

```bash
# Check all installed Pythons
ls /Library/Frameworks/Python.framework/Versions/
which -a python3

# Use specific version for venv
python3.11 -m venv .venv311
python3.12 -m venv .venv312
```

### 8. Poetry (alternative package manager)

Only use if user explicitly asks for Poetry or has a `pyproject.toml`.

```bash
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add package
poetry add pandas

# Install all deps
poetry install

# Export to requirements.txt
poetry export -f requirements.txt -o requirements.txt
```

### 9. uv (fast pip alternative)

```bash
# Install uv
pip install uv

# Install packages (much faster than pip)
uv pip install -r requirements.txt

# Create venv
uv venv
```

### 10. Diagnosis Commands

```bash
# Where is Python?
which python3
python3 -c "import sys; print(sys.executable)"

# Where are packages installed?
python3 -c "import site; print(site.getsitepackages())"

# What's importing what?
pip show pandas          # metadata for one package
pipdeptree               # full dependency tree (pip install pipdeptree first)

# Why is X installed? (reverse dependency lookup)
pipdeptree -r -p X
```

## Pitfalls

1. **Forgot to activate venv?** `pip install` installs to global/user site-packages. Check: `which python3` should show `.venv/bin/python3`.
2. **requirements.txt out of sync?** Always freeze after installing something new during development.
3. **SSL errors on pip download?** Use `--trusted-host` flag (see section 3). Common on macOS with corporate proxies.
4. **pip download vs pip install?** `pip download` resolves deps but doesn't install — useful for offline packaging. `pip install` does both.
5. **.venv in git?** Should be in `.gitignore`. Only commit `requirements.txt` or `pyproject.toml`.
6. **Mixed Python versions?** Packages installed for 3.12 won't work in a 3.11 venv. Always recreate the venv when switching Python versions.

## Environment Variables for pip

```bash
# Offline wheel cache
export PIP_CACHE_DIR=/path/to/cache

# Trust custom index
export PIP_INDEX_URL=https://pypi.org/simple
export PIP_TRUSTED_HOST=pypi.org

# Extra index (for private registries)
export PIP_EXTRA_INDEX_URL=https://private-registry.example.com/simple
