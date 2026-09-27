"""
🚀 Master Process Runner for Social Hub Ecosystem
Launches all microservices in parallel with robust process management,
pre-flight port checking, automatic cleanup on exit, and browser auto-open support.

Services Managed:
- Social Hub (FastAPI Planner & Analytics): http://localhost:8000
- Insta+Facebook Uploader (FastAPI):       http://localhost:8001
- Threads Uploader (FastAPI):              http://localhost:8002
- YouTube Shorts Uploader (FastAPI):       http://localhost:8003
- new-lyrics-2 (Express Studio):           http://localhost:3000
"""

import os
import sys
import time
import socket
import signal
import atexit
import argparse
import subprocess
import webbrowser
import threading
import json
import urllib.request
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent

SERVICES = [
    {
        "name": "Social Hub (Planner & Analytics)",
        "port": 8000,
        "cwd": ROOT_DIR / "social-hub",
        "cmd": [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000", "--reload"]
    },
    {
        "name": "Instagram + Facebook Uploader",
        "port": 8001,
        "cwd": ROOT_DIR / "Insta+Facebook uploader",
        "cmd": [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8001", "--reload"]
    },
    {
        "name": "Threads Uploader",
        "port": 8002,
        "cwd": ROOT_DIR / "threads uploader",
        "cmd": [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8002", "--reload"]
    },
    {
        "name": "YouTube Shorts Uploader",
        "port": 8003,
        "cwd": ROOT_DIR / "ytuploader",
        "cmd": [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8003", "--reload"]
    },
    {
        "name": "new-lyrics-2 (Web Studio)",
        "port": 3000,
        "cwd": ROOT_DIR / "new-lyrics-2",
        "cmd": ["npm", "run", "dev"] if os.name != 'nt' else ["cmd", "/c", "npm run dev"]
    }
]

processes = []
_cleaned_up = False


def is_port_in_use(port: int) -> bool:
    """Checks if a local TCP port is already open/bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def kill_process_on_port(port: int):
    """Finds and terminates any stale process bound to the given port."""
    if sys.platform == "win32":
        try:
            cmd = f'powershell -NoProfile -Command "(Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue).OwningProcess"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            pids = set(result.stdout.strip().split())
            for pid_str in pids:
                if pid_str.isdigit():
                    pid = int(pid_str)
                    if pid > 4:
                        print(f"   ⚠️ Port {port} occupied by PID {pid}. Cleaning up...", flush=True)
                        subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, capture_output=True)
                        time.sleep(0.5)
        except Exception:
            pass


def terminate_process_tree(proc):
    """Gracefully and forcefully terminates a process and all its children."""
    if proc is None or proc.poll() is not None:
        return
    pid = proc.pid
    if sys.platform == "win32":
        try:
            subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, capture_output=True)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    else:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def stop_all_services():
    """Cleanup hook to stop all background processes."""
    global _cleaned_up
    if _cleaned_up or not processes:
        return
    _cleaned_up = True
    print("\n🛑 Stopping all services...", flush=True)
    for svc, p in processes:
        print(f"   Terminating {svc['name']} (PID: {p.pid})...", flush=True)
        terminate_process_tree(p)
    print("✅ All services stopped.\n", flush=True)


def handle_exit_signal(sig, frame):
    stop_all_services()
    sys.exit(0)


atexit.register(stop_all_services)
try:
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)
except Exception:
    pass


def main():
    parser = argparse.ArgumentParser(description="Master Process Runner for Social Hub Ecosystem")
    parser.add_argument("--web", "-w", action="store_true", help="Automatically open web dashboard in default browser")
    args = parser.parse_args()

    print("=" * 65, flush=True)
    print("🚀 Starting Social Hub & Publishing Ecosystem...", flush=True)
    print("=" * 65, flush=True)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    # Pre-flight port verification
    print("🔍 Pre-flight check: verifying port availability...", flush=True)
    for svc in SERVICES:
        port = svc["port"]
        if is_port_in_use(port):
            kill_process_on_port(port)
            time.sleep(0.5)
            if is_port_in_use(port):
                print(f"   ⚠️ Warning: Port {port} ({svc['name']}) is still reported busy.", flush=True)
            else:
                print(f"   ✅ Port {port} freed.", flush=True)
        else:
            print(f"   ✅ Port {port} available.", flush=True)

    print("\n📦 Launching microservices...", flush=True)
    for svc in SERVICES:
        print(f"   👉 Launching {svc['name']} on port {svc['port']}...", flush=True)
        p = subprocess.Popen(
            svc["cmd"],
            cwd=str(svc["cwd"]),
            env=env,
            shell=False
        )
        processes.append((svc, p))
        time.sleep(1)

    print("\n" + "=" * 65, flush=True)
    print("✅ All services initiated! Access points:", flush=True)
    print("   • Metricool Planner & Analytics: http://localhost:8000")
    print("   • new-lyrics-2 Studio:           http://localhost:3000")
    print("   • Instagram/FB Uploader Docs:    http://localhost:8001/docs")
    print("   • Threads Uploader Docs:         http://localhost:8002/docs")
    print("   • YouTube Shorts Uploader Docs:  http://localhost:8003/docs")
    print("=" * 65, flush=True)
    print("Press Ctrl+C to safely stop all services.\n", flush=True)

    def auto_refresh_status_worker():
        """Waits for microservices to spin up, then auto-refreshes and prints verified account status."""
        time.sleep(4)
        for attempt in range(5):
            try:
                req = urllib.request.Request(
                    "http://127.0.0.1:8000/api/accounts/status",
                    headers={"User-Agent": "SocialHubServerInit/1.0"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        accounts = data.get("all_accounts", [])
                        if accounts:
                            print("\n" + "─" * 65, flush=True)
                            print("🔄 Automatic Account Status Refresh on Startup:", flush=True)
                            for acc in accounts:
                                handle = acc.get("handle")
                                plat = acc.get("platform", "").capitalize()
                                status = acc.get("status_label", "Unknown")
                                is_auth = acc.get("is_authenticated", False)
                                icon = "✅" if (is_auth and acc.get("status") == "verified") else "⚠️"
                                print(f"   {icon} @{handle} [{plat}]: {status}", flush=True)
                            print("─" * 65 + "\n", flush=True)
                            return
            except Exception:
                time.sleep(2)

    threading.Thread(target=auto_refresh_status_worker, daemon=True).start()

    if args.web:
        print("🌐 Opening Metricool Planner dashboard in browser...", flush=True)
        time.sleep(1.5)
        try:
            webbrowser.open("http://localhost:8000")
        except Exception as e:
            print(f"Could not open browser: {e}", flush=True)

    try:
        while True:
            # Health monitoring
            for svc, p in processes:
                code = p.poll()
                if code is not None:
                    print(f"⚠️ Service '{svc['name']}' exited unexpectedly with code {code}!", flush=True)
            time.sleep(2)
    except KeyboardInterrupt:
        stop_all_services()


if __name__ == "__main__":
    main()
