from gui.base.base_dashboard import DashboardView
from gui.base.utils import ImageSlideshow, LoadingDialog
from gui.user.lecturer_home import LecturerHome
from gui.user.lecturer_attendance import LecturerAttendance
from gui.user.lecturer_schedule import LecturerSchedule
from gui.user.lecturer_settings import LecturerSettings
from gui.user.lecturer_statistical import LecturerStatistical
import customtkinter as ctk
import core.database as Db  
from core.utils import get_base_path
import os   
import threading


class LecturerDashboard(DashboardView):
    """Tạo giao diện dashboard cho giảng viên."""
    def __init__(self, master, user, config, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.user = user
        self.master.title("Dashboard Giảng Viên")
        self.nameLecturer = Db.get_username(self.user)
        self.AppConfig = config
        
        # --- CẢI TIẾN: KIẾN TRÚC STACKING FRAMES ---
        self.frames = {} # Dictionary để lưu các frame trang con
        self.slideshow = None # Biến để giữ slideshow
        self.current_page = None # Lưu trang hiện tại
        
        self._create_pages() # Tạo tất cả các trang một lần
        self.setup_ui_sidebar(self.nameLecturer)
        
        # --- CẢI TIẾN: Hiển thị slideshow ban đầu ---
        self.show_slideshow()
        self.update_button_highlight() # Đảm bảo không có nút nào được chọn
        
    def ButtonTheme(self, master, text, font=("Bahnschrift", 18, "bold"), fg_color="#31FCA1", hover_color="#00C785", txt_color="#05243F", border_color="white", border_width=2, command=None, **kwargs):
        return super().ButtonTheme(
            master, text, font, fg_color, hover_color, border_color, border_width, command, text_color=txt_color, **kwargs
        )
    
    def setup_ui_sidebar(self, user):
        """Thiết lập các thành phần giao diện."""
        self.infor_app = ctk.CTkLabel(self.sidebar, text="GitHub dự án:@NCH2024\nỨng dụng điểm danh bằng nhận diện khuôn mặt\nĐồ án sinh viên thực hiện.", font=("Bahnschrift", 10, "normal"), justify="center", height=80, text_color="white")
        self.infor_app.pack(pady=5, padx=5, fill="x")
        
        self.say_hello = ctk.CTkLabel(self.sidebar, text=f"Xin chào\n{user}!", font=("Bahnschrift", 18, "bold"), justify="left", height=80, text_color="white")
        self.say_hello.pack(pady=20, padx=10, fill="x")
        
        # Cập nhật command của các nút để gọi hàm show_frame
        self.home_btn = self.ButtonTheme(self.sidebar, "Trang chủ", height=50, command=lambda: self.show_frame(LecturerHome))
        self.home_btn.pack(pady=10, padx=30, fill="x")
        
        self.attendance_btn = self.ButtonTheme(self.sidebar, "Điểm danh", height=50, command=lambda: self.show_frame(LecturerAttendance))
        self.attendance_btn.pack(pady=10, padx=30, fill="x")
        
        self.schedule_btn = self.ButtonTheme(self.sidebar, "Lịch điểm danh", height=50, command=lambda: self.show_frame(LecturerSchedule))
        self.schedule_btn.pack(pady=10, padx=30, fill="x")

        self.statistical_btn = self.ButtonTheme(self.sidebar, "Thống kê", height=50, command=lambda: self.show_frame(LecturerStatistical))
        self.statistical_btn.pack(pady=10, padx=30, fill="x")
        
        self.setting_btn = self.ButtonTheme(self.sidebar, "Cài đặt", height=50, command=lambda: self.show_frame(LecturerSettings))
        self.setting_btn.pack(pady=10, padx=30, fill="x")
        
    # --- CÁC HÀM MỚI ĐỂ QUẢN LÝ FRAME ---
    
    def _create_pages(self):
        """Tạo tất cả các frame trang con và đặt chúng chồng lên nhau."""
        # Danh sách các lớp trang con cần tạo
        pages = (LecturerHome, LecturerAttendance, LecturerSchedule, LecturerStatistical, LecturerSettings)
        
        for F in pages:
            # Tạo một instance của trang
            # Lưu ý: truyền các tham số cần thiết cho từng trang
            if F == LecturerHome:
                frame = F(self.content, username=self.user)
            elif F == LecturerAttendance:
                frame = F(self.content, username=self.user, config=self.AppConfig)
            elif F == LecturerSchedule:
                frame = F(self.content, lecturer_username=self.user)
            elif F == LecturerStatistical:
                frame = F(self.content, username=self.user)
            elif F == LecturerSettings:
                frame = F(self.content, user=self.user, AppConfig=self.AppConfig)
            else:
                frame = F(self.content)

            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
    def show_slideshow(self):
        """Tạo và hiển thị slideshow."""
        # Hủy slideshow cũ nếu có
        if self.slideshow and self.slideshow.winfo_exists():
            self.slideshow.destroy()
            
        slide_path = os.path.join(get_base_path(), "resources","slideshow","user")
           
        self.slideshow = ImageSlideshow(self.content, image_folder=slide_path, size=(1024, 768), delay=3000)
        self.slideshow.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.slideshow.tkraise() # Đưa slideshow lên trên cùng

    def show_frame(self, page_class):
        """Nâng frame của lớp được chỉ định lên trên cùng."""
        # Hủy slideshow nếu nó đang tồn tại
        if self.slideshow and self.slideshow.winfo_exists():
            self.slideshow.destroy()
            self.slideshow = None
            
        frame = self.frames[page_class]
        frame.tkraise() # Đây là lệnh chính để chuyển trang
        self.current_page = page_class.__name__ # Lưu tên lớp để highlight nút
        self.update_button_highlight()
    
    def update_button_highlight(self):
        # Reset màu tất cả nút
        normal_color = "#31FCA1"
        hover_color = "#00C785"
        active_color = "#0E8EE9"  # Màu khi được chọn

        self.home_btn.configure(fg_color=normal_color, hover_color=hover_color)
        self.attendance_btn.configure(fg_color=normal_color, hover_color=hover_color)
        self.schedule_btn.configure(fg_color=normal_color, hover_color=hover_color)
        self.statistical_btn.configure(fg_color=normal_color, hover_color=hover_color)
        self.setting_btn.configure(fg_color=normal_color, hover_color=hover_color)

        # Tô đậm nút đang được chọn
        if self.current_page == "LecturerHome":
            self.home_btn.configure(fg_color=active_color)
        elif self.current_page == "LecturerAttendance":
            self.attendance_btn.configure(fg_color=active_color)
        elif self.current_page == "LecturerSchedule":
            self.schedule_btn.configure(fg_color=active_color)
        elif self.current_page == "LecturerStatistical":
            self.statistical_btn.configure(fg_color=active_color)
        elif self.current_page == "LecturerSettings":
            self.setting_btn.configure(fg_color=active_color)
