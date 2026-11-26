#!/usr/bin/env python3
"""
AI文本检测器 — 基于多维特征的中文AI生成文本检测
方法：困惑度估算 + AI惯用语匹配 + 句式均匀度 + 结构模式检测
纯本地运行，无需API，无需GPU。

用法: python3 ai_detect.py [文件路径]
"""
import re, math, sys
from collections import Counter

AI_PATTERNS = {
    'transition': ['首先','其次','再次','最后','综上所述','总而言之','总的来看','此外','另外','不仅如此','与此同时','另一方面'],
    'structuring': ['在.*方面','通过.*实现','基于.*的','以.*为','具有.*的','起到.*作用','发挥.*功能','呈现.*趋势','提供了.*支撑'],
    'buzzwords': ['赋能','闭环','抓手','痛点','落地','打通','对齐','颗粒度','链路','迭代','沉淀','重构','底层','上层','核心','关键','重要','显著','明显','有效','高效','精准','全面','系统'],
    'sentence_starters': ['该方案','该方法','该系统','本发明','本系统','具体来说','具体而言','这意味着','这表明','这说明','由此可见'],
}

def sentence_stats(text):
    sentences = re.split(r'[。！？；\n\.\!\?\;]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 2]
    if not sentences: return 0, 0, 0, 0
    lengths = [len(s) for s in sentences]
    avg = sum(lengths)/len(lengths)
    var = sum((l-avg)**2 for l in lengths)/len(lengths)
    cv = math.sqrt(var)/avg if avg > 0 else 0
    return len(sentences), avg, var, cv

def perplexity_proxy(text):
    chars = list(text)
    trigrams = [''.join(chars[i:i+3]) for i in range(len(chars)-2)]
    if not trigrams: return 0
    counter = Counter(trigrams)
    total = len(trigrams)
    entropy = -sum((c/total)*math.log2(c/total) for c in counter.values())
    return min(1.0, entropy/10.0)

def detect_ai(text):
    if len(text) < 50: return 0.5, "文本太短"
    entropy = perplexity_proxy(text)
    n_sent, avg_len, var_len, cv = sentence_stats(text)
    total_pat = sum(len(re.findall(p, text)) if cat=='structuring' else text.count(p) for cat, pats in AI_PATTERNS.items() for p in pats)
    pattern_density = min(1.0, total_pat/max(1,n_sent))
    chars = list(text)
    bigrams = [''.join(chars[i:i+2]) for i in range(len(chars)-1)]
    diversity = len(set(bigrams))/len(bigrams) if bigrams else 0
    buzz = sum(text.count(p) for p in AI_PATTERNS['buzzwords'])
    buzz_density = min(1.0, buzz/max(1,n_sent)*5)
    starter = sum(text.count(p) for p in AI_PATTERNS['sentence_starters'])
    starter_density = min(1.0, starter/max(1,n_sent)*3)
    score = 0.25*(1-entropy)+0.20*(1-min(1,cv*2))+0.20*pattern_density+0.15*(1-diversity)+0.10*buzz_density+0.10*starter_density
    return round(score,4), {
        '总分': round(score*100,1), '困惑度(低=AI)': round((1-entropy)*100,1),
        '句式均匀度': round((1-min(1,cv*2))*100,1), 'AI惯用语密度': round(pattern_density*100,1),
        '词汇多样性(低=AI)': round((1-diversity)*100,1), '行业黑话密度': round(buzz_density*100,1),
        '句首格式化': round(starter_density*100,1), '句子数': n_sent, '平均句长': round(avg_len,1)
    }

if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
        score, info = detect_ai(text)
        print(f"文件: {sys.argv[1]}\nAI概率: {score*100:.1f}%\n")
        if isinstance(info, dict):
            for k,v in info.items():
                bar = '█'*int(v/5)+'░'*(20-int(v/5)) if isinstance(v,float) else ''
                print(f"  {k}: {str(v):8s} {bar}")
    else:
        print("用法: python3 ai_detect.py 文件路径")
