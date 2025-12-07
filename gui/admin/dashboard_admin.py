from gui.base.base_dashboard import DashboardView
from gui.base.utils import ImageSlideshow
import customtkinter as ctk
import core.database as Db
from core.utils import get_base_path
import os
import threading
from gui.admin.admin_general import AdminGeneral
from gui.admin.admin_students_manager import AdminStudentsManager
from gui.admin.admin_lecturer_manager import AdminLecturerManager
from gui.admin.admin_academic import AdminAcademic
from gui.admin.admin_notice import AdminNotice

class AdminDashboard(DashboardView):
    """Tạo giao diện dashboard cho admin"""
    def __init__(self, master, user, config,*args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.user = user
        self.master.title("Dashboard Admin")
        self.nameAdmin = Db.get_username(self.user)
        self.AppConfig = config

        # --- CẢI TIẾN: KIẾN TRÚC STACKING FRAMES ---
        self.frames = {}
        self.slideshow = None
        self.current_page = None
        self._create_pages()
        self.setup_ui_sidebar(self.nameAdmin)
        
        # --- CẢI TIẾN: Hiển thị slideshow ban đầu ---
        self.show_slideshow()
        self.update_button_highlight()

    def ButtonTheme(self, master, text, font=("Bahnschrift", 18, "bold"), fg_color="#31FCA1", hover_color="#00C785", txt_color="#05243F", border_color="white", border_width=2, command=None, **kwargs):
        return super().ButtonTheme(
            master, text, font, fg_color, hover_color, border_color, border_width, command, text_color=txt_color, **kwargs
        )
    
    def setup_ui_sidebar(self, user):
        """Thiết lập các thành phần giao diện."""
        self.infor_app = ctk.CTkLabel(self.sidebar, text="QUẢN TRỊ HỆ THỐNG\nGitHub dự án:@NCH2024\nỨng dụng điểm danh bằng nhận diện khuôn mặt\nĐồ án sinh viên thực hiện.", font=("Bahnschrift", 10, "normal"), justify="center", height=80, text_color="white")
        self.infor_app.pack(pady=5, padx=5, fill="x")
        
        self.say_hello = ctk.CTkLabel(self.sidebar, text=f"Xin chào\n{user}!", font=("Bahnschrift", 18, "bold"), justify="left", height=80, text_color="white")
        self.say_hello.pack(pady=20, padx=10, fill="x")
        # Thêm các nút hoặc thành phần khác vào sidebar
        self.home_btn = self.ButtonTheme(self.sidebar, "Trang chủ", height=50, command=lambda: self.show_frame(AdminGeneral))
        self.home_btn.pack(pady=10, padx=30, fill="x")
        
        # self.student_btn = self.ButtonTheme(self.sidebar, "Quản lý SV & Lớp", height=50, command=lambda: self.show_frame(AdminStudentsManager))
        # self.student_btn.pack(pady=10, padx=30, fill="x")
        
        # self.lecturer_btn = self.ButtonTheme(self.sidebar, "Quản lý GV & Khoa", height=50, command=lambda: self.show_frame(AdminLecturerManager))
        # self.lecturer_btn.pack(pady=10, padx=30, fill="x")
        
        # self.academic_btn = self.ButtonTheme(self.sidebar, "Quản lý Học vụ", height=50, command=lambda: self.show_frame(AdminAcademic))
        # self.academic_btn.pack(pady=10, padx=30, fill="x")
        
        # self.notice_btn = self.ButtonTheme(self.sidebar, "Quản lý Thông báo", height=50, command=lambda: self.show_frame(AdminNotice))
        # self.notice_btn.pack(pady=10, padx=30, fill="x")
        
    def _create_pages(self):
        """Tạo tất cả các frame trang con và đặt chúng chồng lên nhau."""
        pages = (AdminGeneral, AdminStudentsManager, AdminLecturerManager, AdminAcademic, AdminNotice)
        
        for F in pages:
            frame = F(self.content, user=self.user)
            self.frames[F] = frame
            frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            
    def show_slideshow(self):
        """Tạo và hiển thị slideshow."""
        if self.slideshow and self.slideshow.winfo_exists():
            self.slideshow.destroy()
          
        slide_path = os.path.join(get_base_path(), "resources","slideshow","admin")
       
        self.slideshow = ImageSlideshow(self.content, image_folder=slide_path, size=(1024, 768), delay=3000)
        self.slideshow.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.slideshow.tkraise()
        
    def show_frame(self, page_class):
        """Nâng frame của lớp được chỉ định lên trên cùng."""
        if self.slideshow and self.slideshow.winfo_exists():
            self.slideshow.destroy()
            self.slideshow = None
            
        frame = self.frames[page_class]
        frame.tkraise()
        self.current_page = page_class.__name__
        self.update_button_highlight()
        
    def update_button_highlight(self):
        # Reset màu tất cả nút
        normal_color = "#31FCA1"
        hover_color = "#00C785"
        active_color = "#0E8EE9"  # Màu khi được chọn
        
        self.home_btn.configure(fg_color=normal_color, hover_color=hover_color)
        # self.student_btn.configure(fg_color=normal_color, hover_color=hover_color)
        # self.lecturer_btn.configure(fg_color=normal_color, hover_color=hover_color)
        # self.academic_btn.configure(fg_color=normal_color, hover_color=hover_color)
        # self.notice_btn.configure(fg_color=normal_color, hover_color=hover_color)

        # Tô đậm nút đang được chọn
        if self.current_page == "AdminGeneral":
            self.home_btn.configure(fg_color=active_color)
        # elif self.current_page == "AdminStudentsManager":
        #     self.student_btn.configure(fg_color=active_color)
        # elif self.current_page == "AdminLecturerManager":
        #     self.lecturer_btn.configure(fg_color=active_color)
        # elif self.current_page == "AdminAcademic":
        #     self.academic_btn.configure(fg_color=active_color)
        # elif self.current_page == "AdminNotice":
        #     self.notice_btn.configure(fg_color=active_color)
