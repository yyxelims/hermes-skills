---
name: browser-automation-tools
description: 用 Selenium 构建浏览器自动化工具（连点、表单填写、批量查询）。含 Tkinter GUI 模板、Edge 远程调试模式、多选择器兜底策略、PyInstaller 打包指南。用户提到连点、自动点击、模拟点击、Selenium、批量操作、浏览器自动化时触发。
tags: [selenium, automation, gui, tkinter, edge, windows, packaging]
---

# 浏览器自动化工具构建 Skill

## ⚠️ 最关键的规则：用户已有能跑的代码 → 只做最小改动

如果用户给了你一份已验证可用的 `.py` 文件，**不要重写，不要"优化"，不要"重构"**。正确的做法：
1. 对照原版，只修改需要改的部分（加日志、换选择器、拆分按钮）
2. 原版的 import 方式、启动方式（EdgeService vs 远程端口）、打包方式——全部原样保留
3. 不要改 import 位置、不要改启动逻辑、不要"改进"代码结构

本次 session 反复重写 send_approval.py 导致：import 放函数体内 → 打包 exe 找不到模块 → 浏览器打不开 → 按钮没绑定 → batch 编码错误闪退。最终用户说"按这个修"才解决。**教训：拿到能跑的代码 → 只改必要的部分 → 其他逻辑原样保留。**

## 硬编码选择器模式（最简单可靠）

不需要输入框，直接把验证过的选择器写死在代码里。支持 CSS 和 XPath fallback。模板见：`templates/send_clicker.py`

## 核心模式

构建 Selenium 浏览器自动化工具的标准流程：

1. 先用远程调试连上已有浏览器（保留登录态）
2. 写核心点击/填写逻辑（多选择器兜底）
3. 包 Tkinter GUI（开始/停止/速度控制）
4. PyInstaller 打包成独立 exe

## 远程调试连接（Edge / Chrome）

用户不想每次跑自动化都重新登录 → 连已有浏览器：

```powershell
# Windows: 先关掉所有 Edge，管理员 PowerShell 运行：
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222
```

Python 连上去，不需要写死 URL——用户自己导航到目标页面：

```python
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions

options = EdgeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Edge(options=options)  # 不需要 Service/路径

# 从所有标签页找到目标
for handle in driver.window_handles:
    driver.switch_to.window(handle)
    if "审批" in driver.title:  # 用关键词匹配
        break
```

**优点**：不需要 EdgeDriver、用户自己管理登录态、可以在其他标签页同时操作。

## 元素定位：多选择器兜底

不要依赖单一选择器——网站改版就全挂。用层级兜底：

```python
def click_send_button(driver):
    selectors = [
        (By.ID, "_ctp_toolbar_item_button_sendfmbm"),     # 最精确
        (By.LINK_TEXT, "发送总行审批"),                     # 按文字找
        (By.PARTIAL_LINK_TEXT, "发送总行"),                 # 部分文字
        (By.CSS_SELECTOR, "[id*='sendfmbm']"),              # ID 包含
        (By.XPATH, "//*[contains(text(),'发送总行审批')]"), # XPath 兜底
    ]
    for by, value in selectors:
        try:
            elem = driver.find_element(by, value)
            driver.execute_script("arguments[0].click();", elem)  # JS 绕过可见性检查
            return True
        except NoSuchElementException:
            continue
    return False
```

关键：用 `execute_script("arguments[0].click();", elem)` 而非 `elem.click()`——前者不检查元素的可见性/可点击状态，适合绕过前端拦截。

## 循环点击模式

```python
while not stop_event.is_set():
    # ① 先检查并关闭失败弹窗
    if check_and_close_error_dialog(driver):
        error_count += 1
        continue
    
    # ② 点击目标按钮
    if click_target(driver):
        click_count += 1
    
    # ③ 检查是否成功（按钮变灰/消失/出现成功提示）
    if is_success(driver):
        break
    
    time.sleep(interval)
```

## 检测成功：用 disabled 属性

当操作成功后，按钮通常会 `disabled`：

```python
def is_success(driver):
    try:
        btn = driver.find_element(By.ID, "target_button_id")
        return btn.get_attribute("disabled") is not None
    except NoSuchElementException:
        return False
```

## 关闭弹窗：也需多种方式兜底

```python
def close_dialog(driver):
    # 方式1: id 前缀 + 文案匹配（⚠️ 绝不能写死 ymPrompt_btn_0 — 见「弹窗按钮 id 是自增的」）
    try:
        for btn in driver.find_elements(By.CSS_SELECTOR, "input[id^='ymPrompt_btn_'][value*='确']"):
            if btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                return True
    except: pass

    # 方式2: 弹窗容器里的"确定"
    try:
        dlg = driver.find_element(By.CLASS_NAME, "ctp-messagebox-btn")
        for b in dlg.find_elements(By.TAG_NAME, "input"):
            if b.get_attribute("value") == "确定" and b.is_displayed():
                driver.execute_script("arguments[0].click();", b)
                return True
    except: pass
    
    # 方式3: 全文扫描 value="确定"
    for b in driver.find_elements(By.TAG_NAME, "input"):
        if b.get_attribute("value") == "确定" and b.is_displayed():
            driver.execute_script("arguments[0].click();", b)
            return True
    return False
```

## Tkinter GUI 模板

标准结构：速度滑块 + 开始/停止按钮 + 日志区 + 状态栏。

```python
class ClickToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("工具名")
        self.driver = None
        self._stop_event = threading.Event()
        self.click_count = 0
        self._build_ui()
    
    def _build_ui(self):
        # 速度滑块
        self.speed_var = tk.DoubleVar(value=0.3)
        ttk.Scale(from_=0.1, to=5.0, variable=self.speed_var)
        # 开始/停止按钮
        ttk.Button(text="开始", command=self.start)
        ttk.Button(text="停止", command=self.stop)
        # 日志 + 状态栏
        
    def start(self):
        self._stop_event.clear()
        self.driver = connect_browser()
        threading.Thread(target=self._worker, daemon=True).start()
    
    def _worker(self):
        while not self._stop_event.is_set():
            do_work()
            self._stop_event.wait(self.speed_var.get())
```

## PyInstaller 打包

### 在 Windows 上打包（正常路径）

```batch
REM build_exe.bat — 双击打包
pip install selenium pyinstaller -q
pyinstaller --onefile --windowed --name SendApproval --hidden-import selenium --hidden-import tkinter send_approval_v2.py
```

或者用 Python 脚本：
```python
python build.py  # 含依赖安装、清理、构建、打开输出文件夹
```

`--windowed` = 不弹命令行窗口，`--onefile` = 单 exe。

### 在 macOS 上打包 Windows exe（不可行）

**Apple Silicon Mac 上无法为 Windows 打包。** 原因：

| 方案 | 结果 |
|------|------|
| Docker + Wine (`cdrx/pyinstaller-windows`) | Wine 在 macOS 虚拟化框架下 `virtual.c:281: alloc_pages_vprot` 崩溃 |
| Docker + Wine staging | 同样的虚拟内存错误 |
| `--privileged` 模式 | 无济于事 |
| Nuitka + mingw-w64 交叉编译 | 缺少 Windows Python 头文件和依赖库 |
| Homebrew Wine (`wine-stable`, `wine-crossover`) | Apple Silicon 上 wine 命令不可用 |

**唯一可靠路径：在 Windows 机器上打包，或用 GitHub Actions (`windows-latest` runner)。**

## 关键 pitfalls

1. **不要用 `button.click()`，用 `execute_script("arguments[0].click();", elem)`**——绕过可见性检查
2. **不要依赖单个选择器**——网站改版 = 工具报废
3. **不要在主线程跑 Selenium**——GUI 会冻结，必须在后台线程
4. **Apple Silicon Mac 不能为 Windows 打包 exe**——这是硬限制，不要反复尝试
5. **Edge 连接已有浏览器不需要 EdgeDriver**——`debuggerAddress` 模式不需要驱动文件
6. **`time.sleep()` 会阻塞 `stop_event` 检查**——用 `stop_event.wait(timeout)` 替代
7. **区分浏览器原生弹窗 vs 网页DOM弹窗**——原生 alert 用 `switch_to.alert.accept()`，DOM 弹窗用 `find_element` + JS click。用户说"浏览器信息/浏览器弹窗"= 原生 alert，不是 DOM 元素。搞混了工具完全不工作。
8. **先读懂用户给的 HTML 再写代码**——用户给 1.txt 两个元素，第一个是网页 `<a>` 按钮，第二个是网页 `<input>` 弹窗按钮。但用户说"点击第一个会弹出浏览器信息"——这个"浏览器信息"是原生 alert，不在 HTML 里！必须问清或从流程描述推断出三步流程，不要只看 HTML 就动手。
9. **工具必须内置诊断模式**——用户在行内电脑打包运行，反复试错成本极高。诊断按钮（只检测不点击）让用户跑一次就能远程定位选择器/iframe/弹窗问题。
10. **`--remote-debugging-port` 必须配 `--user-data-dir`**——不加独立用户目录，新 Edge 窗口合并到后台残留进程，端口参数被忽略，Selenium 报 `cannot connect to Edge at 127.0.0.1:9222`。这是远程调试端口方式最常见的失败原因。
11. **EdgeDriver 版本必须与 Edge 浏览器版本匹配**——Edge 自动更新（143版），打包进去的旧驱动（126版）会报 `session not created`。每次打包前确认 EdgeDriver 版本。查 Edge 版本：地址栏输入 `edge://version`。
12. **Socket 检测端口先于 Selenium 连接**——Selenium 连不上时先 socket 探测 9222 端口是否真的开了，没开直接提示而不是等 Selenium 超时报一大堆 stacktrace。
13. **诊断模式必须 alert-safe**——点击成功后原生弹窗还挂着，此时 current_url/find_element/switch_to 全部抛 `UnexpectedAlertPresentException`。弹窗检测必须放诊断**最前面**，其余区块逐个 `_safe()` 包容错，不能一处异常整个诊断崩成一行。详见"诊断模式必须 alert-safe"章节。
14. **UnexpectedAlertPresentException 是信号不是错误**——工具里凡 catch-all `except Exception: pass` 的地方（如多上下文查找/点击、变灰检测），弹窗挂着时会被静默吞掉，造成"按钮找不到"的假象。检测类函数要么显式处理它并报"被弹窗挡住"，要么让诊断层能区分"没找到"和"被弹窗挡住"——两个状态的日志必须不同。
15. **弹窗确认按钮的 id 会自增，绝不能写死**——`ymPrompt_btn_0` 只对第一个弹窗成立，出现 `_9` 说明已经堆了 10 个。一律用 `input[id^='ymPrompt_btn_'][value*='确']` 这种「id 前缀 + 文案包含」的写法。本 skill 旧版那份 `["ymPrompt_btn_0","ymPrompt_btn_2","ymPrompt_btn_1"]` 硬编码列表就是 2026-11-04 翻车的直接原因，已删除。
16. **JS click 会把遮罩保护一起绕掉**——`execute_script("arguments[0].click();")` 不看遮挡，所以「弹窗没关掉」和「主按钮还能点」会同时成立，形成弹窗堆叠死循环。凡是「关弹窗 + 点主按钮」的循环，必须做防堆叠：每轮先排干残留弹窗、确认按钮找不到时停止点主按钮、失败不计轮数。
17. **XPath 兜底救不了 iframe 层数不够**——只扫一层的 `find_elements(By.TAG_NAME,"iframe")` 看不到嵌套 frame 里的元素，表现是「连 `//input[contains(@value,'确')]` 都找不到，但用户屏幕上明明有」。改成 BFS 递归 `_frame_paths()`，层数用 `max_frame_depth` 配置化（默认 3）。统一用 CSS `"iframe, frame"` 查询，别混用 `iframe`/`frame` 两套索引。
18. **按钮文案带全角空格**——`value="确 定"` / `"取 消"`，直接 `"取消" in txt` 判不出来。比较前先 `norm(s) = "".join(s.split())`。
19. **`--windowed` 崩了是彻底静默的**——没有 stderr、没有弹窗，用户只看到「双击没反应」。`main` 里包一层
    try/except 把 traceback 追加写入 exe 同目录的 `*_error.log`，**每个 worker 线程也要包**（用
    `_guarded_thread(fn)` 统一包），否则用户只能告诉你「就是不动了」。
20. **用户说「打包」时先问清交付链，别先讲「有 Python 就不用打包」**——银行场景几乎一定是
    「行外打包 → 行内运行」，问的是这条链怎么搭，不是要不要 exe。用户连纠正两次：「不是，我是要用优盘把
    代码和批处理还有正确版本的 edgedriver 拷到行外 windows 上做打包，再把可执行文件放到行内 windows 上运行。」
    先复述交付链再动手，能省一轮返工。
21. **别把「脱敏版」的配置化方案套到自用/U 盘版上**——用户原话：「我让你直接把该点什么明文写死进代码里，
    不要给我弄什么破 json 再让我自己填写」。同一份工具要交付**两份产物**：
    U 盘/行内自用版 = 元素明文写死、零配置、驱动内置单文件 exe；git 版 = 脱敏 + `config.example.json` 占位符。
    把 config 那套搬到 U 盘版 = 让用户在行内机上手工填选择器，是纯倒退。详见
    `references/plaintext-vs-sanitized-delivery.md`。
22. **「能明白我什么意思吗？」= 你漏了核心约束，不是让你解释**——用户这句话出现时，别复述、别辩解，
    直接按他刚说的重做，并把改动点逐条列出来（写死了什么、内置了什么、删掉了什么）。
23. **`No module named 'selenium.webdriver.edge.webdriver'` ≠ 环境问题**——环境自检全绿、端口已开的时候
    报这个，就是打包漏了懒加载子模块。修复只认两条：`--collect-all selenium` + 顶层
    `import selenium.webdriver.edge.webdriver`，手写 hidden-import 枚举救不了。
24. **有了结论要能自我反驳**——本次日志里「驱动 143 ✓ / 端口已开 / 马上报 No module named」三行同时出现，
    就该立刻排除驱动和网络假设，直接去查打包参数；不要顺着「再试一次连接」的惯性继续重试。
