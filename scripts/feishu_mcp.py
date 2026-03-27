#!/usr/bin/env python3
"""Feishu Remote MCP Client - calls https://mcp.feishu.cn/mcp via JSON-RPC 2.0
Supports both TAT (app identity) and UAT (user identity) authentication."""

import json, os, sys, urllib.request, urllib.error, webbrowser, time, re
from datetime import datetime, timezone, timedelta
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
ALL_TOOLS = "fetch-doc,search-doc,list-docs,create-doc,update-doc,get-comments,add-comments,search-user,get-user,fetch-file,send-message,get-messages,get-thread-messages,search-messages"


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
    scopes = "docx:document:readonly search:docs:read wiki:wiki:readonly im:chat:read task:task:read docx:document docx:document:create docx:document:write_only docs:document.media:upload docs:document.media:download wiki:node:read wiki:node:create docs:document.comment:read docs:document.comment:create contact:user:search contact:contact.base:readonly contact:user.base:readonly board:whiteboard:node:read drive:drive im:message:send_as_bot im:message im:chat search:message im:message.send_as_user im:message.p2p_msg:get_as_user im:message.group_msg:get_as_user calendar:calendar:readonly calendar:calendar bitable:app:readonly bitable:app im:chat:create"
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


# --- Feishu Open API (for messaging, not MCP) ---

OPEN_API = "https://open.feishu.cn/open-apis"


def api_call(endpoint, data=None, method="POST", token=None):
    """Call Feishu Open API directly. Uses TAT by default."""
    if not token:
        token = get_tat()
    url = f"{OPEN_API}/{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def get_uat_token():
    """Load UAT access_token or exit with error."""
    uat_data = load_uat()
    if not uat_data or not uat_data.get("access_token"):
        print("Error: UAT required. Run 'login' first.", file=sys.stderr)
        sys.exit(1)
    return uat_data["access_token"]


def parse_timestamp(value):
    """Parse a time string to unix timestamp string.

    Accepts:
    - Unix timestamp (digits only)
    - ISO 8601: "2026-03-27T14:00:00+08:00" or "2026-03-27T14:00"
    - Date only: "2026-03-27" (returns 00:00 in local timezone)
    - "today" (returns 00:00 today in local timezone)
    """
    if value is None:
        return None
    value = value.strip()
    if value.isdigit():
        return value
    # "today" keyword
    if value.lower() == "today":
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return str(int(start.timestamp()))
    # Date only: "2026-03-27"
    if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        dt = datetime.strptime(value, "%Y-%m-%d")
        return str(int(dt.timestamp()))
    # ISO 8601 with timezone: "2026-03-27T14:00:00+08:00"
    # Try various ISO formats
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            dt = datetime.strptime(value, fmt)
            return str(int(dt.timestamp()))
        except ValueError:
            continue
    # Last resort: try parsing with fromisoformat (Python 3.7+)
    try:
        dt = datetime.fromisoformat(value)
        return str(int(dt.timestamp()))
    except (ValueError, AttributeError):
        pass
    print(f"Error: cannot parse timestamp '{value}'", file=sys.stderr)
    sys.exit(1)


def parse_date_range(date_str):
    """Parse a date string to (start_ts, end_ts) unix timestamp strings for a full day."""
    if date_str is None or date_str.lower() == "today":
        now = datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        start = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        print(f"Error: invalid date '{date_str}'. Use YYYY-MM-DD or 'today'.", file=sys.stderr)
        sys.exit(1)
    end = start.replace(hour=23, minute=59, second=59)
    return str(int(start.timestamp())), str(int(end.timestamp()))


def get_primary_calendar_id(uat):
    """Get the primary calendar ID for the current user."""
    resp = api_call("calendar/v4/calendars/primary", method="GET", token=uat)
    if resp.get("code") != 0:
        print(f"Error getting primary calendar: {resp.get('msg', resp)}", file=sys.stderr)
        sys.exit(1)
    data = resp["data"]
    # Handle both formats: direct calendar_id or calendars array
    if "calendar_id" in data:
        return data["calendar_id"]
    return data["calendars"][0]["calendar"]["calendar_id"]


# --- Calendar / Meeting ---

