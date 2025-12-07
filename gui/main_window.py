from tkinter import messagebox
from gui.base.base_view import BaseView
import customtkinter as ctk
from gui.base.utils import ImageProcessor, LoadingDialog
import tkinter as tk
import core.database 
from core.utils import bcrypt_password, check_password
from gui.user.dashboard_lecturer import LecturerDashboard
from gui.admin.dashboard_admin import AdminDashboard
from core.app_config import load_config, save_config
import threading 
from core.utils import get_base_path  , resource_path
import os

class MainWindow(BaseView):
    def __init__(self, master, config):

        super().__init__(master) 
        self.AppConfig = config
        

        self.sidebar = ctk.CTkFrame(self, width=450, corner_radius=0, fg_color="#05243F")
        self.sidebar.pack(side="left", fill="y")
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="#05243F")
        self.content.pack(side="right", fill="both", expand=True)
        
        base_path = get_base_path()
        self.bg_ctkimage = ImageProcessor(os.path.join(base_path, "resources","images","bg_main_window.png")) \
                                .crop_to_aspect(1280, 720) \
                                .resize(1280, 720) \
                                .to_ctkimage(size=(1280,720))
        self.bg_label = ctk.CTkLabel(self.content, image=self.bg_ctkimage, text="")
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.setup_ui()
        self.password_entry.bind("<Return>", lambda event: self.start_login_process())
        
        
    def setup_ui(self):
        text_var_first = tk.StringVar(value="KHOA CÔNG NGHỆ THÔNG TIN\nTRƯỜNG ĐẠI HỌC NAM CẦN THƠ\n---------------\n\nĐỒ ÁN 2")
        self.tittle_first_label = self.LabelFont(self.sidebar, text=text_var_first,
                                                  font=("Bahnschrift", 20, "bold"),
                                                  justify="center", bg_color="transparent",
                                                  width=400, height=80, text_color="white")
        self.tittle_first_label.place(relx=0.5, rely=0.1, anchor="center")
        
        

        text_var = tk.StringVar(value="PHẦN MỀM ĐIỂM DANH")
        text_var2 = tk.StringVar(value="(Bằng công nghệ nhận dạng khuôn mặt)")
        self.title_label = self.LabelFont(self.sidebar, text=text_var, font=("Bahnschrift", 30, "bold"),
                                          justify="center", text_color="white", width=1280, height=50)
        self.title_label.place(relx=0.5, rely=0.35, anchor="center")
        
        self.tittle_label2 = self.LabelFont(self.sidebar, text=text_var2, font=("Bahnschrift", 13, "italic"), text_color="white")
        self.tittle_label2.place(relx=0.5, rely=0.4, anchor="center")

        
        
        self.username_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Tên đăng nhập", 
                                            width=200, height=40, font=("Bahnschrift", 16))
        self.username_entry.place(relx=0.5, rely=0.5, anchor="center")  
        self.password_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Mật khẩu", show="*", 
                                            width=200, height=40, font=("Bahnschrift", 16))
        self.password_entry.place(relx=0.5, rely=0.6, anchor="center")
        
        self.check_save_login = ctk.CTkCheckBox(self.sidebar, text="Lưu đăng nhập", text_color="white", command=self.on_check_save_login)
        self.check_save_login.place(relx=0.5, rely=0.67, anchor="center")

        # CẢI TIẾN: Gọi hàm start_login_process thay vì on_login trực tiếp
        # để hiển thị dialog loading và chạy trong luồng nền.
        self.login_button = self.ButtonTheme(self.sidebar, "Đăng nhập",width=200, height=50, command=self.start_login_process)
        self.login_button.place(relx=0.5, rely=0.75, anchor="center")

        text_var_second = tk.StringVar(value="Sinh viên: NGUYỄN CHÁNH HIỆP \n Mã số sinh viên: 223408 \n Lớp: 22TIN-TT \n\n Tháng 6/2025")
        self.tittle_second_label = self.LabelFont(self.sidebar, text=text_var_second,
                                                  font=("Bahnschrift", 15, "bold"),
                                                  justify="center", bg_color="transparent",
                                                  width=400, height=80, text_color="white")
        self.tittle_second_label.place(relx=0.5, rely=0.9, anchor="center")
        
    # Kiểm tra kết nối cơ sở dữ liệu
    def check_database_connection(self):
        value, e = core.database.test_connection(self.AppConfig.database)
        if not value:
            self.show_message("LỖI KẾT NỐI", 
                            f"KẾT NỐI CỦA BẠN KHÔNG KHẢ DỤNG\n\nMã lỗi: {e}\n\nVui lòng kiểm tra lại mạng và thử lại.\n"
                            "(Hoặc liên hệ với quản trị viên hệ thống để được hỗ trợ).")
            return False
        return True

    # --- HÀM MỚI ĐỂ XỬ LÝ ĐĂNG NHẬP THỦ CÔNG ---
    def start_login_process(self):
        """
        Hàm này được gọi khi người dùng nhấn nút "Đăng nhập".
        Nó sẽ hiển thị LoadingDialog và bắt đầu quá trình đăng nhập trong luồng nền.
        """
        username = self.username_entry.get()
        password = self.password_entry.get()
    
        if not username or not password:
            self.show_message("Thiếu thông tin", "Vui lòng nhập tên đăng nhập và mật khẩu.")
            return
        # 1. Xác thực thông tin đăng nhập trước
        # 1.1 Kiểm tra kết nối cơ sở dữ liệu
        if not self.check_database_connection():
            return
        result = core.database.login(username, password)
    
        if result is False:
            # Nếu sai, chỉ hiển thị thông báo lỗi và không làm gì thêm
            self.show_message("Thao tác không thành công!", "Sai mật khẩu hoặc tên tài khoản.\nVUI LÒNG THỬ LẠI!")
            self.password_entry.delete(0, 'end') # Chỉ xóa mật khẩu
            self.username_entry.focus_set()
        else:
            # 2. Nếu đúng, hiển thị dialog và bắt đầu tải dashboard trong luồng nền
            loading_dialog = LoadingDialog(self.master, "Đăng nhập thành công, đang tải...", mode="indeterminate", temp_topmost_off=True)
            self.master.withdraw()
            self.master.update_idletasks()
    
            def on_load_done(success):
                """Callback để đóng dialog khi tải xong."""
                self.master.after(0, loading_dialog.stop)
            threading.Thread(target=lambda: self.on_login(username, password, on_load_done), daemon=True).start()


    def on_login(self, username, password, on_done_callback=None):
        """Xử lý sự kiện khi nút đăng nhập được nhấn."""
        # Kiểm tra kết nối cơ sở dữ liệu
        if not self.check_database_connection():
            return
        result = core.database.login(username, password)
        

        if result is False:
            # Phần này giờ chỉ xử lý cho đăng nhập tự động thất bại
            # Không cần hiển thị messagebox ở đây nữa vì luồng tự động sẽ tự mở lại cửa sổ login
            # Nếu đăng nhập thất bại, gọi callback ngay trên luồng chính
            if on_done_callback: self.master.after(0, on_done_callback, False)
        else:
            user_id, role = result
            try:
                self.master.after(0, self.destroy) # Hủy frame login trên luồng chính
                
                if role == "giangvien":
                    lecturer_dashboard = LecturerDashboard(self.master, user_id, config=self.AppConfig)
                    lecturer_dashboard.pack(expand=True, fill="both")
                    self.master.title("Dashboard Giảng Viên")
                else:
                    admin_dashboard = AdminDashboard(self.master, user_id, config=self.AppConfig)
                    admin_dashboard.pack(expand=True, fill="both")
                    self.master.title("Dashboard Quản Trị Viên")

                # --- LOGIC PHÓNG TO ĐƠN GIẢN HÓA ---
                
                # 1. Reset min/max size để cho phép cửa sổ thay đổi kích thước
                self.master.minsize(0, 0)
                self.master.maxsize(9999, 9999) # Hoặc một giá trị đủ lớn

                # 2. Mở khóa resizable
                self.master.resizable(True, True) 
                
                # 3. Phóng to cửa sổ
                self.master.state('zoomed')
                self.master.attributes('-topmost', False) # Đảm bảo dashboard không chiếm vị trí cao nhất
                # Nếu thành công, gọi callback
                if on_done_callback: self.master.after(0, on_done_callback, True)
    
            except Exception as e:
                self.show_message("Lỗi", f"Đăng nhập thất bại.\n{e}")
                # Nếu có lỗi, gọi callback
                if on_done_callback: self.master.after(0, on_done_callback, False)
                if self.master:
                    self.master.quit()

    def on_check_save_login(self):
        """Xử lý sự kiện khi checkbox lưu đăng nhập được thay đổi."""
        if self.check_save_login.get():
            username = self.username_entry.get()
            password = self.password_entry.get()
            if username and password:
                self.AppConfig.login_info.username = username
                self.AppConfig.login_info.password = password
                save_config(self.AppConfig)
            else:
                messagebox.showwarning("CẢNH BÁO HỆ THỐNG", "Không thể lưu đăng nhập khi chưa có tên đăng nhập hoặc mật khẩu!")
                self.check_save_login.deselect()
                
        else:
            self.AppConfig.login_info.username = None
            self.AppConfig.login_info.password = None
            save_config(self.AppConfig)
            

