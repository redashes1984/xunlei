# 迅雷远程下载服务(非官方)

<!-- AGENT-PROMPT -->
给自动化 Agent 的开场指令：本仓库自带一份可直接加载的技能文件 `SKILL.md`（仓库根目录）。
在操作迅雷面板之前，先阅读并遵循 `SKILL.md`：它定义了 headless 提交下载任务（CLI REST :8787 / MCP stdio）、查询、清理记录与产物的完整用法、环境变量约定与全部生产坑位。
不要重复造轮子：浏览器自动化是兜底路径，优先走 sidecar HTTP API。改动本仓库代码后的验收流程也写在 `SKILL.md` 末尾「Verify deployments honestly」。

[![GitHub Stars][1]][2] [![Docker Pulls][3]][5] [![Docker Version][4]][5]

[1]: https://img.shields.io/github/stars/cnk3x/xunlei?style=flat
[2]: https://star-history.com/#cnk3x/xunlei&Date
[3]: https://img.shields.io/docker/pulls/cnk3x/xunlei.svg
[4]: https://img.shields.io/docker/v/cnk3x/xunlei
[5]: https://hub.docker.com/r/cnk3x/xunlei

从迅雷群晖套件中提取出来用于其他设备的迅雷远程下载服务程序。仅供研究学习测试。 \
本程序仅提供 Linux 模拟和容器化运行环境，未对原版迅雷程序进行任何修改。