def cmd_create_event(args):
    """create-event <title> <start> <end> [attendees_json]"""
    if len(args) < 3:
        print("Usage: create-event <title> <start_time> <end_time> [attendees_json]", file=sys.stderr)
        sys.exit(1)
    title = args[0]
    start_ts = parse_timestamp(args[1])
    end_ts = parse_timestamp(args[2])
    attendees_json = args[3] if len(args) >= 4 else None

    uat = get_uat_token()
    calendar_id = get_primary_calendar_id(uat)

    event_body = {
        "summary": title,
        "start_time": {"timestamp": start_ts},
        "end_time": {"timestamp": end_ts},
        "vchat": {"vc_type": "vc"},
    }
    resp = api_call(f"calendar/v4/calendars/{calendar_id}/events", data=event_body, token=uat)
    if resp.get("code") != 0:
        print(f"Error creating event: {resp.get('msg', resp)}", file=sys.stderr)
        return resp

    event = resp.get("data", {}).get("event", {})
    event_id = event.get("event_id")
    print(f"Event created: {event_id}", file=sys.stderr)

    # Add attendees if provided
    if attendees_json and event_id:
        try:
            attendee_ids = json.loads(attendees_json)
            attendees = [{"type": "user", "user_id": uid} for uid in attendee_ids]
            att_resp = api_call(
                f"calendar/v4/calendars/{calendar_id}/events/{event_id}/attendees?user_id_type=open_id",
                data={"attendees": attendees},
                token=uat,
            )
            if att_resp.get("code") != 0:
                print(f"Warning: failed to add attendees: {att_resp.get('msg', att_resp)}", file=sys.stderr)
            else:
                print(f"Added {len(attendee_ids)} attendee(s)", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"Warning: invalid attendees JSON: {attendees_json}", file=sys.stderr)

    return resp


def cmd_list_events(args):
    """list-events [date]"""
    date_str = args[0] if len(args) >= 1 else "today"
    start_ts, end_ts = parse_date_range(date_str)

    uat = get_uat_token()
    calendar_id = get_primary_calendar_id(uat)

    resp = api_call(
        f"calendar/v4/calendars/{calendar_id}/events?start_time={start_ts}&end_time={end_ts}",
        method="GET",
        token=uat,
    )
    return resp


# --- Bitable (Multi-dimensional Table) ---

def cmd_list_tables(args):
    """list-tables <app_token>"""
    if len(args) < 1:
        print("Usage: list-tables <app_token>", file=sys.stderr)
        sys.exit(1)
    app_token = args[0]
    uat = get_uat_token()
    return api_call(f"bitable/v1/apps/{app_token}/tables", method="GET", token=uat)


def cmd_list_records(args):
    """list-records <app_token> <table_id> [page_size]"""
    if len(args) < 2:
        print("Usage: list-records <app_token> <table_id> [page_size]", file=sys.stderr)
        sys.exit(1)
    app_token = args[0]
    table_id = args[1]
    page_size = args[2] if len(args) >= 3 else "20"
    uat = get_uat_token()
    return api_call(
        f"bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size={page_size}",
        method="GET",
        token=uat,
    )


def cmd_create_record(args):
    """create-record <app_token> <table_id> <fields_json>"""
    if len(args) < 3:
        print("Usage: create-record <app_token> <table_id> <fields_json>", file=sys.stderr)
        sys.exit(1)
    app_token = args[0]
    table_id = args[1]
    fields = json.loads(args[2])
    uat = get_uat_token()
    return api_call(
        f"bitable/v1/apps/{app_token}/tables/{table_id}/records",
        data={"fields": fields},
        token=uat,
    )


def cmd_update_record(args):
    """update-record <app_token> <table_id> <record_id> <fields_json>"""
    if len(args) < 4:
        print("Usage: update-record <app_token> <table_id> <record_id> <fields_json>", file=sys.stderr)
        sys.exit(1)
    app_token = args[0]
    table_id = args[1]
    record_id = args[2]
    fields = json.loads(args[3])
    uat = get_uat_token()
    return api_call(
        f"bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
        data={"fields": fields},
        method="PUT",
        token=uat,
    )


# --- Group Management (uses TAT) ---

def cmd_create_group(args):
    """create-group <name> [members_json]"""
    if len(args) < 1:
        print("Usage: create-group <name> [members_json]", file=sys.stderr)
        sys.exit(1)
    name = args[0]
    members = json.loads(args[1]) if len(args) >= 2 else []
    tat = get_tat()
    body = {"name": name, "chat_type": "private"}
    if members:
        body["user_id_list"] = members
    return api_call("im/v1/chats?user_id_type=open_id", data=body, token=tat)


def cmd_add_members(args):
    """add-members <chat_id> <members_json>"""
    if len(args) < 2:
        print("Usage: add-members <chat_id> <members_json>", file=sys.stderr)
        sys.exit(1)
    chat_id = args[0]
    members = json.loads(args[1])
    tat = get_tat()
    return api_call(
        f"im/v1/chats/{chat_id}/members?member_id_type=open_id",
        data={"id_list": members},
        token=tat,
    )


def cmd_list_groups(args):
    """list-groups — List groups the bot is in"""
    tat = get_tat()
    return api_call("im/v1/chats?page_size=20", method="GET", token=tat)


def send_message(receive_id, receive_id_type, msg_type, content):
    """Send a message via Feishu Open API."""
    return api_call(f"im/v1/messages?receive_id_type={receive_id_type}", {
        "receive_id": receive_id,
        "msg_type": msg_type,
        "content": content,
    })


