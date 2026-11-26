# 提交后的「不可交互窗口」：不是 disabled 锁，是 frame 重载

2026-11-04 实测（某银行 CTP 页面，Edge 143，40 轮连跑）。这一篇是
`post-submit-busy-window.md` 的**结论升级**：那一版只知道「有 2–3 秒点不动」，
这一版用忙碌期探针查明了**它到底是什么**，并给出可检测的就绪信号。

## 1. 现象基线（真机 40 轮，不是仿真）

| 轮次 | 点主按钮 → 原生弹窗出现 |
|---|---|
| 第 1 轮（页面刚打开，没有前一笔提交） | **0.03s** |
| 第 2–40 轮 | 2.1 – 3.6s，平均 3.0s，每轮要点 3–4 次才弹 |

吞吐：40 笔 / 2 分 40 秒 ≈ **16 笔/分钟**。

## 2. 忙碌期报告（探针每 100ms 采样，只记变化的时刻）

```
t(ms) | A按钮 class          | disabled | 可见 | pointer-events | 遮罩层数 | readyState
     7ms | ctp-toolbar-image  | dis=0    | vis=1 | pe=auto        | mask=0  | complete
   180ms | ?                  | ?        | ?     | ?              | ?       | ?
   498ms | ctp-toolbar-image  | dis=0    | vis=1 | pe=auto        | mask=0  | complete
  1999ms | (空)               | dis=-1   | vis=-1| (空)           | mask=1  | complete
  2209ms | ctp-toolbar-image  | dis=0    | vis=1 | pe=auto        | mask=0  | complete
  3501ms | ?                  | ?        | ?     | ?              | ?       | ?
  ...
```

### 判读表

| 观察 | 含义 |
|---|---|
| `dis=0` 从头到尾没变 | **A 按钮从来没有被 `disabled`** —— 没有"禁用"信号可等，别去查 `disabled` |
| `mask=1` 且同一行 `dis=-1 / vis=-1`（元素查不到） | **frame 正在重载**，DOM 被整体替换 → 此刻点必然无效 |
| 一行全是 `?` | 那条 JS 跑不了（导航中 / 上下文失效）＝重载的另一个指纹 |
| `mask` 出现→消失，之间约 200ms | 重载完成，**这就是"可以再点"的信号** |

结论：**不是提交锁，是提交后页面重载一次**。重载期间点击被静默丢弃（不报错、不弹窗、
`disabled` 也不变），这正是「一枪必空、重点必成」的机制。

## 3. 用"重载完成"当门控，而不是盲等 N 秒

```python
def _mask_state(self, path):
    """当前可见遮罩层数；JS 都跑不了(典型: frame 正在重载) 返回 -1"""
    st = self._js(path, JS_BUSY)
    return int(st.get("mask", -1)) if isinstance(st, dict) else -1

def _wait_effect_or_reload(self, path, timeout=6.0):
    """等"点击生效"(弹窗出现) 或 "页面重载完成"。
    返回 'alert' / 'dialog' / 'reloaded' / None
    """
    t0 = time.time()
    saw_mask = False
    last_probe = 0.0
    while time.time() - t0 < timeout and not self._stop.is_set():
        if self._alert_present():          # 最便宜，先查
            return "alert"
        now = time.time()
        if now - last_probe >= 0.12:       # 遮罩/确认框查得稀一点，省命令
            last_probe = now
            n, _ids = self._dialog_count_fast()
            if n > 0:
                return "dialog"
            if path is not None:
                m = self._mask_state(path)
                if m > 0:
                    saw_mask = True
                elif saw_mask and m == 0:
                    return "reloaded"      # 遮罩出现→消失 = 重载完成
        self._stop.wait(0.05)
    return None
```

调用侧（主按钮循环）：

```python
while time.time() - t_a0 < A_MAX_WAIT and not self._stop.is_set():
    if not self._click_a(tag, quiet=(attempts > 0)):
        ...
    attempts += 1
    res = self._wait_effect_or_reload(getattr(self, "_a_path", None), A_FIRST_WAIT)
    if res in ("alert", "dialog"):
        kind = res; break
    if res == "reloaded":
        self._log(f"  · 页面重载完成 ({time.time()-t_a0:.1f}s) → 立刻重点A")
        continue                       # 重载一结束立刻再点，不等满窗口
```

