# 原生 alert 的 frame 作用域 —— 「点了没反应、等 6 秒、重点就成」的真因

2026-11-04 在某银行 CTP 页面（按钮和弹窗都在 `frame[1]`）上定位。这条坑吃掉了 4 轮返工，
且**推翻了本 skill 曾经写过的一句结论**（"alert 是浏览器级弹窗，检测/accept 不受当前 frame 影响"）。

## 症状（认准这个形态）

```
[14:39:13] ═══ 第 1 轮完成 ═══
[14:39:14]   ✓ [A] 已点击            ← 点了
[14:39:21]   · A 点了但没弹出任何窗口 (第 1 次), 稍等重试   ← 空 6–7 秒（全是我在等）
[14:39:22]   ✓ [A重试1] 已点击
[14:39:22]   原生弹窗: 非结算性同业存款业务…               ← 重点一下"立刻"就有了
```

三个特征同时出现就是它：

1. **每轮第一枪必空，重试一枪必成**（间隔调到多大都一样）；
2. 空白时长 ≈ 你设的 `_wait_effect` 超时值（6s → 就空 6s，改成 0.8s → 就空 0.8s，
   但**改成 0.2s 就变成"每轮点 6 次才成功"**，看着像"点击被吞/页面有提交锁"）；
3. 第 1 轮例外地正常（因为那是整个流程的第一枪，没有"上一轮切走上下文"这个前置动作）。

## 为什么

Selenium 的原生 alert 是**属于某个 browsing context（frame）**的。
弹窗是在 `frame[1]` 里点按钮触发的，所以只有 driver 的当前上下文**在 `frame[1]` 里**时，
`driver.switch_to.alert` 才看得见它。

而等待循环长这样：

```python
while time.time() < deadline:
    if self._alert_present():            # 这次可能在 frame[1]，能看到
        return "alert"
    el = self._find(BTN_CONFIRM)         # ← 这里 switch_to.default_content() + 遍历 frame
    self._stop.wait(0.2)                 #   循环结束时上下文停在 default_content
```

弹窗要 350ms 才出现；`_find` 早就把上下文切回 `default_content` 了。**从那一刻起
`switch_to.alert` 永远抛 `NoAlertPresentException`**，于是等满超时；重试那一枪重新 `_goto_path`
进 `frame[1]`，弹窗立刻可见 —— 这就是"重点一下就成"的假象。

## 修法

把"看弹窗"统一收口到一个永远切回触发 frame 的函数里：

```python
def _alert_here(self):
    try:
        return self.driver.switch_to.alert
    except NoAlertPresentException:
        return None
    except Exception:                     # UnexpectedAlertPresentException 也说明有弹窗
        try: return self.driver.switch_to.alert
        except Exception: return None

def _alert_go_a_frame(self):
    p = getattr(self, "_a_path", None)    # 点主按钮成功时缓存下来的 frame 路径
    if p is None: return False
    try:
        self._goto_path(p)
        return True
    except Exception:
        return False

def _alert_present(self):
    if self._alert_here() is not None: return True
    if self._alert_go_a_frame():
        return self._alert_here() is not None
    return False

def _accept_alert_once(self):
    a = self._alert_here()
    if a is None:
        self._alert_go_a_frame()
        a = self._alert_here()
    if a is None: return False
    try:
        a.accept(); return True
    except Exception:
        try: a.dismiss(); return True
        except Exception: return False
```

要求：`_wait_no_alert`、诊断、测速/狂点探针，**凡是判断弹窗的地方都调 `_alert_present()`**，
禁止直接写 `driver.switch_to.alert`。

## 顺带修掉的性能坑

同一次诊断里发现：狂点报告 `点击时间点(ms)=[378]` —— 那 378ms 不是页面延迟，是
**`_find` 遍历 4–5 个 frame × 每条选择器**的开销。小间隔下它就是主要成本。

```python
def _paths_to_try(self, prefer=None):
    paths = [prefer] if prefer is not None else []
    paths += [p for p in self._frame_paths() if p != prefer]
    return paths

# _click_any 里命中后 setattr(self, cache_key, path)，下次 prefer 它
self._find(sel, prefer=getattr(self, cache_key, None) if cache_key else None)
```

实测把单次点击从 ~380ms 压到几十毫秒。**注意**：`prefer` 只是"先试"，找不到仍要退回全树扫描，
否则页面改版后会出现"昨天还能点、今天找不到"的幽灵 bug。

## 狂点实验：怎么在 30 秒内证伪"有锁"

```
试验1: 第 1 次点击、首点后 379ms 弹出 | 点击时间点(ms)=[378] | 确认框共点 1 次, 重复 0 个
试验2: 第 1 次点击、首点后 345ms 弹出 | 点击时间点(ms)=[344] | 确认框共点 1 次, 重复 0 个
试验3: 第 1 次点击、首点后 352ms 弹出 | 点击时间点(ms)=[351] | 确认框共点 1 次, 重复 0 个
```

读法：**每轮都是"第 1 次点击"生效**，所以没有锁、也没有"点击被吞"；
`首点后 Xms` ≈ `点击时间点` 说明 X 全是我自己点击的开销；
`重复 0` 说明高频点击不会被应用排队（不构成重复提交风险），重试间隔可以放心压到 0.2s。

只要出现"`第 1 次点击` + `重复 0`"，就不要再往"锁/间隔"方向改代码了，直接去查 alert 的 frame 作用域。

## 桩测试：把 frame 作用域写进假 driver

假 driver 里让 `switch_to.alert` **只在特定 frame 路径下可见**，就能在 macOS 上离线复现这个 bug：

```python
A_PATH = [0]                      # A 按钮和弹窗都在 frame[0]

class Switch:
    @property
    def alert(self):
        if self.d.alert_up and self.d.path == A_PATH:   # ← 关键这一行
            return Alert(self.d)
        raise NoAlert()

# find_elements 也要按 doc 隔离：不在 frame[0] 里就查不到页面元素
# frame 树查询（"iframe, frame"）例外，任何 doc 都要能查，否则 _goto_path 直接失败
```

断言（旧逻辑必挂、新逻辑必过）：

- 完成轮数 == 期望轮数，且**每轮都是第 1 次点击命中**（日志里不应出现"第 N 次点击才见到弹窗"）；
- 全程耗时远小于 `轮数 × 等待超时`（旧逻辑 3 轮 ≥ 18s，新逻辑 2.6s 含末尾判定）；
- `_probe_state` 换成"一调用就抛异常"后仍能跑完 —— 证明主循环不再依赖 JS 判遮罩。

## 排查顺序（下次别再倒着来）

1. **alert 的 frame 作用域**（本节）——症状：第一枪必空、重点必成、空白≈超时值；
2. **超时值本身**——所有耗时都≈你设的超时，说明等的东西没成立；
3. **动作是否生效**——确定按钮到底关没关（`_dialog_gone_wait` 用 `is_displayed` 判，别用 JS 数节点）；
4. **才轮到**间隔下限 / 提交锁 / 页面延迟。

倒着查的代价：本次先怀疑"间隔太快"，再怀疑"提交锁"，两个假设各改了一版代码，全部作废。
