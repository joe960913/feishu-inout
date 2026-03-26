---
name: feishu-inout
description: |
  通过飞书官方远程 MCP 服务读写云文档、搜索文档、管理评论。适用于 Claude Code、Cursor、Codex、OpenCode、OpenClaw 等 AI 编程助手。当用户提到飞书、Feishu、Lark、飞书文档、云文档、读取文档、搜索文档、文档评论时使用此 skill。即使用户只是给出飞书文档链接也应触发。
---

# Feishu InOut - 飞书文档操作

通过飞书官方远程 MCP 服务 (`https://mcp.feishu.cn/mcp`) 操作云文档，零依赖，纯 Python。

## 快速判断：用户是否已完成配置？

检查两件事：
1. 环境变量 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 是否已设置（运行 `echo $FEISHU_APP_ID`）
2. UAT token 是否存在且有效（运行脚本的 `whoami` 命令）

如果都就绪 → 直接跳到 [使用方式](#使用方式)。
如果缺少任何一项 → 引导用户走 [首次配置](#首次配置指南从零开始) 流程。

---

## 首次配置指南（从零开始）

分 5 步，引导用户逐步完成。每步完成后确认再进入下一步。

### 第 1 步：创建飞书自建应用

1. 打开 [飞书开放平台](https://open.feishu.cn/app)，登录飞书账号
2. 点击右上角 **创建自建应用**
3. 填写应用名称（任意，如"我的文档助手"）和描述
4. 创建完成后，进入应用详情页
5. 在 **凭证与基础信息** 页面，找到并记录：
   - **App ID**（格式：`cli_xxxxxxxxxxxxxxxx`）
   - **App Secret**（一串字母数字）

提醒用户自行将这两个值设置为环境变量（见第 4 步），不要将 App Secret 直接发送给 AI 或粘贴到对话中。

### 第 2 步：开通 API 权限

进入应用 → 左侧菜单 **权限管理** → 点击 **开通权限**，搜索并开通以下权限：

**必须开通（文档读写核心权限）：**

| 权限 scope | 名称 | 权限类型 |
|-----------|------|----------|
| `docx:document:readonly` | 查看新版文档 | 应用身份 |
| `search:docs:read` | 搜索云文档 | 用户身份 |
| `wiki:wiki:readonly` | 查看知识库 | 用户身份 + 应用身份 |
| `im:chat:read` | 查看群信息 | 应用身份 |
| `task:task:read` | 查看任务信息 | 应用身份 |

**写入/编辑文档（append、replace、insert、overwrite、delete、create-doc）：**

| 权限 scope | 名称 | 权限类型 |
|-----------|------|----------|
| `docx:document` | 查看、编辑新版文档 | 应用身份 |
| `docx:document:create` | 创建新版文档 | 应用身份 |
| `docx:document:write_only` | 编辑新版文档 | 应用身份 |
| `docs:document.media:upload` | 上传图片到文档 | 应用身份 |
| `wiki:node:read` | 查看知识库节点 | 应用身份 |
| `wiki:node:create` | 创建知识库节点 | 应用身份 |

**评论功能（get-comments、add-comments）：**

| 权限 scope | 名称 | 权限类型 |
|-----------|------|----------|
| `docs:document.comment:read` | 查看文档评论 | 应用身份 |
| `docs:document.comment:create` | 创建文档评论 | 应用身份 |

**用户功能（search-user、get-user）：**

| 权限 scope | 名称 | 权限类型 |
|-----------|------|----------|
| `contact:user:search` | 搜索用户 | 用户身份 |
| `contact:contact.base:readonly` | 获取通讯录基本信息 | 应用身份 |
| `contact:user.base:readonly` | 获取用户基本信息 | 应用身份 |

**文件功能（fetch-file）：**

| 权限 scope | 名称 | 权限类型 |
|-----------|------|----------|
| `docs:document.media:download` | 下载文档中的图片和附件 | 应用身份 |
| `board:whiteboard:node:read` | 查看画板 | 应用身份 |
| `drive:drive` | 管理云空间文件 | 应用身份 |

开通后，**用户身份**类型的权限标注为"与用户权限范围一致"是正常的。**应用身份**类型标注"-"也是正常的。

确认所有权限状态显示为 ✅ **已开通**。

### 第 3 步：配置重定向 URL（OAuth 授权用）

进入应用 → 左侧菜单 **安全设置** → **重定向URL** → 添加：

```
http://localhost:9876/callback
```

这是 OAuth 授权流程的回调地址，用于获取用户身份令牌（UAT）。

### 第 4 步：设置环境变量

指导用户自行将凭证写入 shell 配置文件。**不要让用户把 App Secret 发给你，也不要在对话中输出或回显凭证值。**

根据用户操作系统，指导对应的设置方式：

**macOS / Linux：**
```bash
echo 'export FEISHU_APP_ID="你的AppID"' >> ~/.zshrc
echo 'export FEISHU_APP_SECRET="你的AppSecret"' >> ~/.zshrc
source ~/.zshrc
```

**Windows (PowerShell)：**
```powershell
[System.Environment]::SetEnvironmentVariable('FEISHU_APP_ID', '你的AppID', 'User')
[System.Environment]::SetEnvironmentVariable('FEISHU_APP_SECRET', '你的AppSecret', 'User')
```
设置后需重启终端或 IDE 使环境变量生效。

设置完成后，验证是否生效（仅验证 App ID，不要输出 Secret）：
- macOS/Linux: `echo $FEISHU_APP_ID`
- Windows: `echo $env:FEISHU_APP_ID`

### 第 5 步：OAuth 登录获取 UAT

运行登录命令：
```bash
python3 ~/.claude/skills/feishu-inout/scripts/feishu_mcp.py login
```

流程：
1. 脚本自动打开浏览器跳转飞书授权页面
2. 如果提示"权限不足"，浏览器会**列出具体缺少的权限名称**，去开放平台开通后点"刷新重试"即可，不需要一次性开完所有权限
3. 用户在浏览器中点击 **授权**
4. 浏览器显示"授权成功！可以关闭此页面了。"
5. 终端显示 `UAT saved!` 表示成功

Token 有效期 2 小时，脚本会自动用 refresh_token 续期。如果过期太久，重新运行 `login` 即可。

验证一切就绪：
```bash
python3 ~/.claude/skills/feishu-inout/scripts/feishu_mcp.py whoami
python3 ~/.claude/skills/feishu-inout/scripts/feishu_mcp.py search-doc "测试"
```

---

## 认证模式

脚本自动选择最佳 token：
- **UAT（用户身份）** - 优先使用，支持搜索文档、访问个人文档等用户级操作
- **TAT（应用身份）** - UAT 不可用时的兜底，功能受限（搜索不可用，只能访问应用有权的文档）

两种 token 对应飞书 MCP 不同的请求头：
- UAT → `X-Lark-MCP-UAT`
- TAT → `X-Lark-MCP-TAT`

检查当前状态：
```bash
python3 ~/.claude/skills/feishu-inout/scripts/feishu_mcp.py whoami
```

重新登录（token 过期时）：
```bash
python3 ~/.claude/skills/feishu-inout/scripts/feishu_mcp.py login
```

---

## 文档 ID 提取

从飞书 URL 提取 docID：
```
https://xxx.feishu.cn/docx/ABC123def   → docID = ABC123def
https://xxx.feishu.cn/wiki/XYZ789abc   → docID = XYZ789abc
https://xxx.feishu.cn/docs/doccn123c   → docID = doccn123c
```

规则：URL 最后一段路径即为 docID。`/docx/`、`/wiki/`、`/docs/` 后面的部分。

---

## 使用方式

所有操作通过 `scripts/feishu_mcp.py` 脚本完成（以下用 `$S` 代替完整路径）：

```bash
S=~/.claude/skills/feishu-inout/scripts/feishu_mcp.py

# 认证
python3 $S login                                   # OAuth 登录获取 UAT
python3 $S whoami                                  # 查看当前 token 状态

# 读取文档
python3 $S fetch-doc <docID>                       # 读取完整文档
python3 $S fetch-doc <docID> 0 5000                # 分页读取（offset, limit）

# 搜索
python3 $S search-doc <keyword>                    # 搜索文档（需 UAT）
python3 $S search-user <keyword>                   # 搜索用户

# 浏览
python3 $S list-docs                               # 列出"我的文档库"
python3 $S list-docs <docID>                       # 列出某文档的子文档
python3 $S get-user                                # 获取当前用户信息
python3 $S get-user <open_id>                      # 获取指定用户信息

# 创建文档（一步到位，带 markdown 内容）
python3 $S create-doc <title> '<markdown>'
python3 $S create-doc <title> '<markdown>' '{"wiki_space":"my_library"}'
python3 $S create-doc <title> '<markdown>' '{"folder_token":"fldcnXXX"}'

# 更新文档（7 种模式）
python3 $S append <docID> '<markdown>'             # 追加到末尾
python3 $S overwrite <docID> '<markdown>'          # 覆盖整个文档（慎用）
python3 $S replace <docID> '<selection>' '<md>'    # 定位替换
python3 $S insert-after <docID> '<sel>' '<md>'     # 在匹配位置后插入
python3 $S insert-before <docID> '<sel>' '<md>'    # 在匹配位置前插入
python3 $S delete-range <docID> '<selection>'      # 删除匹配内容

# 评论
python3 $S get-comments <docID>                    # 获取全部评论
python3 $S get-comments <docID> whole              # 仅全文评论
python3 $S get-comments <docID> segment            # 仅划词评论
python3 $S add-comments <docID> <text>             # 添加文本评论

# 文件
python3 $S fetch-file <token>                      # 获取文件/图片内容
python3 $S fetch-file <token> whiteboard           # 获取画板内容

# 高级（直接传 JSON 调任意工具）
python3 $S call <toolName> '<jsonArgs>'
python3 $S update-doc '{"doc_id":"xxx","mode":"replace_range","selection_by_title":"## 章节","markdown":"新内容"}'
```

### 定位语法（用于 replace / insert / delete）

- **范围匹配**：`开头内容...结尾内容` — 匹配两段文字之间的所有内容
- **精确匹配**：`完整文本` — 不含 `...`，精确匹配
- **标题定位**：通过 `update-doc` 的 JSON 模式使用 `selection_by_title: "## 标题"`，定位整个章节

---

## 工作流

### 读取文档内容
1. 从用户给的 URL 提取 docID
2. 运行 `fetch-doc <docID>`
3. 解析返回的 JSON，`result.content[0].text` 中包含文档的 markdown 内容
4. 大文档可分页：`fetch-doc <docID> <offset> <limit>`

### 搜索并读取
1. 运行 `search-doc <keyword>` 找到文档
2. 从结果的 `items` 数组中提取目标文档的 `id`（即 docID）和 `title`
3. 如果有多个结果，先列出让用户选择
4. 运行 `fetch-doc <docID>` 读取选中文档内容

### 创建文档（一步到位）
1. 运行 `create-doc <title> '<markdown>'` 直接创建带内容的文档
2. 可指定位置：知识库节点 `wiki_node`、知识空间 `wiki_space`（`my_library` = 个人文档库）、文件夹 `folder_token`
3. 返回 `doc_id` 和 `doc_url`
4. **注意**：不指定位置时文档会创建在个人空间根目录，不会出现在飞书"最近访问"列表中。建议指定 `wiki_space: "my_library"` 创建到个人文档库，方便用户在飞书中找到

### 编辑文档
优先使用局部更新，避免 overwrite：
1. `append` — 追加内容到文档末尾
2. `replace` — 定位并替换指定内容（用 `开头...结尾` 范围匹配，或精确文本匹配）
3. `insert-after` / `insert-before` — 在指定位置前后插入
4. `delete-range` — 删除匹配的内容
5. `overwrite` — 最后手段，会清空文档重写（丢失图片、评论等）

**按标题定位整个章节**（替换/删除整个章节时特别好用）：
```bash
python3 $S call update-doc '{"doc_id":"xxx","mode":"replace_range","selection_by_title":"### 章节标题","markdown":"### 章节标题\n\n替换后的内容"}'
```
`selection_by_title` 会自动匹配从该标题到下一个同级标题之间的所有内容。

### 浏览知识库
1. 运行 `list-docs` 查看"我的文档库"
2. 或 `list-docs <docID>` 查看某文档的子文档（返回中有 `has_child` 字段）
3. 可以逐层递归浏览

### @用户 工作流
1. 运行 `search-user <姓名>` 获取用户 `open_id`
2. 在 `add-comments` 中使用高级模式：`call add-comments '{"doc_id":"xxx","elements":[{"type":"mention","open_id":"ou_xxx"}]}'`

---

## 错误处理

| 错误码 | 含义 | 解决方案 |
|--------|------|----------|
| `-32011` | 认证凭证缺失 | 检查环境变量 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 是否设置 |
| `-32003` | 凭证无效或过期 | TAT: 检查 App Secret 是否正确；UAT: 运行 `login` 重新授权 |
| `-32601` | 工具或方法不存在 | 运行 `tools` 查看可用工具列表 |
| `-32602` | 参数错误 | 检查参数名和格式是否正确 |
| `-32700` | JSON 格式错误 | 检查传入的 JSON 参数格式 |
| `429` | 请求频率超限 | 等待几秒后重试 |
| `99991679` | 用户未授权该 scope | 需要重新 `login`，或在应用权限管理中开通对应权限 |

### 常见问题

**search-doc 返回 "required ... search:docs:read"**
→ 这个权限是用户身份类型，必须用 UAT。运行 `login` 获取 UAT。

**fetch-doc 返回 "permission denied"**
→ TAT 模式下，应用需要被加为文档协作者才能访问。用 UAT 可以访问用户自己有权的所有文档。

**login 后浏览器没反应**
→ 检查是否已在飞书应用的安全设置中添加重定向 URL `http://localhost:9876/callback`。

**UAT 过期**
→ 脚本会自动尝试用 refresh_token 续期。如果 refresh_token 也过期（30天），需要重新 `login`。
