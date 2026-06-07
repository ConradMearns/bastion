"""Host health agent — reports to bastion every 60 seconds."""

import os
import sys
import time
import socket
import argparse
from datetime import datetime, timezone

import httpx
import psutil
import yaml


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def collect_health() -> dict:
    """Gather system health metrics."""
    return {
        "hostname": socket.gethostname(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "uptime_seconds": time.time() - psutil.boot_time(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="Bastion health agent")
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="Path to config file"
    )
    parser.add_argument(
        "--token", help="JWT token (overrides config)"
    )
    parser.add_argument(
        "--bastion-url", help="Bastion API URL (overrides config)"
    )
    parser.add_argument(
        "--hostname", help="Hostname to report as (overrides config)"
    )
    args = parser.parse_args()

    # Load config
    cfg = load_config(args.config)
    bastion_url = (args.bastion_url or cfg["bastion_url"]).rstrip("/")
    token = args.token or cfg.get("token", "") or os.environ.get("BASTION_TOKEN", "")
    hostname = args.hostname or cfg.get("hostname", socket.gethostname())

    if not token:
        print("Error: no token provided (via --token, config.yaml, or BASTION_TOKEN env)", file=sys.stderr)
        sys.exit(1)

    print(f"Agent starting — hostname: {hostname}, bastion: {bastion_url}")

    while True:
        try:
            data = collect_health()
            data["hostname"] = hostname  # override with configured name

            resp = httpx.post(
                f"{bastion_url}/report",
                json=data,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
                verify=False,  # self-signed cert on bastion
            )
            if resp.status_code == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] OK — "
                      f"cpu={data['cpu_percent']:.0f}% mem={data['memory_percent']:.0f}% disk={data['disk_percent']:.0f}%")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error {resp.status_code}: {resp.text}", file=sys.stderr)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection error: {e}", file=sys.stderr)

        time.sleep(60)


if __name__ == "__main__":
    main()
