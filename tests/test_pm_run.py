import json
import os
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run(cmd, cwd):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True, env=env)


def test_pm_creates_run_and_backup(tmp_path):
    run([sys.executable, "-m", "dowith", "start"], cwd=tmp_path)
    exchange_file = tmp_path / ".dowith" / "exchange" / "note.txt"
    exchange_file.write_text("hello", encoding="utf-8")
    runs_dir = tmp_path / ".dowith" / "runs"
    backups_dir = tmp_path / ".dowith" / "backups"
    before_runs = set(p.name for p in runs_dir.iterdir())
    before_backups = set(p.name for p in backups_dir.iterdir())
    run([sys.executable, "-m", "dowith", "pm", "--seed", "hi"], cwd=tmp_path)
    new_runs = set(p.name for p in runs_dir.iterdir()) - before_runs
    new_backups = set(p.name for p in backups_dir.iterdir()) - before_backups
    assert len(new_runs) == 1
    assert (runs_dir / next(iter(new_runs)) / "log.txt").exists()
    assert len(new_backups) == 1
    assert (backups_dir / next(iter(new_backups)) / "note.txt").exists()
    state = json.loads((tmp_path / ".dowith" / "state.json").read_text())
    assert "last_summary" in state
