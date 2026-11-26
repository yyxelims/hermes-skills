# 各站点抓取详情

## 1. 中国人民银行 pbc.gov.cn

### 领导列表页
- URL: `https://www.pbc.gov.cn/hanglingdao/128697/index.html`
- 方法: urllib + BS4 ✅
- 编码: GBK
- 提取: `<a href="/hanglingdao/128697/\d+/index.html">姓名</a>`
- 输出: 7位领导（潘功胜、朱鹤新、曲吉山、宣昌能、陆磊、陶玲、邹澜）+ 个人页URL

### 领导详情页
- URL 格式: `https://www.pbc.gov.cn/hanglingdao/128697/{id}/index.html`
- 方法: Browser/Playwright（urllib 被302重定向拦截，完全不可用）⚠️
- 简历格式: "姓名，男/女，汉族，YYYY年M月生，EDUCATION，中共党员，现任TITLE。"
- 额外提取: 照片URL、发表文章列表(标题+日期)、重要活动列表(标题+日期)
- 注意: 无详细履历时间线，仅单段式简介

### 政策公告列表
- URL: `https://www.pbc.gov.cn/rmyh/105208/index.html`
- 方法: urllib + BS4 ✅
- 关键数据: 非银行支付机构《支付业务许可证》续展批次

### 支付结算司
- URL: `https://www.pbc.gov.cn/zhifujiesuansi/index.html`
- 方法: urllib + BS4 ✅
- 输出: 60条支付政策（标题+URL，详情页需Browser）
- ⭐支付行业最重要官方源

## 2. 金融监管总局 nfra.gov.cn

### 首页
- URL: `https://www.nfra.gov.cn`
- 方法: Playwright/Browser（纯Angular SPA，urllib拿不到数据）
- 关键: `wait_until='load'`（非`networkidle`，后者频繁超时），然后 `wait_for_timeout(5000)`
- 提取: DOM遍历所有`<a>`标签，根据上下文(bodyText前后500字符)分类
- 栏目: 政策法规(policies)、公告通知(announcements)、监管动态(dynamics)
- 旧路径已失效: `ItemList.html?itemId=917/928/4097` 全部→404

### 政策详情页
- URL 格式: `https://www.nfra.gov.cn/cn/view/pages/ItemDetail.html?docId={docId}&itemId={itemId}`
- 方法: Browser/Playwright
- 提取: `document.body.innerText`
- 注意: 直接导航ItemDetail.html可能超时（大量图片/资源），可接受

### 领导详情页
- URL 格式: `https://www.nfra.gov.cn/cn/view/pages/jigougaikuang/hld-xiangqing.html?{id}`
- ID映射（非递增）: 丁向群=31, 肖远企=18, 丛林=24, 付万军=28, 杨国瑞=?
- 方法: Browser/Playwright
- 简历格式: 单段式简介，含性别/出生/学历/政治面貌/职务

### CDN API（已失效）
- 格式: `{origin}/cn/static/data/{transformed_path}[sorted_params].json`
- transformed_path: 去掉开头的`/`，内部`/`替换为`_`
- params: 按字母排序
- 当前已不可用（2026-08-05验证）

## 3. 国家外汇管理局 safe.gov.cn

### 首页
- URL: `https://www.safe.gov.cn`
- 方法: urllib + BS4 ✅

### 局领导
- URL: `https://www.safe.gov.cn/safe/jld/index.html`
- 方法: urllib/Browser ✅
- 5位: 朱鹤新(局长)、李红燕、徐志斌、李斌、刘斌(副局长)

## 4. 市场监管总局 samr.gov.cn

### 总局领导
- URL: `https://www.samr.gov.cn/jg/`
- 方法: Playwright/Browser（JS渲染）
- 10人: 副局长孟扬/束为/白清元/柳军/邓志勇、纪检组长林国耀、药监局局长黄果、反垄断总监王铁汉、总工刘敏、食安总监孙会川
- 注意: 局长位可能空缺（页面未显示）
- 领导详情页: `https://www.samr.gov.cn/jg/zjld/{id}/index.html`

## 5. 北京金融管理局 jrj.beijing.gov.cn

### 机构名称变更
原「北京市地方金融监督管理局」→ 三块牌子「中共北京市委金融委员会办公室 + 中共北京市委金融工作委员会 + 北京市地方金融管理局」
域名未变: `jrj.beijing.gov.cn`

