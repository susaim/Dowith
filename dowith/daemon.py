import argparse
import time
from .cli import _backup_exchange


def run(interval: float = 60.0) -> None:
    """Run periodic backups every ``interval`` seconds until terminated."""
    try:
        while True:
            _backup_exchange()
            time.sleep(interval)
    except KeyboardInterrupt:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=60.0)
    args = parser.parse_args()
    run(args.interval)


if __name__ == "__main__":
    main()
