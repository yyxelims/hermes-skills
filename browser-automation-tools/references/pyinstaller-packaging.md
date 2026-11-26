# PyInstaller 打包指南

## Windows 打包（正常路径）

```batch
pip install selenium pyinstaller
pyinstaller --onefile --windowed --name ToolName script.py ^
    --collect-all selenium ^
    --hidden-import tkinter
```

参数说明：
- `--onefile`：单 exe 文件
- `--windowed`：运行时不弹命令行窗口
- `--name`：exe 文件名
- `--collect-all <pkg>`：**第三方库一律优先用它**（PyInstaller ≥4.4）。它等价于
  `--collect-submodules` + `--collect-data` + `--collect-binaries`，一次收全。
- `--hidden-import`：只留给 tkinter 这类没有懒加载的简单模块

**为什么不要手写 hidden-import 枚举**：selenium 4.x 的 `webdriver.Edge` 是运行时懒加载
`selenium.webdriver.edge.webdriver`，2026-11-04 实测「把 `selenium.webdriver.edge`、`.options`、
`.service`、`.common.by`、`selenium.common.exceptions` 全写进 hidden-import」**照样报**
`No module named 'selenium.webdriver.edge.webdriver'`。双保险：

```python
# 文件顶层（别放函数里）
import selenium.webdriver.edge.webdriver  # noqa: F401
```

判断口径：打包后报 `No module named '<某第三方包的子模块>'` → 无脑换 `--collect-all <包名>`，
不要在 hidden-import 列表里打地鼠。

## macOS → Windows 交叉打包（不可行）

以下方案在 Apple Silicon Mac 上全部失败：

| 方案 | 具体尝试 | 失败原因 |
|------|---------|---------|
| `cdrx/pyinstaller-windows` Docker | `docker run --platform linux/amd64` | Wine 在 macOS Docker VM 中 `virtual.c:281: alloc_pages_vprot` 崩溃 |
| Wine staging 升级 | 在容器内 `apt install wine-staging` | 同样的虚拟内存错误，Wine 4.x→5.19 均不工作 |
| `--privileged` 模式 | Docker 特权模式 | 无济于事，是 macOS 虚拟化框架的底层限制 |
| Nuitka + mingw-w64 | `x86_64-w64-mingw32-gcc` 交叉编译 | 缺少 Windows Python 头文件(.h)和导入库(.lib) |
| Homebrew Wine | `brew install --cask wine-stable` | 安装后 `/Applications/Wine Stable.app` 不存在，`wine` 命令不可用 |
| `gcenx/wine` tap | `brew tap gcenx/wine` | 仅有 Game Porting Toolkit，无通用 Wine |
| 生成 .def + dlltool | `x86_64-w64-mingw32-nm` 解析 DLL | 只能找到 1 个符号，无法生成有效的导入库 |

### 根本原因

macOS 的 Hypervisor.framework（Docker Desktop 底层）不给 VM 内的 Wine 分配足够大的连续虚拟内存页。Wine 的 `alloc_pages_vprot` 在 Apple Silicon 上的 Rosetta 2 + VM 嵌套场景下系统性失败。这是操作系统级限制，不是配置问题。

### 替代方案

1. **Windows 上打包**：拷贝脚本到 Windows，`pip install pyinstaller && pyinstaller --onefile --windowed script.py`
2. **GitHub Actions**：`windows-latest` runner，免费
3. **远程 Windows 机器**：SSH + SCP

## EdgeDriver 处理

`webdriver-manager` 可以在运行时自动下载匹配的 EdgeDriver：

```python
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.service import Service as EdgeService

service = EdgeService(EdgeChromiumDriverManager().install())
driver = webdriver.Edge(service=service, options=options)
```

但如果用远程调试模式（连接已有浏览器），**不需要 EdgeDriver 也不需要 webdriver-manager**：

```python
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Edge(options=options)  # 无需 Service
```
