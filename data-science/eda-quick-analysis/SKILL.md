---
name: eda-quick-analysis
description: |-
  快速探索性数据分析 (EDA) — 对任何表格数据 (CSV/Excel/DataFrame) 进行全面的自动化分析，
  生成结构化 HTML 报告。触发词: "分析这个数据", "数据探索", "EDA", "数据长什么样",
  "看看这个数据集", "描述性统计"。
tags: [eda, data-analysis, pandas, visualization, html-report]
---

# EDA 快速分析 Skill

## 触发条件
用户提供文件路径或已加载的 DataFrame，说"分析数据"/"EDA"/"看下数据情况"等。

## 执行方式

### 方式A: 直接运行模板脚本 (简单场景)
```bash
python {SKILL_DIR}/templates/eda_run.py <文件路径> [--target 列名] [--sample 5000]
```
报告输出: `outputs/eda_report.html`

### 方式B: 分步交互分析 (复杂场景，数据已加载)
在 Python 中分步执行，每步向用户解释发现：

```python
import pandas as pd, numpy as np
# 1. 加载
df = pd.read_csv(path, encoding='utf-8')  # 失败时尝试 gbk
print(f"形状: {df.shape}, 类型分布:\n{df.dtypes.value_counts()}")

# 2. 缺失值 — 重点关注 >30% 缺失的列
miss = df.isnull().mean().sort_values(ascending=False)
print(f"缺失率 >30%: {miss[miss > 0.3].index.tolist()}")

# 3. 数值列 — describe() + 偏度 + 零值率
num_stats = df.describe().T
num_stats['零值率'] = (df.select_dtypes('number') == 0).mean()
print(num_stats)

# 4. 类别列 — 基数 + TOP 频次
for c in df.select_dtypes('object'):
    vc = df[c].value_counts()
    print(f"{c}: {len(vc)} 类, TOP3={vc.head(3).to_dict()}")

# 5. 如有目标列 — 分组对比
if target_col and target_col in df.columns:
    top_diff = df.groupby(target_col).mean().diff().iloc[1].abs().sort_values(ascending=False).head(10)
    print(f"与 {target_col} 最相关的特征 TOP10:\n{top_diff}")

# 6. 生成报告
exec(open('{SKILL_DIR}/templates/eda_run.py').read().split("if __name__")[0])
analyze_and_report(df, target_col=target_col)
```

## 传递给模型的关键信息
当 skill 加载后，模型应主动提取并告诉用户：
1. **数据规模**: 行数×列数，太大要建议采样
2. **缺失情况**: 哪些列缺失严重，建议怎么处理
3. **数据类型**: 多少数值列/类别列，类别列的基数
4. **异常值**: 数值列的异常比例
5. **相关性**: 强相关特征对 (建模时注意共线性)
6. **目标分析**: 如果有目标列，找出区分度高的特征
7. **数据质量建议**: 删除/填充/编码的具体建议

## 注意事项
- CSV 先 UTF-8，失败后尝试 GBK/GB2312
- 大表 (>10万行) 全局统计 + 可视化采样 5000 行
- 所有图表浅色主题，中文 PingFang SC / Microsoft YaHei
- 异常值用 IQR × 1.5，不假设正态分布
- 强相关阈值 0.7