参数：`A_FIRST_WAIT = 6.0`（一次尝试内"等到弹窗或等到重载"的窗口）、`A_MAX_WAIT = 15.0`
（整轮上限，含末尾"确认没有待办"）。

日志只报真数：

```
· A→弹窗 2.3s (共点 2 次; 提交后页面会重载一次, 重载完成才接受点击)
· 页面重载完成 (2.1s) → 立刻重点A
```

## 4. 三态返回的单元测试（不需要真页面）

`_wait_effect_or_reload` 是纯决策逻辑，把三个探测函数换成假实现就能钉死：

```python
a = object.__new__(sf.App)
a._stop = FakeStop()                       # wait() 睡 5ms 就返回
a._dialog_count_fast = lambda: (0, "")
seq = [0, 0, 1, 1, 0]                      # 遮罩时间线
a._mask_state = lambda path: seq.pop(0) if seq else 0
a._alert_present = lambda: False
assert a._wait_effect_or_reload([0], timeout=2.0) == "reloaded"

# 弹窗先出现 → 即使后面还有遮罩也返回 alert
# 一直没遮罩也没弹窗 → None（超时）
```

三条都要断言。这一步能在 1 秒内否掉"信号判据写错"，不用等用户打包。

## 5. 配套修复：JS 失败要作废 frame 上下文缓存

报告里的 `?` 行暴露了一个真 bug：为了省命令缓存了 `_ctx_now`（"我现在在哪个 frame"），
但 JS 执行失败（frame 重载中）时没作废缓存，后续会**一直在失效的上下文里跑 JS**，
继续返回 `?`，直到别的路径碰巧把它重置。

```python
def _js(self, path, script):
    try:
        if path is not None:
            self._goto_path(path)
        return self.driver.execute_script(script)
    except Exception:
        self._ctx_now = None      # 失败多半是 frame 正在重载 → 下次重新进入
        return None
```

## 6. 为什么"狂点实验"没量到这个窗口

狂点实验每个 trial 之前都有 `_dialog_gone_wait(2.0, reclick=True)` + `0.3s` + `_count_dialogs`，
等它真的开始点时页面早已重载完毕，于是量到"首点 350ms 就弹、重复 0"。

**探针的起点决定了它看不见什么。** 单次试验与持续循环结论冲突时，以**持续循环**为准
（那才是用户真实的运行形态）；并回头检查探针的预热/间隔是否把待测现象挡掉了。

## 7. 忙碌期探针本身（可复用）

```python
# 采样脚本要点：真提交一笔 → 每 100ms 读一次状态 → 只在"变化时"记一行
JS_BUSY = """
var el = document.querySelector("[id='<主按钮 id>']");
var out = {cls:"", dis:-1, vis:-1, pe:"", mask:-1, rs:document.readyState};
if (el) {
  out.cls = ((el.className || "") + "").slice(0, 60);
  out.dis = (el.getAttribute("disabled") !== null) ? 1 : 0;
  var r = el.getBoundingClientRect();
  out.vis = (r.width > 0 && r.height > 0) ? 1 : 0;
  out.pe = getComputedStyle(el).pointerEvents || "";
}
var n = 0, nodes = document.querySelectorAll(
  "[id^='ymPrompt'], [class*='mask'], [class*='Mask'], [class*='loading'], [class*='busy']");
for (var i = 0; i < nodes.length; i++) {
  var rr = nodes[i].getBoundingClientRect();
  if (rr.width > 0 && rr.height > 0) n++;
}
out.mask = n;
return out;
"""
```

- 报告写 exe 同目录 `忙碌期报告.txt`，`encoding="utf-8-sig"`（Windows 记事本不乱码）
- **只在状态变化时记一行**，否则 8 秒采样 = 80 行噪声
- 报告头写清字段含义，用户发文件回来你才不用猜
- 探针会**真的提交一笔**，界面说明里写「先拿测试单跑」

## 8. 报数纪律

- 仿真（假 driver、命令延迟按 8ms 估）只能验逻辑，**不能估吞吐**；本次"仿真 134ms/轮"
  与真机"3.0s/轮"差了 20 倍。
- 报吞吐前至少真机跑 20 轮，从日志取平均；写清数据来源。
- 报错了立刻认并给订正表——用户会据此调整预期，含糊比报错更糟。
