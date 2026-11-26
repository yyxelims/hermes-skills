---
name: alibaba-cloud-oss
description: "Use for 阿里云 OSS (对象存储): oss2 SDK, buckets, ACL, CDN."
version: 1.0.0
tags: [alibaba-cloud, oss, object-storage, aliyun, miniprogram, cdn]
---

# 阿里云 OSS（对象存储）

## 什么时候用
存文件（图片/PDF/JSON/附件），或做「只读小数据」的静态托管后端（如微信小程序直接 fetch 一份 data.json）。**不是数据库、不是服务器。**

## 省钱要点（按量付费 vs 资源包）
- OSS 默认就是**按量付费，没有「计费方式」开关**。只要不去买「资源包/预留空间」就是按量付费。
- <1MB 数据月成本 ¥0.00x（存储 ¥0.12/GB/月 + 流量 ¥0.5/GB）；买 40GB 资源包（¥9/年）纯浪费。
- 存储类型选「标准存储·本地冗余 LRS」（最便宜标准档）；别选同城冗余 ZRS（贵）、低频/归档（读慢，要天天读）。

## 建 Bucket 勾选清单
| 项 | 选什么 |
|----|--------|
| 存储类型 | 标准存储 |
| 冗余类型 | 本地冗余 LRS |
| 读写权限 | 公共读（要匿名公开访问）或 私有（走 CDN 回源鉴权） |
| 版本控制 | 不开 |

## oss2 SDK 要点
```python
import oss2
auth = oss2.Auth(ak, sk)
bucket = oss2.Bucket(auth, endpoint, bucket_name)  # endpoint 是区域地址，不含 bucket 名

# 上传
bucket.put_object_from_file('data.json', local_path,
    headers={'Content-Type': 'application/json; charset=utf-8',
             'Cache-Control': 'max-age=300'})

# 设公共读（账号开「禁止公共读写」时会 403，见下）
bucket.put_bucket_acl(oss2.BUCKET_ACL_PUBLIC_READ)               # 整桶
bucket.put_object_acl('data.json', oss2.OBJECT_ACL_PUBLIC_READ)  # 单对象（最小权限）
```
- endpoint 例：`https://oss-cn-beijing.aliyuncs.com`（**不含 Bucket 名**，bucket 名单独传）
- 对象 URL：`https://{bucket}.{region}.aliyuncs.com/data.json`

## 坑：账号「禁止公共读写」管控
阿里云新账号常默认开启。SDK 设公共读时，对象级、桶级都会被拦，报 403：
- `Put public bucket acl is not allowed`（`put_bucket_acl(PUBLIC_READ)`）
- `Put public object acl is not allowed`（`put_object_acl(PUBLIC_READ)`）

**解决：走 CDN 回源鉴权**——bucket 保持私有，CDN 用 AK 读私有桶，对外以备案域名 + HTTPS 提供公共访问。这既是生产标准做法，也顺便解决小程序「备案域名 + HTTPS」的硬要求（OSS 默认域名 `xxx.oss-cn-xxx.aliyuncs.com` 非备案域名，小程序真机不能用）。

## 小程序静态后端模式（absorbed from `mini-program-oss-backend`）

Use OSS as a read-only JSON backend when data is small and periodically refreshed: upload `data.json`, fetch once with `wx.request`, then search/filter/paginate locally. Upgrade to a database/API only for large datasets, real-time writes, or server-side queries. Keep the production path as private OSS + CDN origin authentication +备案 HTTPS; development may use the OSS endpoint with domain checking disabled. Convert Chinese JSON keys to English aliases before WXML binding because dot notation does not accept Chinese identifiers. Verify the upload with an HTTP 200 and keep credentials in a config file.

## 静态托管模式（小程序「场景 B」）

This section covers the implementation details for the mini-program pattern:
数据是「每天更新一次、只读、<1MB JSON」时，最省架构：本地脚本打成 `data.json` → 上传 OSS → 前端直接 fetch，**零服务器/数据库/云函数**。「查询」类需求（如共事反查）在客户端算。data.json 结构 `{meta, summary, tabs, leaders}`。小程序侧细节见 `wechat-miniprogram-dev` skill。

