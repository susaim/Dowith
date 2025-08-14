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
    run([sys.executable, '-m', 'dowith', 'start', '--name', 'Demo'], cwd=tmp_path)
    base = tmp_path / '.dowith'
    assert (base / 'config.yaml').exists()
    assert (base / 'flow.yaml').exists()
    assert (base / 'roles' / 'pm.md').exists()
    assert (base / 'roles' / 'ui.md').exists()
    assert (base / 'roles' / 'dev.md').exists()
    assert json.loads((base / 'state.json').read_text()) == {'phase': 'pm_spec', 'role': 'pm'}
