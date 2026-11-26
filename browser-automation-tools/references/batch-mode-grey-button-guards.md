# 批量/总行模式：灰按钮判定 + 防死循环闸门（2026-11-04 实测）

配套 `SKILL.md` pitfall 28 与「批量/总行模式」小节。本文记的是**现场证据、可复制代码、桩测试**。

## 1. 现场症状（用户原话）

> 「为什么我点开始总行连点，在总行连点按钮位空的时候还是在打日志？……就是按钮为灰色」

日志形态：

```
开始总行循环: 关弹窗 → 点发送总行审批
  ✓ [总行发送] 已点击 (frame[1]) id=_ctp_toolbar_item_button_sendfmbm
  已发送 1 次
  ✓ [总行发送] 已点击 (frame[1]) id=_ctp_toolbar_item_button_sendfmbm
  已发送 2 次
...   （按钮屏幕上一直是灰的，循环不停）
```

关键判读：**按钮被"点中"了（Selenium 返回成功），但业务上不可用**。所以不能用"点击成功"当进度，
必须用按钮状态。

## 2. 根因：只认一种"灰"

```python
# ❌ 旧写法：没有 disabled 属性就当成能点
for el in els:
    if el.get_attribute("disabled") is None:
        return "enabled"
    result = "disabled"
```

CTP 工具栏的灰是 **class**（`ctp-toolbar-image-disable` / `... disabled`）或 `aria-disabled="true"`，
`disabled` 属性根本不出现。于是：

1. `_submit_state()` 恒返回 `enabled`；
2. 「见 disabled = 全部发完」永远不成立 → 循环不停；
3. 每次点击都打一行 `✓ [已点击]`（`quiet` 默认 False）→ 刷屏；
4. 用户看到的就成"灰的还在打日志"。

## 3. 修法

### 3.1 三态判定

```python
def _submit_state(self):
    """'enabled' / 'disabled' / 'missing' —— 只看该按钮本身"""
    el, _p = self._find(DONE_FLAG, prefer=getattr(self, "_a_path", None))
    if el is None:
        return "missing"
    try:
        if el.get_attribute("disabled") is not None:
            return "disabled"
        cls = (el.get_attribute("class") or "").lower()
        aria = (el.get_attribute("aria-disabled") or "").lower()
        if "disab" in cls or aria in ("true", "1"):
            return "disabled"
        return "enabled"
    except StaleElementReferenceException:
        return "missing"
```

顺带收益：改用 `_find(..., prefer=_a_path)` 后，不再每轮 `_frame_paths()` 扫全树（原来这个状态
查询本身就是每轮几百毫秒的开销）。

### 3.2 worker 里的四道闸门

```python
no_dlg = 0        # 连续几次点了没弹出确认框（按钮灰 / 页面没反应）
miss_btn = 0      # 连续几次找不到按钮

while not stop:
    if self._click_confirm("关弹窗", quiet=True):
        self._clicks += 1; no_dlg = 0; wait(0.1); continue

    st = self._submit_state()
    if st == "enabled":
        self._saw_enabled = True
        miss_btn = 0
    elif st == "disabled":
        if self._saw_enabled:
            log(f"发送按钮已变灰 → 全部发完! 共 {self._clicks} 次点击")
        else:
            log("发送总行按钮是灰的(不可点) → 这一笔不需要总行审批, 停止")   # 0 次点击
        break
    else:                                     # missing
        miss_btn += 1
        if miss_btn >= 5:
            log("找不到「发送总行审批」按钮 → 可能不在总行审批页面, 停止")
            break
        wait(interval); continue

    # 点击（前 3 次打日志，之后静默）
    if self._click_submit("总行发送", quiet=(self._clicks >= 3)):
        self._clicks += 1
        if self._clicks <= 3 or self._clicks % 20 == 0:
            log(f"  已发送 {self._clicks} 次")
        no_dlg += 1
        if no_dlg == 8:
            log("  · 已连点 8 次都没弹确认框, 按钮可能是灰的; 再试 7 次就停")
        if no_dlg >= 15:
            log("连续 15 次点「发送总行审批」都没弹出确认框 → 按钮灰/点不动, 停止")
            break
    else:
        no_dlg += 1
        if no_dlg >= 15:
            log("15 次都点不到「发送总行审批」按钮 → 停止"); break

    wait(interval)
```

