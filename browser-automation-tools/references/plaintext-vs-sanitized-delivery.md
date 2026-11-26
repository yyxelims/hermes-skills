# 两份产物：明文自用版 vs 脱敏 git 版（2026-11-04 定稿）

## 为什么会有两份

同一个连点工具，用户要交付到两个方向，**约束完全相反**：

| | 明文自用版（U 盘 / 行内） | 脱敏 git 版 |
|---|---|---|
| 元素定位 | **写死在代码里**，一个常量列表 | 外置 `config.example.json`（`REPLACE_*` 占位符）+ 本地 `config.json`（gitignore） |
| 用户要做什么 | 双击 exe 就跑 | 填一次选择器 |
| 驱动 | **打进 exe 里**（`--add-binary`），产出单文件 | 可选，缺了给警告 |
| 打包 | 双击 `build.bat`，无选项无提问 | 可选包型菜单 |
| 版本控制 | 无（U 盘 + 本机备份） | 本地 `git init`，**不建远端** |
| 代码量 | 一份文件搞定 | 多一层配置加载/校验 |

**踩过的坑**：先做了脱敏配置化版本，又把它当成 U 盘交付物 → 用户炸了：
「不是，优盘上这个代码，我让你直接把该点什么明文写死进代码里，不要给我弄什么破 json 再让我自己填写。
然后把 edgedriver 直接一起打包进最后的打包文件，能明白我什么意思吗？」

结论：**脱敏需求只作用于「要进 git 的那份」**，不要外溢到自用版。做之前先确认这次交付是哪一个方向。

## 明文版骨架（常量区放文件顶部，一眼能看见）

```python
# ===== 元素写死区（改这里，不读任何外部文件）=====
BTN_A = [                                        # 第一步：发送/触发按钮
    (By.ID, "_ctp_toolbar_item_button_send"),
    (By.CSS_SELECTOR, "#_ctp_toolbar_item_button_send"),
    (By.PARTIAL_LINK_TEXT, "发送分行"),
]
BTN_CONFIRM = [                                  # 弹窗确定（id 自增，用前缀+文案）
    (By.CSS_SELECTOR, "input[id^='ymPrompt_btn_'][value*='确']"),
    (By.CSS_SELECTOR, "input.btnStyle[value*='确']"),
    (By.XPATH, "//input[contains(@value,'确') and contains(@value,'定')]"),
]
BTN_SUBMIT = [                                   # 第二步（总行/批量）
    (By.ID, "_ctp_toolbar_item_button_sendfmbm"),
    (By.ID, "_ctp_toolbar_item_button_center_sendfmbm"),
]
DONE_FLAG = BTN_SUBMIT                           # disabled = 全部完成
CANCEL_KEY = "取"                                # value 含"取"=取消，一律不点
PORT, INTERVAL_DEFAULT, MAX_FRAME_DEPTH = 9222, 0.5, 3
```

选择器支持 `(By.X, value)` 元组，`_find()` 逐条试 → 天然同时支持 CSS 与 XPath，不用给配置写 `xpath:` 前缀。

## 驱动必须打进 exe

```python
subprocess.check_call([
    sys.executable, "-m", "PyInstaller",
    "--onefile", "--windowed", "--name", APP_NAME,
    "--add-binary", f"{driver}{';' if os.name == 'nt' else ':'}.",
    ...  # hidden-import 见主 SKILL.md 清单
    os.path.abspath(__file__),
])
```

产出 `dist/<App>.exe` 单文件 = 程序 + selenium + 驱动，行内机双击即用，**旁边不放任何文件**。
`_get_driver_path()` 仍然保留「exe 同目录优先」作为热替换后门，但正常使用根本不用管。

打包函数要**自己**检查驱动存在性并 `input("按回车退出...")`——双击 bat 时窗口一闪而过就没法排查。

## 交付时要逐条说清的三件事

用户不看你做了什么，只看该不该信。交付回复里固定给：

1. **写死了什么** —— 把常量列表原文贴出来（`('id','_ctp_toolbar_item_button_send')` 这种）
2. **内置了什么** —— `--add-binary` 那行 + 驱动版本号（从文件里读出来核对，别抄用户说的）
3. **删掉了什么** —— `grep -niE "config\.json|REPLACE_"` 输出 0 命中，证明不依赖配置

## 驱动版本怎么核（不跑 exe 也能查）

Mac 上也能读：`re.findall(rb"(1[0-9]{2}\.\d\.\d{3,5}\.\d{1,3})", open(path,"rb").read())`，
第一组就是版本（如 `143.0.3650.139`）。用户 U 盘里常年躺着好几个版本的 `msedgedriver.exe`，
**用版本号挑，不要用目录名猜**——实测 `机构连点/` 里是 126、`连点程序/1/` 里才是 143。

## bat（明文版，无菜单无提问）

```bat
@echo off
chcp 65001 >nul
cd /d "%~dp0"
python --version
if errorlevel 1 (echo 没装 Python。装 3.8+ 并勾 Add to PATH & pause & exit /b 1)
if not exist msedgedriver.exe (echo 没找到 msedgedriver.exe，必须同目录 & pause & exit /b 1)
msedgedriver.exe --version
python SendFenhang.py --build
if exist "dist\SendFenhang.exe" (echo 完成：dist\SendFenhang.exe 这一个文件就够了 & explorer dist)
pause
```

中文 bat：文件存 UTF-8（**无 BOM**）+ 首行 `chcp 65001 >nul` + 行尾 CRLF，三样齐才不会乱码/闪退。
写完 `file build.bat` 应看到 `DOS batch file text`；行尾转 CRLF 用一段 .py 读改写（
`raw.replace(b"\r\n",b"\n").replace(b"\n",b"\r\n")`），并断言 bare LF 为 0。
