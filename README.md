# 迅雷远程下载服务(非官方)

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

# xlmcp — Headless bridge for the cnk3x/xunlei Docker panel

Zero-dependency Python 3 sidecar (stdlib only) that drives the
[cnk3x/xunlei](https://github.com/cnk3x/xunlei) Docker panel without a browser.
Three surfaces: **CLI**, **Komga-style REST**, **MCP stdio server**.

The panel (`http://<host>:2345/webman/3rdparty/pan-xunlei-com/index.cgi`)
normally needs a browser SPA session. xlmcp reproduces its auth chain directly:

1. `GET /webman/login.cgi?enable_syno_token=yes` with Basic auth → `SynoToken`
2. `GET <panel>/` → scrape the embedded JWT from the HTML
3. Call CGI paths directly with headers `pan-auth: <jwt>` + `x-syno-token` + Basic

> Note: the `device/v1/fetch` proxy enforces a URL allowlist and rejects most
> absolute URLs ("url not allowed") — bypass it and hit relative CGI paths directly.

## Requirements

- Python ≥ 3.8 (stdlib only; no pip installs)
- A running cnk3x/xunlei container

## Configuration (environment variables)

| Variable | Purpose | Default |
|---|---|---|
| `XL_URL` | Full panel base URL. Highest priority — overrides HOST/PORT entirely. | — |
| `XL_HOST` | Panel host only (used when `XL_URL` unset). | `10.10.4.21` |
| `XL_PORT` | Panel port only (used when `XL_URL` unset). | `2345` |
| `XL_USER` | Panel Basic-auth username. | `bdm965` |
| `XL_PASS` | Panel Basic-auth password. | `189810bdm` |
| `XL_API_PORT` | REST listen port for `serve`. | `8787` |
| `XL_API_KEY` | Shared secret for the REST front (checked against `X-API-KEY` header). Empty ⇒ auth off. | `""` |

Base URL resolution: `XL_URL` > `XL_HOST`/`XL_PORT`. If neither set:
`http://10.10.4.21:2345/webman/3rdparty/pan-xunlei-com/index.cgi`.

## CLI

```bash
# device readiness (prints {"ready": true, "about": {...}})
python3 xlmcp.py status

# recent download tasks
python3 xlmcp.py list --limit 20

# submit a download, wait until COMPLETE/ERROR (default deadline 600s)
python3 xlmcp.py add https://example.com/file.zip --name mypack

# fire-and-forget: return immediately with the task id
python3 xlmcp.py add https://example.com/file.zip --no-wait

# push the result JSON to a callback endpoint when the task reaches a terminal state
python3 xlmcp.py add https://example.com/file.zip --callback http://127.0.0.1:9911/done --deadline 300

# REST front (see below), bind address override:
python3 xlmcp.py serve --host 0.0.0.0

# MCP stdio server (see below)
python3 xlmcp.py --mcp

# help
python3 xlmcp.py help
```

`add` options: `--name NAME` (file/stem name; default = last URL path segment
minus query), `--callback URL`, `--deadline SEC` (default 600), `--no-wait`.

On success the CLI prints a compact summary — branch on `ok`:

```json
{
 "summary": {"id": "VP1v...", "name": "mypack", "phase": "PHASE_TYPE_COMPLETE",
             "ok": true, "message": "完成", "path": "/downloads/mypack", "size": "16958"},
 "task": {...full Thunder task object...}
}
```

With `--no-wait` only `{"summary": {"id": ..., "phase": "submitted"}}` is printed.

## REST API

Start the server: `python3 xlmcp.py serve` (binds `XL_API_PORT`, default 8787).
When `XL_API_KEY` is set, every request must carry `X-API-KEY: <key>`; empty
key means auth off (banner announces `auth=off` at startup).

### `GET /health`
Liveness + panel readiness.
```bash
curl -s http://127.0.0.1:8787/health
# {"ok": true, "ready": true, "about": {"kind": "drive#about", ...}}
```

### `GET /api/v1/tasks?limit=N`
List recent download tasks (Thunder `drive#task` objects). Invalid `limit`
falls back to 50 rather than dropping the connection.
```bash
curl -s 'http://127.0.0.1:8787/api/v1/tasks?limit=20'
```

### `GET /api/v1/tasks/{id}`
Fetch one task by id. Lookup scans the most recent listed window only — ids
are not durable once a task ages out. Returns `{}` when not found.
```bash
curl -s http://127.0.0.1:8787/api/v1/tasks/VP1vAoajw3cYB24N5bv5U8ydA1
```

### `POST /api/v1/tasks`
Submit a download. Blocks until COMPLETE/ERROR by default; returns
`{"summary": {...}, "task": {...}}`.

Body fields — `url` (required); optional `name`, `callback`, `deadline`
(seconds, default 600), `no_wait` (bool):
```bash
curl -s -X POST http://127.0.0.1:8787/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.baidu.com/favicon.ico","name":"probe"}'

# asynchronous: don't hold the HTTP connection — the summary JSON is POSTed
# to `callback` when the task finishes
curl -s -X POST http://127.0.0.1:8787/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://…/file.zip","callback":"http://collector:9911/done","deadline":900}'

# fire-and-forget
curl -s -X POST http://127.0.0.1:8787/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://…/file.zip","no_wait":true}'
```

Errors are JSON: `500 {"error": "…"}`, `502` on failed `/health` probe,
`401 {"error":"bad X-API-KEY"}` when the key is wrong, `404` on unknown routes.

### Completion reporting for agents
Two mechanisms, pick one:
1. **Sync** — keep the POST open; read `summary.ok` (`true` ⇔
   `phase == PHASE_TYPE_COMPLETE`) when it returns. Typical latency for a
   small file: ≈6 s.
2. **Async callback** — set `"callback":"http://…"`. The sidecar POSTs the
   summary JSON (`{id,name,phase,ok,message,path,size}`) to that URL once the
   task reaches a terminal state, best-effort (failures logged to stderr).
   On timeout the summary carries `"phase":"TIMEOUT"`.

### Running as a service
Example systemd unit:
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

## MCP server

Serve over stdio for any MCP-compatible agent host:

```json
{
  "mcpServers": {
    "xlmcp": { "command": "python3", "args": ["/root/xl-mcp/xlmcp.py", "--mcp"] }
  }
}
```

Implements `initialize`, `notifications/initialized`, `tools/list`,
`tools/call`, ping-style fallback. Three tools:

| Tool | Arguments | Behavior |
|---|---|---|
| `status` | — | Device readiness check. |
| `list_tasks` | `{limit?: int=50}` | Recent tasks. |
| `add_task` | `{url, name?, callback?, deadline?=600, no_wait?}` | Same semantics as REST POST: waits for COMPLETE/ERROR, returns `{summary, task}`; optional `callback` receives summary JSON via POST; `no_wait` returns `{summary:{id,phase:"submitted"}}`. |

Quick smoke test:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize"}' | python3 xlmcp.py --mcp
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python3 xlmcp.py --mcp
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"add_task","arguments":{"url":"https://www.baidu.com/favicon.ico","name":"mcp-probe"}}}' | python3 xlmcp.py --mcp
```

## Implementation notes

- **Token cache self-healing**: JWT/SynoToken are cached per process; if the
  panel rotates them (restart/redeploy), the next failing `api()` call drops
  the cache and re-fetches once — long-lived `serve` processes recover without
  a manual restart.
- **Task visibility lag**: the empty-space Thunder listing lags minutes behind
  new tasks; `task_by_id` therefore queries the runner-space-scoped listing
  first (`space=device_id#…`), then falls back to the empty-space one. This is
  what makes sync completion reports arrive in seconds instead of minutes.
- **`params.target` pitfall**: must be the runner's real `device_id` (read from
  a `user#runner` task's `params.target`). The literal `"downloads"` leaves
  tasks stuck in `PHASE_TYPE_PENDING` forever.
