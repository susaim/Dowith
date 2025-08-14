import json
import subprocess
import datetime
from pathlib import Path
import shutil
import typer

APP_DIR = Path('.dowith')
app = typer.Typer(help="dowith (dw) — Role & Workflow Orchestrator for Claude/Gemini")

DEFAULT_CONFIG = """mode: {mode}
project: {project}
roles:
  pm:
    backend: gemini
    model: gemini-2.5-pro
  ui:
    backend: claude
    model: claude-sonnet-4-latest
  dev:
    backend: gemini
    model: gemini-2.5-pro
handoff:
  hotkey_detach: \"Ctrl+Alt+B\"
  seed_policy: role_charter
  inherit_platform_memory: false
managed:
  max_turns: 3
  per_call_timeout_sec: 600
  graceful_int_sec: 2
  inject_mode: every
  allowed_tools: []
backups:
  on_switch_back: true
  include: [\"exchange/\"]
  exclude: []
"""

DEFAULT_FLOW = """phases:
  - id: pm_spec
    title: \"产品需求定义\"
    role: pm
    goal: \"沉淀 PRD（范围/用户故事/验收/风险）并落到 exchange/prd.md\"
  - id: ui_specs
    title: \"UI 设计规范\"
    role: ui
    goal: \"产出 ui-spec.md（色彩/字体/间距/组件/页面骨架）\"
  - id: dev_impl
    title: \"开发实施计划\"
    role: dev
    goal: \"产出 dev-plan.md（任务拆分/里程碑/目录结构）\"
"""

ROLE_PM = """# 角色：产品经理（PM）\n\n## 使命\n- 将零散想法整理为可执行的 **产品需求文档（PRD）**。\n- 与 UI 与 DEV 协作，输出明确的范围、用户故事、验收清单与风险。\n\n## 输入清单（缺一则必须追问）\n- 目标用户（画像或样例）\n- 核心场景（3~5 条）\n- 关键约束（时间/平台/依赖/合规）\n- 目标指标（如留存/时长/转化/效率）\n\n## 产出格式（写入 exchange/prd.md）\n- 《产品概述》\n- 《用户画像与问题》\n- 《核心场景与用户故事》\n- 《信息架构与页面清单》\n- 《验收标准（可被 QA/DEV 复用）》\n- 《里程碑（MVP/Alpha/Beta）》\n- 《风险与对策》\n- 必须引用来源：来自 exchange/* 文档或用户回答（标记 “来源：xxx”）\n\n## 风格与禁止\n- 不得臆测缺失输入；必须先列“缺失信息清单”，逐项确认。\n- 段落短句化，清单化，关键指标加粗。\n\n## 自检清单\n- [ ] 每个用户故事是否有验收标准？\n- [ ] MVP 是否可在既定约束下完成？\n- [ ] 风险有对应缓解方案？\n"""

ROLE_UI = """# 角色：UI 工程师（UI）\n\n## 使命\n- 基于 PRD 产出 **UI 设计规范**：色彩/字体/间距/组件库/页面骨架。\n\n## 输入清单\n- PRD（exchange/prd.md）\n- 品牌/可用性要求（对比度/键盘可达性/动效节制）\n- 目标平台（Web/Mobile/桌面）\n\n## 产出格式（写入 exchange/ui-spec.md）\n- 《设计原则》\n- 《色彩系统》（主色/语义色/状态）\n- 《排版系统》（字体/字号/行高/间距）\n- 《栅格与布局》\n- 《组件清单》（Button/Input/Select/List/Sheet...）\n- 《页面骨架与导航流》\n- 《无障碍与响应式规则》\n\n## 风格与禁止\n- 所有色值和尺寸需给出 token 名称（如 `--color-primary-500`）。\n- 插图/图片只给占位符说明与尺寸，不嵌入二进制。\n\n## 自检清单\n- [ ] 颜色对比度 ≥ 4.5:1\n- [ ] 移动端断点覆盖 320/375/414/768/1024\n- [ ] 组件 API 是否稳定且可复用？\n"""

