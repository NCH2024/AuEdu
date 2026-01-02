from gui.base.base_dashboard import DashboardView
from gui.base.utils import ImageSlideshow, FullLoadingScreen
import customtkinter as ctk
import core.database as Db
from core.utils import get_base_path
from core.theme_manager import ColorPalette, Theme, AppFont
import os
import threading

# Import các trang con
from gui.admin.admin_general import AdminGeneral
from gui.admin.admin_students_manager import AdminStudentsManager
from gui.admin.admin_lecturer_manager import AdminLecturerManager
from gui.admin.admin_academic import AdminAcademic
from gui.admin.admin_notice import AdminNotice

class AdminDashboard(DashboardView):
    """Tạo giao diện dashboard cho admin (Đã tối ưu)"""
    def __init__(self, master, user, config, *args, **kwargs):
        kwargs['fg_color'] = Theme.Color.BG 
        super().__init__(master, *args, **kwargs)
        
        self.user = user
        self.master.title("Dashboard Quản Trị Viên")
        self.nameAdmin = Db.get_username(self.user)
        self.AppConfig = config

        self.sidebar.configure(fg_color=Theme.Color.SECONDARY)

        # 1. Loading Screen
        self.loading_screen = FullLoadingScreen(self, text="Đang truy cập quyền quản trị...")
        self.loading_screen.lift()

        self.frames = {}
        self.slideshow = None
        self.current_page = None
        
        # 2. Khởi tạo Async
        self.after(100, self._init_components)

    def _init_components(self):
        try:
            self.loading_screen.update_status("Đang tải menu chức năng...")
            self.setup_ui_sidebar(self.nameAdmin)
            self.after(50, self.step_2_create_pages)
        except Exception as e:
            print(f"Lỗi khởi tạo Admin Dashboard: {e}")
            self.loading_screen.destroy()

    def step_2_create_pages(self):
        self.loading_screen.update_status("Đang khởi tạo các module quản lý...")
        self.pages_to_load = [
            (AdminGeneral, "Trang chủ"),
            (AdminStudentsManager, "QL Sinh viên"),
            (AdminLecturerManager, "QL Giảng viên"),
            (AdminAcademic, "QL Học vụ"),
            (AdminNotice, "QL Thông báo")
        ]
        self.load_next_page(0)

    def load_next_page(self, index):
        if index < len(self.pages_to_load):
            page_class, page_name = self.pages_to_load[index]
            self.loading_screen.update_status(f"Đang tải {page_name}...")
            try:
                try: frame = page_class(self.content, user=self.user)
                except TypeError: frame = page_class(self.content)
                
                self.frames[page_class] = frame
                frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            except Exception as e:
                print(f"Lỗi load {page_name}: {e}")
            self.after(10, lambda: self.load_next_page(index + 1))
        else:
            self.step_3_finalize()

    def step_3_finalize(self):
        self.loading_screen.update_status("Hoàn tất!")
        self.show_slideshow()
        self.update_button_highlight()
        self.after(500, self.loading_screen.destroy)

    def ButtonTheme(self, master, text, command=None, **kwargs):
        btn_config = {
            "font": AppFont.BODY_BOLD,
            "height": 45, "corner_radius": 10, "border_width": 0, "anchor": "w",
            "fg_color": "transparent", "text_color": ColorPalette.DEEP_NAVY, "hover_color": Theme.Color.BG_CARD
        }
        btn_config.update(kwargs)
        return ctk.CTkButton(master, text=text, command=command, **btn_config)
    
    def setup_ui_sidebar(self, user):
        self.infor_app = ctk.CTkLabel(self.sidebar, text="QUẢN TRỊ HỆ THỐNG\nVersion 2.0", font=AppFont.SMALL, justify="center", text_color=Theme.Color.TEXT_SUB)
        self.infor_app.pack(pady=(20, 10), padx=5, fill="x")

        self.say_hello = ctk.CTkLabel(self.sidebar, text=f"Xin chào,\n{user}", font=AppFont.H4, justify="center", anchor="center", text_color=Theme.Color.PRIMARY)
        self.say_hello.pack(pady=(20, 20), padx=5, fill="x")

        self.home_btn = self.setup_theme_button_menu(img_name="icon_home.png", text_btn="Trang chủ", command=lambda: self.show_frame(AdminGeneral))
        self.home_btn.pack(pady=(10, 0), padx=10, anchor="n", side="top")
        
    def show_slideshow(self):
        if self.slideshow and self.slideshow.winfo_exists(): self.slideshow.destroy()
        if self.AppConfig.theme_mode == "Dark":
            slide_path = os.path.join(get_base_path(), "resources", "slideshow_dark")
        else:
            slide_path = os.path.join(get_base_path(), "resources", "slideshow_light")
        
        self.slideshow = ImageSlideshow(self.content, image_folder=slide_path, delay=3000)
        self.slideshow.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self.slideshow.tkraise()
        
    def show_frame(self, page_class):
        if self.slideshow and self.slideshow.winfo_exists():
            self.slideshow.destroy()
            self.slideshow = None
        frame = self.frames[page_class]
        frame.tkraise()
        self.current_page = page_class.__name__
        self.update_button_highlight()
        
    def update_button_highlight(self):
        # 1. Cấu hình mặc định (Inactive)
        bg_normal = "transparent"
        text_normal = Theme.Color.TEXT
        hover_normal = Theme.Color.BG_CARD
        
        # 2. Xác định màu chữ cho nút Active
        mode = ctk.get_appearance_mode()
        
        if mode == "Light":
            # Active Light: Nền PRIMARY (Tối) -> Chữ TRẮNG
            bg_active = Theme.Color.PRIMARY
            text_active = ColorPalette.WHITE # Dùng từ Palette
            hover_active = Theme.Color.PRIMARY_HOVER
        else:
            # Active Dark: Nền PRIMARY (Sáng/Mint) -> Chữ XANH ĐẬM
            bg_active = Theme.Color.PRIMARY
            text_active = ColorPalette.DEEP_NAVY # Dùng từ Palette
            hover_active = Theme.Color.PRIMARY_HOVER

        buttons = {
            "AdminGeneral": getattr(self, 'home_btn', None),
            # "AdminStudentsManager": getattr(self, 'student_btn', None),
            # "AdminLecturerManager": getattr(self, 'lecturer_btn', None),
            # "AdminAcademic": getattr(self, 'academic_btn', None),
            # "AdminNotice": getattr(self, 'notice_btn', None)
        }
        for page, btn in buttons.items():
            if btn: btn.configure(fg_color=bg_active if page == self.current_page else bg_normal, text_color=text_active if page == self.current_page else text_normal, hover_color=hover_active if page == self.current_page else hover_normal)