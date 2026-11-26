# 离线交付链：U 盘 → 行外打包 → 行内运行（2026-11-04 实测）

用户环境：开发机 macOS，行外一台有网 Windows，行内一台无网/无 Python/装不了东西的 Windows。
交付方式：U 盘搬代码 + 批处理 + 正确版本的 `msedgedriver.exe`，在行外打包，产物拷进行内。

```
开发机  --U盘-->  行外 Windows(有网, 装 Python)   双击 build.bat
                    --U盘-->  行内 Windows(无网)  双击 exe
```

## 0. 三条铁律

1. **驱动版本盯运行机**。行内 Edge 143 → 必须带 143 的 `msedgedriver.exe`；行外那台是几版都无所谓。
2. **驱动可热替换**：查找顺序 `exe 同目录 > 打包内置`，版本错了换文件即可，不用重打包。
3. **包型可切**：`--onefile` 可能被行内杀软/AppLocker 拦（自解压到 TEMP），必须能退到 `--onedir` 文件夹版。

## 1. 版本探测（无第三方依赖）

```python
import re, subprocess
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)   # 非 Windows 上 0

def _file_version(path):
    """msedge.exe 的 ProductVersion"""
    if not path or not os.path.exists(path):
        return ""
    try:
        return subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-Item -LiteralPath '{path}').VersionInfo.ProductVersion"],
            capture_output=True, text=True, timeout=25,
            creationflags=NO_WINDOW).stdout.strip()
    except Exception:
        return ""

def _driver_version(path):
    """msedgedriver.exe --version"""
    if not path or not os.path.exists(path):
        return ""
    try:
        return subprocess.run([path, "--version"], capture_output=True, text=True,
                              timeout=25, creationflags=NO_WINDOW).stdout.strip()
    except Exception:
        return ""

def _major(ver):
    m = re.search(r"(\d+)\.", ver or "")
    return m.group(1) if m else ""
```

不要用 `wmic`（新 Windows 已移除）；`edge://version` 只适合让人手查，代码里要能自动读。

## 2. 运行时环境自检（开始连点前跑，写进日志区）

```python
def _check_env(self, edge):
    self._log("── 环境自检 ──")
    drv = _get_driver_path()          # exe 同目录 > 内置
    ev  = _file_version(edge)
    self._log(f"  浏览器版本: {ev or '读取失败(不影响运行)'}")
    if not drv:
        self._log("  ✗ 未找到 msedgedriver.exe — 离线机无法自动下载驱动")
        self._log("    请把与浏览器同版本的 msedgedriver.exe 放到 exe 同目录")
        return
    dv = _driver_version(drv)
    self._log(f"  驱动位置  : {drv}")
    self._log(f"  驱动版本  : {dv or '读取失败'}")
    me, md = _major(ev), _major(dv)
    if me and md:
        if me == md:
            self._log(f"  · 大版本一致 ({me}) ✓")
        else:
            self._log(f"  ✗ 大版本不一致: 浏览器 {me} / 驱动 {md}")
            self._log("    → 换成与浏览器同大版本的 msedgedriver.exe 放到 exe 同目录")
            self._log("      文件放进去即可生效，不用重新打包")
```

价值：行内机上的失败从 `session not created: This version of MSEDriver only supports...`
（看到也不知道该干什么）变成「换哪个文件、放哪里」。

## 3. 崩溃兜底（`--windowed` 下否则完全静默）

```python
def log_crash(text):
    try:
        with open(os.path.join(APP_DIR, "app_error.log"), "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}]\n{text}\n")
    except Exception:
        pass

# main
try:
    root = tk.Tk(); App(root); root.mainloop()
except Exception:
    tb = traceback.format_exc(); log_crash(tb)
    try:
        from tkinter import messagebox
        messagebox.showerror("启动失败", tb[-1500:])
    except Exception:
        pass
    raise

# 每个 worker 线程统一包一层
def _guarded_thread(self, fn, *args):
    def _wrap():
        try:
            fn(*args)
        except Exception:
            tb = traceback.format_exc(); log_crash(tb)
            try:
                self._log("✗ 运行异常，已写入 app_error.log")
                self._log("  " + tb.strip().splitlines()[-1][:180])
                self._halt_ui()
            except Exception:
                pass
    return threading.Thread(target=_wrap, daemon=True)
```

