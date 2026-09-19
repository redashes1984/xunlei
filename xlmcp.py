#!/usr/bin/env python3
"""xlmcp — headless bridge for the cnk3x/xunlei docker panel (no browser).

Verified chain (2026-09-20):
  1. Basic-auth GET /webman/login.cgi?enable_syno_token=yes  -> SynoToken JSON
  2. GET panel HTML -> embedded JWT ("eyJhbGciOiJIUzI1NiIs...")
  3. Call CGI paths DIRECTLY with headers: pan-auth + x-syno-token + Basic.
     (The device/v1/fetch proxy enforces a URL allowlist and rejects absolute
      URLs with "url not allowed" — bypass it, use relative CGI paths.)

Pitfall: params.target must be the runner's real device_id (read from a
user#runner task's params.target). The literal "downloads" leaves tasks
stuck in PHASE_TYPE_PENDING forever.

Env for the panel endpoint:
  XL_URL  full base URL (highest priority), e.g. http://myhost:18080/webman/3rdparty/pan-xunlei-com/index.cgi
  XL_HOST host only (default 10.10.4.21), XL_PORT port only (default 2345)
  XL_USER / XL_PASS Basic-auth credentials (defaults match cnk3x/xunlei compose)

CLI:
  python3 xlmcp.py status
  python3 xlmcp.py list [--limit N]
  python3 xlmcp.py add <url> [--name NAME] [--no-wait] [--callback URL] [--deadline SEC]
  python3 xlmcp.py remove [ID ...] [--keep-files]   # deletes task records (+downloaded files unless --keep-files); no ids = whole recent list
MCP stdio:
  python3 xlmcp.py --mcp    (tools: status, list_tasks, add_task, remove_task)
"""
import base64
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

def _base():
    """Panel base URL; override with XL_URL, or XL_HOST/XL_PORT for host and port."""
    v = os.environ.get("XL_URL")
    if v:
        return v.rstrip("/")
    host = os.environ.get("XL_HOST", "10.10.4.21")
    port = os.environ.get("XL_PORT", "2345")
    return "http://%s:%s/webman/3rdparty/pan-xunlei-com/index.cgi" % (host, port)


CGI = _base()
CRED = "%s:%s" % (
    os.environ.get("XL_USER", "bdm965"),
    os.environ.get("XL_PASS", "189810bdm"),
)
_BASIC = "Basic " + base64.b64encode(CRED.encode()).decode()

_cache = {}


def _get(url, timeout=25):
    req = urllib.request.Request(url, headers={"Authorization": _BASIC})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode()


def tokens():
    """(jwt, syno_token) — cached per process, refreshed on invalidation."""
    if "jwt" in _cache and "syn" in _cache:
        return _cache["jwt"], _cache["syn"]
    root = "/".join(CGI.split("/")[:3])
    login = json.loads(_get(root + "/webman/login.cgi?enable_syno_token=yes"))
    syn = login.get("SynoToken", "")
    html = _get(CGI + "/")
    m = re.search(r'"(eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)"', html)
    if not m:
        raise RuntimeError("JWT not found in panel HTML")
    _cache.update(jwt=m.group(1), syn=syn)
    return m.group(1), syn


def api(path, body=None, timeout=30, method=None):
    for attempt in (0, 1):
        jwt, syn = tokens()
        headers = {"pan-auth": jwt, "x-syno-token": syn, "Authorization": _BASIC}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            CGI + path, data=data, headers=headers,
            method=method or ("POST" if data is not None else "GET"))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read().decode())
                return d if isinstance(d, dict) else {}
        except Exception:
            # Panel restart rotates its embedded JWT: drop the cached token
            # once so a long-lived serve process self-heals without restart.
            if attempt == 0 and _cache.get("jwt"):
                _cache.pop("jwt", None)
                _cache.pop("syn", None)
                continue
            raise


def qs(d):
    return "&".join("%s=%s" % (k, urllib.parse.quote(str(v))) for k, v in d.items())


def runner_space():
    """params.target of the live runner task — correct value for task target."""
    if "sp" in _cache:
        return _cache["sp"]
    f = json.dumps({"type": {"in": "user#runner"}})
    d = api("/drive/v1/tasks?limit=1&space=&filters=" + urllib.parse.quote(f))
    for t in d.get("tasks", []):
        tgt = t.get("params", {}).get("target", "")
        if tgt:
            _cache["sp"] = tgt
            return tgt
    return "downloads"


