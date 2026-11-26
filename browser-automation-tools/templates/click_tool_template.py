#!/usr/bin/env python3
"""
点击自动化 GUI 模板 — Selenium + Tkinter
连已有浏览器、可调速、开始/停止按钮。
"""
import time, threading, tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import NoSuchElementException

DEBUG_PORT = 9222
TARGET_KEYWORD = "审批"


class ClickTool:
    def __init__(self, root):
        self.root = root
        self.root.title("自动化工具")
        self.root.geometry("600x480")
        self.driver = None
        self._stop = threading.Event()
        self.count = 0
        self._build()

    def _build(self):
        f = ttk.Frame(self.root, padding=10)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="工具标题", font=("Microsoft YaHei", 14, "bold")).pack()
        ttk.Label(f, text="目标URL:").pack(anchor=tk.W)
        self.url_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.url_var).pack(fill=tk.X, pady=2)

        sf = ttk.LabelFrame(f, text="速度", padding=5)
        sf.pack(fill=tk.X, pady=5)
        self.speed_var = tk.DoubleVar(value=0.3)
        ttk.Scale(sf, from_=0.1, to=5.0, variable=self.speed_var,
                  orient=tk.HORIZONTAL).pack(fill=tk.X)

        bf = ttk.Frame(f)
        bf.pack()
        self.start_btn = ttk.Button(bf, text="开始", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(bf, text="停止", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(f, textvariable=self.status_var, foreground="#2563eb").pack()

        self.log = scrolledtext.ScrolledText(f, height=10)
        self.log.pack(fill=tk.BOTH, expand=True)

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)

    def start(self):
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self._stop.clear()
        self.count = 0
        opts = EdgeOptions()
        opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
        self.driver = webdriver.Edge(options=opts)
        self._log("已连接浏览器")
        threading.Thread(target=self._worker, daemon=True).start()

    def stop(self):
        self._stop.set()

    def _cleanup(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if self.driver:
            try: self.driver.quit()
            except: pass

    # ========== 业务逻辑（改这里）==========
    def _worker(self):
        while not self._stop.is_set():
            if self._click():
                self.count += 1
                self.status_var.set(f"已点击 {self.count} 次")
            self._stop.wait(self.speed_var.get())
        self._cleanup()

    def _click(self):
        for by, val in [
            (By.ID, "your_button_id"),
            (By.LINK_TEXT, "按钮文字"),
        ]:
            try:
                el = self.driver.find_element(by, val)
                self.driver.execute_script("arguments[0].click();", el)
                return True
            except NoSuchElementException:
                continue
        return False


if __name__ == "__main__":
    tk.Tk().__init__() or ClickTool(tk.Tk()) or tk.mainloop()
