# 连点工具脱敏 + 版本控制（工具要进 git 时）

触发：用户说「在 git 上新建个项目存这个代码，但是不要展示任何有关系统元素的东西」、
「仅做版本控制」、要把行内系统自动化脚本归档 / 给别人看 / 发版。

## 硬性规则（用户明确要求，别自行加戏）

1. **不含任何站点元素**：id、class、onclick 片段、按钮文案、iframe 索引、内网域名、
   业务措辞（分行/总行/审批/某业务名）一律不出现。
2. **不要建远端**，除非用户明说要 GitHub。「仅做版本控制」= `git init` + 本地提交，
   不 `gh repo create`、不 `git remote add`。用户此前所有私有仓库都是自己决定的，
   别替他决定公开/私有。
3. 仓库里**只放占位符模板**，真配置在本地且被 ignore。

## 做法：把元素定位整体外置，而不是删字符串

删字符串会留下跑不了的尸体代码。正确做法是**配置与逻辑分离**：

```
config.example.json   ← 进仓库，全是 REPLACE_* 占位符
config.json           ← 本地真实选择器，写进 .gitignore，永不提交
```

`config.example.json` 骨架（全占位，无任何真实值）：

```json
{
  "debug_port": 9222,
  "selectors": {
    "primary_button": ["#REPLACE_PRIMARY_BUTTON_ID",
                       "xpath: //a[contains(text(), 'REPLACE_PRIMARY_TEXT')]"],
    "dialog_confirm": ["input[id^='REPLACE_DIALOG_PREFIX_'][value*='REPLACE_CONFIRM_TEXT']",
                       "xpath: //input[contains(@value, 'REPLACE_CONFIRM_TEXT')]"],
    "cancel_label": "REPLACE_CANCEL_TEXT",
    "submit_button": ["#REPLACE_SUBMIT_BUTTON_ID"],
    "done_when_disabled": ["#REPLACE_SUBMIT_BUTTON_ID"]
  },
  "behavior": {"interval": 0.5, "max_frame_depth": 3, "max_drain": 15}
}
```

代码侧两个小工具：

```python
def by_of(sel):                     # 支持 "xpath: ..." 前缀，其余按 CSS
    sel = (sel or "").strip()
    if sel.lower().startswith("xpath:"):
        return By.XPATH, sel[6:].strip()
    return By.CSS_SELECTOR, sel

def is_placeholder(sel):
    return "REPLACE_" in (sel or "").upper()
```

启动前用 `is_placeholder` 做校验：占位符没换就报「配置未填写」并列出缺哪几个 key，
而不是带着假选择器跑到超时。

## 中性化措辞对照

| 原名 | 仓库里改成 |
|---|---|
| 分行审批 / 总行审批 | 两步确认 / 批量提交 |
| 发送分行审批按钮 | primary_button |
| ymPrompt 弹窗确定 | dialog_confirm |
| 弹窗堆叠 | 残留弹窗 / max_drain |
| 银行内网系统 | 目标页面 |

函数的通用名：`_worker_two_step` / `_worker_batch` / `_click_dialog_confirm` /
`_frame_paths` / `_is_done`。别用 `_go_zh`、`_zh_clicks` 这类内部黑话。

## 交付前自查（必须真跑）

```bash
git ls-files                                   # 确认只有代码/模板/README
grep -rniE 'bank|ymPrompt|sendfmbm|_ctp_|分行|总行|审批|内网域名' $(git ls-files)
                                               # 必须 0 命中
python3 -m py_compile flow_clicker.py           # 语法
git status --short                              # 应为空
```

`grep` 命中数必须是 0 才回复用户「已脱敏」。别只说「我去掉了」，要给命令输出。

## 附带：脱敏版的单测桩（不依赖 Windows）

脱敏后逻辑没法在行内电脑上试，用假 driver 桩跑本地单测：

- `FakeEl`：包 lxml 元素，实现 `get_attribute / text / is_displayed`
- `FakeSwitch`：`default_content()` 清空 path，`frame(el)` 把元素在 `iframe,frame`
  列表里的下标压进 path
- `FakeDriver.doc_idx`：沿 path 从根文档走到目标文档；`find_elements` 用
  `cssselect` / `xpath` 在对应文档上查；`execute_script` 只记录点了哪个 id
- 先 `sys.modules` 桩掉 `selenium.*` 和 `tkinter`，再 `import` 被测模块，
  用 `object.__new__(App)` 绕过 tkinter root 构造

能验的东西：动态 id 点中、取消跳过、递归到嵌套 frame、多选择器计数去重、
`max_depth` 生效。这套桩一次写好能反复用。

## 两份副本：U 盘上的不脱敏，git 里的脱敏

用户原话：「在 u 盘上这个版本不脱敏，你上传到 git 的版本脱敏就行」。

= 用户手上始终有一份**填好真选择器、能直接跑**的副本（U 盘 / 行内电脑），
git 仓库里是**占位符 + 通用逻辑**的孪生版本。所以：

- 不要为了脱敏去改用户能跑的那份 —— 会把他正在用的工具改坏
- 两份的**逻辑修复要同步**（防堆叠、递归 frame、动态 id 这些必须两边都改），
  只是选择器来源不同：一份写死，一份读 config.json
- 交付时说清楚哪份是哪份，别让用户拿脱敏版去行内跑

## 脱敏版怎么打包（用户会直接问「还要不要打包」）

先给判断标准，别默认要打包：

> 用户问「是不是还要打包」时，**先确认他手上有没有现成的 bat**——这类用户通常早就拿到过
> 一个 `build_exe.bat`。他要的是能双击的东西，不是决策矩阵。照搬老 bat 的结构改名改脚本名，
> 补上配置文件的处理，比解释 PyInstaller 原理有用得多。本 session 先给了判断表 + 修了个
> frozen 路径 bug，用户回「不是，之前你是给我写了个打包批处理文件」。

| 情况 | 做法 |
|---|---|
| 目标机没有 Python（行内办公电脑） | 要打包，**且必须在 Windows 上打**（PyInstaller 不能从 mac 交叉编译） |
| 自己的机器能装 Python | 不用打包，`python xxx.py` 直接跑，改 config 重启即生效 |

打包两个必踩的坑：

1. **配置路径**：onefile 下 `__file__` = `_MEIPASS`，`config.json` 放 exe 旁边读不到。
   按 `sys.executable` 定位，模板回落 `_MEIPASS`（代码见 SKILL.md「用户可编辑的配置/数据文件」）。
2. **bat 委托**：bat 调 `python xxx.py --build`，PyInstaller 参数只留一份，避免 bat 与
   `self_build()` 两处不同步。

frozen 路径单测（真打包前就能验）：

```python
sys.frozen = True
sys._MEIPASS = "/tmp/fz/_MEI12345"
sys.executable = "/tmp/fz/dist/App.exe"
importlib.reload(mod)          # 断言 CONFIG_PATH 在 dist/、EXAMPLE_PATH 在 _MEI
```

并在 `dist/` 旁边建一个真 `config.json`，确认 `load_config()` 优先读到它而不是模板。
