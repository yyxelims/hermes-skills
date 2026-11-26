# BANK MMTA 系统诊断实录 (2026-09-02)

## 系统
- URL: `http://mmta.bank/index.jsp`
- 标题: 金融市场交易应用
- iframe 数量: 2
  - iframe[0]: `http://mmta.bank/servlet/com.bank.cte.cs.servlet.CSReqServle...`
  - iframe[1]: `http://mmta.bank/mmtaibdapprovalmng.flowc?flowActionName=mmt...`

## 按钮位置（诊断结果）

### A按钮: 发送分行审批
- **在 iframe[1] 里**，主文档和 iframe[0] 都找不到
- 选择器: `#_ctp_toolbar_item_button_send` (ID 命中)
- tag=a, visible=True, text=发送分行审批
- 所有5个选择器在 iframe[1] 里全部命中

### B按钮: 浏览器原生弹窗
- 点击A后出现，`switch_to.alert` 检测
- 弹窗内容待确认（session中弹窗闪了一下就没了，可能是页面自动关闭了）
- **关键**: 必须先 `switch_to.default_content()` 退出 iframe 才能检测 alert

### C按钮: 网页DOM弹窗确定
- `#ymPrompt_btn_0` — 诊断时未出现（需先完成B步骤才会弹出）
- 应该也在 iframe 内（与A按钮同一 iframe）

## 诊断日志关键发现

1. **主文档扫描无果** — 所有5个A选择器在主文档全部 ✗ 未找到
2. **iframe[0] 无果** — CSReqServlet iframe 里也找不到A和C
3. **iframe[1] 全部命中** — 业务iframe，5个选择器全部 ✓
4. **全局input扫描** — 主文档只有隐藏的session/配置input，没有可见按钮

## 教训

1. 诊断模式必须扫描所有 iframe，不能只查主文档
2. 按钮在哪个 iframe 里不能猜——必须诊断确认
3. 用户肉眼看到弹窗"闪了一下就没了"——可能是JS自动关闭，alert检测需要更快的循环间隔
4. 诊断模式和运行模式要共用同一套查找方法（session中改了方法名但诊断没同步导致 `_find_with_log` not found 报错）
