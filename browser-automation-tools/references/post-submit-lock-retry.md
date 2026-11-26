# 提交锁重试（post-submit lock retry）

面向「点按钮 → 关原生弹窗 → 点确定」这类循环：每一笔提交完成后，页面会短暂锁住工具栏，
锁着时对主按钮的点击**被静默丢弃**——不报错、不弹窗、`is_displayed()` 正常、`disabled` 属性也没有。
唯一能看出来的信号是「点了没反应」。

## 现场日志（某银行 MMTA，2026-11-04）

```
[14:39:12] ✓ [A] 已点击 (frame[1]) id=_ctp_toolbar_item_button_send
[14:39:12] 原生弹窗: ...  → 已点确定
[14:39:13] ✓ [C] 已点击 (frame[1]) id=ymPrompt_btn_0
[14:39:13] ═══ 第 1 轮完成 ═══
[14:39:14] ✓ [A] 已点击              ← 间隔 0.1s，点到了
[14:39:21] · A 点了但没弹出任何窗口 (第 1 次), 稍等重试   ← 空 7 秒
[14:39:22] ✓ [A重试1] 已点击 → 立刻出弹窗
```

判读：

- 第 1 轮不空 / 之后每轮都空 → 锁是**上一笔提交**引起的，不是间隔太小。
- 间隔 0.1 和 0.5 表现完全一致（都空）→ 更加确认不是速度问题。
- 那 6–7 秒是代码里 `_wait_effect(6.0)` 在等，**是我制造的**。

## 修复

```python
A_RETRY_TIMEOUT = 0.8   # 正常 340ms 弹窗；0.8s 无动静 = 被吞，重点
A_MAX_WAIT = 12.0       # 一轮上限；超过才判"没有待办"

kind = None
attempts = 0
t_a0 = time.time()
while time.time() - t_a0 < A_MAX_WAIT and not self._stop.is_set():
    tag = "A" if attempts == 0 else f"A重试{attempts}"
    if not self._click(BTN_A, tag, cache_key="_a_path", quiet=(attempts > 0)):
        miss += 1
        if miss >= 30:
            kind = "no_button"
            break
        self._stop.wait(0.5)
        continue
    miss = 0
    attempts += 1
    kind = self._wait_effect(A_RETRY_TIMEOUT)     # 返回 'alert'/'dialog'/None
    if kind:
        if attempts > 1:
            self._log(f"  · 点 A 第 {attempts} 次才生效 — 页面提交后锁了 "
                      f"{time.time() - t_a0:.1f}s (这次等到了)")
        break
    if attempts % 4 == 0:
        self._log(f"  · 还在等弹窗 (已点 {attempts} 次, {time.time()-t_a0:.1f}s)")

if kind == "no_button":
    ...  # 找不到按钮：停止
if not kind:
    self._log(f"连点 {attempts} 次、共等 {A_MAX_WAIT:.0f}s 都没弹窗 "
              f"→ 应该没有待处理的了, 自动停止")
    break
```

`_wait_effect(t)`：轮询「原生弹窗出现」或「目标弹窗出现」，出现即返回，不等满 t：

```python
def _wait_effect(self, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline and not self._stop.is_set():
        if self._alert_present():
            return "alert"
        el, _ = self._find(BTN_CONFIRM, skip_cancel=True)   # _find 只返回可见元素
        if el is not None:
            return "dialog"
        self._stop.wait(0.2)
    return None
```

## 探针也要改

旧探针只量「点A→弹窗」，锁期被算成页面延迟，得出"物理下限 0.9s、0.1s 不可能"的错误结论。
必须改成量「点几次才生效 + 累计等待」：

```python
taps = 0
t_alert = None
t_click = time.time()
while time.time() - t_click < A_MAX_WAIT and not self._stop.is_set():
    self._click(BTN_A, "A", quiet=True)
    taps += 1
    deadline = time.time() + A_RETRY_TIMEOUT
    while time.time() < deadline:
        if self._alert_present():
            t_alert = time.time()
            break
        time.sleep(0.02)
    if t_alert:
        break
# 报告行：f"点A {taps} 次才生效, 累计 {lat:.0f}ms"
```

汇总里加两列：`点A生效 平均N次`、`累计等待 平均Xms`。`N>1.2` 就在结论里点明"页面有提交锁，
程序已自适应，不需要调间隔"。

## 单测骨架（真实时间，不需要 Windows）

```python
LOCK = 0.45
sf.A_RETRY_TIMEOUT = 0.15      # 测试里缩短，保持"重试间隔 << 锁时长"的比例
sf.A_MAX_WAIT = 3.0

class Page:
    def click_A(self):
        self.taps += 1
        if time.time() < self.locked_until:      # 锁：点击被吞
            self.blocked_taps += 1
            return
        if self.items_left > 0:
            self.alert_at = time.time() + ALERT_LAT
    def click_confirm(self):
        self.confirms += 1
        self.items_left -= 1
        self.locked_until = time.time() + LOCK   # 提交完成 → 上锁
```

断言三条：

1. `page.confirms == 轮数`
2. 日志里有 `页面提交后锁了`（证明重试真的发生并记录）
3. `elapsed - A_MAX_WAIT < 轮数 × 1.0`（扣掉末尾"确认没待办"的等待；旧逻辑同场景 6s/轮）

## 坑

- **重试日志会刷屏**：0.8s 一次 → 一屏 `✓ [A重试N]`，真异常被淹。`quiet=(attempts > 0)`。
- **不要把重试超时也调大**：设成 5s 就是把 6s 换了个数字，用户看到的停顿一样。
- **`A_MAX_WAIT` 不能太小**：锁长会波动（0.2–0.6s，服务器慢时更长），末尾还要靠它判断
  "确实没有待办"，12s 是本次验证过的折中；再小会误判"已完成"而漏单。
- **重试是否会重复提交**：本次页面锁着时点击被直接丢弃，所以重点安全。若目标系统不丢而是排队，
  重点可能提交两次——上生产前用一笔测试单确认"重点不会重复提交"。