25. **日志里的 `⚠ 点击失败: NoSuchElementException` 十有八九是自己在错的 frame 里点**——`_find`
    扫完所有 frame 后 driver 停在最后一个 frame，拿着前面某个 frame 找到的元素去 `execute_script`，
    必然 NoSuchElement。点击前必须 `_goto_path(元素所在路径)` 切回去；`_find` 要**返回 frame 路径**
    而不是一个 ctx 字符串。
26. **别把「隐藏但存在」的元素当兜底返回**——弹窗关掉后 ymPrompt 按钮还在 DOM（`visible=False`），
    当命中就会每轮刷一行 `⚠ 点击失败`，把真异常淹掉。查找只返回**可见**元素；隐藏项只在诊断里列。
    「清残留弹窗」这类本来就可能没有目标的探测要传 `quiet=True`。
27. **固定 sleep 调到 0.6s 以下必翻车**——上一轮弹窗还有淡出动画，此时点主按钮是空点（日志：A 点了 →
    5 秒没弹窗 → C 全空 → 超时停机）。改**事件驱动**：轮询「弹窗一出现就立刻继续」；点完主按钮长时间
    无任何窗口先**重试 3 次**（6s/2.5s/2.5s），仍无才是「没有待处理的了」。
    **最终解不是把下限从 0.5 调到 0.4，而是每轮结束校验「确定按钮真的消失了」**
    （`_dialog_gone_wait`：可见性判定 + 补点，见「间隔还能不能更小」），`MIN_GAP=0.1` 只当兜底——
    详见 `references/timing-probe.md`。
28. **「按钮变灰 = 全部发完」要加前提**——有些页面这个按钮天生就是灰的（这单不需要走这一步），
    一见 `disabled` 就 break 会立刻误停。必须**见过一次 enabled 才认 disabled**（`_submit_state()`
    返回 enabled/disabled/missing；诊断里也报三态而不是布尔）。
    **而且「灰」有三种表现，只认 `disabled` 属性会把它当成「能点」**：`disabled` 属性 /
    `class` 里带 `disab`（CTP 工具栏就是这种）/ `aria-disabled="true"`。漏认的后果不是误停，
    是**反向的**——程序以为能点，于是每轮点一下、每轮打一行 `✓ [发送总行审批] 已点击`，永远不停
    （用户原话：「点开始总行连点，按钮是灰色的时候还是在打日志」）。三态判定 + 三道闸门的完整代码、
    桩测试见 `references/batch-mode-grey-button-guards.md`。
29. **用户说「有没有什么方式探索一下、我把日志弄出来给你」= 给他一个探针，不是让他盯着屏幕描述**——
    加个「测速/探针」按钮，把每段毫秒、关键状态（遮罩层数、按钮 disabled、所在 frame）写进
    exe 同目录的 `utf-8-sig` 文本报告，让他发文件。用户主动提出要配合采集时，千万别回「你多试几次看看」。
30. **改公共方法签名后，桩测试会立刻抓出来**——本次 `_click(..., quiet=True)` 少传一层参数，
    在仿真测试里直接 `TypeError`；没有桩就只能打包后在行内电脑上才发现。凡是加了参数的包装方法
    （`_click` → `_click_any`），改完先跑一遍本地假 driver 测试。
31. **用户说「我屏幕上看到 X 一直在」时，把它当一手证据，优先于你的日志推断**——本次据
    「遮罩消失 3020ms」推断"页面慢、0.1s 物理不可能"，用户一句「确定按钮一直在，所以你一直没有
    把它点掉」直接推翻：真正没做到的是那一下点击。**日志证明我点了，不证明点成功了。**
    凡是"某状态一直不满足 → 我超时"的循环，先加一条"动作是否生效"的校验（按钮/元素是否消失），
    再谈时长。
32. **每轮之间「格很久」八成是提交锁 + 我自己的长超时，不是间隔**——点完确定后应用在后台提交，
    工具栏有一段被**静默锁住**的时间，这期间点主按钮不报错、不弹窗。旧版「点一次然后死等 6 秒看
    有没有弹窗」正好把锁期整段睡过去，实测每轮白花 6 秒。正确做法：0.8s 内没弹窗就判定这一枪被吞
    → **立刻重点**，一轮最多 12s；生效后记一行「第 N 次才生效，锁了 X.Xs」。**别把重试间隔设成
    6 秒——那不是耐心，那是浪费**。详见 `references/post-submit-lock-retry.md`。
33. **加快重试之前，必须先证明「点击不会排队」**——银行单据类页面上，连续点击有可能被应用排队成
    多次提交（重复发单）。用户喊「大胆点、疯狂点」时，正确做法是做一个**带安全阀的实验**：每 100ms
    点一次、**一出现弹窗立刻停手**、事后数「多冒出几个确认框」（`重复 = max(0, 补点次数-1)`）。
    重复数 >0 就说明点击会排队，**重试间隔必须放大甚至改成不重试**；重复数 =0 才敢把
    `A_RETRY_TIMEOUT` 压到 0.2 甚至更低。判读表与完整代码见
    `references/hammer-probe-and-duplicate-risk.md`。**先拿一笔测试单跑，别上正式单。**
34. **判断「弹窗清干净了」必须给异步留时间**——点掉原生 alert 之后，网页确认框是**稍后**才创建的。
    此时立刻问「有没有可见确认框」，答案是「没有」→ 被当成「已经清干净」，其实是**假阴性**；
    下一轮开局的残留弹窗就是这么漏掉的。凡是在 accept/close 之后做「是否已消失」判断，
    先 `wait(0.3)` 再判（清理型判断要判两次）。同理：`_dialog_gone_wait` 返回 True 只代表
    **此刻**没有，不代表**马上不会出现**。
35. **探针的结论别解析自己打的日志字符串**——`l.split("最大")[1]` 这种写法会输出「最长约 8ms」
    这种笑话。所有统计都从**数值列表**算（`max(lat_clear)` / `sum(...)/len(...)`），格式化只用于展示。
36. **原生 alert 属于触发它的那个 frame，不是"浏览器级、在哪都看得见"**——iframe 里的按钮弹出的
    alert，一旦上下文被 `_find`/`switch_to.default_content()` 切走，`switch_to.alert` 就**永远**报
    "没有弹窗"。表现是「点了 A 之后 6 秒无声 → 提示没弹窗 → 重试一枪就立刻弹」。**这是本 skill 曾经
    写错的一条结论，2026-11-04 实测推翻。** 判断/关闭 alert 前必须切回主按钮所在 frame
    （缓存 `_a_path`）。任何日志里出现"每轮第一枪必空、重点必成"，先查这个，再怀疑锁/间隔。
    详见 `references/frame-scoped-alert.md`。
37. **所有耗时都约等于你设的超时值 = 假测量**——报告里一片 `3020ms / 3026ms / 3038ms`（超时设 3s）
    说明等的东西根本没成立，不是"页面需要 3 秒"。同理 `A→弹窗 340ms` 里可能大半是**自己扫 frame
    树的开销**。先怀疑"动作没生效 / 判据看不见 / 开销算进延迟了"，再谈页面慢；测量脚本要能把
    "点击耗时"和"点击后到弹窗的耗时"分开记。
38. **用户说「还是会有轮间间隔，彻查代码」= 数 WebDriver 命令，不是调参数**——轮循环里每一次
    "查一下有没有弹窗"都是一次 `find_elements` × N 选择器 × N frame 路径；一次**未命中** ≈ 35 条命令
    = 0.5–1.5s，一轮里往往有 3 次这样的未命中。体检动作：把 loop 体内每个 Selenium 调用列出来，
    稳态每轮应 ≤ 25 条。本次从 37 条降到 22 条，轮间间隔才从「秒级」变成「interval + 30ms」。
39. **热循环里用一条 `execute_script` 查/点，**但只对弹窗里的「确定」**——在**已缓存的 frame** 里
    `document.querySelectorAll("input[id^='ymPrompt_btn_']")` + `.click()`，一次往返约 20ms。
    ⚠ **不要用同一个手法去点工具栏按钮**：实测 `document.querySelector("#_ctp_toolbar_item_button_send").click()`
    返回成功但页面**毫无反应**（框架绑的是 mousedown/自定义事件），而 Selenium 的
    `execute_script("arguments[0].click();", el)` 有效。铁律：**工具栏/业务按钮走 Selenium（多选择器 + 可见性判定），
    只有弹窗「确定」用 JS 直点**。日志上两者可区分：Selenium 路径打 `已点击 (frame[1]) id=xxx`，
    JS 路径没有 `id=`。详见 `references/js-click-scope-and-lazy-find.md`。
    关键细节：JS 明确返回「""＝现在没有」时**绝不能**退回去扫 frame 树（那正是耗时来源），
    只在每 10 次空结果时校准一次缓存路径。
40. **间隔要"补差额"，不能叠加**——从「点确定」那一刻起算满 `interval` 就进下一轮；
    如果校验已花掉 80ms，就只补剩下的 20ms，别再 `sleep(interval)` 全量加一遍。
    配套：轮询粒度 50ms、`_goto_path` 若已在目标 frame 直接 early-return、窗口句柄 pin 住不来回切。
41. **重试/补点的窗口必须大于页面延迟**——`A_RETRY_TIMEOUT=0.2s` 小于实测 350ms，会在弹窗出现前
    重复点主按钮（重复提交风险）；点完「确定」后 250ms 内也不要补点同一个按钮（淡出中会重复触发）。
    给"动作生效"留 grace，别比谁快。
42. **审计测试要能"禁止"退化**——把 `_frame_paths` 在第 1 轮之后 monkeypatch 成直接 `raise`，
    再统计每轮 WebDriver 命令数与「点确定→下次点A」的毫秒差。这样"又在稳态扫树"会立刻测试失败，
    而不是等用户再抱怨一次。骨架见 `references/steady-state-speed-audit.md`。
43. **别让用户从秒级时间戳里去推间隔**——日志用 `%H:%M:%S` 时，134ms 的轮间间隔两条记录同秒，
    用户根本算不出来（本次用户直接质问"你就不能直接计算这个间隔吗？没到一秒怎么办？"）。
    动作：① 时间戳改 `strftime("%H:%M:%S.%f")[:-3]`；② **程序自己算并打印**每轮间隔/本轮耗时；
    ③ 停止时给汇总（平均/最大/最小）；④ 给一条判据（`≈ interval + ≤200ms` 为正常，>1s 才是我漏了东西），
    让用户不用懂代码就能自我判断。**能算的数字不要交给用户去减。**
44. **间隔必须从"真正点下去的时刻"算，不是"检测到弹窗的时刻"**——本次第一版把 `t_a_ok`
    记在 `_wait_effect()` 返回之后，日志打"轮间间隔 366ms"，外部实测只有 134ms：多出来的
    232ms 是页面延迟 + 轮询粒度。日志数字骗人比没有数字更糟。在"点"的动作里打点
    （`_click_a` 里 JS click 成功立即 `self._t_a_click = time.time()`），间隔与轮耗时都用它。
45. **worker 里初始化自己的统计字段，别只放 `__init__`**——桩测试常用 `object.__new__(App)`
    绕过 `__init__`，新增 `_gaps`/`_t_c_prev` 后立刻 `AttributeError`（本次 4 个测试同时红）。
    凡是被 worker 独占的运行时状态，在 worker 开头重置一遍（顺带保证"再点开始"时统计归零）。

46. **短周期仿真跑出来的数字，不能当承诺**——本次拿"3 轮仿真 = 134ms/轮"去汇报，真机连跑 40 轮
    是 **3.0s/轮**。仿真是假 driver、命令延迟按 8ms 估、页面延迟按几十毫秒建模，**它只能验逻辑，
    不能估吞吐**。引用任何"每轮多少秒 / 每分钟多少笔"之前，必须在真机上跑 **≥20 轮**，从日志里
    取平均值。给用户报数时写清来源（"仿真 134ms"≠"真机 3.3s"），报错了立刻认并给订正后的表。
47. **"没有锁"的结论可能只是探针看不见锁**——狂点实验每个 trial 之前都有 `_dialog_gone_wait`
    + 0.3s 等待，等它开始点时页面早已稳定，于是量到"首点 350ms 就弹、重复 0"。而**持续循环**
    （40 轮）显示：第 1 轮 0.03s，之后每轮 2.1–3.6s、要点 3–4 次才弹。两者不矛盾——**探针的
    起点决定了它看不见什么**。凡是"单次试验"和"持续循环"结论冲突，**以持续循环为准**（那是用户
    真实的运行形态），并回头检查探针的预热/间隔是否把待测现象挡掉了。
48. **提交后的不可交互窗口，第一次等待必须覆盖它**——`A_FIRST_WAIT=4.0`（>实测 2–3s），
    日志写成 `· A→弹窗 3.2s (页面提交后的忙碌期, 共点 N 次)`。别用 1s 超时在里面反复点：
    那一枪必被吞，纯属给自己刷无效点击和日志。要把它和"alert 的 frame 作用域"分开归因：
    **frame 作用域问题 = 第一枪立刻就有弹窗（只是我看不见）；忙碌期 = 真的有 2–3 秒点不动。**

49. **界面上"新加的按钮一直是灰的"= 我建了却没启用，不是权限也不是环境**——本次「忙碌期」按钮
    `ttk.Button(..., state=tk.DISABLED)` 建出来后，`_post_connect()` 里只启用了 dbtn/pbtn/hbtn，
    漏了 bbtn，用户看到的就是"怎么一直是灰色、点不动"。规矩：**任何 action 按钮都要有明确的三处状态**
    ——`_post_connect()`（连上后启用）、`_start()`（跑起来时禁用，防止两个线程同时操作同一个页面）、
    `_halt_ui()`（停止后恢复）。增删按钮时三处一起改，并用静态自检兜底：
    `scripts/check_tk_buttons_enabled.py <文件.py>`（创建了但从不启用 → 退出码 1）。
    另外探测类动作要加守卫：连点在跑时点「测速/诊断/探针」直接提示"先点停止"。

