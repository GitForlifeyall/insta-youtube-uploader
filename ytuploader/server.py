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

# Global State
class UploadManager:
    def __init__(self):
        self.active_process: Optional[asyncio.subprocess.Process] = None
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

manager = UploadManager()


def get_pause_flag_path(account: str) -> Path:
    return Path(tempfile.gettempdir()) / f"redroid_pause_{account}.flag"


def resolve_port(account: str) -> int:
    acc = account.strip().lower()
    if "alpha" in acc or acc in ["brand_01", "brand-01", "01", "5555"]:
        return 5555
    if acc.isdigit():
        num = int(acc)
        return 5800 + num if num < 5000 else num
    return 5555


@app.get("/api/status")
async def get_system_status(account: str = "Brand Alpha"):
    port = resolve_port(account)
    target = f"127.0.0.1:{port}"
    pause_flag = get_pause_flag_path(account)

    # Check ADB device status
    adb_status = "offline"
    try:
        proc = await asyncio.create_subprocess_exec(
            "adb", "devices",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        out_str = stdout.decode("utf-8", errors="ignore")
        for line in out_str.splitlines():
            if f":{port}" in line or (port == 5555 and "5555" in line):
                if "device" in line and "offline" not in line:
                    adb_status = "online"
                elif "offline" in line:
                    adb_status = "offline"
    except Exception:
        adb_status = "unknown"

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
        # Launch scrcpy in background detached
        try:
            # First ensure adb connect
            subprocess.run(["adb", "connect", target], capture_output=True)
            scrcpy_cmd = f'scrcpy -s {target} --window-title "Redroid - {account} ({target})" --always-on-top --max-size 1024'
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", f"Start-Process {scrcpy_cmd}"],
                shell=False
            )
            await manager.broadcast_log(f"[+] Launched Scrcpy window for {target}\n")
            return {"success": True, "message": f"Scrcpy window opened for {target}"}
        except Exception as e:
            await manager.broadcast_log(f"[ERROR] Failed to launch Scrcpy: {e}\n")
            return {"success": False, "error": str(e)}

    # For start, stop, restart call redroid.ps1
    ps_script = BASE_DIR / "redroid.ps1"
    if not ps_script.exists():
        raise HTTPException(status_code=500, detail="redroid.ps1 script not found")

    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_script), action, account]

    async def run_ps_cmd():
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(BASE_DIR)
        )
        stdout, stderr = await proc.communicate()
        out = stdout.decode("utf-8", errors="ignore")
        err = stderr.decode("utf-8", errors="ignore")
        if out:
            for l in out.splitlines():
                await manager.broadcast_log(f"[{action.upper()}] {l}\n")
        if err:
            for l in err.splitlines():
                await manager.broadcast_log(f"[WARN] {l}\n")

    asyncio.create_task(run_ps_cmd())
    return {"success": True, "message": f"Action '{action}' triggered for {account}"}


@app.post("/api/upload/start")
async def start_upload_task(payload: Dict[str, Any]):
    async with manager.lock:
        if manager.active_process is not None and manager.active_process.returncode is None:
            raise HTTPException(status_code=400, detail="An upload job is already running")

        video_path = payload.get("video_path")
        if not video_path or not Path(video_path).exists():
            raise HTTPException(status_code=400, detail="Valid video path is required")

        account = payload.get("account", "Brand Alpha")
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

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(BASE_DIR)
        )
        manager.active_process = proc

        # Background streaming reader
        async def stream_output():
            try:
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="ignore")
                    await manager.broadcast_log(decoded)

                _, stderr = await proc.communicate()
                if stderr:
                    err_decoded = stderr.decode("utf-8", errors="ignore")
                    for l in err_decoded.splitlines():
                        await manager.broadcast_log(f"[STDERR] {l}\n")

                code = proc.returncode
                if code == 0:
                    await manager.broadcast_log(f"\n[SYSTEM] ✅ Upload completed successfully (Exit Code: {code})\n")
                else:
                    await manager.broadcast_log(f"\n[SYSTEM] ❌ Upload process terminated with exit code {code}\n")
            except Exception as e:
                await manager.broadcast_log(f"\n[SYSTEM] Process stream error: {e}\n")
            finally:
                async with manager.lock:
                    manager.active_process = None
                    manager.active_job_info = None

        asyncio.create_task(stream_output())

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
        if manager.active_process is None or manager.active_process.returncode is not None:
            return {"success": True, "message": "No active upload process to stop"}

        try:
            manager.active_process.terminate()
            await manager.broadcast_log(f"\n[SYSTEM] 🛑 Terminating active upload job...\n")
        except Exception as e:
            await manager.broadcast_log(f"[SYSTEM] Error terminating process: {e}\n")

        return {"success": True, "message": "Termination signal sent"}


@app.post("/api/upload/clean")
async def clean_drafts_task(payload: Dict[str, Any]):
    account = payload.get("account", "Brand Alpha")
    script_path = BASE_DIR / "upload_short.py"
    python_exe = sys.executable

    cmd = [python_exe, "-u", str(script_path), "-c", "-a", str(account)]
    await manager.broadcast_log(f"[SYSTEM] 🧹 Cleaning emulator media, MediaStore, and YouTube upload session for {account}...\n")

    async def _clean_worker():
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(BASE_DIR)
        )
        stdout, stderr = await proc.communicate()
        out = stdout.decode("utf-8", errors="ignore")
        if out:
            for l in out.splitlines():
                await manager.broadcast_log(f"[CLEAN] {l}\n")
        if stderr:
            for l in stderr.splitlines():
                await manager.broadcast_log(f"[CLEAN-ERR] {l}\n")

    asyncio.create_task(_clean_worker())
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
