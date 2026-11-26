# Spider_XHS: 小红书数据采集工具

> 仓库: [cv-cat/Spider_XHS](https://github.com/cv-cat/Spider_XHS) | ⭐ 6,300+ | 语言: Python + Node.js | 最后更新: 2026-04

## 是什么

Spider_XHS 是小红书的逆向工程 API 底座。它破解了小红书所有客户端的签名算法（X-S、X-S-Common、X-Rap-Param 等），封装为 Python API，实现程序化数据采集和内容发布。

## 能做什么

| 模块 | 平台 | 能力 |
|------|------|------|
| 数据采集 | PC 端 | 搜索笔记/用户、获取笔记详情（无水印图片+视频）、评论、用户主页、收藏/点赞 |
| 内容发布 | 创作者平台 | 上传图集/视频、定时发布、查看已发布列表 |
| KOL 数据 | 蒲公英平台 | KOL 博主列表、粉丝画像、历史趋势、发起合作 |
| 分销商 | 千帆平台 | 分销商列表、合作品类/商品 |

## 签名破解原理（补环境法）

小红书用 JSVMP（JavaScript 虚拟机保护）混淆了签名算法。Spider_XHS 不逆向 JSVMP 本身，而是在 Node.js 中模拟完整浏览器环境：

1. **手工构建** `window`、`navigator`、`document`、`localStorage`、`screen` 等对象
2. **注入真实密钥**（`localStorage.b1` 和 `sdt_source_storage_key`，从真实浏览器抓取）
3. **加载小红书线上 JS chunk**（从 CDN 拉取 webpack 模块）
4. 让混淆代码在假浏览器中**正常执行**，提取生成的签名参数

核心签名流程：`MD5(api+data) → JSVMP mnsv2 → 自定义 Base64 → "XYS_" + encoded`

## 关键限制

- **必须登录**: 需要真实小红书账号 Cookie（含 a1、webId、websectiga 等）
- **Cookie 有时效性**: 过期后需重新获取
- **b1 密钥会过期**: localStorage 中的密钥是动态下发的
- **签名版本会升级**: 代码硬编码了版本号 `"4.3.2"`，小红书升级时需跟进
- **需 Node.js 20+**: 签名 JS 通过 Node.js 子进程执行
- **仅供学习**: MIT 协议，作者声明禁止商业化

## 环境要求

- Python 3.10+
- Node.js 20+
- `pip install -r requirements.txt && npm install`
- 在 `.env` 中填入登录后的 Cookie

## 对文旅项目的价值

小红书是国内旅游内容的核心平台（景点攻略、打卡笔记、美食推荐）。结合 AI 可以做：

1. **舆情监控**: 搜索"北京故宫攻略"→采集笔记+评论→AI 情感分析→趋势报告
2. **热点发现**: 定时搜索关键词→AI 提取热门话题和新兴打卡点
3. **竞品分析**: 采集同类景区/文旅项目的用户反馈

## 风险提示

频繁请求可能触发封号。建议配合代理使用，降低请求频率。
