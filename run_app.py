"""
Global News AI — All-in-One Application Launcher

Runs both the FastAPI REST Backend (Port 8000) and the React Web UI (Port 5173) simultaneously,
and automatically opens http://localhost:5173/ in your default web browser.

Usage:
    python run_app.py
"""

import sys
import os
import time
import subprocess
import webbrowser
import signal
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def open_browser_fullscreen(url: str):
    """
    Opens the specified web URL in full screen / maximized browser window mode.
    Tries Chrome/Edge with --start-maximized, falling back to webbrowser module.
    """
    opened = False
    if os.name == "nt":
        candidate_browsers = [
            (r"C:\Program Files\Google\Chrome\Application\chrome.exe", ["--start-maximized"]),
            (r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", ["--start-maximized"]),
            (os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"), ["--start-maximized"]),
            (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", ["--start-maximized"]),
            (r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", ["--start-maximized"]),
            (r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe", ["--start-maximized"]),
        ]
        for exe_path, flags in candidate_browsers:
            if os.path.exists(exe_path):
                try:
                    subprocess.Popen([exe_path] + flags + [url])
                    opened = True
                    break
                except Exception:
                    pass

    if not opened:
        webbrowser.open(url)


def main():
    print("\n" + "=" * 80)
    print(" 🌍 GLOBAL NEWS AI — UNIFIED FULL SYSTEM LAUNCHER")
    print("=" * 80)
    print(" 🚀 1. Starting FastAPI REST Backend (Port 8000)...")
    print(" 🚀 2. Starting Near-Real-Time Continuous Ingestion Scheduler...")
    print(" 🚀 3. Starting React Web Application (Port 5173)...")
    print("=" * 80 + "\n")

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.api.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]

    scheduler_cmd = [
        sys.executable,
        "-m",
        "src.scheduler",
    ]

    frontend_dir = PROJECT_ROOT / "frontend"
    npm_bin = "npm.cmd" if os.name == "nt" else "npm"
    frontend_cmd = [npm_bin, "run", "dev"]

    processes = []

    try:
        # 1. Start FastAPI Backend Process
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(PROJECT_ROOT),
        )
        processes.append(backend_proc)

        # 2. Start Near-Real-Time Continuous Ingestion Scheduler Process
        scheduler_proc = subprocess.Popen(
            scheduler_cmd,
            cwd=str(PROJECT_ROOT),
        )
        processes.append(scheduler_proc)

        # 3. Start React Frontend Process (if frontend exists)
        if frontend_dir.exists():
            frontend_proc = subprocess.Popen(
                frontend_cmd,
                cwd=str(frontend_dir),
            )
            processes.append(frontend_proc)
        else:
            print(" ℹ️ Frontend UI directory not found (awaiting new UI implementation).")

        print("\n [INFO] All 3 Integrated Services (API, Ingestion Scheduler, Web UI) Are Active!")
        print(" [INFO] Opening http://localhost:5173/ in full screen mode in 3 seconds...")
        print(" [INFO] Press CTRL+C at any time to stop all services cleanly.\n")

        time.sleep(3)
        open_browser_fullscreen("http://localhost:5173/")


        # Keep launcher alive until user presses CTRL+C
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"⚠️ Process {p.args} exited unexpectedly with code {p.returncode}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 [Shutdown] CTRL+C received. Stopping all servers cleanly...")
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("👋 All servers stopped cleanly. Have a great day!")


if __name__ == "__main__":
    main()
