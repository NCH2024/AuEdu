import customtkinter as ctk
from gui.base.utils import *
from gui.user.lecturer_attendance_setting import LecturerAttendance_Setting
from gui.user.lecturer_account_settings import LecturerAccount_Setting
from core.theme_manager import Theme, AppFont

class LecturerSettings(ctk.CTkFrame):
    def __init__(self, master=None, user=None, AppConfig=None, **kwargs):
        # 1. Màu nền chính (BG)
        kwargs['fg_color'] = Theme.Color.BG
        kwargs['corner_radius'] = 0
        super().__init__(master, **kwargs)
        
        self.user = user
        self.AppcConfig = AppConfig
        
        # 2. Cấu hình Grid
        self.grid_rowconfigure(0, weight=0) # Dòng tiêu đề không dãn
        self.grid_rowconfigure(1, weight=1) # Dòng nội dung dãn hết mức
        self.grid_columnconfigure((0, 1), weight=1) # Chia đôi màn hình
        
        # 3. Tiêu đề
        self.title = ctk.CTkLabel(
            self, text="Dashboard > CÀI ĐẶT CHUNG", 
            font=AppFont.H3,
            text_color=Theme.Color.TEXT
        )
        self.title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        # 4. Khung Cài đặt Điểm danh (Trái)
        # Dùng BG_CARD và Border màu BORDER
        self.widget_settings_attendace = ctk.CTkFrame(
            self, 
            fg_color=Theme.Color.BG_CARD, 
            border_color=Theme.Color.BORDER, 
            border_width=1,
            corner_radius=10
        )
        self.widget_settings_attendace.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.widget_settings_attendace.grid_columnconfigure(0, weight=1)
        self.widget_settings_attendace.grid_rowconfigure(0, weight=1)
        
        # Load nội dung con (Truyền bg_color để đồng bộ)
        self.widget_settings_attendace_content = LecturerAttendance_Setting(
            master=self.widget_settings_attendace, 
            AppConfig=self.AppcConfig,
            fg_color="transparent" # Quan trọng: Để nền trong suốt, ăn theo BG_CARD
        )
        self.widget_settings_attendace_content.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
                
        # 5. Khung Cài đặt Tài khoản (Phải)
        self.widget_settings_account = ctk.CTkFrame(
            self, 
            fg_color=Theme.Color.BG_CARD, 
            border_color=Theme.Color.BORDER, 
            border_width=1,
            corner_radius=10
        )
        self.widget_settings_account.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.widget_settings_account.grid_columnconfigure(0, weight=1)
        self.widget_settings_account.grid_rowconfigure(0, weight=1)
        
        self.widget_settings_account_content = LecturerAccount_Setting(
            master=self.widget_settings_account, 
            user=self.user, 
            AppConfig=self.AppcConfig,
            fg_color="transparent" # Quan trọng
        )
        self.widget_settings_account_content.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")