# 微信小程序 + 自建 Java 后端

## 1. 先确认主体与手机号能力

| 主体 | `getPhoneNumber`（手机号快速验证） | 静默 `wx.login` 换 openid |
|---|---|---|
| 个人 | **不可用**（需企业主体；且按次计费 0.03 元/次，1000 次体验额度） | 可用 |
| 企业 | 可用 | 可用 |

**个人主体不要做"微信快捷登录拿手机号"**，接口会一直失败。正确做法见下。

## 2. 登录方案：静默 openid + 首次手输手机号

```
wx.login() → code
POST /auth/login {loginCode}
  ├─ openid 已绑定 → 直接发 token（用户无感）
  └─ 未绑定 → 409 PHONE_REQUIRED
       └─ 用户手输 11 位手机号 → 重新 wx.login()（code 只能用一次）
           └─ POST /auth/login {loginCode, phone}
                ├─ 手机号在白名单 → 绑定 openid↔phone，返回 token + newlyBound:true
                ├─ 不在白名单 → 403 FORBIDDEN
                ├─ 号已被别的微信绑 → 409 PHONE_BOUND
                └─ 微信已绑别的号 → 409 WECHAT_BOUND
```

- 手机号只是"第一次认人的口令"，之后靠 openid；别人不知道你的微信进不来。
- 保留 openid 才能做订阅消息提醒；纯手机号登录会直接失去提醒能力。
- 管理员提供"解绑"接口：`UPDATE ... SET openid=NULL,bind_time=NULL WHERE phone=?` + 清会话，换微信后重新绑。

## 3. 一张表存 phone + openid + role

不要拆成"白名单表 + 绑定表"两张，几个人用的系统没必要：

```sql
ALTER TABLE t_login_whitelist
  ADD COLUMN openid VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin NULL,
  ADD COLUMN bind_time DATETIME(3) NULL,
  ADD COLUMN last_login_time DATETIME(3) NULL,
  ADD UNIQUE KEY uk_whitelist_openid (openid);
```

`phone` 主键 + `openid` 唯一（MySQL 唯一索引允许多个 NULL）。绑定用 `WHERE phone=? AND openid IS NULL`，影响 0 行即"已绑别人"。

## 4. 审核模式开关（提审必备）

审核员用自己微信登录，手机号不在白名单会被 403 挡住，导致审核无法进行。

```
AUTH_WHITELIST_ENABLED=true|false     # 默认 true
AUTH_AUTO_ROLE=1                      # 关闭时自动建号的角色
AUTH_AUTO_NAME=审核                    # 姓名前缀，后接手机号后 4 位
```

关闭时：白名单外手机号首次登录**自动建号并绑定**，正常发 token；`/auth/login` 与 `/auth/me` 返回 `whitelistEnforced` 便于自检；日志写明"白名单校验已关闭"。审核通过后改回 true 并清理 `emp_name LIKE '审核%'`。

## 5. 微信接口的 Content-Type 坑（最容易误判成网络故障）

微信 `sns/jscode2session`、`cgi-bin/stable_token`、订阅消息接口返回的 **`Content-Type` 是 `text/plain`**，不是 `application/json`。

```java
// ❌ 抛 UnknownContentTypeException，被 catch 后表现为"第三方服务暂不可用"
http.get().uri(target).retrieve().body(JsonNode.class);

// ✅ 先取字符串再解析
String text = body == null
    ? http.get().uri(target).retrieve().body(String.class)
    : http.post().uri(target).contentType(MediaType.APPLICATION_JSON).body(body).retrieve().body(String.class);
return objectMapper.readTree(text);
```

排查手法：`curl -s -D - -o /dev/null "<url>"` 看响应头；服务器能直连（curl 200）但 JVM 报第三方不可用，优先怀疑解析而不是网络。

## 6. jscode2session 错误码翻译

| errcode | 含义 | 给用户的文案 |
|---|---|---|
| 40029 | code 无效/已用 | 微信登录凭证无效或已使用，请退出小程序重新进入 |
| 40163 | code 已被使用 | 请重新进入小程序 |
| 45011 | 频率限制 | 登录太频繁，请稍后再试 |
| 40013 | AppID 错 | 配置不正确，联系管理员 |
| 40125 | AppSecret 错 | 配置不正确，联系管理员 |

返回体固定 `{code, message, wxErrcode}`，前端按 `code` 分支。

## 7. 请求合法域名（硬规则）

| 场景 | 能否用 IP / http |
|---|---|
| 开发者工具 | 可以：详情 → 本地设置 → 勾"不校验合法域名" |
| 体验版（手机开调试） | 可以，但每台手机要开调试、体验版有有效期 |
| 体验版正常使用 / 提交审核 / 正式版 | **不可以**，必须 HTTPS + 已备案域名的 443 |

后台填 `https://***`（只填域名，不带路径/端口）；前端 `baseURL = https://***/api/v1`。每月限改 5 次。

想"完全不用自己域名"只有两条路：微信云托管（容器，微信给默认 HTTPS 域名）或重新买域名备案。**云开发要重写后端，不适用于已有 Java + MySQL 系统。**

## 8. 订阅消息

- 发送必须用 **openid**，所以登录要保留 openid。
- 一次性授权：用户同意一次只能收一条，需在每次登记时引导 `wx.requestSubscribeMessage`。
- 服务端按 `errcode` 区分：0 受理 / 43101 用户拒收 / 45009 频率超限（退避重试）/ -1 系统繁忙。
- 未配模板 ID 时接口应返回明确 503，而不是空指针。

## 9. 审核前必查

- 个人主体：名称、简介必须与实际功能相符（"等我研究研究"这种名字配"外出登记"功能会被驳回）；类目选「工具 → 效率」。
- **用户隐私保护指引**必须逐项填写：收集手机号（登录）、位置（外出地点坐标）、姓名（客户经理/买方/卖方/引荐人）。漏填直接拒。
- 提审时把白名单开关关掉，审核员才进得去。
