---
name: xunlei-agentic
description: Use when submitting or managing Thunder (迅雷) remote-download tasks headlessly — CLI, REST, or MCP. Covers task submit/wait/callback, listing, and cleanup of records + artifacts.
---

# Xunlei Agentic — Headless Thunder Download Skill

Drives the `cnk3x/xunlei` Docker panel (迅雷远程下载) without any browser.
The sidecar `xlmcp.py` speaks three surfaces: CLI, REST (`:8787`), MCP stdio.
Pick whichever your host supports; semantics are identical across surfaces.

## When to use
- A task requires downloading a file via Thunder (comic zips, movies, assets).
- You need to check whether a download finished, read its landing path, or clean up the queue afterwards.
- Browser automation of the Xunlei panel is too slow or blocked by dialogs/captcha-style flows.

## Connection facts
- Panel: `http://<host>:2345` (default `10.10.4.21:2345`).
- Sidecar REST: `http://<host>:8787`, header `X-API-KEY: *** set.
- Auth chain (already handled inside the sidecar; only reproduce manually if it is down): Basic `GET /webman/login.cgi?enable_syno_token=yes` → `SynoToken`; GET panel HTML → embedded JWT `eyJ…`; then call CGI paths with headers `pan-auth: <jwt>` + `x-syno-token` + Basic. `device/v1/fetch` whitelists URLs ("url not allowed") — bypass it, use relative CGI paths directly.
- Downloads land in `/mnt/user/Downloads/Xunlei/` (= container `/xunlei/downloads`).

## Environment variables
| Var | Meaning | Default |
|---|---|---|
| `XL_URL` | Full panel base URL (highest priority) | — |
| `XL_HOST` / `XL_PORT` | Host/port when `XL_URL` unset | `10.10.4.21` / `2345` |
| `XL_USER` / `XL_PASS` | Panel Basic auth | bdm965 (see CREDENTIALS.md) |
| `XL_API_PORT` | REST listen port | `8787` |
| `XL_API_KEY` | REST shared secret, empty = auth off | `""` |

Never hardcode host/key in scripts — read env, fall back to these defaults.

## Core workflow (the one thing you need)
Submit → wait for terminal state → read `summary.ok`:

```bash
# CLI (blocking, small file ≈ 6 s)
python3 xlmcp.py add https://example.com/file.zip --name mypack

# REST
curl -s -X POST http://10.10.4.21:8787/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/file.zip","name":"mypack"}'
# → {"summary":{"id","name","phase","ok","message","path","size"},"task":{...}}
```

- `summary.ok == true` ⇔ `phase == PHASE_TYPE_COMPLETE`. Branch on `ok`, not on the message string.
- Long downloads: add `"callback":"http://collector:9911/done"` (+ `"deadline":900`) so the summary JSON is POSTed when done and the HTTP call returns immediately.
- Fire-and-forget: `"no_wait":true` returns only `{summary:{id,phase:"submitted"}}`.

## Manage the queue
```bash
python3 xlmcp.py status                     # readiness
python3 xlmcp.py list --limit 20            # recent tasks
python3 xlmcp.py remove ID... [--keep-files] [--limit N]   # record + artifact cleanup
curl -s -X DELETE 'http://10.10.4.21:8787/api/v1/tasks?limit=5&keep_files=1'
```
- `remove` deletes the task record AND its downloaded artifact (resolved from `params.real_path` under the download dir). Without `real_path` (pending/error tasks) only the record goes. `--keep-files` / `?keep_files=1` keeps files.
- MCP equivalent: tool `remove_task {ids?, keep_files?, limit?=50}`; omit `ids` to clean the recent window.

## Pitfalls (learned in production)
- **`params.target` must be the runner's real device_id** (`device_id#<hex>`, read from a `user#runner` task). The literal `"downloads"` strands tasks in PHASE_TYPE_PENDING forever.
- **Empty-space listing lags minutes** behind fresh tasks; query the runner-space-scoped listing first, fall back to empty-space. This is why sync reports arrive in seconds.
- **Deadline ≥600 s.** A 300 s budget returned TIMEOUT for a file that actually landed. On timeout return the last snapshot merged with id/phase, never a bare TIMEOUT stub.
- **URLs with non-ASCII titles**: keep the complete `?n=<percent-encoded title>` suffix; raw Unicode tails stall Thunder at 0B.
- **Panel restart rotates its JWT**: the sidecar drops its token cache and refetches once on failure — long-lived `serve` processes self-heal; restart them only if health stays broken.
- **Stale digest after image repush**: the running Unraid container keeps the old pulled digest; compare `docker inspect` Image digest vs Hub manifest, Force update / recreate to roll new code. Data volumes and login survive recreate.
- **Unraid host can't reach Docker Hub** (`registry-1.docker.io` EOF, proxy included): transfer images via `docker save` → scp → `docker load` from a machine that has them.
- **After editing xlmcp.py**: `pkill -f "xlmcp.py serve"` before restarting, else "Address already in use" on the stale port.
- Inline for-loops with quoted JSON get mangled by shell eval — write a small /tmp bash/python script for multi-round polling instead.

## Verify deployments honestly
Every change must pass a live round-trip: `status` ready → POST a probe (e.g. `https://www.baidu.com/favicon.ico`, ~17 KB) → `summary.ok == true` with a `path` under `/downloads/` → `remove` it → confirm gone from `list`. A successful push exit code is not proof; read back (`gh api repos/<fork>/commits/main --jq .sha`).
