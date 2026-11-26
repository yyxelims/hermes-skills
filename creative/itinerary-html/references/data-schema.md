# 数据结构（通用）

HTML 模板依赖 5 个数据对象。**字段含义固定，与具体行程无关**。

---

## 1. AMAP_KEY / AMAP_SECURITY

高德地图 JS API 凭证。

```javascript
const AMAP_KEY = '<用户提供的高德 Web 端 JS Key>';
const AMAP_SECURITY = '<对应的 securityJsCode>';
```

**这两个 Key 必须配套**：
- `AMAP_KEY` 用在 `https://webapi.amap.com/maps?v=2.0&key=...`（地图加载）
- `AMAP_SECURITY` 用在 `window._AMapSecurityConfig = { securityJsCode: ... }`（白名单）

如果用户只给了 Web 服务 Key（用于 REST API 查坐标），**这两个 Key 用户没提供，要问用户**。

---

## 2. TRIP（主数据，必填）

每个 POI 一条记录。

```javascript
const TRIP = [
  {
    day: 1,                  // Day 编号（从 0 开始，连号）
    time: '08:30',           // 时间字符串，HH:MM 或 "次日 06:42"
    type: 'must',            // 类型，见下表
    icon: '🦁',              // emoji（视觉标识，1 个字符）
    name: 'POI 显示名',       // 用户给的原名（不要加 emoji 装饰）
    desc: '一句简述',        // 不超过 30 字
    city: 'foshan',          // 城市名（用于天气坐标查表）
    lng: 113.112990,         // 经度（高德核实）
    lat: 23.029738,          // 纬度（高德核实）
    info: { ... }            // 可选，见下
  }
];
```

### type 取值约定

| 值 | 颜色 | 用于 |
|---|---|---|
| `must` | 赭红 | 核心必看 |
| `scenic` | 青绿 | 普通景点 |
| `food` | 橙红 | 餐饮 |
| `hotel` | 紫色 | 住宿 |
| `transit` | 蓝色 | 车站/机场 |

如果用户的行程有新的类型（如 `shopping` 购物、`show` 看演出），**在 `template-*.html` 里加对应的 type 颜色 + TYPE_NAME 中文名**。

### info 子字段（全部可选，缺则该小节不显示）

```javascript
info: {
  ticket: '¥20',                  // 门票 / 人均
  hours: '08:30-18:00',          // 营业时间
  duration: '2-3h',              // 建议时长
  best: '9:30 入园先拿时刻表',   // 最佳玩法
  booking: '需提前 7 天预约',    // 预约说明
  photo: ['🔥 红墙斜光', ...],   // 拍照建议
  tips: ['汉服绝配', ...]         // 贴士
}
```

**禁瞎编**字段：`ticket / hours / duration / best / booking / photo / tips`。拿不准就**留空**让小节自动隐藏。

---

## 3. TRANSIT_HINTS（段间交通，强烈建议填）

key 格式 `"<day>:<order>"`，描述**从这个 POI 出发到下一个 POI 的交通方式**。

```javascript
const TRANSIT_HINTS = {
  '1:2': {                         // D1 第 2 个 POI 的下一段
    mode: '🚄 火车/航班/城际（任意交通工具）',
    from: '起点城市/站名',
    to: '终点城市/站名',
    depart: 'HH:MM',
    arrive: 'HH:MM',
    nextDay: false,                // true 表示 arrive 是次日时间
    cost: '¥X',
    time: 'X 分钟/X 小时'
  }
};
```

### key 编号规则

第 N 个 POI 的下一段交通是 `day:N`，**不是** `day:N-1`。

例：
- TRIP 里 D1 第 2 条是车站 A → 那 `1:2` 是**从车站 A 出发到下一站 B 的交通**

### 哪些段需要填

只在**两个 POI 之间有明显交通需求**时填：
- ✅ 城市之间（A 城 → B 城）
- ✅ 不同区域之间（远距离的景点 → 景点）
- ❌ 同一景区内步行（两个 POI 相邻 5 分钟步行，可不填）

### 拿不准就**整段不填**，不要瞎编车次/航班号

---

## 4. HOTELS（酒店 tab 专用，可选）

如果用户的行程没有"酒店清单" tab 需求（如一日游、跟团游），可以**整个删除 HOTELS** 以及相关的 `renderHotelView` / `.hotel-view` 样式 + Tab。

```javascript
const HOTELS = [
  {
    day: 'D1-D2',                  // 入住日期范围（用户给的原样）
    name: '酒店全名（含括号分店名）',
    type: '连锁商旅',              // 用户给的类型
    nights: 2,                     // 入住晚数
    checkIn: '2026-08-01',
    checkOut: '2026-08-03',
    address: '街道+门牌号',
    price: '¥447/2 晚',
    total: '¥447',
    order: 1                       // 显示顺序
  }
];
```

---

## 5. DAY_META（Day 标题）

```javascript
const DAY_META = {
  0: {title: 'D0 · ...', subtitle: '...'},
  1: {title: 'D1 · ...', subtitle: '...'}
};
```

title 用 `"D{n} · {城市/地点}·{主题}"`，subtitle 一句话点明核心。

### 如果行程是单日

只用 `0: {...}` 一个键，模板能正确处理。

### 如果行程超过 7 天

模板默认 D0-D6。如果用户行程 8+ 天，**需要扩展 DAY_META 键**，并在 HTML 里加对应 day-pill。

---

## 6. WEATHER_COORDS（天气坐标表，必填）

模板用 `WEATHER_COORDS[day]` 查每天天气。**key 必须覆盖 TRIP 里出现过的所有 day**。

```javascript
const WEATHER_COORDS = {
  0: {lat: 0, lng: 0, name: '城市A'},  // 用 TRIP 中 D0 主要城市的一个 POI 坐标
  1: {lat: 0, lng: 0, name: '城市B'},
  ...
};
```

**如何获取这个表**：
- 优先用当天 TRIP 里**主要城市**的一个 POI 坐标（直接从 TRIP 数组复制 lng/lat 即可）
- 例如 D1 主要在某城市，取 TRIP 里 D1 第一个 POI 的 `lng/lat`
- 不用专门查，每个 day 复制主 POI 的坐标即可

### 国际行程

Open-Meteo **支持全球**，lng/lat 用 Google Geocoding 查出来的。`name` 字段仅用于显示，可以省略。

---

## 7. TRIP_DATES（每天对应日期，必填）

```javascript
const TRIP_DATES = ['2026-07-31', '2026-08-01', ...];
```

长度必须 >= 行程天数。

**如何获取**：问用户行程的出发日期，按 day 顺序往后加一天。如果用户说"下周末出发"，问具体日期。

---

## 8. TYPE_NAME（类别中文名映射）

```javascript
const TYPE_NAME = {transit:'交通', food:'美食', hotel:'住宿', scenic:'景点', must:'必看'};
```

如果加了新 type（如 shopping），这里也要加。

---

## 自动计算的字段

`order`（POI 在当天内的序号）由代码自动算，**不要手动填**。

---

## 不要写进 HTML 的字段

- ❌ 用户没提到的细节（价格、时间、电话）
- ❌ 主观形容词（"美""值得"）
- ❌ 第三方评分（"4.5 分"）
- ❌ 用户没说的 POI（即使你"知道"这个地方）

如果用户问"那 XX 景点要不要也加上？"，**这是用户在主动扩展**，按用户意愿加。如果用户没说，**绝不主动加**。