ROLE_DEV = """# 角色：开发工程师（DEV）\n\n## 使命\n- 生成 **实施计划** 与 **目录/任务拆分**，确保可落地。\n\n## 输入清单\n- PRD（exchange/prd.md）\n- UI 规范（exchange/ui-spec.md）\n- 技术约束（语言/框架/部署/CI）\n\n## 产出格式（写入 exchange/dev-plan.md）\n- 《技术选型与目录结构》\n- 《子系统与接口清单》\n- 《任务拆分（按周里程碑）》\n- 《开发规范》（分支命名/提交规范/代码风格）\n- 《测试策略》（单测/集成/e2e）\n- 《风险与试错计划》\n\n## 风格与禁止\n- 避免伪代码海量堆砌；优先结构化清单与表格。\n- 若缺输入，先列缺失项并请求补齐后再输出。\n\n## 自检清单\n- [ ] 每个任务是否有完成定义（DoD）？\n- [ ] 每个接口是否有错误处理与超时？\n- [ ] 是否规划最小可演示路径（dev server/preview）？\n"""

@app.command()

def start(
    name: str = typer.Option("MyProject", "--name", help="project name"),
    mode: str = typer.Option(
        "handoff",
        "--mode",
        help="execution mode",
        case_sensitive=False,
        show_default=True,
        callback=None,
    ),
):
    """Initialize .dowith directory with defaults."""
    mode = mode.lower()
    if mode not in {"handoff", "managed-beta"}:
        typer.echo("mode must be 'handoff' or 'managed-beta'")
        raise typer.Exit(code=1)

    if APP_DIR.exists():
        typer.echo(".dowith already exists")
        raise typer.Exit(code=1)
    APP_DIR.mkdir(parents=True)
    # required directories
    for d in [
        "roles",
        "exchange",
        "agents",
        "workflows",
        "drafts",
        "runs",
        "backups",
    ]:
        (APP_DIR / d).mkdir()
    # sentinel lock file
    (APP_DIR / ".lock").touch()
    # config
    (APP_DIR / "config.yaml").write_text(
        DEFAULT_CONFIG.format(project=name, mode=mode), encoding="utf-8"
    )
    # flow
    (APP_DIR / "flow.yaml").write_text(DEFAULT_FLOW, encoding="utf-8")
    # roles
    (APP_DIR / "roles" / "pm.md").write_text(ROLE_PM, encoding="utf-8")
    (APP_DIR / "roles" / "ui.md").write_text(ROLE_UI, encoding="utf-8")
    (APP_DIR / "roles" / "dev.md").write_text(ROLE_DEV, encoding="utf-8")
    # exchange placeholders
    (APP_DIR / "exchange" / "prd.md").touch()
    (APP_DIR / "exchange" / "ui-spec.md").touch()
    (APP_DIR / "exchange" / "dev-plan.md").touch()
    # state
    (APP_DIR / "state.json").write_text(
        json.dumps({"phase": "pm_spec", "role": "pm"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    typer.echo(f"initialized .dowith ({mode})")
@app.command()
def roles():
    """List roles and backends from config."""
    cfg_file = APP_DIR / "config.yaml"
    if not cfg_file.exists():
        typer.echo("No .dowith/config.yaml found")
        raise typer.Exit(code=1)
    import yaml
    data = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    roles = data.get("roles", {})
    for name, info in roles.items():
        backend = info.get("backend", "?")
        typer.echo(f"{name}: {backend}")

@app.command()
def status():
    """Show current phase and role."""
    state_file = APP_DIR / "state.json"
    if not state_file.exists():
        typer.echo("No state.json found. Did you run dw start?")
        raise typer.Exit(code=1)
    state = json.loads(state_file.read_text(encoding="utf-8"))
    typer.echo(f"phase: {state.get('phase')} role: {state.get('role')}")


role_app = typer.Typer(help="role management")
app.add_typer(role_app, name="role")


@role_app.command("add")
def role_add(name: str, from_path: Path = typer.Option(..., "--from", exists=True, readable=True, help="source file")):
    roles_dir = APP_DIR / "roles"
    if not roles_dir.exists():
        typer.echo("No roles directory. Run dw start first")
        raise typer.Exit(code=1)
    target = roles_dir / f"{name}.md"
    if target.exists():
        typer.echo(f"role {name} already exists")
        raise typer.Exit(code=1)
    shutil.copy(from_path, target)
    typer.echo(f"added role {name}")


@role_app.command("ls")
def role_ls():
    roles_dir = APP_DIR / "roles"
    if not roles_dir.exists():
        typer.echo("No roles directory. Run dw start first")
        raise typer.Exit(code=1)
    for p in sorted(roles_dir.glob("*.md")):
        typer.echo(p.stem)


flow_app = typer.Typer(help="flow management")
app.add_typer(flow_app, name="flow")


@flow_app.command("ls")
def flow_ls():
    import yaml
    flow_file = APP_DIR / "flow.yaml"
    if not flow_file.exists():
        typer.echo("No flow.yaml found. Run dw start first")
        raise typer.Exit(code=1)
    data = yaml.safe_load(flow_file.read_text(encoding="utf-8")).get("phases", [])
    for p in data:
        typer.echo(f"{p.get('id')}: {p.get('role')}")


def _load_flow_and_state():
    import yaml
    flow_file = APP_DIR / "flow.yaml"
    state_file = APP_DIR / "state.json"
    if not flow_file.exists() or not state_file.exists():
        typer.echo("Missing flow.yaml or state.json. Did you run dw start?")
        raise typer.Exit(code=1)
    flow = yaml.safe_load(flow_file.read_text(encoding="utf-8")).get("phases", [])
    state = json.loads(state_file.read_text(encoding="utf-8"))
    return flow, state, state_file


@app.command()
def next():
    """Advance to next phase in flow."""
    flow, state, state_file = _load_flow_and_state()
    ids = [p.get("id") for p in flow]
    try:
        idx = ids.index(state.get("phase"))
    except ValueError:
        typer.echo("Current phase not found in flow.yaml")
        raise typer.Exit(code=1)
    if idx + 1 >= len(flow):
        typer.echo("Already at final phase")
        raise typer.Exit()
    nxt = flow[idx + 1]
    state["phase"] = nxt.get("id")
    state["role"] = nxt.get("role")
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"phase: {state['phase']} role: {state['role']}")


@app.command()
def back():
    """Go back to previous phase in flow."""
    flow, state, state_file = _load_flow_and_state()
    ids = [p.get("id") for p in flow]
    try:
        idx = ids.index(state.get("phase"))
    except ValueError:
        typer.echo("Current phase not found in flow.yaml")
        raise typer.Exit(code=1)
    if idx == 0:
        typer.echo("Already at first phase")
        raise typer.Exit()
    prev = flow[idx - 1]
    state["phase"] = prev.get("id")
    state["role"] = prev.get("role")
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"phase: {state['phase']} role: {state['role']}")


def _backup_exchange() -> Path:
    """Copy exchange/ to backups/<timestamp>/ and return path."""
    exchange_dir = APP_DIR / "exchange"
    if not exchange_dir.exists():
        raise RuntimeError("exchange directory missing")
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = APP_DIR / "backups" / ts
    shutil.copytree(exchange_dir, target)
    return target


def _run_backend(role: str, seed: str) -> None:
    """Simulate backend interaction for role and log output."""
    import yaml
    cfg_file = APP_DIR / "config.yaml"
    if not cfg_file.exists():
        typer.echo("No .dowith/config.yaml found")
        raise typer.Exit(code=1)
    data = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    role_cfg = data.get("roles", {}).get(role)
    if not role_cfg:
        typer.echo(f"role {role} not found in config")
        raise typer.Exit(code=1)
    backend = role_cfg.get("backend", "echo")
    proc = subprocess.run(["echo", seed], capture_output=True, text=True)
    stdout = proc.stdout
    stderr = proc.stderr
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = APP_DIR / "runs" / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "log.txt").write_text(
        f"role: {role}\nbackend: {backend}\nseed: {seed}\nstdout:\n{stdout}\nstderr:\n{stderr}",
        encoding="utf-8",
    )
    # update state summary
    state_file = APP_DIR / "state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state["last_summary"] = stdout.strip()[:200]
        state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    # backup
    try:
        _backup_exchange()
        typer.echo("backup saved")
    except Exception as e:
        typer.echo(f"backup failed: {e}")
    if stdout:
        typer.echo(stdout.strip())


def _register_role_commands() -> None:
    """Register top-level commands for each role in config."""
    cfg_file = APP_DIR / "config.yaml"
    if not cfg_file.exists():
        return
    import yaml
    data = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
    for role_name in data.get("roles", {}).keys():
        def _make_cmd(name: str):
            @app.command(name=name)
            def _cmd(seed: str = typer.Option("", "--seed", help="seed message")):
                _run_backend(name, seed)
        _make_cmd(role_name)


_register_role_commands()

if __name__ == "__main__":
    app()
