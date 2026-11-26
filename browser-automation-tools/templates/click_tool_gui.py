#!/usr/bin/env python3
"""Selenium 连点工具 GUI 模板 — 连接已有 Edge 浏览器"""
import time, threading, tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import NoSuchElementException

# ===== 配置区 =====
DEBUG_PORT = 9222
TARGET_TAB_KEYWORD = "审批"
CLICK_INTERVAL = 0.3

# 按钮定位选择器（按优先级排列）
CLICK_SELECTORS = [
    (By.ID, "your_button_id"),
    (By.LINK_TEXT, "按钮文字"),
    (By.PARTIAL_LINK_TEXT, "部分文字"),
]

# 弹窗关闭选择器
ERROR_DIALOG_SELECTORS = [
    (By.ID, "error_ok_btn_id"),
    (By.CLASS_NAME, "dialog-class"),
]

# 成功检测条件
SUCCESS_CHECK = lambda driver: False  # 替换为实际检测逻辑


class ClickTool:
    def __init__(self, root):
        self.root = root
        self.root.title("连点工具")
        self.root.geometry("600x500")
        self.driver = None
        self._stop = threading.Event()
        self.count = 0
        self.errors = 0
        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding="10")
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="速度(秒):").pack(side=tk.LEFT)
        self.speed = tk.DoubleVar(value=CLICK_INTERVAL)
        ttk.Scale(main, from_=0.1, to=5.0, variable=self.speed,
                  orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        ttk.Button(main, text="开始", command=self._start).pack(side=tk.LEFT, padx=4)
        self.stop_btn = ttk.Button(main, text="停止", command=self._stop_clicking, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        self.status = tk.StringVar(value="就绪")
        ttk.Label(self.root, textvariable=self.status).pack()

        self.log = scrolledtext.ScrolledText(self.root, height=12, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def _find_and_click(self):
        for by, val in CLICK_SELECTORS:
            try:
                el = self.driver.find_element(by, val)
                self.driver.execute_script("arguments[0].click();", el)
                return True
            except NoSuchElementException: continue
        return False

    def _close_dialog(self):
        for by, val in ERROR_DIALOG_SELECTORS:
            try:
                el = self.driver.find_element(by, val)
                if el.is_displayed():
                    self.driver.execute_script("arguments[0].click();", el)
                    return True
            except NoSuchElementException: continue
        return False

    def _worker(self):
        while not self._stop.is_set():
            if self._close_dialog():
                self.errors += 1
                self._stop.wait(0.1); continue
            if self._find_and_click():
                self.count += 1
                self.status.set(f"点击: {self.count} | 弹窗: {self.errors}")
            else:
                self.status.set("等待中 — 请切换到目标页面")
                self._stop.wait(2); continue
            self._stop.wait(max(0.1, self.speed.get()))
            if SUCCESS_CHECK(self.driver):
                self._log("操作成功！"); break

    def _start(self):
        opts = EdgeOptions()
        opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
        self.driver = webdriver.Edge(options=opts)
        for h in self.driver.window_handles:
            self.driver.switch_to.window(h)
            if TARGET_TAB_KEYWORD in self.driver.title: break
        self._stop.clear()
        self.stop_btn.config(state=tk.NORMAL)
        threading.Thread(target=self._worker, daemon=True).start()

    def _stop_clicking(self):
        self._stop.set()
        self.stop_btn.config(state=tk.DISABLED)
        if self.driver:
            self.driver.quit()
            self.driver = None


if __name__ == "__main__":
    tk.mainloop(ClickTool(tk.Tk()))
