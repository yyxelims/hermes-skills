---
name: spring-boot-backend-delivery
description: Use when 交付 Spring Boot+MySQL 后端并上线单机。
version: 1.0.0
tags: [spring-boot, java, mysql, backend, deploy, nginx, systemd, wechat]
---

# Spring Boot + MySQL 后端交付

面向"给小程序/内部系统做一套自建后端并上线到一台机器"的完整路径。

## When to Use

- 用户给了需求文档 / 库表 DDL，要一套能跑的后端（Spring Boot + MySQL）。
- 已有数据库（触发器、存储过程、字典、角色权限码），要写应用层对接。
- 要把 Java 服务部署到一台云服务器，用 HTTPS 域名给小程序/前端调用。
- 要补接口错误码、前端对接文档、联调测试报告。
- 排查"服务器能 curl 通第三方，但应用报第三方不可用"这类问题。

参考文件：
- `references/api-error-contract.md` — 统一错误响应、Web 异常清单、MySQL 错误翻译
- `references/wechat-miniprogram-backend.md` — 微信登录/手机号/订阅消息/域名硬规则/`text-plain` 坑
- `references/single-host-deploy.md` — JDK21 安装、systemd、nginx、版本软链、清理与回滚


## 一、开工顺序（别跳）

1. **先读需求 + 规格 + DDL**，再写代码。核对：主表/流水表/快照表、触发器、函数、字典、角色功能码、账号权限。
2. **先输出"需求—接口—表/字段—验收用例"对照**，把差异一次列清（缺表、缺字段、缺功能码、需求与规格冲突）。冲突时以业务需求文档为准，但要写进文档。
3. 数据库现状用**只读**方式核对（`SHOW CREATE TRIGGER`、`information_schema`），不要假设线上表跟脚本一致。
4. 代码按域拆小类：`Access`（登录态/权限）、各业务 `Records/Queries/Administration`、`Providers`（第三方）、`Plan`（请求体+校验）、`ApiError`（错误契约）。不引 JPA，用 Spring JDBC + 手写 SQL 对齐遗留表结构。

## 二、事务与连接级状态（最容易错）

MySQL 触发器常用 `@app_user`、`@last_reg_no` 这类**会话变量**：

- 必须和写语句在**同一物理连接**：`@Transactional` + `JdbcTemplate`（底层 `DataSourceUtils`）即可；自己 `new` 连接池或异步执行会断链。
- 顺序固定：`SET @app_user=?` → INSERT → `SELECT @last_reg_no` → 校验格式（缺失就抛异常回滚）→ 归还前 `SET @app_user=NULL,@last_reg_no=NULL`（`finally`，覆盖异常路径）。
- 主键由触发器生成时，`LAST_INSERT_ID()` 拿不到，别用。

并发控制三件套：白名单/主记录行 `FOR UPDATE` 串行化 + 客户端幂等键表（唯一键，同键不同内容 409）+ `update_time` 毫秒乐观锁。

## 三、错误契约（详见 references/api-error-contract.md）

统一返回 `{code, message, field?, errors?, conflicts?, expected?}`：

- 校验**一次性收集全部字段错误**，不要改一个报一个；单字段错误把 `field` 提到顶层。
- 冲突 409 带上冲突对象明细（时段、单号），前端能直接提示改哪里。
- 数据库错误要翻译：1406 超长 / 1048 非空 / 3819 CHECK / 1062 重复 / 1452 外键 / 1205·1213 重试，**不能把 SQL 错误码原样抛给前端**，也不能一律 409。
- 补全 Web 层异常：缺参、缺请求头、类型不匹配、JSON 解析失败、405、415、404、兜底 500（记日志、不返回堆栈）。

## 四、第三方接入（详见 references/wechat-miniprogram-backend.md）

**微信所有接口返回 `Content-Type: text/plain`**。Spring `RestClient ... .body(JsonNode.class)` 会抛 `UnknownContentTypeException`，被 catch 后表现为"第三方服务暂不可用"，极易误判成网络问题。做法：先 `.body(String.class)`，再用 `ObjectMapper.readTree`。