def list_tasks(limit=50):
    return api("/drive/v1/tasks?" + qs({"limit": limit, "space": ""}))


def task_by_id(tid):
    # Space-scoped listing shows fresh tasks immediately; empty-space listing
    # lags behind (~new tasks missing for minutes), so query both.
    sp = runner_space()
    for path in (
        "/drive/v1/tasks?" + qs({"limit": 20, "space": sp}),
        "/drive/v1/tasks?" + qs({"limit": 20, "space": ""}),
    ):
        d = api(path)
        for t in d.get("tasks", []):
            if t.get("id") == tid:
                return t
    return {}


def status():
    d = api("/drive/v1/about?" + qs({"space": ""}))
    ok = d.get("kind") == "drive#about"
    return {"ready": ok, "about": d}


def remove_tasks(ids):
    """Delete task records — panel's own shape (verified live on the bundle):
    DELETE drive/v1/tasks?space=<runner>&task_ids=<id>[&task_ids=<id>]"""
    if isinstance(ids, str):
        ids = [ids]
    sp = runner_space()
    q = "&".join("task_ids=" + urllib.parse.quote(str(i)) for i in ids if i)
    return api("/drive/v1/tasks?space=%s&%s" % (urllib.parse.quote(sp), q),
               method="DELETE")


def _artifact_root():
    return os.environ.get("XL_DOWNLOAD_DIR", "/xunlei/downloads")


def cleanup(ids=None, with_files=True, limit=50):
    """Remove task records and optionally their downloaded artifacts.

    Completed tasks usually have params.real_path ("/downloads/<name>");
    pending/error ones often have none — their record alone is removed.
    Returns the per-task summaries that were processed."""
    if ids:
        done = []
        for tid in ids:
            t = task_by_id(tid)
            if t:
                done.append(t)
    else:
        done = list_tasks(limit).get("tasks", [])
    removed = []
    for t in done:
        s = summary(t)
        try:
            if with_files and s.get("path"):
                rel = s["path"]
                rel = rel[len("/downloads/"):] if rel.startswith("/downloads/") else rel.lstrip("/")
                # normalize: drop empty/"." segments, reject ".." traversal
                parts = [p for p in rel.split("/") if p not in ("", ".", "..")]
                full = os.path.join(_artifact_root(), *parts) if parts else None
                if full:
                    try:
                        if os.path.isdir(full):
                            import shutil
                            shutil.rmtree(full)
                        elif os.path.exists(full):
                            os.remove(full)
                    except Exception as e:
                        print("artifact delete skipped:", full, e, file=sys.stderr)
            remove_tasks([s["id"]])
            removed.append(s)
        except Exception as e:
            print("remove failed for", s.get("id"), ":", e, file=sys.stderr)
    return removed


def add_task(url, name=None):
    space = runner_space()
    stem = name or re.sub(r"[?#].*$", "", url.split("/")[-1]) or "download"
    body = {
        "type": "user#download-url",
        "name": stem,
        "file_name": stem,
        "file_size": "0",
        "space": space,
        "params": {"target": space, "url": url},
    }
    return api("/drive/v1/task", body=body)


def wait_task(tid, deadline=600):
    end = time.time() + deadline
    last = {}
    while time.time() < end:
        last = task_by_id(tid) or last
        phase = last.get("phase")
        if phase in ("PHASE_TYPE_COMPLETE", "PHASE_TYPE_ERROR"):
            return last
        time.sleep(2)
    return {**last, "id": tid, "phase": last.get("phase") or "TIMEOUT"}


def summary(t):
    """Compact agent-friendly result: branch on t['ok']."""
    p = t.get("params", {}) or {}
    phase = t.get("phase") or ""
    return {
        "id": t.get("id"),
        "name": t.get("name"),
        "phase": phase,
        "ok": phase == "PHASE_TYPE_COMPLETE",
        "message": t.get("message"),
        "path": p.get("real_path"),
        "size": t.get("file_size"),
    }


