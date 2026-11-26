# China Network Workarounds (GFW)

Documented 2026-07-13 during hatch-pet setup and Hermes update attempt.
Applies to: git clone/pull, ComfyUI model downloads, pip installs, any HTTPS to GitHub/PyPI.

## Problem

GitHub (github.com:443) and PyPI (pypi.org:443) are blocked by GFW.
Both HTTPS and SSH (git@github.com:22) connections fail with `SSL_ERROR_SYSCALL`.

## Verified Working Mirror

**ghproxy.net** — HTTP proxy for GitHub raw content and git operations.

| Service | Original | Mirror |
|---------|----------|--------|
| git clone/pull | `https://github.com/user/repo.git` | `https://ghproxy.net/https://github.com/user/repo.git` |
| raw content | `https://raw.githubusercontent.com/...` | `https://ghproxy.net/https://raw.githubusercontent.com/...` |

**Speed:** ~10-30 KB/s. Full clones time out. Use `--depth=1` for initial clone.

## Git Remote Setup (Permanent)

```bash
cd /path/to/repo
git remote set-url origin "https://ghproxy.net/https://github.com/ORG/REPO.git"
```

## Hermes Update via Mirror

```bash
cd ~/.hermes/hermes-agent
git remote set-url origin "https://ghproxy.net/https://github.com/NousResearch/hermes-agent.git"
git fetch --depth=1 origin main
# If full clone: git merge origin/main
# If shallow clone: git reset --hard origin/main (only if no local changes!)
```

**Pitfall:** Shallow clones (depth=1) can't fast-forward merge. `git reset --hard origin/main` is the clean fix when there are no local changes.

## Failed Mirrors (tested 2026-07-13)

| Mirror | Status |
|--------|--------|
| `https://mirror.ghproxy.com/...` | SSL_ERROR_SYSCALL — blocked |
| `https://gh-proxy.com/...` | Failed to connect |
| `https://gh.con.sh/...` | Failed to connect |
| SSH `git@github.com` | Connection closed by YOUR_SERVER_IP (GFW RST) |

## ComfyUI Model Downloads

ComfyUI models are hosted on HuggingFace (huggingface.co) and CivitAI. These may also be affected.
Use `hf-mirror.com` for HuggingFace:

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

Then proceed with normal `comfy model download` commands.
