下面给出 **dowith / dw** 的**完整开发文档（M1）**：含两种模式、目录结构、全部配置文件内容、三角色开箱提示词、命令与 `dw help`、版本/备份策略、命令行 UI、守护进程、工作流创建/部署、以及“让用户用网页 AI 生成角色与流程”的模板与规则。你把这份交给 Codex 就能直接做。

---

# 0. 名称与目标

* 英文名：**dowith**（命令：`dw`；别名：`dowith`）
* 目标：在\*\*非托管（handoff，默认）**或**托管（managed〈beta〉）\*\*两种模式下，用“**角色 × 工作流**”组织项目协作，并与 **Claude Code / Gemini CLI** 无缝衔接。
* 约束：**一个项目的模式创建后不可切换**。

---

# 1. 安装与运行需求

* 平台：macOS / Linux / Windows 10+
* 语言：**Python 3.11+**
* 依赖（PyPI）：`typer`（或 `click`）、`rich`、`prompt_toolkit`、`pyyaml`、`pydantic`、`watchfiles`、`python-slugify`、`unidiff`、`portalocker`、`pywinpty`（Win）/`pexpect`（Unix）
* 可选：已安装 **Claude Code CLI**（`claude`）与 **Gemini CLI**（`gemini`），用于**非托管**进入它们的交互窗；**托管**用它们的 print 模式。

---

# 2. 运行模式（项目级互斥）

* **非托管 handoff（默认）**

  * `dw` 仅做开场与交接：把**角色提示词/规则**作为**首条消息**喂入 **claude/gemini** 的**交互窗口**，后续对话都在它们里继续。
  * `dw` 负责：角色/流程/文档骨架、切回时对 `.dowith/exchange/*` 进行**自动备份**、记录最小 run 日志、快捷键**回到 dw**。
  * **注意**：**版本管理由 Claude/Gemini 侧负责**；`dw` 不做对项目代码/资产的版本控制（只备份 `.dowith/exchange/*` 与必要元数据）。
* **托管 managed〈beta〉**

  * `dw` 作为编排器，使用 `claude -p` / `gemini -p` **print 模式**流式展示，支持中断、恢复、回合推进、打补丁写文档。
  * `dw` 提供 run 级 artifacts、补丁与（可选）脚本执行白名单。

> **创建项目时选择模式，写入 `.dowith/config.yaml`，后续不可切换。**

---

# 3. 目录结构（`dw start` 后）

```
.dowith/
  config.yaml          # 模式/角色路由/后端参数/热键/备份策略
  flow.yaml            # 工作流阶段：id、绑定角色、阶段目标
  roles/               # 角色 Charter（可增删）
    pm.md
    ui.md
    dev.md
  exchange/            # 交流文档（PM/UI/DEV产出；切回时会备份）
    prd.md
    ui-spec.md
    dev-plan.md
  agents/              # （可选）用户自建智能体定义（YAML/MD）
  workflows/           # （可选）用户自建工作流（YAML）
  drafts/              # 裸 AI 草稿（`dw ai`）
  runs/
    2025-08-14T10-00-00Z/
      input.jsonl
      output.jsonl
      exchange.patch
      stdout.log
      stderr.log
  backups/
    2025-08-14T10-00-00Z/
      exchange/        # 仅备份 exchange 与必要元信息
  state.json           # 当前阶段/活跃角色/最近会话摘要
  .lock                # 并发保护
```

---

# 4. 开箱配置文件（完整示例）

## 4.1 `.dowith/config.yaml`

