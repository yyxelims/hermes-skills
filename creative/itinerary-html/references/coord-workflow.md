# 高德 POI 坐标查询工作流

**所有 POI 坐标必须用这个流程查证，禁止凭印象编。**

## 前置

- 用户提供的高德 Web 服务 Key（32 位字符串）
- 能发 HTTPS 请求的工具（PowerShell / curl / Python）

## API 基础（国内 POI）

```
GET https://restapi.amap.com/v3/place/text
    ?key=<用户提供的 Key>
    &keywords=<POI 名称>
    &city=<所在城市>
    &extensions=base
    &offset=1
```

返回 JSON：

```json
{
  "status": "1",
  "pois": [{
    "name": "祖庙博物馆",
    "location": "113.112990,23.029738",   // lng,lat
    "address": "祖庙路 21 号",
    "tel": "0757-82286913",
    "id": "B02F50YS3F",
    "typecode": "110000"
  }]
}
```

## PowerShell 模板（Windows 默认能用）

```powershell
$key = '<用户的 Key>'

function Get-Poi($name, $city) {
  $kwEnc = [uri]::EscapeDataString($name)
  $cityEnc = [uri]::EscapeDataString($city)
  $url = "https://restapi.amap.com/v3/place/text?key=$key&keywords=$kwEnc&city=$cityEnc&extensions=base&offset=1"
  $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 8
  $j = $r.Content | ConvertFrom-Json
  if ($j.status -eq '1' -and $j.pois.Count -gt 0) {
    $p = $j.pois[0]
    [PSCustomObject]@{
      Name     = $name
      Hit      = $p.name
      Location = $p.location
      Address  = $p.address
      Tel      = $p.tel
      Status   = '✅'
    }
  } else {
    [PSCustomObject]@{Name=$name; Status='❌'; Location='—'; Address='—'; Tel='—'}
  }
}

# 批量调用
Get-Poi '酒店全名' '所在城市'
Get-Poi '景点全名' '所在城市'
```

## curl 模板（macOS/Linux）

```bash
KEY='<用户的 Key>'
curl -s "https://restapi.amap.com/v3/place/text?key=$KEY&keywords=$(printf '酒店全名' | jq -sRr @uri)&city=所在城市&extensions=base&offset=1" | jq '.pois[0] | {name,location,address,tel}'
```

## 查询策略（按优先级）

### 1. 先用全称搜

返回第 1 条即用，同时记录 `address` + `tel` 备用。

### 2. 搜不到时试以下变体

| 原关键词 | 试这些 |
|---|---|
| XX 酒店（X 号店） | `XX 酒店 X 号店`（去掉括号） |
| XX 餐厅（招牌菜） | `XX 餐厅` |
| XX 火车站 | `XX 站`、`XX 城际站`、`XX 轻轨站` |
| XX 汽车站 | `XX 客运站`、`XX 客运中心` |
| 陶艺 DIY（品类词） | `XX 陶艺体验`、`XX 陶艺工作坊` |
| XX 博物馆 | 先 `XX 博物馆`，再 `XX 博物馆售票处`、`XX 景区` |

### 3. 仍然搜不到 → **不要编**

**关键问题**（按优先级）：
1. "你说的 XX 是哪家？有具体的店名或官方名吗？"
2. "可以提供高德 App 收藏夹截图，或携程/美团的店名链接吗？"
3. "如果不知道具体店名，那这个 POI 在地图上就不显示了，可以从行程里删掉，或者用 '[景区名]入口' 这种通用地址代替"

### 4. 搜到但地址残缺

返回的 `address` 字段像 `XX 区 XX 段路`（缺门牌号）：
- 记下来问用户："高德显示在 XX 区 XX 路，但门牌号没返回，能提供订单截图吗？"
- 在 HTML 的 desc 加 `⚠️ 地址以 [酒店/餐厅] 订单为准`

### 5. 搜到多个相似结果

按 `importance` 字段排序（API 默认已经按这个排），第一个就是最相关的。如果不确定哪个对：

