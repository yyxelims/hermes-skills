# Spring Boot + MySQL 后端审查清单

按"能跑 → 正确 → 可审计 → 可运维"四层过一遍。每项都要问：代码在哪一行？实测过没有？

## A. 事务与主键契约

| 检查项 | 合格标准 | 常见错法 |
|---|---|---|
| 会话变量 | `SET @app_user=?` 与写语句在同一物理连接 | 用 `JdbcTemplate` 手写 SET 但在非事务方法里 → 连接池会换连接，留痕人变成 DB 账号 |
| 取号 | INSERT 后同连接读 `@last_reg_no`，格式校验失败即抛异常回滚 | 用 `LAST_INSERT_ID()`（非自增主键返回 0）；读到 null 仍返回成功 |
| 生成列 | INSERT/UPDATE 列清单里不出现（否则 MySQL 3105） | 图省事 `INSERT ... SELECT *` |
| 幂等键 | 持久化唯一键 `(操作人, key)`，payload hash 不同返回 409，相同返回首次结果 | 只在内存缓存；hash 用 `toString()` 时注意 `12.34` 与 `12.340` 会被判成不同内容 |
| 乐观锁 | `update_time` 毫秒精度，`FOR UPDATE` 读旧值后比对，或 WHERE 带旧值 | 只比秒级时间；改完不推进 update_time 导致连续两次修改都用同一版本 |
| 并发串行化 | 先 `SELECT ... FOR UPDATE` 锁稳定的主体行（如白名单行），再查重 | 只靠唯一索引兜底，冲突报 500 |
| 软删 | 统一常量 `VALID = "(reserve_5 IS NULL OR reserve_5='')"`，列表/冲突/协同/统计/提醒全带上 | 只在一两个查询里加了条件 |

## B. 权限与数据范围

- 功能码 + 位（`can_view/add/edit/delete/export`）是否**每次都查库**，而不是写死在 token 里（管理员改权限要立刻生效）。
- 角色过滤是否落在 SQL 的 WHERE，而不是 `if (role==1) return 403` 之类只挡入口。
- 管理端新增接口是否忘了给**管理员角色**插功能码（只给 role 1 插，管理员一调就 403）。
- 新功能码是否只存在于增量 SQL 而线上库没有 → 未执行前全 403，这属于 P0。
- 越权测试：拿 A 的 token 请求 B 的单号，应 404 而不是 403（不泄露存在性）。

## C. 审计保真（最容易被"写了"骗过去）

- `module` 是否硬编码：一个通用 `log()` 方法把白名单/角色/字典操作全写成 `OUTWORK`，按模块筛选就失真。
- `ip` 字段有没有真写；`before_data/after_data` 是否整行 JSON。
- 事务回滚后的失败日志（`result=0` + 失败原因）有没有单独落库——规格里常明确要求，代码里常没有。
- 查询/导出日志是否记录了筛选条件（只写"导出成功"等于没审计）。
- 留痕表读取接口：按主键 UNION 当前表 + 归档表（`_bak` + `_archive`），有没有对外接口。

## D. 统计与分页

- 报表是否用 LEFT JOIN 扩展表：历史缺金额的签单仍计笔数，`COUNT(*)-COUNT(amount)` 给出缺失笔数，全缺失 `SUM` 返 null，确认的 0 返 0。
- 归属期用开始时间还是登记时间，是否在文档写明。
- 聚合接口是否返回 `total`；只返回 `summary` 时前端无法翻页。
- 跨时段去重：人数用 `COUNT(DISTINCT 手机号)`，笔数单独给，两者口径不同要写明。
- 同名人员是否用手机号区分。
- 导出是否流式（`fetchSize=Integer.MIN_VALUE`）、是否防公式注入（前导 `= + - @` 加单引号）、是否复用同一查询与权限。

## E. 状态机与外部依赖

- 提醒/任务表：领取用 `FOR UPDATE SKIP LOCKED`，卡在 SENDING 超时置 UNKNOWN，退避重试有上限，终态不再重发。
- 发前复核：记录未作废、接收人未撤白名单、绑定 openid 一致、授权记录仍有效。
- 一次性授权（微信订阅消息）成功后必须置终态，别再重试。
- 第三方调用超时是否设置（connect/read），失败是否降级成"可手工填写"而不是整体 500。
- 外部 code 换手机号这类调用是否放在事务外（事务里做外部调用会长时间持锁）。

## F. 工程与可运维

- 技术栈是否与规格一致；自研替代（自写拦截器代替 Spring Security）要明确标为偏差，不能说"等价"就跳过。
- 健康检查分 live / ready；ready 必须真探库（`SELECT ... LIMIT 0` 也行），不能只返 200。
- 部署：systemd 服务用户、EnvironmentFile 0600、`Restart=on-failure`、`TimeoutStopSec`、优雅停机、`-XX:+ExitOnOutOfMemoryError`。
- 连接池上限是否按机器内存定（1.8G 小机器给 6 条合理）。
- 只增不减的表（会话、幂等键、任务）有没有清理任务。
- 能不能删掉最后一个管理员（管理入口锁死）。
- 级联：扩展表/幂等键表是否随主表删除，否则重试返回已删单号。

## G. 证据采集命令

```bash
# 真实测试结果（不信 BUILD SUCCESS）
./mvnw clean verify 2>&1 | tail -35
grep -h "tests=" target/surefire-reports/*.xml

# 产物
ls -la target/*.jar

# 启动冒烟（无库时注入 H2）
java -cp target/app.jar -Dloader.path=<h2.jar> \
  org.springframework.boot.loader.launch.PropertiesLauncher \
  --spring.datasource.url="jdbc:h2:mem:smoke;MODE=MySQL;DATABASE_TO_LOWER=TRUE" \
  --spring.datasource.username=sa --spring.datasource.hikari.connection-init-sql="SELECT 1" --PORT=18080

# 触发器/函数是否与代码假设一致（生产只读）
SHOW CREATE TRIGGER <trigger_name>;
SHOW CREATE FUNCTION <fn_name>;
```

报告里贴命令 + 真实输出（状态码、tests 数），比任何形容词都有说服力。
