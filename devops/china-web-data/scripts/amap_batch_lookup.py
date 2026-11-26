#!/usr/bin/env python3
"""
高德地图 POI 批量查询脚本
用法: 修改 KEY 和 names 列表，运行即可
输出: CSV 文件，包含电话、地址、POI名称
"""
import requests, time, pandas as pd, re

KEY = "YOUR_AMAP_KEY_HERE"
API = "https://restapi.amap.com/v3/place/text"

# ====== 配置区 ======
names = [
    "北京动物园", "北京欢乐谷", "香山公园",
    # 添加更多...
]
CITY = "北京"
OUTPUT = "amap_results.csv"

# ====== 查询 ======
results = []
for i, name in enumerate(names):
    # 先用完整名
    params = {'key': KEY, 'keywords': name, 'city': CITY, 'output': 'JSON', 'offset': 1}
    try:
        r = requests.get(API, params=params, timeout=10)
        data = r.json()

        phone, addr, poi_name = '', '', ''
        if data['status'] == '1' and data['count'] != '0':
            poi = data['pois'][0]
            phone = poi.get('tel', '') or ''
            addr = poi.get('address', '') or ''
            poi_name = poi.get('name', '')
            if addr:
                addr = (poi.get('cityname','') or '') + (poi.get('adname','') or '') + addr
        else:
            # 去"北京"前缀重试
            short = name.replace('北京', '')
            if short != name:
                params['keywords'] = short
                r2 = requests.get(API, params=params, timeout=10)
                d2 = r2.json()
                if d2['status'] == '1' and d2['count'] != '0':
                    p2 = d2['pois'][0]
                    phone = p2.get('tel', '') or ''
                    addr = p2.get('address', '') or ''
                    poi_name = p2.get('name', '')

        results.append({'名称': name, '电话': phone, '地址': addr, 'POI匹配': poi_name})
        print(f"[{i+1}/{len(names)}] {name}: {'☎ '+phone if phone else '未找到'}")

    except Exception as e:
        results.append({'名称': name, '电话': '', '地址': '', 'POI匹配': f'ERR:{e}'})
        print(f"[{i+1}/{len(names)}] {name}: ERR {e}")

    time.sleep(0.3)  # 控制频率，避免触发限流

df = pd.DataFrame(results)
df.to_csv(OUTPUT, index=False)
has = (df['电话'].str.len() > 3).sum()
print(f"\n完成: {has}/{len(df)} 有电话，输出: {OUTPUT}")
