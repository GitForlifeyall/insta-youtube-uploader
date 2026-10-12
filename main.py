"""
Instagram Automation API Server Launcher
Run with:
    python main.py
Or directly with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
import os
import sys
import argparse
import uvicorn

def run():
    parser = argparse.ArgumentParser(description="Instagram Automation API Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", default=True, help="Enable auto-reload on code change")
    args = parser.parse_args()

    print("=" * 60)
    print("🚀 Starting Instagram Automation & Uploader API")
    print(f"📡 Serving at: http://{args.host}:{args.port}")
    print(f"📖 Swagger Docs: http://localhost:{args.port}/docs")
    print("=" * 60)

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    run()
