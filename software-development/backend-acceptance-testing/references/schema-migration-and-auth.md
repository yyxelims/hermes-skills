# 增量迁移与登录身份改造（小程序后端）

## 一、编号脚本，一脚本一件事

```
sql/001_backend.sql     建扩展表 + 功能码（CREATE TABLE IF NOT EXISTS / INSERT ... WHERE NOT EXISTS）
sql/002_drop_amount.sql 砍掉废弃表（DROP TABLE IF EXISTS）
sql/003_merge_binding.sql ALTER 加列 + 删旧表（只能执行一次）
```

- **不要回头改已执行过的脚本**。001 已经被生产环境跑过，砍功能就新开 002/003，README 写清执行顺序。
- `CREATE TABLE IF NOT EXISTS` 可重复执行；`ALTER ... ADD COLUMN` 在 MySQL 8 没有 `IF NOT EXISTS`，脚本头必须写"只执行一次"，重复执行会 Duplicate column。
- 删表前确认是空表：`SELECT COUNT(*)`；有数据先迁移或备份。
- 应用账号通常没有 DDL 权限，DDL 走 root 的 `--defaults-file`，别用业务账号试。

### 003 合并表实例（把绑定表并进用户表）

```sql
ALTER TABLE t_login_whitelist
  ADD COLUMN openid VARCHAR(100) CHARACTER SET ascii COLLATE ascii_bin NULL,
  ADD COLUMN bind_time DATETIME(3) NULL,
  ADD COLUMN last_login_time DATETIME(3) NULL,
  ADD UNIQUE KEY uk_whitelist_openid (openid);
DROP TABLE IF EXISTS ow_binding;
```

MySQL 唯一索引允许多个 NULL，正好表达"未绑定"。

## 二、执行前后必做的取证

```bash
# 执行前备份（含触发器/函数）
ssh root@host 'mysqldump --defaults-file=/root/.xx_db.cnf --single-transaction \
  --routines --triggers db > /root/db_backup/pre_merge_$(date +%Y%m%d_%H%M%S).sql'

# 执行
cat sql/003_merge_binding.sql | ssh root@host 'mysql --defaults-file=/root/.xx_db.cnf db'

# 执行后核对：列、对象数、关键对象清单
ssh root@host 'mysql ... -N -e "SHOW COLUMNS FROM t_login_whitelist;
  SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=\"db\";
  SELECT GROUP_CONCAT(table_name) FROM information_schema.tables WHERE table_schema=\"db\";"'
```

报告里写"改前 N 张表 / 改后 M 张表"，比"已执行"可信。

## 三、E2E 跑完的清理顺序

子表 → 主表 → 留痕 → 流水 → 日志 → 会话；绑定状态单独复位。

```sql
DELETE FROM ow_reminder; DELETE FROM ow_request; DELETE FROM ow_session;
DELETE FROM t_outwork_record;              -- 会触发 AD 写留痕
DELETE FROM t_outwork_record_bak; DELETE FROM t_outwork_record_bak_archive;
DELETE FROM t_outwork_seq; DELETE FROM t_oper_log;
UPDATE t_login_whitelist SET openid=NULL,bind_time=NULL,last_login_time=NULL;
DELETE FROM t_login_whitelist WHERE phone='临时测试号';
```

跑完必须 `SELECT COUNT(*)` 报基线（主表 0 / 留痕 0 / 日志 0 / 白名单回到原人数），不要只说"已清理"。

## 四、小程序登录：openid 是身份，手机号只是匹配键

### 为什么不能"只让用户手输手机号、不发验证码"

- 微信**没有任何接口**能读用户手机号，只有 `getPhoneNumber` 授权（企业主体 + 计费）；不做它就只能让用户自己填，后端无法验证真伪。
- 纯手输 + 无验证码 = 无鉴权：知道张三手机号就能以张三身份看日程、看客户姓名和签约地点。
- 而且没有 openid 就**做不了订阅消息提醒**（提醒按 openid 发）。

### 推荐方案（不需要企业主体手机号能力）

```
第一次：wx.login → code → 后端 jscode2session 换 openid
        openid 已绑定 → 直接发 token（静默）
        openid 未绑定 → 409 PHONE_REQUIRED
        前端弹输入框 → 再提交 {loginCode, phone}
        手机号在白名单 → UPDATE openid=?,bind_time=? WHERE phone=? AND openid IS NULL
之后每次：只传 loginCode
```

一张表就够了（手机号、姓名、角色、openid、绑定时间、最近登录），不要为了"授权名单"和"微信凭证"拆两张表——几个人的内部系统纯属多余，还会让解绑/移出名单要维护两处。

### 错误码

| code | 含义 | 前端动作 |
|---|---|---|
| PHONE_REQUIRED | 首次登录没带手机号 | 弹输入框 |
| PHONE_BOUND | 该手机号已绑别的微信 | 提示联系管理员解绑 |
| WECHAT_BOUND | 当前微信已绑别的手机号 | 提示用原号登录 |
| WECHAT_NOT_BOUND | 开提醒时还没绑微信 | 先登录绑定 |
| WECHAT_LOGIN_FAILED | code 失效 / AppID/Secret 配错（带 wxErrcode） | 重进小程序，持续失败查配置 |

### 提审开关（白名单校验关闭）

```
AUTH_WHITELIST_ENABLED=false      # 默认 true
AUTH_AUTO_ROLE=1                  # 审核员默认客户经理；要看管理端给 2
AUTH_AUTO_NAME=审核                # 自动建号姓名前缀，后接手机号后4位
```

- 关闭时：手机号不在名单 → 自动 INSERT（**同时写 openid**，否则审核员第二次进来又要填一次）+ 正常发 token。
- 响应 `/auth/login`、`/auth/me` 都返回 `whitelistEnforced`，随时自检是不是审核模式。
- 只放宽"准入"，不改角色功能码与数据范围。
- 审核通过必须改回 true 并重启；清理 `DELETE FROM t_login_whitelist WHERE emp_name LIKE '审核%'`。
- 开关状态写进日志（"白名单校验已关闭，首次登录自动建号"），事后可审计。

### 测试矩阵（不需要真实微信）

单测直接调 `Access.byOpenid / Access.bind`，不要为了测登录去 mock 微信 HTTP：

1. 未绑定 → `byOpenid` 返回 null
2. 首绑成功 + `autoCreated=false`
3. 同 openid 再绑同号 → 幂等
4. 第二个微信绑同号 → 409 PHONE_BOUND
5. 同一微信绑第二个号 → 409 WECHAT_BOUND
6. 解绑（openid 置 NULL）后可重绑到新微信
7. 白名单关闭时自动建号 + 写入 openid
8. 真实 MySQL 上用唯一索引再验一遍 PHONE_BOUND（H2 的唯一约束行为不同）

## 五、本项目实例（便于下次直接定位）

- 仓库：`github.com/yyxelims/outwork-backend`（私有，main）
- 服务器：***，库 `db_outwork`，公网 3306 握手失败 → 走 `ssh -L 13307:127.0.0.1:3306`
- 当前 11 张表：8 基础 + `ow_session/ow_request/ow_reminder`；`ow_amount`、`ow_binding` 已删
- 本期不做签约金额（不填、不存、统计只给笔数）
- 登录：openid 认人 + 首次手输手机号绑定；白名单表即用户表
- 未完成：服务器未装 JDK 21、未 systemd 部署、微信/高德凭据未配
