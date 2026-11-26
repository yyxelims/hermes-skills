---
name: backend-acceptance-testing
description: Use when 审后端与需求是否匹配、要联调验收或问进度。
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [backend, acceptance, code-review, integration-test, spring-boot, mysql, e2e]
    related_skills: [mysql-schema-design, wechat-miniprogram-dev, systematic-debugging]
---

# 后端验收：需求对照 + 真机联调 + 进度评估

用户把一整个后端工程丢过来说「帮我看看和需求是否匹配、现在什么进度」时用本技能。
核心原则：**结论必须有实测证据，不许把"代码里写了"当"验证过"**。

## 一、交付形态（用户认这个格式）

先一句话结论 + 两个百分比，再上证据，最后列缺口。顺序不要倒。

```
## 一句话结论
主体已完成，能构建能启动，核心闭环齐全；但离交付联调还差一层：增量表没落地、第三方未配、真机零验证。
进度判定：功能实现约 85%，可交付联调约 60%。

## 我实际验证到的（不是看文档推测）
| 验证项 | 结果 |
| ./mvnw clean verify | BUILD SUCCESS，产物 xxx.jar |
| 单元测试 | 4/4 通过 |
| MySQL 集成测试 | 跳过（0 执行）← 没跑就写没跑 |
| 真实启动 + HTTP | live 200 / 匿名 me 401 |

## 与需求逐条对照
| 需求 | 实现位置 | 状态 |
（✅ 完整 / ⚠️ 部分 + 差在哪 / ❌ 缺失）

## 必须补的缺口（按优先级）
P0 挡住联调 / P1 功能契约缺陷 / P2 长期隐患
每条带文件:行号，不写"建议优化"这种没法验收的话。

## 建议的下一步
```

- 百分比要给依据（构建是否过、接口几个、哪些没验证），不拍脑袋。
- 每个 ⚠️ 必须写"差在哪"，例如"明细没有 total，前端翻不了页"，而不是"部分实现"。
- 用文件:行号定位（`Queries.java:70`），收到的人能直接改。
- 禁"后续验证""理论可行"这类空话；未验证就明写"待真机/待隔离库"。

## 二、五步流程

**第1步：先把资料读全，再读代码**
需求 docx（Word 定业务范围）→ 后端规格/契约 → DDL/建表说明 → 全部源码（10 个类也要读完，别抽样）。
两边冲突时以 Word 业务范围为准、以线上实例元数据为准，把冲突列出来（例：规格写"不得登记未来时间"，Word 要求"提前填报未来计划"→ 代码选支持未来，是对的，要说明）。

**第2步：自己编译一次**
`./mvnw clean verify`（或等价命令）。离线 `-o` 可能缺依赖，先 `dependency:get` 再跑。
把 BUILD SUCCESS、测试数、产物路径记下来——这是报告里"实测"的第一行。

**第3步：真库集成测试**
不要在 H2 上跑完就说"集成通过"。优先起隔离 MySQL（本机一次性实例或服务器上的 `xxx_it` 库），导入 `mysql-base` + 增量 SQL，用真实触发器/函数跑并发取号、幂等、冲突、留痕。
RDS/ECS 公网 3306 握手失败时走 SSH 隧道，见 `references/http-acceptance-harness.md`。

**第4步：HTTP 全链路 E2E**
起真实 JAR 连真实库，用脚本跑接口矩阵（鉴权→登记→冲突→列表→协同→统计→导出→修改→作废→白名单撤销→并发）。
需要微信登录的后端，用"直接插会话"绕过第三方换取 token，不要因为拿不到 wx code 就跳过测试，见 references。

**第5步：清理 + 入库**
测试数据必须清回原状（子表→主表→留痕→流水→日志→会话），并在报告写明"已清理，主表 0 行"。
报告写进仓库 `docs/TEST-REPORT-<日期>.md`，再 commit + push。

## 三、审查时优先找这几类问题（比通读有效）

| 类别 | 怎么查 |
|---|---|
| 权限范围 | 每个查询是否真的在 SQL 里带 `mgr_phone`，而不是前端藏按钮 |
| 事务边界 | `SET @app_user` / 取号 / 写主表是否同一连接、同一事务 |
| 审计完整性 | 日志表 module 是否被硬编码成单一值、ip 是否恒 NULL、失败是否落日志 |
| 错误映射 | CHECK/NOT NULL 是否被统一映射成 409"数据冲突"（应为 400 + 字段提示） |
| 分页契约 | 明细接口有没有 `total`，前端能不能翻页 |
| 状态一致性 | 作废后列表/统计/提醒是否同步过滤；物理删后幂等键是否残留指向已删单号 |
| 权限锁死 | 能不能删掉最后一名管理员；能不能倒填任意历史日期 |

## 四、坑

- **用户说"表我已经在服务器上建好了"≠建好了**。实测过一次：所谓"建好"只是原有 8 张基础表，后端要的 5 张扩展表一张没有。动手前先列 `information_schema.tables` 对象清单，再决定要不要补。
- 补增量 DDL 前先 `mysqldump` 备份，脚本要幂等（`IF NOT EXISTS` + `INSERT ... WHERE NOT EXISTS`），执行后再列清单核对。别在生产库跑旧的全量 DDL。
- 应用账号只有 DML+EXECUTE 时**查不到触发器定义**（`ERROR 1227 ... TRIGGER privilege(s)`），核对触发器要用 root 的 `--defaults-file`。
- H2/MockMvc 全绿不等于真库全绿：H2 没有触发器取号、没有 `FOR UPDATE SKIP LOCKED`、没有严格 CHECK。
- 测试写进真实库的数据一定要清，清的顺序不能反（子表先删，否则 FK 挡住；删主表会触发 AD 往留痕表写行）。
- 项目目录可能嵌在更大的未提交 git 树里（`git rev-parse --show-toplevel` 指到上层 `Documents/工作`）。**必须在项目目录内 `git init` 建独立仓库**，否则第一次 commit 会把整个工作目录卷进来。用户明确要求过"代码记得做 git 同步，做好版本控制"：改前 commit 快照、改后 commit、推私有远端。

## 五、支持文件

- `references/http-acceptance-harness.md` — 绕过微信登录的会话播种 SQL、urllib E2E harness 骨架、验收矩阵、SSH 隧道与一次性 MySQL 实例命令、清理 SQL 顺序。
