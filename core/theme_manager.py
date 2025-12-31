'''
FILE NAME: core/theme_manager.py
DESCRIPTION: Quản lý giao diện Sáng/Tối (Đã thêm màu Hover chuẩn).
'''
from tkinter import ttk
import customtkinter as ctk

import customtkinter as ctk

class AppFont:
    NAME = "Inter" # Hoặc "Arial", "Roboto" tuỳ máy
    H1 = (NAME, 30, "bold")
    H2 = (NAME, 24, "bold")
    H3 = (NAME, 20, "bold")
    BODY = (NAME, 14, "normal")
    BODY_BOLD = (NAME, 14, "bold")
    SMALL = (NAME, 12, "normal")
    # Thêm font nghiêng nhỏ cho các dòng chú thích (*)
    SMALL_ITALIC = (NAME, 11, "italic")

class ColorPalette:
    """Kho màu gốc (Palette)"""
    # Màu chủ đạo (Brand Colors)
    DARK_BLUE = "#05243F"
    DEEP_NAVY = "#021B2F"
    NAVY_HOVER = "#1B3A57" 
    
    MINT_GREEN = "#2DFCB0"
    MINT_HOVER = "#00D68F" 
    
    # Màu chức năng (Semantic Colors)
    GREEN_SUCCESS = "#4CAF50" # Nút Thêm
    BLUE_INFO = "#2196F3"     # Nút Cập nhật/Sửa
    ORANGE_WARNING = "#FF9800"# Nút Tìm kiếm/Lọc
    RED_DANGER = "#F44336"    # Nút Xóa/Báo động (Sáng hơn RED_ALERT xíu)
    RED_ALERT = "#FF2020"     # Màu chữ báo lỗi
    GRAY_NEUTRAL = "#607D8B"  # Nút Làm mới/Refresh
    
    # Màu cơ bản
    WHITE = "#FFFFFF"
    OFF_WHITE = "#F5F7FA"
    GRAY_TEXT = "#333333"
    LIGHT_GRAY = "#E5E5E5"

class Theme:
    """Cửa hàng (Storefront) để lấy màu theo chế độ Sáng/Tối"""
    class Color:
        PRIMARY = ""
        PRIMARY_HOVER = "" 
        SECONDARY = ""
        BG = ""
        BG_CARD = ""
        TEXT = ""
        TEXT_SUB = ""
        BORDER = ""
        
        # Các màu chức năng (Thêm mới)
        SUCCESS = ""
        INFO = ""
        WARNING = ""
        DANGER = ""
        RED_ALERT = ""
        NEUTRAL = ""

    @staticmethod
    def load_theme(mode="Dark"):
        if mode == "Light":
            ctk.set_appearance_mode("Light")
            Theme.Color.PRIMARY = ColorPalette.DARK_BLUE
            Theme.Color.PRIMARY_HOVER = ColorPalette.NAVY_HOVER 
            Theme.Color.SECONDARY = ColorPalette.OFF_WHITE
            Theme.Color.BG = ColorPalette.WHITE
            Theme.Color.BG_CARD = "#EBF2F7"
            Theme.Color.TEXT = ColorPalette.DARK_BLUE
            Theme.Color.TEXT_SUB = ColorPalette.GRAY_TEXT
            Theme.Color.BORDER = "#D1D9E0"
            
        else: # Dark Mode
            ctk.set_appearance_mode("Dark")
            Theme.Color.PRIMARY = ColorPalette.MINT_GREEN
            Theme.Color.PRIMARY_HOVER = ColorPalette.MINT_HOVER 
            Theme.Color.SECONDARY = ColorPalette.DARK_BLUE
            Theme.Color.BG = ColorPalette.DARK_BLUE
            Theme.Color.BG_CARD = ColorPalette.DEEP_NAVY
            Theme.Color.TEXT = ColorPalette.WHITE
            Theme.Color.TEXT_SUB = ColorPalette.LIGHT_GRAY
            Theme.Color.BORDER = ColorPalette.WHITE

        # Các màu chức năng thường giữ nguyên giữa 2 chế độ (hoặc chỉnh nhẹ nếu cần)
        Theme.Color.SUCCESS = ColorPalette.GREEN_SUCCESS
        Theme.Color.INFO = ColorPalette.BLUE_INFO
        Theme.Color.WARNING = ColorPalette.ORANGE_WARNING
        Theme.Color.DANGER = ColorPalette.RED_DANGER
        Theme.Color.RED_ALERT = ColorPalette.RED_ALERT
        Theme.Color.NEUTRAL = ColorPalette.GRAY_NEUTRAL
        
    def apply_treeview_style(self):
        """Hàm ép kiểu giao diện cho bảng Treeview thường"""
        style = ttk.Style()
        style.theme_use("default") # Bắt buộc dùng default để override màu

        # Lấy màu từ Theme
        mode = ctk.get_appearance_mode()
        is_dark = mode == "Dark"

        bg_color = "#2b2b2b" if is_dark else "#ffffff"
        fg_color = "#ffffff" if is_dark else "#000000"
        heading_bg = Theme.Color.SECONDARY
        heading_fg = Theme.Color.TEXT
        selected_bg = Theme.Color.PRIMARY

        # Config cho Treeview
        style.configure("Treeview",
                        background=bg_color,
                        foreground=fg_color,
                        fieldbackground=bg_color,
                        bordercolor=Theme.Color.BORDER,
                        borderwidth=0,
                        font=AppFont.SMALL,
                        rowheight=30)
        
        # Config cho Heading (Tiêu đề cột)
        style.configure("Treeview.Heading",
                        background=heading_bg,
                        foreground=heading_fg,
                        font=AppFont.BODY_BOLD,
                        relief="flat")
        
        # Hiệu ứng Hover cho Heading
        style.map("Treeview.Heading",
                  background=[('active', Theme.Color.PRIMARY_HOVER)])
        
        # Hiệu ứng chọn dòng (Selected)
        style.map("Treeview",
                  background=[('selected', selected_bg)],
                  foreground=[('selected', ColorPalette.DEEP_NAVY if is_dark else ColorPalette.WHITE)]),


# Khởi tạo mặc định
Theme.load_theme("Light")