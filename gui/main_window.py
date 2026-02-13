from tkinter import messagebox
import tkinter as tk
import customtkinter as ctk
import os
import threading

# Import Core & Base
from gui.base.base_view import BaseView
from gui.base.utils import ImageProcessor, LoadingDialog
from core.theme_manager import FontLoader, Theme, AppFont
from core.app_config import load_config, save_config
import core.database 
from core.utils import get_base_path

# Import Dashboard
from gui.user.dashboard_lecturer import LecturerDashboard
from gui.admin.dashboard_admin import AdminDashboard

class MainWindow(BaseView):
    def __init__(self, master, config):
        # BaseView đã tự set màu nền theo Theme.Color.BG
        super().__init__(master) 
        self.AppConfig = config

        # --- SIDEBAR (Bên trái) ---
        self.sidebar = ctk.CTkFrame(self, width=450, 
                                    corner_radius=20, # Bo góc mạnh
                                    fg_color=Theme.Color.SECONDARY)
        # Sử dụng padx, pady để tạo khoảng cách với lề, giúp nó "nổi" lên trên hình nền
        self.sidebar.pack(side="left", fill="y", padx=(20, 20), pady=20)
        
        # --- CONTENT (Bên phải - Hình nền) ---
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=Theme.Color.BG)
        self.content.pack(side="right", fill="both", expand=True)
        
        # Xử lý hình nền
        base_path = get_base_path()
        try:
            self.bg_ctkimage = ImageProcessor(os.path.join(base_path, "resources","images","bg_main_window.png")) \
                                    .crop_to_aspect(1280, 720) \
                                    .resize(1280, 720) \
                                    .to_ctkimage(size=(1280,720))
            self.bg_label = ctk.CTkLabel(self.content, image=self.bg_ctkimage, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Lỗi load ảnh nền: {e}")
            
        self.setup_ui()
        self.password_entry.bind("<Return>", lambda event: self.start_login_process())
        
    def setup_ui(self):
        # 1. Tiêu đề trường
        text_var_first = tk.StringVar(value="KHOA CÔNG NGHỆ THÔNG TIN\nTRƯỜNG ĐẠI HỌC NAM CẦN THƠ\n---------------\n\nĐỒ ÁN TỐT NGHIỆP")
        self.tittle_first_label = self.LabelFont(self.sidebar, text=text_var_first,
                                                  font=AppFont.H3, # Dùng Font Inter
                                                  text_color=Theme.Color.TEXT,
                                                  width=400, height=80)
        self.tittle_first_label.place(relx=0.5, rely=0.1, anchor="center")
        
        # 2. Tiêu đề phần mềm
        text_var = tk.StringVar(value="PHẦN MỀM ĐIỂM DANH")
        text_var2 = tk.StringVar(value="(Bằng công nghệ nhận dạng khuôn mặt)")
        
        self.title_label = self.LabelFont(self.sidebar, text=text_var, font=AppFont.H1, 
                                          text_color=Theme.Color.PRIMARY, width=400, height=50) # Màu nhấn
        self.title_label.place(relx=0.5, rely=0.35, anchor="center")
        
        self.tittle_label2 = self.LabelFont(self.sidebar, text=text_var2, font=AppFont.BODY_BOLD, 
                                            text_color=Theme.Color.TEXT_SUB)
        self.tittle_label2.place(relx=0.5, rely=0.4, anchor="center")

        # 3. Form đăng nhập
        self.username_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Tên đăng nhập", 
                                            width=250, height=45, font=AppFont.BODY,
                                            border_color=Theme.Color.BORDER)
        self.username_entry.place(relx=0.5, rely=0.5, anchor="center")
          
        self.password_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Mật khẩu", show="*", 
                                            width=250, height=45, font=AppFont.BODY,
                                            border_color=Theme.Color.BORDER)
        self.password_entry.place(relx=0.5, rely=0.58, anchor="center")
        
        self.check_save_login = ctk.CTkCheckBox(self.sidebar, text="Lưu đăng nhập", 
                                                text_color=Theme.Color.TEXT, 
                                                font=AppFont.BODY,
                                                command=self.on_check_save_login)
        self.check_save_login.place(relx=0.5, rely=0.65, anchor="center")

        # 4. Nút đăng nhập (Dùng hàm ButtonTheme đã tối ưu)
        self.login_button = self.ButtonTheme(self.sidebar, "Đăng nhập", 
                                             width=250, height=50, 
                                             command=self.start_login_process)
        self.login_button.place(relx=0.5, rely=0.75, anchor="center")

        # 5. Footer
        text_var_second = tk.StringVar(value="Sinh viên: NGUYỄN CHÁNH HIỆP \n Mã số sinh viên: 223408 \n Lớp: 22TIN-TT \n\n Tháng 6/2025")
        self.tittle_second_label = self.LabelFont(self.sidebar, text=text_var_second,
                                                  font=AppFont.SMALL,
                                                  text_color=Theme.Color.TEXT_SUB,
                                                  width=400, height=80)
        self.tittle_second_label.place(relx=0.5, rely=0.9, anchor="center")

    def check_database_connection(self):
        value, e = core.database.test_connection(self.AppConfig.database)
        if not value:
            self.show_message("LỖI KẾT NỐI", f"Không thể kết nối Database.\nLỗi: {e}")
            return False
        return True

    def start_login_process(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
    
        if not username or not password:
            self.show_message("Thiếu thông tin", "Vui lòng nhập tên đăng nhập và mật khẩu.")
            return

        # Hiển thị loading trước khi xử lý nặng
        loading = LoadingDialog(self.master, "Đang xác thực...", mode="indeterminate")
        
        # Chạy logic đăng nhập ở luồng phụ
        threading.Thread(target=lambda: self._thread_login(username, password, loading), daemon=True).start()

    def _thread_login(self, username, password, loading_dialog):
        """Hàm xử lý logic đăng nhập (Chạy ngầm)"""
        if not self.check_database_connection():
            loading_dialog.stop()
            return

        result = core.database.login(username, password)
        
        # Quay lại luồng chính để cập nhật UI
        self.master.after(0, lambda: self._post_login(result, username, password, loading_dialog))

    def _post_login(self, result, username, password, loading_dialog):
        """Hàm xử lý kết quả đăng nhập (Chạy trên luồng chính)"""
        loading_dialog.stop()
        
        if result is False:
            self.show_message("Đăng nhập thất bại", "Sai tài khoản hoặc mật khẩu.")
            self.password_entry.delete(0, 'end')
            self.username_entry.focus_set()
        else:
            user_id, role = result
            self.open_dashboard(user_id, role)

    def open_dashboard(self, user_id, role):
        """Chuyển cảnh sang Dashboard"""
        self.master.withdraw() # Ẩn login
        self.master.minsize(0, 0)
        self.master.maxsize(9999, 9999)
        self.master.resizable(True, True)
        self.master.state('zoomed')
        
        # Xóa frame login cũ để giải phóng bộ nhớ (Optional)
        self.destroy()

        if role == "giangvien":
            app = LecturerDashboard(self.master, user_id, config=self.AppConfig)
            self.master.title("Dashboard Giảng Viên")
        else:
            app = AdminDashboard(self.master, user_id, config=self.AppConfig)
            self.master.title("Dashboard Quản Trị Viên")
            
        app.pack(expand=True, fill="both")

    def on_check_save_login(self):
        if self.check_save_login.get():
            self.AppConfig.login_info.username = self.username_entry.get()
            self.AppConfig.login_info.password = self.password_entry.get()
        else:
            self.AppConfig.login_info.username = None
            self.AppConfig.login_info.password = None
        save_config(self.AppConfig)

# --- PHẦN KHỞI CHẠY (Giữ nguyên logic cũ nhưng gọn hơn) ---
def runapp(config):
    # Khởi tạo Theme lần đầu
    current_theme = getattr(config, "theme_mode", "Light")
    Theme.load_theme(current_theme)
    
    root = ctk.CTk()
    
    # Tải font chữ tùy chỉnh SAU KHI có root window
    FontLoader.load_inter_fonts()
    
    root.title("PHẦN MỀM ĐIỂM DANH")
    root.geometry("1280x720")
    root.resizable(False, False)
    
    app = MainWindow(master=root, config=config)
    app.pack(expand=True, fill="both")
    
    # Logic tự động đăng nhập
    username = config.login_info.username
    password = config.login_info.password
    
    if username and password:
        # Nếu có lưu mật khẩu, tự động điền và bấm đăng nhập
        app.username_entry.insert(0, username)
        app.password_entry.insert(0, password)
        app.check_save_login.select()
        app.start_login_process()
    
    root.mainloop()