def notify(url, obj, timeout=15):
    """Best-effort completion callback so agents proceed without polling."""
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(obj, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read()
    except Exception as e:
        print("callback failed:", e, file=sys.stderr)


# ---- MCP stdio server ----------------------------------------------------

def mcp_server():
    def send(msg):
        msg.setdefault("jsonrpc", "2.0")
        sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            req = json.loads(line)
        except Exception:
            continue
        if not isinstance(req, dict):
            continue
        rid = req.get("id")
        method = req.get("method")
        if method == "initialize":
            send({"id": rid, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "xlmcp", "version": "1.0"},
            }})
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            send({"id": rid, "result": {"tools": [
                {"name": "status", "inputSchema": {"type": "object"},
                 "description": "Check Thunder remote-download device readiness."},
                {"name": "list_tasks", "inputSchema": {
                    "type": "object",
                    "properties": {"limit": {"type": "integer", "default": 50}}},
                 "description": "List recent download tasks (JSON)."},
                {"name": "add_task", "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "name": {"type": "string"},
                        "callback": {"type": "string"},
                        "deadline": {"type": "integer", "default": 600},
                        "no_wait": {"type": "boolean"}},
                    "required": ["url"]},
                 "description": "Submit a download URL; waits until COMPLETE/ERROR by default, returns {summary:{ok,phase,path,...}}; optional callback URL receives the same JSON via POST when done."},
                {"name": "remove_task", "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ids": {"type": "array", "items": {"type": "string"},
                                "description": "Task ids to delete; omit or pass [] to clean the whole recent listing."},
                        "keep_files": {"type": "boolean", "default": False},
                        "limit": {"type": "integer", "default": 50}},
                    },
                 "description": "Delete task records; keep_files=false (default) also removes downloaded artifacts. ids=[] equals omitted ids: cleans recent listing up to `limit`."},
            ]}})
        elif method == "tools/call":
            name = req.get("params", {}).get("name")
            args = req.get("params", {}).get("arguments", {}) or {}
            try:
                if name == "status":
                    out = status()
                elif name == "list_tasks":
                    out = list_tasks(int(args.get("limit", 50)))
                elif name == "add_task":
                    r = add_task(args.get("url", ""), args.get("name"))
                    tid = r.get("task", {}).get("id")
                    if tid and args.get("no_wait"):
                        out = {"summary": {"id": tid, "phase": "submitted"}}
                    elif tid:
                        done = wait_task(tid, deadline=int(args.get("deadline", 600)))
                        s = summary(done)
                        if args.get("callback"):
                            notify(args["callback"], s)
                        out = {"summary": s, "task": done}
                    else:
                        out = r
                elif name == "remove_task":
                    out = {"removed": cleanup(
                        ids=args.get("ids") or None,
                        with_files=not args.get("keep_files", False),
                        limit=int(args.get("limit", 50)))}
                else:
                    out = {"error": "unknown tool"}
            except Exception as e:
                out = {"error": str(e)}
            send({"id": rid, "result": {"content": [
                {"type": "text", "text": json.dumps(out, ensure_ascii=False)}]}})
        elif rid is not None:
            send({"id": rid, "result": {}})
    return 0


# ---- REST server (Komga-style) ---------------------------------------------

