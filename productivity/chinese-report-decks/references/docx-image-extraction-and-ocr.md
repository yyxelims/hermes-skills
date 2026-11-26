# 从 docx / pptx 里挖图和真实指标

汇报 PPT 最缺的是配图和真实数字。用户的过往 docx / pptx 里往往两样都有，别让他们重新截图。

## 1. 提取 docx 里的所有图

```python
import os, zipfile, shutil
from PIL import Image

z = zipfile.ZipFile("报告.docx")
for n in [x for x in z.namelist() if x.startswith("word/media/")]:
    base = os.path.basename(n)
    if not base:                      # word/media/ 目录本身，跳过
        continue
    dst = os.path.join(OUT, "docx_" + base)
    with z.open(n) as f, open(dst, "wb") as o:
        shutil.copyfileobj(f, o)
    w, h = Image.open(dst).size
    print(f"{base}  {w}x{h}  ratio={w/h:.2f}")
```

**长宽比就是线索**：`0.46` ≈ 手机截图（1260×2736），`1.78` ≈ 电脑全屏截图，`1.33` / `1.14` ≈ 图表，`3.5+` ≈ 通栏宣传图。放版式时按比例决定竖排还是通栏。

## 2. 把每张图定位到它所属的章节（关键）

**不要按文件名顺序猜归属。** 解析 `word/document.xml` 的段落顺序，把 `a:blip/@r:embed` 通过 rels 映射回 media 文件名，就能得到"哪段文字下面挂着哪张图"。

```python
import zipfile
from lxml import etree

Z = zipfile.ZipFile("报告.docx")
doc = etree.fromstring(Z.read("word/document.xml"))
rels = etree.fromstring(Z.read("word/_rels/document.xml.rels"))
R = {r.get("Id"): r.get("Target") for r in rels}
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

for p in doc.find('w:body', ns).iter('{%s}p' % ns['w']):
    txt = "".join(t.text or "" for t in p.iter('{%s}t' % ns['w']))
    imgs = [R.get(b.get('{%s}embed' % ns['r'])) for b in p.iter('{%s}blip' % ns['a'])]
    if txt.strip() or imgs:
        print((txt.strip()[:70] or "(无文字)") + ("   <<< IMG: " + ", ".join(imgs) + " >>>" if imgs else ""))
```

输出形如：

```
政策动态追踪（天天在跑）：
交付：Excel业务版 → HTML看板 → 微信小程序 …
(无文字)  <<< IMG: media/image1.png, media/image2.png, media/image3.png >>>
某支行保险数据建模：
4万客户、8195人真实购买 …
(无文字)  <<< IMG: media/image5.jpeg, media/image6.jpeg >>>
```

→ image1-3 属政策追踪，image5-6 属保险建模。归属确定后再往对应页放，不会错配。

## 3. 提取 pptx 里的图（用户已插入的 / 往期架构图）

```python
from pptx import Presentation
prs = Presentation("deck.pptx")
for i, s in enumerate(prs.slides, 1):
    for k, sh in enumerate([x for x in s.shapes if x.shape_type == 13], 1):
        im = sh.image
        if len(im.blob) < 40000:      # 过滤 logo / 小图标
            continue
        open(f"{OUT}/p{i:02d}_{k}.{im.ext}", "wb").write(im.blob)
```

往期汇报 pptx、竞赛路演 pptx 里的架构图/流程图是现成的高质量配图，直接复用。

## 4. OCR 捞回真实指标

图注写不准、指标记不清时，直接 OCR。macOS 上 `brew install tesseract`（含 163 种语言包）。

```bash
tesseract 建模报告截图.jpeg - -l chi_sim+eng
```

能稳定读出表格里的模型名和数字，例如：

```
模型            综合评分  Precision  F1      Recall   Accuracy
CatBoost 最优   0.8263    0.8473     0.7946  0.7480   0.9221
ROC Curves (验证集)  CatBoost (AUC=0.9729)  LightGBM (AUC=0.9710)
客户聚类 PCA 分布 (GMM K=18)
```

这些就是**可写进 PPT 的真实指标**，比"效果良好"强一百倍。

**⚠️ OCR 出来的数字要和用户文字稿交叉核对，冲突必须上报，不许自己挑一个：**

| 用户文字稿 | 报告截图 OCR | 处理 |
|---|---|---|
| 803 种特征 | 特征数: 223 | 写"累计 803 种，入模 223 个"，并在回复里请用户确认口径 |
| 11 个客群 | GMM K=18 | 正文用 11，图注不写 K 值，回复里列出冲突 |
| 综合评分权重 0.30/0.30/0.30/0.10 | 截图是旧公式 0.4/0.35/0.15/0.1 | 正文只说"四项加权"，不硬编权重，避免和配图自相矛盾 |

纯图形（热力图、无文字图表）OCR 会返回空 —— 这种图注写成"（请确认图注）"并在回复里点名，别硬猜内容。
