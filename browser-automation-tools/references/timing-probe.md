# 时序探针：把「间隔调小就出错」从调参问题变成测量问题

## 何时用

用户说「间隔调到 0.5s 以下就报错」「能不能压到 0.1」「到底哪里的问题」时。

**不要**去猜一个魔法数字（0.3？0.5？0.8？），也不要只回「页面就这么快」。这类问题有确定答案，
可以量出来：失败几乎总是「上一轮弹窗遮罩还没消失就点了主按钮」。

行内电脑上试错成本极高（每次改都要重新打包 + 拷进去），所以一次把数据采全，让用户跑一次、
发一个文件回来。

## ⚠️ 终局修正（2026-11-04 用户实测，推翻本篇下面两处结论）

1. **判「弹窗关没关」只看「确认按钮是否可见」（Selenium `is_displayed`），不要用 JS 数节点/遮罩。**
   本篇那套 `[id^='ymPrompt']` 计数只能当**旁证**，绝不能当门控：关闭后节点仍在 DOM，
   祖先 `display:none` 还会让元素自身 computed display 保持 `inline-block`。
2. **真因不是判据，是动作没成功。** 用户看着屏幕说「确定按钮一直在」——确定压根没被点掉，
   所以遮罩永远不消失，门控每轮等到超时（那 1–3s 停顿是自己加的）。日志只能证明"我点了"，
   不能证明"点成功了"。
3. **0.1s 是能跑的。** 之前 0.1 档的失败样本（`v=1`）是**上一轮遗留弹窗**挡住的，不是间隔太小。
   判据换成"按钮是否还在"之后，0.1s 与 0.2s 都能通，用户实测"三个点击都正常、很快"。
4. **正确形态**：主循环里不放 JS 门控；开工靠"排干可见确认按钮"，轮末
   `_dialog_gone_wait(1.5, reclick=True)` 校验并补点。探针报告必须记「补点次数 / 按钮是否消失」，
   这是唯一能区分"页面慢"和"没点掉"的字段。
5. **还有第二道门：提交锁。** 即使弹窗都关干净了，每轮**第一枪点主按钮仍会被静默丢弃**
   （上一笔提交后页面锁住工具栏，不报错不弹窗）。表现是「一枪必空、重点必成」，旧版用一个
   6 秒超时去等，于是每轮白停 6 秒——用户说的"每轮之间格很久"。探针必须量
   **「点几次才生效 + 累计等待」**，否则锁期会被算进"页面延迟"，得出"0.1s 物理不可能"的错误结论。
   修复与单测骨架见 `references/post-submit-lock-retry.md`。

## 四段耗时模型

一轮 A→B→C 里能测量的四段：

| 段 | 含义 | 谁决定的 |
|---|---|---|
| `A→弹窗` | 点主按钮到原生 alert 出现 | 后台接口响应 |
| `原生弹窗→确定可点` | accept 到 DOM 弹窗确定按钮可点 | 前端渲染 |
| `点确定→遮罩消失` | 点确定到遮罩真的没了 | 关闭动画 + 框架清理 |
| `点击时 v` | 点主按钮那一刻**可见遮罩层数** | 前一轮是否还没清完 |

**`v > 0` 的失败 = 确诊「点空了」**；`v == 0` 还失败 = 存在第二道锁（工具栏被禁用等），
报告里同时记按钮 `disabled` / `class` 状态来区分。

## 收集遮罩状态的 JS（一次调用拿全）

```python
OVERLAY_SEL = "[id^='ymPrompt']"     # 弹窗容器前缀；框架不同就换这里

PROBE_JS = """
var sel = arguments[0] || "";
if (!sel) { return {v: -2, ids: "", r: document.readyState}; }
function rendered(el) {
  // ★ 必须用 getClientRects 判"真正占了布局"。
  // getComputedStyle(el).display 只看元素自身：祖先 display:none 时，
  // 元素自己的 computed display 仍然是 inline-block → 永远判成"可见"。
  // 后果：_wait_overlay_gone 每轮都等到超时（实测报告里"遮罩消失 3020ms"
  // 就是 3s 超时值，不是真实耗时），程序比改之前还慢。
  if (!el.getClientRects().length) return false;
  var s = getComputedStyle(el);
  if (s.visibility === 'hidden') return false;
  if (parseFloat(s.opacity || 1) <= 0.01) return false;
  return true;
}
var nodes = document.querySelectorAll(sel), vis = [], i, r;
for (i = 0; i < nodes.length; i++) {
  if (rendered(nodes[i])) {
    r = nodes[i].getBoundingClientRect();
    vis.push((nodes[i].id || nodes[i].tagName) + ':' +
             Math.round(r.width) + 'x' + Math.round(r.height));
  }
}
return {v: vis.length, ids: vis.slice(0, 3).join(' | '), r: document.readyState};
"""
```

要点：
- **判"可见"用 `getClientRects().length`（或 `offsetWidth||offsetHeight`），不要用 `getComputedStyle().display`。**
  这是本次唯一一个"探针自己在骗人"的坑，一次错误判断让每轮白等 3 秒。
