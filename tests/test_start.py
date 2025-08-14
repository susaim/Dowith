import json
import subprocess
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def run(cmd, cwd):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(REPO_ROOT)
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True, env=env)


def test_start_creates_structure(tmp_path):
    run([sys.executable, '-m', 'dowith', 'start', '--name', 'Demo', '--mode', 'managed-beta'], cwd=tmp_path)
    base = tmp_path / '.dowith'
    cfg = base / 'config.yaml'
    assert cfg.exists()
    assert 'mode: managed-beta' in cfg.read_text()
    assert (base / 'flow.yaml').exists()
    assert (base / 'roles' / 'pm.md').exists()
    assert (base / 'roles' / 'ui.md').exists()
    assert (base / 'roles' / 'dev.md').exists()
    assert (base / 'agents').exists()
    assert (base / 'workflows').exists()
    assert (base / 'drafts').exists()
    assert (base / '.lock').exists()
    assert json.loads((base / 'state.json').read_text()) == {'phase': 'pm_spec', 'role': 'pm'}
