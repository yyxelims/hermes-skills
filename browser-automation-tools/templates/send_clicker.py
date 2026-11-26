#!/usr/bin/env python3
"""
Send Clicker Template — 硬编码选择器 + EdgeService 直接启动 + iframe 处理
=============================================================================
适用于：银行/政务内网，固定两个按钮（主按钮 + 弹窗确定），不需要填选择器。

使用前改 APP_CONFIG 字典里的选择器。
"""

APP_CONFIG = {
    "main_selectors": [
        ("css", "#_ctp_toolbar_item_button_sendfmbm"),
        ("xpath", "/html/body/div[5]/..."),  # 浏览器 Copy → Copy XPath
        ("link", "发送总行审批"),
    ],
    "confirm_selectors": [
        ("css", "#ymPrompt_btn_0"),
        ("xpath", "//input[@value='确 定']"),
    ],
    "approve_iframe_index": 1,   # 按钮在哪个 iframe 里（从 0 开始）。None = 自动扫描
}

# === 模板代码（不要改下面）====
import sys, os, time, threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.common.exceptions import NoSuchElementException

BY_MAP = {"css": By.CSS_SELECTOR, "xpath": By.XPATH, "link": By.LINK_TEXT, "partial": By.PARTIAL_LINK_TEXT}

class SendClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Send Clicker")
        self.driver = None
        self.clicks = 0
        self.errors = 0
        self._stop = threading.Event()
        self._build()

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_widget.config(state=tk.NORMAL)
        self.log_widget.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_widget.see(tk.END)
        self.log_widget.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _find_element(self, selectors):
        for kind, val in selectors:
            try:
                el = self.driver.find_element(BY_MAP.get(kind, By.CSS_SELECTOR), val)
                if not el.is_displayed():
                    continue
                return el
            except NoSuchElementException:
                continue
        return None

    def _switch_to_iframe(self):
        idx = APP_CONFIG.get("approve_iframe_index")
        if idx is not None:
            try:
                self.driver.switch_to.frame(self.driver.find_elements(By.TAG_NAME, "iframe")[idx])
                if self._find_element(APP_CONFIG["main_selectors"]):
                    return True
                self.driver.switch_to.parent_frame()
            except:
                pass
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for i, f in enumerate(iframes):
            self.driver.switch_to.frame(f)
            if self._find_element(APP_CONFIG["main_selectors"]):
                return True
            self.driver.switch_to.parent_frame()
        return False

    def _build(self):
        m = ttk.Frame(self.root, padding="12"); m.pack(fill=tk.BOTH, expand=True)
        self._add_speed_control(m, row=1)
        self._add_buttons(m, row=2)
        self._add_status(m, row=3)
        self._add_log(m, row=4)

    def _work(self):
        if not self._switch_to_iframe():
            self._log("ERROR: button not found"); return
        self.clicks = self.errors = 0
        while not self._stop.is_set():
            el = self._find_element(APP_CONFIG["confirm_selectors"])
            if el:
                self.driver.execute_script("arguments[0].click();", el)
                self.errors += 1; self._stop.wait(0.1); continue
            el = self._find_element(APP_CONFIG["main_selectors"])
            if el:
                self.driver.execute_script("arguments[0].click();", el)
                self.clicks += 1
            self._stop.wait(self.speed.get())

if __name__ == "__main__":
    root = tk.Tk(); SendClickerApp(root); root.mainloop()