def runapp(config):
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")
    root = ctk.CTk()
    
    # --- THIẾT LẬP CỬA SỔ LOGIN BAN ĐẦU ---
    root.title("PHẦN MỀM ĐIỂM DANH")
    root.geometry("1280x720")      # Kích thước cố định
    root.resizable(False, False)  # Khóa cửa sổ login
    # ---
    
    root.withdraw() # Tạm ẩn cửa sổ chính
    
    app = MainWindow(master=root, config=config)
    app.pack(expand=True, fill="both") 
    
    username = config.login_info.username
    password = config.login_info.password

    # --- CẢI TIẾN: Logic hiển thị cửa sổ và loading dialog ---
    loading_dialog = None


    def show_login_window():
        root.deiconify() 
        root.lift()
        root.focus_force()
        root.attributes('-topmost', True)
        root.after(100, lambda: root.attributes('-topmost', False))
        


    if username and password:
        # --- CẢI TIẾN LOGIC HIỂN THỊ ---
        # 1. Tạo LoadingDialog trước. Cửa sổ root sẽ tự động hiện ra do có Toplevel con,
        # nhưng vì nó trống và LoadingDialog nằm trên nên sẽ không thấy.
        loading_dialog = LoadingDialog(root, "Đang Đăng Nhập", mode="indeterminate", height_progress=20, temp_topmost_off=True)
        root.withdraw() # Đảm bảo cửa sổ chính được ẩn ngay cả khi CTkToplevel tự động hiển thị nó
        # 2. Ép Tkinter phải vẽ LoadingDialog ngay lập tức.
        root.update_idletasks()

        def on_auto_login_done(success):
            """Callback được gọi khi quá trình đăng nhập tự động hoàn tất."""
            if success:
                # Nếu thành công, on_login đã mở Dashboard, chỉ cần đóng dialog.
                if loading_dialog: loading_dialog.stop()
            else:
                # Nếu thất bại, đóng dialog và hiển thị cửa sổ đăng nhập.
                if loading_dialog: loading_dialog.stop()
                show_login_window()

        # 3. Sau khi dialog đã hiển thị, mới bắt đầu luồng đăng nhập.
        threading.Thread(target=lambda: app.on_login(username, password, on_auto_login_done), daemon=True).start()
    else:
        # Nếu không có lưu đăng nhập, hiển thị cửa sổ login ngay
        root.after(200, show_login_window)

    root.mainloop()