`app_error.log` 要进 `.gitignore`。

## 4. 打包函数：onefile / onedir 双模 + 驱动必检

```python
def self_build(onedir=False):
    for dep in ["selenium>=4.10", "pyinstaller"]:
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    driver_path = os.path.join(APP_DIR, "msedgedriver.exe")
    if not os.path.exists(driver_path):                    # 离线目标：缺了直接中止
        print("  ERROR: 未找到 msedgedriver.exe")
        print("  目标机离线时无法自动下载驱动，必须随包带上。")
        print("  请把与【运行机】浏览器同大版本的驱动放到本文件同目录后重试。")
        sys.exit(2)
    print(f"  Driver version: {_driver_version(driver_path) or '(读取失败)'}")

    ev = _file_version(_find_edge_for_build())
    if ev:
        print(f"  本机 Edge      : {ev}")
        print("                  ↑ 本机版本不重要，重要的是【运行机】的 Edge 版本")
        if _major(ev) and _major(_driver_version(driver_path)) and \
           _major(ev) != _major(_driver_version(driver_path)):
            print("  WARNING: 本机 Edge 与驱动大版本不一致（给别的机器用则忽略）")

    args = [
        sys.executable, "-m", "PyInstaller",
        "--onedir" if onedir else "--onefile",
        "--windowed", "--name", "AppName",
        "--add-data",   f"{EXAMPLE_PATH}{';' if os.name=='nt' else ':'}.",
        "--add-binary", f"{driver_path}{';' if os.name=='nt' else ':'}.",
        # selenium 4.x 的 webdriver.Edge 是运行时懒加载，手写 hidden-import 枚举必漏
        # （实测漏 selenium.webdriver.edge.webdriver）。必须 collect-all。
        "--collect-all", "selenium",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.scrolledtext",
        os.path.abspath(__file__),
    ]
    subprocess.check_call(args)

    out_dir = os.path.join(APP_DIR, "dist", "AppName" if onedir else "")
    exe = os.path.join(out_dir, "AppName.exe")
    if os.path.exists(exe):
        shutil.copyfile(EXAMPLE_PATH, os.path.join(out_dir, "config.example.json"))
        print(f"\n  Done! {exe}")
```

入口：`--build` → onefile，`--build-dir` → onedir。

| 包型 | 启动 | 行内风险 |
|---|---|---|
| `--onefile` | 每次解压到 `%TEMP%`，慢 2-5s | 杀软/AppLocker 常拦；TEMP 被限制时直接崩 |
| `--onedir` | 直接跑，快 | 分发的是一个目录（整个拷过去即可），**管控电脑首选** |

## 5. build.bat（纯 ASCII + CRLF，含包型菜单）