```yaml
# 项目创建后不可切换
mode: handoff   # handoff | managed-beta

project: MyProject

# 角色→后端路由（handoff 用于进入交互窗；managed 用于选择 print 模式后端/模型）
roles:
  pm:
    backend: gemini          # gemini | claude | local
    model: gemini-2.5-pro
    include_dirs: [".", "docs"]   # 仅 gemini: --include-directories
  ui:
    backend: claude
    model: claude-sonnet-4-latest
    add_dirs: [".", "assets"]     # 仅 claude: --add-dir
  dev:
    backend: gemini
    model: gemini-2.5-pro

# 非托管：TTY 包裹器设置与首条注入策略
handoff:
  hotkey_detach: "Ctrl+Alt+B"     # 从后端窗口脱离回到 dw
  seed_policy: role_charter       # role_charter | none
  inherit_platform_memory: false  # 不改 CLAUDE.md / GEMINI.md

# 托管：print 模式调用参数
managed:
  max_turns: 3
  per_call_timeout_sec: 600
  graceful_int_sec: 2
  inject_mode: every              # none | once | every
  allowed_tools: []               # 仅 claude: --allowedTools

# 备份策略（两种模式都生效）
backups:
  on_switch_back: true            # 每次从后端切回时，备份 exchange/*
  include: ["exchange/"]
  exclude: []
```

## 4.2 `.dowith/flow.yaml`

```yaml
phases:
  - id: pm_spec
    title: "产品需求定义"
    role: pm
    goal: "沉淀 PRD（范围/用户故事/验收/风险）并落到 exchange/prd.md"
  - id: ui_specs
    title: "UI 设计规范"
    role: ui
    goal: "产出 ui-spec.md（色彩/字体/间距/组件/页面骨架）"
  - id: dev_impl
    title: "开发实施计划"
    role: dev
    goal: "产出 dev-plan.md（任务拆分/里程碑/目录结构）"
```

## 4.3 `.dowith/roles/pm.md`（提示词/规则/自检表）

```md
# 角色：产品经理（PM）

## 使命
- 将零散想法整理为可执行的 **产品需求文档（PRD）**。
- 与 UI 与 DEV 协作，输出明确的范围、用户故事、验收清单与风险。

## 输入清单（缺一则必须追问）
- 目标用户（画像或样例）
- 核心场景（3~5 条）
- 关键约束（时间/平台/依赖/合规）
- 目标指标（如留存/时长/转化/效率）

## 产出格式（写入 exchange/prd.md）
- 《产品概述》
- 《用户画像与问题》
- 《核心场景与用户故事》
- 《信息架构与页面清单》
- 《验收标准（可被 QA/DEV 复用）》
- 《里程碑（MVP/Alpha/Beta）》
- 《风险与对策》
- 必须引用来源：来自 exchange/* 文档或用户回答（标记 “来源：xxx”）

## 风格与禁止
- 不得臆测缺失输入；必须先列“缺失信息清单”，逐项确认。
- 段落短句化，清单化，关键指标加粗。

## 自检清单
- [ ] 每个用户故事是否有验收标准？
- [ ] MVP 是否可在既定约束下完成？
- [ ] 风险有对应缓解方案？
```

## 4.4 `.dowith/roles/ui.md`

```md
# 角色：UI 工程师（UI）

## 使命
- 基于 PRD 产出 **UI 设计规范**：色彩/字体/间距/组件库/页面骨架。

## 输入清单
- PRD（exchange/prd.md）
- 品牌/可用性要求（对比度/键盘可达性/动效节制）
- 目标平台（Web/Mobile/桌面）

## 产出格式（写入 exchange/ui-spec.md）
- 《设计原则》
- 《色彩系统》（主色/语义色/状态）
- 《排版系统》（字体/字号/行高/间距）
- 《栅格与布局》
- 《组件清单》（Button/Input/Select/List/Sheet...）
- 《页面骨架与导航流》
- 《无障碍与响应式规则》

## 风格与禁止
- 所有色值和尺寸需给出 token 名称（如 `--color-primary-500`）。
- 插图/图片只给占位符说明与尺寸，不嵌入二进制。

## 自检清单
- [ ] 颜色对比度 ≥ 4.5:1
- [ ] 移动端断点覆盖 320/375/414/768/1024
- [ ] 组件 API 是否稳定且可复用？
```

## 4.5 `.dowith/roles/dev.md`