50. **两份产物里，只有进 git 的那份有历史——用户随时会问"拉一下三点五十之前那版"**——本次用户要
    "15:50 之前最近的一个版本"，git 里只有脱敏版，**明文版（U 盘那份）一直被覆盖同一个文件**，
    只能反过来按提交手工回退重建（改 6 处，还得再验一遍）。规矩：
    ① 每轮调优后给明文版留带时间戳的快照（`SendFenhang-1547.py` 或 `snapshots/1547/`），一步 `cp` 的成本；
    ② 交付话术里说清"这版对应几点几分"，让"哪一版"可指认；
    ③ 用户要旧版时先给 `git archive <commit> | tar -x -C 目录` 的**快照目录**（别 `git checkout` 动工作区），
    再说明脱敏版与明文版的对应关系。**别让"能不能回滚"变成考古。**

51. **用没被证实存在的信号做门控，会卡死在不具备该信号的页面上**——遮罩门控必须有"未知就放行"的分支：
    JS 跑不了（返回 -1）且此前**从未见过遮罩**时直接返回，别死等；只有真见过 `mask>0` 的页面才严格等它归零。
    通用规则：**任何"等某状态出现"的门控，都要给"这个页面根本没有该状态"留出口**，否则换一个页面就整轮卡住。

52. **删常量/方法后编译通过 ≠ 没删断东西**——Python 只在运行时解析全局名。本次删「测速/狂点」探针时
    一起删了 `JS_BUSY`，而**保留下来的**运行逻辑 `_mask_state()` 还在引用它：`py_compile` 全绿，
    真机一跑就 `NameError`。规矩：删功能后必须 ①`grep` 出每一处剩余引用（含"名字像探针、实际被
    运行逻辑共用"的 JS/常量）；②跑一次带桩的 import/冒烟测试；③在测试里断言"已删名字不再出现"。
    **探针里的 JS 常量经常是共用的**，先确认归属再删。

53. **探针是一次性脚手架，问题定案后就该删——而且用户会明确要求删**——原话：
    「把测速和狂点测删掉，慢速演示一定保留！！！！！」。这类探针（测速/狂点/忙碌期）都会真的提交单据，
    留着是风险不是功能。删除清单：按钮 + 方法 + 常量 + `_post_connect/_start/_halt_ui` 三处状态语句 +
    测试断言 + 静态按钮自检里的名单。**同时保住三类东西**：①运行逻辑共用的 JS/常量（见 pitfall 52）；
    ②用户要用的运行期开关（慢速演示、间隔滑块）；③「诊断」按钮——它是在行内机上唯一能自证状态的入口。
    删完形态：`[启动浏览器][开始分行连点][开始总行连点][停止][诊断]` + 间隔滑块 + 慢速演示勾选框。
    完整删除脚本骨架、验证三步、收敛后的标准形态见 `references/settle-delay-and-probe-removal.md`。

54. **"为了让用户看清"的停顿可能是在补页面节奏**——本次用户开了慢速演示后反馈「更流畅、轮间间隔也变小」，
    查下去是那个 0.6s 停顿正好落在「关原生弹窗」与「点确定（真正提交）」之间，避开了页面收尾期，
    反而省掉 2~3 秒重试。**用户说"保留/开启某个看似多余的动作就变顺"，先怀疑它补了你没发现的时序**，
    别急着优化掉；确认后把它从演示开关拆成默认常量（`SUBMIT_SETTLE=0.6`），演示开关只做额外加时。

55. **用字符串替换改方法体，会留下两份同名定义**——本次把 `_submit_state()` 的头部替换成通用
    `_btn_state()`，原实现没删干净，类里出现两个 `_submit_state`（前一个还引用已不存在的 `selectors`）。
    Python 允许重复定义、后者生效，`py_compile` 全绿、静态检查也看不出来。规矩：**脚本化重构后立刻
    `grep -c "def <方法名>"` 断言等于预期值**，再跑一次带桩 import —— 否则留着的死代码哪天被改顺序就爆
    `NameError`。

56. **模块新增一个顶层 import，所有桩测试都得跟着补**——本次给
    `from tkinter import ttk, scrolledtext` 加了 `messagebox`，四个桩测试当场
    `ImportError: cannot import name 'messagebox'`（不是代码坏了，是 `mk("tkinter", ...)` 没注册子模块）。
    规矩：动过 import 就**全量跑一遍本地桩测试**，并在 stub 里补
    `mk("tkinter.messagebox", showinfo=..., showerror=...)`；
    同理 `winsound` 也要 stub（`MessageBeep` 计数，用来断言"响了几声"）。

57. **「给一个模式加了收尾提示，另一个模式忘了」= 用户下一句一定会问**——本次给分行加了
    「变灰 → 停 + 响三声 + 弹框」，总行只打日志，用户立刻追问：「**总行变灰会有声音吗？**」。
    规矩：**任何跨模式共用的行为（提示音、弹框、计数、日志格式、停止条件），加完立刻 `grep`
    所有 worker 的停止点**（`_worker_fen` / `_worker_zh` / `_worker_batch`）逐个比对，别只改
    当前调的那条分支。分支 ≥2 时把行为抽成单一实现（`_notify()` / `_btn_state()`），
    而不是在每个 worker 里各写一遍——两套实现必然漂移。这也正是用户那句「别修了分行的
    总行又挂了」的另一面：**修改要窄，但一致性审计要全**。

---

## 两种连接模式对比

> **⚠️ 铁律：用户已有能跑的工具 → 启动/连接逻辑必须照搬原版，禁止换方式。**
> 本 session 自作主张把远程调试端口改成 EdgeService 直接启动 → 内网连不上 → 用户发火"之前连点怎么做的现在怎么做不就可以了？"。
> 用户原版 `send_approval_v2.py` 用的是 kill_edge + `--remote-debugging-port` + `debuggerAddress`，**而且能跑**。不要"优化"成别的方式。

### 硬编码选择器模式（最简单可靠）

不需要输入框，直接把验证过的选择器写死在代码里。支持 CSS 和 XPath fallback。模板见：`templates/send_clicker.py`

## IFRAME 处理

银行/政务内网系统的按钮经常藏在 iframe 里，主页面上找不到。必须切进 iframe 再查元素：

```python
def _switch_to_iframe_with_button(driver, selectors):
    """扫描所有 iframe，找到包含目标按钮的那个"""
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for i, iframe in enumerate(iframes):
        driver.switch_to.frame(iframe)
        for by, val in selectors:
            try:
                driver.find_element(by, val)
                return True  # 找到了，留在当前 iframe
            except NoSuchElementException:
                continue
        driver.switch_to.parent_frame()  # 没找到，退回
    return False
```

**优化**：首次扫描后记住 iframe 索引，之后直接 `switch_to.frame(iframes[1])` 无需重扫。

## 弹窗按钮 id 是自增的 + 嵌套 iframe（2026-11-04 实测定位，本次工具翻车根因）

**症状**：连点跑到第 2 轮后日志全是 `C: 10秒内未找到确定按钮`，但主按钮 A 还在点，弹窗越堆越多；用户贴的报错 HTML 是
`<input id="ymPrompt_btn_9" class="btnStyle ctp-fs ctp-ct" value="确 定">`。

**根因三层叠在一起**：

1. **弹窗按钮 id 每次弹出自增**：`ymPrompt_btn_0` → `_1` → … → `_9`。代码写死 `find_element(By.ID, "ymPrompt_btn_0")` → 命中的永远不是当前弹窗。看到 `_9` 就等于「前面已经堆了 10 个弹窗」——这个数字本身就是堆叠证据。
2. **JS click 不受遮罩约束**：主按钮 A 用 `execute_script("arguments[0].click();", el)`，遮罩盖住了照样点得进去（`Element.click()` 才会报 not interactable）。于是「C 关不掉 + A 继续开」= 死循环堆叠。**JS click 的代价就是遮罩保护也一起绕过了。**
3. **弹窗在嵌套 iframe 里**：旧版只扫一层 `find_elements(By.TAG_NAME,"iframe")`，而弹窗在 `iframe[1]` 内再嵌的 frame 里。连兜底的 `//input[contains(@value,'确')]` 都返回「主文档+2个iframe 均未找到」——**XPath 兜底救不了层数不够**。

**正确写法（已验证）**：

```python
FRAME_CSS = "iframe, frame"   # 统一成一个选择器，索引才不会错位

def _goto_path(self, path):
    self.driver.switch_to.default_content()
    for idx in path:
        frames = self.driver.find_elements(By.CSS_SELECTOR, FRAME_CSS)
        self.driver.switch_to.frame(frames[idx])

def _frame_paths(self, max_depth=3):
    """BFS 所有 frame 路径: [] / [0] / [1] / [1,0] …（含嵌套）"""
    paths, frontier = [[]], [[]]
    for _ in range(max_depth):
        nxt = []
        for p in frontier:
            try:
                self._goto_path(p)
            except Exception:
                continue
            for i in range(len(self.driver.find_elements(By.CSS_SELECTOR, FRAME_CSS))):
                nxt.append(p + [i])
        if not nxt:
            break
        paths.extend(nxt)
        frontier = nxt
    self.driver.switch_to.default_content()
    return paths
```

弹窗确认选择器（按顺序试，第一条最关键）：

```python
BTN_CONFIRM = [
    "input[id^='ymPrompt_btn_'][value*='确']",          # id 前缀 + 文案，抗自增
    "input[class*='btnStyle'][value*='确']",
    "input[id^='ymPrompt_btn_']",
    "xpath: //input[starts-with(@id,'ymPrompt_btn_') and contains(@value,'确')]",
]
```

点击时三个必做动作：

```python
txt = (el.get_attribute("value") or el.text or "").strip()
if "取" in norm(txt):        # norm() = 去掉所有空白，"取 消" 才拦得住
    continue                  # 别点取消
if not el.is_displayed():     # 关闭后的 DOM 残留
    continue
driver.execute_script("arguments[0].click();", el)
```

**防堆叠三件套（缺一不可）**：

```python
# ① 每轮开始先清残留弹窗，把已经堆上的排干
drained = 0
while drained < 15 and self._click_confirm(quiet=True):
    drained += 1; self._stop.wait(0.2)

# ② 确认按钮找不到时，绝对不能再点主按钮 —— 转入只等确认，超时自动停机
if not c_ok:
    self._log("未找到确认按钮 — 停止点主按钮，转为只等确认 (最多30秒)")
    ...

# ③ 只有确认成功才算一轮，失败不累加轮数（旧版失败也 +1，掩盖了问题）
```

**诊断要能一眼看出堆叠**：加一段「弹窗按钮清单」，递归列出所有 `ymPrompt_btn_*` 的 `id / value / visible / 所在 frame 路径`。用户截这一段回来就能定死位置。**多个选择器命中同一元素时计数要按 `(frame路径, id)` 去重**，否则一个弹窗会被数成 2 个。

**验证手法（不依赖 Windows）**：用 lxml + 假 driver 桩在本地跑逻辑单测——`FakeDriver.find_elements`
用 `cssselect`/xpath 在假文档树上查、`switch_to.frame` 记录索引路径，就能验证「递归到 frame[1][0]」
「`dlg_btn_9` 点中、`dlg_btn_10`(取消) 跳过」「多选择器去重」「点击前切回元素所在 frame」。
比在行内电脑上反复打包试错快两个数量级。**可直接复制的骨架：`templates/stub_driver_test.py`**
（把 `execute_script` 里加一条"元素不属于当前 frame 就抛 NoSuchElement"，就能复现真实的跨 frame 报错）。

## 弹窗关闭后的 DOM 残留

弹窗关掉后确认按钮仍在 DOM 中（`visible=False`），必须检查 `is_displayed()` 再点，否则会一直点空气：

```python
for by, val in selectors:
    try:
        el = driver.find_element(by, val)
        if not el.is_displayed():  # 关键！
            continue
        driver.execute_script("arguments[0].click();", el)
        return True
    except NoSuchElementException:
        continue
```

| 方式 | 适用场景 | 连接方法 |
|------|---------|---------|
| **EdgeService 直接启动**（内网/离线首选） | 银行、政务等安全策略严格的内网电脑 | `webdriver.Edge(service=EdgeService(executable_path=dp))` |
| 远程调试端口 | 普通联网机器，需要复用已有登录态 | `--remote-debugging-port=9222` + `debuggerAddress` |

## 两种连接模式对比（旧）

| 方式 | 适用场景 | 连接方法 |
|------|---------|---------|
| **直接 EdgeDriver 启动**（内网/离线首选） | 银行、政务等安全策略严格的内网电脑 | `webdriver.Edge(service=EdgeService(...))` 让 EdgeDriver 自己启动 Edge |
| 远程调试端口 | 普通联网机器，需要复用已有登录态 | `--remote-debugging-port=9222` + `debuggerAddress` |

**重要教训：两种方式都可能在内网遇到问题，取决于具体机器的安全策略。不要假设哪种"更好"——用户已有能跑的代码用哪种就保持哪种。** 原版 `send_approval_v2.py` 用远程调试端口方式在用户行内电脑上能跑，就不要改成 EdgeService 直接启动。反之亦然。

### 直接 EdgeDriver 方式（内网首选）

```python
dp = _get_driver_path()  # 打包内置的 msedgedriver.exe
service = EdgeService(executable_path=dp) if dp else EdgeService()
driver = webdriver.Edge(service=service)
# Edge 自动打开，用户在里面登录操作。不需要手动 PowerShell 命令。
```

**关键：必须传 `service=EdgeService()`，否则 Selenium Manager 搜 PATH 上的驱动，找不到就报 "Unable to obtain driver"**。

### 远程调试端口方式（仅当直接方式也失败时尝试）

```python
import subprocess, tempfile, time, os

PORT = 9222
CREATE_NO_WINDOW = 0x08000000

# 1. 必须杀全部 Edge 进程（不是只杀带端口号的！）
subprocess.run(
    'powershell -Command "Get-Process msedge -ErrorAction SilentlyContinue | Stop-Process -Force"',
    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    creationflags=CREATE_NO_WINDOW)
time.sleep(2)

# 2. 用独立用户目录启动——不加这个新窗口会合并到旧进程中
temp_dir = os.path.join(tempfile.gettempdir(), "myapp_edge")
subprocess.Popen(
    [edge, f"--remote-debugging-port={PORT}",
     f"--user-data-dir={temp_dir}", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    creationflags=CREATE_NO_WINDOW)
```

## Socket 端口诊断

Selenium 连不上时，先用原始 socket 检查端口是否真的开了：

