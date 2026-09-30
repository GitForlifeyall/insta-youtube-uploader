import os
import sys
import json
import time
import asyncio
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Resolve root ytuploader directory
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "upload files"
WEB_DIR = BASE_DIR / "web"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="YouTube Shorts Redroid Studio", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import threading
from typing import Optional, Dict, Any, List, Callable

# Global State
class UploadManager:
    def __init__(self):
        self.active_process: Optional[subprocess.Popen] = None
        self.active_job_info: Optional[Dict[str, Any]] = None
        self.log_history: List[str] = []
        self.max_history: int = 5000
        self.connected_websockets: List[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect_ws(self, ws: WebSocket):
        await ws.accept()
        self.connected_websockets.append(ws)
        # Send history on connect
        for line in self.log_history[-300:]:
            try:
                await ws.send_text(line)
            except Exception:
                pass

    def disconnect_ws(self, ws: WebSocket):
        if ws in self.connected_websockets:
            self.connected_websockets.remove(ws)

    async def broadcast_log(self, text: str):
        self.log_history.append(text)
        if len(self.log_history) > self.max_history:
            self.log_history.pop(0)

        dead_sockets = []
        for ws in self.connected_websockets:
            try:
                await ws.send_text(text)
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            self.disconnect_ws(ws)


def stream_process(cmd: List[str], prefix: str = "", on_exit: Optional[Callable[[int], Any]] = None, track_as_active: bool = False):
    loop = asyncio.get_running_loop()

    def _worker():
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="ignore",
                cwd=str(BASE_DIR)
            )
            if track_as_active:
                manager.active_process = proc

            for line in iter(proc.stdout.readline, ''):
                if line:
                    formatted = f"[{prefix}] {line}" if prefix else line
                    asyncio.run_coroutine_threadsafe(manager.broadcast_log(formatted), loop)

            proc.wait()
            code = proc.returncode
            if on_exit:
                asyncio.run_coroutine_threadsafe(on_exit(code), loop)
        except Exception as e:
            asyncio.run_coroutine_threadsafe(manager.broadcast_log(f"[ERROR] Process failed: {e}\n"), loop)
            if on_exit:
                asyncio.run_coroutine_threadsafe(on_exit(1), loop)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


manager = UploadManager()


def get_pause_flag_path(account: str) -> Path:
    return Path(tempfile.gettempdir()) / f"redroid_pause_{account}.flag"


def resolve_port(account: str) -> int:
    acc = account.strip().lower()
    if "alpha" in acc or acc in ["brand_01", "brand-01", "5555"]:
        return 5555
    if acc.isdigit():
        num = int(acc)
        return 5800 + num if num < 5000 else num
    return 5555


def resolve_account_alias(account: str) -> str:
    acc = account.strip().lower()
    if "alpha" in acc or acc in ["brand_01", "brand-01", "5555"]:
        return "brand_01"
    return account.strip()


