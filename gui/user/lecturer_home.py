import customtkinter as ctk
import threading  
import core.database as Db
from core.models import GiangVien
from gui.base.utils import WigdetFrame as WF
from gui.base.utils import LabelCustom as LBL
from gui.base.utils import CustomTable as TB
from gui.base.utils import NotifyList
from core.theme_manager import Theme, AppFont  

class LecturerHome(ctk.CTkFrame):
    def __init__(self, master=None, username=None, **kwargs):
        # Áp dụng màu nền từ Theme
        kwargs['fg_color'] = Theme.Color.BG 
        kwargs['corner_radius'] = 0
        super().__init__(master, **kwargs)
        self.username = username
        
        # Grid layout chính
        self.grid_rowconfigure((0, 1), weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure((0, 1), weight=1)

        # 1. VẼ GIAO DIỆN "KHUNG XƯƠNG" TRƯỚC (Sẽ hiển thị ngay lập tức)
        self.setup_ui_skeleton()

        # 2. BẮT ĐẦU LUỒNG LẤY DỮ LIỆU (Chạy ngầm, không làm đơ ứng dụng)
        threading.Thread(target=self.thread_load_data, daemon=True).start()

    def setup_ui_skeleton(self):
        """Vẽ toàn bộ giao diện với dữ liệu giả/trống"""
        # --- TITLE ---
        self.title_widget = ctk.CTkLabel(
            self, text="Dashboard > TRANG CHỦ", 
            font=AppFont.H3, 
            text_color=Theme.Color.TEXT
        )
        self.title_widget.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nw")

        # --- CỘT TRÁI: THÔNG TIN GIẢNG VIÊN ---
        self.info_lecturer = ctk.CTkFrame(self, fg_color=Theme.Color.BG_CARD) # Dùng màu Card
        self.info_lecturer.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        LBL(self.info_lecturer, "THÔNG TIN GIẢNG VIÊN", font_size=12, font_weight="bold", 
            text_color=Theme.Color.PRIMARY, pack_pady=5, pack_padx=20)

        # Tạo các Label giữ chỗ (Placeholder) để sau này update text
        # Lưu ý: Ta gán vào self để hàm khác có thể truy cập
        self.lbl_name = LBL(self.info_lecturer, "Giảng Viên: ", value="Đang tải...", font_weight="bold")
        self.lbl_id = LBL(self.info_lecturer, "Mã cán bộ: ", value="...", font_weight="bold")
        self.lbl_phone = LBL(self.info_lecturer, "Số điện thoại: ", value="...", font_weight="bold")
        self.lbl_faculty = LBL(self.info_lecturer, "Khoa: ", value="...", font_weight="bold")
        self.lbl_notes = LBL(self.info_lecturer, "Ghi chú: ", value="...", font_weight="italic")

        # --- CỘT TRÁI DƯỚI: LỊCH DẠY ---
        self.info_schedule = ctk.CTkFrame(self, fg_color=Theme.Color.BG_CARD)
        self.info_schedule.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.info_schedule.grid_rowconfigure(2, weight=1) # Để bảng co giãn
        self.info_schedule.grid_columnconfigure(0, weight=1)

        LBL(self.info_schedule, "PHÂN CÔNG ĐIỂM DANH", font_size=12, font_weight="bold", 
            text_color=Theme.Color.PRIMARY, pack_pady=(10,0), pack_padx=20)
        
        # Container chứa bảng
        self.table_wrapper = ctk.CTkFrame(self.info_schedule, fg_color="transparent")
        self.table_wrapper.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Khởi tạo bảng rỗng
        self.tb_schedule = TB(self.table_wrapper, 
                            columns=["LỚP", "HỌC PHẦN", "HỌC KỲ", "SỐ BUỔI"],
                            column_widths=[100, 200, 80, 70],
                            data=[])
        self.tb_schedule.pack(fill="both", expand=True)

        # --- CỘT PHẢI: THÔNG BÁO ---
        self.info_notify = ctk.CTkFrame(self, fg_color=Theme.Color.BG_CARD)
        self.info_notify.grid(row=1, column=1, rowspan=2, padx=(5,10), pady=10, sticky="nsew")
        
        LBL(self.info_notify, "THÔNG BÁO MỚI", font_size=12, font_weight="bold", 
            text_color=Theme.Color.RED_ALERT , pack_pady=5, pack_padx=20)
        
        # Frame chứa danh sách thông báo (Để dễ dàng xóa đi vẽ lại)
        self.notify_container = ctk.CTkFrame(self.info_notify, fg_color="transparent")
        self.notify_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Hiển thị loading trong lúc chờ
        self.lbl_loading_notify = ctk.CTkLabel(self.notify_container, text="Đang cập nhật tin tức...", text_color="gray")
        self.lbl_loading_notify.pack(pady=20)

    def thread_load_data(self):
        """Hàm này chạy trong luồng riêng, chuyên đi lấy dữ liệu"""
        try:
            # 1. Lấy thông tin giảng viên
            info_tuple = Db.get_info_lecturer(self.username)
            gv = None
            if info_tuple:
                gv = GiangVien(*info_tuple[:6]) # Unpack data

            # 2. Lấy lịch dạy
            schedule_data = Db.get_schedule(self.username) or []

            # 3. Lấy thông báo
            notify_data = Db.get_thongbao() or []

            # 4. Khi đã có đủ dữ liệu, gọi hàm update UI
            # Quan trọng: Phải dùng self.after để quay lại luồng chính (Main Thread) cập nhật giao diện
            self.after(0, self.update_ui_with_data, gv, schedule_data, notify_data)

        except Exception as e:
            print(f"Lỗi load data: {e}")
            # Có thể hiển thị thông báo lỗi nhẹ ở đây

    def update_ui_with_data(self, giangvien, schedule, notifies):
        """Hàm này chạy trên luồng chính để vẽ lại giao diện"""
        
        # 1. Điền thông tin giảng viên
        if giangvien:
            self.lbl_name.value.configure(text=giangvien.TenGiangVien)
            self.lbl_id.value.configure(text=giangvien.MaGV)
            self.lbl_phone.value.configure(text=str(giangvien.SDT))
            self.lbl_faculty.value.configure(text=giangvien.MaKhoa)
            self.lbl_notes.value.configure(text=giangvien.GhiChu)
        else:
            self.lbl_name.value.configure(text="Không tìm thấy dữ liệu")

        # 2. Cập nhật bảng lịch dạy
        self.tb_schedule.update_data(schedule)

        # 3. Cập nhật thông báo
        # Xóa loading cũ
        for widget in self.notify_container.winfo_children():
            widget.destroy()
        
        # Tạo list mới
        if notifies:
            NotifyList(self.notify_container, data=notifies).pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(self.notify_container, text="Không có thông báo mới", text_color="gray").pack(pady=20)