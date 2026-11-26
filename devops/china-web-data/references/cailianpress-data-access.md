# 财联社 (cls.cn) 数据获取方法与渠道

> 研究日期: 2026-08-03 (更新: 发现无签名公开API) | 财联社 = 中国主流财经新闻集团和财经通讯社

## 核心事实

- 财联社使用 Next.js SSR，多数端点需要签名认证
- 旧接口 `/nodeapi/telegraphList` 已下线 (404)，akshare 也已弃用 cls 支持
- **✅ 发现公开可用的无签名 API**（见下方"直接 API"章节）
- 需要签名的端点：`/v1/roll/get_roll_list`（返回"签名错误"）、`/v2/roll/get_roll_list`（返回"小财正在加载中..."）
- 签名算法仍需逆向时，参考 RSSHub 或 a-stock-data 的源码

## 获取渠道总览

### 1. 直接 API（零依赖，无需签名）⭐ 推荐

**端点**: `GET https://www.cls.cn/api/cache`

| 参数 | 值 | 说明 |
|------|-----|------|
| `app` | `CailianpressWeb` | 固定 |
| `name` | `telegraphList` | 电报列表；也可用 `telegraph` |
| `os` | `web` | 固定 |
| `sv` | `8.7.9` | 版本号（**8.7.9 有效，8.4.6 不行**） |
| `lastTime` | Unix timestamp（可选） | 增量拉取：只返回该时间戳之后的新电报 |

**请求示例**:
```
GET https://www.cls.cn/api/cache?app=CailianpressWeb&name=telegraphList&os=web&sv=8.7.9
Headers: Referer: https://www.cls.cn/telegraph
         User-Agent: (任意浏览器UA)
```

**响应格式**:
```json
{
  "errno": 0,
  "data": {
    "roll_data": [{
      "id": 2444213,
      "type": -1,
      "title": "电报标题",
      "brief": "摘要（通常含完整内容）",
      "content": "正文",
      "ctime": 1785747111
    }]
  }
}
```

**type 字段**: `-1` = 普通电报，`20026` = VIP电报解读（仅标题，内容需付费）。

**增量拉取**: 加上 `&lastTime=<上次最新ctime>` 参数，只返回新电报，适合轮询监控。

**⚠️ 关键发现过程**: 通过浏览器 Performance API 拦截到真实 XHR 请求，发现 `/api/cache` 端点**不需要 sign 参数**。之前以 `sv=8.4.6` 测试的 `/v1/roll/get_roll_list` 确实需要签名，但 `sv=8.7.9` + `/api/cache` 路径完全公开可用。`sv` 版本号是关键。

**可运行脚本**: `/Users/you/quant-lab/cls_api.py` — 零依赖 Python 脚本，支持：
- 获取最新 N 条电报
- 增量轮询监控（`--stream`）
- 单条详情查看（`--detail <id>`）

### 2. 在线服务（零代码）

| 渠道 | 说明 | 费用 |
|------|------|------|
| **Investor RSS** (https://investorrss.waytomaster.com) | 财联社电报转 RSS + AI 摘要，支持 Feedly/Inoreader/NetNewsWire 等阅读器。同一平台还支持巨潮、SEC EDGAR、雪球等 12 个源。 | 付费 |
| **RSSHub** (https://github.com/DIYgod/RSSHub) | 自部署开源 RSS 聚合器，有 `cls/telegraph` 路由。本地/服务器部署后访问 `你的域名/cls/telegraph` 即可获得 RSS 源。 | 免费/自部署 |
| **财联社 VIP** (https://cls.cn/vip) | 官方付费资讯服务：电报解读、风口专家会议等 | 付费 |

### 3. 开源项目（代码级接入）

| 项目 | 仓库 | 要点 |
|------|------|------|
| **cailianpress-unified** | `caimao9539/cailianpress-unified` (GitHub) | Python 财联社统一接口，封装电报和文章数据获取 |
| **a-stock-data** | `skyformat99/a-stock-data`, `ufo6849-web/a-stock-data`, `kilingzhang/a-stock-data`, `doccode/a-stock-data` (GitHub) | A股全栈数据工具包（7层架构28端点13数据源），**零第三方依赖**，直连 HTTP API，包含财联社数据源。V3.0 起完全移除 akshare 依赖。 |
| **briefy** | `Lysander66/briefy` (GitHub) | AI 每日简报，聚合财联社 + 百度 + 今日头条 + 金十数据 + 华尔街见闻，含智能筛选、AI摘要、语音播报 |
| **go-stock** | `ethanli-dev/go-stock` (GitHub) | Go 语言实现，commit 中有 `getnewslist("财联社电报")` 的 API 调用模式 |
| **jiucaihua-android** | `lzx1413/jiucaihua-android` (GitHub) | Android 端财联社数据应用 |

### 4. Python 爬虫路线

CSDN 上的实战教程（2026年更新），注意需要处理反爬：
- "Python爬虫实战:构建稳健的财联社新闻数据采集系统" (weixin_31220401, 2026-07-29)
- "用Python+PyQt5写个桌面财经小工具,上班摸鱼也能看财联社7x24电报" (weixin_26950847, 2026-04-29)
- "如何应对财联社反爬虫机制?" (ask.csdn.net, 2026-01-12)

核心反爬：IP频率限制、请求头签名、动态token。requests/httpx 为主，需要模拟浏览器 headers。

## 推荐方案

| 场景 | 推荐 |
|------|------|
| 最快接入 | **直接 API** (`/api/cache`) — 零依赖，一个 HTTP GET 即可，运行 `/Users/you/quant-lab/cls_api.py` |
| 个人阅读 | Investor RSS 或自部署 RSSHub |
| 量化/分析程序化接入 | clone `a-stock-data`（零依赖，直连HTTP）或直接用 `cls_api.py` |
| 深度定制 | 参考 `cailianpress-unified` 或 RSSHub 的 cls 路由源码 |

## 关键发现：akshare 已无法用 cls

CSDN 文章 (2026-06-08): "ak share财联社挂了" — 根因是财联社下线了 `/nodeapi/telegraphList`，akshare 内置路径死透，升级 akshare 也没用。**现行正确接口需查 RSSHub 获取。**
