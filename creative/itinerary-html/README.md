# itinerary-html

把任意行程数据做成可视化交互 HTML（桌面 + 移动端双版本）。

## 文件结构

```
itinerary-html/
├── SKILL.md                       # 主入口 · 触发场景 · 铁律
├── README.md                      # 本文件
├── LICENSE                        # MIT
├── .gitignore                     # 忽略本地生成文件
├── assets/
│   ├── template-desktop.html      # 通用桌面模板
│   └── template-mobile.html       # 通用移动模板
├── references/
│   ├── coord-workflow.md          # 高德 POI 查询 API 工作流（必读）
│   ├── data-schema.md             # 数据结构定义
│   └── qa-checklist.md            # 交付前自检清单
└── examples/                      # 空目录，按需放示例
```

## 适用场景

✅ 用户提供火车票/酒店订单/景点列表，要做可视化 HTML
✅ 需要地图 + 时间轴 + 详情三栏布局
✅ 桌面 + 移动端两个版本
✅ 国内行程（**默认只支持国内**，海外行程需要扩展）

## 不适用

❌ 简单 Markdown 行程清单
❌ 实时导航
❌ 多人协作编辑（需要后端）
❌ 海外行程（默认不支持，需要换 Google Maps API）

## 使用流程

1. **解析输入**：把用户的行程数据（任意形式）整理成 POI 列表
2. **核实坐标**：每个 POI 用 `references/coord-workflow.md` 的高德 API 查真实坐标
3. **澄清盲点**：搜不到 / 缺细节的 POI 列出来问用户
4. **填模板**：复制 `assets/template-*.html`，替换 4 个数据数组 + AMAP_KEY
5. **自检**：按 `references/qa-checklist.md` 逐项过
6. **交付**：两个 HTML + `poi-candidates.md`（坐标来源表）

## 关键铁律

1. **绝不瞎编任何数据** — 拿不准就问用户
2. **坐标必须用高德 API 查证** — 不允许凭印象编
3. **缺数据就留空 + 标注 ⚠️** — 不要硬填

详见 `SKILL.md`。

## 配色规范（10.0 墨绿扁平）

所有模板默认使用，不要轻易改：

- 主色：墨绿 `#1f3d34`
- 强调：暖橙 `#c97b4a`（必看/核心用）
- 类别色：蓝(交通)/青绿(景点)/橙红(餐饮)/紫(住宿)/赭红(必看)
- 零圆角（除 Day 切换条），1px 描边，硬阴影

如果用户明确要换色系，**整个配色模块需要重写**，不要只改主色。

## 在其他项目里复用

这个 skill 是独立的，可以：

1. **整体搬到另一个项目目录**（直接复制整个 `itinerary-html/` 文件夹）
2. **作为 SKILL 注册到 OpenCode/Claude Code**：把文件夹路径加到 skill 配置
3. **作为 skill-creator 的产出发布**

## 隐私

skill 本身**不包含任何个人信息或高德 Key**（已在发布前扫描验证）。用户使用时会自己填数据，模板里的 `<请替换>` 占位符确保不会误用。