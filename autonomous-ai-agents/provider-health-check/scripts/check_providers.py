#!/usr/bin/env python3
"""Hermes 全 provider/模型健康探针。

逐个发最小 chat 请求（max_tokens=32 — poe 要求 >=16），输出 ✅/❌ 表。
2026-08-28 全端点实测验证。新增 provider 在 PROVIDERS 表加一行。

坑位（勿删，都是踩过的）:
- opencode.ai 有 Cloudflare UA 指纹拦截: python urllib 默认 UA 一律 403(1010)，
  必须 curl + 浏览器 UA + --http2
- ark 的 key 在 config.yaml providers.volcengine-agent-plan.api_key，不在 .env
- /v1/models 列表含已下线模型，必须逐个 chat 才算数
- 500 重试 3 次+换参数仍 500 = 服务端故障，标记挂了等修复
"""
import json
import os
import re
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def load_env():
    env = {}
    path = os.path.join(HOME, ".hermes", ".env")
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


def load_ark_key():
    path = os.path.join(HOME, ".hermes", "config.yaml")
    if os.path.exists(path):
        with open(path) as f:
            m = re.search(r"api_key: (ark-[\w-]+)", f.read())
            if m:
                return m.group(1)
    return ""


def curl_chat(base_url, key, model, timeout=40):
    """curl + 浏览器 UA（绕 Cloudflare 指纹）。返回 (ok, detail)。"""
    payload = {"model": model,
               "messages": [{"role": "user", "content": "hi"}],
               "max_tokens": 32}
    out = "/tmp/_probe_out.json"
    cmd = ["curl", "-s", "-m", str(timeout), "-o", out, "-w", "%{http_code}",
           "--http2", "-A", BROWSER_UA,
           "-H", "Authorization: Bearer " + key,
           "-H", "Content-Type: application/json",
           "-d", json.dumps(payload),
           base_url.rstrip("/") + "/chat/completions"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    code = r.stdout.strip()
    body = ""
    try:
        body = open(out).read()
    except OSError:
        pass
    if code.startswith("2"):
        try:
            d = json.loads(body)
            if d.get("choices"):
                return True, "OK"
            return False, "空响应"
        except Exception:
            return False, "2xx 但响应不可解析"
    err = ""
    try:
        e = json.loads(body).get("error", {})
        err = e.get("message", "") if isinstance(e, dict) else str(e)
    except Exception:
        err = body.replace("\n", " ")[:80]
    return False, f"HTTP {code} {err[:80]}".strip()


def main():
    env = load_env()
    ark = load_ark_key()

    PROVIDERS = [
        # (显示名, base_url, key, [models])
        ("opencode-go", "https://opencode.ai/zen/go/v1",
         env.get("OPENCODE_GO_API_KEY", ""),
         ["gpt-5.6-luna", "kimi-k3", "glm-5.3", "glm-5.3-flash", "glm-5.2",
          "deepseek-v4-pro", "deepseek-v4-flash", "qwen3.8-max",
          "minimax-m3", "minimax-m2.5", "mimo-v2.5", "longcat-2.0", "hy3"]),
        ("volcengine-ark", "https://ark.cn-beijing.volces.com/api/plan/v3", ark,
         ["doubao-seed-2-0-pro-260215", "glm-5.2", "kimi-k2.7-code",
          "deepseek-v4-pro-260425", "minimax-m3"]),
        ("zai", "https://api.z.ai/api/paas/v4", env.get("GLM_API_KEY", ""),
         ["glm-5.3-flash", "glm-4.7"]),
        ("poe", "https://api.poe.com/v1", env.get("POE_API_KEY", ""),
         ["Claude-Sonnet-4.6", "GPT-5.4"]),
    ]

    results = []
    for name, base, key, models in PROVIDERS:
        if not key:
            for m in models:
                results.append((f"{name} / {m}", False, "无 key，跳过"))
            continue
        for m in models:
            ok, msg = curl_chat(base, key, m)
            results.append((f"{name} / {m}", ok, msg))
            time.sleep(0.5)

    print(f"{'模型':<48} 详情")
    print("-" * 88)
    alive = 0
    for name, ok, msg in results:
        alive += ok
        print(f"{'✅' if ok else '❌'} {name:<46} {msg}")
    print("-" * 88)
    print(f"可用 {alive}/{len(results)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
