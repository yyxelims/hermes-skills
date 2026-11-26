#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静态自检：tkinter 工具里「创建了但从不启用」的按钮。

踩过的坑（2026-11-04）：新加一个「忙碌期」探针按钮，`state=tk.DISABLED` 建出来，
`_post_connect()` 里只启用了另外三个，于是用户看到的是「这个按钮一直是灰色、点不动」。
编译通过、其他按钮正常，所以只有用户在界面上才发现。

用法：
    python3 check_tk_buttons_enabled.py app.py           # 检查单个文件
    python3 check_tk_buttons_enabled.py a.py b.py ...    # 检查多个
    python3 check_tk_buttons_enabled.py                 # 扫当前目录 *.py

退出码：0 = 全部按钮都能被启用；1 = 有永远灰着的按钮（列出名字）。
可直接挂进本地测试：`python3 .../check_tk_buttons_enabled.py SendFenhang.py || exit 1`
"""
import re
import sys
from pathlib import Path

# self.X = ttk.Button(...) / tk.Button(...)
CREATE_RE = re.compile(r"self\.(\w+)\s*=\s*(?:ttk|tk)\.Button\(")
# 任何能让按钮恢复可点的地方：config(state=...) / configure(state=...) / state=["!disabled"]
ENABLE_RE = re.compile(
    r"self\.{name}\s*\.\s*(?:config|configure)\(\s*state\s*=\s*(?:tk\.)?(?:NORMAL|\"normal\")"
    r"|self\.{name}\s*\.\s*(?:config|configure)\([^)]*state\s*=\s*\[[^\]]*!disabled"
)
# 循环里统一处理：for b in (self.a, self.b, ...): b.config(state=tk.NORMAL)
LOOP_RE = re.compile(
    r"for\s+(\w+)\s+in\s*\(([^)]*self\.\w+[^)]*)\)\s*:\s*\n\s*\1\s*\.\s*(?:config|configure)\(\s*state\s*=\s*(?:tk\.)?(?:NORMAL|\"normal\")",
    re.M,
)


def enabled_names(src: str) -> set:
    names = set()
    for name in set(CREATE_RE.findall(src)):
        # 直接调用
        if re.search(
            rf"self\.{name}\s*\.\s*(?:config|configure)\(\s*state\s*=\s*(?:tk\.)?(?:NORMAL|[\"']normal[\"'])",
            src,
        ):
            names.add(name)
    # for b in (self.x, self.y): b.config(state=tk.NORMAL)
    for _, group in LOOP_RE.findall(src):
        for m in re.finditer(r"self\.(\w+)", group):
            names.add(m.group(1))
    return names


def check(path: Path) -> tuple[bool, list, list]:
    src = path.read_text(encoding="utf-8", errors="replace")
    created = set(CREATE_RE.findall(src))
    if not created:
        return True, [], []
    enabled = enabled_names(src)
    dead = sorted(created - enabled)
    dup = sorted(n for n in created if len(re.findall(rf"self\.{n}\s*=\s*(?:ttk|tk)\.Button\(", src)) > 1)
    ok = not dead and not dup
    return ok, dead, dup


def main(argv):
    targets = [Path(a) for a in argv[1:]] or sorted(Path(".").glob("*.py"))
    bad = 0
    for p in targets:
        if not p.exists() or p.suffix != ".py":
            continue
        ok, dead, dup = check(p)
        created_n = len(CREATE_RE.findall(p.read_text(encoding="utf-8", errors="replace")))
        if created_n == 0:
            continue
        if ok:
            print(f"OK   {p.name}: {created_n} 个按钮，全部有启用路径")
        else:
            bad += 1
            if dead:
                print(f"FAIL {p.name}: 创建了但从不启用（会一直是灰的）: {', '.join(dead)}")
            if dup:
                print(f"FAIL {p.name}: 同一个按钮被创建多次（状态会被后一个覆盖）: {', '.join(dup)}")
    if bad:
        print("\n修法：在 _post_connect() 里启用，在 _start() 里禁用（防并发），在 _halt_ui() 里恢复。")
        return 1
    print("\nALL PASSED — 没有'永远灰色'的按钮")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
