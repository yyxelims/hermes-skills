#!/usr/bin/env python3
"""EDA 一键分析脚本 — 对任何 CSV/Excel 生成完整 HTML 报告。
用法: python eda_run.py <数据文件路径> [--target 目标列] [--sample 5000]
输出: outputs/eda_report.html
"""
import sys, os, warnings
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt; import seaborn as sns

def load_data(path):
    ext = os.path.splitext(path)[1].lower()
    for enc in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
        try:
            if ext == '.csv': return pd.read_csv(path, encoding=enc)
            if ext in ('.xlsx', '.xls'): return pd.read_excel(path)
        except: continue
    raise ValueError(f"无法读取: {path}")

def _safe_name(s): return str(s).replace('/', '_').replace('\\', '_')[:50]

def analyze_and_report(df, output_path="outputs/eda_report.html", target_col=None, sample_n=5000):
    os.makedirs(os.path.dirname(output_path) or "outputs", exist_ok=True)
    os.makedirs("outputs/figures", exist_ok=True)

    if sample_n and len(df) > sample_n:
        df = df.sample(sample_n, random_state=42)

    n_rows, n_cols = df.shape
    now = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

    # ── 1. 基础信息 ──
    dtypes_count = df.dtypes.apply(lambda x: str(x)).value_counts().to_dict()
    dup_count = df.duplicated().sum()
    mem_mb = df.memory_usage(deep=True).sum() / 1024**2
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    # ── 2. 缺失值 ──
    miss = pd.DataFrame({'缺失数': df.isnull().sum(), '缺失率': df.isnull().mean().round(4)})
    miss = miss[miss['缺失数'] > 0].sort_values('缺失率', ascending=False)
    high_miss = miss[miss['缺失率'] > 0.5] if len(miss) > 0 else pd.DataFrame()

    # ── 3. 数值列统计 ──
    num_stats = pd.DataFrame()
    if num_cols:
        d = df[num_cols].describe().T
        d['偏度'] = df[num_cols].skew()
        d['零值率'] = (df[num_cols] == 0).mean()
        d['异常值(IQR)'] = df[num_cols].apply(lambda x: ((x < x.quantile(0.25)-1.5*(x.quantile(0.75)-x.quantile(0.25))) | (x > x.quantile(0.75)+1.5*(x.quantile(0.75)-x.quantile(0.25)))).mean()).round(4)
        num_stats = d.round(2)

    # ── 4. 类别列统计 ──
    cat_info = []
    for c in cat_cols:
        vc = df[c].value_counts()
        n_uniq = len(vc)
        top5 = vc.head(5).to_dict()
        cat_info.append({'列名': c, '唯一值': n_uniq, '高基数': '是' if n_uniq > 50 else '否', 'TOP1': f"{vc.index[0]} ({vc.iloc[0]/len(df):.1%})"})
    cat_df = pd.DataFrame(cat_info)

    # ── 5. 目标变量 ──
    target_info = ""
    if target_col and target_col in df.columns:
        y = df[target_col]
        pos_rate = y.mean() if y.dtype in (np.float64, np.int64) else (y == y.value_counts().index[0]).mean()
        target_info = f"目标列: {target_col}, 均值={y.mean():.4f}" if y.dtype in (np.float64, np.int64) else f"目标列: {target_col}, 分布={y.value_counts().to_dict()}"

    # ── 6. 相关性 ──
    corr_info = []
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        for i in range(len(num_cols)):
            for j in range(i+1, len(num_cols)):
                if abs(corr.iloc[i, j]) > 0.7:
                    corr_info.append(f"{num_cols[i]} ↔ {num_cols[j]}: {corr.iloc[i,j]:.3f}")

    # ── 7. 可视化 ──
    plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    sns.set_theme(style="whitegrid")

    viz = {}
    try:
        # 缺失值图
        if len(miss) > 0:
            fig, ax = plt.subplots(figsize=(10, max(4, len(miss)*0.3)))
            ax.barh(range(len(miss)), miss['缺失率']*100, color='#ef4444')
            ax.set_yticks(range(len(miss))); ax.set_yticklabels(miss.index, fontsize=8)
            ax.set_xlabel('缺失率 (%)'); ax.set_title('缺失值分析')
            fig.tight_layout(); fig.savefig("outputs/figures/eda_missing.png"); plt.close()
            viz['缺失值分析'] = "figures/eda_missing.png"

        # 相关性热力图
        if len(num_cols) >= 2:
            top_corr = corr if len(num_cols) <= 25 else corr.iloc[:25, :25]
            fig, ax = plt.subplots(figsize=(12, 10))
            sns.heatmap(top_corr, annot=len(num_cols)<=15, fmt='.2f', cmap='RdBu_r', center=0, ax=ax)
            ax.set_title('相关性矩阵')
            fig.tight_layout(); fig.savefig("outputs/figures/eda_corr.png"); plt.close()
            viz['相关性热力图'] = "figures/eda_corr.png"

        # 目标变量分布
        if target_col and target_col in df.columns:
            fig, ax = plt.subplots(figsize=(6, 4))
            df[target_col].value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
            ax.set_title(f'{target_col} 分布'); ax.set_ylabel('')
            fig.tight_layout(); fig.savefig("outputs/figures/eda_target.png"); plt.close()
            viz['目标分布'] = "figures/eda_target.png"
    except Exception as e:
        print(f"  [Viz] 部分图表生成失败: {e}")

    # ── HTML 报告 ──
    miss_rows = "".join(f"<tr><td>{i}</td><td>{int(r['缺失数'])}</td><td>{r['缺失率']:.2%}</td></tr>" for i, r in miss.iterrows()) if len(miss) else "<tr><td colspan=3>无缺失值</td></tr>"
    high_miss_rows = "".join(f"<tr><td>{i}</td><td>{r['缺失率']:.2%}</td></tr>" for i, r in high_miss.iterrows()) if len(high_miss) else "<tr><td colspan=2>无高缺失列</td></tr>"
    num_rows = "".join(f"<tr><td>{i}</td><td>{r['mean']:.2f}</td><td>{r['50%']:.2f}</td><td>{r['std']:.2f}</td><td>{r['min']:.2f}</td><td>{r['max']:.2f}</td><td>{r.get('零值率',0):.1%}</td><td>{r.get('异常值(IQR)',0):.1%}</td></tr>" for i, r in num_stats.iterrows()) if len(num_stats) else ""
    cat_rows = "".join(f"<tr><td>{r['列名']}</td><td>{r['唯一值']}</td><td>{r['高基数']}</td><td>{r['TOP1']}</td></tr>" for _, r in cat_df.iterrows()) if len(cat_df) else ""
    corr_rows = "".join(f"<tr><td colspan=2>{c}</td></tr>" for c in corr_info[:20]) if corr_info else "<tr><td colspan=2>无强相关 (|r|>0.7)</td></tr>"
    viz_block = "".join(f'<div><h3>{k}</h3><img src="{v}"></div>' for k, v in viz.items())

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>EDA 数据分析报告</title>
<style>
:root{{--bg:#f8fafc;--card:#fff;--text:#1e293b;--muted:#64748b;--border:#e2e8f0;--primary:#1a56db;--danger:#ef4444;--warn:#f59e0b}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);padding:28px;line-height:1.7}}
h1{{font-size:1.5rem;color:var(--primary);margin-bottom:4px}}
h2{{font-size:1.1rem;margin:28px 0 12px;border-left:3px solid var(--primary);padding-left:10px}}
h3{{font-size:0.95rem;color:#334155}}
.meta{{color:var(--muted);font-size:0.8rem;margin-bottom:24px}}
table{{width:100%;border-collapse:collapse;margin:10px 0;font-size:0.82rem}}
th,td{{border:1px solid var(--border);padding:6px 10px;text-align:left}}
th{{background:#f1f5f9;font-weight:600}}
tr:hover{{background:#f8fafc}}
.highlight{{background:#fef2f2;border-left:3px solid var(--danger);padding:10px 14px;margin:8px 0;font-size:0.85rem}}
img{{max-width:100%;border:1px solid var(--border);border-radius:8px;margin:8px 0}}
</style></head><body>
<h1>EDA 数据分析报告</h1>
<p class="meta">生成: {now} | 行数: {n_rows} | 列数: {n_cols} | 数值列: {len(num_cols)} | 类别列: {len(cat_cols)} | 内存: {mem_mb:.1f}MB | 重复行: {dup_count}</p>

<h2>1. 数据概览</h2>
<table><tr><th>指标</th><th>值</th></tr>
<tr><td>行数 × 列数</td><td>{n_rows} × {n_cols}</td></tr>
<tr><td>数值列 / 类别列</td><td>{len(num_cols)} / {len(cat_cols)}</td></tr>
<tr><td>缺失率</td><td>{df.isnull().mean().mean():.2%}</td></tr>
<tr><td>重复行</td><td>{dup_count} ({dup_count/n_rows:.2%})</td></tr>
<tr><td>内存</td><td>{mem_mb:.1f} MB</td></tr>
{target_info and f'<tr><td>{target_col}</td><td>{target_info}</td></tr>'}
</table>

<h2>2. 缺失值分析</h2>
<table><tr><th>列名</th><th>缺失数</th><th>缺失率</th></tr>{miss_rows}</table>
{"<div class='highlight'><strong>⚠ 高缺失列 (>50%):</strong><table><tr><th>列名</th><th>缺失率</th></tr>" + high_miss_rows + "</table></div>" if len(high_miss) else ""}

<h2>3. 数值列统计</h2>
<table><tr><th>列名</th><th>均值</th><th>中位数</th><th>标准差</th><th>Min</th><th>Max</th><th>零值率</th><th>异常值率</th></tr>{num_rows}</table>

<h2>4. 类别列分析</h2>
<table><tr><th>列名</th><th>唯一值数</th><th>高基数</th><th>TOP1</th></tr>{cat_rows}</table>

<h2>5. 强相关性</h2>
<table><tr><th colspan=2>|r| > 0.7 的列对</th></tr>{corr_rows}</table>

<h2>6. 可视化</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(400px,1fr));gap:16px">{viz_block}</div>

<h2>7. 数据质量摘要</h2>
{"<div class='highlight'>⚠ 存在高缺失列 (>50%)，建议删除或特殊处理。</div>" if len(high_miss) else ""}
{"<div class='highlight'>⚠ 存在重复行 ({dup_count}行)，建议去重。</div>" if dup_count > 0 else ""}
{"<div class='highlight'>⚠ 存在强相关特征，建模时注意多重共线性。</div>" if corr_info else ""}
<p style="color:var(--muted);margin-top:12px">分析完成。建议: 1) 删除高缺失列 2) 数值缺失用-1哨兵+isnull指示列 3) 高基数类别用目标编码 4) 强相关特征考虑删除或PCA</p>
</body></html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[EDA] 报告已保存: {output_path}")
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python eda_run.py <数据文件> [--target 列名] [--sample N]")
        sys.exit(1)
    path = sys.argv[1]
    target = None; sample = 5000
    for i, arg in enumerate(sys.argv):
        if arg == '--target' and i+1 < len(sys.argv): target = sys.argv[i+1]
        if arg == '--sample' and i+1 < len(sys.argv): sample = int(sys.argv[i+1])
    df = load_data(path)
    analyze_and_report(df, target_col=target, sample_n=sample)
