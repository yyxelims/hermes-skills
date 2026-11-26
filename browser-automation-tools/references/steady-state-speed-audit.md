# 稳态速度审计：把「轮间间隔」压到 interval + 几十毫秒

2026-11-04 实战。背景：工具已能连做 15 轮，但用户第二次反馈「每轮之间还是会隔很久」。
前几轮都在调 `MIN_GAP` / 改等待判据，没用。做命令级体检后一次解决。

## 1. 成本模型（先认这个数，再谈优化）

| 操作 | WebDriver 命令数 | 真实耗时（本案） |
|---|---|---|
| 一次 `find_elements` 未命中 | 1 | 5–30ms |
| 一次 `_find`（5 选择器 × 7 条 frame 路径）未命中 | ~35 | **0.5–1.5s** |
| `switch_to.default_content()` + 逐层 `switch_to.frame()` | 1 + N | 5–30ms |
| 一次 `execute_script`（JS 里查+点） | 1 | 20–40ms |
| `switch_to.window()` | 1 | 5–20ms |

一轮循环里藏着 3 次「查一下有没有弹窗」：轮首清残留、点确定前、点确定后。全部走 `_find` 时，
每轮凭空多出 1–4 秒 —— 这就是用户看到的「轮间间隔」。**它不是 sleep，是扫描。**

体检动作：把 loop 体内的每个 Selenium 调用列出来数一遍。稳态每轮应 ≤ 25 条命令。

## 2. JS 快路径：一条命令查/点

必须在**已知的 frame** 里跑（先 `_goto_path(_a_path)`），否则查不到。

```python
JS_CLICK_A = """
var el = document.querySelector("[id='_ctp_toolbar_item_button_send']");
if (!el) return 'no_element';
el.click();
return 'clicked';
"""

JS_DIALOG = """
var bs = document.querySelectorAll("input[id^='ymPrompt_btn_']"), n = 0, ids = [];
for (var i = 0; i < bs.length; i++) {
  var s = getComputedStyle(bs[i]), r = bs[i].getBoundingClientRect();
  if (r.width > 0 && r.height > 0 && s.visibility !== 'hidden'
      && parseFloat(s.opacity || 1) > 0.01
      && (bs[i].value || '').indexOf('\u53d6') < 0) {      // 排除「取 消」
    n++; if (ids.length < 3) ids.push(bs[i].id);
  }
}
return {n: n, ids: ids.join(',')};
"""

JS_CLICK_CONFIRM = """
var bs = document.querySelectorAll("input[id^='ymPrompt_btn_']");
for (var i = 0; i < bs.length; i++) {
  var s = getComputedStyle(bs[i]), r = bs[i].getBoundingClientRect();
  if (r.width > 0 && r.height > 0 && s.visibility !== 'hidden'
      && parseFloat(s.opacity || 1) > 0.01
      && (bs[i].value || '').indexOf('\u53d6') < 0) { bs[i].click(); return bs[i].id; }
}
return '';
"""
```

可见性判定用 `getBoundingClientRect()` + `visibility` + `opacity`：
**不要只看 `el.style.display`**（祖先 `display:none` 时元素自身仍是 `inline-block`），
也不要数 DOM 节点（关闭后节点仍在 DOM 里）。判定语义是「有没有真正占据布局」。

```python
def _js(self, path, script):
    """失败（含老测试桩）返回 None，调用方回落到 Selenium —— 保证兼容"""
    try:
        if path is not None:
            self._goto_path(path)
        return self.driver.execute_script(script)
    except Exception:
        return None
```

### 关键陷阱：JS 说「没有」时不要退回扫描

```python
def _click_confirm(self, tag="确认", quiet=False, cache_key="_c_path"):
    for p in self._cached_paths():                     # _c_path / _a_path
        r = self._js(p, JS_CLICK_CONFIRM)
        if isinstance(r, str):
            if r:                                      # 点到了
                return True
            self._c_miss = getattr(self, "_c_miss", 0) + 1
            if self._c_miss % 10 != 0:                 # 每 10 次空结果才校准一次缓存
                return False                            # ← 绝不落进 _find 扫树
    return self._click_any(BTN_CONFIRM, tag, skip_cancel=True,
                           quiet=quiet, cache_key=cache_key)
```

调用方本来就每 0.1s 重试一次，「这次没有」= 返回 False 就够。**退回全树扫描是纯粹的性能自杀。**

## 3. 缓存三样上下文

```python
def _goto_path(self, path):
    """已经在目标 frame 里就不重复切（每次切换 5–30ms）"""
    path = list(path)
    if getattr(self, "_ctx_now", None) == path:
        return
    self.driver.switch_to.default_content()
    for idx in path:
        frames = self._frames_here()
        if idx >= len(frames):
            self._ctx_now = None
            raise NoSuchElementException(f"frame[{idx}] 不存在")
        self.driver.switch_to.frame(frames[idx])
    self._ctx_now = path
```

