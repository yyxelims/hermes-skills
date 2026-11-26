---
name: tikhub-api
description: TikHub API 客户端用法与实测状态。Use when 调TikHub抓公众号/抖音/微博数据。
---

# TikHub API

## 资产位置
- 客户端脚本: `~/.hermes/scripts/tikhub.py`（库 + CLI 双用法）
- 密钥文件: `~/.hermes/tikhub_key.json` → `{"api_key": "...", "base_url": "https://api.tikhub.io"}`
- OpenAPI 全量文档（1066 端点）: https://api.tikhub.io/openapi.json （本地缓存 /tmp/tikhub_openapi.json，重启后需重拉）

## 用法
```python
import sys; sys.path.insert(0, "/Users/you/.hermes/scripts")
from tikhub import call, TikHubError
r = call("POST", "/api/v1/wechat_mp/v2/fetch_account_articles",
         json_body={"username": "gh_xxx", "page_size": 10, "raw": False})
```
```bash
python3 ~/.hermes/scripts/tikhub.py GET  /api/v1/tikhub/user/get_user_info
python3 ~/.hermes/scripts/tikhub.py POST /api/v1/wechat_mp/v2/fetch_article_detail '{"url":"...","raw":false}'
```

## 实测状态（2026-09-03）
- ✅ `/api/v1/tikhub/user/get_user_info`（账户信息）
- ✅ `/api/v1/wechat_mp/v2/fetch_account_profile`（公众号资料）
- ✅ `/api/v1/wechat_mp/v2/fetch_account_articles`（文章列表，返回真实标题）
- ⚠️ 403 维护中（TikHub 平台侧禁用，防错误计费，不是密钥问题，需隔天重试）:
  - `/api/v1/wechat_search/v2/fetch_search`（搜一搜——用户想要的"补充搜索能力"核心，截至 09-03 仍不可用）
  - `/api/v1/wechat_mp/v2/fetch_article_detail`（文章详情）
- 官方测试 gh 号: `gh_363b924965e9`（OpenAPI 示例值，实测有数据；自己猜的 gh 号会返回空）

## 坑
1. `page_size` 最小 10，传 5 报 422。
2. 微信三件套（搜一搜/公众号/视频号）全是 **POST + JSON body**，不是 query 参数。
3. 大部分端点有 `raw` 参数: true=原始响应（体积巨大），false=精简解析（推荐）。
4. 403 "under maintenance" = 平台关了该端点，密钥没问题；换个同类端点或等恢复。
5. 终端 curl/terminal 调用易空返回（老坑），用 execute_code 或脚本文件跑。
6. 计费按次，错误请求一般不计费（维护期 403 明确不计费）。
