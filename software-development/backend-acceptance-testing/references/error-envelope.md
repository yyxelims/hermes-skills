# 统一错误响应（可直接照抄的骨架）

用户原话：「后端做好细致的报错说明」。要求不是"有 message 就行"，而是**前端拿着响应就能告诉用户改哪个字段、改成什么样**。

## 1. 响应形态

单字段错误：`field` 和 `message` 提到顶层，同时保留 `errors` 数组（前端只写一条解析路径）。

```json
{"code":"VALIDATION_FAILED",
 "message":"工作内容不能超过1000个字（当前1001字）",
 "field":"content",
 "errors":[{"field":"content","message":"工作内容不能超过1000个字（当前1001字）"}]}
```

多字段错误：一次返回全部，不要第一个失败就抛。

```json
{"code":"VALIDATION_FAILED",
 "message":"提交内容有 3 处需要修改",
 "errors":[{"field":"endTime","message":"结束时间必须晚于开始时间"},
           {"field":"buyerName","message":"买方姓名必填"},
           {"field":"bizChannel","message":"业务渠道必填"}]}
```

业务冲突：带冲突明细，前端可直出"与 09:30 在某城区的安排冲突"。

```json
{"code":"TIME_CONFLICT",
 "message":"该时段与已有外出安排重叠，请调整时间或先修改原安排",
 "conflicts":[{"regNo":"20261126000002","beginTime":"2026-11-27T09:30:00",
               "endTime":"2026-11-27T10:30:00","areaName":"某城区","placeName":"测试签约中心"}]}
```

参数格式错：给 `expected` 示例 + 回显 `received`。

```json
{"code":"INVALID_PARAMETER","message":"参数 from 格式不正确","field":"from",
 "expected":"2026-12-01T09:30:00（北京时间，不带时区偏移）","received":"不是时间"}
```

未知字段/JSON 坏：`hints` 数组，写清"字段名大小写"并给完整请求示例。

## 2. Java 侧结构

```java
class ApiError extends RuntimeException {
    final int status; final String code; final String field; final Map<String,Object> extra;
    static void require(boolean ok,String msg){ if(!ok) throw new ApiError(400,msg); }
    static ApiError invalid(String field,String msg){ return new ApiError(400,"VALIDATION_FAILED",msg,field,null); }
    static ApiError validation(List<Map<String,String>> errors){
        if(errors.size()==1){ var only=errors.get(0);           // 单条提顶层
            return new ApiError(400,"VALIDATION_FAILED",only.get("message"),only.get("field"),Map.of("errors",errors)); }
        return new ApiError(400,"VALIDATION_FAILED","提交内容有 "+errors.size()+" 处需要修改",null,Map.of("errors",errors));
    }
}
```

序列化用 `LinkedHashMap` 保序（`code`、`message`、`field`、其余），`null` 字段不输出。

## 3. HTTP × code 表（写进 README，前端照着分支）

| HTTP | code | 场景 |
|---|---|---|
| 400 | VALIDATION_FAILED | 缺失、超长、时间先后、坐标越界、字典项不存在 |
| 400 | MISSING_PARAMETER / MISSING_HEADER | 缺查询参数 / 缺幂等键 |
| 400 | INVALID_PARAMETER | 类型或格式不对（带 expected） |
| 400 | INVALID_JSON | 非法 JSON、未知字段、字段类型错（带 hints） |
| 401 | UNAUTHORIZED | 未登录 / 会话过期 / 被移出白名单 |
| 403 | FORBIDDEN | 缺功能码（带 requiredFunction/requiredAction） |
| 404 | NOT_FOUND | 单号不存在或已作废、路径错 |
| 405 | METHOD_NOT_ALLOWED | 带 allowed 列表 |
| 409 | TIME_CONFLICT | 时段重叠（带 conflicts） |
| 409 | DUPLICATE_KEY / PHONE_BOUND / WECHAT_BOUND | 唯一键、绑定冲突 |
| 415 | MEDIA_TYPE_NOT_SUPPORTED | 没带 application/json |
| 500 | INTERNAL_ERROR | 未预期异常，记日志不返堆栈 |
| 503 | DATABASE_UNAVAILABLE / QUERY_TIMEOUT / THIRD_PARTY_UNAVAILABLE | 依赖不可用 |

## 4. 数据库异常翻译（别一把抓成 409）

```java
@ExceptionHandler(DataIntegrityViolationException.class) ResponseEntity<?> integrity(DataIntegrityViolationException ex){
    Throwable cause=ex.getMostSpecificCause();
    int code=cause instanceof SQLException se?se.getErrorCode():0;
    String text=Objects.toString(cause.getMessage(),"");
    var m=COLUMN.matcher(text); String column=m.find()?m.group(1):null;   // 正则 "column 'x'"
    return switch(code){
        case 1406 -> body(new ApiError(400,"FIELD_TOO_LONG","字段 "+column+" 内容超长",column,...));
        case 1048 -> body(new ApiError(400,"MISSING_FIELD","必填字段 "+column+" 不能为空",column,...));
        case 3819 -> body(byConstraintName(text));      // ck_xxx → 中文 + 字段
        case 1062 -> body(new ApiError(409,"DUPLICATE_KEY",...));
        case 1452 -> body(new ApiError(409,"REFERENCE_MISSING",...));
        case 1205,1213 -> body(new ApiError(503,"RETRY_LATER","数据库繁忙，请稍后重试"));
        default -> body(new ApiError(409,"DATA_CONFLICT",...));
    };
}
```

CHECK 约束按名字给中文（`ck_outwork_sign` → "签单必须填写买方、卖方、业务类型、业务渠道…"），并把 `field` 指到最可能的字段。**CHECK 违约是 400，不是 409**——这是最容易犯的"一把抓"错误。

## 5. 必须补的 handler 清单

缺参、缺头、类型错、JSON 错、405、415、404、数据库不可用、超时、兜底 500。
兜底 500 只记服务端日志，响应固定一句"服务处理失败，请稍后重试；若持续出现请联系管理员"，不返回异常类型或堆栈。

## 6. 验证方式

E2E 里逐条断言 `code` / `field` / 关键文案，例如：

- 缺 `from` → `code=MISSING_PARAMETER, field=from`
- `from=不是时间` → `code=INVALID_PARAMETER, expected` 含示例格式
- 未知字段 → `code=INVALID_JSON` 且 `hints` 非空
- 三处字段错 → `errors` 的 field 集合包含三项
- 重叠 → `conflicts` 长度 1 且含 regNo/时段
- 405 → `allowed` 含 `GET`

只断言 HTTP 状态码不够：用户要的"细致"体现在 `field` 和文案上。
