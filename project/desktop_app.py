"""Desktop app launcher — wraps the Flask web server in a native window using pywebview.

Run with:           python desktop_app.py
Build standalone:   python build_desktop.py
Web only:          python app.py
"""

import os
import sys
import threading
import webview

FLASK_HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.environ.get("FLASK_PORT", "5003"))
FLASK_URL = f"http://{FLASK_HOST}:{FLASK_PORT}"

def start_flask():
    os.environ["ECHOACTION_DESKTOP"] = "1"
    sys.argv = [sys.argv[0]]
    from app import app
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()
    webview.create_window(
        "EchoAction AI",
        FLASK_URL,
        width=1280,
        height=800,
        resizable=True,
        text_select=True,
    )
