# 狂点实验：用点击频次量「锁」，同时排查重复提交风险

适用场景：用户说「每轮之间格很久」已经修过一轮，仍然快不起来；或用户直接否认你关于
「页面有提交锁 / 间隔太小」的推断（原话：「我觉得你应该大胆试试，就我观察，应该是没有所谓的
锁定窗口的，你可以做个测试疯狂点」）。

原则：**用户在屏幕前看到的，优先于你从日志做的推断。** 有分歧就做一个能出数字的实验，
不要写第二段推理。

---

## 1. 实验设计

| 参数 | 值 | 理由 |
|---|---|---|
| `HAMMER_INTERVAL` | 0.1s | 足够密，能夹住任何 >100ms 的锁 |
| `HAMMER_MAX` | 8s | 单次试验上限，防止无人值守时点爆 |
| `HAMMER_TRIALS` | 3 | 3 次就能看出波动 |
| 停手条件 | **一出现原生弹窗立刻停** | 绝不连续点到弹窗满天飞 |

三个要记录的数值：

1. `taps` —— 第几次点击生效（>1 说明前面的被吞）
2. `dt = 首点 → 弹窗出现` 的毫秒数（这才是真正的"锁长/延迟"）
3. `stamps` —— 每次点击相对首点的毫秒数组，例如 `[0, 107, 219]`
4. `dupes` —— 弹窗关掉后又多冒出几个确认框 = **重复提交风险**

## 2. 代码（直接搬）

```python
HAMMER_INTERVAL = 0.1
HAMMER_MAX = 8.0
HAMMER_TRIALS = 3

def _hammer(self):
    if not self.driver:
        self._log("先点「启动浏览器」"); return
    self._log(f"狂点实验: 每 {HAMMER_INTERVAL*1000:.0f}ms 点一次, 一出现弹窗立刻停手")
    self._log("⚠ 会真的提交, 请先拿一笔测试单跑")
    self._guarded_thread(self._hammer_worker).start()

def _hammer_worker(self):
    report = [f"狂点报告 {datetime.now():%Y-%m-%d %H:%M:%S}",
              f"URL: {self.driver.current_url}", ""]
    for trial in range(HAMMER_TRIALS):
        if self._stop.is_set(): break

        # 清场：判两次，中间留 0.3s 给"异步冒出来的确认框"
        self._ensure_window()
        self._dialog_gone_wait(2.0, reclick=True)
        self._wait_no_alert()
        self._stop.wait(0.3)
        self._dialog_gone_wait(2.0, reclick=True)

        t0 = time.time(); taps = 0; t_alert = None; stamps = []
        while time.time() - t0 < HAMMER_MAX and not self._stop.is_set():
            self._click(BTN_A, "狂点", quiet=True)      # 必须 quiet，否则刷屏
            taps += 1
            stamps.append((time.time() - t0) * 1000)
            deadline = time.time() + HAMMER_INTERVAL
            while time.time() < deadline:
                if self._alert_present():               # 只查 alert，最便宜
                    t_alert = time.time(); break
                time.sleep(0.01)
            if t_alert: break

        if t_alert is None:
            report.append(f"试验{trial+1}: 狂点 {taps} 次 / {HAMMER_MAX:.0f}s 一次弹窗都没有")
            self._dialog_gone_wait(2.0, reclick=True)
            continue

        dt = (t_alert - t0) * 1000
        atext = ""
        try: atext = (self.driver.switch_to.alert.text or "")[:24]
        except Exception: pass
        self._accept_alert_once()
        self._stop.wait(0.3)                            # ← 关键：等确认框异步出现

        gone, waited, extra = self._dialog_gone_wait(3.0, reclick=True)
        dupes = max(0, extra - 1)                       # 第一下是本轮本该点的
        report.append(
            f"试验{trial+1}: 第 {taps} 次点击、首点后 {dt:.0f}ms 弹出 | "
            f"点击时间点(ms)={[round(s) for s in stamps]} | "
            f"确认框共点 {extra} 次, 重复 {dupes} 个, 残留 {self._count_dialogs()} | 弹窗: {atext}")
        if dupes > 0:
            self._log(f"  ⚠ 多出 {dupes} 个确认框 — 点击被排队了, 重试必须放慢")

    write_report(APP_DIR, "狂点报告.txt", report)   # encoding="utf-8-sig"
```

## 3. 判读表

| 观察 | 结论 | 动作 |
|---|---|---|
| 每轮 `首点后 ≈ 350ms`、`taps ≤ 4`（0.1s 档下正常）、`重复 0` | **没有锁**，首点即生效 | `A_RETRY_TIMEOUT` 压到 **0.2s**；之前那次"空 6 秒"另有原因（多半是上轮残留弹窗挡住） |
| `首点后` 随轮次递增到 1s 以上 | 有提交锁 | 重试间隔取锁长一半；用重试自适应，别写死 sleep |
| `重复 N > 0` | **点击会排队 → 会重复提交单据** | 立刻把重试改成"点一次只等不重点"，并把该结论告诉用户 |
| 狂点 8s 无弹窗 | 页面用别的方式拒绝 | 查 A 是否 `disabled`/`class` 含 `disab`；查是否弹了自己没识别的提示 |

## 4. 两个必踩的坑

### 4.1 accept 之后立刻判断「是否已消失」= 假阴性

确认框是**关了原生弹窗之后**才创建的，间隔几十到几百毫秒。立刻判断会得到
「没有可见确认框」→ 被当成"已经清干净"，于是：

- 清理判断提前返回，**上一轮的确认框**留到下一轮，把主按钮挡住
- 症状极具迷惑性：`试验2: 狂点 28 次 / 3s 一次弹窗都没有`

修法：清理型判断**判两次**，中间 `wait(0.3)`。判断"是否还在"（收尾校验）不受影响，
判断"是否已经没了"（开局清理）必须留缓冲。

### 4.2 「补点 1 次」不是重复

`_dialog_gone_wait(reclick=True)` 会把**本轮本该点的那一次**也计入 `clicks`。
重复数必须 `max(0, clicks - 1)`，否则每个正常试验都报「有重复提交风险」，结论直接反。

## 5. 假页面桩（本地验证实验本身，不用打包）

两个模型，都用 `time.time()` 真实时间，`wait()` 真的 sleep（可以把参数调小让测试快）：

```python
# 模型 A：不排队 —— 已有待处理时再点直接忽略
def click_A(self):
    if self.pending == 0 and not self.dlg_up:
        self.pending = 1
        self.alert_at = time.time() + LAT

# 模型 B：排队 —— 每次点击都加一个待办（重复提交）
def click_A(self):
    self.pending += 1
    if self.alert_at is None:
        self.alert_at = time.time() + LAT
```

断言（模型 A）：

```python
assert 200 <= int(首点后ms) <= 700      # 应 ≈ LAT*1000
assert "重复 0 个" in body
assert "被排队了" not in body
```

## 6. 交付话术

- 报告写 exe 同目录 `狂点报告.txt`，**`encoding="utf-8-sig"`**（Windows 记事本不乱码）
- 按钮/日志里明写「**先拿一笔测试单跑**」——这个实验会真的提交
- 让用户发文件而不是截图；报告里带 `判读:` 几行，用户自己也能看懂结论
