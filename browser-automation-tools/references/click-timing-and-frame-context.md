# 「点击失败: NoSuchElementException」+ 间隔调快就点空（2026-11-04 终局定位）

功能已经跑通（连做 15 轮），但日志里每轮都有一行 `⚠ 点击失败`，且用户把间隔拖到 0.6s 以下
就必翻车。两个问题同源：**页面状态在「扫描 → 定位 → 点击」之间变了**。

## 症状原文

```
[13:57:21]   ✓ [C] 已点击 (frame[1]) id=ymPrompt_btn_0
[13:57:21] ═══ 第 1 轮完成 ═══
[13:57:22]   ⚠ [清残留] 点击失败: NoSuchElementException     ← 每轮一条，功能其实正常
...
[13:57:26] ━━━ B: 浏览器原生弹窗 ━━━
[13:57:31]   · 5秒内没出原生弹窗, 直接到C
[13:57:32]   ⚠ [C] 点击失败: NoSuchElementException        ← 连报 9 次
[13:57:41]   ✗ 30秒仍无确定 — 自动停止

诊断片段：
  frame[1] id=ymPrompt_btn_15 value='确 定' visible=False   ← 隐藏残留
  · 已变灰: True                                            ← 总行按钮天生灰
```

## 根因（两层叠在一起）

1. **把「隐藏但仍在 DOM 里」的元素当兜底返回**。弹窗关掉后 ymPrompt 按钮节点还在，只是
   `visible=False`。旧 `_find` 有 `fallback` 分支，循环结束返回这个隐藏按钮 → 点击动作
   对着空气点 → 报异常。证据就在诊断输出里：`ymPrompt_btn_15 visible=False`。
2. **找到元素的位置 ≠ 执行点击的位置**。`_find` 遍历 `_frame_paths()`（本例 主文档 + 4 个
   frame），每轮 `switch_to.frame` 会移动 driver 上下文；循环结束时上下文停在**最后**访问的
   frame，而元素是在**前面**某个 frame 找到的。此时 `execute_script("arguments[0].click()", el)`
   在错误上下文里查元素 → `NoSuchElementException`。
3. **固定 sleep 比页面慢**。上一轮弹窗有淡出动画，`interval=0.5` 时点主按钮偶尔空点
   （日志表现为「A 已点击 → 5 秒内没出原生弹窗 → C 全空」）。用户拖到 0.4s/0.3s 时空点变常态。

## 修复一：只返回可见元素 + 返回 frame 路径

```python
def _find(self, selectors, skip_cancel=False):
    """返回 (element, frame路径)。只返回可见元素。"""
    for path in self._frame_paths():
        try:
            self._goto_path(path)
        except Exception:
            continue
        for by, val in selectors:
            try:
                els = self.driver.find_elements(by, val)
            except Exception:
                continue
            for el in els:
                try:
                    txt = (el.get_attribute("value") or el.text or "").strip()
                    if skip_cancel and CANCEL_KEY in txt:
                        continue
                    if el.is_displayed():          # ← 隐藏的一律不算
                        return el, path            # ← 返回 path 而不是 ctx 字符串
                except StaleElementReferenceException:
                    continue
    return None, None
```

## 修复二：点击前切回元素所在 frame，失效重找一次

```python
def _click_any(self, selectors, tag, skip_cancel=False, quiet=False):
    for attempt in range(2):
        el, path = self._find(selectors, skip_cancel=skip_cancel)
        if el is None:
            return False
        try:
            self._goto_path(path)          # ★ 关键：回到元素真正所在的 frame
            self.driver.execute_script("arguments[0].click();", el)
            if not quiet:
                self._log(f"  ✓ [{tag}] 已点击 ({self._ctx(path)}) id={el.get_attribute('id')}")
            return True
        except (StaleElementReferenceException, NoSuchElementException):
            if attempt == 0:
                self._stop.wait(0.15)
                continue                   # 页面在扫描中途变了 → 重找一次再点
            if not quiet:
                self._log(f"  ⚠ [{tag}] 元素失效, 重找后仍点不到")
            return False
```

`quiet=True` 用于「清残留弹窗」这类**本来就可能没有目标**的探测：找不到就静默返回 False，
不要每轮刷一行 `⚠`。日志噪音会把真异常淹掉。