阈值取 8/15 而不是 3/5：有些页面确实不弹确认框直接提交，太激进会误停。8 次先给一行提醒，
让用户有机会看到"这是在硬撑"，15 次才真正停。

### 3.3 参数要沿包装链传下去

```python
def _click_by_key(self, key, tag, skip_label=None, cache_key=None, quiet=False):
    ...
    return self._click_any(sels, tag, skip_label=skip_label,
                           cache_key=cache_key, quiet=quiet)
```

`quiet` 少传一层 → 「日志闸」失效，重复点击照旧刷屏（本次就是这样漏的）。

## 4. 桩测试（不用假浏览器，2 秒跑完）

```python
import sys, types, time
# --- selenium / tkinter stub（同 templates/stub_driver_test.py 的头部）---
sys.path.insert(0, "<工程目录>")
import SendFenhang as sf

class El:
    def __init__(self, attrs): self.a = attrs
    def get_attribute(self, k): return self.a.get(k)
    @property
    def text(self): return self.a.get("text", "发送总行审批")
    def is_displayed(self): return True

def state_of(attrs):
    app = object.__new__(sf.App)
    app._a_path = None
    app._find = lambda sels, skip_cancel=False, prefer=None: (
        (El(attrs), []) if attrs is not None else (None, None))
    return app._submit_state()

cases = [
    ({"disabled": "disabled"},               "disabled", "disabled 属性"),
    ({"class": "ctp-toolbar-image disabled"},"disabled", "class 带 disabled"),
    ({"class": "ctp-toolbar-image-disable"}, "disabled", "class 带 -disable"),
    ({"aria-disabled": "true"},              "disabled", "aria-disabled"),
    ({"class": "ctp-toolbar-image"},          "enabled",  "正常可点"),
    (None,                                    "missing",  "按钮不存在"),
]
for attrs, want, label in cases:
    assert state_of(attrs) == want, label
```

worker 行为用 monkeypatch 验（不需要 driver）：

```python
app = object.__new__(sf.App)
app.driver = types.SimpleNamespace(current_url="http://x/")
app._stop = Stop()                      # is_set()->False, wait(t)->sleep(0)
app.speed = types.SimpleNamespace(get=lambda: 0.01)
app._ensure_window = lambda: True
app._submit_state = lambda: state       # 注入状态
app._click_confirm = lambda tag, quiet=False: dialog_ok
app._click_submit  = lambda tag="总行发送", quiet=False: (
    logs.append(f"  ✓ [{tag}] 已点击") if not quiet else None) or click_ok
app._worker_zh(1)

# 灰：0 次点击 + 立刻停
# missing：≤5 次循环内停
# enabled 但从不弹框：15 次后停，且 "已点击" 日志 ≤3 行
```

## 5. 回退版本时，把修复的范围说清楚

本次顺序是：用户先要「回退到 15:50 之前那版」，紧接着报总行 bug。做法是在**回退后的那份**上
只改总行相关函数，并在回复里明确写：

> 本次只改 `_submit_state` / `_worker_zh`，分行的 `_wait_effect` / `_dialog_gone_wait` /
> 点 A 路径一个字符没动。

用户被"修一个挂一个"坑过（原话「别修了分行的总行又挂了」），"改了哪些 / 没改哪些"必须明说，
并且用回归测试证明分行关键函数还在（`grep -c "_wait_effect("` 之类的最便宜的断言）。

## 6. 明文版没有历史时怎么回退（本次实操）

git 里只有脱敏版，U 盘明文版一直被覆盖同一个文件。重建"某一时刻"的明文版：