- 看 `address` 是否更接近用户行程的其他 POI（步行距离、地铁口）
- 看 `typecode`（高德分类编码）是否匹配（如 110000 = 景点，050000 = 餐饮）
- 仍然不确定就问用户

## 常见错误

| 错误 | 后果 | 正确做法 |
|---|---|---|
| 用 Web 端 JS API Key 调 REST API | 返回 `USERKEY_PLAT_NOMATCH` | 必须用 Web 服务 Key（用户单独提供的） |
| 不传 `city` 参数 | 返回全国结果，难筛选 | 必须传 |
| 直接取 `pois[0]` 不看 `name` | 匹配到同名但不同城市/不同店 | 检查 `name` 字段是否完全一致 |
| 用模糊品类词（如"陶艺 DIY"） | 几乎搜不到 | 改用具体店名，或问用户 |
| 凭印象把坐标偏移几十米"修正" | 用户到了附近找不到 | **直接用 API 返回值，不做二次加工** |

## 结果记录规范

每次会话存一份 `poi-candidates.md`（放在用户工作目录，不在 skill 里）：

```markdown
| 用户说的名字 | 高德返回名 | location | address | 状态 |
|---|---|---|---|---|
| XX 景点 | XX 景点（售票处） | 113.xxx,23.xxx | XX 路 21 号 | ✅ |
| YY 餐厅 | （未找到） | — | — | ❌ 待用户确认 |
```

> ⚠️ 这是模板示例。**不要复制粘贴**示例里的具体名字 — 每次会话用自己的查询结果。

只有 ✅ 状态的才进 HTML。❌ 状态的要么问清楚、要么删掉。

## 备用 API（Key 不通时）

如果用户给的 Key 返回 `INVALID_USER_KEY` / `USERKEY_PLAT_NOMATCH` / 任何非 10000 的 infocode：

1. **不要**去网上搜其他人的公开 Key（违规 + 可能随时失效）
2. **问用户**：
   - "你给的 Key 返回 `USERKEY_PLAT_NOMATCH`，是高德 Web 服务的 Key 吗？"
   - "请到高德开放平台控制台 → 我的应用 → 添加 Key，服务平台勾选'Web 服务 API'"
3. 如果用户坚持做不了，**告知用户**："没有 Key 就无法验证坐标，所有 POI 会标 ⚠️ 坐标未核实，是否继续？"让用户决定是否接受

## 国际行程怎么办

高德 POI **不支持海外**。如果用户做国外行程：

1. **明确告知**：本 skill 默认只支持国内
2. **选项**：
   - 用户提供 Google Geocoding API Key → 用 Google API 替代，**但 HTML 模板里的高德地图 API 也要换成 Google Maps Embed/JS API**
   - 用户接受只用名字 + 大致地址（无地图）→ 删掉地图模块
   - 用户接受用 OpenStreetMap（免费）→ 改用 Leaflet + OpenStreetMap tiles

**这是 skill 的扩展点，不内置**。遇到时和用户讨论方案。

## 一次会话的批量查询脚本

```powershell
$key = '<用户的 Key>'
$candidates = @(
  @{display='用户行程里的名字'; kw='高德搜索词'; city='城市'}
  # ...
)
foreach ($c in $candidates) {
  $kwEnc = [uri]::EscapeDataString($c.kw)
  $cEnc = [uri]::EscapeDataString($c.city)
  $url = "https://restapi.amap.com/v3/place/text?key=$key&keywords=$kwEnc&city=$cEnc&extensions=base&offset=1"
  $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 8
  $j = $r.Content | ConvertFrom-Json
  if ($j.status -eq '1' -and $j.pois.Count -gt 0) {
    $p = $j.pois[0]
    Write-Host "✅ $($c.display) | $($p.name) | $($p.location) | $($p.address)"
  } else {
    Write-Host "❌ $($c.display) | NOT FOUND (kw=$($c.kw))"
  }
}
```

## 关于示例数据

本 skill 不保留任何"示例 POI"作为数据源。每次会话的查询结果都写到当前工作目录的 `poi-candidates.md`，**不要跨会话复用**。坐标会变、POI 会改名/关店。