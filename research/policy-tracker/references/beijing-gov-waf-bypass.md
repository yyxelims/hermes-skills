# beijing.gov.cn WAF 绕过方案

## 问题
`beijing.gov.cn` 详情页返回 403：
```
您的IP最近有可疑的攻击行为，请稍后重试.
client: 240e:xxxx:xxxx:xxxx, server: ec63fa5
```
这是**创宇盾（知道创宇）WAF**，基于 IPv6 地址 + 行为模式封禁。

## 解决方案：IPv4 + Referer

### 三步走
1. **强制 IPv4**：`socket.getaddrinfo` 限制 `AF_INET`
2. **带 Referer header**：从列表页 URL 作为 Referer
3. **速率控制**：0.25-0.3s/篇，避免触发频率限制

### 代码
```python
import socket
orig = socket.getaddrinfo
socket.getaddrinfo = lambda h, p, f=0, *a, **kw: orig(h, p, socket.AF_INET, *a, **kw)

headers = {
    'User-Agent': 'Mozilla/5.0 ...',
    'Referer': 'https://www.beijing.gov.cn/gongkai/rsxx/rsrm/',  # 列表页 URL
}
req = urllib.request.Request(detail_url, headers=headers)
html = urllib.request.urlopen(req, timeout=15, context=ctx).read()
```

### 注意事项
- IPv4 可用，IPv6 被 WAF 拦截
- 必须带 Referer，否则即使 IPv4 也可能触发 WAF
- 列表页 urllib 直接可达（无需特殊处理）
- 抓取 209 篇详情约需 80 秒（0.25s 间隔）

## 相关脚本
- `脚本/scrape_beijing_gov.py`：北京政务公开网增量抓取
- 抓取范围：`/gongkai/rsxx/rsrm/`（人事任免）+ `/zhengce/zhengcefagui/`（政策法规）
