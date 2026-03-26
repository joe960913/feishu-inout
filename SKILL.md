---
name: feishu-inout
description: |
  Read/write Feishu/Lark cloud documents and send/search messages via the official Remote MCP service. Works with Claude Code, Cursor, Codex, OpenCode, OpenClaw, and other AI coding agents. Trigger this skill when the user mentions Feishu, Lark, cloud docs, read/search/create documents, messaging, sending messages, or provides a Feishu/Lark document URL.
---

# Feishu InOut - Feishu/Lark Document & Messaging Operations

Operate cloud documents and send/search messages via the official Feishu/Lark Remote MCP service (`https://mcp.feishu.cn/mcp`). Zero dependencies, pure Python.

## Security: Credential Handling Rules

**CRITICAL — follow these rules at all times:**
- **NEVER** include `FEISHU_APP_ID` or `FEISHU_APP_SECRET` values inline in any shell command
- **NEVER** echo, print, or output the App Secret value
- Before running any script command, ensure env vars are loaded: run `source ~/.zshrc` (or `source ~/.bashrc`) first if `echo $FEISHU_APP_ID` returns empty
- The script reads credentials from environment variables automatically — no need to pass them as arguments

## Quick Check: Is the User Already Configured?

Check two things:
1. Are env vars `FEISHU_APP_ID` and `FEISHU_APP_SECRET` set? (run `echo $FEISHU_APP_ID` — if empty, run `source ~/.zshrc` first)
2. Is a valid UAT token present? (run the script's `whoami` command)

If both are ready → skip to [Usage](#usage).
If either is missing → guide the user through the [First-Time Setup](#first-time-setup).

---

## First-Time Setup

Before starting, ask the user:

> Which features do you need?
> 1. **Read-only** (search, read, browse) — minimal permissions, fastest setup
> 2. **Read & write** (+ create, edit, comments) — recommended, covers most scenarios
> 3. **All features** (+ send/search messages in groups/DMs) — messaging uses MCP with user identity (UAT), bot capability is optional

Based on the user's choice, show the matching permission string in Step 2. Note that Step 6 (bot capability) is optional for all choices.

**You MUST show the corresponding permission string for the user's choice:**

Choice 1 (read-only):
```
docx:document:readonly,search:docs:read,wiki:wiki:readonly,im:chat:read,task:task:read
```

Choice 2 (read & write, recommended):
```
docx:document:readonly,search:docs:read,wiki:wiki:readonly,im:chat:read,task:task:read,docx:document,docx:document:create,docx:document:write_only,docs:document.media:upload,docs:document.media:download,wiki:node:read,wiki:node:create,docs:document.comment:read,docs:document.comment:create,contact:user:search,contact:contact.base:readonly,contact:user.base:readonly,board:whiteboard:node:read,drive:drive
```

Choice 3 (all features):
```
docx:document:readonly,search:docs:read,wiki:wiki:readonly,im:chat:read,task:task:read,docx:document,docx:document:create,docx:document:write_only,docs:document.media:upload,docs:document.media:download,wiki:node:read,wiki:node:create,docs:document.comment:read,docs:document.comment:create,contact:user:search,contact:contact.base:readonly,contact:user.base:readonly,board:whiteboard:node:read,drive:drive,im:message,im:message:send_as_bot,im:chat,search:message,im:message.send_as_user,im:message.p2p_msg:get_as_user
```

Guide the user to paste the string in the open platform → Permission Management → **Batch Import/Export**.

6 steps total. Confirm each step is done before moving to the next.

### Step 1: Create a Feishu/Lark App

1. Go to [Lark Open Platform](https://open.larksuite.com/app) (China: [open.feishu.cn](https://open.feishu.cn/app)), log in
2. Click **Create Custom App** in the top right
3. Enter an app name (anything, e.g. "My Doc Assistant") and description
4. After creation, go to the app detail page
5. On the **Credentials & Basic Info** page, note:
   - **App ID** (format: `cli_xxxxxxxxxxxxxxxx`)
   - **App Secret** (alphanumeric string)

Remind the user to set these as environment variables (see Step 4). **Do NOT let the user send the App Secret to you or paste it in the conversation.**

### Step 2: Enable API Permissions

Go to the app → **Permission Management** → **Batch Import/Export**, paste the permission string that matches the user's choice from above.

Or enable individually:

**Core (required):**

| Scope | Description | Auth Type |
|-------|-------------|-----------|
| `docx:document:readonly` | View documents | App |
| `search:docs:read` | Search documents | User |
| `wiki:wiki:readonly` | View wiki | User + App |
| `im:chat:read` | View chat info | App |
| `task:task:read` | View tasks | App |

**Write/edit (append, replace, insert, overwrite, delete, create-doc):**

| Scope | Description | Auth Type |
|-------|-------------|-----------|
| `docx:document` | View & edit documents | App |
| `docx:document:create` | Create documents | App |
| `docx:document:write_only` | Write documents | App |
| `docs:document.media:upload` | Upload images | App |
| `wiki:node:read` | View wiki nodes | App |
| `wiki:node:create` | Create wiki nodes | App |

**Comments (get-comments, add-comments):**

| Scope | Description | Auth Type |
|-------|-------------|-----------|
| `docs:document.comment:read` | Read comments | App |
| `docs:document.comment:create` | Create comments | App |

**Users (search-user, get-user):**

| Scope | Description | Auth Type |
|-------|-------------|-----------|
| `contact:user:search` | Search users | User |
| `contact:contact.base:readonly` | Contact info | App |
| `contact:user.base:readonly` | User info | App |

**Files (fetch-file):**

| Scope | Description | Auth Type |
|-------|-------------|-----------|
| `docs:document.media:download` | Download images/attachments | App |
| `board:whiteboard:node:read` | View whiteboards | App |
| `drive:drive` | Manage drive files | App |

**Messaging (send-msg, reply, get-msgs, search-msgs, etc.):**

| Scope | Description | Auth Type |
|-------|-------------|-----------|
| `im:message` | Manage messages | App |
| `im:message:send_as_bot` | Send as bot | App |
| `im:chat` | Manage chats | App |
| `search:message` | Search messages | User (needs approval) |
| `im:message.send_as_user` | Send as user | User (needs approval) |
| `im:message.p2p_msg:get_as_user` | Read DM history | User (needs approval) |

**Note**: Messaging permissions only need to be enabled if the user chose "All features". Messaging goes through the official MCP using UAT (user identity) -- bot capability is optional, not required.

After enabling, "User" type permissions showing "consistent with user scope" is normal. "App" type showing "-" is also normal.

Confirm all permissions show ✅ **Enabled**.

### Step 3: Add Redirect URL (for OAuth)

Go to the app → **Security Settings** → **Redirect URL** → Add:

```
http://localhost:9876/callback
```

This is the OAuth callback URL for obtaining the User Access Token (UAT).

### Step 4: Set Environment Variables

Guide the user to set credentials themselves. **Do NOT let the user send the App Secret to you, and do NOT output or echo credential values in the conversation.**

Based on the user's OS:

**macOS / Linux:**
```bash
echo 'export FEISHU_APP_ID="your_app_id"' >> ~/.zshrc
echo 'export FEISHU_APP_SECRET="your_app_secret"' >> ~/.zshrc
source ~/.zshrc
```

**Windows (PowerShell):**
```powershell
[System.Environment]::SetEnvironmentVariable('FEISHU_APP_ID', 'your_app_id', 'User')
[System.Environment]::SetEnvironmentVariable('FEISHU_APP_SECRET', 'your_app_secret', 'User')
```
Restart terminal or IDE after setting.

Verify (App ID only, never output the Secret):
- macOS/Linux: `echo $FEISHU_APP_ID`
- Windows: `echo $env:FEISHU_APP_ID`

### Step 5: OAuth Login to Get UAT

Run the login command:
```bash
python3 ~/.claude/skills/feishu-inout/scripts/feishu_mcp.py login
```

Flow:
1. The script opens the browser to the Feishu/Lark authorization page
2. If "insufficient permissions" is shown, the browser will **list the exact missing permissions** — enable them on the open platform and click "Retry", no need to enable everything at once
3. The user clicks **Authorize** in the browser
4. Browser shows "Authorization successful! You can close this page."
5. Terminal shows `UAT saved!` — done

Token expires in 2 hours; the script auto-refreshes via refresh_token. If expired too long, re-run `login`.

Verify everything is ready:
```bash
python3 ~/.claude/skills/feishu-inout/scripts/feishu_mcp.py whoami
python3 ~/.claude/skills/feishu-inout/scripts/feishu_mcp.py search-doc "test"
```

### Step 6: Bot Capability (optional)

Messaging via MCP uses UAT (user identity), so **bot capability is NOT required** for sending or reading messages. The `send-message` MCP tool sends messages as the authenticated user, not as a bot.

However, if the user wants a bot identity (e.g., to send automated notifications as a bot), they can optionally enable it:

1. Go to the app → **Add Capabilities** → Enable **Bot**
2. Go to **Version Management & Release** → Create version → Submit for approval
3. After approval, add the bot to target groups

This step is entirely optional. If the user only needs to send messages as themselves, skip it.

---

## Authentication

The script auto-selects the best token:
- **UAT (User Access Token)** — preferred. Supports searching docs, accessing personal docs, and other user-level operations
- **TAT (Tenant Access Token)** — fallback when UAT is unavailable. Limited: search not available, can only access docs the app has been granted access to

The two tokens use different MCP headers:
- UAT → `X-Lark-MCP-UAT`
- TAT → `X-Lark-MCP-TAT`

Check current status:
```bash
python3 ~/.claude/skills/feishu-inout/scripts/feishu_mcp.py whoami
```

Re-login (when token expires):
```bash
python3 ~/.claude/skills/feishu-inout/scripts/feishu_mcp.py login
```

---

## Extracting Document ID

Extract docID from Feishu/Lark URLs:
```
https://xxx.feishu.cn/docx/ABC123def      → docID = ABC123def
https://xxx.larksuite.com/docx/ABC123def   → docID = ABC123def
https://xxx.feishu.cn/wiki/XYZ789abc       → docID = XYZ789abc
https://xxx.feishu.cn/docs/doccn123c       → docID = doccn123c
```

Rule: the docID is the last path segment after `/docx/`, `/wiki/`, or `/docs/`.

---

## Usage

All operations use the `scripts/feishu_mcp.py` script (`$S` = full path below):

```bash
S=~/.claude/skills/feishu-inout/scripts/feishu_mcp.py

# Auth
python3 $S login                                   # OAuth login to get UAT
python3 $S whoami                                  # Show current token status

# Read documents
python3 $S fetch-doc <docID>                       # Read full document
python3 $S fetch-doc <docID> 0 5000                # Paginated read (offset, limit)

# Search
python3 $S search-doc <keyword>                    # Search documents (needs UAT)
python3 $S search-user <keyword>                   # Search users

# Browse
python3 $S list-docs                               # List "My Library"
python3 $S list-docs <docID>                       # List child docs
python3 $S get-user                                # Get current user info
python3 $S get-user <open_id>                      # Get specific user info

# Create document (one step, with markdown content)
python3 $S create-doc <title> '<markdown>'
python3 $S create-doc <title> '<markdown>' '{"wiki_space":"my_library"}'
python3 $S create-doc <title> '<markdown>' '{"folder_token":"fldcnXXX"}'

# Update document (7 modes)
python3 $S append <docID> '<markdown>'             # Append to end
python3 $S overwrite <docID> '<markdown>'          # Overwrite entire doc (use with caution)
python3 $S replace <docID> '<selection>' '<md>'    # Replace matched range
python3 $S insert-after <docID> '<sel>' '<md>'     # Insert after match
python3 $S insert-before <docID> '<sel>' '<md>'    # Insert before match
python3 $S delete-range <docID> '<selection>'      # Delete matched content

# Comments
python3 $S get-comments <docID>                    # Get all comments
python3 $S get-comments <docID> whole              # Whole-doc comments only
python3 $S get-comments <docID> segment            # Inline comments only
python3 $S add-comments <docID> <text>             # Add a text comment

# Files
python3 $S fetch-file <token>                      # Get file/image content
python3 $S fetch-file <token> whiteboard           # Get whiteboard content

# Messaging (via MCP)
python3 $S send-msg <chat_id|open_id> <text> [--user]  # Send markdown message
python3 $S send-card <chat_id|open_id> '<json>' [--user] # Send interactive card
python3 $S reply <message_id> <text> [--thread]    # Reply to a message
python3 $S get-msgs <chat_id> [time] [count]       # Get group chat history
python3 $S get-msgs-user <open_id> [time] [count]  # Get DM history
python3 $S search-msgs <keyword> [time]            # Search messages across chats
python3 $S get-thread <thread_id>                  # Get thread replies

# Advanced (raw JSON call to any tool)
python3 $S call <toolName> '<jsonArgs>'
python3 $S update-doc '{"doc_id":"xxx","mode":"replace_range","selection_by_title":"## Section","markdown":"New content"}'
```

### Selection Syntax (for replace / insert / delete)

- **Range match**: `start text...end text` — matches everything between the two text fragments
- **Exact match**: `exact text` — no `...`, matches exactly
- **Title-based**: use `selection_by_title: "## Title"` in the JSON mode of `update-doc` to target an entire section

---

## Workflows

### Read a Document
1. Extract docID from the user's URL
2. Run `fetch-doc <docID>`
3. Parse the returned JSON — `result.content[0].text` contains the markdown content
4. For large docs, use pagination: `fetch-doc <docID> <offset> <limit>`

### Search and Read
1. Run `search-doc <keyword>` to find documents
2. Extract `id` (docID) and `title` from the `items` array in the result
3. If multiple results, list them and let the user choose
4. Run `fetch-doc <docID>` to read the selected document

### Create a Document (one step)
1. Run `create-doc <title> '<markdown>'` to create a doc with content
2. Optionally specify location: wiki node `wiki_node`, wiki space `wiki_space` (`my_library` = personal library), or folder `folder_token`
3. Returns `doc_id` and `doc_url`
4. **Note**: without a location, the doc is created in the personal space root and won't appear in the "Recent" list. Recommend using `wiki_space: "my_library"` so the user can find it easily

### Edit a Document
Prefer partial updates over overwrite:
1. `append` — add content to the end
2. `replace` — find and replace specific content (use `start...end` range match or exact text)
3. `insert-after` / `insert-before` — insert at a specific position
4. `delete-range` — delete matched content
5. `overwrite` — last resort, clears the entire doc (loses images, comments, etc.)

**Target an entire section by title** (great for replacing/deleting whole sections):
```bash
python3 $S call update-doc '{"doc_id":"xxx","mode":"replace_range","selection_by_title":"### Section Title","markdown":"### Section Title\n\nReplaced content"}'
```
`selection_by_title` matches from the heading to the next heading of the same level.

### Browse Wiki
1. Run `list-docs` to view "My Library"
2. Or `list-docs <docID>` to view child docs (response includes `has_child` field)
3. Recursively browse deeper levels

### @Mention Workflow
1. Run `search-user <name>` to get the user's `open_id`
2. Use advanced mode in `add-comments`: `call add-comments '{"doc_id":"xxx","elements":[{"type":"mention","open_id":"ou_xxx"}]}'`

### Create Doc and Send to Group Chat
1. Run `create-doc <title> '<markdown>'` to create the doc
2. Run `send-msg <chat_id> <text>` to share the doc link to the group (include the doc URL in the text)
3. To @mention: use `<mention-user id="openId"/>` syntax in the message text (first `search-user` to get open_id)

### Send Messages
Messages go through the official Feishu/Lark MCP using UAT (user identity) -- no bot capability needed.

- **Group message**: `send-msg <chat_id> <text>` -- sends as the authenticated user
- **DM**: `send-msg <open_id> <text> --user` -- send to a user by open_id
- **Interactive card**: `send-card <chat_id|open_id> '<json>' [--user]` -- send a card message
- **Reply**: `reply <message_id> <text>` -- reply to a specific message
- **Reply in thread**: `reply <message_id> <text> --thread` -- reply within a thread
- **Group history**: `get-msgs <chat_id> [time] [count]` -- get chat history with time filter
- **DM history**: `get-msgs-user <open_id> [time] [count]` -- read DM history
- **Search**: `search-msgs <keyword> [time]` -- search messages across all chats
- **Thread replies**: `get-thread <thread_id>` -- get all replies in a thread

**Markdown formatting**: `send-msg` supports Markdown syntax in message text.

**@mention syntax**:
- Mention a specific user: `<mention-user id="openId"/>`
- Mention everyone: `<mention-user id="all"/>`
- Emoji support: `[SMILE]`, `[THUMBSUP]`, etc.

**Time filters** for `get-msgs`, `get-msgs-user`, `search-msgs`: `today`, `yesterday`, `this_week`, `last_week`, `this_month`, `last_month`, `last_30_minutes`, `last_3_days`, etc.

---

## Error Handling

| Code | Meaning | Solution |
|------|---------|----------|
| `-32011` | Auth credentials missing | Check that `FEISHU_APP_ID` and `FEISHU_APP_SECRET` env vars are set |
| `-32003` | Invalid or expired credentials | TAT: check App Secret; UAT: run `login` to re-authorize |
| `-32601` | Tool or method not found | Run `tools` to see available tools |
| `-32602` | Invalid parameters | Check parameter names and format |
| `-32700` | JSON parse error | Check the JSON argument format |
| `429` | Rate limited | Wait a few seconds and retry |
| `99991679` | User hasn't authorized this scope | Re-run `login`, or enable the permission in the app's permission management |

### Common Issues

**search-doc returns "required ... search:docs:read"**
→ This permission requires user identity (UAT). Run `login` to get UAT.

**fetch-doc returns "permission denied"**
→ In TAT mode, the app must be added as a document collaborator. Use UAT (after `login`) to access all docs the user has permission for.

**Browser doesn't respond after login**
→ Check that the redirect URL `http://localhost:9876/callback` has been added in the app's Security Settings.

**UAT expired**
→ The script auto-attempts refresh via refresh_token. If the refresh_token has also expired (30 days), re-run `login`.