```python
import socket

for _ in range(8):
    time.sleep(1.5)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", PORT))
        s.close()
        print(f"Port {PORT} is open!")
        break
    except:
        continue
else:
    print(f"ERROR: Port {PORT} never opened!")
```

端口不开的常见原因：Edge 已在后台运行被合并、防火墙/安全软件拦截、Edge 版本与 EdgeDriver 不匹配。

## CONNECT → START → STOP 用户操作流程

对于需要用户在浏览器中先登录再自动操作的场景：

```
1. 点 CONNECT → 工具打开 Edge（EdgeDriver 自动启动）
2. 在 Edge 里手动登录、导航到目标页面
3. 点 START → 开始自动操作
4. 点 STOP → 停止操作（浏览器不关，可重新 START）
```

**不要设计成"工具帮你导航到目标页面"**——很多内部系统是单页应用，URL 不变，工具无法判断用户到了哪个页面。把导航的控制权交给用户。

### GUI 按钮状态机

```python
# CONNECT → 浏览器活着就用旧的不开新的
def _launch(self):
    if self.driver:
        try:
            self.driver.current_url  # 测试连接
            self._log("Reusing existing browser.")
            self.lbtn.config(state=tk.DISABLED)
            self.sbtn.config(state=tk.NORMAL)
            return
        except:
            self.driver = None
    # 开新的...

# STOP → 不关浏览器，START 恢复可用
def _halt(self):
    self._stop.set()
    self.tbtn.config(state=tk.DISABLED)
    self.sbtn.config(state=tk.NORMAL)  # START 恢复
    self.st.set("Stopped — click START to resume")
    # 不调 driver.quit()！
```

**按钮一多，状态就漏（本次「忙碌期」按钮永远是灰的）**。工具里只要超过 3 个 action 按钮，就按这张表维护，
增删按钮时三行一起改：

| 时机 | 该启用 | 该禁用 |
|---|---|---|
| `_post_connect()` 连上浏览器 | 开始×2、诊断、所有探针 | 启动浏览器、停止 |
| `_start()` 连点开跑 | 停止 | 开始×2、诊断、所有探针（防止两个线程同时操作同一页面）|
| `_halt_ui()` 停止 | 启动、开始×2、诊断、所有探针 | 停止 |

```python
# _post_connect()
for b in (self.sbtn, self.zbtn, self.dbtn, self.pbtn, self.hbtn, self.bbtn):
    b.config(state=tk.NORMAL)

# _start()
for b in (self.pbtn, self.hbtn, self.bbtn, self.dbtn):
    b.config(state=tk.DISABLED)      # 连点中禁止开探针

# 探针入口也要守卫，光禁用按钮不够（用户可能用快捷键/旧引用触发）
def _probe_busy_guard(self, name):
    if not self.driver:
        self._log("先点「启动浏览器」"); return False
    if self._worker_thread is not None and self._worker_thread.is_alive():
        self._log(f"正在连点中，先点「停止」再用「{name}」"); return False
    return True
```

**静态自检**：`scripts/check_tk_buttons_enabled.py <你的.py>` —— 扫出「创建了但从不启用」的按钮并返回
非零退出码，可挂进本地测试。本次就是漏了 `_post_connect()` 里一行，编译通过、其他按钮正常，用户才发现。

## 来回点击模式 (A↔B)

当需要交替点击两个不同元素（A→B→A→B...），计数器用"轮次"（一轮 = A+B 各点一次）：

```python
toggle = True
rounds = 0
while not self._stop.is_set():
    if toggle:
        click_element_A()
        toggle = False
    else:
        click_element_B()
        rounds += 1
        toggle = True
    self._stop.wait(interval)
```

支持 CSS 选择器和 XPath。先试 CSS，fallback 到 XPath。用 `execute_script("arguments[0].click();", el)` 绕过可见性检查。

## 三步循环模式 (A→B→C：网页按钮 → 浏览器原生弹窗 → 网页DOM弹窗)

银行/政务内网常见流程：点击网页按钮 A 后，弹出**浏览器原生 alert/confirm**（不是 DOM 元素！），需用 `switch_to.alert.accept()` 点确定；确认后又弹出**网页 DOM 弹窗**（`<input>` 按钮），需用 `find_element` + JS click。

**关键区别**：浏览器原生弹窗（alert/confirm/prompt）不是 DOM 元素，`find_element` 找不到，必须用 `driver.switch_to.alert` API。用户说"浏览器信息"="浏览器原生弹窗"。

### ⚠️ 三步循环的上下文管理（最易出错）

银行系统按钮常在 iframe 内。每步必须显式管理上下文：

```
步骤A: switch_to.default_content() → 遍历 iframe 找A → 点击 → 留在 iframe 内
步骤B: 直接 switch_to.alert 检测/accept —— 不要先 default_content()！
步骤C: switch_to.default_content() → 遍历 iframe 找C → 点击
```

**关键教训（2026-11-04 二次修正 —— 推翻本 skill 之前那句「alert 检测/accept 不受当前 frame 影响」）**：

- **仍然成立**：alert 挂着时任何普通 WebDriver 命令都会抛 `UnexpectedAlertPresentException`，**`switch_to.default_content()` 自己也是一条命令**，所以 B 步骤要**先** `switch_to.alert`，别先切上下文。反过来：任何命令抛 `UnexpectedAlertPresentException` = 弹窗正挂着。
- **错的那半句**：`switch_to.alert` **只在「触发弹窗的那个 frame 的上下文」里看得见它**。iframe 里点的按钮，alert 就属于那个 iframe；上下文一旦被切到 `default_content`/别的 frame，`switch_to.alert` 会**一直**抛 `NoAlertPresentException`——弹窗就在屏幕上，代码却认为没有。
- **日志长相**（认准这个形态）：`✓ [A] 已点击` → 6 秒无声 → `A 点了但没弹出任何窗口` → 重试一枪（重新切回 frame）→ 弹窗"立刻"出现。**看着像"点击被吞/页面有提交锁"，真相是我自己把眼睛挪开了。** 本次为此白改了两版（重试间隔 6s→0.8s→0.2s），最后靠"狂点实验"（首点 350ms 就弹、重复 0）才钉死。

正确写法：**每次判断/关闭 alert 前，先切回触发它的那个 frame**（把主按钮的 frame 路径缓存下来）：

```python
def _alert_here(self):
    try:
        return self.driver.switch_to.alert
    except NoAlertPresentException:
        return None
    except Exception:                      # UnexpectedAlertPresentException 也算"有"
        try: return self.driver.switch_to.alert
        except Exception: return None

def _alert_go_a_frame(self):
    """alert 属于触发它的 frame；上下文被切走就永远看不见"""
    p = getattr(self, "_a_path", None)     # 点主按钮时缓存下来的 frame 路径
    if p is None: return False
    try: self._goto_path(p); return True
    except Exception: return False

def _alert_present(self):
    if self._alert_here() is not None: return True
    if self._alert_go_a_frame():
        return self._alert_here() is not None
    return False

def _accept_alert_once(self):
    a = self._alert_here()
    if a is None:
        self._alert_go_a_frame(); a = self._alert_here()
    if a is None: return False
    a.accept()                             # 失败再 dismiss 兜底
    return True
```

`_wait_no_alert`、诊断、探针里凡是"看有没有弹窗"的地方，全都要走 `_alert_present()`，不要直接 `driver.switch_to.alert`。

**附带性能坑**：`_find` 遍历 frame 树会重扫 4–5 个 frame × 每条选择器，一次点击 **300–400ms**。狂点报告里 `点击时间点(ms)=[378]` 那 378ms 就是它，不是页面延迟。把上次命中过的 frame 路径缓存起来当**首选**：

```python
def _find_in(self, path, selectors, skip_cancel=False):
    """只在指定 frame 路径里找"""
    try:
        self._goto_path(path)
    except Exception:
        return None, None
    for by, val in selectors:
        ...
    return None, None

def _find(self, selectors, skip_cancel=False, prefer=None):
    """先试缓存路径（命中就不扫树），未命中才扫全树兜底"""
    if prefer is not None:
        el, path = self._find_in(prefer, selectors, skip_cancel)
        if el is not None:
            return el, path
    for path in self._frame_paths():
        if path == prefer:
            continue
        el, p2 = self._find_in(path, selectors, skip_cancel)
        if el is not None:
            return el, p2
    return None, None
# 调用侧：self._find(sel, prefer=getattr(self, cache_key, None) if cache_key else None)
```

⚠ **别写成「先拼出一个 `[prefer] + 全部路径` 的列表再逐个试」**——那样 `_frame_paths()` 会被提前调用，
命中缓存也照样扫一遍整棵树，缓存等于白做（本次就是这样把审计测试直接跑红的）。必须**懒扫**：
prefer 命中就 return，根本不构造全树列表。

命中后 `setattr(self, cache_key, path)`（`_a_path` / `_c_path`），小间隔下这是主要开销。

```python
# 步骤A: 在 iframe 里找并点击网页按钮
driver.switch_to.default_content()
iframes = driver.find_elements(By.TAG_NAME, "iframe")
for i, f in enumerate(iframes):
    driver.switch_to.default_content()
    driver.switch_to.frame(f)
    try:
        el = driver.find_element(By.ID, "btn_send")
        if el.is_displayed():
            driver.execute_script("arguments[0].click();", el)
            break
    except NoSuchElementException:
        pass

# 步骤B: 直接检测 alert —— 不要先 default_content()！
# alert 挂着时 default_content() 本身就会抛 UnexpectedAlertPresentException
# 且 alert 只属于它的触发 frame：上下文不在那个 frame 里就永远看不见 →
# 一律用 _alert_present()（内部会切回 _a_path 再判断），别裸写 switch_to.alert
for attempt in range(10):
    self._log(f"  B: 尝试 {attempt+1}/10 检测弹窗...")  # 每次都打日志
    try:
        alert = driver.switch_to.alert
        self._log(f"  B: 弹窗存在 | text={alert.text[:50]}")
        alert.accept()
        break
    except NoAlertPresentException:
        self._log(f"  B: 无弹窗")
        time.sleep(0.5)

# 步骤C: 回到 DOM 世界，在主文档+所有 iframe 里找 C 按钮
driver.switch_to.default_content()
# 先主文档找，再逐个 iframe 找...
```

**alert 检测每次都要打日志**：`switch_to.alert` 在无弹窗时可能阻塞数秒不返回，不像 `find_element` 立即抛异常。如果不在每次尝试前后都打日志，用户看到的就是"B步骤卡死"——实际是在等 alert 超时。

### 窗口管理（启动后导航导致原窗口失效）

工具启动 Edge 打开 `about:blank`，用户手动导航到业务页面后，**原窗口句柄可能失效**（`NoSuchWindowException: target window already closed`）。Selenium 仍指向已关闭的 about:blank 窗口。

**修复**：每轮循环开始前调 `_ensure_window()` 扫描所有窗口句柄，切到非 about:blank 的那个：

```python
def _ensure_window(self):
    """切到活着的、非 about:blank 的窗口"""
    for h in self.driver.window_handles:
        try:
            self.driver.switch_to.window(h)
            if "about:blank" not in self.driver.current_url:
                return True
        except:
            continue
    return False
```

**症状**：第一次点"开始"就报 `NoSuchWindowException`，所有选择器全报 `target window already closed`。诊断模式下 URL/标题正常（因为用户已导航），但运行模式连不上——因为 Selenium 还指向旧窗口。

**浏览器原生弹窗的多种处理方法（遍历兜底）**：
1. `alert.accept()` — 点确定（首选）
2. `alert.send_keys(Keys.ENTER)` — 发送回车
3. `alert.dismiss()` — 点取消（兜底，注意语义不同）

模板见：`templates/send_fenhang.py`（三步循环 + 诊断模式）

**真实诊断案例**：见 `references/bank-mmta-iframe-diagnostic.md`（某银行 MMTA 系统的 iframe 布局、按钮定位、弹窗检测实录）。

## 点击乱报失败 / 间隔调快就点空（2026-11-04 终局定位）

功能已经能连做 15 轮，但日志每轮一行 `⚠ 点击失败: NoSuchElementException`，且用户把间隔拖到
0.6s 以下必翻车。**两个问题同源：页面状态在「扫描 → 定位 → 点击」之间变了。**

四条硬规则（详细代码、验证桩见 `references/click-timing-and-frame-context.md`）：

1. `_find` 只返回**可见**元素，并返回 **frame 路径**；点击前 `_goto_path(path)` 切回该 frame。
2. 点击遇 `StaleElementReferenceException` / `NoSuchElementException` → 重找一次再点，别直接报失败。
3. 等待改**事件驱动**（弹窗出现立刻继续）；主按钮点完无任何窗口先重试 3 次（6s/2.5s/2.5s），仍无才是「没有待处理的了」。
4. 「变灰 = 发完」必须先见过一次 enabled，否则天生灰的按钮会让工具立刻误停。
5. **两轮之间等「遮罩消失」，不是等固定秒数**——见下节。`MIN_GAP` 只留 0.1 当兜底，滑块 `from_=0.1`。

诊断输出里如果出现 `visible=False` 的弹窗按钮，那就是根因 1 的现场证据——不要忽略它去查别处。

## 间隔还能不能更小？先测，别调参（2026-11-04 收尾）

用户问「能不能压到 0.1 / 到底哪儿的问题」时，正确反应是**加一个测速按钮把每段耗时量出来**，
而不是把 `MIN_GAP` 从 0.5 试到 0.4 再试 0.3。

真正的门是**「确认按钮到底点掉了没有」**，不是秒数，也不是 JS 眼里的遮罩：

```python
# 点完确定后：用 Selenium 的 is_displayed 判「按钮还在不在」，还在就补点
gone, waited, extra = self._dialog_gone_wait(1.5, reclick=True)
```

```python
def _dialog_gone_wait(self, timeout=1.5, reclick=False):
    t0 = time.time(); clicks = 0
    while time.time() - t0 < timeout and not self._stop.is_set():
        el, _ = self._find(BTN_CONFIRM, skip_cancel=True)   # _find 只返回可见元素
        if el is None:
            return True, time.time() - t0, clicks
        if reclick and clicks < 3:                          # 还看得见 = 上一刀被吞了
            self._click_confirm("补点", quiet=True); clicks += 1
        self._stop.wait(0.1)
    return False, time.time() - t0, clicks
```

