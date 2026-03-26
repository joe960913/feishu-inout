<p align="right"><b>English</b> | <a href="README_CN.md">中文</a></p>

<div align="center">

# feishu-inout

**One command to connect your AI coding agent to Lark (Feishu) documents**

Claude Code / Cursor / Codex / OpenCode / OpenClaw — instant Lark cloud doc access

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.6+](https://img.shields.io/badge/Python-3.6+-green.svg)](https://python.org)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-0-brightgreen.svg)](#)
[![Lark Official MCP](https://img.shields.io/badge/Lark-Official%20MCP-4f46e5.svg)](https://mcp.feishu.cn)

</div>

---

> **Search, read, create, edit, append, replace, insert, delete, send messages** — do everything with Lark docs and messaging from your AI coding agent.
>
> Built on Lark's official Remote MCP service + Open API. Zero dependencies, single file, works out of the box.

## Highlights

- **Search Documents** — by keyword, author, time range
- **7 Edit Modes** — append, overwrite, replace range, replace all, insert before/after, delete — precise edits without data loss
- **One-Step Create** — title + Markdown content in one call, with wiki/folder targeting
- **Send to Group Chat** — share docs to groups, send text, doc links, or rich cards
- **Zero Dependencies** — pure Python stdlib, no Node.js, no local MCP server
- **Comment Management** — view whole-doc and inline comments, add comments with @mentions
- **User Search** — find colleagues' open_id for @mentions
- **File Access** — download images, attachments, whiteboard content
- **My Library** — browse personal docs without IDs, recursive wiki exploration
- **Paginated Reading** — offset + limit for large documents
- **Auto Token Refresh** — OAuth tokens refresh automatically, login once and forget

## Who Is This For?

Not just for developers — anyone who uses Lark/Feishu docs can benefit:

- **Product** — generate PRDs, update requirements, sync release notes
- **Operations** — draft campaign plans, maintain content calendars, update SOPs
- **Data** — write analysis reports directly to docs, auto-format weekly metrics
- **Sales** — create proposals, update client records, generate quotes
- **HR** — draft job descriptions, update onboarding guides, revise policies

If your workflow involves "open Lark → find a doc → edit → notify someone", now it's just one sentence.

## Supported AI Tools

<table>
<tr>
<td align="center"><b>Claude Code</b></td>
<td align="center"><b>Cursor</b></td>
<td align="center"><b>Codex</b></td>
<td align="center"><b>OpenCode</b></td>
<td align="center"><b>OpenClaw</b></td>
</tr>
<tr>
<td align="center"><b>Gemini CLI</b></td>
<td align="center"><b>GitHub Copilot</b></td>
<td align="center"><b>Amp</b></td>
<td align="center"><b>Windsurf</b></td>
<td align="center"><b>Cline</b></td>
</tr>
<tr>
<td align="center"><b>Roo Code</b></td>
<td align="center"><b>Clawd</b></td>
<td align="center"><b>Trae</b></td>
<td align="center"><b>Kiro</b></td>
<td align="center"><b>Kilo</b></td>
</tr>
<tr>
<td align="center"><b>Goose</b></td>
<td align="center"><b>Factory.ai</b></td>
<td align="center"><b>Antigravity</b></td>
<td align="center" colspan="2"><b>+ any skills-compatible agent</b></td>
</tr>
</table>

## Install

```bash
npx skills add joe960913/feishu-inout
```

## Quick Start (5 min)

### 1. Create a Lark App

Go to [Lark Open Platform](https://open.larksuite.com/app) ([China: open.feishu.cn](https://open.feishu.cn/app)) → Create a custom app → Note your **App ID** and **App Secret**

### 2. Enable Permissions

Go to your app → Permission Management → **Batch Import/Export** and paste:

```
docx:document:readonly,search:docs:read,wiki:wiki:readonly,im:chat:read,task:task:read,docx:document,docx:document:create,docx:document:write_only,docs:document.media:upload,docs:document.media:download,wiki:node:read,wiki:node:create,docs:document.comment:read,docs:document.comment:create,contact:user:search,contact:contact.base:readonly,contact:user.base:readonly,board:whiteboard:node:read,drive:drive,im:message:send_as_bot,im:message,im:message:send
```

<details>
<summary><b>Or enable individually (click to expand)</b></summary>

#### Core (required)

| Scope | Description |
|-------|-------------|
| `docx:document:readonly` | View documents |
| `search:docs:read` | Search documents |
| `wiki:wiki:readonly` | View wiki |
| `im:chat:read` | View chat info |
| `task:task:read` | View tasks |

#### Write (for editing)

| Scope | Description |
|-------|-------------|
| `docx:document` | Edit documents |
| `docx:document:create` | Create documents |
| `docx:document:write_only` | Write documents |
| `docs:document.media:upload` | Upload images |
| `wiki:node:read` | View wiki nodes |
| `wiki:node:create` | Create wiki nodes |

#### Comments / Users / Files (optional)

| Scope | Description |
|-------|-------------|
| `docs:document.comment:read` | Read comments |
| `docs:document.comment:create` | Create comments |
| `contact:user:search` | Search users |
| `contact:contact.base:readonly` | Contact info |
| `contact:user.base:readonly` | User info |
| `docs:document.media:download` | Download files |
| `board:whiteboard:node:read` | View whiteboards |
| `drive:drive` | Manage drive files |

#### Messaging (optional)

| Scope | Description |
|-------|-------------|
| `im:message:send_as_bot` | Send as bot |
| `im:message` | Manage messages |
| `im:message:send` | Send messages |

</details>

### 3. Add Redirect URL

App → Security Settings → Redirect URL → Add:

```
http://localhost:9876/callback
```

### 4. Set Environment Variables

Set your credentials (**never share App Secret with AI**):

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
# Restart terminal after setting
```

### 5. Login

Tell your AI agent to log in:

```
You: Log in to Lark

AI:  Running OAuth login...
     Browser opened, please authorize ✓
     UAT saved! You can now access your Lark docs.
```

Tokens auto-refresh. No need to log in repeatedly.

### 6. Enable Bot (for messaging only)

If you need to **send messages to groups or users**:

1. App → **Add Capabilities** → Enable **Bot**
2. **Version Management** → Create version → Submit for approval
3. After approval, **add the bot to target groups**
4. For DMs, users must **open a conversation with the bot first**

> Skip this step if you don't need messaging. Document operations work without it.

## Usage Examples

After setup, **just talk to your AI agent naturally**:

### Search and Browse

```
You: What Lark docs do I have?

AI:  Found 20 documents:
     1. Q2 Product Roadmap — Wang Ming (3/25)
     2. Frontend Refactor Plan — Li Hua (3/24)
     3. Onboarding Guide — Zhang Wei (3/23)
     ...
```

### Read Documents

```
You: Read this doc https://xxx.larksuite.com/wiki/ABC123def

AI:  ## Frontend Refactor Plan
     ### Goals
     - Migrate to React 18 + TypeScript
     - First paint < 1.5s
     ### Progress
     1. ✅ Component library upgrade
     2. ❌ Router refactor (in progress)
     ...
```

### Create and Edit

```
You: Create a Lark doc called "Q2 Product Roadmap" with an outline

AI:  Document created!
     Link: https://xxx.larksuite.com/docx/xxx
     Outline written: Goals, Timeline, Milestones, Resources
```

```
You: Replace all "TBD" with "Confirmed" in that doc

AI:  Replaced 3 occurrences.
```

### Send to Group Chat

```
You: Share that doc to the product team group

AI:  Document "Q2 Product Roadmap" shared to "Product Team" group.
```

```
You: Send a message to the engineering group: today's build is deployed

AI:  Message sent to "Engineering" group.
```

### More Scenarios

```
You: Find David's open_id so I can @ him in the doc
You: Download the images from that document
You: Browse the "Product Docs" wiki and list sub-pages
You: Write the test results to a Lark doc and share it in the dev group
```

---

<details>
<summary><b>CLI Direct Usage (advanced)</b></summary>

```bash
S=scripts/feishu_mcp.py

python3 $S search-doc "weekly report"                            # Search
python3 $S fetch-doc ABC123def                                   # Read
python3 $S list-docs                                             # My Library
python3 $S create-doc "Meeting Notes" "## Topics\n\n- Item 1"   # Create
python3 $S append ABC123def "## Update\n\nAppended content"      # Append
python3 $S replace ABC123def "old text...end" "new text"         # Replace
python3 $S insert-after ABC123def "some text" "inserted content" # Insert
python3 $S delete-range ABC123def "content to delete"            # Delete
python3 $S get-comments ABC123def                                # Comments
python3 $S search-user "David"                                   # Search user
python3 $S fetch-file filetoken123                               # Get file
python3 $S list-chats                                            # List groups
python3 $S send-text oc_xxx "message"                            # Send to group
python3 $S send-doc oc_xxx ABC123def                             # Share doc
python3 $S send-text-user ou_xxx "message"                       # DM user
```

</details>

## How It Works

```
AI Agent ──► feishu_mcp.py ──► mcp.feishu.cn/mcp ──► Lark Cloud Docs
               │                    (Official MCP)
               ├─ Auto TAT/UAT auth
               ├─ JSON-RPC 2.0
               └─ Single file, zero deps
```

Calls Lark's official Remote MCP service directly. No local MCP server, no Node.js — one Python script handles everything.

## FAQ

<details>
<summary><b>search-doc error "search:docs:read"</b></summary>

This permission requires UAT (user identity). Run `login` to authorize.
</details>

<details>
<summary><b>fetch-doc error "permission denied"</b></summary>

With TAT, the app needs document collaborator access. Use UAT (after `login`) to access all documents you have permission for.
</details>

<details>
<summary><b>Browser doesn't open after login</b></summary>

Check that you added the redirect URL `http://localhost:9876/callback` in your app's Security Settings.
</details>

<details>
<summary><b>Token expired</b></summary>

Tokens auto-refresh via refresh_token. If the refresh_token also expires (30 days), run `login` again.
</details>

## Security

- **Credentials** — App Secret is passed via environment variables, never exposed in conversations
- **Official Service** — All API calls go through Lark's official MCP service (`mcp.feishu.cn`)
- **Local Tokens** — OAuth tokens stored locally, never uploaded to external services
- **Third-party Content** — Document content comes from docs you have access to; be aware of potentially untrusted content

## Contributing

Issues and PRs welcome!

## License

MIT