def get_adb_path() -> str:
    candidates = [
        shutil.which("adb"),
        r"C:\Users\Shahid\tools\scrcpy\adb.exe",
        r"C:\platform-tools\adb.exe",
        str(Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return str(c)
    return "adb"


def check_adb_device_status(port: int) -> str:
    adb_bin = get_adb_path()
    try:
        res = subprocess.run(
            [adb_bin, "devices"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=5.0
        )
        for line in res.stdout.splitlines():
            line_str = line.strip()
            if f":{port}" in line_str or (port == 5555 and ("5555" in line_str or "emulator-5554" in line_str)):
                if "device" in line_str and "offline" not in line_str:
                    return "online"
                elif "offline" in line_str:
                    return "offline"
        return "offline"
    except Exception as e:
        return "offline"


@app.get("/api/status")
async def get_system_status(account: str = "Brand Alpha"):
    port = resolve_port(account)
    target = f"127.0.0.1:{port}"
    pause_flag = get_pause_flag_path(account)

    # Check ADB device status synchronously in thread
    adb_status = await asyncio.to_thread(check_adb_device_status, port)

    return {
        "account": account,
        "port": port,
        "target": target,
        "adb_status": adb_status,
        "is_paused": pause_flag.exists(),
        "is_uploading": manager.active_process is not None and manager.active_process.returncode is None,
        "active_job": manager.active_job_info
    }


@app.get("/api/files")
async def list_available_files():
    files = []
    if UPLOAD_DIR.exists():
        for f in UPLOAD_DIR.glob("*"):
            if f.is_file() and f.suffix.lower() in [".mp4", ".mov", ".mkv", ".webm"]:
                files.append({
                    "name": f.name,
                    "path": str(f.resolve()),
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    "modified": f.stat().st_mtime
                })
    files.sort(key=lambda x: x["modified"], reverse=True)
    return {"files": files}


@app.post("/api/upload_file")
async def upload_video_file(file: UploadFile = File(...)):
    filename = file.filename
    clean_name = Path(filename).name
    save_path = UPLOAD_DIR / clean_name
    
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "success": True,
        "filename": clean_name,
        "path": str(save_path.resolve()),
        "size_mb": round(save_path.stat().st_size / (1024 * 1024), 2)
    }


@app.post("/api/container/action")
async def container_action(payload: Dict[str, Any]):
    action = payload.get("action")  # start, stop, restart, scrcpy
    account = payload.get("account", "01")
    port = resolve_port(account)
    target = f"127.0.0.1:{port}"

    await manager.broadcast_log(f"[SYSTEM] Container Action '{action}' requested for account '{account}' ({target})...\n")

    if action == "scrcpy":
        # Launch scrcpy in background directly
        try:
            adb_bin = shutil.which("adb") or "adb"
            scrcpy_bin = shutil.which("scrcpy") or "scrcpy"

            # Connect target first
            subprocess.run([adb_bin, "connect", target], capture_output=True)

            scrcpy_args = [
                scrcpy_bin,
                "-s", target,
                "--video-codec=h264",
                "--video-encoder=OMX.google.h264.encoder",
                "--no-audio",
                "--video-bit-rate=4M",
                "--max-fps=30",
                "--stay-awake",
                "--window-title", f"Redroid - {account} ({target})"
            ]

            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

            subprocess.Popen(
                scrcpy_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
                close_fds=True
            )
            await manager.broadcast_log(f"[+] Successfully launched Scrcpy live window for {target}\n")
            return {"success": True, "message": f"Scrcpy window opened for {target}"}
        except Exception as e:
            await manager.broadcast_log(f"[ERROR] Failed to launch Scrcpy: {e}\n")
            return {"success": False, "error": str(e)}

    # For start, stop, restart call redroid.ps1
    ps_script = BASE_DIR / "redroid.ps1"
    if not ps_script.exists():
        raise HTTPException(status_code=500, detail="redroid.ps1 script not found")

    account_arg = resolve_account_alias(account)
    cmd = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(ps_script), action, account_arg]

    async def _on_container_exit(code: int):
        if code == 0:
            await manager.broadcast_log(f"[+] Container action '{action}' finished successfully for {account}.\n")
        else:
            await manager.broadcast_log(f"[-] Container action '{action}' exited with code {code}.\n")

    stream_process(cmd, prefix=action.upper(), on_exit=_on_container_exit)
    return {"success": True, "message": f"Action '{action}' triggered for {account}"}


@app.post("/api/upload/start")
async def start_upload_task(payload: Dict[str, Any]):
    async with manager.lock:
        if manager.active_process is not None and manager.active_process.poll() is None:
            raise HTTPException(status_code=400, detail="An upload job is already running")

        video_path = payload.get("video_path")
        if not video_path or not Path(video_path).exists():
            raise HTTPException(status_code=400, detail="Valid video path is required")

        account = payload.get("account", "01")
        title = payload.get("title", "")
        sound = payload.get("sound")
        timestamp = payload.get("timestamp")
        media_name = payload.get("media_name")

        # Clear any stale pause flag
        p_flag = get_pause_flag_path(account)
        if p_flag.exists():
            try:
                p_flag.unlink()
            except Exception:
                pass

        script_path = BASE_DIR / "upload_short.py"
        python_exe = sys.executable

        # Exact matching CLI syntax: py upload_short.py <video_path> -a <account> --title <title> [-s <sound>] [-t <timestamp>] [-n <media_name>]
        cmd = [
            python_exe,
            "-u",
            str(script_path),
            str(video_path),
            "-a", str(account)
        ]

        if title:
            cmd.extend(["--title", str(title)])
        if sound and str(sound).strip():
            cmd.extend(["-s", str(sound).strip()])
        if timestamp and str(timestamp).strip():
            cmd.extend(["-t", str(timestamp).strip()])
        if media_name and str(media_name).strip():
            cmd.extend(["-n", str(media_name).strip()])

        manager.active_job_info = {
            "video_path": video_path,
            "account": account,
            "title": title,
            "sound": sound,
            "timestamp": timestamp,
            "start_time": time.time(),
            "cmd": " ".join(cmd)
        }

        await manager.broadcast_log(f"\n{'='*60}\n")
        await manager.broadcast_log(f"[SYSTEM] 🚀 LAUNCHING UPLOAD AUTOMATION\n")
        await manager.broadcast_log(f"[SYSTEM] Video:   {video_path}\n")
        await manager.broadcast_log(f"[SYSTEM] Account: {account}\n")
        await manager.broadcast_log(f"[SYSTEM] Title:   {title}\n")
        if sound:
            await manager.broadcast_log(f"[SYSTEM] Sound:   {sound} (Timestamp: {timestamp or 'Default'})\n")
        await manager.broadcast_log(f"[SYSTEM] Command: {' '.join(cmd)}\n")
        await manager.broadcast_log(f"{'='*60}\n")

        async def _on_upload_exit(code: int):
            if code == 0:
                await manager.broadcast_log(f"\n[SYSTEM] ✅ Upload completed successfully (Exit Code: {code})\n")
            else:
                await manager.broadcast_log(f"\n[SYSTEM] ❌ Upload process terminated with exit code {code}\n")
            async with manager.lock:
                manager.active_process = None
                manager.active_job_info = None

        stream_process(cmd, on_exit=_on_upload_exit, track_as_active=True)

        return {"success": True, "message": "Upload job started successfully"}


@app.post("/api/upload/pause")
async def pause_upload(payload: Dict[str, Any]):
    account = payload.get("account", "Brand Alpha")
    flag = get_pause_flag_path(account)
    try:
        flag.write_text("PAUSED", encoding="utf-8")
        await manager.broadcast_log(f"[SYSTEM] ⏸ Pause signal sent for account '{account}' (Automation frozen)\n")
        return {"success": True, "is_paused": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/upload/resume")
async def resume_upload(payload: Dict[str, Any]):
    account = payload.get("account", "Brand Alpha")
    flag = get_pause_flag_path(account)
    try:
        if flag.exists():
            flag.unlink()
        await manager.broadcast_log(f"[SYSTEM] ▶ Resume signal sent for account '{account}' (Automation continuing)\n")
        return {"success": True, "is_paused": False}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/upload/stop")
async def stop_upload_task():
    async with manager.lock:
        if manager.active_process is None or manager.active_process.poll() is not None:
            return {"success": True, "message": "No active upload process to stop"}

        try:
            manager.active_process.terminate()
            await manager.broadcast_log(f"\n[SYSTEM] 🛑 Terminating active upload job...\n")
        except Exception as e:
            await manager.broadcast_log(f"[SYSTEM] Error terminating process: {e}\n")

        return {"success": True, "message": "Termination signal sent"}


@app.post("/api/upload/clean")
async def clean_drafts_task(payload: Dict[str, Any]):
    account = payload.get("account", "01")
    script_path = BASE_DIR / "upload_short.py"
    python_exe = sys.executable

    cmd = [python_exe, "-u", str(script_path), "-c", "-a", str(account)]
    await manager.broadcast_log(f"[SYSTEM] 🧹 Cleaning emulator media, MediaStore, and YouTube upload session for {account}...\n")

    stream_process(cmd, prefix="CLEAN")
    return {"success": True, "message": f"Clean task initiated for {account}"}


@app.websocket("/ws/logs")
async def websocket_logs_endpoint(websocket: WebSocket):
    await manager.connect_ws(websocket)
    try:
        while True:
            # Keep alive and listen for any client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_ws(websocket)
    except Exception:
        manager.disconnect_ws(websocket)


# Serve web frontend
@app.get("/")
async def serve_index():
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>YouTube Shorts Studio Frontend is initializing...</h1>")

app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


if __name__ == "__main__":
    print("=" * 60)
    print("  🚀 YOUTUBE SHORTS REDROID STUDIO - WEB CONTROL")
    print("  URL: http://127.0.0.1:8080")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
