# Hermes Skills

在 [Hermes Agent](https://hermes-agent.nousresearch.com/docs) 上实际用出来的技能库：每个目录一个技能，`SKILL.md` 是触发条件和操作步骤，`references/` `scripts/` `templates/` 是配套资料。

共 **74** 个技能，14 个分类。全部来自真实任务，不是示例模板。

## 怎么用

```bash
# 装某一个
cp -r creative/baoyu-infographic ~/.hermes/skills/creative/

# 或者整包
cp -r ./* ~/.hermes/skills/
```

装完在 Hermes 里说一句相关的话就会自动匹配；也可以 `skill_view(name='技能名')` 手动加载。

## 分类

| 分类 | 技能数 |
|---|---|
| [apple](#apple) | 1 |
| [autonomous-ai-agents](#autonomous-ai-agents) | 3 |
| [creative](#creative) | 8 |
| [data-science](#data-science) | 2 |
| [devops](#devops) | 10 |
| [finance](#finance) | 1 |
| [gaming](#gaming) | 3 |
| [mcp](#mcp) | 1 |
| [media](#media) | 2 |
| [productivity](#productivity) | 12 |
| [red-teaming](#red-teaming) | 1 |
| [research](#research) | 7 |
| [software-development](#software-development) | 8 |
| [通用](#通用) | 15 |

## 技能清单

### apple

| 技能 | 用途 |
|---|---|
| `macos-computer-use` | \| |

### autonomous-ai-agents

| 技能 | 用途 |
|---|---|
| `ai-coding-agent-model-routing` | Use when 给 AI 编码 agent 换模型/配网关（CC Switch、magpie）。 |
| `hermes-agent` | Configure, extend, or contribute to Hermes Agent. |
| `provider-health-check` | 检测Hermes各provider/模型哪些可用。Use when 问模型挂没挂、切默认模型前批量验证。 |

### creative

| 技能 | 用途 |
|---|---|
| `ai-video-storyboard` | Use when 剧本/文案扩写成AI视频分镜脚本提示词（可灵/即梦/Runway）。 |
| `baoyu-comic` | Knowledge comics (知识漫画): educational, biography, tutorial. |
| `baoyu-infographic` | Infographics: 21 layouts x 21 styles (信息图, 可视化). |
| `comfyui` | Generate images, video, and audio via diffusion workflows. |
| `creative-ideation` | Generate project ideas via creative constraints. |
| `image-watermark-removal` | Use when user asks to 去水印. OpenCV inpaint + pixel-verify. |
| `itinerary-html` | 把任意多日/多段行程（火车/航班/景点/酒店/餐厅）做成交互式 HTML 攻略页面，桌面 + 移动端双版本。左时间轴 / 中高德地图 / 右详情 / 天气 / 导出 PNG。... |
| `pixel-art` | Pixel art w/ era palettes (NES, Game Boy, PICO-8). |

### data-science

| 技能 | 用途 |
|---|---|
| `eda-quick-analysis` | \|- |
| `jupyter-live-kernel` | Iterative Python via live Jupyter kernel (hamelnb). |

### devops

| 技能 | 用途 |
|---|---|
| `alibaba-cloud-oss` | Use for 阿里云 OSS (对象存储): oss2 SDK, buckets, ACL, CDN. |
| `china-web-data` | >- |
| `cybernetics-framework` | 钱学森《工程控制论》14条核心原则框架——用于日常梳理和评估所有skill。所有经验技能都应按照此框架进行归档和审核。 |
| `frontend-design` | > |
| `glm-zhipu` | GLM/智谱AI(Z.AI) provider接入与调用：Hermes配置、双端点兼容、模型清单。 |
| `kanban-orchestrator` | Decomposition playbook + anti-temptation rules for an orchestrator profile routing work... |
| `kanban-worker` | Pitfalls, examples, and edge cases for Hermes Kanban workers. The lifecycle itself is a... |
| `scheduled-data-pipeline-maintenance` | Use when 定时数据管道静默失效、产出停在旧日期。 |
| `skill-creator` | > |
| `skill-export` | Package Hermes skills to a portable .md/.txt format. |

### finance

| 技能 | 用途 |
|---|---|
| `quant-finance` | > |

### gaming

| 技能 | 用途 |
|---|---|
| `minecraft-modpack-server` | Host modded Minecraft servers (CurseForge, Modrinth). |
| `pokemon-player` | Play Pokemon via headless emulator + RAM reads. |
| `world-cup-prediction` | 2026世界杯小组赛比分预测。结合盘口赔率、振幅递增节奏规律、三组数学框架（信息熵梯度+傅里叶热谱+NLSE冷门探测器）、已完成比赛数据，输出正常预测+爆冷预测双版本。用户提... |

### mcp

| 技能 | 用途 |
|---|---|
| `native-mcp` | MCP client: connect servers, register tools (stdio/HTTP). |

### media

| 技能 | 用途 |
|---|---|
| `heartmula` | HeartMuLa: Suno-like song generation from lyrics + tags. |
| `spotify` | Spotify: play, search, queue, manage playlists and devices. |

### productivity

| 技能 | 用途 |
|---|---|
| `chinese-report-decks` | Use when 做中文业务汇报PPT：留图位、无GUI校验、保留手改。 |
| `docx` | Create, read, edit, template, and review Word .docx files. |
| `grill-me` | Use when 用户说拷问我/grill me/挑战我的方案。轮次访谈压测方案。 |
| `image-to-excel` | Use when 用户给图片/海报/截图要转成表格或Excel。同回合建表交付+stdlib校验。 |
| `linear` | Linear: manage issues, projects, teams via GraphQL + curl. |
| `powerpoint` | Create, read, edit .pptx decks, slides, notes, templates. |
| `pptx-deck-building` | Use when 做中文汇报 PPT 初稿或改 pptx（python-pptx）。 |
| `presentation-defense` | Use for innovation-contest defense Q&A. |
| `teach` | Teach the user a new skill or concept, within this workspace. Use when the user says "t... |
| `weather-briefing` | Use when 用户要天气简报或每日天气推送（某片区/某城区）。官方实况校准湿度+露点，纯中文简报。 |
| `word-docx-editing` | >- |
| `xlsx` | Create, read, edit Excel .xlsx workbooks and CSVs. |

### red-teaming

| 技能 | 用途 |
|---|---|
| `godmode` | Jailbreak LLMs: Parseltongue, GODMODE, ULTRAPLINIAN. |

### research

| 技能 | 用途 |
|---|---|
| `aihot` | 查询 AIHOT（aihot.news）的中文 AI 资讯。用户问今天或最近 AI 圈发生了什么、AI 新闻和 AI 日报、大模型与 AI 产品发布、OpenAI／Anthr... |
| `arxiv` | Search arXiv papers by keyword, author, category, or ID. |
| `gov-budget-attachment-download` | Use when 批量下载政府预决算公开栏目全部附件到本地。 |
| `grounded-citations` | Ground answers and documents in cited, verifiable sources. |
| `policy-tracker` | > |
| `polymarket` | Query Polymarket: markets, prices, orderbooks, history. |
| `regulatory-monitoring-workflows` | Use for Chinese regulatory monitoring and leader research. |

### software-development

| 技能 | 用途 |
|---|---|
| `backend-acceptance-testing` | Use when 审后端与需求是否匹配、要联调验收或问进度。 |
| `backend-delivery-review` | Use when 审查后端代码是否匹配需求/规格、评估交付进度。实测构建+启动取证，不只读代码。 |
| `python-env` | Python environment and package management skill. Use when user needs to create/manage v... |
| `spring-boot-backend-delivery` | Use when 交付 Spring Boot+MySQL 后端并上线单机。 |
| `subagent-driven-development` | Execute plans via delegate_task subagents (2-stage review). |
| `systematic-debugging` | 4-phase root cause debugging: understand bugs before fixing. |
| `tkinter-gui-tools` | Use when 用户要 Python tkinter 本地 GUI 小工具：文件选择、预览、批处理、双击启动。 |
| `writing-plans` | Write implementation plans: bite-sized tasks, paths, code. |

### 通用

| 技能 | 用途 |
|---|---|
| `baidu-ai-search` | > |
| `browser-automation-tools` | 用 Selenium 构建浏览器自动化工具（连点、表单填写、批量查询）。含 Tkinter GUI 模板、Edge 远程调试模式、多选择器兜底策略、PyInstaller 打... |
| `byted-supabase` | Manage Volcengine's AI-native BaaS platform (Supabase edition / 火山引擎 AI 原生 BaaS 平台 Supa... |
| `hatch-pet` | Create, repair, validate, preview, and package Codex-compatible animated pet spriteshee... |
| `neat-freak` | > |
| `poe-api` | Use Poe.com as an LLM/image provider: API setup, Hermes config, image generation via ch... |
| `ponytail` | Lazy senior dev mode. Forces the simplest, shortest solution that works: YAGNI, stdlib ... |
| `ponytail-audit` | Audit the whole repo for over-engineering. A ranked list of what to delete, simplify, o... |
| `ponytail-debt` | Harvest every ponytail: shortcut comment into one debt ledger, so deferrals get tracked... |
| `ponytail-gain` | Show ponytail measured impact as a scoreboard: less code, less cost, more speed, from t... |
| `ponytail-help` | Quick reference for ponytail's modes, skills, and commands. One-shot display. |
| `ponytail-review` | Review a diff for over-engineering. Finds what to delete: reinvented stdlib, needless d... |
| `reverse-engineer-anything` | Reverse engineer native, managed, Electron/JavaScript, packaged, firmware, and browser ... |
| `tikhub-api` | TikHub API 客户端用法与实测状态。Use when 调TikHub抓公众号/抖音/微博数据。 |
| `yuanbao` | Yuanbao (元宝) groups: @mention users, query info/members. |

## 说明

- 本仓库内容已做脱敏：服务器地址、账号密钥、手机号、本机路径、具体机构与地点均已替换为占位符，示例中的 `***`、`YOUR_SERVER_IP` 需要换成你自己的值。
- 部分技能依赖特定环境（macOS、某个 CLI、某个 MCP 服务），`SKILL.md` 里写了前置条件，缺依赖时按文档里的替代方案降级。
- 技能是经验沉淀，不是通用 SDK。同一类任务换个环境可能需要调整命令，但踩坑记录和判断逻辑仍然适用。
- 欢迎提 issue 指出过时内容。

## License

MIT
