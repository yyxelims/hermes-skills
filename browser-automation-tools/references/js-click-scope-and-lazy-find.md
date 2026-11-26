# JS click 的适用边界 + 懒扫 `_find`（2026-11-04 真机日志定案）

提速改造里唯一一次**只有真机能暴露**的翻车：把工具栏按钮的点击从 Selenium 换成
`el.click()`，功能静默失效。

## 1. 症状：第 1 轮好、之后每轮"点了没反应"

```
[15:37:49.781] ✓ [A] 已点击 (frame[1]) id=_ctp_toolbar_item_button_send   ← 第1轮
[15:37:49.816]   原生弹窗: 非结算性同业存款业务为总行专营业务...
[15:37:50.020] ✓ [C] 已点确定 (frame[1]) id=ymPrompt_btn_0
[15:37:50.058] ═══ 第 1 轮完成 ═══ (本轮 256ms)

[15:37:51.327] ✓ [A] 已点击 (frame[1])                      ← 第2轮：没有 id= ！
[15:37:55.521]   · 还在等弹窗 (已点 4 次, 4.2s)
[15:38:04.127]   · 还在等弹窗 (已点 12 次, 12.8s)
[15:38:04.143] 连点 12 次、共等 12s 都没弹窗 → 应该没有待处理的了, 自动停止
```

### 日志判读（一眼分辨走的哪条路）

| 日志形态 | 走的哪条路 | 是否可信 |
|---|---|---|
| `✓ [A] 已点击 (frame[1]) id=_ctp_...` | Selenium：`find_element` + `arguments[0].click()` | ✅ |
| `✓ [A] 已点击 (frame[1])`（无 `id=`） | JS 快路径：`document.querySelector(...).click()` | ❌ 对工具栏无效 |
| `✓ [C] 已点确定 (frame[1]) id=ymPrompt_btn_N` | JS 快路径点弹窗按钮 | ✅ 有效 |

所以排查口诀：**同一条"已点击"日志，第 1 轮带 id、之后不带 → 一定是 JS 那一路在假点。**
第 1 轮带 id 是因为那时 `_a_path` 还没缓存，只能走 Selenium 兜底。

## 2. 结论：按控件类型分派，不是"全都用 JS 提速"

| 控件 | 可用手法 | 说明 |
|---|---|---|
| 网页弹窗的「确定」（`ymPrompt_btn_*`） | JS `el.click()` | 有效，单次往返 ~20ms |
| 工具栏/业务按钮（`_ctp_toolbar_item_button_*`） | **必须** Selenium `find_element` + `arguments[0].click()` | JS 纯 DOM click 返回成功但页面无反应（框架绑的是 mousedown/自定义事件） |
| 读状态（有没有可见确定按钮） | JS `querySelectorAll` + `getClientRects()` | 安全，只读 |

```python
# 工具栏按钮：只走 Selenium（多选择器 + 可见性判定），不要 JS 直点
def _click_a(self, tag="A", quiet=False):
    ok = self._click_any(BTN_A, tag, cache_key="_a_path", quiet=quiet)
    if ok:
        self._t_a_click = time.time()          # 真正点下去的时刻
    return ok

# 弹窗按钮：JS 快路径 + 每 10 次空结果校准一次缓存
def _click_confirm(self, tag="确认", quiet=False, cache_key="_c_path"):
    for p in self._cached_paths():
        r = self._js(p, JS_CLICK_CONFIRM)
        if isinstance(r, str):
            if r:
                return True
            self._c_miss = getattr(self, "_c_miss", 0) + 1
            if self._c_miss % 10 != 0:
                return False        # JS 明确说没有 → 立刻返回，绝不退回扫树
    return self._click_any(BTN_CONFIRM, tag, skip_cancel=True, cache_key=cache_key)
```

`_js()` 要吞掉异常并返回 `None`，让调用方回落到 Selenium —— 桩测试里
`execute_script` 不认识新脚本时会抛 `AttributeError`，靠这个回落老测试才不会被误伤。

## 3. 懒扫 `_find`：prefer 命中就必须完全不扫树

第一版写成"先拼 `[prefer] + 全部路径` 再逐个试"，`_frame_paths()` 在拼列表时就被调用了，
缓存等于白做。审计测试（第 1 轮后把 `_frame_paths` 换成 `raise`）当场把它抓出来：

```
File ".../SendFenhang.py", line 680, in _find
AssertionError: 稳态下还在扫 frame 树（每轮几百毫秒的来源）
```

正确写法见 SKILL.md「三步循环的上下文管理」里的 `_find_in` + `_find` 组合：
prefer 命中即 `return`，未命中才 `_frame_paths()`。

配套提速（本轮把每轮命令数从 37 降到 22）：

- `_ctx_now`：`_goto_path` 里 `if self._ctx_now == path: return`；`_frame_paths()` 末尾把 `_ctx_now` 置 `[]`，
  切窗口时置 `None`（window 切换会让 frame 上下文失效）。
- `_win`：pin 住窗口句柄，不再每轮遍历 `window_handles` + 读 URL。
- interval 补差额：`rest = interval - (time.time() - t_c)`，只补剩下的。

## 4. 桩测试要能"禁止退化"

```python
_orig = App._frame_paths
state = {"allow": True}

def guarded(self, *a, **k):
    if not state["allow"]:
        import traceback; traceback.print_stack()
        raise AssertionError("稳态下还在扫 frame 树")
    return _orig(self, *a, **k)

App._frame_paths = guarded
# 第 1 轮结束后：state["allow"] = False
# 断言：确认次数 == N、每轮 WebDriver 命令数 < 40、轮间间隔 < interval+200ms
```

窗口/帧上下文缓存很容易把 `_ctx_now` 弄脏，所以这类缓存型优化**必须**配一个
"带命令计数的假 driver"（每条 `find_elements` / `execute_script` / `frame()` 都 `sleep(8ms)` 并计数），
否则 300ms 的优化在测试里看不出效果，也测不出退化。

## 5. 慢速演示（验证用）

用户看不到 166ms 就消失的确认框时会怀疑工具跳过步骤。加复选框：
`慢速演示：每个「确定」弹出后停 0.6s 再点`，在 `_accept_alert_once()` 之后、
`_wait_click_confirm()` 之前 `self._stop.wait(0.6)`。验证时勾上，正式跑取消。