## 修复三：事件驱动等待 + 点击无效果就重试

```python
MIN_GAP = 0.5      # 页面下限：低于它上一轮弹窗还没关干净，点主按钮会点空

def _alert_present(self):
    try:
        self.driver.switch_to.alert
        return True
    except NoAlertPresentException:
        return False
    except UnexpectedAlertPresentException:
        return True          # 这个异常本身就是"弹窗挂着"的信号

def _wait_effect(self, timeout):
    """等主按钮的点击生效：出现原生弹窗 或 页面弹窗。返回 'alert'/'dialog'/None"""
    deadline = time.time() + timeout
    while time.time() < deadline and not self._stop.is_set():
        if self._alert_present():
            return "alert"
        el, _ = self._find(CONFIRM_SELECTORS, skip_cancel=True)
        if el is not None:
            return "dialog"
        self._stop.wait(0.2)
    return None

def _wait_click_confirm(self, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline and not self._stop.is_set():
        if self._click_confirm("C"):
            return True
        self._stop.wait(0.2)
    return False
```

主循环里把「点了 A 之后就死等 0.5 秒」改成「点了 A 就等效果，生效立刻往下走」；
没反应先重试，而不是直接判失败：

```python
kind = None
for attempt in range(3):
    if not self._click(BTN_A, "A" if attempt == 0 else f"A重试{attempt}"):
        kind = "no_button"; break
    kind = self._wait_effect(6.0 if attempt == 0 else 2.5)
    if kind:
        break
    self._log(f"  · A 点了但没弹出任何窗口 (第 {attempt+1} 次), 稍等重试")
    self._stop.wait(0.5)

if not kind:
    self._log("连点 A 三次都没任何弹窗 → 应该没有待处理的了, 自动停止")
    break
```

**连点 3 次无任何弹窗 = 业务上没有待处理项了**，这是比「30 秒超时报错」准确得多的终态信号。
滑块下限也一起改成 `MIN_GAP`（`ttk.Scale(from_=MIN_GAP, ...)`），用户拖不到会空点的区间，
并在首次触发时打一行「间隔 0.4s 比页面刷新还快，实际按 0.5s 下限执行」。

## 修复四：「按钮变灰 = 发完」必须先见过可点

诊断显示 `· 已变灰: True`，但那单根本不需要走总行（按钮天生灰）。一见 `disabled` 就
`break` 会立刻误停，用户会以为工具坏了。

```python
def _submit_state(self):
    """'enabled' / 'disabled' / 'missing'"""
    result = "missing"
    for path in self._frame_paths():
        ...
        for el in els:
            if el.get_attribute("disabled") is None:
                return "enabled"
            result = "disabled"
    return result

# 循环里
st = self._submit_state()
if st == "enabled":
    self._saw_enabled = True
elif st == "disabled":
    if self._saw_enabled:
        self._log("按钮已变灰 → 全部发完")
    else:
        self._log("按钮一开始就是灰的 → 这单可能不需要这一步, 停止")
    break
```

## 不用 Windows 就能验证：假 driver + 假时钟

关键是把「延迟」建成 tick 模型：`wait()` 里推进时间，A 点击后 `alert_due = t+2`，
accept 后 `dialog_due = t+2`；`execute_script` 里断言 `el.doc_idx == driver.doc_idx`，
不相等就抛 `NoSuchElementException`（精确复刻现场 bug）。

```python
page, logs = run(items=3, speed=0.1)
assert "点击失败" not in "\n".join(logs)          # 不再有假失败
assert "下限执行" in "\n".join(logs)              # 低于 0.5s 有提示
assert "连点 A 三次都没任何弹窗" in "\n".join(logs)  # 发完后优雅停止
assert page.clicks["confirm"] == 3
assert page.clicks["A_blocked"] == 0              # 没在上轮弹窗未关时点 A
```

这类仿真的价值：本次全部改动的正确性在 macOS 上就验证完了，用户只需要在行内机上跑一次。

## 调参结论

- 间隔 **0.5–0.8s** 是这类 CTP 页面的实际极限，再快就是和页面动画赛跑，靠调参压不下去。
- 用户要更快只能改交互方式（比如找后端接口），不要承诺「再优化一下就能 0.2s」。
