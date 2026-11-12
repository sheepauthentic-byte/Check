# Language: Python 3.10+
# Target: Global Configuration Settings

import os

class Config:
    TARGET_WEBSITE = "https://tainguyenmmo.com"
    CATALOG_PATH = "/products"
    
    # Tài khoản đăng nhập (nếu shop yêu cầu, để nguyên nếu chạy chế độ khách)
    AUTH_ENDPOINT = "/api/auth/login"
    USERNAME = os.getenv("TARGET_USER", "your_username_here")
    PASSWORD = os.getenv("TARGET_PASS", "your_password_here")
    
    # Thư mục chứa file tải về và file tổng hợp kết quả
    OUTPUT_DIRECTORY = "downloaded_resources"
    RESULT_LOG_FILE = "acccheck.txt"
    
    # Giới hạn phân trang và độ trễ tránh chặn IP
    MAX_PAGES = 10
    REQUEST_DELAY = 1.0
