# 单机部署：Aliyun Linux + JDK21 + systemd + nginx

## 1. JDK

Aliyun Linux 4 的 yum 源只有 `java-1.8.0-openjdk`，Spring Boot 3.x 要 21：

```sh
curl -fL -o /tmp/jdk21.tar.gz \
  "https://api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jdk/hotspot/normal/eclipse"
mkdir -p /opt/jdk-21 && tar xzf /tmp/jdk21.tar.gz -C /opt/jdk-21 --strip-components=1
rm -f /tmp/jdk21.tar.gz            # 199MB，装完立即删
/opt/jdk-21/bin/java -version
```

## 2. 目录与权限

```
/opt/outwork/releases/1.0.2/outwork-backend.jar   # 版本化，按版本存
/opt/outwork/current -> releases/1.0.2            # 软链切换
/etc/outwork/backend.env                          # root:root 600
/etc/systemd/system/outwork.service
```

```sh
useradd -r -s /sbin/nologin -d /opt/outwork outwork-api
chown -R outwork-api:outwork-api /opt/outwork
install -m 600 -o root -g root /tmp/backend.env /etc/outwork/backend.env
```

环境文件放数据库密码、AppID/Secret、第三方 key。**不要写进仓库、不回显、不写进日志。**

## 3. systemd

```ini
[Service]
User=outwork-api
WorkingDirectory=/opt/outwork/current
EnvironmentFile=/etc/outwork/backend.env
ExecStart=/opt/jdk-21/bin/java -Duser.timezone=Asia/Shanghai -Dfile.encoding=UTF-8 \
          -XX:+ExitOnOutOfMemoryError -jar /opt/outwork/current/outwork-backend.jar
Restart=on-failure
RestartSec=8
TimeoutStopSec=40
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
```

- `ExecStart` 写**绝对路径**，系统里没有 `java` 也能起。
- 内存吃紧：`JAVA_TOOL_OPTIONS="-Xms64m -Xmx192m -XX:MaxMetaspaceSize=128m"`，1.8G 机器实测 RSS ≈185MB。
- 优雅停机：`server.shutdown=graceful` + `spring.lifecycle.timeout-per-shutdown-phase=20s`。

## 4. nginx 反代

```nginx
location /api/v1/ {
    client_max_body_size 128k;
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 60s;
}
location ^~ /health/ { return 404; }     # 健康检查不对外
```

后端只 `BIND_ADDRESS=127.0.0.1`，外网全走 nginx。

## 5. 发布与回滚

```sh
# 发布
ssh root@host 'mkdir -p /opt/outwork/releases/1.0.2'
scp target/app-1.0.0.jar root@host:/opt/outwork/releases/1.0.2/outwork-backend.jar
ssh root@host 'chown -R outwork-api:outwork-api /opt/outwork/releases/1.0.2 && \
               ln -sfn /opt/outwork/releases/1.0.2 /opt/outwork/current && \
               systemctl restart outwork'

# 回滚：只切软链
ssh root@host 'ln -sfn /opt/outwork/releases/1.0.1 /opt/outwork/current && systemctl restart outwork'
```

**先 `readlink -f /opt/outwork/current` 再删旧版本**，别删掉正在跑的目录。保留当前版 + 上一版（各 24MB 左右），其余删掉并清 `dnf clean all`（约 79MB）。

## 6. 验证

```sh
systemctl is-active outwork
curl -s localhost:8080/health/ready          # {"status":"UP"}
curl -s -o /dev/null -w '%{http_code}\n' https://<domain>/api/v1/<需要登录的接口>   # 401
```

外部依赖（微信/高德）也要在**服务器上**验证一次，不要只在本地测。

## 7. 坑

- **动用户已有的 nginx 站点/域名前必须先问**。改之前 `cp` 备份并告知路径，被质疑时能立刻回滚（`cp` 回来 + `nginx -t` + `reload`）。
- 复合危险命令（切换 + 重启 + 删除 + 多步验证）容易触发审批超时被拦。**拆成单条最小命令**，每步单独执行。
- 执行增量 DDL 前先 `mysqldump` 一份到 `/root/db_backup/`，把文件名写进报告。
- `ProtectSystem=strict` 下 JVM 写 `/tmp` 靠 `PrivateTmp=true` 提供；不要再加 `ReadWritePaths` 除非确实要写业务目录。
- 服务器内存 1.8G 时，MySQL + JVM + 其他常驻服务要一起算，别只看 `free` 的 available。
