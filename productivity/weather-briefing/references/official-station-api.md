# 中国天气网官方数据端点（北京站，实测 2026-09-21）

所有请求必须带 `Referer` 与 UA，否则可能被拦：

```bash
curl -s -m 25 \
  -H "Referer: http://www.weather.com.cn/" \
  -H "User-Agent: Mozilla/5.0" \
  "https://d1.weather.com.cn/sk_2d/101010100.html" -o /tmp/sk.js
```

> 终端提示：`Referer: http://...` 是明文 HTTP，会触发安全审批。无人值守场景请把 curl 拆成独立命令落盘，再 read_file 读；不要 `curl | python3`。

---

## 1. 实况 `d1.weather.com.cn/sk_2d/101010100.html`

北京 city code = `101010100`（某城区/某片区同属该站）。返回 `var dataSK={...}`：

```json
{"nameen":"beijing","cityname":"北京","city":"101010100",
 "temp":"24.3","tempf":"75.7",
 "WD":"北风","wde":"N","WS":"1级","wse":"4km/h",
 "SD":"70%","sd":"70%",
 "qy":"1015","njd":"5km",
 "time":"09:20","rain":"0","rain24h":"0","aqi":"35","aqi_pm25":"35",
 "weather":"晴","weathere":"Sunny","weathercode":"d00",
 "limitnumber":"1和6","date":"09月21日(星期一)"}
```

| 字段 | 含义 |
|---|---|
| `temp` / `tempf` | 气温 °C / °F |
| `SD` / `sd` | **相对湿度 %（官方实况，湿度以此为准）** |
| `WD` / `wde` | 风向中文 / 英文 |
| `WS` / `wse` | 风力等级 / 风速 |
| `qy` | 气压 hPa |
| `njd` | 能见度 km |
| `aqi` / `aqi_pm25` | 空气指数 |
| `time` | **本地**更新时间（09:20 即北京时间） |
| `weather` | 天气中文（晴/多云…） |
| `rain` / `rain24h` | 当前/24h 降水量 |
| `limitnumber` | 北京当日限行尾号 |

## 2. 当天预报 + 预警 `d1.weather.com.cn/dingzhi/101010100.html`

```js
var cityDZ101010100 ={"weatherinfo":{"city":"101010100","cityname":"北京",
  "fctime":"202609210800","temp":"29℃","tempn":"18℃","weather":"晴",
  "weathercode":"d0","weathercoden":"n0","wd":"南风","ws":"<3级"}};
var alarmDZ101010100 ={"w":[]}
```

- `temp` = 白天最高，`tempn` = 夜间最低，`fctime` = 预报生成时间（`YYYYMMDDHHmm`）。
- `alarmDZ.w` 为空数组 ⇒ 当日北京无气象预警。

## 3. 生活指数 `d1.weather.com.cn/weather_index/101010100.html`

同一文件里含 `dataZS.zs`，可直接引用官方措辞：

- `co_*` 舒适度（例："较舒适 / 白天晴，早晚凉爽、舒适，午后偏热"）
- `uv_*` 紫外线（例："很强 / 涂擦SPF20以上，PA++"）
- `ct_*` 穿衣、`pl_*` 空气污染扩散、`yd_*` 运动、`gm_*` 感冒、`ls_*` 晾晒、`xc_*` 洗车

这比自己编出行建议更权威，直接翻译进"出行建议"段落。

## 4. 预警全局核验 `www.nmc.cn/rest/findAlarm`

```bash
# 全国列表
curl -s "http://www.nmc.cn/rest/findAlarm?pageNo=1&pageSize=30"
# 省级过滤
curl -s "http://www.nmc.cn/rest/findAlarm?pageNo=1&pageSize=30&province=北京市"
```

返回结构：

```json
{"code":0,"data":{"page":{"count":0,"list":[],"totalPage":1},
 "provinceAlarms":[],
 "stat":{"province":{"r":0,"b":0,"y":0,"o":0}, ...}}}
```

- `data.page.count = 0` 且 `provinceAlarms` 为空 ⇒ 北京无生效预警。
- 全国列表的 `list` 项含 `title`（如"河北省沧州市东光县气象台发布雷电黄色预警信号"），`province` 字段常为 `null`，看 title 前缀判断省份。
- `stat` 里 `r/b/y/o` = 红/橙/黄/蓝数量。

## 5. 不通的路径（别再试）

`d1.weather.com.cn/weather1d/101010100.html`、`d1.weather.com.cn/hour3/101010100.html`、`d1.weather.com.cn/mweather/101010100.shtml` 全部返回 302 空跳转。
逐小时走势改用 wttr.in `?format=j1`。

## 6. 2026-09-21 wttr vs 官方 实测差异（湿度）

| 时点 | wttr.in | 官方 sk_2d |
|---|---|---|
| 湿度 | 45%（露点 10°C） | **70%**（换算露点 **18.0°C**） |
| 气温 | 23°C | 23.8°C |
| 风 | 北风 微风 | 东北风 2级 |
| 能见度 | 8 km | 5 km |
| AQI | — | 36 |

同一时刻，wttr 的湿度比官方低 25 个百分点、露点低 8°C —— 足以把"闷热易出汗"写成"干爽"。
**结论：湿度/露点/能见度以官方为唯一口径，wttr 只用来取逐小时天气走势。**
