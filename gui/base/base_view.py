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
from PIL import Image, ImageTk
from core.app_config import load_config

class BaseView(ctk.CTkFrame):
    def __init__(self, master, 
        message_exit=True, 
        *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.pack(expand=True, fill="both")
        self._fg_color="#05243F"  

        # if enable_fullscreen_control:
        #     self.DisableFullscreen()
        if message_exit:
            self.master.protocol("WM_DELETE_WINDOW", self.ExitWindow)
        # if disable_resize:
        #   self.master.resizable(False, False)

        


    def LabelFont(self, master, text, font=("Bahnschrift", 20, "bold"), justify="center", **kwargs):
        """Tạo một nhãn với phông chữ tùy chỉnh."""
        return ctk.CTkLabel(master, textvariable=text, font=font, justify=justify, **kwargs)
    
    def ButtonTheme(self, master, text, font=("Bahnschrift", 18, "bold"), fg_color="green", hover_color="darkblue", border_color="white", border_width=2, command=None, **kwargs):
        """Tạo mẫu nút"""
        return ctk.CTkButton(master=master, text=text, font=font, fg_color=fg_color, hover_color=hover_color, border_color=border_color, border_width=border_width, command=command, **kwargs)

    def DisableFullscreen(self):
        """Vô hiệu hóa chế độ toàn màn hình"""
            # --- ĐÃ VÔ HIỆU HÓA DÒNG NÀY ---
        # self.master.resizable(False, False) 
        self.master.bind("<F11>", lambda event: self.DisableFullscreen())
        
    def ExitWindow(self):
        """Đóng cửa sổ ứng dụng."""
        answer = messagebox.askokcancel("Thông Báo!", "Bạn có chắc chắn muốn thoát ứng dụng không?")
        if answer:
            self.master.quit()
        else:
            pass 
        
    def show_message(self, title, message):
        """Hiển thị thông báo."""
        messagebox.showinfo(title, message)


if __name__ == "__main__":

    root = ctk.CTk()
    root.title("Base View Example")
    root.geometry("800x600")
    home = BaseView(master=root)


    root.mainloop()