### 领导页
- URL: `https://jrj.beijing.gov.cn/jgjs/zqgdxx/201901/t20190125_711709.html`
- HTML格式: `<td>name</td><td>title</td>` 表格
- 5位: 曾林峰(局长)、李景祥、王颖、潘琍、闫小娜(副局长)
- 注意: 仅姓名+职务，**无性别/出生/学历**

## 6. 北京市人事任免 beijing.gov.cn

- URL: `https://www.beijing.gov.cn/gongkai/rsxx/rsrm/`
- 文章格式: `<a href="./YYYYMM/tYYYYMMDD_XXXXXXX.html">标题</a>`
- 方法: urllib + BS4 ✅
- 检测逻辑: 对比URL集合，新URL=新任免公告

## 7. 网联清算 nucc.com

- URL: `https://www.nucc.com/newsCenter`
- 方法: Playwright/Browser
- 3个Tab: 公司新闻、媒体报道、行业动态
- Tab切换: 需用`page.evaluate`执行`element.click()`
- 旧域名`nhunionpay.com`已失效，新域名`nucc.com`
- **关键正则** (2026-08-06 修复): 原 regex `(\d{2})\s+(\d{4}\.\d{2})\s+(.{15,120}?)` 不匹配——日期可能为1位（`4`而非`04`），且标题长度限制太死。正确模式：
  ```python
  articles = re.findall(
      r'(\d{1,2})\s+(\d{4}\.\d{2})\s+(.+?)(?=\s*\d{1,2}\s+\d{4}\.\d{2}|\s*(?:1\s*\n|下一页|$))',
      body, re.DOTALL
  )
  ```
- 页面加载策略: 不要每 tab 都 `page.goto()`（重新加载），只需 load 一次 → 点击 tab → `wait_for_timeout(2000)` 即可
- 调试技巧: 先用 `browser_navigate` + `browser_console` 验证 JS 端提取逻辑 → 再写 Python Playwright 代码

## 8. 人行行政许可平台 xzxk.pbc.gov.cn

- URL: `https://xzxk.pbc.gov.cn`
- 方法: Browser
- 11类行政审批事项（含非银行支付机构行政许可、银行卡清算机构准入）
- 查看详情需要法人/个人登录

## 9. 银联 unionpay.com

- ✅ 可用: `www.unionpay.com/upowhtml/cn/templates/newsList-{menuId}/`
  - 银联新闻=01017, 业务公告=01018, 媒体报道=01019, 党建专栏=01004
  - 文章正文直接显示在列表页，无需进详情
- ❌ 旧域名: `unionpay.com.cn` SSL证书CN不匹配

## 10. 财联社 cls.cn

- 电报API: `https://www.cls.cn/api/cache?app=CailianpressWeb&name=telegraphList&os=web&sv=8.7.9`
- 无需签名、无需登录、直接GET
- 脚本: `政策动态追踪/cls_api.py`（已从 ~/quant-lab/cls_api.py 复制到项目目录）

## 11. 北京市市监局 scjgj.beijing.gov.cn

- 领导页: `https://scjgj.beijing.gov.cn/jgzq/ldjs/`
- 方法: urllib ✅ 可用（非JS渲染）
- 9位领导: 高念东(局长)、唐云华、宋同飞、史勍(纪检组长)、李明、周小丰、许泽楠、屈浩鹏(药监局书记)、于爽(巡视员)
- 提取方案: 先用 `strip_tags()` 去HTML，然后对已知名单逐人 `text.find(name)` 定位 + `re.match(r'\s*北京市市场监督管理局\s*([\u4e00-\u9fa5、，,（）()（）/\w]+)', chunk)` 提取职务
- 为什么不用纯正则: 贪婪匹配 `[\u4e00-\u9fa5]+` 会把"党组成员"吃掉，导致交替 `(?:局长|党组成员)` 无内容匹配 → 漏掉宋同飞(仅"党组成员")

## 12. 北京市政务数据局 zwfwj.beijing.gov.cn

- 领导页: `https://zwfwj.beijing.gov.cn/zwgk/qzxx/ldjs/index.html`
- 方法: urllib ✅ 可用
- 8位领导: 沈彬华(局长)、孙舫、彭雪海、朱琴、宋冬娜、张琳(大数据中心主任)、姚磊(热线中心主任)、莽琦(挂职)
- 提取方案: 用HTML结构而非纯文本——`re.findall(r'<span[^>]*><strong>([\u4e00-\u9fa5]{2,4})</strong>', html)` 提取姓名 → `html.find(f'{name}</strong>')` 定位 → `re.search(r'职务：</strong>(.+?)</p>', chunk)` 提取职务
