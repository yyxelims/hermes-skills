#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SendApproval — Selenium auto-click tool (Edge, single-file, offline EXE)
=========================================================================
python send_approval.py          → GUI
python send_approval.py --build  → build EXE (bundles EdgeDriver)

Pattern: Launch Edge via debug port, connect with Selenium, worker thread
clicks target button in a loop. Button disabled = success = auto-stop.
EdgeDriver bundled into EXE via PyInstaller --add-binary.

See skill: selenium-edge-gui-packaging
"""

import sys, os, subprocess, zipfile, time, threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import NoSuchElementException

PORT = 9222

# ============================================================
# EdgeDriver management
# ============================================================
def _get_driver_path():
    """Resolve EdgeDriver: bundled > local > none"""
    if getattr(sys, 'frozen', False):
        bundled = os.path.join(sys._MEIPASS, "msedgedriver.exe")
        if os.path.exists(bundled):
            return bundled
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "msedgedriver.exe")
    if os.path.exists(local):
        return local
    return None

# ============================================================
# Self-build (--build flag)
# ============================================================
def self_build():
    print("=" * 50)
    print("  SendApproval — Build (bundles EdgeDriver)")
    print("=" * 50)
    for dep in ["selenium>=4.10", "pyinstaller"]:
        print(f"[1/4] Installing {dep}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep, "-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[2/4] Getting EdgeDriver...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.join(script_dir, "msedgedriver.exe")
    if not os.path.exists(driver_path):
        print("       No local msedgedriver.exe found!")
        print("       Download from: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        print("       Place next to this script and run again.")
        sys.exit(1)

    print(f"       Local: {driver_path}")
    add_binary = ["--add-binary", f"{driver_path};."]

    print("[3/4] Building EXE...")
    subprocess.check_call([
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--windowed", "--name", "SendApproval",
        "--hidden-import", "selenium", "--hidden-import", "tkinter",
    ] + add_binary + [os.path.abspath(__file__)])

    exe = os.path.join(script_dir, "dist", "SendApproval.exe")
    if os.path.exists(exe):
        print(f"\n[4/4] Done! {exe}")
        os.startfile(os.path.dirname(exe))

# ============================================================
# GUI + Selenium worker
# ============================================================
class ClickApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SendApproval")
        self.root.geometry("600x500")
        self.driver = None
        self.clicks = 0
        self.errors = 0
        self._stop = threading.Event()
        self._build()

    def _build(self):
        m = ttk.Frame(self.root, padding="12")
        m.pack(fill=tk.BOTH, expand=True)
        m.columnconfigure(0, weight=1)

        ttk.Label(m, text="SendApproval", font=("Microsoft YaHei", 14, "bold")).grid(row=0, column=0, pady=(0, 12))

        inst = ttk.LabelFrame(m, text="Steps", padding="8")
        inst.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(inst, text="1. Click LAUNCH BROWSER").grid(row=0, column=0, sticky="w")
        ttk.Label(inst, text="2. Login and navigate in Edge").grid(row=1, column=0, sticky="w")
        ttk.Label(inst, text="3. Click START").grid(row=2, column=0, sticky="w")

        sf = ttk.LabelFrame(m, text="Speed", padding="8")
        sf.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        sf.columnconfigure(1, weight=1)
        ttk.Label(sf, text="Interval (sec):").grid(row=0, column=0, padx=(0, 8))
        self.speed = tk.DoubleVar(value=0.3)
        ttk.Scale(sf, from_=0.1, to=5.0, variable=self.speed, orient=tk.HORIZONTAL,
                  command=lambda v: self.slbl.config(text=f"{float(v):.1f}s")).grid(row=0, column=1, sticky="ew")
        self.slbl = ttk.Label(sf, text="0.3s", width=6)
        self.slbl.grid(row=0, column=2, padx=(8, 0))

        bf = ttk.Frame(m)
        bf.grid(row=3, column=0, pady=(0, 8))
        self.lbtn = ttk.Button(bf, text="LAUNCH\nBROWSER", command=self._launch)
        self.lbtn.pack(side=tk.LEFT, padx=(0, 8))
        self.sbtn = ttk.Button(bf, text="START", command=self._go, state=tk.DISABLED)
        self.sbtn.pack(side=tk.LEFT, padx=(0, 8))
        self.tbtn = ttk.Button(bf, text="STOP", command=self._halt, state=tk.DISABLED)
        self.tbtn.pack(side=tk.LEFT)

        stf = ttk.LabelFrame(m, text="Status", padding="8")
        stf.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        self.st = tk.StringVar(value="Click LAUNCH BROWSER")
        ttk.Label(stf, textvariable=self.st, foreground="#2563eb").grid(row=0, column=0, sticky="w")
        self.ct = tk.StringVar(value="Clicks: 0 | Errors: 0")
        ttk.Label(stf, textvariable=self.ct).grid(row=1, column=0, sticky="w", pady=(4, 0))

        lf = ttk.LabelFrame(m, text="Log", padding="4")
        lf.grid(row=5, column=0, sticky="nsew")
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)
        m.rowconfigure(5, weight=1)
        self.log = scrolledtext.ScrolledText(lf, height=12, width=65, state=tk.DISABLED)
        self.log.grid(row=0, column=0, sticky="nsew")

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _ctr(self):
        self.ct.set(f"Clicks: {self.clicks} | Errors: {self.errors}")
        self.root.update_idletasks()

    def _launch(self):
        subprocess.run(
            f'powershell -Command "Get-Process msedge -ErrorAction SilentlyContinue | '
            f'Where-Object {{$_.CommandLine -like \'*{PORT}*\'}} | Stop-Process -Force"',
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)

        for ep in [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                   r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]:
            if os.path.exists(ep):
                edge = ep
                break
        else:
            edge = "msedge"

        subprocess.Popen([edge, f"--remote-debugging-port={PORT}", "about:blank"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)

        try:
            driver_path = _get_driver_path()
            service = EdgeService(executable_path=driver_path) if driver_path else EdgeService()
            opts = EdgeOptions()
            opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{PORT}")
            self.driver = webdriver.Edge(service=service, options=opts)
            self._log("Connected. Login, navigate, then START.")
            self.st.set("Ready")
            self.lbtn.config(state=tk.DISABLED)
            self.sbtn.config(state=tk.NORMAL)
        except Exception as e:
            self._log(f"Failed: {e}")
            self.st.set("Failed")

    # --- Override these for your specific target ---
    TARGET_SELECTORS = [
        (By.ID, "_ctp_toolbar_item_button_sendfmbm"),
        (By.LINK_TEXT, "发送总行审批"),
        (By.PARTIAL_LINK_TEXT, "发送总行"),
    ]

    def _click(self):
        for by, val in self.TARGET_SELECTORS:
            try:
                el = self.driver.find_element(by, val)
                self.driver.execute_script("arguments[0].click();", el)
                return True
            except NoSuchElementException:
                continue
        return False

    def _close_err(self):
        try:
            for b in self.driver.find_elements(By.TAG_NAME, "input"):
                if b.get_attribute("value") == "确定" and b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    return True
        except:
            pass
        try:
            b = self.driver.find_element(By.ID, "ymPrompt_btn_2")
            if b.is_displayed():
                self.driver.execute_script("arguments[0].click();", b)
                return True
        except NoSuchElementException:
            pass
        return False

    def _done(self):
        for id_ in ["_ctp_toolbar_item_button_sendfmbm"]:
            try:
                if self.driver.find_element(By.ID, id_).get_attribute("disabled") is not None:
                    return True
            except NoSuchElementException:
                pass
        return False

    def _worker(self):
        self._log("Running...")
        self.st.set("Running")
        while not self._stop.is_set():
            if self._close_err():
                self.errors += 1
                self._ctr()
                self._stop.wait(0.1)
                continue
            if self._click():
                self.clicks += 1
                if self.clicks % 100 == 0:
                    self._log(f"{self.clicks} clicks, {self.errors} errors")
                self._ctr()
            self._stop.wait(self.speed.get())
            if self._done():
                self._log("SUCCESS — button disabled!")
                self.st.set("DONE")
                self._ctr()
                break

    def _go(self):
        self.clicks = self.errors = 0
        self._ctr()
        self._stop.clear()
        self.sbtn.config(state=tk.DISABLED)
        self.tbtn.config(state=tk.NORMAL)
        self.st.set("Running")
        threading.Thread(target=self._worker, daemon=True).start()

    def _halt(self):
        self._log("Stopped")
        self._stop.set()
        self.lbtn.config(state=tk.NORMAL)
        self.sbtn.config(state=tk.DISABLED)
        self.tbtn.config(state=tk.DISABLED)
        self.st.set("Stopped")
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

# ============================================================
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--build":
        self_build()
    else:
        root = tk.Tk()
        ClickApp(root)
        root.mainloop()
