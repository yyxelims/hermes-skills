# 统一错误响应契约（Spring Boot）

前端只读 `code` 分支、按 `field` 高亮、`message` 直接弹给用户。别让前端猜。

## 响应形状

固定含 `code`（机器码）+ `message`（人读中文），能定位字段时带 `field`，其余按情况附 `expected` / `received` / `errors` / `conflicts` / `allowed` / `hints`。

单字段：

```json
{"code":"VALIDATION_FAILED","message":"工作内容不能超过1000个字（当前1001字）","field":"content",
 "errors":[{"field":"content","message":"工作内容不能超过1000个字（当前1001字）"}]}
```

多字段（一次性列全，不要改一个报一个）：

```json
{"code":"VALIDATION_FAILED","message":"提交内容有 3 处需要修改",
 "errors":[{"field":"endTime","message":"结束时间必须晚于开始时间"},
           {"field":"buyerName","message":"买方姓名必填"},
           {"field":"bizChannel","message":"业务渠道必填"}]}
```

冲突（带上冲突对象，前端可直接提示改哪段）：

```json
{"code":"TIME_CONFLICT","message":"该时段与已有外出安排重叠，请调整时间或先修改原安排",
 "conflicts":[{"regNo":"20261126000002","beginTime":"2026-11-27T09:30:00",
               "endTime":"2026-11-27T10:30:00","areaName":"某城区","placeName":"测试签约中心"}]}
```

## 异常类设计

```java
class ApiError extends RuntimeException {
    final int status; final String code; final String field; final Map<String,Object> extra;
    ApiError(int status,String message){this(status,defaultCode(status),message,null,null);}
    ApiError(int status,String code,String message,String field,Map<String,Object> extra){...}
    static ApiError invalid(String field,String message){ return new ApiError(400,"VALIDATION_FAILED",message,field,null); }
    static ApiError validation(List<Map<String,String>> errors){
        if(errors.size()==1){                       // 单条错误提到顶层，前端只读 field/message
            var only=errors.get(0);
            return new ApiError(400,"VALIDATION_FAILED",only.get("message"),only.get("field"),Map.of("errors",errors));
        }
        return new ApiError(400,"VALIDATION_FAILED","提交内容有 "+errors.size()+" 处需要修改",null,Map.of("errors",errors));
    }
}
```

组装响应时用 `LinkedHashMap` 保证 `code`/`message` 在前，且 null 字段不输出。

## 必须注册的 @ExceptionHandler

| 异常 | 状态 | code | 关键点 |
|---|---|---|---|
| `ApiError` | 自带 | 自带 | 业务异常唯一出口 |
| `MissingServletRequestParameterException` | 400 | `MISSING_PARAMETER` | `field` 用 `e.getParameterName()` |
| `MissingRequestHeaderException` | 400 | `MISSING_HEADER` | 如 `Idempotency-Key` |
| `MethodArgumentTypeMismatchException` | 400 | `INVALID_PARAMETER` | `expected` 给示例：`2026-12-01T09:30:00` |
| `HttpMessageNotReadableException` | 400 | `INVALID_JSON` | `hints` 提示字段名大小写 / 时间格式 / 完整示例 |
| `HttpRequestMethodNotSupportedException` | 405 | `METHOD_NOT_ALLOWED` | `allowed` 列方法 |
| `HttpMediaTypeNotSupportedException` | 415 | `MEDIA_TYPE_NOT_SUPPORTED` | 提示 `Content-Type: application/json` |
| `NoResourceFoundException` | 404 | `NOT_FOUND` | 未匹配路由 |
| `DataIntegrityViolationException` | 细分 | 见下表 | 取 `getMostSpecificCause()` 的 SQLState/errorCode |
| `DataAccessResourceFailureException` | 503 | `DATABASE_UNAVAILABLE` | 含 `CannotGetJdbcConnectionException`（父子类，别重复注册） |
| `QueryTimeoutException` | 503 | `QUERY_TIMEOUT` | 建议缩小时间范围 |
| `Exception` | 500 | `INTERNAL_ERROR` | 记日志，**不返回堆栈** |

## 数据库错误翻译

```java
int code = cause instanceof SQLException se ? se.getErrorCode() : 0;
String text = Objects.toString(cause.getMessage(),"");
Matcher m = Pattern.compile("column '([^']+)'").matcher(text);
String column = m.find() ? m.group(1) : null;
```

| errorCode | 状态 | code | 文案 |
|---|---|---|---|
| 1406 | 400 | `FIELD_TOO_LONG` | 字段 X 内容超长 |
| 1048 | 400 | `MISSING_FIELD` | 必填字段 X 不能为空 |
| 3819 | 400 | 按约束名细分 | 见下 |
| 1062 | 409 | `DUPLICATE_KEY` | 数据已存在，不能重复提交 |
| 1452 | 409 | `REFERENCE_MISSING` | 关联记录不存在 |
| 1205 / 1213 | 503 | `RETRY_LATER` | 数据库繁忙 |

3819 按约束名映射（MySQL 的 message 里含约束名）：`ck_xxx_sign` → 签单必填字段缺失、`ck_xxx_time` → 结束早于开始、`ck_xxx_coord` → 经纬度不成对/越界。**不要把这些统一报成 409"数据冲突"**，前端会提示错方向。

## 坑

- `DataIntegrityViolationException` 笼统映射 409 是常见错误：CHECK 约束违反本质是 400 参数问题。
- 多字段校验如果第一条就 `throw`，前端得改一次提交一次。收集到列表再抛。
- 500 兜底 handler 里必须 `log.error`，否则线上只有"服务处理失败"没有线索。
- `spring.jackson.deserialization.fail-on-unknown-properties=true` 能让"字段名拼错"变成明确 400，但**只对 Spring Boot 正常启动生效**；手动建 ApplicationContext 的测试要单独加这个属性。
