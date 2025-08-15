import os
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run(cmd, cwd):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + ":" + env.get("PYTHONPATH", "")
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True, env=env)


def _replace_backend(cfg_path: Path, backend: str):
    text = cfg_path.read_text()
    # replace the first backend occurrence for pm role
    text = text.replace("backend: gemini", f"backend: {backend}")
    cfg_path.write_text(text)


def test_run_backend_uses_configured_cli(tmp_path):
    run([sys.executable, "-m", "dowith", "start"], cwd=tmp_path)
    cfg = tmp_path / ".dowith" / "config.yaml"
    _replace_backend(cfg, "cat")
    res = run([sys.executable, "-m", "dowith", "pm", "--seed", "hello"], cwd=tmp_path)
    assert "hello" in res.stdout
    log = next((tmp_path / ".dowith" / "runs").rglob("log.txt"))
    content = log.read_text()
    assert "backend: cat" in content
    assert "stdout:\nhello" in content


def test_run_backend_falls_back_to_echo(tmp_path):
    run([sys.executable, "-m", "dowith", "start"], cwd=tmp_path)
    cfg = tmp_path / ".dowith" / "config.yaml"
    _replace_backend(cfg, "nonexistentcmd")
    res = run([sys.executable, "-m", "dowith", "pm", "--seed", "hi"], cwd=tmp_path)
    assert "hi" in res.stdout  # fallback still echoes
    log = next((tmp_path / ".dowith" / "runs").rglob("log.txt"))
    content = log.read_text()
    assert "backend: echo" in content
