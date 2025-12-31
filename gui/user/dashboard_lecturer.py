from gui.base.base_dashboard import DashboardView
from gui.base.utils import ImageSlideshow, FullLoadingScreen # Import FullLoadingScreen
from gui.user.lecturer_home import LecturerHome
from gui.user.lecturer_attendance import LecturerAttendance
from gui.user.lecturer_schedule import LecturerSchedule
from gui.user.lecturer_settings import LecturerSettings
from gui.user.lecturer_statistical import LecturerStatistical
import customtkinter as ctk
import core.database as Db  
from core.utils import get_base_path
from core.theme_manager import Theme, AppFont, ColorPalette
import os   
import pygame 
import threading

class LecturerDashboard(DashboardView):
    """Tạo giao diện dashboard cho giảng viên."""
    def __init__(self, master, user, config, *args, **kwargs):
        # Set màu nền chính từ Theme
        kwargs['fg_color'] = Theme.Color.BG 
        super().__init__(master, *args, **kwargs)
        
        self.user = user
        self.master.title("Dashboard Giảng Viên")
        self.nameLecturer = Db.get_username(self.user)
        self.AppConfig = config
        
        # Cấu hình màu sắc Sidebar
        self.sidebar.configure(fg_color=Theme.Color.SECONDARY)

        # 1. HIỆN LOADING SCREEN NGAY LẬP TỨC
        self.loading_screen = FullLoadingScreen(self, text="Đang khởi động hệ thống...")
        self.loading_screen.lift() 
        
        self.frames = {} 
        self.slideshow = None 
        self.current_page = None 
        
        # 2. BẮT ĐẦU QUY TRÌNH KHỞI TẠO TỪNG BƯỚC
        # Gọi hàm khởi tạo thành phần sau 100ms để UI kịp hiển thị Loading Screen
        self.after(100, self._init_components)

    def _init_components(self):
        """Hàm chứa các tác vụ khởi tạo nặng, được chia nhỏ"""
        try:
            # 1. KHỞI TẠO ÂM THANH (CHẠY NGẦM)
            threading.Thread(target=self._init_sound_system, daemon=True).start()

            # 2. Setup Sidebar (Bước 1)
            self.loading_screen.update_status("Đang thiết lập giao diện...")
            self.setup_ui_sidebar(self.nameLecturer)
            
            # 3. Chuyển sang tạo các trang con (Bước 2)
            self.after(50, self.step_2_create_pages)
            
        except Exception as e:
            print(f"Lỗi khởi tạo Dashboard: {e}")
            self.loading_screen.destroy()

    def _init_sound_system(self):
        """Hàm khởi tạo âm thanh trong luồng phụ"""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
                print("Âm thanh đã sẵn sàng!")
        except Exception as e:
            print(f"Lỗi khởi tạo âm thanh: {e}")

    def step_2_create_pages(self):
        """Bước 2: Tạo các trang con (Nặng nhất)"""
        self.loading_screen.update_status("Đang khởi tạo các mô-đun chức năng...")
        
        # Danh sách các trang cần tạo
        self.pages_to_load = [
            (LecturerHome, "Trang chủ"),
            (LecturerAttendance, "Điểm danh"), 
            (LecturerSchedule, "Lịch dạy"),
            (LecturerStatistical, "Thống kê"),
            (LecturerSettings, "Cài đặt")
        ]
        self.load_next_page(0) # Bắt đầu load trang đầu tiên

    def load_next_page(self, index):
        """Hàm đệ quy để load từng trang một"""
        if index < len(self.pages_to_load):
            page_class, page_name = self.pages_to_load[index]
            
            # Update text loading
            self.loading_screen.update_status(f"Đang tải {page_name}...")
            
            # Tạo trang
            if page_class == LecturerHome:
                frame = page_class(self.content, username=self.user)
            elif page_class == LecturerAttendance:
                frame = page_class(self.content, username=self.user, config=self.AppConfig)
            elif page_class == LecturerSchedule:
                frame = page_class(self.content, lecturer_username=self.user)
            elif page_class == LecturerStatistical:
                frame = page_class(self.content, username=self.user)
            elif page_class == LecturerSettings:
                frame = page_class(self.content, user=self.user, AppConfig=self.AppConfig)
            else:
                frame = page_class(self.content)

            self.frames[page_class] = frame
            frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
            # Gọi đệ quy để load trang tiếp theo sau 1 khoảng nghỉ ngắn (10ms)
            self.after(10, lambda: self.load_next_page(index + 1))
            
        else:
            # Khi đã load hết các trang -> Sang bước cuối
            self.step_3_finalize()

    def step_3_finalize(self):
        """Bước 3: Hoàn tất"""
        self.loading_screen.update_status("Hoàn tất!")
        self.show_slideshow()
        self.update_button_highlight()
        
        # Hủy loading screen sau 500ms
        self.after(500, self.loading_screen.destroy)

    def ButtonTheme(self, master, text, command=None, **kwargs):
        """
        Hàm tạo nút thông minh:
        - Tự động dùng style Menu (trong suốt, chữ đậm) nếu không có tham số gì.
        - Tự động dùng style của Base (nút Logout màu xanh) nếu có tham số truyền vào.
        """
        # 1. Định nghĩa cấu hình MẶC ĐỊNH cho nút Menu Sidebar
        btn_config = {
            "font": AppFont.BODY_BOLD,
            "height": 45,
            "corner_radius": 10,
            "border_width": 0,
            "anchor": "w",             # Canh lề trái
            "fg_color": "transparent", # Nền trong suốt
            "text_color": Theme.Color.TEXT,
            "hover_color": Theme.Color.BG_CARD
        }

        # 2. Ghi đè cấu hình nếu có tham số từ bên ngoài (kwargs)
        btn_config.update(kwargs)

        # 3. Tạo nút với cấu hình đã hợp nhất
        return ctk.CTkButton(
            master, 
            text=text, 
            command=command,
            **btn_config
        )
    
    def setup_ui_sidebar(self, user):
        """Thiết lập Sidebar bên trái."""
        # 1. Thông tin App
        self.infor_app = ctk.CTkLabel(
            self.sidebar, 
            text="Dev. Nguyen Chanh Hiep\nGitHub: @NCH2024\n\nAuEdu FaceID\nĐiểm danh bằng khuôn mặt", 
            font=AppFont.SMALL, 
            justify="center", 
            text_color=Theme.Color.TEXT_SUB
        )
        self.infor_app.pack(pady=(20, 10), padx=5, fill="x")
        
        # 2. Lời chào
        self.say_hello = ctk.CTkLabel(
            self.sidebar, 
            text=f"Xin chào,\n{user}", 
            font=AppFont.H2, 
            justify="left", 
            anchor="w",
            text_color=Theme.Color.PRIMARY # Tên người dùng màu nổi bật
        )
        self.say_hello.pack(pady=(0, 20), padx=30, fill="x")
        
        # 3. Danh sách nút Menu
        self.home_btn = self.ButtonTheme(self.sidebar, "🏠  TRANG CHỦ", font=AppFont.BODY_BOLD, command=lambda: self.show_frame(LecturerHome))
        self.home_btn.pack(pady=5, padx=20, fill="x")

        self.attendance_btn = self.ButtonTheme(self.sidebar, "📸  ĐIỂM DANH", font=AppFont.BODY_BOLD, command=lambda: self.show_frame(LecturerAttendance))
        self.attendance_btn.pack(pady=5, padx=20, fill="x")
        
        self.schedule_btn = self.ButtonTheme(self.sidebar, "📅  LỊCH DẠY", font=AppFont.BODY_BOLD, command=lambda: self.show_frame(LecturerSchedule))
        self.schedule_btn.pack(pady=5, padx=20, fill="x")

        self.statistical_btn = self.ButtonTheme(self.sidebar, "📊  THỐNG KÊ", font=AppFont.BODY_BOLD, command=lambda: self.show_frame(LecturerStatistical))
        self.statistical_btn.pack(pady=5, padx=20, fill="x")
        
        self.setting_btn = self.ButtonTheme(self.sidebar, "⚙  CÀI ĐẶT", font=AppFont.BODY_BOLD, command=lambda: self.show_frame(LecturerSettings))
        self.setting_btn.pack(pady=5, padx=20, fill="x")

    def show_slideshow(self):
        """Hiển thị Slideshow Responsive Full Panel."""
        if self.slideshow and self.slideshow.winfo_exists():
            self.slideshow.destroy()
        if self.AppConfig.theme_mode == "Dark":
            slide_path = os.path.join(get_base_path(), "resources", "slideshow_dark")
        else:
            slide_path = os.path.join(get_base_path(), "resources", "slideshow_light")

        self.slideshow = ImageSlideshow(self.content, image_folder=slide_path, delay=3000)
        
        # Grid fill toàn bộ khung content
        self.slideshow.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        # Đảm bảo khung cha (self.content) cho phép giãn
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        
        self.slideshow.tkraise()

    def show_frame(self, page_class):
        """Chuyển trang."""
        # 1. Hủy slideshow
        if self.slideshow and self.slideshow.winfo_exists():
            self.slideshow.destroy()
            self.slideshow = None
            
        # 2. Nâng trang cần xem lên trên cùng
        frame = self.frames[page_class]
        frame.tkraise() 
        
        # 3. Cập nhật trạng thái nút
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
                "LecturerHome": self.home_btn,
                "LecturerAttendance": self.attendance_btn,
                "LecturerSchedule": self.schedule_btn,
                "LecturerStatistical": self.statistical_btn,
                "LecturerSettings": self.setting_btn
            }

            for page_name, btn in buttons.items():
                if page_name == self.current_page:
                    # Active: Áp dụng màu nền, màu chữ tương phản và màu hover mới
                    btn.configure(fg_color=bg_active, text_color=text_active, hover_color=hover_active)
                else:
                    # Inactive
                    btn.configure(fg_color=bg_normal, text_color=text_normal, hover_color=hover_normal)