```bat
@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
echo ==================================================================
echo   AppName -- Build   (run this on a PC WITH internet)
echo ==================================================================
echo   USB --^> build here --^> copy dist folder to the offline PC

echo [1/5] Checking Python...
python --version
if errorlevel 1 (echo   ERROR: Python not found. Install 3.8+ with "Add to PATH". & pause & exit /b 1)

echo [2/5] Checking msedgedriver.exe...
if not exist msedgedriver.exe (
  echo   ERROR: driver missing. The target PC is offline, it MUST be bundled.
  echo   Put the driver that matches the TARGET PC Edge version next to this file.
  pause
  exit /b 1
)
for /f "delims=" %%v in ('msedgedriver.exe --version 2^>nul') do set "DRVVER=%%v"
echo   Driver : !DRVVER!
for /f "delims=" %%e in ('powershell -NoProfile -Command "try{(Get-Item 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe').VersionInfo.ProductVersion}catch{''}"') do set "EDGEVER=%%e"
if defined EDGEVER echo   Edge on THIS pc : !EDGEVER!   ^(not the important one^)
echo   NOTE: only the TARGET pc Edge version matters.

echo [3/5] Installing deps...
python -m pip install -r requirements.txt pyinstaller -q
if errorlevel 1 (echo   ERROR: pip failed. Try: -i https://pypi.tuna.tsinghua.edu.cn/simple & pause & exit /b 1)

echo [4/5] Choose package type
echo   1 = single exe  ^(one file, slower start, unpacks to TEMP^)
echo   2 = folder      ^(recommended for locked-down / anti-virus heavy PCs^)
set "MODE=1"
set /p MODE=Enter 1 or 2 [1]: 
if "%MODE%"=="2" (set "BARG=--build-dir") else (set "BARG=--build")
python flow_clicker.py %BARG%

echo [5/5] Result
set "OUT="
if exist "dist\AppName.exe" set "OUT=dist\AppName.exe"
if exist "dist\AppName\AppName.exe" set "OUT=dist\AppName\AppName.exe"
if defined OUT (
  echo   OK: !OUT!
  echo   NEXT: copy config.example.json to config.json, fill selectors, copy dist to the offline PC
  explorer dist
) else (echo   FAILED - scroll up for the PyInstaller error)
pause
```

坑：
- `set /p` 空回车不会改变已有值 → 先 `set "MODE=1"` 再 `set /p`，默认值才生效
- 括号块里 `set` 后马上 `if defined` 读，必须 `setlocal enabledelayedexpansion` + `!VAR!`，否则是解析期的空值
- 有 `&` 的 echo 行别加括号嵌套过深；`^(` `^)` 转义括号，`^&` 转义与号
- 写完 `file build.bat` 必须是 `DOS batch file text, ASCII text, with CRLF line terminators`

## 6. 不依赖 Windows 的验证手法

两种都在 macOS 上跑通（`py_compile` + 逻辑桩），比在行内机反复打包快两个数量级。

**a) 冻结路径 / 驱动优先级**：先 stub `selenium`、`tkinter` 到 `sys.modules`，再设
`sys.frozen=True; sys._MEIPASS="/tmp/fz/_MEI"; sys.executable="/tmp/fz/dist/App.exe"`，
`importlib.reload(mod)` 后断言：

```
only bundled -> /tmp/fz2/_MEI999/msedgedriver.exe
local wins   -> /tmp/fz2/dist/msedgedriver.exe     ← 换驱动免重打
none         -> None
环境自检 → ✗ 未找到 msedgedriver.exe — 离线机无法自动下载驱动
```

**b) 打包缺模块的报错路径**（本次踩坑后补的单测，防止再退化成静默重试）：
把桩里的 `webdriver.Edge` 写成 `raise ModuleNotFoundError("...edge.webdriver")`，再把
`mod.subprocess` 换成 `SimpleNamespace(Popen=..., run=..., DEVNULL=-3, CREATE_NO_WINDOW=0)`、
`socket.socket` 换成 `connect()` 不抛异常的假对象（骗过端口探测），断言：

```python
assert "打包缺 selenium 模块" in logs              # 日志说清是打包问题
assert "重新打包" in logs                          # 给出下一步
assert calls["edge"] == 1                         # 只尝试一次，不再兜底重试
```

⚠️ **桩要跟着静态 import 一起加**：代码里多了 `import selenium.webdriver.edge.webdriver` 之后，
所有只注册了 `selenium.webdriver.edge`（非包）的旧桩都会在 import 阶段就 `ModuleNotFoundError:
'selenium.webdriver.edge' is not a package`。补一行 `mk("selenium.webdriver.edge.webdriver", WebDriver=object)`
即可，别误判成代码坏了——本次四个测试同时红就是这么来的。

**c) 版本解析 / 缺文件安全**：`_major("143.0.3650.139")=="143"`、
`_major("Microsoft Edge WebDriver 143.0.3650.139 (abc)")=="143"`、
`_file_version("/no/such") == ""` 且不抛异常（macOS 上没有 powershell，正好验证降级路径）。

stub 模板见本 skill「弹窗按钮 id 是自增的」章节里的假 driver 桩，两者可拼在一起用。