### 本地脚本骨架（密钥走配置文件，不进命令行历史）
```python
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--endpoint'); ap.add_argument('--bucket')
    ap.add_argument('--ak'); ap.add_argument('--sk')
    ap.add_argument('--object', default='data.json')
    ap.add_argument('--config', default='oss_config.json')
    ap.add_argument('--no-upload', action='store_true')
    args = ap.parse_args()
    cfg = json.load(open(args.config)) if os.path.exists(args.config) else {}
    for k in ('endpoint', 'bucket', 'ak', 'sk', 'object'):
        if not getattr(args, k):
            setattr(args, k, cfg.get(k, '') or getattr(args, k))
    # ... build data.json ...
    if not args.no_upload:
        bucket.put_object_from_file(args.object, out_path, headers={...})
```

## 坑：Hermes 终端里装 oss2 的 venv 被污染
Hermes 会把自家 site-packages 塞进 `PYTHONPATH`，泄漏进新 venv 导致依赖装不全、跨版本 import 冲突（`numpy._core._multiarray_umath` / `No module named 'six'`）。修复：
```bash
env -u PYTHONPATH .venv/bin/pip install --force-reinstall --no-cache-dir oss2 openpyxl
env -u PYTHONPATH .venv/bin/python script.py
```
在用户自己的普通终端（非 Hermes）里跑则不需要 `env -u PYTHONPATH`。

## 每日刷新 JSON：缓存与定时上传的两个复发坑
「网页每天 fetch 一份 OSS JSON（如 AI 日报 daily.json）」模式的实战教训（2026-09-03，用户看到昨天的日报）：

**坑1：浏览器缓存旧数据——OSS 更新了，用户还是看到昨天的**
页面 fetch 无缓存破坏时，用户在每日更新前打开过页面，浏览器会把旧 JSON 缓存一整天。根治必须两层都做：
- 页面侧：`fetch(url + '?ts=' + Date.now(), {cache: 'no-store'})`（每次打开强制拉新）
- OSS 侧：上传时带响应头 `Cache-Control: max-age=300`（oss2 put headers 或原生签名 PUT 的请求头均可），这样每天更新后最多 5 分钟全网生效。
- 诊断：`curl '公开URL?随机数'` 看 JSON 里的 `date` 字段，与浏览器显示分开验证——OSS 上的数据 ≠ 浏览器渲染的数据，中间隔着一层用户浏览器缓存。

**坑2：cron 定时上传"跑了但没跑"**
cron 任务指向的 wrapper 脚本是空文件（0 字节）→ 每天定时触发但什么都不做，静默无产物。排查顺序：cronjob list 看 last_status / last_run_at → `wc -c ~/.hermes/scripts/<脚本>` 验脚本非空 → 手动跑一遍 → curl OSS 公网 URL 验产物日期。wrapper 模板：
```bash
cd "$HOME/<pipeline目录>" || exit 1
exec python3 <主脚本>.py --config oss.json
```

**零依赖上传替代**：不想装 oss2 时，纯标准库 hmac-sha1 V1 签名即可 PUT/GET（含上传时自定义 Cache-Control 头），完整可运行示例见 `~/Documents/工作/个人网站/pipeline/aihot_daily_pipeline.py`（日报→OSS 管道：daily.json + 按日期归档 + index.json 索引三件套）。

## 密钥安全
- 用 RAM 子账号最小权限（AliyunOSSFullAccess 或更细），别用主账号 key。
- 密钥写本地配置文件（脚本读 config），别贴聊天记录/命令行历史；贴过就提醒用户轮换。

## 备案与本地预览
小程序 `wx.request` 需要备案域名 + HTTPS。备案前本地预览：
```bash
cd import && python3 -m http.server 8000
# 前端 dataUrl 指向 http://127.0.0.1:8000/data.json，开发者工具勾「不校验合法域名」
```
