"""Build a standalone EchoAction Desktop executable.

Usage:
    python build_desktop.py          # Build .exe
    python build_desktop.py --clean  # Clean build artifacts
"""

import os
import sys
import shutil
import subprocess

APP_NAME = "EchoActionAI"
BUILD_DIR = "build_dist"
ENTRY_POINT = "desktop_app.py"
EXCLUDE_MODULES = ["matplotlib", "scipy", "pandas", "PIL", "cv2", "sklearn"]

def clean():
    for d in ["build", BUILD_DIR, "__pycache__"]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
    for f in [f"{APP_NAME}.spec"]:
        if os.path.exists(f):
            os.remove(f)
    print("[CLEAN] Done.")

def build():
    # Install PyInstaller if not available
    try:
        import PyInstaller
    except ImportError:
        print("[INFO] Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--distpath", BUILD_DIR,
        "--add-data", "templates;templates",
        "--add-data", "static;static",
        "--add-data", "db.py;.",
        "--add-data", "security.py;.",
        "--add-data", "models.py;.",
        "--add-data", "requirements.txt;.",
    ]
    for mod in EXCLUDE_MODULES:
        cmd.extend(["--exclude-module", mod])
    cmd.append(ENTRY_POINT)

    print(f"[BUILD] Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print(f"[BUILD] Done. Executable in '{BUILD_DIR}/'")

if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    else:
        build()
