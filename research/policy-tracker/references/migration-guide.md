# 新设备迁移指南

## 必须拷贝的文件

| 内容 | 来源 | 说明 |
|------|------|------|
| Skill 定义 | `~/.hermes/skills/research/policy-tracker/` | SKILL.md + references + scripts |
| 项目脚本 | `政策动态追踪/脚本/*.py`（9 个） | 核心流水线 |
| README | `政策动态追踪/README.md` | 操作手册 |
| 领导基线 | `政策动态追踪/数据/leader_data/snapshots/` | 首次运行需要 |
| DeepSeek API key | `~/.hermes/config.yaml` 或 `/tmp/ds_key.txt` | LLM 摘要必需 |

## 安装步骤

```bash
# 1. 目录结构
mkdir -p ~/Documents/工作/2026创新大赛/agent/政策动态追踪/{脚本,数据}

# 2. 复制 Skill（Hermes 新设备）
scp -r old-device:~/.hermes/skills/research/policy-tracker ~/.hermes/skills/research/

# 3. 复制项目脚本
scp old-device:"~/Documents/工作/2026创新大赛/agent/政策动态追踪/{脚本/*.py,README.md}" \
    ~/Documents/工作/2026创新大赛/agent/政策动态追踪/

# 4. 复制领导快照基线
scp -r old-device:"~/Documents/工作/2026创新大赛/agent/政策动态追踪/数据/leader_data" \
    ~/Documents/工作/2026创新大赛/agent/政策动态追踪/数据/

# 5. 安装依赖
pip3 install playwright openpyxl pyyaml
python3 -m playwright install chromium

# 6. 配置 DeepSeek API key
# 选项 A：通过 Hermes config
hermes config set custom_providers deepseek api_key "sk-xxx"
# 选项 B：手动写文件
echo "sk-xxx" > /tmp/ds_key.txt

# 7. 验证
cd ~/Documents/工作/2026创新大赛/agent/政策动态追踪/脚本
python3 leader_monitor.py --init
python3 build_final.py   # 用已有数据测试
```

## 注意事项

- **项目路径硬编码**：脚本中的 `BASE` 变量指向绝对路径，迁移后需同步修改
- **数据目录**：`数据/` 下的运行时 JSON 可重新生成，不需要拷贝
- **Playwright**：需要完整的 Chromium 浏览器（`playwright install chromium`，约 150MB）
- **网络环境**：中国大陆需确保能访问 `api.deepseek.com`、各政府网站
