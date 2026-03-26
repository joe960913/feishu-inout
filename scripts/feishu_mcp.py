#!/usr/bin/env python3
"""Feishu Remote MCP Client - calls https://mcp.feishu.cn/mcp via JSON-RPC 2.0
Supports both TAT (app identity) and UAT (user identity) authentication."""

import json, os, sys, urllib.request, urllib.error, webbrowser, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

MCP_URL = "https://mcp.feishu.cn/mcp"
TAT_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
APP_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
UAT_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token"
REFRESH_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/refresh_access_token"
AUTH_URL = "https://open.feishu.cn/open-apis/authen/v1/authorize"
REDIRECT_URI = "http://localhost:9876/callback"
TOKEN_FILE = os.path.expanduser("~/.claude/skills/feishu-inout/.uat_token.json")
ALL_TOOLS = "fetch-doc,search-doc,list-docs,create-doc,update-doc,get-comments,add-comments,search-user,get-user,fetch-file"


def get_app_id_secret():
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        print("Error: set FEISHU_APP_ID and FEISHU_APP_SECRET env vars", file=sys.stderr)
        sys.exit(1)
    return app_id, app_secret


def get_tat():
    app_id, app_secret = get_app_id_secret()
    req = urllib.request.Request(
        TAT_URL,
        data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    if data.get("code") != 0:
        print(f"TAT error: {data.get('msg')}", file=sys.stderr)
        sys.exit(1)
    return data["tenant_access_token"]


def get_app_access_token():
    app_id, app_secret = get_app_id_secret()
    req = urllib.request.Request(
        APP_TOKEN_URL,
        data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    if data.get("code") != 0:
        print(f"App token error: {data.get('msg')}", file=sys.stderr)
        sys.exit(1)
    return data["app_access_token"]


def save_uat(token_data):
    token_data["saved_at"] = int(time.time())
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)


def load_uat():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        data = json.load(f)
    saved_at = data.get("saved_at", 0)
    expires_in = data.get("expires_in", 7200)
    if time.time() - saved_at > expires_in - 300:
        # Token expired or about to expire, try refresh
        refresh_token = data.get("refresh_token")
        if refresh_token:
            refreshed = refresh_uat(refresh_token)
            if refreshed:
                return refreshed
        return None
    return data


def refresh_uat(refresh_token):
    try:
        app_token = get_app_access_token()
        req = urllib.request.Request(
            REFRESH_URL,
            data=json.dumps({
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }).encode(),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {app_token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        if data.get("code") == 0:
            token_data = data["data"]
            save_uat(token_data)
            return token_data
    except Exception as e:
        print(f"Refresh failed: {e}", file=sys.stderr)
    return None


def exchange_code_for_uat(code):
    app_token = get_app_access_token()
    req = urllib.request.Request(
        UAT_URL,
        data=json.dumps({
            "grant_type": "authorization_code",
            "code": code,
        }).encode(),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {app_token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    if data.get("code") != 0:
        print(f"UAT exchange error: {data.get('msg')}", file=sys.stderr)
        return None
    return data["data"]


def oauth_login():
    """Start OAuth2 flow: open browser, catch callback, exchange for UAT."""
    app_id, _ = get_app_id_secret()
    scopes = "docx:document:readonly search:docs:read wiki:wiki:readonly im:chat:read task:task:read docx:document docx:document:create docx:document:write_only docs:document.media:upload docs:document.media:download wiki:node:read wiki:node:create docs:document.comment:read docs:document.comment:create contact:user:search contact:contact.base:readonly contact:user.base:readonly board:whiteboard:node:read drive:drive"
    auth_url = f"{AUTH_URL}?app_id={app_id}&redirect_uri={REDIRECT_URI}&state=feishu_inout&scope={scopes}"

    captured = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = parse_qs(urlparse(self.path).query)
            code = query.get("code", [None])[0]
            if code:
                captured["code"] = code
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("授权成功！可以关闭此页面了。".encode())
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"No code received")

        def log_message(self, format, *args):
            pass  # Suppress logs

    server = HTTPServer(("localhost", 9876), CallbackHandler)
    print(f"Opening browser for authorization...")
    webbrowser.open(auth_url)
    print("Waiting for callback on http://localhost:9876/callback ...")

    server.handle_request()  # Handle one request then stop

    code = captured.get("code")
    if not code:
        print("No authorization code received.", file=sys.stderr)
        sys.exit(1)

    print("Got authorization code, exchanging for UAT...")
    token_data = exchange_code_for_uat(code)
    if not token_data:
        print("Failed to get UAT.", file=sys.stderr)
        sys.exit(1)

    save_uat(token_data)
    print(f"UAT saved! User: {token_data.get('name', 'unknown')}")
    print(f"Expires in: {token_data.get('expires_in', '?')} seconds")
    print(f"Token file: {TOKEN_FILE}")


def get_best_token():
    """Return (token_value, token_type). Prefer UAT if available."""
    uat_data = load_uat()
    if uat_data and uat_data.get("access_token"):
        return uat_data["access_token"], "UAT"
    return get_tat(), "TAT"


def mcp_call(token, token_type, method, params=None):
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params:
        body["params"] = params
    header_key = "X-Lark-MCP-UAT" if token_type == "UAT" else "X-Lark-MCP-TAT"
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            header_key: token,
            "X-Lark-MCP-Allowed-Tools": ALL_TOOLS,
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def call_tool(token, token_type, tool_name, arguments):
    return mcp_call(token, token_type, "tools/call", {"name": tool_name, "arguments": arguments})


def main():
    if len(sys.argv) < 2:
        print("Usage: feishu_mcp.py <command> [args]")
        print()
        print("Auth:")
        print("  login                                OAuth2 login to get UAT")
        print("  whoami                               Show current token status")
        print()
        print("Documents:")
        print("  fetch-doc <docID> [offset] [limit]   Read document (supports pagination)")
        print("  search-doc <keyword>                 Search documents (needs UAT)")
        print("  list-docs [docID]                    List wiki docs (omit docID for My Library)")
        print("  create-doc <title> '<markdown>' [location_json]  Create doc with content")
        print("  append <docID> '<markdown>'           Append content to document")
        print("  overwrite <docID> '<markdown>'        Overwrite entire document")
        print("  replace <docID> '<selection>' '<markdown>'  Replace matched range")
        print("  insert-after <docID> '<selection>' '<markdown>'  Insert after match")
        print("  insert-before <docID> '<selection>' '<markdown>' Insert before match")
        print("  delete-range <docID> '<selection>'    Delete matched content")
        print()
        print("Comments:")
        print("  get-comments <docID> [all|whole|segment]  Get comments (default: all)")
        print("  add-comments <docID> <text>           Add a text comment")
        print()
        print("Users:")
        print("  get-user [open_id]                   Get user info (self if no ID)")
        print("  search-user <keyword>                Search users by name")
        print()
        print("Files:")
        print("  fetch-file <token> [media|whiteboard] Get file/image content")
        print()
        print("Advanced:")
        print("  tools                                List all available MCP tools")
        print("  call <tool> '<json_args>'            Call any tool with raw JSON")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "login":
        oauth_login()
        return

    if cmd == "whoami":
        uat_data = load_uat()
        if uat_data:
            print(f"UAT active: {uat_data.get('name', '?')} (expires_in: {uat_data.get('expires_in', '?')}s)")
        else:
            print("No UAT. Using TAT (app identity). Run 'login' to get UAT.")
        return

    token, token_type = get_best_token()
    print(f"[Using {token_type}]", file=sys.stderr)

    # Always initialize first
    mcp_call(token, token_type, "initialize")

    p = lambda d: print(json.dumps(d, ensure_ascii=False, indent=2))

    if cmd == "init":
        p(mcp_call(token, token_type, "initialize"))

    elif cmd == "tools":
        p(mcp_call(token, token_type, "tools/list"))

    # --- Documents ---
    elif cmd == "fetch-doc":
        args = {"doc_id": sys.argv[2]}
        if len(sys.argv) >= 4:
            args["offset"] = int(sys.argv[3])
        if len(sys.argv) >= 5:
            args["limit"] = int(sys.argv[4])
        p(call_tool(token, token_type, "fetch-doc", args))

    elif cmd == "search-doc":
        args = {"query": sys.argv[2]} if len(sys.argv) >= 3 else {}
        p(call_tool(token, token_type, "search-doc", args))

    elif cmd == "list-docs":
        if len(sys.argv) >= 3:
            args = {"doc_id": sys.argv[2]}
        else:
            args = {"my_library": True}
        p(call_tool(token, token_type, "list-docs", args))

    elif cmd == "create-doc":
        args = {"title": sys.argv[2]}
        if len(sys.argv) >= 4:
            args["markdown"] = sys.argv[3]
        if len(sys.argv) >= 5:
            args.update(json.loads(sys.argv[4]))
        p(call_tool(token, token_type, "create-doc", args))

    # --- Update modes ---
    elif cmd == "append":
        p(call_tool(token, token_type, "update-doc", {
            "doc_id": sys.argv[2], "mode": "append", "markdown": sys.argv[3]
        }))

    elif cmd == "overwrite":
        p(call_tool(token, token_type, "update-doc", {
            "doc_id": sys.argv[2], "mode": "overwrite", "markdown": sys.argv[3]
        }))

    elif cmd == "replace":
        p(call_tool(token, token_type, "update-doc", {
            "doc_id": sys.argv[2], "mode": "replace_range",
            "selection_with_ellipsis": sys.argv[3], "markdown": sys.argv[4]
        }))

    elif cmd == "insert-after":
        p(call_tool(token, token_type, "update-doc", {
            "doc_id": sys.argv[2], "mode": "insert_after",
            "selection_with_ellipsis": sys.argv[3], "markdown": sys.argv[4]
        }))

    elif cmd == "insert-before":
        p(call_tool(token, token_type, "update-doc", {
            "doc_id": sys.argv[2], "mode": "insert_before",
            "selection_with_ellipsis": sys.argv[3], "markdown": sys.argv[4]
        }))

    elif cmd == "delete-range":
        p(call_tool(token, token_type, "update-doc", {
            "doc_id": sys.argv[2], "mode": "delete_range",
            "selection_with_ellipsis": sys.argv[3]
        }))

    # update-doc with raw JSON (backwards compat + full control)
    elif cmd == "update-doc":
        p(call_tool(token, token_type, "update-doc", json.loads(sys.argv[2])))

    # --- Comments ---
    elif cmd == "get-comments":
        args = {"doc_id": sys.argv[2]}
        if len(sys.argv) >= 4:
            args["comment_type"] = sys.argv[3]
        p(call_tool(token, token_type, "get-comments", args))

    elif cmd == "add-comments":
        p(call_tool(token, token_type, "add-comments", {
            "doc_id": sys.argv[2],
            "elements": [{"type": "text", "text": sys.argv[3]}]
        }))

    # --- Users ---
    elif cmd == "get-user":
        args = {"open_id": sys.argv[2]} if len(sys.argv) >= 3 else {}
        p(call_tool(token, token_type, "get-user", args))

    elif cmd == "search-user":
        p(call_tool(token, token_type, "search-user", {"query": sys.argv[2]}))

    # --- Files ---
    elif cmd == "fetch-file":
        args = {"resource_token": sys.argv[2]}
        if len(sys.argv) >= 4:
            args["type"] = sys.argv[3]
        p(call_tool(token, token_type, "fetch-file", args))

    # --- Raw call ---
    elif cmd == "call":
        p(call_tool(token, token_type, sys.argv[2], json.loads(sys.argv[3])))

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
