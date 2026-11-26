# Poe API Provider Reference

## Summary

Poe (poe.com) provides an OpenAI-compatible API at `https://api.poe.com/v1`. Single API key covers 300+ models from all major labs plus community bots. Uses existing Poe subscription points — no separate billing.

## Quick Start

```python
from openai import OpenAI
client = OpenAI(api_key="***", base_url="https://api.poe.com/v1")
client.chat.completions.create(
    model="Claude-Sonnet-4.6",
    messages=[{"role": "user", "content": "Hello"}],
)
```

## API Key

Get from https://poe.com/api/keys. Format: `sk-poe-<50 chars>`.

## Image Generation

**Critical**: Poe image models work through Chat Completions, NOT `/v1/images/generations`. Must use `stream=False`.

Working models (verified 2026-07):
- `gpt-image-1.5` — ~15s, 1024x1024 PNG, most reliable
- `z-image-lightning` — ~10s, 1024x768 PNG
- `grok-imagine-image` — ~10s, 1024x1024 JPEG

Non-working:
- `flux-2-pro`, `flux-2-flex` — empty response or content-filtered
- `gpt-image-2` — empty response (may need longer timeout)
- `stablediffusion3.5-l`, `qwen-image-2-pro`, `hunyuan-image-3` — empty

Response format: image URLs in `choices[0].message.content` (poecdn.net).

## Endpoints

| Endpoint | Status |
|----------|--------|
| `/v1/chat/completions` | ✅ Text + Image (with `stream=False`) |
| `/v1/responses` | ✅ Reasoning, web search, structured output |
| `/v1/images/generations` | ❌ Returns 403 (use chat instead) |
| `/v1/models` | ✅ Lists all available models |

## Rate Limits

500 requests/minute. Supports request-based rate limit headers. Points-based billing uses existing subscription.

## Migration from OpenAI

1. `base_url` → `https://api.poe.com/v1`
2. `OPENAI_API_KEY` → `POE_API_KEY`
3. Model names use Poe bot names (e.g. `Claude-Sonnet-4.6`)
4. Remove: `n > 1`, audio params, `parallel_tool_calls`
