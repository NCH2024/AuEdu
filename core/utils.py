'''
FILE NAME: core/utils.py
CODE BY: Nguyễn Chánh Hiệp 
DATE: 17/06/2025
DESCRIPTION:
        + Đây là file chứa các hàm tiện ích cho ứng dụng
        + Định nghĩa các hàm xử lý dữ liệu
        + Các hàm này sẽ được sử dụng để hỗ trợ cho các model và controller
VERSION: 1.0.0
'''
from datetime import datetime
import bcrypt
import pygame
import os
import sys


def bcrypt_password(password: str) -> str:
    """Mã hóa password bằng bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    b = bcrypt.hashpw(password.encode(), salt) 
    return b.decode()  # Trả về chuỗi để lưu trong DB

def check_password(plain_password: str, bcrypt_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), bcrypt_password.encode())


def get_base_path():
    """ 
    Lấy đường dẫn gốc của ứng dụng (thư mục DACS2-...).
    Hoạt động cho cả script .py và file .exe đã đóng gói. 
    """
    if hasattr(sys, '_MEIPASS'):
        # Chạy từ file .exe (PyInstaller --onefile)
        # _MEIPASS là thư mục tạm được giải nén
        return sys._MEIPASS
    elif getattr(sys, 'frozen', False):
        # Chạy từ file .exe (PyInstaller --onedir)
        # sys.executable là đường dẫn đến file .exe
        return os.path.dirname(sys.executable)
    else:
        # Chạy từ script .py
        # __file__ trỏ đến core/utils.py
        # os.path.dirname(__file__) trỏ đến .../core
        # os.path.join(..., "..") sẽ trỏ lên thư mục gốc .../DACS2-....
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
def resource_path(relative_path):
    """Lấy đường dẫn đúng cho file khi chạy .py hoặc .exe"""
    try:
        # PyInstaller giải nén vào _MEIxxxx
        base_path = sys._MEIPASS
    except AttributeError:
        # Chạy script bình thường
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)


def convert_to_mysql_date(date_str):
    """Chuyển từ 'DD/MM/YYYY' sang 'YYYY-MM-DD'."""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None