- **绝对不要用 JS 数 `[id^='ymPrompt']` 节点判「弹窗关没关」**。① 关闭后节点仍留在 DOM；
  ② 祖先 `display:none` 时元素自身 `getComputedStyle().display` 仍是 `inline-block`
  （必须 `getClientRects().length` 才判得准）。两条合起来 → 门控恒定认为"还没关"。
- **但更根本的错不是判据，是把「下游信号」当成了「动作成功」的证明**。本次真因是确定按钮
  压根没被点掉——用户看着屏幕说「确定按钮一直在，所以你一直没有把它点掉」，遮罩当然永远
  不消失 → 每轮白等 1–3s。**日志只能证明"我点了"，不能证明"点成功了"。**
- **测量值 ≈ 超时值 = 先怀疑动作没生效**（其次才是探针判据写错）。报告里一片
  `3020ms / 3026ms / 3038ms` 全是 3s 超时值；那一版还据此把 0.1s 判成"物理不可能"，
  而实际 0.1s 能跑，失败样本全是**上一轮遗留弹窗**挡住的。
- 主循环里**不要放 JS 门控**（只会新增失败模式）。开工靠「排干可见确认按钮」+ 轮末
  `_dialog_gone_wait` 校验；探针报告必须记「补点次数 / 按钮是否消失」——这是唯一能区分
  "页面慢"和"没点掉"的字段。
- **间隔压得掉空档，压不掉页面固有延迟**。~~实测一轮 = 主按钮→alert 340ms +
  accept→确定可点 540ms ≈ 0.9s~~ **这组 340/540ms 后来被证伪：其中大半是我自己扫 frame 树的开销。**
  换成 JS 查弹窗 + 缓存路径后，真实值是 **主按钮→alert ≈50ms、accept→确定可点 ≈166ms，一轮 ≈250ms**。
  教训：**凡是在"点击/查找很慢"的版本上量出来的页面延迟，都要在优化后重新量一遍**，否则会把
  自己的开销当物理极限，还据此否掉用户要的参数（本次就误判过"0.1s 物理不可能"）。
  吞吐按 `1/(页面延迟+gap)` 估：先量准两个数，再谈能跑多快，别承诺倍数。
- 顺手把主按钮所在 frame 路径缓存进 `_a_path`（`_click(..., cache_key="_a_path")`），
  每轮重扫 4 个 frame 的 100–300ms 在小间隔下就是主要浪费。
- 没配容器选择器的页面自动退化：`_wait_overlay_gone` 直接放行，行为等同旧版。

**测速探针**（`PROBE_GAPS=[0.1,0.2,0.3,0.5]` × 每档 5 轮）：记录「点击时可见遮罩层数 v /
主按钮→弹窗 / 弹窗→确定可点 / 点确定→遮罩消失」，结论写成「遮罩消失最慢 Xms = 物理下限」。
`v>0` 的失败 = 确诊点空；`v==0` 还失败 = 有第二道锁（工具栏 disabled）。
报告写 **exe 同目录 `测速报告.txt`，`encoding="utf-8-sig"`**（Windows 记事本才不乱码），
用户跑一次发文件，比在界面里复制中文靠谱。完整探针代码、扫描骨架、判读表、坑见
`references/timing-probe.md`；**发到行内电脑之前**先用
`templates/overlay_probe_fixture.html` 在本地验证探针本身（关闭态必须 `v=0`）。
验证手法：本地起个页面（含一个祖先 `display:none`、内含 `input#ymPrompt_btn_0` 的容器），
用浏览器打开后把探针 JS 包成 `(function(){ ...原样... })("[id^='ymPrompt']")` 在 console 里跑：
**关闭态必须 `v=0`，弹开态应返回 `id:宽x高`**。这一步能在 1 分钟内否掉「探针判据写错」，
不用等用户打完包、在行内机上跑一轮再把报告发回来。本次就是靠它把
「`getComputedStyle` 判不出祖先隐藏」钉死的。

先测再改的好处：改动有据（门控 + 缓存），而不是把 0.5 悄悄换成 0.35 再赌一次。
另外测速会**真的提交单据**，按钮说明里要写一句「先拿一笔测试单跑」。

## 稳态速度审计：让每轮只剩「interval + 几十毫秒」（2026-11-04 终局）

用户第二次说「**还是会有轮间间隔，请你彻查代码，不要再出现这种问题**」时，说明调参已经到头了，
必须做**命令级体检**。真相是：所有「查一下有没有弹窗」都在调 `find_elements`，一次未命中
= 5 选择器 × 7 条 frame 路径 ≈ 35 条 WebDriver 命令 ≈ 0.5–1.5 秒；一轮里有 3 次这种未命中
（轮首清残留、点确定、确认框消失校验），于是每轮凭空多出 1–4 秒。

四条改法（按收益排序）：

1. **JS 一条命令查/点**：在缓存的 frame 里 `document.querySelectorAll(...)` + `.click()`。
   查 20ms、点 20ms，替代几十条 `find_elements`。
2. **缓存三样上下文**：主按钮/确认按钮的 frame 路径（`_a_path`/`_c_path`）、当前 frame 上下文
   （`_ctx_now`，`_goto_path` 里 early-return）、窗口句柄（`_win`）。省掉每轮 2 次 `switch_to.window`
   和每次查找前的 `default_content()` + 逐层 `frame()`。
   ⚠ **`_js()` 抛异常时必须把 `_ctx_now` 置 None**：JS 跑挂最常见的原因是 frame 正在重载
   （日志里的 `?` 行就是这么来的），此时缓存已失效，不清掉会让后续所有 JS 都在旧上下文里打转。
   同理，`switch_to.window()` 之后也要清——换窗口等于换 frame 上下文。
3. **interval 补差额**：从点确定起算，别在轮末再 `sleep(interval)` 全量加一遍。
4. **轮询粒度 50ms**，确认框判据查得比 alert 稀（每 150ms 一次），省一半命令。

**验收标准（本地假 driver 就能量，不用等行内机）**：

```
轮间间隔(点确定→下次点A) ms: [132, 134, 134]     ← interval 设 0.1
第2/3轮 WebDriver 命令数: [22, 22]                ← 改前 37+
```

并加一条**反退化断言**：第 1 轮之后把 `_frame_paths` 换成 `raise AssertionError("稳态下还在扫 frame 树")`，
测试仍要跑通。这样以后谁再往热循环里加一次全树扫描，单测立刻红。
完整代码（JS 快路径、上下文缓存、带命令计数的假 driver、间隔测量）见
`references/steady-state-speed-audit.md`。

> ⚠ 这一节有个真机陷阱：**JS 快路径只对弹窗「确定」有效，工具栏按钮用 `el.click()` 会静默失效**
> （日志特征：`已点击 (frame[1])` 后面没有 `id=`，且第 1 轮成功、之后每轮"点了没反应"）。
> 另外 `_find` 的 prefer 必须**懒扫**，否则缓存白做。两者都在
> `references/js-click-scope-and-lazy-find.md`（含日志判读表、审计测试骨架）。

## 把测量做进日志：毫秒时间戳 + 程序自己算指标（2026-11-04 用户拍板）

用户原话：「**这两行的秒差 = 轮间间隔，你就不能直接计算这个间隔吗？没到一秒怎么办？**」
——工具的性能问题不该让用户拿秒级时间戳去减。三件事一起做：

```python
# ① 时间戳带毫秒（否则几百毫秒的间隔两条记录在同一秒，人眼算不出来）
ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

# ② 在"动作"里打点，不在"检测到结果"里打点
def _click_a(self, tag="A", quiet=False):
    r = self._js(path, JS_CLICK_A)
    if r == "clicked":
        self._t_a_click = time.time()      # ← 真正点下去的时刻
        return True

# ③ 每轮直接打印，停止时给汇总
self._gaps.append((t_a_click - self._t_c_prev) * 1000)
self._log(f"  · 轮间间隔 {gap_ms:.0f}ms (上次点确定 → 本次点A)")
self._log(f"═══ 第 {n} 轮完成 ═══ (本轮 {round_ms:.0f}ms)")
self._log(f"── 轮间间隔: 平均 {avg:.0f}ms, 最大 {mx:.0f}ms (共 {len(self._gaps)} 次)")
self._log(f"   期望值 ≈ 你设的间隔({interval*1000:.0f}ms) + 200ms 以内; 明显更大请发我")
```

界面计数栏也带 `轮间均 XXXms`，用户抬头就能看，不用翻日志。

判据（直接写进日志，用户能自评）：

| `轮间间隔` | 结论 |
|---|---|
| 100–350ms | 正常 = interval + 命令开销 |
| 350–800ms | 偏高（命令慢/淡出慢），可接受 |
| >1000ms | 不对，要日志定位 |
| 一片 ≈ 超时值 | 等的东西根本没成立（假测量，见 pitfall 37）|

配套坑：`t_a_ok` 若记在 `_wait_effect()` 返回之后，会把页面延迟+轮询粒度算进间隔
（本次 366ms vs 真实 134ms）；统计字段还要在 **worker 开头**重置，别只放 `__init__`
（`object.__new__` 桩测试不走 `__init__`，会当场 `AttributeError`）。

## 「看不见弹窗了」≠ 没弹：给一个慢速演示开关（2026-11-04 用户提问）

提速成功后用户新的疑问变成：**「为什么现在我视觉上看不到第三个确定了，是你动作太快了吗？」**
——对，也不是 bug。日志能自证：

```
[15:37:49.854] ━━━ C: 弹窗「确定」━━━
[15:37:50.020]   ✓ [C] 已点确定 (frame[1]) id=ymPrompt_btn_0     ← 找到了、点掉了
[15:37:50.058] ═══ 第 1 轮完成 ═══ (本轮 256ms)
```

网页确认框从出现到被点掉只有 **166ms**，人眼跟不上；以前每步 sleep 0.5s 所以看得见。
回答要点：① 用日志行证明"找到并点掉了"；② 补充一句"若没点掉，下轮会报 `清掉 N 个残留弹窗` 或 `⚠`"。

**但别只解释——给开关**。用户要的是"能自己确认一遍"：

```python
self.slow = tk.BooleanVar(value=False)
ttk.Checkbutton(sf, text="慢速演示：每个「确定」弹出后停 0.6s 再点（只看效果用，会变慢）",
                variable=self.slow).grid(...)

# worker 里，accept 原生弹窗之后、点确定之前
if getattr(self, "slow", None) is not None and self.slow.get():
    self._stop.wait(0.6)      # 让你看清第三个「确定」再点掉
```

验证时勾上，正式跑取消。**「界面上看不见」这类投诉，标准答复 = 日志证据 + 一个演示开关**，
不要长篇解释动作有多快。

### ⚠ 反转：这个"演示开关"后来被证明是真优化（2026-11-04 收尾，用户先发现）

用户原话：**「开了慢速演示这个按钮以后，变得更流畅了，而且轮间隔也变小了，非常奇怪。」**
—— 不是错觉。0.6s 停顿落在「accept 原生弹窗」和「点网页确定」之间，而**点确定才是真正提交**：
弹窗刚关就点确定，提交被页面拖着走，紧随的 iframe 重载也晚开始，下一枪就点空 → 重试 3~4 次
→ 每轮多花 2~3 秒。停 0.6s 再点，提交干净、重载更早完成，下一枪一次命中。
**多花 0.6s，省掉 2~3s。**

所以要把它从演示开关里**拆出来做成默认**：

```python
SUBMIT_SETTLE = 0.6          # 关掉原生弹窗后停这么久再点确定(立刻点会让页面卡一下)

self._stop.wait(SUBMIT_SETTLE)     # 永远生效
if self.slow.get():
    self._stop.wait(0.4)           # 演示开关只负责"看得清"
```

**通用判断：任何一个"为了让用户看清"而加的停顿，都要回头问它是不是在补页面节奏。**
用户说"开了反而更顺/轮间隔更小" = 它是功能性参数，必须转正为默认常量（并在日志里说明），
别再当成"演示用、会变慢"。详见 `references/settle-delay-and-probe-removal.md`。

## 改了旋钮含义就必须改标签（用户当场质问过）

本次把「每步间隔」悄悄改成「轮间最小间隔」（步骤间不再 sleep，只在两轮之间补差额），
标签没跟着改，用户直接质问：**「什么叫我设的间隔？我设的不是点击间隔吗？我什么时候设置过轮间间隔？」**

规则：

1. 旋钮语义一变，**UI 标签、`LabelFrame` 说明、启动日志、收尾汇总**四处一起改，措辞写清
   "从 A 到 B 的最小时间"，别只写"间隔"。
2. 启动时打一行解释，例如
   `间隔 0.1s = 上一轮点确定到下一轮点A 的最小时间; 步骤之间不等, 弹窗一出现就继续`。
3. 如果用户其实想要"每步也停一下"，**另开一个独立开关**，不要把一个旋钮赋予两种含义。



本次为此改了 5 版，正确顺序是这样：

1. **动作到底生效没有**（加一次"元素是否消失"的校验，别只看"我点了"）——用户说"屏幕上的按钮一直在"就是这一条，
   优先级最高，见 pitfall 31。
2. **原生 alert 的 frame 作用域**（每轮第一枪必空、重点必成 = 这个，见 `references/frame-scoped-alert.md`）。
3. **命令数**（数每轮 `find_elements` 未命中，>25 条就是扫树问题，见上文审计节）。
4. **轮询/等待的粒度与叠加**（interval 补差额、50ms 粒度、别在轮末再全量 sleep）。
5. **页面固有延迟**（最后才认，而且要先用探针把"点击耗时"和"点后延迟"分开量，别混算成物理极限）。
6. **重试窗口是否小于页面延迟**（会重复提交，属安全性问题而非速度问题）。

**用户对某条机制的说法与你冲突时，用实验裁决，别用推理坚持**：本次连着两次被用户
（「确定按钮一直在」/「应该没有锁定窗口，你可以疯狂点」）纠正，两次他都是对的。

## 每轮之间「格很久」：页面提交锁 vs 我的长超时（2026-11-04 终局）

