# Language: Python 3.10+
# Target: Local File Aggregator & Master Dumper Engine (No Telegram)

import os
import time
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse
from curl_cffi import requests
from bs4 import BeautifulSoup
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("system_execution.log", encoding="utf-8")]
)

class LocalMasterEngine:
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIRECTORY)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Khởi tạo session giả lập vân tay Chrome 120 (vượt WAF/Cloudflare)
        self.session = requests.Session(impersonate="chrome120")
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": Config.TARGET_WEBSITE
        })

    def run(self):
        logging.info("[*] Initializing Local Dumper Engine...")
        
        # Bước 1: Xác thực nếu có thông tin tài khoản
        if Config.USERNAME != "your_username_here":
            self._authenticate()

        # Bước 2: Cào và tải file từ danh mục
        downloaded_files = self._scrape_catalog()

        # Bước 3: Gom toàn bộ nội dung vào file acccheck.txt cục bộ
        if downloaded_files:
            self._aggregate_to_local_txt(downloaded_files)
        else:
            logging.warning("[-] No files were downloaded to aggregate.")

        logging.info("[+] Process finished successfully.")

    def _authenticate(self):
        login_url = urljoin(Config.TARGET_WEBSITE, Config.AUTH_ENDPOINT)
        payload = {"username": Config.USERNAME, "password": Config.PASSWORD}
        logging.info(f"[*] Authenticating at {login_url}...")
        try:
            res = self.session.post(login_url, json=payload, timeout=15)
            if res.status_code == 200:
                logging.info("[+] Authentication successful.")
            else:
                logging.warning(f"[-] Auth returned status {res.status_code}. Running as guest...")
        except Exception as e:
            logging.error(f"[-] Auth exception: {str(e)}")

    def _scrape_catalog(self) -> list:
        collected_files = []
        for page in range(1, Config.MAX_PAGES + 1):
            target_url = f"{Config.TARGET_WEBSITE}{Config.CATALOG_PATH}?page={page}"
            logging.info(f"[*] Crawling page {page}: {target_url}")
            
            try:
                response = self.session.get(target_url, timeout=20)
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                file_links = set()
                
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if any(ext in href.lower() for ext in ['.txt', '.zip', '.rar', '.csv', '.json', '/download/']):
                        file_links.add(urljoin(Config.TARGET_WEBSITE, href))

                for link in file_links:
                    saved_path = self._download_file(link)
                    if saved_path:
                        collected_files.append(saved_path)
                
                time.sleep(Config.REQUEST_DELAY)
            except Exception as e:
                logging.error(f"[-] Error at page {page}: {str(e)}")
                break
                
        return collected_files

    def _download_file(self, file_url: str) -> Path | None:
        parsed_url = urlparse(file_url)
        filename = os.path.basename(parsed_url.path) or f"resource_{int(time.time())}.txt"
        save_path = self.output_dir / filename

        if save_path.exists():
            return save_path

        try:
            with self.session.get(file_url, stream=True, timeout=30) as r:
                if r.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    logging.info(f"[+] Downloaded -> {save_path}")
                    return save_path
        except Exception:
            pass
        return None

    def _aggregate_to_local_txt(self, files: list):
        master_log_path = Path(Config.RESULT_LOG_FILE) # acccheck.txt
        total_lines = 0
        
        logging.info(f"[*] Aggregating downloaded contents into {master_log_path.name}...")
        with open(master_log_path, "w", encoding="utf-8", errors="ignore") as outfile:
            for file_path in files:
                if file_path.suffix == ".txt":
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        outfile.write(content + "\n")
                        total_lines += len(content.splitlines())
                    except Exception as e:
                        logging.error(f"[-] Error reading {file_path.name}: {str(e)}")
                        
        logging.info(f"[+] SUCCESS: Saved total {total_lines} records directly to local file -> {master_log_path.absolute()}")

if __name__ == "__main__":
    engine = LocalMasterEngine()
    engine.run()