- `_frame_paths()` 结束时会 `default_content()`：那里必须同步 `_ctx_now = []`。
- `_ensure_window()` 切窗口会让 frame 上下文失效：切完把 `_ctx_now = None`；
  并且**pin 住一个句柄**（`self._win`），之后每轮只 `switch_to.window(self._win)` + 读一次 URL，
  不再遍历所有句柄。
- 元素查找 `_find(..., prefer=_c_path)`：优先试缓存路径，未命中再走 BFS（见
  `references/click-timing-and-frame-context.md`）。

## 4. interval 补差额 + 轮询粒度

```python
ok, t_c = self._wait_click_confirm(TIMEOUT_CONFIRM)   # 返回「点到的时刻」
...
if t_c is not None:
    rest = interval - (time.time() - t_c)             # 校验已花掉的时间不再重复等
    if rest > 0:
        self._stop.wait(rest)
```

- `_wait_effect`：alert 每 50ms 查一次，确认框每 150ms 查一次（省一半命令）。
- `_dialog_gone_wait`：50ms 轮询，且要带 **grace**（见下）。

## 5. 安全阀：重试/补点的窗口必须 > 页面延迟

本次踩过两个「为了快而引入重复提交风险」的坑，务必带着 grace：

| 参数 | 错误值 | 正确值 | 后果 |
|---|---|---|---|
| `A_RETRY_TIMEOUT`（点主按钮后等弹窗） | 0.2s | **1.0s**（页面实测 350ms） | 弹窗还没出现就重点 → 可能排队成两次提交 |
| 补点确认框的最小间隔 | 0（立刻） | **grace 0.25s** | 弹窗淡出中重复点同一个「确定」 |

```python
def _dialog_gone_wait(self, timeout=1.5, reclick=False, grace=0.25):
    t0 = time.time(); clicks = 0
    while time.time() - t0 < timeout and not self._stop.is_set():
        n, _ = self._dialog_count_fast()
        if n == 0:
            return True, time.time() - t0, clicks
        if reclick and clicks < 3 and (time.time() - t0) >= grace:   # ← 先让它自然关
            self._click_confirm("补点", quiet=True); clicks += 1
        self._stop.wait(0.05)
    return False, time.time() - t0, clicks
```

## 6. 审计测试骨架（可复制）

用「按命令计延迟」的假 driver，一边量间隔一边量命令数，并**禁止稳态扫树**。

```python
CMD = 0.008       # 每条 WebDriver 命令 8ms（按目标机实测调）
ALERT_LAT, DLG_LAT = 0.05, 0.05

class Page:
    def find_elements(self, by, val):
        self.cmds += 1; time.sleep(CMD); self.tick()
        ...
    def execute_script(self, js, *args):
        self.cmds += 1; time.sleep(CMD); self.tick()
        if args:                              # arguments[0].click()
            ...
        if js is sf.JS_CLICK_A:      ...      # 无参 = JS 快路径，按内容分派
        if js is sf.JS_DIALOG:       return {"n": 1 if self.dlg_up else 0, "ids": ""}
        if js is sf.JS_CLICK_CONFIRM: ...
    def click_confirm(self):
        ...; self.items -= 1; self.t_c = time.time()      # 记下"点确定"时刻
    def click_A(self):
        if self.t_c is not None:
            self.gaps.append((time.time() - self.t_c) * 1000); self.t_c = None
```

```python
# 反退化：第 1 轮之后禁止扫 frame 树
_orig = sf.App._frame_paths
state = {"allow": True}
def guarded(self, *a, **k):
    if not state["allow"]:
        raise AssertionError("稳态下还在扫 frame 树（每轮几百毫秒的来源）")
    return _orig(self, *a, **k)
sf.App._frame_paths = guarded
# 第 1 轮 click_confirm 之后：state["allow"] = False

assert page.confirms == 3
assert max(gaps) < INTERVAL * 1000 + 200      # 轮间只允许 interval + 命令开销
deltas = [round_cmds[i] - round_cmds[i-1] for i in range(1, len(round_cmds))]
assert max(deltas) < 40                        # 稳态命令数上限
```

本次实测：改前 37 条/轮、间隔秒级；改后 **22 条/轮、间隔 132–134ms（interval=0.1）**。

## 7. 交付话术

- 给用户的验收口径是**日志时间戳差**：`═══ 第 N 轮完成 ═══` 到下一条 `━━━ A ━━━` 的秒差，
  以前 7 秒、现在 0–1 秒。比讲"我优化了 XX"有说服力。
- 末尾「确认没有待办」会吃满 `A_MAX_WAIT`（12s），那是收尾不是轮间停顿，先在说明里写清，
  否则用户会把收尾等待再当成一次 bug 报回来。
