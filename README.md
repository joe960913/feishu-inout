<div align="center">

# feishu-inout

**一行命令，让 AI 编程助手读写你的飞书文档**

Claude Code / Cursor / Codex / OpenCode / OpenClaw — 一键接入飞书云文档

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.6+](https://img.shields.io/badge/Python-3.6+-green.svg)](https://python.org)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-0-brightgreen.svg)](#)
[![Feishu Official MCP](https://img.shields.io/badge/Feishu-Official%20MCP-4f46e5.svg)](https://mcp.feishu.cn)

</div>

---

> **搜索、阅读、创建、编辑、追加、替换、插入、删除** — 在 AI 编程助手中完成飞书文档的一切操作。
>
> 基于飞书官方远程 MCP 服务，零依赖，单文件，开箱即用。

## 亮点

- **搜索文档** — 按关键词、作者、时间范围搜索，快速定位
- **7 种编辑模式** — 追加、覆盖、定位替换、全文替换、前后插入、删除，精准编辑不丢内容
- **一步创建** — 标题 + Markdown 内容一次搞定，支持指定知识库/文件夹位置
- **零依赖** — 纯 Python 标准库，不需要 Node.js，不需要本地 MCP 服务器
- **评论管理** — 全文评论、划词评论分类查看，支持 @用户
- **用户搜索** — 查找同事的 open_id，配合 @提及 使用
- **文件获取** — 下载文档中的图片、附件、画板内容
- **"我的文档库"** — 无需 ID 直接浏览个人文档，逐层递归探索知识库
- **大文档分页** — offset + limit 分段读取，不怕文档太长
- **自动续期** — OAuth token 自动刷新，登录一次长期使用

## 支持的 AI 工具

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
<td align="center" colspan="2"><b>+ 所有兼容 skills 格式的 AI 编程助手</b></td>
</tr>
</table>

## 安装

```bash
npx skills add joe960913/feishu-inout
```

## 快速开始（5 分钟）

### 1. 创建飞书应用

打开 [飞书开放平台](https://open.feishu.cn/app) → 创建自建应用 → 记录 **App ID** 和 **App Secret**

### 2. 开通权限

进入应用 → 权限管理 → **批量导入/导出权限**，粘贴以下内容一键导入：

```
docx:document:readonly,search:docs:read,wiki:wiki:readonly,im:chat:read,task:task:read,docx:document,docx:document:create,docx:document:write_only,docs:document.media:upload,docs:document.media:download,wiki:node:read,wiki:node:create,docs:document.comment:read,docs:document.comment:create,contact:user:search,contact:contact.base:readonly,contact:user.base:readonly,board:whiteboard:node:read,drive:drive
```

<details>
<summary><b>或者逐个搜索开通（点击展开查看完整列表）</b></summary>

#### 基础权限（必须）

| 权限 scope | 名称 |
|-----------|------|
| `docx:document:readonly` | 查看新版文档 |
| `search:docs:read` | 搜索云文档 |
| `wiki:wiki:readonly` | 查看知识库 |
| `im:chat:read` | 查看群信息 |
| `task:task:read` | 查看任务信息 |

#### 写入权限（编辑文档需要）

| 权限 scope | 名称 |
|-----------|------|
| `docx:document` | 编辑新版文档 |
| `docx:document:create` | 创建新版文档 |
| `docx:document:write_only` | 写入新版文档 |
| `docs:document.media:upload` | 上传图片 |
| `wiki:node:read` | 查看知识库节点 |
| `wiki:node:create` | 创建知识库节点 |

#### 评论 / 用户 / 文件权限（可选）

| 权限 scope | 名称 |
|-----------|------|
| `docs:document.comment:read` | 查看评论 |
| `docs:document.comment:create` | 创建评论 |
| `contact:user:search` | 搜索用户 |
| `contact:contact.base:readonly` | 通讯录基本信息 |
| `contact:user.base:readonly` | 用户基本信息 |
| `docs:document.media:download` | 下载图片/附件 |
| `board:whiteboard:node:read` | 查看画板 |
| `drive:drive` | 管理云空间文件 |

</details>

### 3. 配置重定向 URL

应用 → 安全设置 → 重定向 URL → 添加：

```
http://localhost:9876/callback
```

### 4. 设置环境变量

自行设置凭证（**请勿将 App Secret 发送给 AI**）：

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
# 设置后重启终端
```

### 5. 登录授权

环境变量设好后，告诉 AI 助手帮你登录：

```
You: 帮我登录飞书

AI:  正在执行 OAuth 登录...
     浏览器已打开，请点击授权 ✓
     UAT 获取成功！现在可以操作你的飞书文档了。
```

Token 自动刷新，无需反复登录。

## 使用示例

安装配置好后，**直接用自然语言对话**，skill 自动触发：

### 搜索和浏览

```
You: 看看我飞书上有哪些文档

AI:  找到 20 篇文档：
     1. Q2 产品规划 — 王明 (3/25)
     2. 前端重构方案 — 李华 (3/24)
     3. 新人入职指南 — 张伟 (3/23)
     ...
```

```
You: 搜索飞书文档：项目周报

AI:  搜索到 5 篇相关文档，要看哪篇？
```

### 阅读文档

```
You: 读一下这个飞书文档 https://xxx.feishu.cn/wiki/ABC123def

AI:  ## 前端重构方案
     ### 目标
     - 迁移至 React 18 + TypeScript
     - 首屏加载时间 < 1.5s
     ### 进度
     1. ✅ 组件库升级
     2. ❌ 路由重构（进行中）
     ...
```

### 创建和编辑

```
You: 帮我在飞书创建一个"Q2 产品规划"文档，先写个大纲

AI:  文档已创建！
     链接：https://xxx.feishu.cn/docx/xxx
     已写入大纲：目标、时间线、里程碑、资源分配
```

```
You: 在第二章后面加一段关于竞品分析的内容

AI:  已在"时间线"章节后插入"竞品分析"段落。
```

```
You: 把文档里所有的"待定"替换成"已确认"

AI:  已替换 3 处。
```

### 追加内容

```
You: 在那个文档末尾追加今天的会议纪要

AI:  已追加"2026-03-26 会议纪要"到文档末尾。
```

### 评论和协作

```
You: 看看那篇文档有什么评论

AI:  共 3 条评论：
     1. @张三: "第二章需要补充数据"
     2. @李四: "时间线建议推迟一周"
     ...
```

```
You: 帮我回复一条评论："已更新，请再看看"

AI:  评论已添加。
```

### 更多对话场景

```
You: 帮我找一下 David 的 open_id，我要在文档里 @ 他
You: 下载那个文档里的图片
You: 浏览一下知识库里"产品文档"下面有哪些子文档
You: 把这段代码的运行结果写到飞书文档里
```

---

<details>
<summary><b>CLI 直接调用（高级用法）</b></summary>

```bash
S=scripts/feishu_mcp.py

python3 $S search-doc "周报"                                    # 搜索
python3 $S fetch-doc ABC123def                                  # 读取
python3 $S list-docs                                            # 我的文档库
python3 $S create-doc "会议纪要" "## 议题\n\n- 要点1"             # 创建
python3 $S append ABC123def "## 补充\n\n追加内容"                 # 追加
python3 $S replace ABC123def "旧内容...结尾" "新内容"             # 替换
python3 $S insert-after ABC123def "某段文字" "插入的内容"          # 插入
python3 $S delete-range ABC123def "要删除的内容"                  # 删除
python3 $S get-comments ABC123def                                # 评论
python3 $S search-user "张三"                                    # 搜索用户
python3 $S fetch-file filetoken123                               # 获取文件
```

</details>

## 工作原理

```
AI Agent ──► feishu_mcp.py ──► mcp.feishu.cn/mcp ──► 飞书云文档
               │                    (官方 MCP)
               ├─ 自动获取 TAT/UAT
               ├─ JSON-RPC 2.0
               └─ 单文件, 零依赖
```

直接调用飞书官方远程 MCP 服务，不需要部署本地 MCP 服务器，不需要 Node.js，一个 Python 脚本搞定所有事。

## 全部命令

| 命令 | 说明 |
|------|------|
| `login` | OAuth2 浏览器授权 |
| `whoami` | 查看当前 token 状态 |
| `fetch-doc <id> [offset] [limit]` | 读取文档（支持分页） |
| `search-doc <keyword>` | 搜索文档 |
| `list-docs [id]` | 浏览文档库（不传 id = 我的文档库） |
| `create-doc <title> [markdown] [location]` | 创建文档 |
| `append <id> <markdown>` | 追加内容 |
| `overwrite <id> <markdown>` | 覆盖文档 |
| `replace <id> <selection> <markdown>` | 定位替换 |
| `insert-after <id> <selection> <markdown>` | 后插入 |
| `insert-before <id> <selection> <markdown>` | 前插入 |
| `delete-range <id> <selection>` | 删除内容 |
| `get-comments <id> [all\|whole\|segment]` | 获取评论 |
| `add-comments <id> <text>` | 添加评论 |
| `get-user [open_id]` | 获取用户信息 |
| `search-user <keyword>` | 搜索用户 |
| `fetch-file <token> [media\|whiteboard]` | 获取文件/图片 |
| `call <tool> <json>` | 调用任意 MCP 工具 |

## 常见问题

<details>
<summary><b>search-doc 报错 "search:docs:read"</b></summary>

这个权限是用户身份类型，需要 UAT。运行 `python3 scripts/feishu_mcp.py login` 重新授权。
</details>

<details>
<summary><b>fetch-doc 报错 "permission denied"</b></summary>

TAT 模式下应用需要被添加为文档协作者。用 UAT（`login` 后）可以访问你有权限的所有文档。
</details>

<details>
<summary><b>login 后浏览器没反应</b></summary>

检查是否在飞书应用的安全设置中添加了重定向 URL `http://localhost:9876/callback`。
</details>

<details>
<summary><b>Token 过期了怎么办</b></summary>

脚本自动用 refresh_token 续期。如果 refresh_token 也过期（30天），重新运行 `login` 即可。
</details>

## Security

- **凭证安全** — App Secret 通过环境变量传递，不会出现在对话记录或 AI 上下文中
- **官方服务** — 所有 API 调用通过飞书官方远程 MCP 服务 (`mcp.feishu.cn`)，非第三方代理
- **本地 Token** — OAuth token 存储在本地文件中，不上传到任何外部服务
- **第三方内容** — 读取的飞书文档内容来自用户自己有权限的文档，请注意文档中可能包含不可信内容

## Contributing

Issues and PRs welcome!

## License

MIT
