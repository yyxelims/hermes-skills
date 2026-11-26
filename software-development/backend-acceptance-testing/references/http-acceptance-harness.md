# HTTP 验收 harness（真实库联调）

实测环境：Spring Boot JAR + MySQL 8.0.46（阿里云 ECS），本机 macOS 跑 JAR 经 SSH 隧道连库，33 项用例全过。

## 1. 连不上远程 MySQL 时先开隧道，别改安全组

现象：`nc -z host 3306` 显示通，客户端却报
`ERROR 2013 (HY000): Lost connection to MySQL server at 'reading initial communication packet', system error: 25`
（或 `ERROR 2003`）。此时改安全组/绑地址都是白折腾。

```bash
# 本机开隧道（后台进程）
ssh -N -L 13307:127.0.0.1:3306 -i ~/.ssh/<key> -o ExitOnForwardFailure=yes root@<host>
# 落地端是服务器本机，root@localhost 与应用账号都能用
mysql -h127.0.0.1 -P13307 -u<app_user> -p<pass> <db> -N -e "SELECT VERSION();"
```

JAR 连隧道：

```bash
DB_URL="jdbc:mysql://127.0.0.1:13307/<db>?connectionTimeZone=Asia/Shanghai&connectTimeout=4000&socketTimeout=15000" \
DB_USER=... DB_PASSWORD=... PORT=18081 java -jar target/app.jar
```

注意：本机 `root` 走隧道仍需密码（服务器 `root@localhost` 有口令时），用 `--defaults-file` 或应用账号更省事。
MySQL 客户端版本差异（本机 anaconda 的 5.7 client）不影响连 8.0 服务端。

## 2. 本机一次性 MySQL（真实触发器/CTE，不碰 3306）

```bash
mysqld=/opt/homebrew/opt/mysql/bin/mysqld
rm -rf /tmp/mysql-it && $mysqld --initialize-insecure --datadir=/tmp/mysql-it --basedir=/opt/homebrew/opt/mysql
# 必须用 background=true + exec 启动，前台跑会被工具超时杀掉（日志里只有 Received SHUTDOWN）
exec $mysqld --datadir=/tmp/mysql-it --basedir=/opt/homebrew/opt/mysql \
  --port=13306 --socket=/tmp/mysql-it.sock --mysqlx=OFF --skip-log-bin --log-error=/tmp/mysql-it.err
```

然后建库导 fixture：

```bash
mysql -h127.0.0.1 -P13306 -uroot -e "CREATE DATABASE outwork_it CHARACTER SET utf8mb4;
 CREATE USER 'it_user'@'%' IDENTIFIED BY 'itpass'; GRANT ALL ON outwork_it.* TO 'it_user'@'%';"
mysql -h127.0.0.1 -P13306 -uroot -D outwork_it < src/test/resources/mysql-base.sql
mysql -h127.0.0.1 -P13306 -uroot -D outwork_it < sql/001_backend.sql
```

集成测试类用环境变量开关（避免 CI 里误跑）：

```java
@EnabledIfEnvironmentVariable(named="OUTWORK_MYSQL_TEST", matches="1")
...
assertTrue(url.matches("jdbc:mysql://127[.]0[.]0[.]1:[0-9]+/outwork_it"));
```

## 3. 绕过微信登录：直接播种会话

后端把 token 以 SHA-256 存 `ow_session`，所以只要知道明文 token 就能造一条会话：

```sql
INSERT INTO ow_session VALUES(SHA2(REPEAT('a',64),256),'***',NOW()+INTERVAL 3 HOUR);
```

请求头 `Authorization: Bearer aaaa...`（64 个 a，正好过 `[a-f0-9]{64}` 校验）。
再用不同字母给第二个角色（`b`*64 = 管理者）。**不要**因为拿不到 `wx.login` 的 code 就跳过接口测试。

## 4. urllib harness 骨架（不依赖 requests）

```python
import json, urllib.request, urllib.error

def call(method, path, token=None, body=None, headers=None, raw=False):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data: req.add_header("Content-Type", "application/json")
    if token: ***("Authorization", "Bearer " + token)
    for k, v in (headers or {}).items(): req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            txt = r.read().decode()
            return r.status, (txt if raw else (json.loads(txt) if txt.strip() else None))
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        try: return e.code, json.loads(txt)
        except Exception: return e.code, txt[:200]

def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (" | " + str(detail) if detail else ""))
```

逐项 print PASS/FAIL，最后打"总计 N 项，通过 N，失败 N"——用户要的是这个数字，不是日志。
断言失败不算异常，跑完所有用例再汇总。

## 5. 验收矩阵（后端通用，按业务裁剪）

1. `health/live` 200、`health/ready` 200（ready 必须真的查表）
2. 匿名受保护接口 401
3. 登录态 `/auth/me` 角色与功能码正确；开关类返回（如 `whitelistEnforced`）
4. 字典条数与启用项
5. 新增成功，单号长度/格式符合规则
6. 同幂等键同内容 → 原单号；同键不同内容 → 409
7. 同人重叠时段 → 409；空闲段接口正确避开
8. 无坐标/边界值可登记
9. 跨日安排（23:00→次日 01:00）
10. 角色 1 查他人记录 → 404（不是 403，避免泄露存在性）
11. 同事协同可见未来、距离为 null / 区间筛选
12. 统计口径：笔数、两类金额、缺失计数、时段去重
13. 导出 CSV：BOM 表头 + 数据行 + 防公式注入
14. 详情返回毫秒 `update_time`；旧版本再改 409
15. 角色 1 作废 403；管理员作废 200
16. 作废后列表/统计/提醒同步消失
17. 白名单撤销后同一会话立即 401
18. 双线程抢同一时段：`sorted([200,409])`
19. 分页：page/size 边界、total 存在

## 6. 清理顺序（外键在前）

```sql
DELETE FROM <子表1>; DELETE FROM <子表2>;      -- 引用主表的外键表先删
DELETE FROM t_outwork_record WHERE mgr_phone IN ('测试号');
DELETE FROM t_outwork_record_bak;
DELETE FROM t_outwork_record_bak_archive;
DELETE FROM t_outwork_seq;
DELETE FROM t_oper_log;
DELETE FROM t_login_whitelist WHERE phone='临时测试号';
SELECT (SELECT COUNT(*) FROM t_outwork_record),(SELECT COUNT(*) FROM t_outwork_record_bak),(SELECT COUNT(*) FROM t_outwork_seq);
```

删主表会触发 `AFTER DELETE` 往留痕表写 `D` 行——所以留痕表要放在主表之后删，且最终必须复查全为 0。
报告里写明"跑完已清空（主表/留痕/流水/日志/会话均 0 行）"。

## 7. 提交

报告落 `docs/TEST-REPORT-YYYY-MM-DD.md`，含：环境（真实库版本/是否隧道）、补齐了什么对象、逐组用例表、未覆盖项及原因、结论。
然后 `git add -A && git commit && git push`。用户会检查提交，版本控制别忘。
