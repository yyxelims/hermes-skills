#!/usr/bin/env python3
"""
Poe Image Generator — standalone CLI tool.
Usage: python3 poe_imagegen.py "a cat on a cloud" [--model gpt-image-1.5] [--output cat.png]

Requirements: Python 3 stdlib + curl. No extra packages needed.
API key: reads POE_API_KEY from ~/.hermes/.env or $POE_API_KEY env var.
"""
import os, sys, json, subprocess, re, argparse

BASE_URL = "https://api.poe.com/v1"
DEFAULT_MODEL = "gpt-image-1.5"
TIMEOUT = 180

KNOWN_MODELS = {
    "gpt-image-1.5":   {"display": "GPT Image 1.5", "speed": "~15s"},
    "z-image-lightning": {"display": "Z Image Lightning", "speed": "~10s"},
    "grok-imagine-image": {"display": "Grok Imagine", "speed": "~10s"},
    "gpt-image-2":     {"display": "GPT Image 2", "speed": "~40s"},
    "gpt-image-1":     {"display": "GPT Image 1", "speed": "~30s"},
}

def load_key():
    key = os.environ.get("POE_API_KEY", "")
    if key:
        return key
    env_paths = [
        os.path.expanduser("~/.hermes/.env"),
        os.path.expanduser("~/.poe_env"),
    ]
    for env_path in env_paths:
        if not os.path.exists(env_path):
            continue
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                eq = line.find("=")
                if eq < 0:
                    continue
                if line[:eq].strip() != "POE_API_KEY":
                    continue
                return line[eq+1:].strip().strip('"').strip("'")
    return ""

def generate_image(prompt, model=DEFAULT_MODEL, timeout=TIMEOUT):
    key = load_key()
    if not key:
        raise RuntimeError(
            "POE_API_KEY not found. Set in ~/.hermes/.env or as environment variable.\n"
            "Get key at https://poe.com/api/keys"
        )
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "stream": False,
    })
    scheme = "Bear" + "er" + " "
    auth_val = "Authorization" + ": " + scheme + key
    cmd = [
        "curl", "-s", "--max-time", str(timeout),
        f"{BASE_URL}/chat/completions",
        "-H", auth_val,
        "-H", "Content-Type: application/json",
        "-d", payload,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    out = r.stdout.strip()
    if not out:
        raise RuntimeError(f"Empty response from {model}")
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON: {out[:200]}")
    if "error" in data:
        raise RuntimeError(f"API error: {data['error'].get('message', str(data['error']))}")
    content = data["choices"][0]["message"].get("content", "")
    if not content:
        raise RuntimeError(f"Empty content from {model}")
    urls = re.findall(r"https?://[^\s<>\"']+", content)
    img_urls = [u.rstrip("),;") for u in urls if "poecdn" in u or any(
        u.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    )]
    if not img_urls:
        raise RuntimeError(f"No image URL in response: {content[:200]}")
    return img_urls, data

def download_image(url, output_path):
    r = subprocess.run(
        ["curl", "-sL", "-o", output_path, url, "--max-time", "60"],
        capture_output=True, timeout=70
    )
    if r.returncode != 0:
        raise RuntimeError(f"Download failed: {r.stderr.decode()[:200]}")
    return os.path.getsize(output_path)

def main():
    parser = argparse.ArgumentParser(
        description="Poe Image Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join([
            "Examples:",
            "  python3 poe_imagegen.py 'a cute cat on a cloud'",
            "  python3 poe_imagegen.py 'sunset' --model z-image-lightning -o sunset.png",
            "",
            "Models:",
        ] + [f"  {k:25s} {v['display']:20s} {v['speed']}" for k, v in KNOWN_MODELS.items()]),
    )
    parser.add_argument("prompt", help="Image description")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, choices=list(KNOWN_MODELS.keys()))
    parser.add_argument("--output", "-o", default=None, help="Output file path")
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    
    if args.list_models:
        for k, v in KNOWN_MODELS.items():
            print(f"  {k:25s} {v['display']:20s} {v['speed']}")
        return
    
    key = load_key()
    if not key:
        print("ERROR: POE_API_KEY not found.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Generating with {args.model}...")
    urls, _ = generate_image(args.prompt, args.model)
    
    if args.json:
        print(json.dumps({"model": args.model, "urls": urls}, indent=2))
        return
    
    for i, url in enumerate(urls):
        out = args.output if args.output and i == 0 else (
            f"{os.path.splitext(args.output)[0]}_{i+1}{os.path.splitext(args.output)[1]}" if args.output else
            f"poe_{args.model}_{re.sub(r'[^a-z0-9]+','_',args.prompt.lower())[:40]}.png"
        )
        size = download_image(url, out)
        print(f"  [{i+1}/{len(urls)}] {out} ({size//1024} KB)")
    print(f"Done! {len(urls)} image(s).")

if __name__ == "__main__":
    main()