def list_chats(page_size=20, page_token=""):
    """List groups the bot is in."""
    params = f"page_size={page_size}"
    if page_token:
        params += f"&page_token={page_token}"
    return api_call(f"im/v1/chats?{params}", method="GET")


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
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return json.loads(body)
        except Exception:
            return {"error": f"HTTP {e.code}: {body[:500]}"}


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
        print("Messaging (via MCP):")
        print("  send-msg <chat_id|open_id> <text> [--user]  Send markdown message")
        print("  send-card <chat_id|open_id> '<json>' [--user] Send interactive card")
        print("  reply <message_id> <text> [--thread]  Reply to a message")
        print("  get-msgs <chat_id> [time] [count]    Get chat history (time: today/yesterday/this_week/last_3_days)")
        print("  get-msgs-user <open_id> [time] [count] Get DM history")
        print("  search-msgs <keyword> [time]         Search messages across chats")
        print("  get-thread <thread_id>               Get thread replies")
        print()
        print("Calendar / Meeting (UAT):")
        print("  create-event <title> <start> <end> [attendees_json]  Create event with video meeting")
        print("       start/end: ISO 8601 (2026-03-27T14:00:00+08:00) or unix timestamp")
        print("       attendees_json: '[\"ou_xxx\",\"ou_yyy\"]' (optional)")
        print("  list-events [date]                   List events (date: YYYY-MM-DD or 'today')")
        print()
        print("Bitable / Multi-dimensional Table (UAT):")
        print("  list-tables <app_token>              List tables in a bitable app")
        print("  list-records <app_token> <table_id> [page_size]  List records")
        print("  create-record <app_token> <table_id> <fields_json>  Create a record")
        print("  update-record <app_token> <table_id> <record_id> <fields_json>  Update a record")
        print()
        print("Group Management (TAT / bot identity):")
        print("  create-group <name> [members_json]   Create a group chat")
        print("  add-members <chat_id> <members_json> Add members to group")
        print("  list-groups                          List groups the bot is in")
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

    # --- Messaging (via MCP) ---
    elif cmd == "send-msg":
        # send-msg <receive_id> <text> [--user]
        is_user = "--user" in sys.argv
        args = {"receive_id": sys.argv[2], "msg_type": "normal", "content": sys.argv[3],
                "receive_id_type": "user" if is_user else "chat"}
        p(call_tool(token, token_type, "send-message", args))

    elif cmd == "send-card":
        # send-card <receive_id> '<json>' [--user]
        is_user = "--user" in sys.argv
        args = {"receive_id": sys.argv[2], "msg_type": "interactive", "content": sys.argv[3],
                "receive_id_type": "user" if is_user else "chat"}
        p(call_tool(token, token_type, "send-message", args))

    elif cmd == "reply":
        # reply <message_id> <text> [--thread]
        is_thread = "--thread" in sys.argv
        args = {"msg_type": "normal", "content": sys.argv[3],
                "reply_to_message_id": sys.argv[2]}
        if is_thread:
            args["reply_in_thread"] = True
        p(call_tool(token, token_type, "send-message", args))

    elif cmd == "get-msgs":
        # get-msgs <chat_id> [relative_time] [page_size]
        args = {"chat_id": sys.argv[2]}
        if len(sys.argv) >= 4:
            args["relative_time"] = sys.argv[3]
        if len(sys.argv) >= 5:
            args["page_size"] = int(sys.argv[4])
        p(call_tool(token, token_type, "get-messages", args))

    elif cmd == "get-msgs-user":
        # get-msgs-user <open_id> [relative_time] [page_size]
        args = {"open_id": sys.argv[2]}
        if len(sys.argv) >= 4:
            args["relative_time"] = sys.argv[3]
        if len(sys.argv) >= 5:
            args["page_size"] = int(sys.argv[4])
        p(call_tool(token, token_type, "get-messages", args))

    elif cmd == "search-msgs":
        # search-msgs <query> [relative_time]
        args = {"query": sys.argv[2]}
        if len(sys.argv) >= 4:
            args["relative_time"] = sys.argv[3]
        p(call_tool(token, token_type, "search-messages", args))

    elif cmd == "get-thread":
        # get-thread <thread_id>
        p(call_tool(token, token_type, "get-thread-messages", {"thread_id": sys.argv[2]}))

    # --- Calendar / Meeting ---
    elif cmd == "create-event":
        p(cmd_create_event(sys.argv[2:]))

    elif cmd == "list-events":
        p(cmd_list_events(sys.argv[2:]))

    # --- Bitable ---
    elif cmd == "list-tables":
        p(cmd_list_tables(sys.argv[2:]))

    elif cmd == "list-records":
        p(cmd_list_records(sys.argv[2:]))

    elif cmd == "create-record":
        p(cmd_create_record(sys.argv[2:]))

    elif cmd == "update-record":
        p(cmd_update_record(sys.argv[2:]))

    # --- Group Management ---
    elif cmd == "create-group":
        p(cmd_create_group(sys.argv[2:]))

    elif cmd == "add-members":
        p(cmd_add_members(sys.argv[2:]))

    elif cmd == "list-groups":
        p(cmd_list_groups(sys.argv[2:]))

    # --- Raw call ---
    elif cmd == "call":
        p(call_tool(token, token_type, sys.argv[2], json.loads(sys.argv[3])))

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
