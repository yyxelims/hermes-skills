# Python Offline Package Downloads

## When to use this

When you need to prepare offline install packages for a target platform different from
the current one (e.g. building win_amd64 wheels on macOS for a user's Windows machine).

## The Only Reliable Method: `pip download`

Do NOT manually resolve transitive deps by crawling PyPI JSON or guessing URLs.
`pip download` with the full dependency resolver is the only way to get it right.

### Step 1: Download everything with full dependency resolution

```bash
pip download \
  --only-binary=:all: \
  --platform win_amd64 \
  --python-version 312 \
  --implementation cp \
  -d ./offline_deps/ \
  <your-top-level-packages...>
```

This single command resolves ALL transitive dependencies for the target platform.
It downloads wheels for the target platform even when run on a different OS.

Important: do NOT add `--no-deps` — that forces you to manually trace transitive deps,
which WILL miss packages (as shown by the user's repeated corrections in this session:
missed pytz, python-dateutil, six, tzdata, mpmath, matplotlib, contourpy, cycler,
fonttools, kiwisolver, narwhals, packaging, pillow, pyparsing, threadpoolctl,
typing-extensions — all found by pip's resolver).

### Step 2: Clean up version conflicts

`pip download` may download multiple versions of the same package if different
top-level packages have conflicting constraints. After download completes, keep
only the newest version of each package (sort by version number and delete older ones).

### Step 3: Provide a batch install script

```bat
pip install --no-index --find-links=. <packages>
```

The `--no-index --find-links=.` tells pip to only use the local `.whl` files.

## Pitfalls

- **Do NOT use `--no-deps`** unless you are certain every transitive dep is already covered.
- **PyPI.org can be slow from some regions** — the download may take several minutes
  even for modest packages. Use `--timeout 300` or run in background with notify.
- **Version pinning matters** — sympy 1.14.0 specifically requires mpmath >=1.1.0,<1.4,
  so let pip pick the correct mpmath version (1.3.0 in this case) rather than
  downloading the latest mpmath (1.4.1).
- **Never guess wheel URLs from PyPI JSON** — the hash in the URL changes between
  releases and even between rebuilds. Wrong hashes return 404.
- **Don't manually trace transitive deps** — you will miss some, and the user will
  have to tell you. Multiple corrections in one session is a strong signal to use
  pip's resolver from the start.
