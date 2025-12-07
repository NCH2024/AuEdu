import customtkinter as ctk
from gui.base.utils import *
from gui.user.lecturer_attendance_setting import LecturerAttendance_Setting
from gui.user.lecturer_account_settings import LecturerAccount_Setting


class LecturerSettings(ctk.CTkFrame):
    def __init__(self, master=None, user=None, AppConfig=None, **kwargs):
        super().__init__(master, **kwargs)
        self.user = user
        self.AppcConfig = AppConfig
        self.configure(fg_color="#05243F")
        
        
        # Bién màu sắc
        self.widget_color = "#2DFCB0"

        # Cấu hình grid tổng thể
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure((0,1), weight=1)
        
        # Title
        self.title = ctk.CTkLabel(self, text="Dashboard > CÀI ĐẶT CHUNG", font=("Bahnschrift", 20, "bold"),
            text_color="white")
        self.title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # Khung cài đặt dành cho phần mềm
        self.widget_settings_attendace = ctk.CTkFrame(self, fg_color="white", border_color=self.widget_color, border_width=2)
        self.widget_settings_attendace.grid(row=1, column=0, padx=5, pady=5, sticky="news")
        self.widget_settings_attendace.grid_columnconfigure(0,weight=1)
        self.widget_settings_attendace.grid_rowconfigure(0,weight=1)
        
        self.widget_settings_attendace_content = LecturerAttendance_Setting(master=self.widget_settings_attendace, AppConfig=self.AppcConfig)
        self.widget_settings_attendace_content.grid(row=0, column=0, padx=20, pady=20, sticky="news")
                
        # Khung cài đặt dành cho tài khoản user
        self.widget_settings_account = ctk.CTkFrame(self, fg_color=self.widget_color)
        self.widget_settings_account.grid(row=1, column=1, padx=5, pady=5, sticky="news")
        self.widget_settings_account.grid_columnconfigure(0,weight=1)
        self.widget_settings_account.grid_rowconfigure(0,weight=1)
        
        self.widget_settings_account_content = LecturerAccount_Setting(master=self.widget_settings_account, user=self.user, AppConfig=self.AppcConfig)
        self.widget_settings_account_content.grid(row=0, column=0, padx=20, pady=20, sticky="news")
        
        