**当前为测试版本，版本号 [4.0.0-beta](https://hub.docker.com/layers/cnk3x/xunlei/4.0.0-beta)，且并未大规模验证。**

**3.20 版本介绍在此: (https://github.com/cnk3x/xunlei/tree/v3.20.2)**

## 特性

- 支持本地运行和容器化运行
- 重构了运行环境，有比较完善的回滚流程。
- 容器镜像基于busybox，不再内嵌SPK，改成从远程下载，大幅减小了镜像体积(50M->5M)。
- 不再内嵌SPK，不在受镜像包的luncher限制，理论上随时可以使用任何指定的版本。

## 使用

### Docker

#### 镜像

```plain
cnk3x/xunlei:beta
ghcr.io/cnk3x/xunlei:beta

# 或者指定版本
cnk3x/xunlei:4.0.0-beta
ghcr.io/cnk3x/xunlei:4.0.0-beta
```

#### 参数

程序默认参数

```shell
OPTIONS:
      --dashboard_port uint16       网页访问的端口 [XL_DASHBOARD_PORT, XL_PORT] (default 2345)
      --dashboard_ip ip             网页访问绑定IP，默认绑定所有IP [XL_DASHBOARD_IP, XL_IP]
      --dashboard_username string   网页访问的用户名 [XL_DASHBOARD_USERNAME, XL_BA_USER]
      --dashboard_password string   网页访问的密码 [XL_DASHBOARD_PASSWORD, XL_BA_PASSWORD]
  -d, --dir_download strings        下载保存文件夹，可多次指定，需确保有权限访问 [XL_DIR_DOWNLOAD] (default [/mnt/d/Code/github.com/cnk3x/xunlei/artifacts/xunlei/downloads])
  -D, --dir_data string             程序数据保存文件夹，其下'.drive'文件夹中，存储了登录的账号，下载进度等信息 [XL_DIR_DATA] (default "/mnt/d/Code/github.com/cnk3x/xunlei/artifacts/xunlei/data")
  -u, --uid uint32                  运行迅雷的用户ID [XL_UID, UID]
  -g, --gid uint32                  运行迅雷的用户组ID [XL_GID, GID]
      --prevent_update              阻止更新 [XL_PREVENT_UPDATE]
  -r, --chroot string               主目录 [XL_CHROOT] (default "/mnt/d/Code/github.com/cnk3x/xunlei/artifacts/xunlei")
      --spk string                  SPK 下载链接 [XL_SPK] (default "https://down.sandai.net/nas/nasxunlei-DSM7-x86_64.spk")
  -F, --force_download              强制下载 [XL_SPK_FORCE_DOWNLOAD]
      --launcher_log_file string    迅雷启动器日志文件 [XL_LAUNCHER_LOG_FILE]
      --debug                       是否开启调试日志 [XL_DEBUG]
```

容器内参数默认值（在容器内运行时，覆盖程序默认参数）

```shell
#网页访问的端口
XL_DASHBOARD_PORT=2345
#网页访问绑定IP
XL_DASHBOARD_IP=
# 网页访问的用户名
XL_DASHBOARD_USERNAME=
# 网页访问的密码
XL_DASHBOARD_PASSWORD=
# 如果需要指定多个下载目录，手动指定XL_DIR_DOWNLOAD
# 多个以冒号`:`隔开，在容器内,都必须以 /xunlei 开头，迅雷面板选择保存路径显示会去掉/xunlei前缀
# 指定后可以在 volumes 中绑定宿主机实际目录
# 迅雷云盘的缓存会使用第一个目录会缓存
# /xunlei/后面可以用中文
# 不设置默认一个目录 /xunlei/downloads
XL_DIR_DOWNLOAD=/xunlei/downloads
# 程序数据保存文件夹，存储了登录的账号，下载进度等信息,容器内不要更改
XL_DIR_DATA=/xunlei/data
# 阻止更新
XL_PREVENT_UPDATE=false
# SPK下载链接, 默认指向官方下载地址，如果失效，请自行指定 ***.spk的下载地址
# 可以使用 file:/// 访问本地文件, 真实使用路径会去掉 file://, 所以如果是绝对路径, 三个斜杠不能少
XL_SPK=
# 是否强制下载SPK, 0: 不强制, 1: 强制，如果不指定强制下载，不会重复下载SPK
XL_SPK_FORCE_DOWNLOAD=0
# 运行迅雷的用户ID, 默认0,即 root 账号
# 推荐使用当前账号的UID和GID, 一般来说是 1000, 以免出现下载后普通账号无法处理文件的情况
XL_UID=0
# 运行迅雷的用户GID
XL_GID=0
# 是否开启调试日志
XL_DEBUG=false
```

#### 示例: docker-compose

```yaml
services:
  xunlei:
    container_name: xunlei
    image: cnk3x/xunlei:beta
    restart: unless-stopped

    # 宿主机名，迅雷远程控制的名称与此相关，会显示 `群晖-r66s`
    hostname: r66s

    # 必须, cap_add: [SYS_ADMIN] 和 privileged: true 二选一
    cap_add: [SYS_ADMIN]

    # 面板访问端口，如需更改访问端口到5432，替换前面的2345为5432即可
    ports: [2345:2345/tcp]
    network_mode: bridge
    # 可以通过环境变量 XL_DASHBOARD_PORT=5432 来更改内部端口, 不过bridge网络模式没有必要更改默认端口
    # 如果设置 network_mode: host, 将忽略上面的端口映射配置(ports), 但可以通过环境变量 XL_DASHBOARD_PORT=5432 来更改端口
    # network_mode: host

    environment:
      ##如果需要指定多个下载目录，手动指定XL_DIR_DOWNLOAD
      ##多个以冒号`:`隔开，都必须以 /xunlei 开头，迅雷面板选择保存路径显示会去掉/xunlei前缀
      ##指定后可以在 volumes 中绑定宿主机实际目录
      ##迅雷云盘的缓存会使用第一个目录会缓存
      ##/xunlei/后面可以用中文
      ##不设置默认一个目录 /xunlei/downloads
      #- XL_DIR_DOWNLOAD=/xunlei/下载:/xunlei/影音:/xunlei/大人

      # 设置用户身份，请确保该用户对 XL_DIR_DOWNLOAD 指定的目录或者默认的 /xunlei/downloads 有读写权限
      - XL_UID=1000 # 用户ID
      - XL_GID=1000 # 用户组ID
    volumes:
      ## 二选一必须，对应 XL_DIR_DOWNLOAD 指定的目录, 请替换冒号前面的路径为实际路径
      #- /vol1/1000/下载:/xunlei/下载
      #- /vol1/1000/影音/下载:/xunlei/影音
      #- /vol1/1000/大人/下载:/xunlei/大人

      ## 二选一必须，如果没有通过 XL_DIR_DOWNLOAD 指定下载目录，请将下面这行代码替换为上面代码
      - /vol1/1000/下载:/xunlei/downloads

      # 必须，数据目录，迅雷运行时，插件，升级，包括登录数据都在这
      - ./data:/xunlei/data

      # 可选，首次初始化，会从远程下载迅雷套件到此处，如果不配置每次重新创建都会重新从远程下载
      - ./cache:/xunlei/var/packages/pan-xunlei-com
```

# xlmcp — cnk3x/xunlei Docker 面板的无浏览器桥接

零依赖 Python 3 sidecar（仅标准库），无需浏览器即可驱动
[cnk3x/xunlei](https://github.com/cnk3x/xunlei) Docker 面板。
三个使用面：**CLI**、**REST API**、**MCP stdio 服务器**。

面板（`http://<host>:2345/webman/3rdparty/pan-xunlei-com/index.cgi`）
正常情况下需要一个浏览器 SPA 会话。xlmcp 直接复刻其鉴权链：

1. `GET /webman/login.cgi?enable_syno_token=yes` + Basic 认证 → `SynoToken`
2. `GET <panel>/` → 从 HTML 中提取内嵌 JWT
3. 携带 `pan-auth: <jwt>` + `x-syno-token` + Basic 头，直接调用 CGI 路径

> 说明：`device/v1/fetch` 代理带有 URL 白名单，多数绝对地址会被拒绝
> （返回 "url not allowed"）——绕过它，直接请求相对 CGI 路径即可。

## 依赖要求

- Python ≥ 3.8（仅标准库，无需 pip 安装任何东西）
- 一个运行中的 cnk3x/xunlei 容器

## 配置（环境变量）

| 变量 | 用途 | 默认值 |
|---|---|---|
| `XL_URL` | 完整的面板基础 URL，优先级最高，直接覆盖 HOST/PORT | — |
| `XL_HOST` | 仅面板主机（`XL_URL` 未设置时生效） | `10.10.4.21` |
| `XL_PORT` | 仅面板端口（`XL_URL` 未设置时生效） | `2345` |
| `XL_USER` | 面板 Basic 认证用户名 | (自己的账号名) |
| `XL_PASS` | 面板 Basic 认证密码 | (自己的密码) |
| `XL_API_PORT` | `serve` 模式的 REST 监听端口 | `8787` |
| `XL_API_KEY` | REST 面的共享密钥（校验 `X-API-KEY` 请求头），留空即关闭鉴权 | `""` |

基础 URL 解析顺序：`XL_URL` > `XL_HOST`/`XL_PORT`。两者都未设置时默认：
`http://10.10.4.21:2345/webman/3rdparty/pan-xunlei-com/index.cgi`。

## CLI

```bash
# 设备就绪检查（输出 {"ready": true, "about": {...}}）
python3 xlmcp.py status

# 列出最近的下载任务
python3 xlmcp.py list --limit 20

# 提交下载并等待 COMPLETE/ERROR（默认等待上限 600 秒）
python3 xlmcp.py add https://example.com/file.zip --name mypack

# fire-and-forget：立刻返回任务 id，不等待
python3 xlmcp.py add https://example.com/file.zip --no-wait

# 任务到达终态后，把结果 JSON POST 给 callback 回调地址
python3 xlmcp.py add https://example.com/file.zip --callback http://127.0.0.1:9911/done --deadline 300

# 删除任务记录（连同下载产物）：按 id 删，不带 id 则清理整个近期列表
python3 xlmcp.py remove VP1vXXXX YYYY
python3 xlmcp.py remove                # 清空近期列表
python3 xlmcp.py remove --keep-files   # 只删记录，文件留在磁盘上
python3 xlmcp.py remove --limit 100    # 批量清理的窗口大小

# REST 服务（见下文），可覆盖绑定地址：
python3 xlmcp.py serve --host 0.0.0.0

# MCP stdio 服务器（见下文）
python3 xlmcp.py --mcp

# 帮助
python3 xlmcp.py help
```

`add` 的参数：`--name NAME`（文件名/词干，默认取 URL 最后一段并去掉查询串）、
`--callback URL`、`--deadline SEC`（默认 600）、`--no-wait`。

成功后 CLI 打印紧凑摘要——用 `ok` 字段分支判断：

```json
{
 "summary": {"id": "VP1v...", "name": "mypack", "phase": "PHASE_TYPE_COMPLETE",
             "ok": true, "message": "完成", "path": "/downloads/mypack", "size": "16958"},
 "task": {...完整的迅雷任务对象...}
}
```

带 `--no-wait` 时只输出 `{"summary": {"id": ..., "phase": "submitted"}}`。

## REST API

启动服务：`python3 xlmcp.py serve`（监听 `XL_API_PORT`，默认 8787）。
设置了 `XL_API_KEY` 时，每个请求必须携带 `X-API-KEY: ***
key 为空即关闭鉴权（启动横幅会打印 `auth=off`）。

### `GET /health`
存活检查 + 面板就绪状态。
```bash
curl -s http://127.0.0.1:8787/health
# {"ok": true, "ready": true, "about": {"kind": "drive#about", ...}}
```

### `GET /api/v1/tasks?limit=N`
列出最近的下载任务（迅雷 `drive#task` 对象）。`limit` 非法时回落为 50，
而不是断开连接。
```bash
curl -s 'http://127.0.0.1:8787/api/v1/tasks?limit=20'
```

### `GET /api/v1/tasks/{id}`
按 id 查询单个任务。查找只扫描最近的列表窗口——任务老化出窗后 id 即失效。
查不到返回 `{}`。
```bash
curl -s http://127.0.0.1:8787/api/v1/tasks/VP1vAoajw3cYB24N5bv5U8ydA1
```

### `POST /api/v1/tasks`
提交下载。默认阻塞直到 COMPLETE/ERROR，返回
`{"summary": {...}, "task": {...}}`。

请求体字段——`url`（必填）；可选 `name`、`callback`、`deadline`
（秒，默认 600）、`no_wait`（布尔）：
```bash
curl -s -X POST http://127.0.0.1:8787/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.baidu.com/favicon.ico","name":"probe"}'

# 异步：不挂住 HTTP 连接——任务完成后把摘要 JSON POST 给 callback
curl -s -X POST http://127.0.0.1:8787/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://…/file.zip","callback":"http://collector:9911/done","deadline":900}'

# fire-and-forget
curl -s -X POST http://127.0.0.1:8787/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://…/file.zip","no_wait":true}'
```

错误均为 JSON：`500 {"error": "…"}`、`/health` 探测失败 `502`、
密钥不对 `401 {"error":"bad X-API-KEY"}`、未知路由 `404`。

### `DELETE /api/v1/tasks/{id}`
删除一条任务记录**及其下载产物**（即任务 `params.real_path` 指向的、下载目录下对应的文件／目录）。
已完成和失败/挂起态任务都适用；没有 `real_path` 的任务只删记录。
`?keep_files=1` 表示只删记录、保留磁盘上的文件。
```bash
curl -s -X DELETE http://127.0.0.1:8787/api/v1/tasks/VP1vAoajw3cYB24N5bv5U8ydA1
# {"removed": [{"id":"...", "name":"...", "phase":"...", "path":"/downloads/...", ...}]}
```

### `DELETE /api/v1/tasks?limit=N`
批量清理近期列表（默认 50）：对列表中每条任务执行同样的「记录+产物」删除。
适合批量管线跑完后的收尾清理。与单条路由一致，同样支持 `?keep_files=1`。
```bash
curl -s -X DELETE 'http://127.0.0.1:8787/api/v1/tasks?limit=20'
curl -s -X DELETE 'http://127.0.0.1:8787/api/v1/tasks?limit=20&keep_files=1'
```

### 供 Agent 使用的完成回报
两种机制，任选其一：
1. **同步**——保持 POST 连接；返回时读 `summary.ok`
   （`true` ⇔ `phase == PHASE_TYPE_COMPLETE`）。小文件典型延迟 ≈6 秒。
2. **异步回调**——设置 `"callback":"http://…"`。任务到达终态后，sidecar
   把摘要 JSON（`{id,name,phase,ok,message,path,size}`）POST 到该 URL，
   best-effort（失败记入 stderr）。超时时摘要带 `"phase":"TIMEOUT"`。

### 作为服务常驻
systemd unit 示例：
```ini
[Unit]
Description=xlmcp Thunder bridge
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 /root/xl-mcp/xlmcp.py serve
Environment=XL_HOST=10.10.4.21 XL_PORT=2345 XL_API_KEY=
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## MCP 服务器

以 stdio 方式对任何支持 MCP 的 Agent 宿主提供服务：

```json
{
  "mcpServers": {
    "xlmcp": { "command": "python3", "args": ["/root/xl-mcp/xlmcp.py", "--mcp"] }
  }
}
```

实现了 `initialize`、`notifications/initialized`、`tools/list`、
`tools/call`，并有 ping 风格兜底。共四个工具：

| 工具 | 参数 | 行为 |
|---|---|---|
| `status` | — | 设备就绪检查。 |
| `list_tasks` | `{limit?: int=50}` | 最近任务列表。 |
| `add_task` | `{url, name?, callback?, deadline?=600, no_wait?}` | 语义同 REST POST：等待 COMPLETE/ERROR，返回 `{summary, task}`；可选 `callback` 以 POST 接收摘要 JSON；`no_wait` 返回 `{summary:{id,phase:"submitted"}}`。 |
| `remove_task` | `{ids?, keep_files?, limit?=50}` | 删除任务记录及下载产物。给定 `ids` 列表逐条删除；省略或传 `[]` 则清理近期列表（窗口 `limit`）。`keep_files:true` 保留磁盘文件。返回 `{removed:[摘要…]}`。 |

快速冒烟测试：
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | python3 xlmcp.py --mcp
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 xlmcp.py --mcp
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"add_task","arguments":{"url":"https://www.baidu.com/favicon.ico","name":"mcp-probe"}}}' | python3 xlmcp.py --mcp
```

## 实现要点

- **令牌缓存自愈**：JWT/SynoToken 按进程缓存；面板轮换令牌（重启/重新部署）后，
  下一次失败的 `api()` 调用会丢弃缓存并重取一次——常驻的 `serve` 进程无需手动重启即可恢复。
- **任务可见性延迟**：空 space 的迅雷列表对新任务滞后数分钟；因此 `task_by_id`
  先查 runner space 作用域的列表（`space=device_id#…`），再回落查空 space 列表。
  这是同步完成回报能在几秒而不是几分钟内到达的原因。
- **`params.target` 陷阱**：必须是 runner 的真实 `device_id`（从 `user#runner`
  任务的 `params.target` 读取）。写字面量 `"downloads"` 会让任务永远卡在
  `PHASE_TYPE_PENDING`。
