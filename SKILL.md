---
name: feishu-inout
description: |
  Read/write Feishu/Lark cloud documents via the official Remote MCP service. Works with Claude Code, Cursor, Codex, OpenCode, OpenClaw, and other AI coding agents. Trigger this skill when the user mentions Feishu, Lark, cloud docs, read/search/create documents, or provides a Feishu/Lark document URL.
---

# Feishu InOut - Feishu/Lark Document Operations

Operate cloud documents via the official Feishu/Lark Remote MCP service (`https://mcp.feishu.cn/mcp`). Zero dependencies, pure Python.

## Quick Check: Is the User Already Configured?

Check two things:
1. Are env vars `FEISHU_APP_ID` and `FEISHU_APP_SECRET` set? (run `echo $FEISHU_APP_ID`)
2. Is a valid UAT token present? (run the script's `whoami` command)

If both are ready → skip to [Usage](#usage).
If either is missing → guide the user through the [First-Time Setup](#first-time-setup).

---

## First-Time Setup

Before starting, ask the user:

> Which features do you need?
> 1. **Read-only** (search, read, browse) — minimal permissions, fastest setup
> 2. **Read & write** (+ create, edit, comments) — recommended, covers most scenarios
> 3. **All features** (+ send messages to groups/DMs) — requires enabling bot capability and publishing an app version

Based on the user's choice, show the matching permission string in Step 2 and decide whether to guide bot setup in Step 6.

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
docx:document:readonly,search:docs:read,wiki:wiki:readonly,im:chat:read,task:task:read,docx:document,docx:document:create,docx:document:write_only,docs:document.media:upload,docs:document.media:download,wiki:node:read,wiki:node:create,docs:document.comment:read,docs:document.comment:create,contact:user:search,contact:contact.base:readonly,contact:user.base:readonly,board:whiteboard:node:read,drive:drive,im:message:send_as_bot,im:message,im:message:send
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

**Messaging (send-text, send-doc, list-chats):**

| Scope | Description | Auth Type |
|-------|-------------|-----------|
| `im:message:send_as_bot` | Send as bot | App |
| `im:message` | Manage messages | App |
| `im:message:send` | Send messages | App |

**Note**: Messaging permissions only need to be enabled if the user chose "All features". Also requires completing Step 6 (bot capability).

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

### Step 6: Enable Bot Capability (only if "All features" was chosen)

If the user chose "All features" (needs messaging), guide these steps:

1. Go to the app → **Add Capabilities** → Enable **Bot**
2. Go to **Version Management & Release** → Create version → Submit for approval
3. After approval, **add the bot to target groups** so it can send messages
4. For DMs, the target user must **search for the app name in Feishu/Lark and open a conversation with the bot first**

Verify the bot is working:
```bash
python3 ~/.claude/skills/feishu-inout/scripts/feishu_mcp.py list-chats
```
If it returns a group list, the bot is active and has joined groups.

If the user didn't choose "All features", skip this step and let them know they can configure it later if needed.

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

# Messaging (via Open API, requires bot capability)
python3 $S list-chats                              # List groups the bot is in
python3 $S send-text <chat_id> <text>              # Send text to group
python3 $S send-doc <chat_id> <doc_id>             # Share doc link to group
python3 $S send-text-user <open_id> <text>         # Send text to user (needs bot contact)
python3 $S send-rich <chat_id> '<interactive_json>' # Send rich/card message

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
2. Run `list-chats` to see groups the bot is in, get the `chat_id`
3. Run `send-doc <chat_id> <doc_id>` to share the doc to the group
4. To @mention: first `search-user` to get open_id, then use `send-rich` to send a rich message with mentions

### Send Messages
- **Group message**: `send-text <chat_id> <text>` — bot must be in the group
- **DM**: `send-text-user <open_id> <text>` — user must have contacted the bot first
- **Share doc**: `send-doc <chat_id> <doc_id>` — send doc link to group
- **Rich/card**: `send-rich <chat_id> '<json>'` — send interactive card message

**Prerequisites**: App must have bot capability enabled and a published version. Bot must be added to the target group, or the user must have opened a conversation with the bot.

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
