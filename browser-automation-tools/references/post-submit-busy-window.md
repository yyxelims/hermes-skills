# 提交后的 2–3 秒忙碌期：怎么认、怎么量、别把它和 frame 作用域搞混

> **⚠ 结论已升级（同一 session 更晚一步）**：本篇只到「有 2–3 秒点不动 + 探针怎么量」。
> 后续忙碌期探针查明**它到底是什么**——不是锁、不是 `disabled`，而是**提交后 iframe 重载一次**，
> 可检测的就绪信号是「遮罩出现 → 消失」，实现是 `_wait_effect_or_reload()`。
> **先读 `post-submit-reload-signal.md`**（含报告判读表、三态返回、单元测试）；本篇作为
> 探针骨架与"为什么狂点实验看不见它"的对照保留。


2026-11-04 一轮"审批连点"调试的收尾结论。这个文件存在的意义是**防止下一次又把三种完全不同的
"点了没反应"混为一谈**，以及**别再用短仿真去承诺吞吐**。

## 一、证据：40 轮真机日志

同一版代码、间隔设 0.2s、连续跑 40 轮（每轮 = 点主按钮 → 原生 alert → 网页确认框）：

| 轮次 | 点主按钮 → 原生弹窗出现 | 期间点了几次主按钮 |
|---|---|---|
| 1 | **0.03s** | 1 |
| 2–5 | 3.2 – 3.6s | 3–4 |
| 10–40 | 2.1 – 3.4s | 3–4 |
| 汇总 | 平均 **3.0s** | 每轮 3–4 次 |

收尾汇总：`轮间间隔: 平均 2992ms, 最大 3597ms, 最小 2294ms (共 40 次)`、
`每轮总耗时: 平均 520ms`（这里的"本轮"从 alert 出现算起，所以不含忙碌期——两个数字别看混）。

读法：

- **第 1 轮 0.03s** = 页面刚打开、没有上一笔提交 → 没有忙碌期。
- **第 2 轮起 2–3s** = 每一笔提交之后，页面有一段时间不理会工具栏点击（不报错、不弹窗、无任何提示）。
- 忙碌期长度**不恒定**（2.1–3.6s），所以**不能写死 sleep**，只能"给足 + 观察"。

吞吐换算：40 笔 / 2 分 40 秒 ≈ **16 笔/分钟**，每轮 ≈3.3s 就是这台页面的下限。

## 二、和"原生 alert 的 frame 作用域"怎么区分

这两个坑的日志长得像，但一句话就能分开：

| 现象 | 归因 | 修法 |
|---|---|---|
| **点一次就有弹窗**，只是我等到超时也没看见；重试一枪"立刻"弹 | alert 只属于触发它的 frame，上下文被 `switch_to.default_content()` 切走后 `switch_to.alert` 永远报 NoAlert | `_alert_present()` / `_accept_alert_once()` 里先切回 `_a_path`（见 `references/frame-scoped-alert.md`） |
| **点了 2–3 秒才弹**，期间连点几次都毫无反应，且第 1 轮总是很快 | 页面提交后的忙碌期 | 第一次等待给到 4s（`A_FIRST_WAIT`），别用 1s 超时在里面反复点 |

判据一句话：**"第一枪是否立刻生效"。** 第 1 轮永远快 → 往忙碌期方向查；第 1 轮也慢 → 查别处。

## 三、为什么"狂点实验"会得出"没有锁"的错误结论

狂点实验（每 100ms 点一次、一弹窗就停）三次试验都是 `第 1 次点击、首点后 ~350ms、重复 0`。
看起来"没有锁"。但它的每个 trial 之前都有：

```python
self._dialog_gone_wait(2.0, reclick=True)   # 等确认框消失
self._wait_no_alert()
self._stop.wait(0.3)                        # accept 后给异步留时间
self._dialog_gone_wait(2.0, reclick=True)   # 再清一次
```

等到真正开点时，**距上一笔提交已经过去 1s 以上**，而 trial 里第一次成功点击发生在 `t0`，
如果忙碌期在 `t0` 之前就结束了，量到的就是"首点即中"。

**结论：探针的起点决定了它看得见什么。** 单次试验（trial）与持续循环（loop）结论冲突时，
**以持续循环为准**——那才是用户真实的运行形态。要验证忙碌期，必须让探针从"刚点完确定"
那一刻开始计时，中间不做任何 settle 等待。

## 四、参数