```md
# 角色：开发工程师（DEV）

## 使命
- 生成 **实施计划** 与 **目录/任务拆分**，确保可落地。

## 输入清单
- PRD（exchange/prd.md）
- UI 规范（exchange/ui-spec.md）
- 技术约束（语言/框架/部署/CI）

## 产出格式（写入 exchange/dev-plan.md）
- 《技术选型与目录结构》
- 《子系统与接口清单》
- 《任务拆分（按周里程碑）》
- 《开发规范》（分支命名/提交规范/代码风格）
- 《测试策略》（单测/集成/e2e）
- 《风险与试错计划》

## 风格与禁止
- 避免伪代码海量堆砌；优先结构化清单与表格。
- 若缺输入，先列缺失项并请求补齐后再输出。

## 自检清单
- [ ] 每个任务是否有完成定义（DoD）？
- [ ] 每个接口是否有错误处理与超时？
- [ ] 是否规划最小可演示路径（dev server/preview）？
```

---

# 5. 命令行 UI 与守护进程

## 5.1 CLI 视觉规范

* **Rich** 渲染：

  * 顶部**状态栏**：`[role] [phase] [backend/model] [mode] [elapsed]`
  * 主区分块：输入摘要 / 产出摘要 / 文件写入 / 备份路径
  * 颜色：pm=蓝、ui=紫、dev=青、warning=黄、error=红
* **TTY 包裹器**：进入后端时在 PTY 内运行；热键 **`Ctrl+Alt+B`** 脱附回 `dw`（不杀会话）。

## 5.2 守护进程（可选）

