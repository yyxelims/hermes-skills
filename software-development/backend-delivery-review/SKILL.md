---
name: backend-delivery-review
description: Use when 审查后端代码是否匹配需求/规格、评估交付进度。实测构建+启动取证，不只读代码。
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [backend-review, spring-boot, mysql, delivery-audit, java]
    related_skills: [mysql-schema-design, systematic-debugging, writing-plans]
---

# 后端交付审查（需求匹配度 + 真实进度）

## When to Use / 何时用

- "帮我看看这个后端代码和需求是否匹配""现在什么进度""能交付联调了吗"
- 接手别人/上一轮 agent 写的服务端工程，要先判断能不能用
- 交付前自查：功能面 vs 验证面差多少

## 核心原则

**进度不能靠读代码推断，必须跑出来。** 代码齐全 ≠ 能跑 ≠ 验证过。报告里每个结论标证据等级：实测 / 文档自述 / 推测。

**给两个进度数字，不给一个**：
- 功能实现度（对照需求逐条打勾）
- 可交付联调度（外部依赖、增量 SQL、真机链路是否就绪）
例：功能 85% / 可联调 60% —— 差距本身就是结论。

## 工作流

### 第1步：先对齐三份原文（输入→操作→输出）

| 输入 | 操作 | 输出 |
|---|---|---|
| Word 需求、规格书、DDL、README | 按顺序读，**以业务 Word 定范围，以规格书定契约，以实例元数据定现实** | 三者冲突清单（常见：规格写"不得登记未来"，Word 要求"提前填报未来"——以 Word 为准并标明） |

三者冲突必须显式列出，别默默选一个。

### 第2步：通读全部源码

- `execute_code` 里循环 `read_file` 全部源文件，一次看完，比逐个调用省 10 轮往返。
- **一次打印超过 ~50KB 会被截断**，先只打主代码；被截断的文件单独重读。
- 边读边记 `文件:行号`，报告里每个缺口都要能指到行。

### 第3步：实测构建 + 测试（最容易翻车的一步）

```bash
./mvnw clean verify 2>&1 | tail -35; echo "EXIT=${PIPESTATUS[0]}"
grep -h "tests=" target/surefire-reports/*.xml
```

**坑：BUILD SUCCESS 不等于测试真跑了。** 必须读 surefire 报告，看 `tests / skipped / failures`。集成测试常用 `@EnabledIfEnvironmentVariable` 门控，会以 `skipped=1` 静默通过——这类"跳过的测试"要在报告里单列，不能算已验证。

**坑：离线构建缺驱动。** `-o` 报 `Cannot access central in offline mode` 时，先单独拉依赖再重跑：

```bash
./mvnw -q dependency:get -Dartifact=com.mysql:mysql-connector-j:9.3.0
./mvnw clean verify
```

### 第4步：真实启动冒烟（不是只看代码）

没有可用数据库时，给 fat jar 动态注入 H2，不重打包：

```bash
java -cp target/app.jar \
  -Dloader.path=$HOME/.m2/repository/com/h2database/h2/2.3.232/h2-2.3.232.jar \
  org.springframework.boot.loader.launch.PropertiesLauncher \
  --spring.datasource.url="jdbc:h2:mem:smoke;MODE=MySQL;DATABASE_TO_LOWER=TRUE" \
  --spring.datasource.username=sa --spring.datasource.password= \
  --spring.datasource.hikari.connection-init-sql="SELECT 1" \
  --PORT=18080
```

要点：`-cp` 指 jar + `PropertiesLauncher` 才能吃 `loader.path`；`connection-init-sql` 必须覆盖掉生产用的 `SET time_zone`（H2 不支持）；端口用工程自己的 env 变量名。

然后分开验证：
```bash
curl -s -o /dev/null -w "live=%{http_code}\n"  http://127.0.0.1:PORT/health/live
curl -s -o /dev/null -w "me=%{http_code}\n"    http://127.0.0.1:PORT/api/v1/auth/me    # 期望 401
curl -s -o /dev/null -w "ready=%{http_code}\n" http://127.0.0.1:PORT/health/ready
```
`live=200` + `me=401` 才算"进程能起、拦截器生效"；`ready=500` 在空库下是预期，说明就绪探测真查库（这点要在报告里点明，别当 bug）。

**终止进程用 `process(action=kill)`**，不要 `nohup`/`&`（Hermes 会拒绝 shell 级后台）。同时验证日志里出现优雅停机，等于顺带验了 `server.shutdown=graceful`。

### 第5步：逐条对照表

按业务需求编号一行一条：需求 → 实现位置（文件:行）→ 状态 ✅/⚠️/❌ → 一句话说明。后面再按规格书的技术条款补一张（事务契约、审计、权限、分页、错误码）。

### 第6步：缺口分 P0/P1/P2

- **P0 挡联调**：增量 SQL 未落地、触发器版本未核对、第三方凭据为空、真机零验证
- **P1 功能/契约缺陷**：缺接口、口径错、错误码错、审计失真
- **P2 长期隐患**：无清理任务、无频率限制、日志字段缺失

最后给**一个**决策问题（先补代码还是先上线增量 SQL），不要甩待确认清单。

## 审查必查项（Spring Boot + MySQL 类后端）

详细检查清单见 `references/spring-boot-mysql-audit-checklist.md`。高频失分点：

1. **事务内会话变量**：`SET @app_user` 与写语句必须同一连接（靠 `@Transactional` + `DataSourceUtils` 保证），包在 try/finally 里清理。
2. **取号回读**：非自增主键靠 `SELECT @last_reg_no` 时，必须校验格式并在缺失时回滚，不能返回 null 给前端。
3. **数据范围落在 SQL 里**：角色过滤不能只靠前端隐藏按钮，每条查询都带 `mgr_phone = :loginPhone`。
4. **审计保真**：日志的 module 是否硬编码（白名单/权限/字典的日志全串到业务模块）、ip 是否恒空、回滚后失败日志有没有、查询条件是否入 content。这类"写了但写错"最容易漏看。
5. **分页 total**：聚合接口常只返回 summary 不返回 total，前端翻不了页。
6. **错误码映射**：`DataIntegrityViolationException` 一把抓成 409 是通病——CHECK 约束违约（结束早于开始、必填缺失）应是 400 + 字段提示。
7. **软删条件一致性**：列表、冲突检测、协同、统计、提醒必须用同一个"有效记录"条件，漏一处就串数据。
8. **删除级联**：幂等键表/扩展表有没有随主表删除，否则重试会返回已删单号。
9. **管理入口锁死**：能不能删掉最后一个管理员。
10. **集成测试是否真跑**：见第3步。

## 报告格式（用户偏好，照做）

1. 一句话结论 + 两个进度数字（先给结论，不复述过程）
2. "我实际验证到的"证据表（命令 → 真实结果）
3. 需求逐条对照表
4. 缺口按 P0/P1/P2，带 `文件:行`
5. 下一步建议 + 一个决策问题

禁止："后续验证""有待完善"这类空话；每个判断要么有实测输出，要么明说"文档自述，未验证"。

## 坑

- 本地默认 MySQL 可能是 5.7，不支持 CHECK 约束与 CTE。跑之前先 `mysql --version`；版本不符就别拿它验 8.0 特性，改用隔离 MySQL 8 / 容器 / 内存库。
- 生产库只做只读核对。集成测试、建库、写数据必须隔离库，且需授权——不要为了"跑通测试"在生产实例建库。
- 不要因为 README 写了"已验证"就采信；README 的自述和 surefire 报告经常对不上。
