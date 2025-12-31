'''
FILE NAME: main.py
CODE BY: Nguyễn Chánh Hiệp 
DATE: 22/06/2025
DESCRIPTION:
        + Đây là file chính để khởi chạy toàn bộ ứng dụng.
        + File này sẽ gọi hàm `runapp` từ module `gui.main_window` để bắt đầu giao diện đồ họa người dùng (GUI).
VERSION: 1.0.0
'''

from gui.main_window import runapp
from core.app_config import load_config

if __name__ == "__main__":      
        # Khởi chạy tệp cài đặt ứng dụng
        AppConfig = load_config()
        # Gọi hàm runapp để khởi chạy ứng dụng
        runapp(config=AppConfig)                                        
