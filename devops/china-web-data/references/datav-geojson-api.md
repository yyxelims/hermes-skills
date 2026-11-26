# DataV GeoJSON API — Chinese Administrative Boundaries

## Overview

Alibaba Cloud DataV provides a free, no-auth-required GeoJSON API for Chinese
administrative boundaries at all levels: national → provincial → prefecture → county.

**Base URL:** `https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json`

## Adcode Structure

Chinese administrative division codes are 6-digit numbers:

| Digits | Meaning | Example |
|--------|---------|---------|
| XX0000 | Province/Municipality/AR | `110000` = 北京市 |
| XXYY00 | Prefecture-level city | `110100` = 北京市市辖区 |
| XXYYZZ | County/District | `110101` = 东城区 |

Special codes:
- `100000` = 中国 (national boundary, includes all provinces as sub-features)
- `710000` = 台湾省
- `810000` = 香港特别行政区
- `820000` = 澳门特别行政区

## Province-Level Codes (34 total)

```
110000  北京市        340000  安徽省
120000  天津市        350000  福建省
130000  河北省        360000  江西省
140000  山西省        370000  山东省
150000  内蒙古自治区   410000  河南省
210000  辽宁省        420000  湖北省
220000  吉林省        430000  湖南省
230000  黑龙江省      440000  广东省
310000  上海市        450000  广西壮族自治区
320000  江苏省        460000  海南省
330000  浙江省        500000  重庆市
510000  四川省        620000  甘肃省
520000  贵州省        630000  青海省
530000  云南省        640000  宁夏回族自治区
540000  西藏自治区    650000  新疆维吾尔自治区
610000  陕西省        710000  台湾省
                      810000  香港特别行政区
                      820000  澳门特别行政区
```

## URL Patterns

| Level | URL | Returns |
|-------|-----|---------|
| China + all provinces | `100000_full.json` | China boundary + 34 province features (~580KB) |
| Province + all counties | `110000_full.json` | Beijing boundary + 16 district features (~100KB) |
| Single county | `110101_full.json` | Single district boundary |

The `_full` suffix includes all child regions recursively. Without `_full`,
only the parent boundary is returned.

## Response Format

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "adcode": 110000,
        "name": "北京市",
        "center": [116.407, 39.904],
        "level": "province"
      },
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [...]
      }
    }
  ]
}
```

## Extracting Provinces from 100000_full.json

```javascript
const resp = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json');
const data = await resp.json();

// Filter province-level features: adcode ends in '0000' OR is a direct municipality
const provinces = data.features.filter(f => {
  const code = String(f.properties.adcode);
  return code.endsWith('0000') || ['110000','120000','310000','500000'].includes(code);
}).filter(f => f.properties.adcode !== 100000); // remove the China-level feature
```

## Extracting Counties from Province Data

```javascript
const resp = await fetch(`https://geo.datav.aliyun.com/areas_v3/bound/${provinceCode}_full.json`);
const data = await resp.json();

// County features: 6-digit codes that are NOT the province itself
const counties = data.features.filter(f => {
  const code = String(f.properties.adcode);
  return code !== provinceCode && code.length === 6;
});

// Fallback: if no 6-digit codes, try 4-digit (prefecture level)
if (counties.length === 0) {
  counties = data.features.filter(f => {
    const code = String(f.properties.adcode);
    return code !== provinceCode && code.length === 4;
  });
}
```

## Integration with Leaflet

```javascript
const geo = L.geoJSON(geoJSONData, {
  style: { fillColor: '#f5d78c', fillOpacity: 0.6, color: '#e8a020', weight: 1 },
  onEachFeature: (feature, layer) => {
    layer.bindTooltip(feature.properties.name);
    layer.on('click', () => {
      const code = feature.properties.adcode;
      // Handle click...
    });
  },
}).addTo(map);
```

**Pitfall:** Use `L.featureGroup()` not `L.layerGroup()` when you need `.getBounds()`,
`.eachLayer()` for style updates, or map fitting. `L.layerGroup` lacks these methods.

## Performance Notes

- National boundary (100000): ~580KB — loads instantly
- Province boundary: ~100KB — fast
- The API is served via Alibaba Cloud CDN with good response times
- No rate limiting observed (no API key means anonymous access)

## Comparison with Amap API

| Feature | DataV GeoJSON | Amap POI API |
|---------|--------------|--------------|
| Purpose | Geographic boundaries | Point-of-interest data |
| Auth | None required | API key required |
| Free tier | Unlimited (no auth) | 5000/day |
| Data format | GeoJSON | Custom JSON |
| Detail level | County boundaries | Individual POIs |