def serve(host="0.0.0.0", port=None):
    """Lightweight JSON REST front: /health, /api/v1/tasks[/{id}], POST /api/v1/tasks."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    port = int(port or os.environ.get("XL_API_PORT", "8787"))
    api_key = os.environ.get("XL_API_KEY", "")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _json(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _authed(self):
            if not api_key:
                return True
            return self.headers.get("X-API-KEY", "") == api_key

        def do_GET(self):
            if not self._authed():
                return self._json(401, {"error": "bad X-API-KEY"})
            qs = urllib.parse.urlparse(self.path)
            if qs.path == "/health":
                try:
                    return self._json(200, {"ok": True, **status()})
                except Exception as e:
                    return self._json(502, {"ok": False, "error": str(e)})
            if qs.path == "/api/v1/tasks":
                try:
                    limit = int((urllib.parse.parse_qs(qs.query).get("limit") or ["50"])[0])
                except ValueError:
                    limit = 50
                try:
                    return self._json(200, list_tasks(limit))
                except Exception as e:
                    return self._json(500, {"error": str(e)})
            m = re.match(r"^/api/v1/tasks/([^/]+)$", qs.path)
            if m:
                try:
                    return self._json(200, task_by_id(m.group(1)))
                except Exception as e:
                    return self._json(500, {"error": str(e)})
            return self._json(404, {"error": "not found", "routes": [
                "/health", "/api/v1/tasks", "/api/v1/tasks/{id}", "POST /api/v1/tasks"]})

        def do_DELETE(self):
            if not self._authed():
                return self._json(401, {"error": "bad X-API-KEY"})
            q = urllib.parse.urlparse(self.path)
            if q.path == "/api/v1/tasks":
                pq = urllib.parse.parse_qs(q.query)
                try:
                    limit = int((pq.get("limit") or ["50"])[0])
                except ValueError:
                    limit = 50
                keep = (pq.get("keep_files") or ["0"])[0] != "1"
                try:
                    out = cleanup(limit=limit, with_files=keep)
                    return self._json(200, {"removed": out})
                except Exception as e:
                    return self._json(500, {"error": str(e)})
            m = re.match(r"^/api/v1/tasks/([^/]+)$", q.path)
            if m:
                keep = (urllib.parse.parse_qs(q.query).get("keep_files") or ["0"])[0] != "1"
                try:
                    out = cleanup(ids=[m.group(1)], with_files=keep)
                    return self._json(200, {"removed": out})
                except Exception as e:
                    return self._json(500, {"error": str(e)})
            return self._json(404, {"error": "not found"})

        def do_POST(self):
            if not self._authed():
                return self._json(401, {"error": "bad X-API-KEY"})
            if urllib.parse.urlparse(self.path).path != "/api/v1/tasks":
                return self._json(404, {"error": "not found"})
            try:
                n = int(self.headers.get("Content-Length", 0))
                args = json.loads(self.rfile.read(n) or b"{}")
                r = add_task(args.get("url", ""), args.get("name"))
                tid = r.get("task", {}).get("id")
                if tid and args.get("no_wait"):
                    return self._json(200, {"summary": {"id": tid, "phase": "submitted"}})
                if tid:
                    done = wait_task(tid, deadline=int(args.get("deadline", 600)))
                    s = summary(done)
                    cb = args.get("callback")
                    if cb:
                        notify(cb, s)
                    return self._json(200, {"summary": s, "task": done})
                return self._json(200, r)
            except Exception as e:
                return self._json(500, {"error": str(e)})

    srv = ThreadingHTTPServer((host, port), Handler)
    print("xlmcp REST on http://%s:%d  (auth=%s)" % (host, port, "off" if not api_key else "on"))
    srv.serve_forever()
    return 0


# ---- CLI ------------------------------------------------------------------

def cli(argv):
    if argv and argv[0] == "--mcp":
        return mcp_server()
    if not argv or argv[0] in ("help", "-h", "--help"):
        print(__doc__)
        return 0
    cmd = argv[0]
    rest = argv[1:]
    if cmd == "serve":
        host = rest[rest.index("--host") + 1] if "--host" in rest else "0.0.0.0"
        return serve(host)
    if cmd == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=1))
    elif cmd == "list":
        limit = int(rest[rest.index("--limit") + 1]) if "--limit" in rest else 50
        print(json.dumps(list_tasks(limit), ensure_ascii=False, indent=1))
    elif cmd == "add":
        opts = {}
        pos = []
        i = 0
        while i < len(rest):
            if rest[i] == "--name" and i + 1 < len(rest):
                opts["name"] = rest[i + 1]; i += 2
            elif rest[i] == "--callback" and i + 1 < len(rest):
                opts["callback"] = rest[i + 1]; i += 2
            elif rest[i] == "--deadline" and i + 1 < len(rest):
                opts["deadline"] = int(rest[i + 1]); i += 2
            elif rest[i] == "--no-wait":
                opts["no_wait"] = True; i += 1
            else:
                pos.append(rest[i]); i += 1
        if not pos:
            print("usage: add <url> [--name NAME] [--callback URL] [--deadline SEC] [--no-wait]")
            return 1
        r = add_task(pos[0], opts.get("name"))
        tid = r.get("task", {}).get("id")
        if not tid:
            print(json.dumps(r, ensure_ascii=False))
            return 1
        if opts.get("no_wait"):
            print(json.dumps({"summary": {"id": tid, "phase": "submitted"}}, ensure_ascii=False))
            return 0
        done = wait_task(tid, deadline=opts.get("deadline", 600))
        s = summary(done)
        if opts.get("callback"):
            notify(opts["callback"], s)
        print(json.dumps({"summary": s, "task": done}, ensure_ascii=False, indent=1))
    elif cmd == "remove":
        keep = "--keep-files" in rest
        lim = 50
        if "--limit" in rest:
            try:
                lim = int(rest[rest.index("--limit") + 1])
            except (IndexError, ValueError):
                pass
        ids = [a for a in rest if not a.startswith("--") and a != str(lim)]
        if ids:
            out = cleanup(ids=ids, with_files=not keep)
        else:
            out = cleanup(with_files=not keep, limit=lim)
        print(json.dumps({"removed": out}, ensure_ascii=False, indent=1))
    else:
        print("unknown command:", cmd)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(cli(sys.argv[1:]))
