import os
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def run(cmd, cwd):
    env = os.environ.copy()
    env['PYTHONPATH'] = str(REPO_ROOT)
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True, env=env)


def test_role_add_and_flow_ls(tmp_path):
    run([sys.executable, '-m', 'dowith', 'start'], cwd=tmp_path)
    role_file = tmp_path / 'qa.md'
    role_file.write_text('# QA role', encoding='utf-8')
    run([sys.executable, '-m', 'dowith', 'role', 'add', 'qa', '--from', str(role_file)], cwd=tmp_path)
    assert (tmp_path / '.dowith' / 'roles' / 'qa.md').exists()
    res = run([sys.executable, '-m', 'dowith', 'role', 'ls'], cwd=tmp_path)
    assert 'qa' in res.stdout
    res = run([sys.executable, '-m', 'dowith', 'flow', 'ls'], cwd=tmp_path)
    assert 'pm_spec' in res.stdout
