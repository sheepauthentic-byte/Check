# Language: Python 3.10+
# Target: Universal Web Dumper Dashboard & Background Worker

import os
import threading
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from flask import Flask, render_template_string, request, redirect, url_for
from curl_cffi import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Biến trạng thái toàn cục cho Dashboard
STATUS_LOG = "Hệ thống sẵn sàng. Chưa có tiến trình nào chạy."
IS_RUNNING = False
RESULT_FILE = "acccheck.txt"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Universal Web Dumper Dashboard</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: monospace; padding: 20px; margin: 0; }
        .container { max-width: 1000px; margin: auto; background: #1e293b; padding: 25px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); }
        h2 { color: #38bdf8; margin-top: 0; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #94a3b8; font-weight: bold; }
        input[type="text"] { width: 100%; background: #0f172a; color: #38bdf8; border: 1px solid #334155; padding: 12px; border-radius: 6px; box-sizing: border-box; font-size: 14px; }
        button { background: #2563eb; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px; transition: background 0.2s; }
        button:hover { background: #1d4ed8; }
        button:disabled { background: #475569; cursor: not-allowed; }
        .status-box { background: #0f172a; border: 1px solid #334155; padding: 15px; border-radius: 6px; color: #fbbf24; white-space: pre-wrap; height: 120px; overflow-y: auto; margin-bottom: 20px; }
        pre { background: #0f172a; border: 1px solid #334155; padding: 15px; border-radius: 6px; overflow-x: auto; color: #4ade80; max-height: 400px; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge.idle { background: #334155; color: #94a3b8; }
        .badge.running { background: #16a34a; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🌐 Universal Web Dumper Dashboard</h2>
        <div style="margin-bottom: 20px;">
            Trạng thái: 
            {% if is_running %}
                <span class="badge running">Đang chạy...</span>
            {% else %}
                <span class="badge idle">Đang nghỉ</span>
            {% endif %}
        </div>

        <form method="POST" action="/start-dump">
            <div class="form-group">
                <label>Nhập URL mục tiêu cần Dump:</label>
                <input type="text" name="target_url" value="{{ default_url }}" placeholder="https://example.com" required>
            </div>
            <button type="submit" {% if is_running %}disabled{% endif %}>🚀 Bắt Đầu Dump Toàn Bộ Dữ Liệu</button>
        </form>

        <hr style="border-color: #334155; margin: 25px 0;">

        <label>⚡ Log Tiến Trình Thời Gian Thực:</label>
        <div class="status-box">{{ status_log }}</div>

        <label>📁 Nội dung kết quả tổng hợp ({{ result_filename }}):</label>
        <pre>{{ file_content }}</pre>
    </div>
</body>
</html>
"""

def background_dumper(target_url: str):
    global STATUS_LOG, IS_RUNNING
    IS_RUNNING = True
    output_dir = Path("downloaded_resources")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        STATUS_LOG = f"[*] Đang khởi tạo kết nối TLS Spoofing tới: {target_url}"
        session = requests.Session(impersonate="chrome120")
        session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": target_url
        })

        # Quét trang chính và phân trang cơ bản
        collected_files = []
        parsed_base = urlparse(target_url)
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"

        for page in range(1, 6):
            page_url = f"{target_url.rstrip('/')}/products?page={page}" if "products" not in target_url else f"{target_url}&page={page}"
            STATUS_LOG = f"[*] Đang cào dữ liệu trang {page}: {page_url}"
            
            response = session.get(page_url, timeout=20)
            if response.status_code != 200:
                break
            
            soup = BeautifulSoup(response.text, 'html.parser')
            file_links = set()
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                if any(ext in href.lower() for ext in ['.txt', '.zip', '.rar', '.csv', '.json', '/download/']):
                    file_links.add(urljoin(base_domain, href))

            for link in file_links:
                try:
                    filename = os.path.basename(urlparse(link).path) or f"resource_{int(time.time())}.txt"
                    save_path = output_dir / filename
                    if not save_path.exists():
                        r = session.get(link, timeout=20)
                        if r.status_code == 200:
                            save_path.write_bytes(r.content)
                            collected_files.append(save_path)
                            STATUS_LOG = f"[+] Đã tải xuống thành công: {filename}"
                except Exception:
                    pass
            time.sleep(0.5)

        # Tổng hợp vào acccheck.txt
        master_log_path = Path(RESULT_FILE)
        total_lines = 0
        with open(master_log_path, "w", encoding="utf-8", errors="ignore") as outfile:
            for file_path in collected_files:
                if file_path.suffix == ".txt":
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        outfile.write(content + "\n")
                        total_lines += len(content.splitlines())
                    except Exception:
                        pass
                        
        STATUS_LOG = f"[+] Hoàn tất! Đã gom {total_lines} dòng dữ liệu vào {RESULT_FILE}."
    except Exception as e:
        STATUS_LOG = f"[-] Lỗi thực thi: {str(e)}"
    finally:
        IS_RUNNING = False

@app.route("/")
def index():
    file_content = ""
    log_path = Path(RESULT_FILE)
    if log_path.exists():
        file_content = log_path.read_text(encoding="utf-8", errors="ignore")
    
    return render_template_string(
        HTML_TEMPLATE,
        is_running=IS_RUNNING,
        default_url="https://tainguyenmmo.com",
        status_log=STATUS_LOG,
        result_filename=RESULT_FILE,
        file_content=file_content or "Chưa có dữ liệu kết quả..."
    )

@app.route("/start-dump", methods=["POST"])
def start_dump():
    global IS_RUNNING
    if IS_RUNNING:
        return redirect(url_for("index"))
        
    target_url = request.form.get("target_url", "").strip()
    if target_url:
        threading.Thread(target=background_dumper, args=(target_url,)).start()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
