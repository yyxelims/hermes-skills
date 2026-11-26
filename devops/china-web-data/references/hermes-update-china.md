# Hermes Agent 中国区更新方案

## 问题

`hermes update` 底层执行 `git pull`，但 GitHub (`github.com:443`) 在中国大陆被 GFW 阻断，直接更新失败：
```
fatal: unable to access 'https://github.com/NousResearch/hermes-agent.git/': 
LibreSSL SSL_connect: SSL_ERROR_SYSCALL
```

## 解决方案：git remote 走 GitHub 镜像

### 1. 测试可用镜像

推荐按以下顺序尝试：

```bash
# 测试镜像是否可达
git ls-remote "https://ghproxy.net/https://github.com/NousResearch/hermes-agent.git" HEAD
```

已知可用的镜像（2026-07）：
| 镜像 | 状态 | 速度 |
|------|------|------|
| `ghproxy.net` | ✅ 可用 | 中等（完整 clone ~3min） |
| `mirror.ghproxy.com` | ❌ SSL 阻断 | - |

### 2. 切换到镜像 remote 并更新

```bash
cd ~/.hermes/hermes-agent

# 切换 remote
git remote set-url origin "https://ghproxy.net/https://github.com/NousResearch/hermes-agent.git"

# 拉取最新
git fetch --depth=1 origin main
git merge origin/main --ff-only   # 全量克隆可直接 fast-forward
```

### 3. 浅克隆兼容性问题

如果 Hermes 是通过**浅克隆**安装的（`--depth=1`），直接 merge 会因历史不连通而失败。此时有三方案：

**方案 A：unshallow（理论上最干净，实际太慢）**
```bash
cd ~/.hermes/hermes-agent
git fetch --unshallow origin   # 经实测：通过 ghproxy.net 超时（>10min），不推荐
```

**方案 B：硬重置（最快，但需用户确认）**
```bash
# 先确保无未提交的本地修改
cd ~/.hermes/hermes-agent
git status --short
# 然后获取用户同意后执行：
git reset --hard origin/main
```
⚠️ Hermes 的安全机制会自动拦截 `git reset --hard`。需要用户明确同意后才能执行。这是实际可行的方案——ghproxy.net 浅克隆 fetch 只需约 50 秒完成，reset 瞬间完成。

**方案 C：永久使用镜像 remote（一劳永逸）**
```bash
cd ~/.hermes/hermes-agent
git remote set-url origin "https://ghproxy.net/https://github.com/NousResearch/hermes-agent.git"
# 之后 hermes update 会自动走镜像，无需每次手动切换
```
注意：mirror.ghproxy.com (2026-07-13 实测 SSL 阻断) 不可用，不要尝试。

### 4. 更新后恢复原始 remote（可选）

```bash
git remote set-url origin "https://github.com/NousResearch/hermes-agent.git"
```

### 5. pip 不可用

`pip install hermes-agent` 不是官方发布渠道，PyPI 上无此包。`pip install --upgrade certifi` 无法解决 GitHub 阻断问题（本质是 GFW 层 TCP 阻断，非证书问题）。
