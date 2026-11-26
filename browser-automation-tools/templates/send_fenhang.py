#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SendFenhang — 三步循环点击工具模板 (A→B→C + 诊断模式)
=========================================================================
流程: A(网页按钮) → B(浏览器原生弹窗alert.accept) → C(网页DOM弹窗确定) → 循环

特点:
  - 诊断按钮: 只检测不点击，遍历所有选择器打印命中报告
  - 运行模式: 每步也打印每个选择器尝试结果
  - 浏览器原生弹窗: 用 switch_to.alert.accept()，不是 find_element
  - 多选择器兜底: 每个按钮5+个选择器
  - iframe 扫描: 诊断时逐个切进iframe找按钮

选择器配置在 BTN_A_SELECTORS 和 BTN_C_SELECTORS，按实际页面改。
"""

import sys, os, subprocess, time, threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import (
    NoSuchElementException, NoAlertPresentException
)

PORT = 9222

# ============================================================
# 选择器配置 — 按实际页面改这里
# ============================================================
BTN_A_SELECTORS = [
    ("ID",          By.ID,              "_ctp_toolbar_item_button_send"),
    ("LINK_TEXT",   By.LINK_TEXT,       "发送分行审批"),
    ("PARTIAL",     By.PARTIAL_LINK_TEXT,"发送分行"),
    ("CSS_ID",      By.CSS_SELECTOR,    "a[id*='_ctp_toolbar_item_button_send']"),
    ("XPATH_TEXT",  By.XPATH,           "//a[contains(text(),'发送分行审批')]"),
]

BTN_C_SELECTORS = [
    ("ID",          By.ID,              "ymPrompt_btn_0"),
    ("XPATH_ID",    By.XPATH,           "//input[@id='ymPrompt_btn_0']"),
    ("CSS_CLASS",   By.CSS_SELECTOR,    "input.btnStyle[value='确 定']"),
    ("CSS_ID",      By.CSS_SELECTOR,    "#ymPrompt_btn_0"),
    ("XPATH_VALUE", By.XPATH,           "//input[contains(@value,'确') and contains(@value,'定')]"),
]

# ============================================================
# EdgeDriver
# ============================================================
def _get_driver_path():
    if getattr(sys, 'frozen', False):
        bundled = os.path.join(sys._MEIPASS, "msedgedriver.exe")
        if os.path.exists(bundled):
            return bundled
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "msedgedriver.exe")
    if os.path.exists(local):
        return local
    return None

# ============================================================
# GUI App
# ============================================================
class FenhangApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SendFenhang")
        self.root.geometry("660x620")
        self.driver = None
        self.rounds = 0
        self._stop = threading.Event()
        self._build()

    def _build(self):
        m = ttk.Frame(self.root, padding="12")
        m.pack(fill=tk.BOTH, expand=True)
        m.columnconfigure(0, weight=1)
        ttk.Label(m, text="Three-Step Clicker", font=("Microsoft YaHei", 14, "bold")).grid(row=0, column=0, pady=(0, 8))
        # Speed
        sf = ttk.LabelFrame(m, text="Interval", padding="8")
        sf.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        sf.columnconfigure(1, weight=1)
        ttk.Label(sf, text="Step interval (sec):").grid(row=0, column=0, padx=(0, 8))
        self.speed = tk.DoubleVar(value=0.5)
        ttk.Scale(sf, from_=0.1, to=5.0, variable=self.speed, orient=tk.HORIZONTAL,
                  command=lambda v: self.slbl.config(text=f"{float(v):.1f}s")).grid(row=0, column=1, sticky="ew")
        self.slbl = ttk.Label(sf, text="0.5s", width=6)
        self.slbl.grid(row=0, column=2, padx=(8, 0))
        # Buttons
        bf = ttk.Frame(m)
        bf.grid(row=3, column=0, pady=(0, 6))
        self.lbtn = ttk.Button(bf, text="Launch", command=self._launch)
        self.lbtn.pack(side=tk.LEFT, padx=(0, 6))
        self.sbtn = ttk.Button(bf, text="Start", command=self._go, state=tk.DISABLED)
        self.sbtn.pack(side=tk.LEFT, padx=(0, 6))
        self.tbtn = ttk.Button(bf, text="Stop", command=self._halt, state=tk.DISABLED)
        self.tbtn.pack(side=tk.LEFT, padx=(0, 6))
        self.dbtn = ttk.Button(bf, text="Diagnose", command=self._diagnose, state=tk.DISABLED)
        self.dbtn.pack(side=tk.LEFT)
        # Status
        stf = ttk.LabelFrame(m, text="Status", padding="6")
        stf.grid(row=4, column=0, sticky="ew", pady=(0, 6))
        self.st = tk.StringVar(value="Click Launch")
        ttk.Label(stf, textvariable=self.st, foreground="#2563eb").grid(row=0, column=0, sticky="w")
        self.ct = tk.StringVar(value="Rounds: 0")
        ttk.Label(stf, textvariable=self.ct).grid(row=1, column=0, sticky="w", pady=(2, 0))
        # Log
        lf = ttk.LabelFrame(m, text="Log", padding="4")
        lf.grid(row=5, column=0, sticky="nsew")
        lf.columnconfigure(0, weight=1); lf.rowconfigure(0, weight=1); m.rowconfigure(5, weight=1)
        self.log = scrolledtext.ScrolledText(lf, height=16, width=72, state=tk.DISABLED, font=("Consolas", 9))
        self.log.grid(row=0, column=0, sticky="nsew")

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _ctr(self):
        self.ct.set(f"Rounds: {self.rounds}")
        self.root.update_idletasks()

    def _launch(self):
        if self.driver:
            try:
                _ = self.driver.current_url
                self._log("Reusing browser connection")
                self._post_connect(); return
            except: self.driver = None
        # 1. Find Edge
        edge = None
        for ep in [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                   r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                   r"C:\Program Files\Edge\Application\msedge.exe"]:
            if os.path.exists(ep): edge = ep; break
        if not edge:
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe") as key:
                    p = winreg.QueryValue(key, None)
                    if os.path.exists(p): edge = p
            except: pass
        if not edge: edge = "msedge"
        self._log(f"Edge: {edge}")
        # 2. Kill all Edge processes
        self._log("Killing Edge processes...")
        try:
            subprocess.run(
                'powershell -Command "Get-Process msedge -ErrorAction SilentlyContinue | Stop-Process -Force"',
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.5)
        except: pass
        # 3. Launch Edge with --user-data-dir (MUST use independent dir or port is ignored)
        import tempfile
        temp_dir = os.path.join(tempfile.gettempdir(), "sendfenhang_edge")
        self._log(f"Launching Edge (port {PORT}, independent dir)...")
        try:
            subprocess.Popen(
                [edge, f"--remote-debugging-port={PORT}",
                 f"--user-data-dir={temp_dir}", "about:blank"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            self._log(f"Launch failed: {e}"); self.st.set("Failed"); return
        self._log("Waiting for Edge (3s)...")
        time.sleep(3)
        # 4. Socket check: is port actually open?
        import socket
        port_ok = False
        for _ in range(8):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1); s.connect(("127.0.0.1", PORT)); s.close()
                port_ok = True; self._log(f"Port {PORT} is open"); break
            except: self._stop.wait(1)
        if not port_ok:
            self._log(f"Port {PORT} never opened — Edge may be blocked by security software")
            self.st.set("Port not open"); return
        # 5. Connect Selenium — local EdgeDriver first, fallback to Selenium Manager
        opts = EdgeOptions()
        opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{PORT}")
        dp = _get_driver_path()
        try:
            if dp:
                self._log(f"EdgeDriver: {dp}")
                service = EdgeService(executable_path=dp)
                self.driver = webdriver.Edge(options=opts, service=service)
            else:
                self._log("Selenium Manager auto-matching EdgeDriver...")
                self.driver = webdriver.Edge(options=opts)
            self._log("Selenium connected OK")
            try: self._log(f"URL: {self.driver.current_url}"); self._log(f"Title: {self.driver.title}")
            except: pass
            self._post_connect()
        except Exception as e:
            self._log(f"Connect failed: {e}")
            self._log("Trying Selenium Manager auto-match...")
            try:
                self.driver = webdriver.Edge(options=opts)
                self._log("Connected (auto-match)"); self._post_connect()
            except Exception as e2:
                self._log(f"Connect failed: {e2}")
                self._log("Download matching EdgeDriver: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
                self.st.set("Connection failed")

    def _post_connect(self):
        self.st.set("Ready")
        self.lbtn.config(state=tk.DISABLED); self.sbtn.config(state=tk.NORMAL); self.dbtn.config(state=tk.NORMAL)

    def _find_visible(self, selectors):
        for by, val in selectors:
            try:
                el = self.driver.find_element(by, val)
                if el.is_displayed(): return el
            except NoSuchElementException: continue
        return None

    def _find_with_log(self, label, selectors, click_it=False):
        """遍历所有选择器，日志报告每个命中情况"""
        self._log(f"-- {label}: checking {len(selectors)} selectors --")
        found_el = None
        for name, by, val in selectors:
            try:
                el = self.driver.find_element(by, val)
                visible = el.is_displayed()
                detail = f"tag={el.tag_name} id={el.get_attribute('id') or ''} val={el.get_attribute('value') or ''} text={(el.text or '')[:20]}"
                self._log(f"  OK [{name}] hit | visible={visible} | {detail}")
                if found_el is None and visible: found_el = el
            except NoSuchElementException:
                self._log(f"  NO [{name}] miss | {val}")
            except Exception as e:
                self._log(f"  ERR [{name}] {type(e).__name__}: {e}")
        if found_el and click_it:
            try:
                self.driver.execute_script("arguments[0].click();", found_el)
                self._log(f"  -> clicked (JS)"); return True
            except Exception as e:
                self._log(f"  -> click failed: {e}"); return False
        return found_el is not None

    def _handle_alert_with_log(self, label="B"):
        """处理浏览器原生弹窗，遍历多种方法"""
        self._log(f"-- {label}: checking native alert --")
        for attempt in range(20):
            if self._stop.is_set(): return False
            try:
                alert = self.driver.switch_to.alert
                self._log(f"  OK alert found | text={alert.text[:50]}")
                try: alert.accept(); self._log("  -> accept() OK"); return True
                except Exception as e: self._log(f"  WARN accept() failed: {e}")
                try:
                    from selenium.webdriver.common.keys import Keys
                    alert.send_keys(Keys.ENTER); self._log("  -> send_keys(ENTER) OK"); return True
                except Exception as e: self._log(f"  WARN send_keys failed: {e}")
                try: alert.dismiss(); self._log("  WARN dismiss() OK (clicked Cancel)"); return True
                except Exception as e: self._log(f"  WARN dismiss() failed: {e}")
            except NoAlertPresentException:
                if attempt == 0: self._log("  .. no alert, waiting...")
                self._stop.wait(0.5); continue
            except Exception as e:
                self._log(f"  ERR {type(e).__name__}: {e}"); self._stop.wait(0.5)
        self._log(f"  NO {label}: no alert within 10s"); return False

    def _diagnose(self):
        self._log("=" * 50); self._log("DIAGNOSE MODE (read-only)"); self._log("=" * 50)
        threading.Thread(target=self._diag_worker, daemon=True).start()

    def _diag_worker(self):
        try:
            self.dbtn.config(state=tk.DISABLED)
            self._log(f"URL: {self.driver.current_url}")
            self._log(f"Title: {self.driver.title}")
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            self._log(f"iframe count: {len(iframes)}")
            for i, f in enumerate(iframes):
                self._log(f"  iframe[{i}]: src={(f.get_attribute('src') or '(none)')[:60]}")
            self._find_with_log("A:send-button", BTN_A_SELECTORS, click_it=False)
            for i, f in enumerate(iframes):
                try:
                    self.driver.switch_to.frame(f)
                    self._log(f"-- inside iframe[{i}] --")
                    self._find_with_log(f"A(iframe[{i}])", BTN_A_SELECTORS, click_it=False)
                    self._find_with_log(f"C(iframe[{i}])", BTN_C_SELECTORS, click_it=False)
                    self.driver.switch_to.default_content()
                except Exception as e:
                    self._log(f"  iframe[{i}] switch failed: {e}")
                    self.driver.switch_to.default_content()
            self._find_with_log("C:dialog-ok", BTN_C_SELECTORS, click_it=False)
            try:
                alert = self.driver.switch_to.alert
                self._log(f"OK native alert present: {alert.text[:50]}")
                self.driver.switch_to.default_content()
            except NoAlertPresentException:
                self._log(".. no native alert (normal before clicking A)")
            self._log("-- global input scan --")
            for inp in self.driver.find_elements(By.TAG_NAME, "input"):
                v = inp.get_attribute("value") or ""; i_id = inp.get_attribute("id") or ""
                if v or i_id:
                    self._log(f"  input: id={i_id} value={v} visible={inp.is_displayed()}")
            self._log("=" * 50); self._log("Diagnose done. Copy log and send back."); self._log("=" * 50)
        except Exception as e:
            self._log(f"Diagnose error: {e}")
        finally:
            self.dbtn.config(state=tk.NORMAL)

    def _worker(self):
        self._log("=" * 50); self._log("Starting A->B->C loop"); self._log("=" * 50)
        self.st.set("Running"); wait_count = 0
        while not self._stop.is_set():
            interval = self.speed.get()
            # Step A
            self._log("=== Step A: click send button ===")
            if not self._find_with_log("A:send-button", BTN_A_SELECTORS, click_it=True):
                wait_count += 1
                if wait_count >= 60: self._log("Timeout: A button not found for 30s"); break
                self._stop.wait(0.5); continue
            wait_count = 0; self._stop.wait(interval)
            # Step B
            self._log("=== Step B: native alert ===")
            self._handle_alert_with_log("B"); self._stop.wait(interval)
            # Step C
            self._log("=== Step C: DOM dialog OK ===")
            c_ok = False
            for _ in range(20):
                if self._stop.is_set(): break
                if self._find_with_log("C:dialog-ok", BTN_C_SELECTORS, click_it=True):
                    c_ok = True; break
                self._stop.wait(0.5)
            if not c_ok: self._log("WARN C: OK button not found within 10s")
            self.rounds += 1; self._ctr()
            if self.rounds <= 5 or self.rounds % 10 == 0:
                self._log(f"=== Round {self.rounds} done ===")
            self._stop.wait(interval)
        self._halt_ui()

    def _go(self):
        self.rounds = 0; self._ctr(); self._stop.clear()
        self.sbtn.config(state=tk.DISABLED); self.tbtn.config(state=tk.NORMAL)
        self.st.set("Running")
        threading.Thread(target=self._worker, daemon=True).start()

    def _halt(self): self._stop.set()

    def _halt_ui(self):
        self._log("Stopped")
        self.lbtn.config(state=tk.NORMAL); self.sbtn.config(state=tk.NORMAL)
        self.tbtn.config(state=tk.DISABLED); self.st.set("Stopped"); self._ctr()

if __name__ == "__main__":
    root = tk.Tk(); FenhangApp(root); root.mainloop()
