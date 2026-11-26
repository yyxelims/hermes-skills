---
name: image-to-excel
description: Use when 用户给图片/海报/截图要转成表格或Excel。同回合建表交付+stdlib校验。
---

# 图片内容 → Excel 转表格

## 触发
用户给一张图（盘点海报、地图信息图、榜单截图）说"转成表格/Excel/汇总表"。

## 流程（一个回合内一口气完成）
1. **一次看图**：vision 读图一遍，把每条记录提取为字面 Python 数据列表写在建表脚本里。字段名、场地名、地址**逐字保留原文**，不意译、不合并、不省略字段；图上自带的汇总数字（如各区场次）单独记下作校验基准。
2. **建表**：openpyxl 做单张平面表 + 类别列（如"区域"），不要复刻图的分区卡片版式。列序参考：序号/类别/名称/地址/各属性字段。
3. **运行**：terminal 直接 `python3 build.py`（openpyxl 在会话 terminal 环境可用）。
4. **校验**：用下面的 stdlib 解包方案逐行读回，Counter 按类别计数，与图上汇总数字逐组核对，全部对上才算完成。
5. **交付**：回复给 MEDIA: 绝对路径 + 一行结论（总条数、各组分布）。

## 交付节奏红线
加载本 skill 后停下来"思考"会被当场催（用户原话："你倒是给我写excel啊，在这思考啥呢？""给我弄出来excel啊，你干啥呢？"）。skill 加载完必须同回合直接产出文件，禁止出现"我接下来会…"式空转回复；图再大、提取再慢也不许中途停顿等用户喊继续。

## 样式（该用户 Excel 交付惯例）
表头深蓝 #2F5597 白字加粗、首列浅蓝 #D9E2F3、冻结 B2、自动筛选、自动换行、字体 Noto Sans SC。

## 校验：不依赖 openpyxl
生成的 xlsx 可能没有 sharedStrings.xml（openpyxl 某些路径写 inline string），校验必须处理 `t="inlineStr"`：

```python
import zipfile
from xml.etree import ElementTree as ET
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
with zipfile.ZipFile(path) as z:
    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
def val(c):
    if c.get("t") == "inlineStr":
        return "".join(t.text or "" for t in c.iter(f"{M}t"))
    v = c.find(f"{M}v")
    return "" if v is None else (v.text or "")
rows = sheet.find(f"{M}sheetData").findall(f"{M}row")
```

逐行取值后分组计数，对比图上汇总数（如 海淀4/西城4/东城11/朝阳14/通州1）。

## 坑
- Pyright 对 openpyxl 的 `wb.active`、`ws.append` 等报 reportOptionalMemberAccess 是类型推断噪音，不影响运行，别为此改代码。
- 建表脚本的 stdout 偶尔捕获为空但文件已生成，别依赖脚本 stdout 判断成败，以解包校验为准。
- 校验永远用上面的 stdlib 方案，不 import openpyxl（部分子进程 python 环境没有它）。
