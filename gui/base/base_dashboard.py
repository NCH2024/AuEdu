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
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=Theme.Color.BG_CARD)
        # Content area (bên phải)
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="white")

        # Grid Layout
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.propagate(False)  # Giữ nguyên kích thước sidebar
        self.content.grid(row=0, column=1, sticky="nsew")
        
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.grid_columnconfigure(0, minsize=200)      
        self.grid_columnconfigure(1, weight=1)         
        self.grid_rowconfigure(0, weight=1)            

        # Logo
        base_path = get_base_path()
        try:
            self.bg_ctkimage = ImageProcessor(os.path.join(base_path, "resources","images","logo.png")) \
                                    .crop_to_aspect(467, 213) \
                                    .resize(187, 85) \
                                    .to_ctkimage(size=(187,85))
            self.bg_label = ctk.CTkLabel(self.sidebar, image=self.bg_ctkimage, text="")
            self.bg_label.pack(pady=(30,30), padx=5, fill="x")
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
        self.btn_logout.pack(pady=20, padx=10, anchor="s", side="bottom")

        # --- NÚT ĐỔI GIAO DIỆN (Thêm mới) ---
        self.setup_theme_button()
        
    def setup_theme_button(self):
        """Tạo nút đổi giao diện nổi bật"""
        base_path = get_base_path()
        icon_img = None
        try:
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
        self.btn_theme.pack(pady=(10, 0), padx=10, anchor="s", side="bottom")

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
            
    def setup_theme_button_menu(self, img_name=None, text_btn=None, command=None):
        base_path = get_base_path()
        icon_img_white = None
        icon_img_black = None
        try:
            icon_path = os.path.join(base_path, "resources", "images", f"{img_name}") 
            if os.path.exists(icon_path):
                # Tạo sẵn 2 phiên bản màu để chuyển đổi nhanh
                icon_img_white = ImageProcessor(icon_path).resize(24, 24).to_white_icon().to_ctkimage()
                icon_img_black = ImageProcessor(icon_path).resize(24, 24).to_ctkimage()
        except:
            pass

        my_button = self.ButtonTheme(
            self.sidebar,
            text=f"      {text_btn}", # Thêm 6 khoảng trắng trước chữ để giãn cách với icon
            image=icon_img_black if ctk.get_appearance_mode() == "Light" else icon_img_white,
            font=AppFont.H6,
            height=45,          # Tăng chiều cao lên một chút cho thoáng
            width=200,         # Cố định chiều rộng để các nút bằng nhau
            anchor="w",         # CĂN TRÁI TOÀN BỘ
            compound="left",    # ICON BÊN TRÁI CHỮ
            command=command
        )
        
        my_button.icon_white = icon_img_white
        my_button.icon_black = icon_img_black

        # (Giữ nguyên logic hover em đã viết ở dưới)
        def on_hover(event):
            my_button.configure(image=icon_img_white)

        def on_leave(event):
            if ctk.get_appearance_mode() == "Light":
                my_button.configure(image=icon_img_black)
            else:
                my_button.configure(image=icon_img_white)

        my_button.bind("<Enter>", on_hover) 
        my_button.bind("<Leave>", on_leave) 
        return my_button