> **⚠ 结论修正（同一 session 更晚一步）：这一节当初判的"提交锁"其实不存在。**
> 后续的狂点实验显示**首点 350ms 就弹窗、重复 0 个、每次都是第 1 次点击生效**——
> 也就是说根本没有锁，「一枪必空、重点必成」的真因是**原生 alert 只属于它的触发 frame，
> 而我的等待循环先把上下文切去了 default_content，于是永远看不到那个弹窗**，
> 傻等 6s 超时后重试那一枪重新切回 frame，弹窗才"出现"。见上文
> 「三步循环的上下文管理」与 `references/frame-scoped-alert.md`。
>
> **这一节仍然保留，因为下面的重试骨架本身是对的、该留**：把"点一次就死等 N 秒"换成
> "短超时 + 重点 + 静音 + 进度行"是纯粹的健壮性改进，无论有没有锁都受益。
> 但如果日志里出现"每轮第一枪必空、重点必成"，**先查 alert 的 frame 作用域，再谈锁**——
> 顺序反了就要多改两版。
>
> **⚠ 第二次修正（同一 session 最后一步，真机 40 轮）**：修好 frame 作用域之后，"锁"**又回来了**，
> 而且这次有 40 轮数据：第 1 轮 `A→弹窗 0.03s`，第 2–40 轮 `2.1–3.6s`、每轮要点 3–4 次才弹。
> 也就是说**提交后确实有 2–3 秒不可交互窗口**；狂点实验之所以量不到，是它每个 trial 前都有
> `_dialog_gone_wait + 0.3s`，等它开点时页面已经稳定了（见 pitfall 47）。
>
> 归因口诀：
> - **一次点击就弹，只是我看不见** → alert 的 frame 作用域（`_alert_present` 要切回 `_a_path`）；
> - **点了 2–3 秒才弹、期间点几次都没反应** → 页面提交后的忙碌期，第一次等待给到 4s，别 1s 一枪硬刷。
>
> 实测吞吐：40 笔 / 2 分 40 秒 ≈ **16 笔/分钟**，每轮 3.3s 是这台页面的下限（页面 3.0s + 动作 0.3s）。
>
> **这个窗口后来查明是什么了（同一 session 最后一步，忙碌期探针）**：不是锁、不是 `disabled`，
> 而是**提交后 iframe 重载一次**——探针 100ms 采样看到 `dis=0` 从头到尾没变、`mask=1` 且同一行
> `dis=-1/vis=-1`（元素查不到），`?` 行（JS 执行失败）是重载的另一个指纹。
> 所以正确的门控信号是「**遮罩出现 → 消失**」= 重载完成 = 真正可以再点的瞬间：
>
> ```python
> res = self._wait_effect_or_reload(self._a_path, A_FIRST_WAIT)   # 'alert'/'dialog'/'reloaded'/None
> if res == "reloaded":
>     self._log("· 页面重载完成 → 立刻重点")   # 别等满窗口，重载一结束就再点
>     continue
> ```
>
> 归因三层，别混：**一眼就有弹窗但看不见** = alert 的 frame 作用域；
> **点了 2–3s 才弹、期间点几次都没反应** = 提交后的重载窗口；
> **`disabled` 从没变过** = 根本没有禁用信号，别去等它。
> 完整报告判读表、`_wait_effect_or_reload` 三态代码、单元测试、
> 忙碌期探针 JS 见 `references/post-submit-reload-signal.md`
> （`post-submit-busy-window.md` 是它的上一版，结论已被这一篇升级）。

用户原话：「每轮之间会格很久」。日志形态是**一枪必空、重点必成**：

```
[14:39:13] ═══ 第 1 轮完成 ═══
[14:39:14]   ✓ [A] 已点击              ← 点了
[14:39:21]   · A 点了但没弹出任何窗口 (第 1 次), 稍等重试   ← 空 7 秒（我睡的）
[14:39:22]   ✓ [A重试1] 已点击          ← 再点立刻生效
```

读法：第 1 轮是整个流程的第一枪（没有前一笔提交）→ 立刻成功；之后每轮第一枪都空、重点都成
→ **页面在上一笔提交后有一段"锁"**，锁着时点击被**静默丢弃**（不报错、不弹窗）。那 6–7 秒是
`_wait_effect(6.0)` 在睡觉。**间隔调多少都没用，因为它不是间隔问题。**

```python
A_RETRY_TIMEOUT = 0.8   # 正常 340ms 就弹；0.8s 还没动静 = 这枪被吞了，立刻重点
A_MAX_WAIT = 12.0       # 一轮最多试这么久；超了才算"确实没有待办"

while time.time() - t_a0 < A_MAX_WAIT and not stop:
    if not self._click(BTN_A, tag, cache_key="_a_path", quiet=(attempts > 0)):
        ...  # 找不到按钮的分支
    attempts += 1
    kind = self._wait_effect(A_RETRY_TIMEOUT)
    if kind:
        if attempts > 1:
            self._log(f"  · 点 A 第 {attempts} 次才生效 — 页面提交后锁了 "
                      f"{time.time()-t_a0:.1f}s (这次等到了)")
        break
    if attempts % 4 == 0:      # 别让界面看着像卡死
        self._log(f"  · 还在等弹窗 (已点 {attempts} 次, {time.time()-t_a0:.1f}s)")
```

三条配套（缺一条就会被用户吐槽"还是慢"或"刷屏"）：

1. **重试必须静音**：`quiet=(attempts > 0)`。0.8s 一次会把 `✓ [A重试N] 已点击` 刷满一屏，
   真异常全被淹掉。成功时汇总一行就够。
2. **每 4 次打一行进度**，否则用户以为死机。
3. **探针要量「点几次才生效 + 累计等待」**，不能只量"点A→弹窗"。只量后者的话锁期会被算进
   "页面延迟"，看起来像物理极限，结论直接反了（本次就因此误判"0.1s 物理不可能"）。

参数与判读：

| 项 | 值 / 判读 |
|---|---|
| `A_RETRY_TIMEOUT` | 0.8s 保守档（页面正常延迟 340ms 的 2 倍余量）；**狂点实验确认「点击不排队」后可压到 0.2s** |
| `A_MAX_WAIT` | 12s；末尾"确认没有待办"会花掉这么多，属正常 |
| 日志「第 N 次才生效，锁了 X.Xs」 | X 就是这台机器的提交锁时长，一般不恒定（本次 0.2–0.6s 波动）|
| 锁长波动 → | **别写死 sleep**，靠重试自适应；别把重试间隔也设成 5s |

效果：同场景 3 轮 2.4s（0.8s/轮），旧逻辑 18s+。**改完先跑一遍带"提交锁"的假页面单测**
（`Page.click_A` 在 `locked_until` 之前直接 return，`click_confirm` 里 `locked_until = now + LOCK`），
断言总耗时 < 轮数×(锁+页面延迟)+末尾等待——完整骨架见 `references/post-submit-lock-retry.md`。

## 狂点实验：别争「有没有锁」，用点击频次把它量出来（2026-11-04 用户拍板）

用户的原话是判断依据：「**我觉得你应该大胆试试，就我观察，应该是没有所谓的锁定窗口的，
你可以做个测试疯狂点**」。当用户在**屏幕上看着**页面、说某个我推断的机制不存在时，
不要再写一段推理去说服他——**做一个有安全阀的实验**。

### 实验设计（三条缺一不可）

1. **固定高频**：每 `HAMMER_INTERVAL=0.1s` 点一次主按钮，**一出现弹窗立刻停手**（绝不连续点到弹窗
   满天飞），单次试验最多 `HAMMER_MAX=8s`。
2. **记录三个数**：第几次点击生效 / 首点后多少毫秒弹出 / 点击时间点数组（`[0, 107, 219]`）。
3. **安全阀**：弹窗 accept 后**等 0.3s** 再数「后面还冒出几个确认框」，`重复 = max(0, 补点次数-1)`。
   重复 >0 = 点击被应用排队了 = **这笔单会被提交多次**。

```python
t0 = time.time(); taps = 0; stamps = []; t_alert = None
while time.time() - t0 < HAMMER_MAX and not stop:
    self._click(BTN_A, "狂点", quiet=True)          # 静音，否则刷屏
    taps += 1; stamps.append((time.time() - t0) * 1000)
    deadline = time.time() + HAMMER_INTERVAL
    while time.time() < deadline:
        if self._alert_present():                    # 只查 alert，最便宜
            t_alert = time.time(); break
        time.sleep(0.01)
    if t_alert: break
```

判读：

| 观察 | 结论 | 下一步 |
|---|---|---|
| 每轮 `首点后 ≈ 350ms`，`重复 0` | 没有锁，首点就该生效 | `A_RETRY_TIMEOUT` 直接压到 **0.2s** |
| `首点后` 随轮次涨到 1s+ | 有提交锁，该数字就是锁长 | 重试间隔取锁长的 1/2 |
| `重复 >0` | **点击会排队 → 重复提交风险** | 重试间隔放大或改成「点一次只等不重点」 |
| 狂点 8s 一次弹窗都没有 | 页面用别的方式拒绝 | 查 A 是否被 `disabled` / 是否弹了自己没识别的提示 |

报告写 exe 同目录 `狂点报告.txt`（`utf-8-sig`），附一句「**先拿一笔测试单跑**」——
这个实验会真的提交单据。

### 配套的两个坑（本次都踩了）

- **accept 之后要等 0.3s 再判断「确认框是否已消失」**：确认框是关了原生弹窗之后才创建的，
  立刻判断会得到「没有 → 已清干净」的**假阴性**，下一次试验就会被上一轮遗留弹窗卡死
  （表现为狂点 28 次一次弹窗都没有）。清理型判断要判**两次**（中间隔 0.3s）。
- **「补点 1 次」不是重复**：`_dialog_gone_wait(reclick=True)` 里的第一下是**本轮本该点的**，
  重复数必须 `max(0, clicks-1)`，否则每个正常试验都会报「有重复提交风险」。

完整实验代码、判读表、假页面桩（含"点击不排队"与"点击排队"两种模型）见
`references/hammer-probe-and-duplicate-risk.md`。

## 工具要进 git 时：脱敏 + 仅本地版本控制

用户说「存到 git 但不要展示任何系统元素」「仅做版本控制」时，**不要建远端**，
把元素定位整体外置成 `config.example.json`（REPLACE_ 占位符，进仓库）+
`config.json`（真值，进 .gitignore）；措辞中性化（分行/总行 → 两步确认/批量提交）；
交付前用 `grep -rniE '<系统关键词>' $(git ls-files)` 自查必须 0 命中，并把命令输出给用户。
完整配方、骨架、自查清单、假 driver 桩、两份副本（U 盘不脱敏 / git 脱敏）与
脱敏版打包（frozen 配置路径、bat 委托 `--build`）见
`references/sanitized-release-and-versioning.md`。

## 批量/总行模式：灰按钮必须能被认出来，否则循环永远停不下来（2026-11-04 收尾）

用户报的是「按钮是灰色的时候还在打日志」。这不是"误停"，是**反方向**的 bug：把灰的当成能点 →
每轮点一下 → 每轮一行 `✓ [发送总行审批] 已点击` → 永不结束。根因是「灰」的判定只看了
`disabled` 属性，而 CTP 一类框架是用 **class** 画的灰。

三态判定的写法（一次查找、认三种灰）：

```python
def _submit_state(self):
    """'enabled' / 'disabled' / 'missing'"""
    el, _p = self._find(DONE_FLAG, prefer=getattr(self, "_a_path", None))
    if el is None:
        return "missing"
    if el.get_attribute("disabled") is not None:
        return "disabled"
    cls = (el.get_attribute("class") or "").lower()
    aria = (el.get_attribute("aria-disabled") or "").lower()
    if "disab" in cls or aria in ("true", "1"):
        return "disabled"          # ← 漏这一条就是本次的真因
    return "enabled"
```

worker 里配三道闸门（缺一道就有无限循环或刷屏）：

| 闸门 | 触发 | 动作 |
|---|---|---|
| 状态闸 | `disabled` 且已见过 `enabled` | `全部发完! 共 N 次点击` → break |
| 状态闸 | `disabled` 且从未见过 `enabled` | `按钮是灰的(不可点) → 这一步不需要` → **0 次点击** break |
| 缺失闸 | `missing` 连续 5 次 | `找不到按钮 → 可能不在该页面` → break |
| 无反馈闸 | 点了 N 次（N=15）都没弹出确认框 | 8 次先警告、15 次停（防「能点但页面不理」） |
| 日志闸 | 重复点击 | `quiet=(self._clicks >= 3)`，前 3 次打 `已发送 N 次`，之后静默 |

要点：

- **闸门要放在"点击之前"**：状态闸先于 `_click_submit()`，否则已经点了才知道是灰的。
- `quiet` 要沿包装链传下去（`_click_by_key(..., quiet=)` → `_click_any(..., quiet=)`）。漏传一层
  就是「日志闸」失效，这次就是这么漏的（见 pitfall 30）。
- **改批量模式时，明确说清哪些函数没动**。用户被"修一个挂一个"坑过，原话：
  「**别修了分行的总行又挂了**」。回复里直接列「本次只改 `_submit_state` / `_worker_zh`，
  分行的 `_wait_effect` / `_dialog_gone_wait` / 点 A 路径一个字符没动」，比"已修复"有用得多。
- 这个模式的回归测试**不用假浏览器**：`object.__new__(App)` + monkeypatch
  `_submit_state` / `_click_submit` / `_click_confirm`，就能验「灰的 0 次点击立刻停」
  「找不到 5 次停」「一直点不弹框 15 次停且日志只 3 行」。详见
  `references/batch-mode-grey-button-guards.md`。

### 主按钮变灰 = 处理完了：停下来 + 响一声 + 弹个框（2026-11-04 收尾）

用户原话：「**如果发送分行审批这个按钮灰色了，我的点击流程能不能停，然后工具给我报个提示，出个声音？**」
——「跑完了」不能只写一行日志，行内机上没人盯着日志框。收尾要让**人**感知到。

六条做法：

1. **复用同一个判定器**：把 `_submit_state()` 拆成通用 `_btn_state(selectors)`，分行主按钮
   `_btn_state(BTN_A)` 也走三态（enabled/disabled/missing）。别为分行再写一套 —— 两套判定必然漂移。