高德 `inputtips` 实测 QPS≈6，并发会限流；按 `infocode` 区分限流(10004)/配额(10003)/Key 失效，并加 60s 关键词缓存 + 前端 300ms 防抖。

## 五、单机部署（详见 references/single-host-deploy.md）

Aliyun Linux 4 源里只有 JDK 8 → 装 Temurin 21 tar 到 `/opt/jdk-21`，systemd `ExecStart` 写绝对路径。JAR + systemd + nginx 反代 + 版本目录软链回滚。1.8G 内存机器 `-Xmx192m -XX:MaxMetaspaceSize=128m` 实测 RSS 约 185MB。

## 六、测试与验收

| 层 | 做法 |
|---|---|
| 单测 | H2 `MODE=MySQL` + MockMvc，覆盖鉴权、数据范围、分页、错误码、CSV 注入 |
| 集成 | 真实 MySQL。Docker 不可用时用 brew mysql 临时 datadir（`--initialize-insecure` + 独立端口 + 跑完销毁） |
| 端到端 | Python `urllib` 脚本打真实库/真实服务，逐条 PASS/FAIL 打印，跑完清理合成数据 |
| 部署 | 启动后 `/health/live` 200、匿名接口 401、`/health/ready` 探测依赖表 |

`/health/live` 与 `/health/ready` 分开：ready 要真的 join 一遍依赖表（`LIMIT 0`），别只 `SELECT 1`。

## 七、坑（都是踩过的）

- **不要擅自用用户的域名、改他已有的 nginx 站点、动生产库**。上线前问一句"用哪个域名/能不能改这个 server 块"。用户会直接质问"你为什么要用我的域名"。改之前先 `cp` 备份并告诉备份路径。
- **复合危险命令（切换版本 + 重启服务 + 删目录）容易触发审批超时被拦**。拆成单条最小命令：先 upload，再 `ln -sfn`，再 `systemctl restart`，每步单独发。
- **删旧版本前先看 `readlink -f current`**，别把正在跑的版本删了导致重启失败。
- **项目目录可能被父级大 repo 包住**（`git rev-parse --show-toplevel`）。先在该目录 `git init` 独立仓库再提交，否则会把无关文件一起 commit。
- H2 与 MySQL 有差异：`NOW(3)`、会话变量、`FOR UPDATE`。时间戳用 Java 侧 `LocalDateTime.now()` 传参，别依赖 DB 函数。
- 手动建 `AnnotationConfigWebApplicationContext` 测试时 **`application.properties` 不加载**，`fail-on-unknown-properties` 等配置要 `addInlinedPropertiesToEnvironment` 显式加，否则测出来的行为和线上不一致。
- 需求变更（如"金额不要了"）要**全链路一次改完**：请求体校验、表、统计 SQL、导出列、健康检查 join、测试断言、README。漏一处就会在联调时暴露。
- 交付文档里必须写清**请求字段小驼峰 / 响应字段下划线**，否则前端必然踩。

## 八、交付物清单

- [ ] 可构建工程（`./mvnw clean verify` 绿）+ `pom` 固定版本
- [ ] 增量 SQL：幂等建表（`IF NOT EXISTS`）+ 一次性 ALTER（文件名和 README 都标"只能执行一次"）
- [ ] `deploy/`：systemd unit、env 示例、nginx location
- [ ] README：启动、部署、版本回滚、错误码表、第三方配置坑
- [ ] 前端对接文档：登录时序、全部接口、字段命名约定、错误处理、自检清单
- [ ] 测试报告：环境、用例表、实测数据、未覆盖项与原因
- [ ] 配置开关（如白名单校验 `AUTH_WHITELIST_ENABLED`）要能在不改代码的情况下按场景切换

## 相关

- `wechat-miniprogram-dev` — 小程序端注册/审核/域名/前端坑
- `mysql-schema-design` — 表结构设计
- `systematic-debugging` — 排查"看起来像网络问题"的外部依赖异常
