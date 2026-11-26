#!/bin/bash
# verify_glm.sh — 一键验证 GLM/智谱 key 连通性（测两个端点 + 模型列表）
# 用法: bash verify_glm.sh <GLM_API_KEY>
# 输出: 每个端点的 HTTP 状态码 + 可用模型 ID 列表
set -u

KEY="${1:-}"
if [ -z "$KEY" ]; then
  echo "用法: bash verify_glm.sh <GLM_API_KEY>" >&2
  exit 1
fi

for EP in api.z.ai open.bigmodel.cn; do
  echo "=== $EP ==="
  RESP=$(curl -s -m 15 -w '\n%{http_code}' "https://$EP/api/paas/v4/models" \
    -H "Authorization: Bearer $KEY")
  CODE=$(echo "$RESP" | tail -1)
  BODY=$(echo "$RESP" | head -n -1)
  echo "HTTP $CODE"
  # 简单提取模型 id（无 jq 依赖）
  echo "$BODY" | grep -o '"id":"[^"]*"' | sed 's/"id":"//;s/"//' | tr '\n' ' '
  echo; echo
done