1. `git log --format='%h %ad %s' --date=format:'%m-%d %H:%M'` 找时间点对应的提交；
2. `git archive <commit> | tar -x -C <快照目录>`（别 `git checkout`，不动工作区）；
3. 从当前明文版反向删改（用按 `def` 名字成块删除的脚本，别手删）：
   - 常量回到当时值（如 `A_RETRY_TIMEOUT=1.0`、`A_MAX_WAIT=12`）
   - 删掉之后新增的方法 / JS 常量 / 按钮
   - 把调用点改回当时的写法
4. `py_compile` + 一个"特征断言"脚本（`assert not hasattr(App, "_wait_effect_or_reload")`）；
5. 交付时说明"这是按提交反推的、对应几点几分"。

代价很高——所以每轮调优后立刻 `cp` 一份带时间戳的快照，别等用户开口。

## 7. 收尾感知：停下来 + 响三声 + 弹框（两个模式都要）

用户原话：**「如果发送分行审批这个按钮灰色了，我的点击流程能不能停，然后工具给我报个提示，出个声音？」**
紧接着的一句是：**「总行变灰会有声音吗？」** —— 第二句就是本次的坑：分行加了、总行只打日志。

### 7.1 单一实现

```python
def _notify(self, title, msg):
    """响三声 + 弹提示。worker 线程不能直接碰 tkinter，必须 root.after 切回主线程。"""
    try:
        import winsound
        for _ in range(3):
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            time.sleep(0.25)
    except Exception:
        pass                       # 非 Windows / 静音 / 无卡 都不能影响主流程
    try:
        root = getattr(self, "root", None)
        if root is not None:
            root.after(0, lambda: messagebox.showinfo(title, msg))
        else:
            messagebox.showinfo(title, msg)
    except Exception:
        pass
```

顶层 import 也要加：`from tkinter import ttk, scrolledtext, messagebox`
（**加了就得同步补桩测试**：`mk("tkinter.messagebox", showinfo=..., showerror=...)`、
`mk("winsound", MessageBeep=<计数>, MB_ICONEXCLAMATION=48)`，否则四个测试当场 ImportError。）

### 7.2 插入点（两处 worker，缺一就是本次的 bug）

```python
# 分行：每轮开工、点主按钮之前
a_st = self._btn_state(BTN_A)
if a_st == "disabled":
    self._stop.wait(0.4)                  # 提交后重载瞬间会误判成灰，必须复核
    a_st = self._btn_state(BTN_A)
if a_st == "disabled":
    self._log("「发送分行审批」按钮已变灰 → 没有待处理的了, 自动停止")
    self._notify("发送分行审批已变灰", f"按钮已经变灰，没有待处理的了。\n本次完成 {self.rounds} 笔。")
    break
if a_st == "missing":
    a_miss += 1
    if a_miss >= 5:
        self._notify("找不到「发送分行审批」", "连续 5 次没找到按钮。\n请确认浏览器停在待审批列表那一页。")
        break

# 总行：三道闸门的每个 break 之前都要 _notify（变灰完成 / 一开始就灰 / 找不到 / 点不动）
```

### 7.3 桩测试（断言「响了几声 + 弹了什么」）

```python
calls = {"info": [], "beep": 0}
mk("winsound", MessageBeep=lambda c: calls.__setitem__("beep", calls["beep"] + 1),
   MB_ICONEXCLAMATION=48)
mk("tkinter.messagebox", showinfo=lambda t, m: calls["info"].append((t, m)), showerror=lambda *a, **k: None)
app.root = types.SimpleNamespace(after=lambda ms, fn: fn())   # after 直接同步执行

app._btn_state = lambda sels: "disabled"
app._worker_fen(1)
assert clicked["n"] == 0                     # 灰的：一次都不点
assert calls["beep"] == 3                    # 响三声
assert calls["info"] and "变灰" in calls["info"][0][0]
assert "7 笔" in calls["info"][0][1]         # 进度写进提示
```

总行同法跑三种注入状态（`disabled` 且已见过 enabled / `disabled` 且从未见过 / `missing`），
每种都断言 `beep == 3` 且 `info` 非空——**这两条断言就是「用户能感知到」的可执行定义**。