* 命令：`dw daemon start|stop|status`
* 职责：

  * 监听 `.dowith/state.json` 变更，记录最近活跃角色与阶段
  * 捕捉从 PTY 脱附事件，触发**自动备份 exchange/**
  * 定时巡检 `.lock` 防止并行执行
* 实现：`watchfiles` + 本地 Unix domain socket / Windows Named Pipe。

---

# 6. 备份与版本策略

## 6.1 非托管（handoff，默认）

* **不做代码/资产版本管理**；由 **Claude/Gemini** 自己的机制或 Git 负责。
* **每次从后端“切回 dw”时**，自动执行：

  * 仅备份 **`.dowith/exchange/*`** 到 `.dowith/backups/<ts>/exchange/`
  * 写入 `.dowith/runs/<ts>/stdout.log`（本次会话摘要）
* 首次使用和每次备份后，**明确提示**：

  > “非托管模式不管理项目版本；仅备份 `exchange/*`。代码与其他资产请用 Git 或后端工具自行管理。”

## 6.2 托管（managed〈beta〉）

* `runs/<ts>/exchange.patch` + 自动应用/回滚
* `dw backup make|list|restore` 对 `exchange/*` 做时间点恢复
* （可选）与 Git 钩子集成：在 `dw run` 前后调用 `git stash/commit`（默认关闭）

---

# 7. 核心命令与 `dw help`

## 7.1 顶级帮助（示例输出）

```
$ dw help
dowith (dw) — Role & Workflow Orchestrator for Claude/Gemini

USAGE
  dw start [--name <project>]        初始化当前目录的 .dowith/，选择模式 handoff|managed-beta
  dw status                           查看当前阶段/活跃角色/后端/模式
  dw roles                            列出角色与路由
  dw <role> [message]                 进入该角色（handoff: 打开后端交互；managed: 在 dw 中运行）
  dw do [message]                     与当前活跃角色继续对话/执行
  dw next | back                      流程前进/回退
  dw ai [message]                     裸 AI 通道（不注入规则，不写 exchange）
  dw goin <claude|gemini> [--role r]  直接进入指定后端，选填角色种子
  dw daemon start|stop|status         守护进程管理
  dw backup make|list|restore <id>    备份/恢复（默认仅 exchange/*）
  dw flow ls|add|rm|mv|init           工作流管理（读写 .dowith/flow.yaml）
  dw role ls|add|edit|rm              角色管理（读写 .dowith/roles/*.md）
  dw agent build|deploy               从 .dowith/agents/* 构建/部署角色包装
  dw workflow build|deploy            从 .dowith/workflows/* 构建/部署工作流
  dw docs                             打开文档索引（命令用法与模板）

TIPS
  • handoff 模式下，按 Ctrl+Alt+B 可从后端窗口“脱附”回到 dw。
  • 非托管不做项目版本管理；仅在切回时备份 exchange/*。
```

---

# 8. 工作流与智能体：创建 / 修改 / 部署

## 8.1 通过命令创建

* 快速初始化一条标准流：

  ```
  dw flow init pm-ui-dev
  ```

  生成 `flow.yaml` 的三阶段骨架（若已有则提示合并或备份）。

* 添加/调整阶段：

  ```
  dw flow add review --role pm --after dev_impl --goal "版本复查与发布计划"
  dw flow mv review --before dev_impl
  dw flow rm review
  ```

* 新建/导入角色：

  ```
  dw role add qa               # 生成 .dowith/roles/qa.md 模板
  dw role edit pm              # 用 $EDITOR 打开
  dw role rm ui
  ```

## 8.2 通过文件“写好再部署”（更强）

* 目录与格式约定：

  * `.dowith/agents/<name>.yaml`：单个智能体的**配置**（后端路由/模型/上下文源/入口提示等）。
  * `.dowith/workflows/<name>.yaml`：一条工作流（阶段图 + 每阶段入口提示/校验）。
* 部署命令：

  ```
  dw agent deploy <name>       # 校验并写入 config.yaml/roles/*.md
  dw workflow deploy <name>    # 校验并写入 flow.yaml
  ```
* 校验项：必填字段、角色是否存在、后端是否可用、与当下模式是否冲突（例如 managed 才允许注入 every）。

### `.dowith/agents/pm.yaml`（示例）

```yaml
name: pm
backend: gemini
model: gemini-2.5-pro
include_dirs: [".", "docs"]
charter_file: roles/pm.md
seed_policy: role_charter
```

### `.dowith/workflows/pm-ui-dev.yaml`（示例）

```yaml
name: pm-ui-dev
phases:
  - id: pm_spec
    role: pm
    goal: "产出 PRD 至 exchange/prd.md"
  - id: ui_specs
    role: ui
    goal: "产出 UI 规范至 exchange/ui-spec.md"
  - id: dev_impl
    role: dev
    goal: "产出开发计划至 exchange/dev-plan.md"
```

---

# 9. 让“网页 AI”来写角色与流程（无需本地后端）

## 9.1 角色 Charter 生成模板（贴给任意网页 AI）

```
你是我的角色卡生成器。请输出 Markdown，字段与顺序严格如下：
# 角色：<中文名>（<英文代号>）
## 使命
- <3~5条>
## 输入清单
- <必需输入项；缺一则必须追问>
## 产出格式（目标文件路径）
- 写入 <exchange/<file>.md>，包含 <章节清单>
## 风格与禁止
- <风格>
- <禁止>
## 自检清单
- [ ] <检查项1>
- [ ] <检查项2>
```

把生成的文档保存为 `.dowith/roles/<代号>.md`；再执行：

```
dw role add <代号> --from .dowith/roles/<代号>.md
```

## 9.2 工作流生成模板

```
请基于以下角色代号生成 YAML 工作流，字段固定：
name: <workflow-name>
phases:
  - id: <snake_case>
    role: <role_code>
    goal: "<一句话阶段目标>"
  - ...
```

保存为 `.dowith/workflows/<name>.yaml`，再：

```
dw workflow deploy <name>
```

---

# 10. 交互范例（非托管主路径）

```bash
dw start                 # 选择 2=handoff（推荐）
dw roles                 # 看默认映射：pm→gemini, ui→claude, dev→gemini
dw pm                    # 进入 gemini，自动发送“我是PM，本轮要做……”
# PM 完成后按 Ctrl+Alt+B 回到 dw（会自动备份 exchange/*）
dw next                  # 切到 ui_specs
dw ui                    # 进入 claude，自动发 UI 角色开场
dw next
dw dev
```

---

# 11. 托管（managed〈beta〉）要点（若启用）

* `dw <role>` / `dw do`：在 `dw` 控制台流式执行
* 注入策略：`none/once/every`；默认 `every`
* 中断/恢复：`dw break` / `dw resume`
* 工件：`runs/<ts>/input.jsonl|output.jsonl|exchange.patch`
* 安全：`allowed_tools` 白名单（Claude 专用）
* 超时/回合：`per_call_timeout_sec` / `max_turns`

---

# 12. 实现说明（给 Codex）

## 12.1 组件划分

* `core/agent.py`：角色上下文拼装（charter + 平台提示 + 用户消息）
* `core/planner.py`：状态机（phase/role/next/back）；非托管仅改状态
* `core/bus.py`：事件总线（切换/切回/备份/错误）
* `core/exchange.py`：`exchange/*.md` 读写/校验/patch
* `core/runio.py`：子进程/PTY 封装（`pexpect`/`pywinpty`），`Ctrl+Alt+B` 脱附
* `core/state.py`：`state.json` 读写；`.lock` 并发保护
* `backends/claude_code.py`：启动交互 / print 模式；flag 映射
* `backends/gemini_cli.py`：同上
* `utils/render.py`：Rich 布局与主题
* `utils/files.py`：原子写、快照、过滤备份
* `configs/schema.py`：`config.yaml`/`flow.yaml`/agents/workflows 的 pydantic 校验

## 12.2 关键行为

* **非托管进入**：

  * 解析路由 → 生成**首条种子**（按 `seed_policy` 从 `roles/<role>.md` 提炼“使命/输入缺失问答/产出要求”）
  * 以 PTY 启动：`claude "<seed>" --model ... --add-dir ...` 或 `gemini`（随后写入 `<seed>`）
  * 记录 `runs/<ts>/stdout.log` 首屏与摘要
* **切回触发备份**：

  * 守护进程或 PTY hook 捕捉脱附 → 拷贝 `exchange/*` 到 `backups/<ts>/exchange/`
  * 控制台黄色提示“非托管不管理项目版本，仅已备份 exchange/\*”
* **托管调用**：

  * `claude -p --output-format stream-json --model ... --max-turns N`
  * `gemini -p -m ... [--include-directories ...]`
  * 流式解析 → `exchange.patch` → 校验/应用

---

# 13. 用户第一次使用时的“确认/提醒点”

1. `dw start`：选择模式（默认 handoff），**不可更改**。
2. `dw roles`：检查角色→后端映射是否符合预期。
3. 首次进入某角色时：提示**回切热键**、**备份提示**（handoff）。
4. `dw next` 首次使用：提示当前阶段目标与产出路径。
5. 如果 `.dowith/agents/*` 或 `workflows/*` 存在：建议运行 `dw agent deploy` / `dw workflow deploy` 同步。

---

# 14. 常见问题（对用户的原话提示）

* **Q：为什么我回到 dw 时只看到 exchange 被备份？**
  A：你在**非托管**模式。项目代码与其他资产的版本请用 Git 或后端自带功能。`dw` 只备份 exchange 文档，避免与后端冲突。
* **Q：可以改成托管吗？**
  A：项目创建后不可切换。新建目录再 `dw start` 选择 managed〈beta〉。
* **Q：我想用网页 AI 生成一个“需求评审官”角色？**
  A：按第 9 章的模板生成 `.md` 放到 `.dowith/roles/`，再 `dw role add/import`。

---

这份开发文档涵盖：模式、目录、配置、三角色提示词、命令与帮助、CLI UI、守护进程、备份/版本策略、工作流/智能体的创建与部署、以及“用网页 AI 生成角色与工作流”的模板。
如果你要，我可以**进一步输出开箱仓库骨架（代码与这些模板文件）**，直接 `pipx install -e .` 就能跑。