```python
A_FIRST_WAIT   = 4.0   # 第一次点主按钮后等弹窗：必须 > 忙碌期（实测 2–3s）
A_RETRY_TIMEOUT = 4.0  # 后续重点的等待窗口，同样给足
A_MAX_WAIT     = 12.0  # 一轮最多试这么久；超了才是"确实没有待办"
```

日志措辞（别再把重试次数报成异常）：

```python
waited = time.time() - t_a0
if waited >= 1.2:
    self._log(f"  · A→弹窗 {waited:.1f}s (页面提交后的忙碌期, 共点 {attempts} 次)")
```

反例（本次踩过）：`A_RETRY_TIMEOUT=1.0` → 忙碌期内每 1s 白点一次，日志刷出
`· 第 4 次点击才见到弹窗 (累计 3.3s)`，用户看到的是"怎么老要点好几次"。

反例 2（更危险）：`A_RETRY_TIMEOUT=0.2` 小于页面正常延迟 → 会在弹窗出现前重复点主按钮，
若应用会排队就是**重复提交**。窗口必须大于页面延迟（见 pitfall 41）。

## 五、忙碌期探针：找"什么时候才允许下一次点击"的可检测信号

目的：如果页面在放开的那一瞬间有 DOM 变化，就能卡着那一刻点，省掉 0.3–0.5s 的尾巴。
没有变化 = 3.3s 是物理下限，别再调参。

```python
JS_BUSY = """
var el = document.querySelector("[id='_ctp_toolbar_item_button_send']");
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

worker 骨架（**从"刚点完确定"开始采样**，每 100ms 一次，只记录变化的时刻，避免刷屏）：

```python
def _busy_worker(self):
    rows = [f"忙碌期报告 {datetime.now():%Y-%m-%d %H:%M:%S}", ""]
    p_a = getattr(self, "_a_path", None) or self._probe_path()
    if p_a is None:
        return self._log("✗ 找不到主按钮")

    # 真提交一笔
    self._click_a("A")
    t0 = time.time()
    while time.time() - t0 < 6.0:
        if self._alert_present():
            break
        self._stop.wait(0.05)
    self._accept_alert_once()
    ok, t_c = self._wait_click_confirm(6.0)
    if not ok:
        return self._log("✗ 没点到确定")

    rows.append("t(ms) | class | disabled | 可见 | pointer-events | 遮罩层数 | readyState")
    start, prev = time.time(), None
    while time.time() - start < 8.0 and not self._stop.is_set():
        st = self._js(p_a, JS_BUSY) or {}
        key = (st.get("cls"), st.get("dis"), st.get("mask"), st.get("pe"))
        if key != prev:                       # 只在变化时落一行
            rows.append(f"{(time.time()-start)*1000:6.0f}ms | {st.get('cls')} | "
                        f"dis={st.get('dis')} | vis={st.get('vis')} | "
                        f"pe={st.get('pe')} | mask={st.get('mask')} | {st.get('rs')}")
            self._log("  " + rows[-1]); prev = key
        self._stop.wait(0.1)

    with open(os.path.join(APP_DIR, "忙碌期报告.txt"), "w", encoding="utf-8-sig") as f:
        f.write("\n".join(rows))
```

报告写成 **exe 同目录 + `utf-8-sig`**（Windows 记事本才不乱码），让用户发文件而不是描述屏幕。
按钮说明里必须写「只提交 1 笔，先拿测试单跑」。

判读：

| 报告长相 | 结论 | 动作 |
|---|---|---|
| 某个字段在 2100–3200ms 处翻转（`dis=0`→`dis=1`→`dis=0`、`mask` 2→0、`pe` none→auto） | 有可检测信号 | 用该字段做门控，等到翻转立刻点，省 0.3–0.5s |
| 8 秒内每行都一样（`dis=0 vis=1 pe=auto mask=0` 全程不变） | 页面完全没有可检测信号 | 3.3s 是物理下限，别调参；只能并行多开/多账号 |
| 采样报错 / 全字段 `-1` | `_a_path` 过期或 JS 抛错 | 先 `_probe_path()` 重取路径，再跑一次 |

## 六、汇报纪律

- **仿真只验逻辑，不估吞吐。** 本次用 3 轮假 driver 仿真算出"134ms/轮"并当成承诺给用户，
  真机 40 轮是 3.0s/轮。给数时标明来源，别混。
- **用户说"明显更大"时，先认账再算。** 正确开场："我上次报的 134ms 是空闲段，实际每轮 3.2s，
  这个数我之前报错了"，然后再给订正后的表。
- **报"每分钟多少笔"之前，必须真机 ≥20 轮取平均**；否则宁可只说"还没量准，先跑 20 轮"。