- 顺便把 `宽x高` 记进 `ids`：`ymPrompt:1264x25 | ymPrompt_btn_0:46x25` 这种输出能一眼看出
  命中的是容器还是按钮、是否 0×0 的幽灵节点。
- 判「关完了」要判**容器**；弹窗**按钮**（`ymPrompt_btn_*`）关闭后仍留在 DOM（`is_displayed()=False`）。
- 这个调用要便宜（单次 `execute_script`，5–15ms），才能在 20ms 轮询里用。
  用 `_find()`（扫 4 个 frame）去轮询是自找麻烦，一次 100–300ms。

### 先验证探针本身（本地就能做，不用行内电脑）

夹具见 `templates/overlay_probe_fixture.html`（容器默认 `display:none`，`showDialog/hideDialog`
切 class）。写一个 20 行 HTML：容器 `#ymPrompt` 默认 `class="hidden"`（`display:none`），里面放
`<input id="ymPrompt_btn_0" value="确 定">`，再给两个 `window.showDialog/hideDialog` 切 class。
用浏览器打开这个 `file://` 页面，把同一份 JS 在关闭/弹开两种状态下各跑一遍：

```
关闭 → {"v": 0, "ids": ""}
弹开 → {"v": 2, "ids": "ymPrompt:1264x25 | ymPrompt_btn_0:46x25"}
```

旧逻辑在「关闭」状态会返回 `v:1`（因为按钮自身 display 没变），新逻辑返回 0 —— 这一条断言
就能在把 exe 拷进行内电脑之前，证明探针和门控是对的。

## 轮询封装的两种用途

```python
def _probe_state(self, path=None):
    """在指定/当前 frame 里读遮罩状态"""
    if not self.overlay_sel:
        return -2, "", ""                     # -2 = 没配置，未知
    try:
        if path is not None:
            self._goto_path(path)             # 必须切到元素所在 frame
        r = self.driver.execute_script(PROBE_JS, self.overlay_sel) or {}
        return int(r.get("v", -1)), "", r.get("ids", "")
    except Exception:
        return -1, "", ""

def _wait_overlay_gone(self, path, timeout=3.0, poll=0.02):
    """等遮罩消失；正常循环用它替代固定 sleep —— 这才是间隔能压下去的关键"""
    if not self.overlay_sel:
        return True, 0.0                      # 没配选择器就不阻塞
    t0 = time.time()
    while time.time() - t0 < timeout and not self._stop.is_set():
        v, _, _ = self._probe_state(path)
        if v <= 0:                            # 0=没了, -1=读不到也不阻塞
            return True, time.time() - t0
        time.sleep(poll)
    return False, time.time() - t0
```

## 扫描式测速（用户点一下按钮）

```python
PROBE_GAPS = [0.1, 0.2, 0.3, 0.5]
PROBE_ROUNDS = 5

for gap in PROBE_GAPS:
    for i in range(PROBE_ROUNDS):
        self._wait_overlay_gone(path, 3.0)          # 从干净状态开始
        v0, _, ids0 = self._probe_state(path)       # 点击前那一刻的遮罩数
        t_click = time.time(); self._click(BTN_A, quiet=True)
        t_alert = 等 alert 出现(最多 2.5s, 20ms 轮询)
        if t_alert is None:
            记一条失败(v0, ids0, 按钮状态); continue
        alert.accept(); t_btn = 等确定按钮可点
        self._click_confirm(quiet=True); t_conf = time.time()
        self._wait_overlay_gone(path, 3.0)
        # ★ 关键：下一轮点主按钮距「点确定」只隔 gap 秒 —— 复现小间隔
        rest = gap - (time.time() - t_conf)
        if rest > 0: time.sleep(rest)
```

> **上面对主按钮只点了一次，是旧版探针的最后一个缺陷。** 提交锁存在时第一枪必空，
> 探针会把整段锁期记成"A→弹窗 340ms/467ms"之类的抖动，看不出真相。正确写法：主按钮改成
> 「0.8s 内没弹窗就重点，最多 12s」，并记录 `taps`（点几次才生效）与累计等待，
> 报告里输出「点A N 次才生效, 累计 Xms」；`taps` 平均 >1.2 就在结论里点明"页面有提交锁"。
> 代码见 `references/post-submit-lock-retry.md`。

结论行怎么写（用户能看懂、你能据以定方案）——**用数值算，不要从字符串里切**：

```python
all_clear, timeout_cnt = [], 0          # 收集每轮「点确定→遮罩消失」的毫秒
...
if max(all_clear) >= PROBE_TIMEOUT * 1000 - 100:
    report.append(f"⚠ {timeout_cnt} 次卡在超时 {PROBE_TIMEOUT}s，说明选择器命中了关不掉的节点，"
                  "遮罩判断不可靠，只能用固定间隔")
else:
    report.append(f"结论: 遮罩消失最长 {max(all_clear):.0f}ms → 间隔小于它会点空")
    report.append(f"建议: 间隔 >= {max(0.2, round(max(all_clear)/1000 + 0.05, 2))}s")
```

