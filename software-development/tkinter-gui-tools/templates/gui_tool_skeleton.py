#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tkinter GUI 小工具骨架（从已验证工具精简）。
结构：纯逻辑区（可无头测试）+ GUI 区（App/BlockFrame/PreviewTable/ScrollFrame）。
复制后改：逻辑函数、配置块字段、输出写入。
"""

import os
import math
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

MAX_PREVIEW = 50


# ============ 纯逻辑区：不 import tkinter 之外的东西，全部可无头调用 ============

def parse_cell(v):
    """单元格 -> 显示文本；float 整数化 1.0 -> '1'。"""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    return str(v)


def key_of(v):
    """匹配键归一化：float 整数化、去空白/引号、NaN -> None。"""
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v):
            return None
        return str(int(v)) if v.is_integer() else repr(v)
    s = str(v).strip().strip("'\"").strip()
    return None if s == "" or s.lower() == "nan" else s


def sniff_excel_kind(path):
    """魔数嗅探：xlsx(ZIP)=PK.. / xls(OLE2)=\xd0\xcf.. / 其他=伪装文件。"""
    with open(path, "rb") as f:
        head = f.read(8)
    if head[:4] == b"PK\x03\x04":
        return "xlsx"
    if head[:4] == b"\xd0\xcf\x11\xe0":
        return "xls"
    return "unknown"


def read_sheet_raw(path, sheet_name, kind=None):
    """header=None + dtype=object 保原值；xlsx 走 BytesIO 绕扩展名检查。"""
    import io
    import xlrd  # noqa
    import openpyxl
    kind = kind or sniff_excel_kind(path)
    if kind == "xls":
        return pd.read_excel(path, sheet_name=sheet_name, header=None, dtype=object,
                             engine="xlrd")
    with open(path, "rb") as f:
        data = f.read()
    return pd.read_excel(io.BytesIO(data), sheet_name=sheet_name, header=None,
                         dtype=object, engine="openpyxl")


def transform(df, **cfg):
    """TODO: 核心转换逻辑写这里，输入/输出都是 DataFrame，便于断言测试。"""
    return df


def write_output(result, out_path, **cfg):
    result.to_excel(out_path, index=False, sheet_name="结果")  # TODO 按需多 sheet


# ============ GUI 区 ============

class PreviewTable(ttk.Frame):
    """前 N 行预览表：Treeview headings + 双向滚动条。"""

    def __init__(self, master, height=6):
        super().__init__(master)
        self.tree = ttk.Treeview(self, height=height, show="headings")
        vs = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hs = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def set_df(self, df):
        self.tree.delete(*self.tree.get_children())
        if df is None or df.empty:
            self.tree["columns"] = ["（空）"]
            self.tree.heading("（空）", text="（无数据）")
            return
        cols = [str(c) for c in df.columns]
        self.tree["columns"] = cols
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=110, minwidth=60, stretch=False, anchor="w")
        for _, r in df.head(MAX_PREVIEW).iterrows():
            self.tree.insert("", "end", values=[parse_cell(v) for v in r.tolist()])


class ScrollFrame(ttk.Frame):
    """可滚动容器；指针悬在 Treeview 上时不抢滚动（预览表自己滚）。"""

    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        vs = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        self.canvas.configure(yscrollcommand=vs.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")
        self.inner.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.inner.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

    def _wheel(self, e):
        w = self.winfo_containing(e.x_root, e.y_root)
        while w is not None:
            if isinstance(w, ttk.Treeview):
                return
            if w is self.canvas:
                break
            w = getattr(w, "master", None)
        self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")


class BlockFrame(ttk.LabelFrame):
    """单文件配置块：选文件 + Sheet + 表头行 + 编号列 + 预览。按需增删字段。"""

    def __init__(self, master, title, app):
        super().__init__(master, text=title, padding=6)
        self.app = app
        self.path, self.raw, self.df = None, None, None

        r0 = ttk.Frame(self); r0.pack(fill="x")
        self.lbl_file = ttk.Label(r0, text="未选择文件", foreground="#888")
        self.lbl_file.pack(side="left", fill="x", expand=True)
        ttk.Button(r0, text="选择文件…", command=self.pick_file).pack(side="left")

        r1 = ttk.Frame(self); r1.pack(fill="x", pady=2)
        ttk.Label(r1, text="Sheet:").pack(side="left")
        self.cb_sheet = ttk.Combobox(r1, state="readonly", width=20)
        self.cb_sheet.pack(side="left", padx=(2, 10))
        self.cb_sheet.bind("<<ComboboxSelected>>", lambda e: self.on_sheet())
        ttk.Label(r1, text="表头行:").pack(side="left")
        self.var_header = tk.IntVar(value=1)
        sp = ttk.Spinbox(r1, from_=1, to=500, width=5, textvariable=self.var_header,
                         command=self.on_header)
        sp.pack(side="left", padx=(2, 10))
        sp.bind("<KeyRelease>", lambda e: self.on_header())   # 手打数字必须 bind 这个
        sp.bind("<FocusOut>", lambda e: self.on_header())

        self.preview = PreviewTable(self, height=6)
        self.preview.pack(fill="both", expand=True, pady=(4, 0))

    def pick_file(self):
        p = filedialog.askopenfilename(
            filetypes=[("Excel 文件", "*.xls *.xlsx"), ("所有文件", "*.*")])
        if not p:
            return
        try:
            self.path = p
            self.lbl_file.config(text=p, foreground="#000")
            import openpyxl, xlrd, io
            kind = sniff_excel_kind(p)
            if kind == "xls":
                names = xlrd.open_workbook(p).sheet_names()
            else:
                wb = openpyxl.load_workbook(io.BytesIO(open(p, "rb").read()),
                                            read_only=True)
                names, wb_close = wb.sheetnames, wb.close
                wb_close()
            self.cb_sheet["values"] = names
            if names:
                self.cb_sheet.current(0)
            self.on_sheet()
        except Exception as e:
            messagebox.showerror("读取失败", str(e))

    def on_sheet(self):
        if self.path and self.cb_sheet.get():
            self.raw = read_sheet_raw(self.path, self.cb_sheet.get())
            self.on_header()

    def on_header(self, *_):
        if self.raw is None:
            return
        try:
            hr = max(1, int(self.var_header.get())) - 1
            body = self.raw.iloc[hr + 1:].reset_index(drop=True)
            body.columns = [parse_cell(v).strip() or f"列{i+1}"
                            for i, v in enumerate(self.raw.iloc[hr])]
            self.df = body
        except Exception:
            self.df = None
            return
        self.preview.set_df(self.df)

    def config_ok(self):
        return bool(self.path and self.cb_sheet.get() and self.df is not None)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GUI 工具骨架")
        self.geometry("1000x800")
        self.blocks = []

        outer = ttk.Frame(self, padding=8)
        outer.pack(fill="both", expand=True)

        self.scroll = ScrollFrame(outer)
        self.scroll.pack(fill="both", expand=True)

        ttk.Button(self.scroll.inner, text="＋ 添加配置块",
                   command=self.add_block).pack(anchor="w", pady=4)
        self.block_area = ttk.Frame(self.scroll.inner)
        self.block_area.pack(fill="x")

        frame_out = ttk.LabelFrame(outer, text="输出", padding=6)
        frame_out.pack(fill="x", pady=(6, 0))
        self.var_outdir = tk.StringVar()
        ttk.Entry(frame_out, textvariable=self.var_outdir).pack(side="left",
                                                                fill="x", expand=True)
        ttk.Button(frame_out, text="选文件夹…",
                   command=self.pick_outdir).pack(side="left", padx=4)
        ttk.Button(frame_out, text="开始处理", command=self.run).pack(side="left")

        self.txt_log = tk.Text(outer, height=8, state="disabled", font=("Menlo", 11))
        self.txt_log.pack(fill="both", pady=(6, 0))

        self.add_block()

    def add_block(self):
        f = BlockFrame(self.block_area, f"文件 {len(self.blocks) + 1}", self)
        f.pack(fill="x", pady=(4, 0))
        self.blocks.append(f)

    def pick_outdir(self):
        d = filedialog.askdirectory()
        if d:
            self.var_outdir.set(d)

    def log(self, msg):
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")
        self.update_idletasks()

    def run(self):
        for i, b in enumerate(self.blocks, 1):
            if not b.config_ok():
                messagebox.showwarning("缺少配置", f"文件 {i} 未配置完整。")
                return
        out = os.path.join(self.var_outdir.get() or os.path.expanduser("~"),
                           "结果.xlsx")
        try:
            # TODO: 组装 cfg -> transform() -> write_output()
            self.log(f"完成 → {out}")
            messagebox.showinfo("完成", out)
        except Exception as e:
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("失败", str(e))


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
