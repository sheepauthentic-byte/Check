# Language: Python 3.10+
# Target: Flask Web Wrapper for Cloud Execution

import os
from flask import Flask, render_template_string, redirect, url_for
from pathlib import Path
from main import LocalMasterEngine

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Cloud Dumper Dashboard</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: monospace; padding: 20px; }
        .container { max-width: 900px; margin: auto; background: #1e293b; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        button { background: #2563eb; color: white; border: none; padding: 12px 24px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 14px; }
        button:hover { background: #1d4ed8; }
        pre { background: #0f172a; padding: 15px; border-radius: 4px; overflow-x: auto; color: #4ade80; max-height: 450px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 Cloud Dumper & AccCheck Aggregator</h2>
        <form method="POST" action="/run-dump">
            <button type="submit">▶ Kích Hoạt Chạy Dump & Tổng Hợp</button>
        </form>
        <hr style="border-color: #334155; margin: 20px 0;">
        <h3>📁 Nội dung file acccheck.txt hiện tại:</h3>
        <pre>{{ logs }}</pre>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    log_content = ""
    log_path = Path("acccheck.txt")
    if log_path.exists():
        log_content = log_path.read_text(encoding="utf-8", errors="ignore")
    return render_template_string(HTML_PAGE, logs=log_content or "Chưa có dữ liệu. Bấm nút phía trên để bắt đầu...")

@app.route("/run-dump", methods=["POST"])
def run_dump():
    try:
        engine = LocalMasterEngine()
        engine.run()
    except Exception as e:
        print(f"Error: {e}")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