2. **灰要复核一次再停**：`if 灰: wait(0.4); 再判` —— 提交后 iframe 重载的瞬间按钮查不到/读不到状态，
   一次判定就会「点两笔就误报没待办了」。
3. **`missing` 单独计数**（连续 5 次）才停，且提示语换成「请确认浏览器停在待审批页面」——
   和「已变灰」是两回事，别用一句话糊过去。
4. **声音**：`winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)` 响 3 次、每次间隔 0.25s，
   整段 `try/except` 包住（非 Windows / 静音 / 无声卡都不能影响主流程）。
5. **弹框必须在主线程**：worker 线程里直接 `messagebox.showinfo()` 会让 tkinter 崩。
   一律 `root.after(0, lambda: messagebox.showinfo(title, msg))` 切回主线程。
6. 提示内容带上进度（「本次完成 N 笔」），并且**先记录 `rounds` 再 notify**——`_halt_ui()` 会重置状态。

```python
def _notify(self, title, msg):
    try:
        import winsound
        for _ in range(3):
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION); time.sleep(0.25)
    except Exception:
        pass
    try:
        root = getattr(self, "root", None)
        (root.after(0, lambda: messagebox.showinfo(title, msg)) if root
         else messagebox.showinfo(title, msg))
    except Exception:
        pass
```

**覆盖矩阵（两个模式逐行对齐，别只做一个）**：

| 停止原因 | 分行（`_worker_fen`） | 总行（`_worker_zh`） |
|---|---|---|
| 主按钮/总行按钮变灰（已见过可点） | 「本次完成 N 笔」+ 响 3 声 | 「全部发完，共 N 次点击，用时 X 秒」+ 响 3 声 |
| 一开始就是灰（这单不需要走这步） | —（分行不存在此态） | 「按钮是灰的，这一单不需要总行审批」+ 响 3 声 |
| 连续 5 次找不到按钮 | 「请确认停在待审批页面」+ 响 3 声 | 「请确认停在总行审批那一页」+ 响 3 声 |
| 连点 15 次不弹确认框 | 兜底闸 + 响 3 声 | 兜底闸 + 响 3 声 |

每个提示语都要**说清下一步该干什么**（"需要总行审批" vs "页面不对" 是两种事），
不要两种原因共用一句「已停止」。

完整代码（含 `_btn_state` 抽取、worker 插入点、桩测试里 `winsound`/`messagebox` 的假实现）见
`references/batch-mode-grey-button-guards.md` 第 7 节。

## 诊断模式（用户强烈偏好：先诊断再运行）

用户原话："每一步应该遍历所有可能性，打印运行日志，找到正确的可能。不然一遍一遍我都需要打包以后在行内电脑上运行，太复杂了。"

**核心原则**：自动化工具必须内置诊断按钮，只检测不点击，输出所有选择器的命中报告。用户在行内电脑跑一次诊断，把日志截图发回来，就能远程定位问题，避免反复打包试错。

诊断模式需检测：
1. 当前 URL / 标题
2. iframe 数量和每个 iframe 的 src
3. **每个选择器逐个报告**：✓ 命中（含 tag/id/value/text/visible）/ ✗ 未找到 / ⚠ 异常
4. 逐个切进 iframe 里找目标按钮（银行系统按钮常在 iframe 内）
5. 当前是否有浏览器原生弹窗
6. 全局扫描所有 `<input>` 按钮的 id/value/class/visible
7. **报告业务终态按钮的状态**——工具用 disabled 属性判断完成（见"检测成功"），诊断要报同一个按钮的"可点 / 已变灰=发完 / 未找到"，并提示变灰时连点会自动停。这样用户发完几笔跑一次诊断就能确认状态，不用猜。

### 诊断模式必须 alert-safe（2026-09-02 踩坑修正）

**症状**：点击成功后（原生弹窗还挂着）跑诊断，整个诊断崩掉只报一行 `诊断异常: unexpected alert open: {Alert text : ...}`。用户问"点击成功了还能不能做诊断？"——旧版不能。

**根因**：alert 挂着时所有 WebDriver命令（current_url / find_elements / switch_to.*）都会抛 `UnexpectedAlertPresentException`。旧版诊断把弹窗检测排在**最后**，而第一步 `current_url` 就已经炸了——后面的检测全没跑。

**正确结构（已验证）**：
1. **弹窗检测放最前面**，且各区块独立容错——一处被挡只报一条"被弹窗挡住"，其余照常跑完，不再一处崩全崩
2. 弹窗存在时**只报告内容不关闭**（`alert.text` 读取不破坏页面状态，诊断不该替用户做决定）
3. 弹窗内容要完整打印——它本身就是最有价值的诊断信息（如银行系统的风险提示原文）

```python
def _diag_worker(self):
    # 0) 弹窗最先检测
    try:
        alert = self.driver.switch_to.alert
        self._log(f"✓ 浏览器原生弹窗存在 (开始连点会自动处理它):")
        self._log(f"  弹窗内容: {alert.text}")
    except NoAlertPresentException:
        self._log("· 无浏览器原生弹窗")

    # 1) 之后每个检测区块独立容错
    def _safe(label, fn):
        try:
            fn()
        except UnexpectedAlertPresentException:
            self._log(f"⚠ {label}: 被浏览器原生弹窗挡住 (内容见最上方)")
        except Exception as e:
            self._log(f"⚠ {label}: {type(e).__name__}: {str(e)[:100]}")

    _safe("URL/标题",  lambda: self._log(f"URL: {self.driver.current_url}"))
    _safe("iframe检测", self._log_iframes)
    _safe("A按钮检测", lambda: self._find_in_all_contexts("A", A_SELECTORS, click_it=False))
    # ... 每个区块一个 _safe
```

**附带原则**：工具里所有"非运行时"的检测路径（诊断、状态检查、连点前预检）都应套同样的容错结构——它们随时可能在弹窗挂起时被调用。运行 worker 可以顺手 accept 弹窗，但诊断模式绝不能动页面状态。

```python
def _find_with_log(self, label, selectors, click_it=False):
    """遍历所有选择器，日志报告每个命中情况"""
    self._log(f"-- {label}: check {len(selectors)} selectors --")
    found_el = None
    for name, by, val in selectors:
        try:
            el = self.driver.find_element(by, val)
            visible = el.is_displayed()
            detail = f"tag={el.tag_name} id={el.get_attribute('id')} val={el.get_attribute('value')} text={(el.text or '')[:20]}"
            self._log(f"  OK [{name}] hit | visible={visible} | {detail}")
            if found_el is None and visible:
                found_el = el
        except NoSuchElementException:
            self._log(f"  NO [{name}] miss | selector={val}")
        except Exception as e:
            self._log(f"  ERR [{name}] {type(e).__name__}: {e}")
    # ... click logic
```

**运行模式也要全程日志**：正式循环时每步也打印每个选择器的尝试结果，不能闷头跑。用户需要看到哪步通了哪步没通。

## EdgeDriver 捆绑到 PyInstaller exe

内网离线机器无法从微软 CDN 下载 EdgeDriver，必须预打包进 exe。

### 打包时：本地文件优先 + 下载 fallback

```python
def self_build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. 检查本地 msedgedriver.exe
    driver_path = os.path.join(script_dir, "msedgedriver.exe")
    if not os.path.exists(driver_path):
        # 2. 尝试下载（内网可能失败）
        driver_path = _download_edgedriver(version, script_dir)
    
    if not driver_path:
        print("Place msedgedriver.exe next to script and retry")
        sys.exit(1)
    
    # 3. PyInstaller 打包——用 --add-binary 不是 --add-data！
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed", "--name", "AppName",
        "--add-binary", f"{driver_path};.",
        "--collect-all", "selenium",     # 别手写 hidden-import，见上文懒加载坑
        "--hidden-import", "tkinter",
        os.path.abspath(__file__),
    ])
```

**关键：`--add-binary` vs `--add-data`** — `--add-binary "msedgedriver.exe;."` 让 exe 打包进 PyInstaller，运行时提取到 `sys._MEIPASS` 并保留执行权限。`--add-data` 不会给执行权限。

### 运行时：取回打包内置的驱动

```python
def _get_driver_path():
    """优先级：exe/脚本同目录 > 打包内置。
    同目录优先是刻意的——驱动版本不对时用户直接换个文件就行，不用重新打包。"""
    local = os.path.join(APP_DIR, "msedgedriver.exe")     # APP_DIR 见下节，frozen 时=exe 目录
    if os.path.exists(local):
        return local
    if getattr(sys, "frozen", False):
        bundled = os.path.join(getattr(sys, "_MEIPASS", ""), "msedgedriver.exe")
        if os.path.exists(bundled):
            return bundled
    return None
```

⚠️ **顺序别写反**：很多人第一反应是「内置优先，内置没有才找同目录」。那样一旦打包进去的驱动版本不对，
用户只能重新打包才能换——而行内电脑上重打包是最高成本的失败路径。**外置文件优先 = 配置可热修复。**

### 用户可编辑的配置/数据文件：必须按 `sys.executable` 定位

onefile 打包后 `__file__` 指向 `sys._MEIPASS`（临时解压目录），**不是 exe 所在目录**。
凡是「用户要放在 exe 旁边自己改」的文件（config.json、白名单、模板），用 `__file__`
定位 = 永远读不到，而且日志里看不出异常（会静默回落到默认值或报「配置未填写」）。

```python
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))   # exe 目录：用户编辑的文件
    BUNDLE_DIR = getattr(sys, "_MEIPASS", APP_DIR)               # 内置资源：打包进去的模板
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = APP_DIR

CONFIG_PATH = os.path.join(APP_DIR, "config.json")
EXAMPLE_PATH = os.path.join(BUNDLE_DIR, "config.example.json")
if not os.path.exists(EXAMPLE_PATH):        # 兜底：有人把模板拷到 exe 旁边
    EXAMPLE_PATH = os.path.join(APP_DIR, "config.example.json")
```

口诀：**用户改的文件 → exe 旁边 → `sys.executable`；打包进去的只读资源 → `_MEIPASS`。**
打包成功后顺手把模板 copy 到 `dist/`，用户改名就能用。

**验证手法（不用真打包）**：
`sys.frozen=True; sys._MEIPASS="/tmp/x/_MEI"; sys.executable="/tmp/x/dist/App.exe"; importlib.reload(mod)`，
断言 `CONFIG_PATH` 落在 `dist/`、`EXAMPLE_PATH` 落在 `_MEI`、放了 exe 旁的 config.json 能被优先读到。

## 离线交付链：U 盘 → 行外打包 → 行内运行

银行/政务的典型交付方式，**不要用「你要不要打包」这种产品视角回答**：

```
开发机(Mac/Linux)  --U盘-->  行外 Windows(有网)  --U盘-->  行内 Windows(无网/无Python)
   写代码                        双击 build.bat                双击 exe 直接跑
```

U 盘里一起带：`脚本.py` + `build.bat` + **`msedgedriver.exe`**。
**不要在 U 盘版里放 `config.example.json` / 让用户填选择器**——U 盘版就是把元素写死在代码里
（脱敏 + 配置化只属于进 git 的那一份）。两份产物的完整契约、硬编码骨架、交付时要逐条说清的
改动清单见 `references/plaintext-vs-sanitized-delivery.md`。

用户为这条链纠正过两次，记牢三条：

1. **版本盯的是运行机，不是打包机**。行内 Edge 是 143 就必须带 143 驱动，行外那台是什么版本无关。
   bat 里打印打包机版本时要明写「本机版本不重要」，exe 启动时再比对一次运行机的。
2. **驱动可热替换**：查找顺序 exe 同目录 > 内置（见上文 `_get_driver_path`），所以版本错了不用重打包，
   换个文件即可——这是行内电脑上唯一低成本的补救。
3. **包型要能选**：`--onefile` 在管控电脑上会被杀软/AppLocker 拦自解压到 TEMP，
   提供 `--onedir` 文件夹版（整个目录拷过去），并让 bat 用菜单让用户选。

配套代码（版本探测、运行时自检、崩溃日志、`--build-dir`、bat 全文）见
`references/offline-exe-delivery.md`。

**双轨产物必须各自留档**：脱敏版进 git 有历史，**明文版（U 盘那份）默认没有**。每次调优完
`scripts/snapshot_deliverable.sh <文件> <时间点标签>`（一条命令，落到 `snapshots/` + `INDEX.txt` 记 md5），
并在交付话术里写清"这版对应几点几分"。否则用户一句「把三点五十之前最近那版拉一下」，你只能按 git 提交手工回退
重建——本次就是这么补的（见 pitfall 50 与 `references/batch-mode-grey-button-guards.md` 第 6 节）。

本次实际落地的形态（可照搬）：

| 产物 | 位置 | 说明 |
|---|---|---|
| 脱敏版 | `~/Documents/flow-clicker/`（git，21+ 提交，打 tag） | 元素走 `config.example.json` 占位符 |
| 明文版 | `~/Downloads/SendFenhang-*/` + U 盘 `连点-免配置/` | 元素写死、零配置、驱动内置 |
| 明文快照 | `~/Documents/连点-明文版-历史/`，由 `~/.hermes/scripts/snapshot_mingwen.sh` 生成 | 带时间戳副本，**不进 git**（约定：上 git 的才脱敏） |

用户会主动提醒「别忘了做好 git 版本控制」——标准动作是：改完立刻 `git commit`（写"改了什么/为什么"），
再跑一次快照脚本，最后在回复里给一句"git 提交 `xxxxxxx` + 快照已存"。

## EdgeDriver 版本与架构匹配

| Edge 版本 | 需要的 EdgeDriver | 下载文件名 |
|-----------|------------------|-----------|
| 126.0.2592.61 (x64) | x64 | `edgedriver_win64.zip` |
| 126.0.2592.61 (ARM) | ARM64 | `edgedriver_arm64.zip` |

**下错架构 → 运行时报"与 Windows 版本不兼容"。** 绝大多数 Windows 电脑是 x64。

EdgeDriver 从 `https://msedgedriver.azureedge.net/{version}/edgedriver_win64.zip` 下载。微软 CDN 在内网可能被墙 → 提供手动下载 fallback。

## GitHub Actions 自动打包

