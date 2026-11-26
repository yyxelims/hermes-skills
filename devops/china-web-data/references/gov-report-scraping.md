# 政府工作报告批量爬取

## 场景
抓取北京市及16区2025年政府工作报告全文。

## 可行方法

### 1. 百度AI搜索定位URL
```python
from baidu_search import search
r = search("{区名} 2025 政府工作报告 site:gov.cn")
# 从 references 中提取 .gov.cn 域名下含"政府工作"的链接
```

### 2. Python requests 抓取
```python
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
# 剥HTML
text = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.S)
text = re.sub(r'<[^>]+>', '\n', text)
```

### 3. 编码处理（关键！）
北京各区政府网站编码不统一：
- **UTF-8**: 海淀区(zyk.bjhd.gov.cn)、大部分gov.cn域名
- **GBK**: 朝阳区(bjchy.gov.cn)、通州区(tongzhou.gov.cn)
- 检测方法：`r.content.decode('utf-8')` 试一次，看汉字数 > 100 就对了

### 4. PDF附件
部分区的报告是PDF：
- 房山区: `bjfsh.gov.cn/zwgk/zcwj/...pdf`
- 顺义区: `smebj.cn` 第三方附件
- 提取: `pdftotext file.pdf output.txt`

### 5. 浏览器绕过WAF
西城、海淀等区政府有Cloudflare/WAF保护，requests直接访问返回空白。
**解决**: 用浏览器工具直接打开门户网站 → 搜索"政府工作报告" → 获取URL → 再用requests抓。

## 常用URL模式

| 区 | 报告URL模式 |
|----|-----------|
| 北京市 | beijing.gov.cn/zhengce/zhengcefagui/202501/... |
| 东城区 | bjdch.gov.cn/zwgk/ghjh/zfgzbg/... |
| 西城区 | bjxch.gov.cn/xxgk/xxxq/pnidpv... |
| 海淀区 | zyk.bjhd.gov.cn/zwdt/xxgk/zfgzbg/... |
| 通州区 | tongzhou.gov.cn/tzqrmzf/zfgzbg1/... |
| 昌平区 | bjchp.gov.cn/cpqzf/xxgk2671/zfbg/... |

## 实战结果
2025年北京市政府工作报告批量抓取：
- 成功率：15/16 区（缺密云区，全文未公开索引）
- 总字数：209,089 汉字
- 工具链：百度AI搜索 → requests+regex → 浏览器WAF绕过 → pdftotext

## 密云区特例
密云区政府网站只发布"重点任务清单"而非完整报告正文，全网搜索均未找到。
