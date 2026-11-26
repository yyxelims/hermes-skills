#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""假 driver 桩：不装 selenium、不开浏览器、不打包，直接在本地验证点击逻辑。

用法：复制本文件到项目旁，改两处 —— MODULE（你的工具模块名）、A_SEL/CONFIRM（选择器），
然后 `python stub_driver_test.py`。行内电脑上一次打包 10 分钟，这个 0.3 秒。

能验证什么（都是本 skill 里踩过的真坑）：
  1. 弹窗按钮 id 自增（..._9）也能点中；取消按钮（含"取"）绝不被点
  2. 元素在嵌套 frame（frame[1][0]）里也能找到——只扫一层会漏
  3. 点击前会切回元素所在 frame——否则 execute_script 抛 NoSuchElement
  4. 隐藏元素（display:none）不被当作命中，也不会刷"点击失败"
  5. 主循环不依赖 JS 判断弹窗（booby-trap _probe_state，一调用就炸）
"""
import sys, types, time
import lxml.html as LH

MODULE = "my_tool"          # ← 改成你的模块文件名（不带 .py）
A_SEL_ID = "btn_send"       # ← 改成主按钮 id
ROUNDS = 2                  # ← 跑几轮

# ---------------------------------------------------------------- stub selenium
def _mk(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m

class NoSuchElement(Exception): pass
class NoAlert(Exception): pass
class StaleEl(Exception): pass
class UnexpectedAlert(Exception): pass
class NotInteractable(Exception): pass

class By:
    CSS_SELECTOR = "css selector"; XPATH = "xpath"; ID = "id"
    PARTIAL_LINK_TEXT = "partial link text"; LINK_TEXT = "link text"

_mk("selenium.webdriver")
_mk("selenium.webdriver.common", by=None)
_mk("selenium.webdriver.common.by", By=By)
_mk("selenium.webdriver.edge", service=None, options=None)
# ★ 静态 import 的子模块必须存在，否则模块 import 阶段就炸
_mk("selenium.webdriver.edge.webdriver", WebDriver=object)
_mk("selenium.webdriver.edge.service", Service=object)
_mk("selenium.webdriver.edge.options", Options=object)
_mk("selenium.common", exceptions=None)
_mk("selenium.common.exceptions",
    NoSuchElementException=NoSuchElement, NoAlertPresentException=NoAlert,
    StaleElementReferenceException=StaleEl,
    UnexpectedAlertPresentException=UnexpectedAlert,
    ElementNotInteractableException=NotInteractable)
_mk("selenium", webdriver=sys.modules["selenium.webdriver"])
_mk("tkinter", Tk=object, StringVar=object, DoubleVar=object, END="end",
    NORMAL="normal", DISABLED="disabled", BOTH="both", LEFT="left")
_mk("tkinter.ttk"); _mk("tkinter.scrolledtext")

mod = __import__(MODULE)

# ---------------------------------------------------------------- 假页面
# 文档树：0 → [1,2]；2 → [3]；弹窗在 3（两层 frame 深），故意做得比 max_depth 浅一层
DOCS = {
    0: "<html><body><iframe/><iframe/></body></html>",
    1: "<html><body></body></html>",
    2: "<html><body><iframe/></body></html>",
    3: f"""<html><body>
        <span id="hidden_confirm" style="display:none">确 定</span>
        <input type="button" id="dlg_btn_9" value="确 定">
        <input type="button" id="dlg_btn_10" value="取 消">
        <a id="{A_SEL_ID}">main</a>
      </body></html>""",
}
CHILD = {0: [1, 2], 1: [], 2: [3], 3: []}
TREES = {k: LH.fromstring(v) for k, v in DOCS.items()}

class El:
    def __init__(self, e, doc): self.e, self.doc = e, doc
    def get_attribute(self, n): return self.e.get(n)
    @property
    def text(self): return self.e.text or ""
    def is_displayed(self):
        # 近似 Selenium：祖先 display:none → 不可见
        p = self.e
        while p is not None:
            if "display:none" in (p.get("style") or ""):
                return False
            p = p.getparent()
        return True

class Driver:
    def __init__(self):
        self.path = []; self.clicked = []; self.switch_to = self
    # --- switch_to ---
    def default_content(self): self.path = []
    def frame(self, el):
        frames = TREES[self.doc_idx].cssselect("iframe, frame")
        self.path.append(frames.index(el.e))
    def window(self, h): pass
    @property
    def alert(self): raise NoAlert()
    # --- 定位 ---
    @property
    def doc_idx(self):
        cur = 0
        for i in self.path: cur = CHILD[cur][i]
        return cur
    def find_elements(self, by, val):
        doc = TREES[self.doc_idx]
        try:
            if by == By.CSS_SELECTOR:
                if val.strip() == "iframe, frame":
                    return [El(e, self.doc_idx) for e in doc.cssselect(val)]
                els = doc.cssselect(val)
            elif by == By.XPATH: els = doc.xpath(val)
            elif by == By.ID: els = doc.xpath(f"//*[@id='{val}']")
            elif by == By.PARTIAL_LINK_TEXT:
                els = [e for e in doc.iter() if val in (e.text or "")]
            else: els = []
        except Exception:
            return []
        return [El(e, self.doc_idx) for e in els]
    def execute_script(self, js, arg=None):
        if isinstance(arg, str):                 # 探针 JS
            raise AssertionError("主循环不该用 JS 判断弹窗，应判'确认按钮是否可见'")
        if arg.doc != self.doc_idx:              # ★ 复现真实 Selenium 行为
            raise NoSuchElement("element not found in current frame")
        self.clicked.append(arg.get_attribute("id"))

# ---------------------------------------------------------------- 假 App 骨架
class Ev:
    def is_set(self): return False
    def set(self): pass
    def clear(self): pass
    def wait(self, t=None): return False

App = getattr(mod, "App", None) or getattr(mod, "FlowClickerApp")
app = object.__new__(App)
app.driver = Driver(); app._stop = Ev()
app.speed = types.SimpleNamespace(get=lambda: 0.1)
for attr, val in (("rounds", 0), ("_clicks", 0), ("_a_path", None),
                  ("_saw_enabled", False), ("_run_id", 1)):
    try: setattr(app, attr, val)
    except Exception: pass
logs = []
app._log = logs.append
app._ctr = lambda: None
app.st = types.SimpleNamespace(set=lambda v: None)
app._halt_ui = lambda: None
try:
    app._check_config = lambda: True
except Exception:
    pass

# ---------------------------------------------------------------- 跑
print("frame 路径:", app._frame_paths())
assert [1, 0] in app._frame_paths(), "递归 frame 遍历失效：找不到嵌套 frame"

ok = app._click_confirm("T")
print("点确定 ->", ok, app.driver.clicked)
assert ok, "自增 id 的确定按钮没点中"
assert app.driver.clicked == ["dlg_btn_9"], f"点错了：{app.driver.clicked}（绝不能点取消/隐藏项）"
assert not any("点击失败" in l for l in logs), f"不该刷假失败：{logs}"

print("\n".join(logs))
print("\nALL PASSED")