```yaml
name: Build Windows EXE
on: workflow_dispatch
jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install selenium webdriver-manager pyinstaller
      - run: |
          pyinstaller --onefile --windowed --name ToolName ^
            --hidden-import selenium --hidden-import webdriver_manager ^
            script.py
      - uses: actions/upload-artifact@v4
        with: {name: ToolName, path: dist/ToolName.exe}
```

这是 macOS 上为 Windows 打包的唯一可靠路径（云端 Windows runner）。

## 常见问题排查

### 找不到元素
1. 检查是否在正确的标签页（`switch_to.window`）
2. 检查是否有 iframe（`driver.switch_to.frame`）——**银行内网系统最常见原因**
3. 检查元素是否在 DOM 中但不可见（`el.is_displayed()`）——弹窗关闭后 DOM 残留
4. 加 `WebDriverWait` 等待元素出现
5. 页面可能是动态加载的，等 1-2 秒再找

### NoSuchWindowException: target window already closed
工具启动 Edge 打开 `about:blank`，用户手动导航到业务页面后原窗口句柄失效。Selenium 仍指向已关闭的 about:blank 窗口，所有 `find_element` 调用都报此错。

**修复**：每轮循环开始前调 `_ensure_window()` 扫描所有窗口句柄，切到非 about:blank 的那个（见三步循环模式的窗口管理章节）。

**症状**：诊断模式下 URL/标题正常（用户已导航），但点"开始"后所有选择器报 `NoSuchWindowException`。第一次尝试报 `AttributeError: 'NoneType' object has no attribute 'is_displayed'`（`find_element` 返回 None），后续全报 `target window already closed`。

### 点击没反应
1. 用 `execute_script("click()")` 替代 `.click()`
2. 检查元素是否被其他层遮挡
3. 先 `driver.execute_script("arguments[0].scrollIntoView();", el)` 再点

### 按钮找到但一直点（不切换）
弹窗关闭后确认按钮留在 DOM 中 `visible=False`。**必须检查 `is_displayed()` 才点击**，否则永远卡在点空气。

### 打包后 EdgeDriver 找不到
使用 `webdriver-manager` 自动下载，或预打包 EdgeDriver 到 exe。

### ModuleNotFoundError: selenium 子模块
PyInstaller 没扫到函数体内的 import。**所有 import 放文件顶部**（这条仍然成立），
但**打包参数用 `--collect-all selenium`，不要手写 hidden-import 枚举**——懒加载的
`selenium.webdriver.edge.webdriver` 靠枚举永远补不全（详见上文「定案」小节）。

正确的 PyInstaller 打包命令：

```batch
pyinstaller --onefile --windowed --name SendApproval ^
  --add-binary "msedgedriver.exe;." ^
  --collect-all selenium ^
  --hidden-import tkinter ^
  --hidden-import tkinter.ttk ^
  --hidden-import tkinter.scrolledtext ^
  send_approval_v2.py
```

### EdgeDriver 版本不匹配（session 实际踩坑）
EXE 运行报 `session not created: This version of Microsoft Edge WebDriver only supports Microsoft Edge version 126. Current browser version is 143`。
打包进去的 EdgeDriver 太旧，Edge 浏览器自动更新了。

**修复**：让用户在 Edge 地址栏输入 `edge://version` 查版本，去 https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/ 下载对应版本 `msedgedriver.exe`，放 exe 同目录重新打包。

**预防**：build.bat 里检查 `msedgedriver.exe` 存在并提示用户确认版本匹配。不要假设旧驱动能一直用——Edge 自动更新。

### EdgeDriver 下载 404
微软 CDN 在内网不可达 → 手动下载放同目录，build 时本地文件优先。

### 隐藏 CMD 黑窗
`subprocess` 默认显示控制台 → `creationflags=0x08000000`（CREATE_NO_WINDOW）。

### batch 文件闪退（编码问题）— 已修复，标准做法

**用 `write_file` 写 .bat 文件时，内容用纯 ASCII + `\r\n` 行尾。** 不要在 .bat 里写中文。用户原话："记得批处理文件别写中文。"

写完后用 `file build.bat` 验证输出应为 `DOS batch file text, ASCII text`。

用户偏好：给 .bat 文件而不是让用户手动敲命令。用户原话："你给我写个批处理文件不行吗？"

**标准 build.bat 模板**（双击即打包，含依赖安装+EdgeDriver检查+构建+打开输出文件夹）：
```bat
@echo off
cd /d "%~dp0"
echo Build Starting...
python --version
python -m pip install --user --no-cache-dir selenium pyinstaller
if not exist "msedgedriver.exe" (
    echo ERROR: msedgedriver.exe not found!
    pause
    exit /b 1
)
python -m PyInstaller --onefile --windowed --name ToolName ^
  --add-binary "msedgedriver.exe;." ^
  --hidden-import selenium ^
  --hidden-import selenium.webdriver.edge ^
  --hidden-import selenium.webdriver.edge.options ^
  --hidden-import selenium.webdriver.edge.service ^
  --hidden-import selenium.webdriver.edge.webdriver ^
  --hidden-import selenium.webdriver.remote.webdriver ^
  --hidden-import selenium.webdriver.remote.command ^
  --hidden-import selenium.webdriver.remote.errorhandler ^
  --hidden-import selenium.webdriver.common.keys ^
  --hidden-import selenium.webdriver.common.by ^
  --hidden-import selenium.common.exceptions ^
  --hidden-import tkinter ^
  --hidden-import tkinter.ttk ^
  --hidden-import tkinter.scrolledtext ^
  script.py
explorer "dist"
pause
```

**变体：打包参数还在演进时，让 bat 调 `--build`**（2026-11-04 采用）

参数一改就要同步改两处（bat 里一份、`self_build()` 里一份），迟早不一致。这种阶段让
bat 只做「查环境 + 装依赖 + 调 `--build`」，PyInstaller 参数全留在 Python 里一份：

```bat
@echo off
cd /d "%~dp0"
echo [1/4] Checking Python...
python --version
if errorlevel 1 (echo Python not found! Install Python 3.8+ and tick "Add to PATH". && pause && exit /b 1)
echo [2/4] Installing deps...
python -m pip install -r requirements.txt pyinstaller -q
if errorlevel 1 (echo pip install failed. If offline retry with: -i https://pypi.tuna.tsinghua.edu.cn/simple && pause && exit /b 1)
echo [3/4] Checking driver (optional)...
if exist msedgedriver.exe (echo   found - will be bundled) else (echo   NOT found - will auto-match, may fail on intranet)
echo [4/4] Building...
python flow_clicker.py --build
if exist dist\FlowClicker.exe (echo SUCCESS ^&^& explorer dist) else (echo FAILED - see messages above)
pause
```

驱动检查的松紧取决于交付方式，别再两头猜：

| 场景 | 驱动检查 | 理由 |
|---|---|---|
| 仓库里的通用版（脱敏、别人自己填配置） | 警告即可 | 仓库不该有 exe 二进制；有网机器能自动匹配 |
| **给离线内网机打包**（U 盘 → 行外打包 → 行内运行） | **缺失直接 `exit /b 1`** | 行内下不了驱动，缺了等于白打一轮，用户要重跑整条链 |

**重新打包前必须清缓存**：用户机器上已经有上一版 `build/` `dist/` `*.spec`，不清有概率复用旧分析结果，
改过的打包参数不生效，白忙一场。bat 里放在装依赖之后、构建之前：

```bat
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist AppName.spec del /q AppName.spec
```

交付话术也要说清：「旧 exe 请删掉」——用户很容易双击到上一版产物，然后拿旧报错来找你。

离线交付用 `if not exist msedgedriver.exe (echo ERROR... & pause & exit /b 1)`，
并在 bat 里打印打包机的 Edge 版本 + 一行提示「本机版本不重要，重要的是运行机」——
版本盯错机器是这条链上最常见的翻车点。完整 bat（含包型选择 1 单文件 / 2 文件夹）、
运行时环境自检、崩溃日志兜底见 `references/offline-exe-delivery.md`。

### pip 权限错误 + pyinstaller 不在 PATH（行内电脑常见）

行内 Windows 电脑 Python 装在 `C:\Python312`，pip 往 `Scripts` 目录写文件被拦：
```
ERROR: Could not install packages due to an OSError: [WinError 2] 系统找不到指定的文件.
```

**修复**：`pip` → `python -m pip install --user`，装到用户目录绕过权限。`--no-cache-dir` 避免缓存损坏。

`--user` 装完后 `pyinstaller` 命令不在 PATH：
```
'pyinstaller' is not recognized as an internal or external command
```

**修复**：`pyinstaller` → `python -m PyInstaller`（注意大小写 P）。

### PyInstaller 打包后 `No module named 'selenium.webdriver.edge.webdriver'`（2026-11-04 定案）

**症状**：exe 启动后日志显示环境全好——

```
驱动版本: Microsoft Edge WebDriver 143.0.3650.139
· 大版本一致 (143) ✓
端口 9222 已开放          ← Edge 起来了
连接失败: No module named 'selenium.webdriver.edge.webdriver'
```

**根因**：selenium 4.x 的 `webdriver.Edge` 是**运行时懒加载** `selenium.webdriver.edge.webdriver`
（`WebDriver` 类就在这个模块里）。PyInstaller 只跟随静态 import，手写 `--hidden-import` 枚举
（哪怕写了 `selenium.webdriver.edge`、`.options`、`.service`、`.common.by`）**依然漏掉 `.webdriver`**。
不是环境问题、不是驱动问题、换驱动也不会好——只能重新打包。

**正确修复（双保险，已验证）**：

```python
# 1) 文件顶层显式静态 import，让 PyInstaller 分析器一定看得见
import selenium.webdriver.edge.webdriver  # noqa: F401
```

```python
# 2) 打包参数用 collect-all，别再手写 hidden-import 枚举
"--collect-all", "selenium",
"--hidden-import", "tkinter",
"--hidden-import", "tkinter.ttk",
"--hidden-import", "tkinter.scrolledtext",
```

**原则**：第三方库一旦报子模块缺失，第一反应是 `--collect-all <pkg>`（PyInstaller ≥4.4），
**不是**继续往 hidden-import 列表里堆名字——那是打地鼠，而且对懒加载库必然漏。

**诊断要分得清**：`ImportError` / `ModuleNotFoundError` 必须单独 `except`，报「打包缺模块，
重新打包」，**不要**顺手走「换驱动/自动匹配」的兜底重试——本次就是这么把同一条错误打印了两遍，
看着像网络问题，实则是打包缺文件。

**验证**：`file build_exe.bat` 应输出 `DOS batch file text, ASCII text, with CRLF line terminators`。UTF-8 或 Unix LF → 必闪退。
```
[16:35:01] Looking for send button...        ← 开始搜索前
[16:35:01] Button found! Clicking...          ← 首次成功找到时
[16:35:01] Click #1                          ← 前 10 次：逐个
...
[16:36:15] DONE! Button disabled after 247.  ← 成功时
```

前 10 次点击逐个记，之后每 10 次一记。用户需要看到进度，但不是每 500 次都刷屏。

### V2 增强 Logger 模式（生产推荐）

现场调试时，单纯的 print 不够。推荐双通道 Logger：

```python
import threading, os
from datetime import datetime
from pathlib import Path

WORK_DIR = Path(r"C:\SendApprovalLogs")
LOG_FILE = WORK_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
SS_DIR = WORK_DIR / "screenshots"
SS_DIR.mkdir(parents=True, exist_ok=True)

class Logger:
    """双通道：文件 + 控制台。可扩展 GUI widget。"""
    _lock = threading.Lock()
    def info(self, msg):  self._write("INFO", msg)
    def warn(self, msg):  self._write("WARN", msg)
    def error(self, msg): self._write("ERROR", msg)
    def ok(self, msg):    self._write("OK", msg)
    def _write(self, level, msg):
        line = f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [{level}] {msg}"
        with self._lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(line + "\n")
        print(line)
```

**核心价值：**
- 日志持久化到文件 → 用户可以把 `.log` 文件发给你诊断
- 搭配 `driver.save_screenshot()` 定期截图 → concurrent 检查 UI 状态
- 每 50 次点击自动截图，按钮找不到时截图 + 页面元素诊断 → 远程排查不需要 TeamViewer

**关键函数：**
- `dump_page_info()`：打印当前页 URL、标题、所有已知选择器的命中情况、iframe 数量
- `wait_page_ready(timeout)`：等 `document.readyState === 'complete'`
- `reconnect()`：driver 断开后关旧 driver → 重新 launch + wait_page_ready（最多 3 次）

## PyInstaller 打包前检查清单

在运行 `pyinstaller` 之前逐项确认：

- [ ] 所有 import 在文件顶层（不是函数/方法体内，不是 `try:` 块内）
- [ ] 第三方库用 `--collect-all <pkg>`（selenium 必须 `--collect-all selenium`），**不要**手写
  hidden-import 枚举；同时在文件顶层显式 `import selenium.webdriver.edge.webdriver`。
  tkinter 三个子模块用 hidden-import 即可：`tkinter`, `tkinter.ttk`, `tkinter.scrolledtext`
- [ ] 重新打包前先清 `build/` `dist/` `*.spec`，避免复用上次的分析缓存（bat 里先 `rmdir /s /q`）
- [ ] `.bat` 文件是纯 ASCII + CRLF（不要写中文，用 `write_file` 写纯 ASCII）
- [ ] `.bat` 里用 `python -m pip install --user`（不用裸 `pip`，行内电脑权限会被拦）
- [ ] `.bat` 里用 `python -m PyInstaller`（`--user` 装的 pyinstaller 不在 PATH）
- [ ] 如果用 `--add-binary` 捆绑 EdgeDriver：确认架构匹配（x64 / ARM64）
- [ ] 读外部配置的程序：配置路径按 `sys.executable` 定位（onefile 下 `__file__` 指向 `_MEIPASS`）
- [ ] `--windowed` 用于 GUI 程序，否则会有 CMD 黑窗
- [ ] 在目标 Windows 版本上测试过（Win10/Win11）

## Consolidation History

- **2026-07-22**: Absorbed `pyinstaller-packaging` — all its content (import-at-top-level, batch encoding, two-phase GUI, hidden-import discovery, dependency checklist) was already covered here. Added consolidated checklist above.
