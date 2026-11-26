# Offline pip Packages — Reliable Download Pattern

## The Problem
Downloading individual wheels by hand-hunting URLs on PyPI is error-prone:
- URL hashes are hard to find correctly
- Tsinghua mirror hashes differ from PyPI
- Transitive dependencies are invisible and iteratively missed

## The Solution: `pip download` with Full Resolution

One command downloads the package AND all transitive deps for a target platform:

```
pip download --only-binary=:all: \
  --platform win_amd64 \
  --python-version 312 \
  --implementation cp \
  -d <output_dir> \
  <package1> <package2> ...
```

Key flags:
- `--only-binary=:all:` — wheels only, no sdists (faster, no build)
- `--platform win_amd64` — target Windows x64
- `--python-version 312` — Python 3.12 ABI
- `--implementation cp` — CPython (not PyPy)
- NO `--no-deps` — let pip resolve ALL transitive deps automatically
- `-d <dir>` — output directory

## Install on Target Machine

Copy the output directory to the target machine, then:

```
pip install --no-index --find-links=<dir> <package1> <package2> ...
```

Or from a batch file: `pip install --no-index --find-links=. pkg1 pkg2 ...`

## Pitfalls

1. **Do NOT hand-hunt URLs** — PyPI file hashes change; mirrors (Tsinghua) use different hashes. The `pip download` approach is the only reliable path.

2. **Do NOT use `--no-deps`** during the download phase — you'll miss transitive deps and the user will iterate through "missing X, missing Y, missing Z" rounds.

3. **Do `pip download` twice if unsure** — first without `--no-deps` to resolve the full tree into the dir; a second run is idempotent and skips already-downloaded wheels.

4. **Existing packages are auto-skipped** — if the user already has some deps installed (e.g., catboost, numpy), that's fine; the offline dir can include them and `pip install --no-index` will only install what's not already present.

## Example: ML Stack for Windows x64 Python 3.12

```
pip download --only-binary=:all: --platform win_amd64 --python-version 312 --implementation cp \
  -d offline_deps \
  pandas sympy lifelines umap-learn ngboost pynndescent
```

This resolved to 34 wheels (130 MB) including matplotlib, scipy, numba, llvmlite, and all their transitive deps — zero iteration needed.
