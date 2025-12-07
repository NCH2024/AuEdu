'''
FILE NAME: gui/base_dashbroad.py
CODE BY: Nguyễn Chánh Hiệp 
DATE: 22/06/2025
DESCRIPTION:
        + Đây là lớp cơ sở (base class) cho các giao diện dạng Bảng điều khiển (Dashboard).
        + Định nghĩa bố cục chung bao gồm một thanh bên (sidebar) và một khu vực nội dung (content).
        + Cung cấp các thành phần chung như logo, nút đăng xuất và phương thức 'clear_content' để chuyển đổi giữa các trang.
VERSION: 1.0.0
'''
import customtkinter as ctk
from gui.base.base_view import BaseView
from gui.base.utils import ImageProcessor
from core.app_config import save_config, load_config
from core.utils import get_base_path
import os


class DashboardView(BaseView):
    """
    Lớp cơ sở cho các giao diện Bảng điều khiển (Dashboard).

    Kế thừa từ `BaseView` và thiết lập một bố cục hai cột tiêu chuẩn:
    - Một thanh bên (sidebar) cho điều hướng và các chức năng chung.
    - Một khu vực nội dung (content) để hiển thị các trang con.
    """
    def __init__(self, master, *args, **kwargs):
        """
        Khởi tạo giao diện Bảng điều khiển.

        Args:
            master: Widget cha (thường là một cửa sổ Toplevel).
        """
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.pack(fill="both", expand=True)
        self.configure(fg_color="#05243F")
        
        
        # Lấy cấu hình cài đặt ứng dụng
        self.AppConfig = kwargs.get('config')

        # Sidebar (menu bên trái)
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color="#05243F")
        # Content area (bên phải)
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="white")

        # Sử dụng grid thay cho pack
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.content.grid(row=0, column=1, sticky="nsew")
        
        # --- CẢI TIẾN: Cấu hình grid cho content frame ---
        # Điều này rất quan trọng để các trang con có thể xếp chồng và co giãn
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Cấu hình grid để sidebar rộng 400, content mở rộng
        self.grid_columnconfigure(0, minsize=300)      
        self.grid_columnconfigure(1, weight=1)         
        self.grid_rowconfigure(0, weight=1)            

        # Thêm hình ảnh logo
        base_path = get_base_path()
        self.bg_ctkimage = ImageProcessor(os.path.join(base_path, "resources","images","dnc.png")) \
                                .crop_to_aspect(150, 150) \
                                .resize(150, 150) \
                                .to_ctkimage(size=(150, 150))

        self.bg_label = ctk.CTkLabel(self.sidebar, image=self.bg_ctkimage, text="")
        self.bg_label.pack(pady=10, padx=5)
        
        self.btn_logout = self.ButtonTheme(self.sidebar, "Đăng xuất",font=("Bahnschrift", 12, "normal"),height=30, width=120, fg_color="#73B8E9", hover_color="blue", command=self.logout)
        self.btn_logout.pack(pady=5, padx=5, anchor="s", fill="y")
        
    def clear_content(self):
        """
        Xóa tất cả các widget con khỏi khu vực nội dung (content frame).

        Phương thức này được sử dụng để dọn dẹp giao diện trước khi hiển thị một trang mới,
        đảm bảo không có widget cũ nào còn sót lại.
        """
        for widget in self.content.winfo_children():
            widget.destroy()
            
            
    def logout(self):
        """
        Xử lý sự kiện đăng xuất (CHO CẤU TRÚC 1 CỬA SỔ)
        
        Phương thức này sẽ hủy frame dashboard hiện tại và 
        tái tạo lại frame đăng nhập (MainWindow) bên trong 'root'.
        """
        
        # Import local để tránh lỗi 'circular import' (lỗi nhập vòng)
        from gui.main_window import MainWindow 
        
        # 1. Xóa thông tin đăng nhập đã lưu
        if self.AppConfig:
            self.AppConfig.login_info.username = None
            self.AppConfig.login_info.password = None
            save_config(self.AppConfig)
        
        # 2. Lấy cửa sổ 'root' (chính là self.master)
        root = self.master 
        
        # 3. Hủy frame Dashboard HIỆN TẠI (chính là 'self')
        self.destroy()
        
        # 4. Tái tạo lại frame Đăng nhập (MainWindow)
        app_login = MainWindow(master=root, config=self.AppConfig)
        app_login.pack(expand=True, fill="both")
        
        # 5. Reset cửa sổ root về trạng thái đăng nhập
        root.state('normal')
        root.title("PHẦN MỀM ĐIỂM DANH")
        root.geometry("1280x720") # Đặt lại kích thước cho màn hình login
        root.resizable(False, False) # Khóa màn hình login