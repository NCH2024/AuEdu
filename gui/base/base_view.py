'''
FILE NAME: gui/base_view.py
CODE BY: Nguyễn Chánh Hiệp 
DATE: 22/06/2025
DESCRIPTION:
    + Đây là lớp cơ sở (base class) cho tất cả các view (cửa sổ/khung) trong ứng dụng.
    + Cung cấp các chức năng chung như: cấu hình cửa sổ, xử lý sự kiện đóng cửa sổ, và các phương thức tiện ích.
    + Định nghĩa các phương thức tạo widget (Label, Button) theo một theme thống nhất để tái sử dụng.
VERSION: 1.0.0
'''
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from core.theme_manager import Theme, AppFont 
from core.theme_manager import FontLoader

class BaseView(ctk.CTkFrame):
    def __init__(self, master, message_exit=True, *args, **kwargs):
        # Thiết lập màu nền từ Theme ngay khi khởi tạo
        kwargs['fg_color'] = kwargs.get('fg_color', Theme.Color.BG)
        
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.pack(expand=True, fill="both")
        """Đăng ký font Inter khi khởi tạo BaseView"""
        FontLoader.load_inter_fonts()
        if message_exit:
            self.master.protocol("WM_DELETE_WINDOW", self.ExitWindow)

    def LabelFont(self, master, text, font=AppFont.H3, justify="center", text_color=None, **kwargs):
        """
        Tạo label chuẩn.
        Nếu không truyền text_color, tự động dùng màu chính từ Theme.
        """
        if text_color is None:
            text_color = Theme.Color.TEXT
            
        return ctk.CTkLabel(master, textvariable=text, font=font, justify=justify, text_color=text_color, **kwargs)

    def ButtonTheme(self, master, text, font=AppFont.BODY_BOLD, 
                    fg_color=None, hover_color=None, text_color=None,
                    border_color=None, border_width=2, command=None, **kwargs):
        
        if fg_color is None: fg_color = Theme.Color.PRIMARY
        
        if hover_color is None: hover_color = Theme.Color.PRIMARY_HOVER
        
        if border_color is None: border_color = Theme.Color.BORDER
        
        if text_color is None:
            text_color = Theme.Color.BG 
            
        return ctk.CTkButton(master=master, text=text, font=font, 
                             fg_color=fg_color, hover_color=hover_color, 
                             text_color=text_color,
                             border_color=border_color, border_width=border_width, 
                             command=command, **kwargs)

    def ExitWindow(self):
        """Đóng cửa sổ ứng dụng."""
        answer = messagebox.askokcancel("Thông Báo!", "Bạn có chắc chắn muốn thoát ứng dụng không?")
        if answer:
            self.master.quit()
        else:
            pass 
        
    def show_message(self, title, message):
        messagebox.showinfo(title, message)