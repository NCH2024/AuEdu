'''
FILE NAME: gui/base/base_dashboard.py
DESCRIPTION: Lớp cơ sở cho Dashboard (Đã sửa nút Đăng xuất chuẩn Theme).
'''
import customtkinter as ctk
from gui.base.base_view import BaseView
from gui.base.utils import ImageProcessor
from core.app_config import save_config, load_config
from core.utils import get_base_path
import os
from core.theme_manager import Theme, AppFont, ColorPalette
from tkinter import messagebox

class DashboardView(BaseView):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.pack(fill="both", expand=True)
        
        # Lấy cấu hình cài đặt ứng dụng
        self.AppConfig = kwargs.get('config')

        # Sidebar (menu bên trái)
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color=Theme.Color.BG_CARD)
        # Content area (bên phải)
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="white")

        # Grid Layout
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.content.grid(row=0, column=1, sticky="nsew")
        
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.grid_columnconfigure(0, minsize=300)      
        self.grid_columnconfigure(1, weight=1)         
        self.grid_rowconfigure(0, weight=1)            

        # Logo
        base_path = get_base_path()
        try:
            self.bg_ctkimage = ImageProcessor(os.path.join(base_path, "resources","images","logo.png")) \
                                    .crop_to_aspect(467, 213) \
                                    .resize(232, 105) \
                                    .to_ctkimage(size=(232,105))
            self.bg_label = ctk.CTkLabel(self.sidebar, image=self.bg_ctkimage, text="")
            self.bg_label.pack(pady=10, padx=5)
        except Exception as e:
            print(f"Lỗi load logo: {e}")

        # --- NÚT ĐĂNG XUẤT (Giữ nguyên) ---
        self.btn_logout = self.ButtonTheme(
            self.sidebar, 
            "Đăng xuất",
            font=AppFont.BODY_BOLD,
            height=40, 
            width=200,
            anchor="center",
            fg_color=ColorPalette.BLUE_INFO,  # Màu xanh dương nổi bật
            command=self.logout
        )
        self.btn_logout.pack(pady=20, padx=20, anchor="s", side="bottom")

        # --- NÚT ĐỔI GIAO DIỆN (Thêm mới) ---
        self.setup_theme_button()
        
    def setup_theme_button(self):
        """Tạo nút đổi giao diện nổi bật"""
        base_path = get_base_path()
        icon_img = None
        try:
            # Em nhớ đổi tên file ảnh ở đây nếu khác
            icon_path = os.path.join(base_path, "resources", "images", "icon_darkmode.png") 
            if os.path.exists(icon_path):
                 icon_img = ImageProcessor(icon_path).resize(24, 24).to_white_icon().to_ctkimage()
        except:
            pass

        # Xác định Text và Icon dựa trên chế độ hiện tại
        current_mode = ctk.get_appearance_mode()
        is_dark = current_mode == "Dark"
        text_btn = "Chế độ sáng" if is_dark else "Chế độ tối"
        
        # Nút dùng màu WARNING (Cam) hoặc INFO (Xanh) để nổi bật
        self.btn_theme = self.ButtonTheme(
            self.sidebar,
            text=text_btn,
            image=icon_img,
            font=AppFont.BODY_BOLD,
            height=40,
            width=200,
            anchor="center",
            fg_color=Theme.Color.WARNING, # Màu cam nổi bật
            hover_color="#F57C00",        # Màu hover cam đậm
            text_color="white",
            command=self.toggle_theme
        )
        self.btn_theme.pack(pady=(10, 0), padx=20, anchor="s", side="bottom")

    def toggle_theme(self):
        """Xử lý đổi theme và tự động đăng nhập lại"""
        msg = "Để thay đổi giao diện, ứng dụng cần \n\n        ĐĂNG NHẬP LẠI\n\nđể tiếp tục!.\nBạn có muốn tiếp tục không?"
        if messagebox.askyesno("Xác nhận đổi giao diện", msg):
            # 1. Đảo ngược chế độ
            current_mode = ctk.get_appearance_mode()
            new_mode = "Light" if current_mode == "Dark" else "Dark"
            
            # 2. Lưu Theme mới vào Config
            if self.AppConfig:
                try:
                    self.AppConfig.theme_mode = new_mode
                    save_config(self.AppConfig)
                except Exception as e:
                    print(f"Lỗi lưu config theme: {e}")
            
            # 3. Gọi logout với cờ auto_login=True
            self.logout(auto_login=True)

    def logout(self, auto_login=False):
        from gui.main_window import MainWindow 
        
        # 1. Xử lý lưu/xóa Config
        if self.AppConfig:
            # NẾU LÀ ĐĂNG XUẤT THẬT (auto_login=False): Xóa thông tin đã lưu trong RAM
            if not auto_login:
                self.AppConfig.login_info.username = None
                self.AppConfig.login_info.password = None
                # Lưu xuống file để lần sau mở app lên cũng không tự vào
                save_config(self.AppConfig)
            
            # NẾU LÀ ĐỔI THEME (auto_login=True): Giữ nguyên info để tí nữa dùng lại
        
        # 2. Nạp lại Theme
        if hasattr(self.AppConfig, "theme_mode"):
            Theme.load_theme(self.AppConfig.theme_mode)

        root = self.master 
        self.destroy()
        
        # 3. Tạo lại màn hình đăng nhập
        app_login = MainWindow(master=root, config=self.AppConfig)
        app_login.pack(expand=True, fill="both")
        
        root.state('normal')
        root.title("PHẦN MỀM ĐIỂM DANH")
        root.geometry("1280x720") 
        root.resizable(False, False)

        # 4. LOGIC TỰ ĐỘNG ĐĂNG NHẬP (Chỉ chạy khi auto_login=True)
        if auto_login and self.AppConfig.login_info.username and self.AppConfig.login_info.password:
            # Tự điền thông tin vào ô
            app_login.username_entry.insert(0, self.AppConfig.login_info.username)
            app_login.password_entry.insert(0, self.AppConfig.login_info.password)
            app_login.check_save_login.select()
            
            # Tự bấm nút đăng nhập
            app_login.start_login_process()