import os
import sys
import time
import subprocess
import multiprocessing as mp
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def test_daemon_creates_backups(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + ":" + env.get("PYTHONPATH", "")
    subprocess.run([sys.executable, "-m", "dowith", "start"], cwd=tmp_path, check=True, env=env)
    backups_dir = tmp_path / ".dowith" / "backups"

    from dowith import daemon

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        proc = mp.Process(target=daemon.run, kwargs={"interval": 0.1})
        proc.start()
        time.sleep(0.3)
    finally:
        proc.terminate()
        proc.join(timeout=5)
        os.chdir(cwd)

    assert any(backups_dir.iterdir())