> 早期版本用 `l.split("最大")[1]` 从汇总字符串里抠数字，结果输出「最长约 8ms」这种
> 自相矛盾的结论（把 `12ms` 里的 `1` 和 `2` 拆开了）。数值留在 list 里，别回头解析文本。

## 本次实测（某银行 CTP，Edge 143，2026-11-04）

25 轮数据，每档 5 轮的耗时几乎完全一致：

| 段 | 实测 | 说明 |
|---|---|---|
| 点主按钮 → 原生 alert | **340ms**（0.2/0.3/0.5 三档 344/344/341） | 后台接口延迟，**与间隔无关** |
| accept → 确定按钮可点 | **540ms**（534/542/539） | 前端渲染，**与间隔无关** |
| 点确定 → 确定按钮消失 | 百毫秒级 | 报告里 3000ms 是超时值；按钮压根没点掉时该值必然等于超时 |
| 单轮物理下限 | **≈0.9s** | 前两段之和 |

由此得到的判读原则：

1. **间隔参数只能影响"两轮之间的空档"，压不掉页面固有延迟。**
   设置 0.1 还是 0.5，单轮最短都是 ~0.9s；0.5s 设置下实测 1.0–1.3s/轮，其实已经贴着地板。
   给用户的预期要这么算：`吞吐 ≈ 1 / (0.9 + gap)`，0.5→0.77 单/秒，0.2→0.9 单/秒。
   **别承诺 5 倍提速。**
2. **小间隔的失败点很具体，但别急着下"物理做不到"的结论**：`gap=0.1` 时 5 轮 3 败，其中 2 轮
   日志 `v=1` —— 那是**上一轮遗留的弹窗**（当时确定没点掉），不是 0.1s 太快。判据修好后 0.1s 可用。
3. **报"做不到"时要同时给出"已经做到的最优解"**：门控（等遮罩）+ frame 路径缓存让
   0.2s 可用，比原来固定 0.5s 快 ~25%，这就是天花板；再快只能改交互方式（绕开原生 alert
   直接调接口），不是调参能解决的。

## 报告文件：必须落盘，别只打在 GUI 里

行内电脑上从 Tkinter 日志框里复制中文很痛苦，直接写文件让用户发：

```python
fp = os.path.join(APP_DIR, "测速报告.txt")      # exe 同目录
with open(fp, "w", encoding="utf-8-sig") as f:   # ★ BOM，Windows 记事本才不乱码
    f.write("\n".join(report))
```

报告头写「字段说明」，用户看不懂字段就不会配合：

```
测速报告 2026-11-04 14:14:42
URL: ...
A按钮位置: frame[1]
字段说明: v=点击时可见弹窗层数(>0 说明遮罩还在) / A→弹窗=点A到原生弹窗出现 / 清空=点确定到遮罩消失
```

**测速会真的点按钮**——启动前在日志和界面上一句话说明「注意先拿一笔测试单跑」。

## 测出来的结论怎么变成代码

1. **两轮之间：判「确认按钮还在不在」，不是判遮罩**。`_dialog_gone_wait(1.5, reclick=True)`
   放在点确定之后；还看得见就补点一次，并把补点次数写进日志。判据用 Selenium 可见性，不用 JS。
   （早期版本写成 `_wait_overlay_gone` 门控 → 按钮没点掉时永远超时 → 每轮白等 1–3s。）
2. **缓存按钮所在 frame 路径**（`_click(..., cache_key="_a_path")`）。每轮重扫 4 个 frame
   本身就是 100–300ms 的纯浪费，小间隔下这是主要开销。
3. **兜底下限降到 0.1**（`MIN_GAP`），滑块 `from_=0.1`。正确性由遮罩门控保证，不再靠下限。
4. 脱敏版没配 `dialog_container` 时，JS 探测只当参考、不参与门控（`_wait_overlay_gone` 直接放行）。

## 坑

- **`getComputedStyle().display !== 'none'` 判可见是错的**（祖先 `display:none` 时元素自身
  仍报 `inline-block`）→ 探针恒定认为"遮罩还在"。用 `getClientRects()`。**即便判对了，也别拿它
  当门控**——见开头「终局修正」：关没关只看确认按钮是否可见。
- **测量值等于超时值 = 探针坏了，不是页面慢**。看到一堆 `3000ms / 3020ms / 3038ms` 就该怀疑
  自己，而不是去调参。本次就是用户把报告发回来才发现。
- **别拿 `visible=False` 的弹窗按钮当「还没关完」的判据**，它永远留在 DOM 里 → 死等超时。
- **20ms 轮询里不要调 `_find()`**，那会扫全部 frame；先拿到 path 再单点 `execute_script`。
- **探针里的等待可以用 `time.sleep()`**（它自己不响应停止键），主循环仍必须 `stop_event.wait()`。
- **测速超时值别太长**：每档 5 轮 × 4 档 × (2.5s 等弹窗 + 3s 等清空) 最坏几分钟，用户会以为卡死。
  真实耗时是百毫秒级，`PROBE_TIMEOUT=1.5` 足够。
- 报告写失败（目录只读）不能让整个探针崩——`try/except` 包住，日志里说一声即可。
- 别漏了「测速会真的提交单据」，启动前提醒先拿一笔测试单跑。
