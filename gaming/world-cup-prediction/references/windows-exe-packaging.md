# Windows Python EXE 打包模式

本文件记录本次 session 中发现的可靠/不可靠的打包模式。

## 不可靠的方式

### Docker + Wine 交叉编译（Apple Silicon Mac）
- **结论**：完全不可行
- `cdrx/pyinstaller-windows`、`batonogov/pyinstaller-windows` 等镜像使用的 Wine 在 Apple Silicon 的 Rosetta 2 虚拟化下有 `virtual.c:281: alloc_pages_vprot` 内核级崩溃
- `--platform linux/amd64`、`--privileged`、`WINEARCH=win32` 均无效
- 这是 macOS 虚拟化框架 + Wine 的底层 bug，无 workaround

### Nuitka 交叉编译
- mingw-w64 可以安装，但 Nuitka 交叉编译到 Windows 需要完整的 Windows Python 头文件和导入库
- Windows Python 安装包（NSIS 格式）无法在 macOS 上完整提取
- `gendef` + `dlltool` 从 DLL 生成 `.lib` 的方法在交叉环境下不稳定

### Homebrew Wine
- `wine-stable` cask 在 Apple Silicon 上安装后 `wine` 命令不可用
- `gcenx/wine` tap 只有 Game Porting Toolkit，不适用于构建

## 可靠的方式

### 1. GitHub Actions（云端 Windows runner）
```
.github/workflows/build_exe.yml:
  runs-on: windows-latest
  steps:
    - setup-python
    - pip install selenium pyinstaller
    - pyinstaller --onefile --windowed
    - upload-artifact
```
优点：零本地依赖，自动构建
缺点：需要 git push

### 2. Windows 本机 PyInstaller（build_exe.bat）
```bat
@echo off
cd /d "%~dp0"
python send_approval.py --build
pause
```
要点：
- `.bat` 文件**必须纯 ASCII**：中文在 Windows CMD 中乱码导致命令截断
- `--trusted-host` 是 Mac 网络 workaround，Windows 不需要
- 文件编码用 UTF-8 without BOM

### 3. EdgeDriver 内置打包
打包时下载 EdgeDriver 并塞进 exe：
1. 读注册表获取 Edge 版本：`HKCU\SOFTWARE\Microsoft\Edge\BLVersion`
2. 从 `https://msedgedriver.azureedge.net/{version}/edgedriver_win64.zip` 下载
3. PyInstaller 用 `--add-binary "msedgedriver.exe;."` 打包
4. 运行时从 `sys._MEIPASS` 读取：`os.path.join(sys._MEIPASS, "msedgedriver.exe")`

Selenium 连接方式（Selenium 4.10+）：
```python
from selenium.webdriver.edge.service import Service as EdgeService
# 直接传 exe 路径，不需要 Selenium Manager 下载
service = EdgeService(executable_path=driver_path)
opts = EdgeOptions()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Edge(service=service, options=opts)
```

## SPA 页面工具设计模式

当目标系统是单页应用（URL 不变，内部导航不跳转）时：
- 工具**不应自动导航**到目标 URL——URL 只能到达入口页
- 采用**三步分离**流程：LAUNCH BROWSER → 用户手动导航 → START点击
- 不要用 URL 输入框驱动自动跳转，用"about:blank"打开浏览器让用户自己操作

## pip 版本兼容

- macOS 网络问题经常需要 `--trusted-host pypi.org --trusted-host files.pythonhosted.org`
- Windows 通常不需要——加了反而可能冲突
- `selenium>=4.10` 才能可靠使用 `EdgeService()` + `debuggerAddress`
- 低版本 selenium 不内置 Selenium Manager，手动下载 EdgeDriver 是必需的
