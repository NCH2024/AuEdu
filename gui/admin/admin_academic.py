import customtkinter as ctk
from tkinter import ttk, messagebox, Checkbutton, IntVar, Frame
from gui.base.base_frame import BaseFrame
# Đảm bảo ButtonTheme và ComboboxTheme được import đúng
from gui.base.utils import *

# --- Sửa import và cách gọi hàm ---
import core.database as db # Import module database
from mysql.connector import Error # Import Error để bắt lỗi DB
# --- Kết thúc sửa import ---
from tkcalendar import DateEntry
import datetime # Để lấy thứ từ ngày


# ----- LỚP QUẢN LÝ HỌC VỤ CHÍNH -----
class AdminAcademic(BaseFrame):
    def __init__(self, master=None, user=None, **kwargs):
        super().__init__(master, **kwargs)
        self.user = user
        self.set_label_title("Dashboard > Trang Chủ > QUẢN LÝ HỌC VỤ")

        # Kiểm tra kết nối ban đầu bằng cách gọi một hàm đơn giản
        try:
             db.get_all_bac_simple() # Gọi hàm từ module db
        except Error as e:
             messagebox.showerror("Lỗi kết nối CSDL", f"Không thể truy vấn CSDL: {e}\nVui lòng kiểm tra kết nối và cấu hình.")
             # Có thể thực hiện hành động khác, ví dụ: vô hiệu hóa frame
             # self.configure(state="disabled") # Ví dụ
             return # Dừng khởi tạo nếu lỗi

        self.collapsible_frames = []

        # Dữ liệu cache
        self.hocphan_list = {}
        self.giangvien_list = {}
        self.loaihp_list = {}
        self.hocky_list = {}
        self.lophocphan_list = {} # Key là INT (MaLopHocPhan), Value là string hiển thị
        self.bac_list = {}
        self.nienkhoa_list = {}
        self.nganh_list = {}
        self.lop_list = {} # Key là tuple (MaBac, MaNienKhoa, MaNganh, STTLop)
        self.loaibuoi_list = {}
        self.tiet_list = {} # { MaTiet (int): Display Text (str) }
        self.bh_tiet_vars = {} # Lưu IntVar cho các Checkbox tiết học

        # Các biến lưu trạng thái chọn
        self.selected_hocphan_id = None
        self.selected_lophocphan_id = None
        self.selected_buoihoc_id = None
        self.selected_maloaihp_setting = None

        self.setup_ui()
        try:
            self.load_all_data()
        except Error as e: # Bắt lỗi cụ thể của mysql.connector
            messagebox.showerror("Lỗi tải dữ liệu", f"Lỗi CSDL khi tải dữ liệu ban đầu: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi tải dữ liệu", f"Lỗi không xác định khi tải dữ liệu ban đầu: {e}")

    def setup_ui(self):
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=0) # Hàng cho frame thu/mở
        self.content_frame.grid_rowconfigure(1, weight=1) # Hàng cho bảng

        # --- Khung trên ---
        top_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent", height=450)
        top_frame.grid(row=0, column=0, padx=0, pady=0, sticky="new")
        top_frame.grid_columnconfigure(0, weight=1)

        # --- Khung dưới ---
        bottom_frame = ctk.CTkFrame(self.content_frame, fg_color="white", corner_radius=10)
        bottom_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        bottom_frame.grid_columnconfigure(0, weight=1)
        bottom_frame.grid_rowconfigure(1, weight=1)
        self._create_master_schedule_view(bottom_frame)

        # --- Các mục ---
        section_hocphan = CollapsibleFrame(top_frame, title="1. Quản lý Môn học (Học phần)", color="#E0F7FA", controller=self)
        section_hocphan.grid(row=0, column=0, sticky="new", pady=(0,5)) # Thêm pady
        self.collapsible_frames.append(section_hocphan)
        self._create_hocphan_section(section_hocphan.content_frame)

        section_lophocphan = CollapsibleFrame(top_frame, title="2. Quản lý Lớp học phần", color="#FFF9C4", controller=self)
        section_lophocphan.grid(row=1, column=0, sticky="new", pady=(0,5))
        self.collapsible_frames.append(section_lophocphan)
        self._create_lophocphan_section(section_lophocphan.content_frame)

        section_xeplich = CollapsibleFrame(top_frame, title="3. Xếp lịch học (Buổi học)", color="#C8E6C9", controller=self)
        section_xeplich.grid(row=2, column=0, sticky="new", pady=(0,5))
        self.collapsible_frames.append(section_xeplich)
        self._create_buoihoc_section(section_xeplich.content_frame)

        section_settings = CollapsibleFrame(top_frame, title="4. Cài đặt Tỷ lệ điểm danh", color="#FFCDD2", controller=self)
        section_settings.grid(row=3, column=0, sticky="new")
        self.collapsible_frames.append(section_settings)
        self._create_settings_section(section_settings.content_frame)

    def on_expand(self, expanded_frame):
        for frame in self.collapsible_frames:
            if frame is not expanded_frame and frame.is_expanded:
                frame.collapse()

    # --- PHẦN 1: QUẢN LÝ MÔN HỌC (HOCPHAN) ---
    def _create_hocphan_section(self, parent_frame):
        parent_frame.grid_columnconfigure((0, 2), weight=0, pad=10)
        parent_frame.grid_columnconfigure((1, 3), weight=1, pad=5)
        parent_frame.grid_columnconfigure(4, weight=2)

        ctk.CTkLabel(parent_frame, text="Mã học phần:", font=("Bahnschrift", 14)).grid(row=0, column=0, pady=5, sticky="e")
        self.hp_mahp_entry = ctk.CTkEntry(parent_frame, placeholder_text="vd: IT001", width=150)
        self.hp_mahp_entry.grid(row=0, column=1, pady=5, sticky="w")

        ctk.CTkLabel(parent_frame, text="Tên học phần:", font=("Bahnschrift", 14)).grid(row=1, column=0, pady=5, sticky="e")
        self.hp_tenhp_entry = ctk.CTkEntry(parent_frame, placeholder_text="Nhập môn lập trình", width=250)
        self.hp_tenhp_entry.grid(row=1, column=1, columnspan=3, pady=5, sticky="we")

        ctk.CTkLabel(parent_frame, text="Số tín chỉ:", font=("Bahnschrift", 14)).grid(row=2, column=0, pady=5, sticky="e")
        self.hp_sotc_entry = ctk.CTkEntry(parent_frame, width=80)
        self.hp_sotc_entry.grid(row=2, column=1, pady=5, sticky="w")

        ctk.CTkLabel(parent_frame, text="Tổng số tiết:", font=("Bahnschrift", 14)).grid(row=2, column=2, pady=5, sticky="e")
        self.hp_tongtiet_entry = ctk.CTkEntry(parent_frame, width=80)
        self.hp_tongtiet_entry.grid(row=2, column=3, pady=5, sticky="w")

        ctk.CTkLabel(parent_frame, text="Loại học phần:", font=("Bahnschrift", 14)).grid(row=3, column=0, pady=5, sticky="e")
        self.hp_loaihp_cbx = ComboboxTheme(parent_frame, values=[], width=150)
        self.hp_loaihp_cbx.grid(row=3, column=1, pady=5, sticky="w")

        btn_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, columnspan=4, pady=10, sticky="w")

        self.hp_add_btn = ButtonTheme(btn_frame, text="Thêm", font=("Bahnschrift", 14, "bold"), width=100, command=self._add_hocphan)
        self.hp_add_btn.pack(side="left", padx=5)
        self.hp_update_btn = ButtonTheme(btn_frame, text="Cập nhật", font=("Bahnschrift", 14, "bold"), width=100, command=self._update_hocphan)
        self.hp_update_btn.pack(side="left", padx=5)
        self.hp_delete_btn = ButtonTheme(btn_frame, text="Xóa", font=("Bahnschrift", 14, "bold"), width=100, fg_color="#D32F2F", hover_color="#B71C1C", command=self._delete_hocphan)
        self.hp_delete_btn.pack(side="left", padx=5)
        self.hp_clear_btn = ButtonTheme(btn_frame, text="Làm mới", font=("Bahnschrift", 14, "bold"), width=100, fg_color="#757575", hover_color="#616161", command=self._clear_hocphan_form)
        self.hp_clear_btn.pack(side="left", padx=5)

        cols = ("ma_hp", "ten_hp", "so_tc", "tong_tiet", "loai_hp")
        self.hp_tree = ttk.Treeview(parent_frame, columns=cols, show="headings", height=8)
        self.hp_tree.grid(row=0, column=4, rowspan=5, padx=10, pady=10, sticky="nsew")

        self.hp_tree.heading("ma_hp", text="Mã HP")
        self.hp_tree.heading("ten_hp", text="Tên học phần")
        self.hp_tree.heading("so_tc", text="Số TC")
        self.hp_tree.heading("tong_tiet", text="Tổng tiết")
        self.hp_tree.heading("loai_hp", text="Loại HP")
        self.hp_tree.column("ma_hp", width=120, anchor="w")
        self.hp_tree.column("ten_hp", width=250, anchor="w")
        self.hp_tree.column("so_tc", width=60, anchor="center")
        self.hp_tree.column("tong_tiet", width=70, anchor="center")
        self.hp_tree.column("loai_hp", width=80, anchor="w")

        self.hp_tree.bind("<<TreeviewSelect>>", self._select_hocphan_tree)

    # --- PHẦN 2: QUẢN LÝ LỚP HỌC PHẦN (LOPHOCPHAN) ---
    def _create_lophocphan_section(self, parent_frame):
        parent_frame.grid_columnconfigure((0, 2), weight=0, pad=10)
        parent_frame.grid_columnconfigure((1, 3), weight=1, pad=5)
        parent_frame.grid_columnconfigure(4, weight=2)

        ctk.CTkLabel(parent_frame, text="Mã lớp HP:", font=("Bahnschrift", 14)).grid(row=0, column=0, pady=5, sticky="e") # Sửa pady
        self.lhp_malhp_label = ctk.CTkLabel(parent_frame, text="[Tự động]", font=("Bahnschrift", 14, "italic"), text_color="gray")
        self.lhp_malhp_label.grid(row=0, column=1, pady=5, sticky="w")

        ctk.CTkLabel(parent_frame, text="Học phần:", font=("Bahnschrift", 14)).grid(row=1, column=0, pady=5, sticky="e")
        self.lhp_mahp_cbx = ComboboxTheme(parent_frame, values=[], width=300)
        self.lhp_mahp_cbx.grid(row=1, column=1, columnspan=3, pady=5, sticky="we")

        ctk.CTkLabel(parent_frame, text="Lớp:", font=("Bahnschrift", 14)).grid(row=2, column=0, pady=5, sticky="e")
        self.lhp_lop_cbx = ComboboxTheme(parent_frame, values=[], width=300)
        self.lhp_lop_cbx.grid(row=2, column=1, columnspan=3, pady=5, sticky="we")

        ctk.CTkLabel(parent_frame, text="Số buổi:", font=("Bahnschrift", 14)).grid(row=3, column=0, pady=5, sticky="e")
        self.lhp_sobuoi_entry = ctk.CTkEntry(parent_frame, width=80, placeholder_text="vd: 15")
        self.lhp_sobuoi_entry.grid(row=3, column=1, pady=5, sticky="w")

        ctk.CTkLabel(parent_frame, text="Tiết/buổi:", font=("Bahnschrift", 14)).grid(row=3, column=2, pady=5, sticky="e")
        self.lhp_tietmoi_entry = ctk.CTkEntry(parent_frame, width=80, placeholder_text="vd: 3")
        self.lhp_tietmoi_entry.grid(row=3, column=3, pady=5, sticky="w")

        ctk.CTkLabel(parent_frame, text="Giảng viên:", font=("Bahnschrift", 14)).grid(row=4, column=0, pady=5, sticky="e")
        self.lhp_magv_cbx = ComboboxTheme(parent_frame, values=[], width=300)
        self.lhp_magv_cbx.grid(row=4, column=1, columnspan=3, pady=5, sticky="we")

        ctk.CTkLabel(parent_frame, text="Học kỳ:", font=("Bahnschrift", 14)).grid(row=5, column=0, pady=5, sticky="e")
        self.lhp_hocky_cbx = ComboboxTheme(parent_frame, values=[], width=80)
        self.lhp_hocky_cbx.grid(row=5, column=1, pady=5, sticky="w")

        nambd_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        nambd_frame.grid(row=5, column=2, columnspan=2, pady=5, sticky="w")
        ctk.CTkLabel(nambd_frame, text="Năm học:", font=("Bahnschrift", 14)).pack(side="left", padx=(10,5))
        self.lhp_nambd_entry = ctk.CTkEntry(nambd_frame, width=70, placeholder_text="BĐ")
        self.lhp_nambd_entry.pack(side="left", padx=5)
        ctk.CTkLabel(nambd_frame, text="-", font=("Bahnschrift", 14)).pack(side="left")
        self.lhp_namkt_entry = ctk.CTkEntry(nambd_frame, width=70, placeholder_text="KT")
        self.lhp_namkt_entry.pack(side="left", padx=5)

        btn_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        btn_frame.grid(row=6, column=0, columnspan=4, pady=10, sticky="w")

        self.lhp_add_btn = ButtonTheme(btn_frame, text="Thêm", font=("Bahnschrift", 14, "bold"), width=100, command=self._add_lophocphan)
        self.lhp_add_btn.pack(side="left", padx=5)
        self.lhp_update_btn = ButtonTheme(btn_frame, text="Cập nhật", font=("Bahnschrift", 14, "bold"), width=100, command=self._update_lophocphan)
        self.lhp_update_btn.pack(side="left", padx=5)
        self.lhp_delete_btn = ButtonTheme(btn_frame, text="Xóa", font=("Bahnschrift", 14, "bold"), width=100, fg_color="#D32F2F", hover_color="#B71C1C", command=self._delete_lophocphan)
        self.lhp_delete_btn.pack(side="left", padx=5)
        self.lhp_clear_btn = ButtonTheme(btn_frame, text="Làm mới", font=("Bahnschrift", 14, "bold"), width=100, fg_color="#757575", hover_color="#616161", command=self._clear_lophocphan_form)
        self.lhp_clear_btn.pack(side="left", padx=5)

        cols = ("ma_lhp", "ten_hp", "ten_lop", "so_buoi", "tiet_buoi", "ten_gv", "hoc_ky", "nam_hoc")
        self.lhp_tree = ttk.Treeview(parent_frame, columns=cols, show="headings", height=10)
        self.lhp_tree.grid(row=0, column=4, rowspan=7, padx=10, pady=10, sticky="nsew")

        self.lhp_tree.heading("ma_lhp", text="Mã LHP")
        self.lhp_tree.heading("ten_hp", text="Tên học phần")
        self.lhp_tree.heading("ten_lop", text="Lớp")
        self.lhp_tree.heading("so_buoi", text="Số buổi")
        self.lhp_tree.heading("tiet_buoi", text="Tiết/Buổi")
        self.lhp_tree.heading("ten_gv", text="Giảng viên")
        self.lhp_tree.heading("hoc_ky", text="Học kỳ")
        self.lhp_tree.heading("nam_hoc", text="Năm học")
        self.lhp_tree.column("ma_lhp", width=60, anchor="center")
        self.lhp_tree.column("ten_hp", width=180, anchor="w")
        self.lhp_tree.column("ten_lop", width=100, anchor="w")
        self.lhp_tree.column("so_buoi", width=60, anchor="center")
        self.lhp_tree.column("tiet_buoi", width=70, anchor="center")
        self.lhp_tree.column("ten_gv", width=150, anchor="w")
        self.lhp_tree.column("hoc_ky", width=50, anchor="center")
        self.lhp_tree.column("nam_hoc", width=80, anchor="center")

        self.lhp_tree.bind("<<TreeviewSelect>>", self._select_lophocphan_tree)

    # --- PHẦN 3: XẾP LỊCH HỌC (BUOIHOC) ---
    def _create_buoihoc_section(self, parent_frame):
        parent_frame.grid_columnconfigure((0, 2), weight=0, pad=10)
        parent_frame.grid_columnconfigure(1, weight=1, pad=5)
        parent_frame.grid_columnconfigure(3, weight=2)

        ctk.CTkLabel(parent_frame, text="Lớp học phần:", font=("Bahnschrift", 14)).grid(row=0, column=0, pady=5, sticky="e") # Sửa pady
        self.bh_malhp_cbx = ComboboxTheme(parent_frame, values=[], width=300, command=self._load_buoihoc_cho_lhp)
        self.bh_malhp_cbx.grid(row=0, column=1, columnspan=2, pady=5, sticky="we")

        ctk.CTkLabel(parent_frame, text="Ngày học:", font=("Bahnschrift", 14)).grid(row=1, column=0, pady=5, sticky="e")
        date_thu_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        date_thu_frame.grid(row=1, column=1, columnspan=2, pady=5, sticky="w")
        self.bh_ngayhoc_entry = DateEntry(date_thu_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.bh_ngayhoc_entry.pack(side="left", padx=5)
        self.bh_ngayhoc_entry.bind("<<DateEntrySelected>>", self._update_thu_from_date)

        ctk.CTkLabel(date_thu_frame, text="Thứ:", font=("Bahnschrift", 14)).pack(side="left", padx=(10,5))
        self.bh_thu_label = ctk.CTkLabel(date_thu_frame, text="[Chọn ngày]", font=("Bahnschrift", 14, "italic"), text_color="gray")
        self.bh_thu_label.pack(side="left")
        self.bh_thu_var = IntVar()

        ctk.CTkLabel(parent_frame, text="Chọn tiết:", font=("Bahnschrift", 14)).grid(row=2, column=0, pady=5, sticky="ne") # Sửa pady
        self.bh_tiet_scrollframe = ctk.CTkScrollableFrame(parent_frame, height=100)
        self.bh_tiet_scrollframe.grid(row=2, column=1, columnspan=2, pady=5, sticky="we")

        ctk.CTkLabel(parent_frame, text="Loại buổi:", font=("Bahnschrift", 14)).grid(row=3, column=0, pady=5, sticky="e") # Sửa pady
        self.bh_loaibuoi_cbx = ComboboxTheme(parent_frame, values=[], width=150)
        self.bh_loaibuoi_cbx.grid(row=3, column=1, pady=5, sticky="w")

        btn_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10, sticky="w")

        self.bh_add_btn = ButtonTheme(btn_frame, text="Xếp lịch", font=("Bahnschrift", 14, "bold"), width=120, command=self._add_buoihoc)
        self.bh_add_btn.pack(side="left", padx=5)
        self.bh_delete_btn = ButtonTheme(btn_frame, text="Xóa lịch", font=("Bahnschrift", 14, "bold"), width=120, fg_color="#D32F2F", hover_color="#B71C1C", command=self._delete_buoihoc)
        self.bh_delete_btn.pack(side="left", padx=5)
        self.bh_clear_btn = ButtonTheme(btn_frame, text="Làm mới", font=("Bahnschrift", 14, "bold"), width=120, fg_color="#757575", hover_color="#616161", command=self._clear_buoihoc_form)
        self.bh_clear_btn.pack(side="left", padx=5)

        ctk.CTkLabel(parent_frame, text="Lịch học của Lớp đã chọn:", font=("Bahnschrift", 14, "bold")).grid(row=0, column=3, padx=10, pady=(10,0), sticky="sw")

        cols = ("ma_buoi", "ngay_hoc", "thu", "tiet_hoc", "loai_buoi")
        self.bh_tree = ttk.Treeview(parent_frame, columns=cols, show="headings", height=8)
        self.bh_tree.grid(row=1, column=3, rowspan=4, padx=10, pady=(0,10), sticky="nsew")

        self.bh_tree.heading("ma_buoi", text="Mã Buổi")
        self.bh_tree.heading("ngay_hoc", text="Ngày học")
        self.bh_tree.heading("thu", text="Thứ")
        self.bh_tree.heading("tiet_hoc", text="Tiết học")
        self.bh_tree.heading("loai_buoi", text="Loại buổi")
        self.bh_tree.column("ma_buoi", width=20, anchor="center")
        self.bh_tree.column("ngay_hoc", width=40, anchor="center")
        self.bh_tree.column("thu", width=10, anchor="center")
        self.bh_tree.column("tiet_hoc", width=20, anchor="center")
        self.bh_tree.column("loai_buoi", width=20, anchor="w")

        self.bh_tree.bind("<<TreeviewSelect>>", self._select_buoihoc_tree)
        self.selected_buoihoc_id = None

    # --- PHẦN 4: CÀI ĐẶT HỌC VỤ (loaihocphan_cauhinh) ---
    def _create_settings_section(self, parent_frame):
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(1, weight=0, pad=10)
        parent_frame.grid_columnconfigure(2, weight=0, pad=5)
        parent_frame.grid_columnconfigure(3, weight=0, pad=10)

        cols = ("ma_loaihp", "ten_loaihp", "tyle")
        self.setting_tree = ttk.Treeview(parent_frame, columns=cols, show="headings", height=4)
        self.setting_tree.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="nsew")

        self.setting_tree.heading("ma_loaihp", text="Mã Loại HP")
        self.setting_tree.heading("ten_loaihp", text="Tên Loại HP")
        self.setting_tree.heading("tyle", text="Tỷ lệ tối thiểu (%)")
        self.setting_tree.column("ma_loaihp", width=80, anchor="w")
        self.setting_tree.column("ten_loaihp", width=150, anchor="w")
        self.setting_tree.column("tyle", width=120, anchor="center")

        self.setting_tree.bind("<<TreeviewSelect>>", self._select_setting_tree)

        ctk.CTkLabel(parent_frame, text="Loại HP:", font=("Bahnschrift", 14)).grid(row=0, column=1, padx=(10,5), pady=10, sticky="e")
        self.setting_loaihp_label = ctk.CTkLabel(parent_frame, text="[Chọn từ bảng]", font=("Bahnschrift", 14, "italic"), text_color="gray")
        self.setting_loaihp_label.grid(row=0, column=2, columnspan=2, padx=5, pady=10, sticky="w")
        self.selected_maloaihp_setting = None

        ctk.CTkLabel(parent_frame, text="Tỷ lệ mới (%):", font=("Bahnschrift", 14)).grid(row=1, column=1, padx=(10,5), pady=10, sticky="e")
        self.setting_tyle_entry = ctk.CTkEntry(parent_frame, width=80, placeholder_text="vd: 75")
        self.setting_tyle_entry.grid(row=1, column=2, padx=5, pady=10, sticky="w")

        self.setting_update_btn = ButtonTheme(parent_frame, text="Cập nhật", font=("Bahnschrift", 14, "bold"), width=120, command=self._update_settings)
        self.setting_update_btn.grid(row=1, column=3, padx=10, pady=10, sticky="w")

    # --- PHẦN 5: BẢNG LỊCH HỌC TỔNG QUAN ---
    def _create_master_schedule_view(self, parent_frame):
        ctk.CTkLabel(parent_frame, text="LỊCH HỌC TỔNG QUAN", font=("Bahnschrift", 18, "bold"), text_color="#05243F").grid(row=0, column=0, padx=10, pady=(10,5), sticky="w") # Giảm pady

        # Bỏ cột phòng học, thêm cột Thứ, Loại buổi
        cols = ("ma_lhp", "ten_hp", "ten_gv", "ngay_hoc", "thu", "tiet_hoc", "loai_buoi")
        self.master_schedule_tree = ttk.Treeview(parent_frame, columns=cols, show="headings")
        self.master_schedule_tree.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")

        vsb = ttk.Scrollbar(parent_frame, orient="vertical", command=self.master_schedule_tree.yview)
        vsb.grid(row=1, column=1, sticky='ns', pady=(0,10))
        self.master_schedule_tree.configure(yscrollcommand=vsb.set)

        self.master_schedule_tree.heading("ma_lhp", text="Mã LHP")
        self.master_schedule_tree.heading("ten_hp", text="Tên học phần")
        self.master_schedule_tree.heading("ten_gv", text="Giảng viên")
        self.master_schedule_tree.heading("ngay_hoc", text="Ngày học")
        self.master_schedule_tree.heading("thu", text="Thứ")
        self.master_schedule_tree.heading("tiet_hoc", text="Tiết học")
        self.master_schedule_tree.heading("loai_buoi", text="Loại buổi")

        self.master_schedule_tree.column("ma_lhp", width=60, anchor="center")
        self.master_schedule_tree.column("ten_hp", width=200, anchor="w")
        self.master_schedule_tree.column("ten_gv", width=150, anchor="w")
        self.master_schedule_tree.column("ngay_hoc", width=90, anchor="center")
        self.master_schedule_tree.column("thu", width=50, anchor="center")
        self.master_schedule_tree.column("tiet_hoc", width=80, anchor="center")
        self.master_schedule_tree.column("loai_buoi", width=100, anchor="w")

    # -----------------------------------------------------------------
    # CÁC HÀM LOGIC VÀ TẢI DỮ LIỆU (Đã sửa lỗi gọi hàm DB)
    # -----------------------------------------------------------------

    def load_all_data(self):
        """Tải tất cả dữ liệu cần thiết cho các Combobox và Treeview."""
        self._load_combobox_data() # Gọi trước để có dict map
        self._load_hocphan_data()
        self._load_lophocphan_data()
        self._load_master_schedule()
        self._load_settings_data()

    def _load_combobox_data(self):
        try:
            # Tải Loại học phần
            loaihp_data = db.get_all_loaihocphan_simple()
            self.loaihp_list = {ma: ten for ma, ten in loaihp_data} if loaihp_data else {}
            self.hp_loaihp_cbx.configure(values=[''] + list(self.loaihp_list.values())) # Thêm lựa chọn trống
            self.hp_loaihp_cbx.set('') # Set default trống

            # Tải Học phần
            hocphan_data = db.get_all_hocphan_simple()
            self.hocphan_list = {ma: f"{ma} - {ten}" for ma, ten in hocphan_data} if hocphan_data else {}
            self.lhp_mahp_cbx.configure(values=[''] + list(self.hocphan_list.values()))
            self.lhp_mahp_cbx.set('')

            # Tải Giảng viên
            gv_data = db.get_all_giangvien_simple()
            self.giangvien_list = {ma: f"{ma} - {ten}" for ma, ten in gv_data} if gv_data else {}
            self.lhp_magv_cbx.configure(values=[''] + list(self.giangvien_list.values()))
            self.lhp_magv_cbx.set('')

            # Tải Học kỳ
            hocky_data = db.get_all_hocky_simple()
            self.hocky_list = {ma: ten for ma, ten in hocky_data} if hocky_data else {}
            self.lhp_hocky_cbx.configure(values=[''] + list(self.hocky_list.values()))
            self.lhp_hocky_cbx.set('')

            # Tải Lớp
            lop_data = db.get_all_lop_simple_dict()
            self.lop_list = lop_data if lop_data else {}
            self.lhp_lop_cbx.configure(values=[''] + list(self.lop_list.values()))
            self.lhp_lop_cbx.set('')

            # Tải Lớp học phần (cho xếp lịch)
            lhp_simple_data = db.get_all_lophocphan_simple()
            self.lophocphan_list = lhp_simple_data if lhp_simple_data else {}
            self.bh_malhp_cbx.configure(values=[''] + list(self.lophocphan_list.values()))
            self.bh_malhp_cbx.set('')

            # Tải Loại buổi điểm danh
            loaibuoi_data = db.get_all_loaibuoidiemdanh_simple()
            self.loaibuoi_list = {ma: ten for ma, ten in loaibuoi_data} if loaibuoi_data else {}
            self.bh_loaibuoi_cbx.configure(values=[''] + list(self.loaibuoi_list.values()))
            self.bh_loaibuoi_cbx.set('')

            # Tải Tiết học và Tạo Checkbox
            tiet_data = db.get_all_tiet_simple()
            self.tiet_list = {ma: text for ma, text in tiet_data} if tiet_data else {}
            for widget in self.bh_tiet_scrollframe.winfo_children(): widget.destroy()
            self.bh_tiet_vars = {}
            row_num, col_num, max_cols = 0, 0, 3
            for ma_tiet, display_text in sorted(self.tiet_list.items()): # Sắp xếp theo MaTiet
                var = IntVar()
                # Hiển thị text đầy đủ hơn trên checkbox
                chk_text = f"T{ma_tiet} ({display_text.split('(')[-1][:-1]})" # Lấy phần giờ HH:MM-HH:MM
                chk = ctk.CTkCheckBox(self.bh_tiet_scrollframe, text=chk_text, variable=var)
                chk.grid(row=row_num, column=col_num, padx=5, pady=2, sticky="w")
                self.bh_tiet_vars[ma_tiet] = var
                col_num += 1
                if col_num >= max_cols: col_num = 0; row_num += 1

        except Error as e: # Bắt lỗi CSDL cụ thể
            messagebox.showerror("Lỗi tải Combobox", f"Lỗi CSDL khi tải dữ liệu: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi tải Combobox", f"Lỗi không xác định: {e}")


    # --- Logic cho Môn học (HocPhan) ---
    def _load_hocphan_data(self):
        self.hp_tree.delete(*self.hp_tree.get_children())
        try:
            data = db.get_all_hocphan()
            if data:
                 for row in data:
                    loai_hp_ten = self.loaihp_list.get(row[4], row[4])
                    self.hp_tree.insert("", "end", values=(row[0], row[1], row[2], row[3], loai_hp_ten))
        except Error as e:
             messagebox.showerror("Lỗi tải Học phần", f"Lỗi CSDL: {e}")
        except Exception as e:
             messagebox.showerror("Lỗi tải Học phần", f"Lỗi không xác định: {e}")

    def _select_hocphan_tree(self, event=None):
        selected_item = self.hp_tree.focus()
        if not selected_item:
            self.selected_hocphan_id = None
            return
        values = self.hp_tree.item(selected_item, "values")
        self.selected_hocphan_id = values[0]

        self.hp_mahp_entry.delete(0, "end"); self.hp_mahp_entry.insert(0, values[0])
        self.hp_tenhp_entry.delete(0, "end"); self.hp_tenhp_entry.insert(0, values[1])
        self.hp_sotc_entry.delete(0, "end"); self.hp_sotc_entry.insert(0, values[2])
        self.hp_tongtiet_entry.delete(0, "end"); self.hp_tongtiet_entry.insert(0, values[3])
        self.hp_loaihp_cbx.set(values[4])

    def _clear_hocphan_form(self):
        self.hp_mahp_entry.delete(0, "end")
        self.hp_tenhp_entry.delete(0, "end")
        self.hp_sotc_entry.delete(0, "end")
        self.hp_tongtiet_entry.delete(0, "end")
        self.hp_loaihp_cbx.set("")
        if self.hp_tree.focus(): self.hp_tree.selection_remove(self.hp_tree.focus())
        self.selected_hocphan_id = None

    def _add_hocphan(self):
        try:
            mahp = self.hp_mahp_entry.get().strip()
            tenhp = self.hp_tenhp_entry.get().strip()
            sotc_str = self.hp_sotc_entry.get().strip()
            tongtiet_str = self.hp_tongtiet_entry.get().strip()
            ten_loaihp = self.hp_loaihp_cbx.get()

            if not all([mahp, tenhp, sotc_str, tongtiet_str, ten_loaihp]):
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ thông tin học phần.")
                return

            sotc = int(sotc_str)
            tongtiet = int(tongtiet_str)
            maloaihp = self._get_key_from_value(self.loaihp_list, ten_loaihp)

            if not maloaihp:
                 messagebox.showwarning("Lỗi", "Loại học phần không hợp lệ.")
                 return

            if db.add_hocphan(mahp, tenhp, sotc, tongtiet, maloaihp):
                messagebox.showinfo("Thành công", f"Thêm học phần '{tenhp}' thành công.")
                self._load_combobox_data()
                self._load_hocphan_data()
                self._clear_hocphan_form()
            else:
                messagebox.showerror("Lỗi", "Thêm học phần thất bại (Có thể bị trùng Mã HP).")
        except ValueError:
             messagebox.showerror("Lỗi dữ liệu", "Số tín chỉ và Tổng số tiết phải là số nguyên.")
        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi thêm học phần: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")

    def _update_hocphan(self):
        if not self.selected_hocphan_id:
             messagebox.showwarning("Chưa chọn", "Vui lòng chọn học phần từ bảng để cập nhật.")
             return
        mahp_selected = self.selected_hocphan_id

        try:
            mahp_entry = self.hp_mahp_entry.get().strip()
            tenhp = self.hp_tenhp_entry.get().strip()
            sotc_str = self.hp_sotc_entry.get().strip()
            tongtiet_str = self.hp_tongtiet_entry.get().strip()
            ten_loaihp = self.hp_loaihp_cbx.get()

            if mahp_selected != mahp_entry:
                 messagebox.showwarning("Không thể sửa Mã HP", "Không được phép thay đổi Mã học phần.")
                 self.hp_mahp_entry.delete(0, "end"); self.hp_mahp_entry.insert(0, mahp_selected)
                 return

            if not all([tenhp, sotc_str, tongtiet_str, ten_loaihp]):
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ.")
                return

            sotc = int(sotc_str)
            tongtiet = int(tongtiet_str)
            maloaihp = self._get_key_from_value(self.loaihp_list, ten_loaihp)

            if not maloaihp:
                 messagebox.showwarning("Lỗi", "Loại học phần không hợp lệ.")
                 return

            if db.update_hocphan(mahp_selected, tenhp, sotc, tongtiet, maloaihp):
                messagebox.showinfo("Thành công", f"Cập nhật học phần '{tenhp}' thành công.")
                self._load_combobox_data()
                self._load_hocphan_data()
                self._clear_hocphan_form()
            else:
                messagebox.showerror("Lỗi", "Cập nhật học phần thất bại.")
        except ValueError:
             messagebox.showerror("Lỗi dữ liệu", "Số tín chỉ và Tổng số tiết phải là số nguyên.")
        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi cập nhật học phần: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")

    def _delete_hocphan(self):
        if not self.selected_hocphan_id:
             messagebox.showwarning("Chưa chọn", "Vui lòng chọn học phần để xóa.")
             return
        mahp = self.selected_hocphan_id
        tenhp = self.hp_tenhp_entry.get()

        if messagebox.askyesno("Xác nhận xóa", f"Xóa học phần:\n\nMã HP: {mahp}\nTên HP: {tenhp}\n\n(Hành động này có thể ảnh hưởng LHP liên quan)?"):
            try:
                if db.delete_hocphan(mahp):
                    messagebox.showinfo("Thành công", f"Xóa học phần '{tenhp}' thành công.")
                    self._load_combobox_data()
                    self._load_hocphan_data()
                    self._clear_hocphan_form()
                else:
                    messagebox.showerror("Lỗi", f"Xóa thất bại. Học phần '{tenhp}' có thể đang được sử dụng.")
            except Error as e:
                 messagebox.showerror("Lỗi CSDL", f"Lỗi khi xóa học phần: {e}")
            except Exception as e:
                 messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")


    # --- Logic cho Lớp học phần (LopHocPhan) ---
    def _load_lophocphan_data(self):
        self.lhp_tree.delete(*self.lhp_tree.get_children())
        try:
            data = db.get_all_lophocphan()
            if data:
                for row in data:
                    lop_key = (row[3], row[4], row[5], row[6])
                    ten_lop = self.lop_list.get(lop_key, f"{row[3]}{row[4]}{row[5]}{row[6]}")
                    ten_hk = self.hocky_list.get(row[11], row[11])
                    nam_hoc = f"{row[12]}-{row[13]}"
                    self.lhp_tree.insert("", "end", values=(
                        row[0], row[2], ten_lop, row[7], row[8], row[10], ten_hk, nam_hoc
                    ))
        except Error as e:
            messagebox.showerror("Lỗi tải Lớp HP", f"Lỗi CSDL: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi tải Lớp HP", f"Lỗi không xác định: {e}")

    def _select_lophocphan_tree(self, event=None):
        selected_item = self.lhp_tree.focus()
        if not selected_item:
            self.selected_lophocphan_id = None
            return
        values = self.lhp_tree.item(selected_item, "values")
        try:
            self.selected_lophocphan_id = int(values[0])
            data = db.get_lophocphan_by_id(self.selected_lophocphan_id)
            if not data:
                self._clear_lophocphan_form()
                return

            self.lhp_malhp_label.configure(text=str(data[0]))
            self.lhp_mahp_cbx.set(self.hocphan_list.get(data[1], ""))
            lop_key = (data[2], data[3], data[4], data[5])
            self.lhp_lop_cbx.set(self.lop_list.get(lop_key, ""))
            self.lhp_sobuoi_entry.delete(0, "end"); self.lhp_sobuoi_entry.insert(0, data[6])
            self.lhp_tietmoi_entry.delete(0, "end"); self.lhp_tietmoi_entry.insert(0, data[7])
            self.lhp_magv_cbx.set(self.giangvien_list.get(data[8], ""))
            self.lhp_hocky_cbx.set(self.hocky_list.get(data[9], ""))
            self.lhp_nambd_entry.delete(0, "end"); self.lhp_nambd_entry.insert(0, data[10])
            self.lhp_namkt_entry.delete(0, "end"); self.lhp_namkt_entry.insert(0, data[11])

        except (ValueError, IndexError):
             messagebox.showerror("Lỗi", "Dữ liệu lớp học phần không hợp lệ.")
             self._clear_lophocphan_form()
        except Error as e:
             messagebox.showerror("Lỗi CSDL", f"Không thể tải chi tiết LHP: {e}")
             self._clear_lophocphan_form()
        except Exception as e:
             messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")
             self._clear_lophocphan_form()

    def _clear_lophocphan_form(self):
        self.lhp_malhp_label.configure(text="[Tự động]")
        self.lhp_mahp_cbx.set("")
        self.lhp_lop_cbx.set("")
        self.lhp_sobuoi_entry.delete(0, "end")
        self.lhp_tietmoi_entry.delete(0, "end")
        self.lhp_magv_cbx.set("")
        self.lhp_hocky_cbx.set("")
        self.lhp_nambd_entry.delete(0, "end")
        self.lhp_namkt_entry.delete(0, "end")
        if self.lhp_tree.focus(): self.lhp_tree.selection_remove(self.lhp_tree.focus())
        self.selected_lophocphan_id = None

    def _add_lophocphan(self):
        try:
            mahp_val = self.lhp_mahp_cbx.get()
            lop_val = self.lhp_lop_cbx.get()
            sobuoi_str = self.lhp_sobuoi_entry.get().strip()
            tietmoi_str = self.lhp_tietmoi_entry.get().strip()
            magv_val = self.lhp_magv_cbx.get()
            mahky_val = self.lhp_hocky_cbx.get()
            nambd_str = self.lhp_nambd_entry.get().strip()
            namkt_str = self.lhp_namkt_entry.get().strip()

            if not all([mahp_val, lop_val, sobuoi_str, tietmoi_str, magv_val, mahky_val, nambd_str, namkt_str]):
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ.")
                return

            mahp = self._get_key_from_value(self.hocphan_list, mahp_val)
            lop_key = self._get_key_from_value(self.lop_list, lop_val)
            magv = self._get_key_from_value(self.giangvien_list, magv_val)
            mahky = self._get_key_from_value(self.hocky_list, mahky_val)

            if not all([mahp, lop_key, magv, mahky]):
                 messagebox.showwarning("Lỗi dữ liệu", "Học phần, Lớp, GV hoặc Học kỳ không hợp lệ.")
                 return

            mabac, mank, manganh, sttlop = lop_key
            sobuoi = int(sobuoi_str)
            tietmoibuoi = int(tietmoi_str)
            nambd = int(nambd_str)
            namkt = int(namkt_str)

            new_lhp_id = db.add_lophocphan(mahp, mabac, mank, manganh, sttlop, sobuoi, tietmoibuoi, magv, mahky, nambd, namkt)

            if new_lhp_id:
                messagebox.showinfo("Thành công", f"Thêm lớp học phần thành công (Mã LHP: {new_lhp_id}).")
                self.load_all_data() # Tải lại tất cả
                self._clear_lophocphan_form()
            else:
                messagebox.showerror("Lỗi", "Thêm lớp học phần thất bại.")
        except ValueError:
             messagebox.showerror("Lỗi dữ liệu", "Số buổi, Tiết/buổi, Năm BĐ, Năm KT phải là số nguyên.")
        except Error as e:
             messagebox.showerror("Lỗi CSDL", f"Lỗi khi thêm lớp học phần: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")

    def _update_lophocphan(self):
        if not self.selected_lophocphan_id:
             messagebox.showwarning("Chưa chọn", "Vui lòng chọn LHP từ bảng để cập nhật.")
             return
        malhp_selected = self.selected_lophocphan_id

        try:
            # Lấy và kiểm tra dữ liệu tương tự _add_lophocphan
            mahp_val = self.lhp_mahp_cbx.get()
            lop_val = self.lhp_lop_cbx.get()
            sobuoi_str = self.lhp_sobuoi_entry.get().strip()
            tietmoi_str = self.lhp_tietmoi_entry.get().strip()
            magv_val = self.lhp_magv_cbx.get()
            mahky_val = self.lhp_hocky_cbx.get()
            nambd_str = self.lhp_nambd_entry.get().strip()
            namkt_str = self.lhp_namkt_entry.get().strip()

            if not all([mahp_val, lop_val, sobuoi_str, tietmoi_str, magv_val, mahky_val, nambd_str, namkt_str]):
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập đầy đủ.")
                return

            mahp = self._get_key_from_value(self.hocphan_list, mahp_val)
            lop_key = self._get_key_from_value(self.lop_list, lop_val)
            magv = self._get_key_from_value(self.giangvien_list, magv_val)
            mahky = self._get_key_from_value(self.hocky_list, mahky_val)

            if not all([mahp, lop_key, magv, mahky]):
                 messagebox.showwarning("Lỗi dữ liệu", "Học phần, Lớp, GV hoặc Học kỳ không hợp lệ.")
                 return

            mabac, mank, manganh, sttlop = lop_key
            sobuoi = int(sobuoi_str)
            tietmoibuoi = int(tietmoi_str)
            nambd = int(nambd_str)
            namkt = int(namkt_str)

            if db.update_lophocphan(malhp_selected, mahp, mabac, mank, manganh, sttlop, sobuoi, tietmoibuoi, magv, mahky, nambd, namkt):
                messagebox.showinfo("Thành công", f"Cập nhật LHP (Mã: {malhp_selected}) thành công.")
                self.load_all_data()
                self._clear_lophocphan_form()
            else:
                messagebox.showerror("Lỗi", "Cập nhật lớp học phần thất bại.")
        except ValueError:
             messagebox.showerror("Lỗi dữ liệu", "Số buổi, Tiết/buổi, Năm BĐ, Năm KT phải là số nguyên.")
        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi cập nhật lớp học phần: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")

    def _delete_lophocphan(self):
        if not self.selected_lophocphan_id:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn LHP để xóa.")
            return
        malhp = self.selected_lophocphan_id
        selected_item = self.lhp_tree.focus()
        ten_hp_confirm = self.lhp_tree.item(selected_item, "values")[1] if selected_item else f"Mã {malhp}"

        if messagebox.askyesno("Xác nhận xóa", f"Xóa LHP:\n\nMã LHP: {malhp}\nHọc phần: {ten_hp_confirm}\n\n(Toàn bộ lịch học và điểm danh liên quan sẽ bị xóa)?"):
            try:
                if db.delete_lophocphan(malhp):
                    messagebox.showinfo("Thành công", f"Xóa lớp học phần (Mã {malhp}) thành công.")
                    self.load_all_data()
                    self._clear_lophocphan_form()
                else:
                    messagebox.showerror("Lỗi", "Xóa lớp học phần thất bại.")
            except Error as e:
                 messagebox.showerror("Lỗi CSDL", f"Lỗi khi xóa lớp học phần: {e}")
            except Exception as e:
                 messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")

    # --- Logic cho Xếp lịch (BuoiHoc) ---
    def _update_thu_from_date(self, event=None):
        try:
            selected_date = self.bh_ngayhoc_entry.get_date()
            # isoweekday: 1=Thứ 2, ..., 7=Chủ nhật. CSDL Thu: 2=Thứ 2,..., 7=Thứ 7, 8=Chủ nhật
            iso_weekday = selected_date.isoweekday()
            db_thu = iso_weekday + 1 if iso_weekday < 7 else 8 # Chuyển Chủ nhật từ 7 thành 8
            day_map = {2: "Thứ 2", 3: "Thứ 3", 4: "Thứ 4", 5: "Thứ 5", 6: "Thứ 6", 7: "Thứ 7", 8: "Chủ Nhật"}
            self.bh_thu_label.configure(text=day_map.get(db_thu, "[Lỗi]"))
            self.bh_thu_var.set(db_thu)
        except Exception:
            self.bh_thu_label.configure(text="[Lỗi ngày]")
            self.bh_thu_var.set(0)

    def _load_buoihoc_cho_lhp(self, selected_lhp_display_val=None):
        self.bh_tree.delete(*self.bh_tree.get_children())
        self.selected_buoihoc_id = None

        if not selected_lhp_display_val:
            selected_lhp_display_val = self.bh_malhp_cbx.get()

        malhp = self._get_key_from_value(self.lophocphan_list, selected_lhp_display_val)
        if not malhp: return

        try:
            data = db.get_buoihoc_by_lhp(malhp)
            if data:
                for row in data:
                    ten_thu = {2: "T2", 3: "T3", 4: "T4", 5: "T5", 6: "T6", 7: "T7", 8: "CN"}.get(row[2], "?")
                    ten_loaibuoi = self.loaibuoi_list.get(row[3], row[3])
                    tiet_hoc_str = row[4] if row[4] else "Chưa có tiết"
                    # Kiểm tra xem TietHocStr có chứa nhiều tiết không
                    if tiet_hoc_str and ',' in tiet_hoc_str:
                         tiet_parts = tiet_hoc_str.split(',')
                         tiet_display = f"{tiet_parts[0]}-{tiet_parts[-1]}" # Hiển thị tiết đầu - tiết cuối
                    else:
                         tiet_display = tiet_hoc_str # Hiển thị 1 tiết hoặc "Chưa có tiết"

                    self.bh_tree.insert("", "end", values=(row[0], row[1], ten_thu, tiet_display, ten_loaibuoi))
        except Error as e:
            messagebox.showerror("Lỗi tải lịch học", f"Lỗi CSDL: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi tải lịch học", f"Lỗi không xác định: {e}")

    def _select_buoihoc_tree(self, event=None):
        selected_item = self.bh_tree.focus()
        if not selected_item:
            self.selected_buoihoc_id = None
            return
        values = self.bh_tree.item(selected_item, "values")
        try:
            self.selected_buoihoc_id = int(values[0])
        except (ValueError, IndexError):
            self.selected_buoihoc_id = None

    def _clear_buoihoc_form(self):
        self.bh_malhp_cbx.set("")
        # self.bh_ngayhoc_entry.set_date(datetime.date.today()) # Optional: reset date
        self._update_thu_from_date() # Cập nhật lại thứ
        self.bh_loaibuoi_cbx.set("")
        for var in self.bh_tiet_vars.values(): var.set(0)
        self.bh_tree.delete(*self.bh_tree.get_children())
        if self.bh_tree.focus(): self.bh_tree.selection_remove(self.bh_tree.focus())
        self.selected_buoihoc_id = None

    def _add_buoihoc(self):
        try:
            lhp_val = self.bh_malhp_cbx.get()
            malhp = self._get_key_from_value(self.lophocphan_list, lhp_val)
            ngayhoc_dt = self.bh_ngayhoc_entry.get_date()
            ngayhoc_str = ngayhoc_dt.strftime('%Y-%m-%d')
            thu = self.bh_thu_var.get()
            loaibuoi_val = self.bh_loaibuoi_cbx.get()
            maloaibuoi = self._get_key_from_value(self.loaibuoi_list, loaibuoi_val)
            selected_tiet_list = sorted([ma_tiet for ma_tiet, var in self.bh_tiet_vars.items() if var.get() == 1])

            if not malhp: messagebox.showwarning("Chưa chọn", "Vui lòng chọn Lớp học phần."); return
            if thu == 0: messagebox.showwarning("Ngày không hợp lệ", "Vui lòng chọn ngày học."); return
            if not maloaibuoi: messagebox.showwarning("Chưa chọn", "Vui lòng chọn Loại buổi."); return
            if not selected_tiet_list: messagebox.showwarning("Chưa chọn", "Vui lòng chọn ít nhất một tiết học."); return

            # Gọi Stored Procedure mới
            success, message = db.add_buoihoc_with_procedure(
                malhp, ngayhoc_str, thu, maloaibuoi, selected_tiet_list
            )

            if success:
                messagebox.showinfo("Thành công", message)
                self._load_buoihoc_cho_lhp(lhp_val)
                self._load_master_schedule()
            else:
                messagebox.showerror("Lỗi xếp lịch", message)

        except ValueError as ve:
             messagebox.showerror("Lỗi dữ liệu", f"Dữ liệu nhập không hợp lệ: {ve}")
        except Error as e:
             messagebox.showerror("Lỗi CSDL", f"Lỗi khi xếp lịch: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")

    def _delete_buoihoc(self):
        if not self.selected_buoihoc_id:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn buổi học từ bảng để xóa.")
            return
        mabuoi = self.selected_buoihoc_id
        selected_item = self.bh_tree.focus()
        ngayhoc_confirm = self.bh_tree.item(selected_item, "values")[1] if selected_item else f"Mã {mabuoi}"

        if messagebox.askyesno("Xác nhận xóa", f"Xóa buổi học:\n\nMã: {mabuoi}\nNgày: {ngayhoc_confirm}\n\n(Dữ liệu điểm danh liên quan sẽ bị xóa)?"):
            try:
                if db.delete_buoihoc(mabuoi):
                    messagebox.showinfo("Thành công", f"Xóa buổi học (Mã {mabuoi}) thành công.")
                    self._load_buoihoc_cho_lhp()
                    self._load_master_schedule()
                    self.selected_buoihoc_id = None
                else:
                    messagebox.showerror("Lỗi", "Xóa buổi học thất bại.")
            except Error as e:
                 messagebox.showerror("Lỗi CSDL", f"Lỗi khi xóa buổi học: {e}")
            except Exception as e:
                 messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")

    # --- Logic cho Cài đặt (loaihocphan_cauhinh) ---
    def _load_settings_data(self):
        self.setting_tree.delete(*self.setting_tree.get_children())
        try:
            data = db.get_loaihocphan_cauhinh()
            if data:
                 for row in data:
                     self.setting_tree.insert("", "end", values=row)
        except Error as e:
            messagebox.showerror("Lỗi tải Cài đặt", f"Lỗi CSDL: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi tải Cài đặt", f"Lỗi không xác định: {e}")

    def _select_setting_tree(self, event=None):
        selected_item = self.setting_tree.focus()
        if not selected_item:
            self.selected_maloaihp_setting = None
            self.setting_loaihp_label.configure(text="[Chọn từ bảng]")
            self.setting_tyle_entry.delete(0, "end")
            return
        values = self.setting_tree.item(selected_item, "values")
        try:
            self.selected_maloaihp_setting = values[0]
            self.setting_loaihp_label.configure(text=f"{values[0]} - {values[1]}")
            self.setting_tyle_entry.delete(0, "end")
            # Hiển thị tỷ lệ dưới dạng số nguyên nếu nó là số nguyên
            tyle_value = float(values[2])
            display_value = f"{tyle_value:.0f}" if tyle_value == int(tyle_value) else f"{tyle_value:.2f}"
            self.setting_tyle_entry.insert(0, display_value)
        except (ValueError, IndexError, TypeError):
             self.selected_maloaihp_setting = None
             self.setting_loaihp_label.configure(text="[Lỗi]")
             self.setting_tyle_entry.delete(0, "end")

    def _update_settings(self):
        if not self.selected_maloaihp_setting:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn loại HP để cập nhật.")
            return
        maloaihp = self.selected_maloaihp_setting

        try:
            new_tyle_str = self.setting_tyle_entry.get().strip()
            if not new_tyle_str:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tỷ lệ mới.")
                return

            new_tyle = float(new_tyle_str)
            if not (0 <= new_tyle <= 100):
                messagebox.showwarning("Dữ liệu sai", "Tỷ lệ phải từ 0 đến 100.")
                return

            if db.update_loaihocphan_cauhinh(maloaihp, new_tyle):
                messagebox.showinfo("Thành công", f"Cập nhật tỷ lệ cho '{maloaihp}' thành công.")
                self._load_settings_data()
                # Reset form
                self.selected_maloaihp_setting = None
                self.setting_loaihp_label.configure(text="[Chọn từ bảng]")
                self.setting_tyle_entry.delete(0, "end")
                if self.setting_tree.focus(): self.setting_tree.selection_remove(self.setting_tree.focus())
            else:
                messagebox.showerror("Lỗi", "Cập nhật tỷ lệ thất bại.")
        except ValueError:
            messagebox.showerror("Lỗi dữ liệu", "Tỷ lệ phải là số hợp lệ.")
        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi cập nhật tỷ lệ: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")

    # --- Logic cho Bảng tổng ---
    def _load_master_schedule(self):
        self.master_schedule_tree.delete(*self.master_schedule_tree.get_children())
        try:
            # Sử dụng VIEW đã sửa view_ChiTietLichHoc_v2
            # Nó đã bao gồm: MaLHP, TenHP, TenGV, NgayHoc, TietBD, TietKT, TietHocString
            data = db.get_master_schedule()
            if data:
                 for row in data:
                     # Lấy Thứ và Loại buổi từ buoihoc bằng hàm helper
                     thu_str, loaibuoi_str = self.get_buoihoc_details_for_schedule(row[0], row[3])

                     # (MaLHP, TenHP, TenGV, NgayHoc, Thu, TietHocString, LoaiBuoi)
                     display_row = (row[0], row[1], row[2], row[3], thu_str, row[6], loaibuoi_str)
                     self.master_schedule_tree.insert("", "end", values=display_row)
        except Error as e:
             messagebox.showerror("Lỗi tải Lịch tổng quan", f"Lỗi CSDL: {e}")
        except Exception as e:
             messagebox.showerror("Lỗi tải Lịch tổng quan", f"Lỗi không xác định: {e}")

    # --- Hàm helper bổ sung (giữ lại trong class vì cần self.loaibuoi_list) ---
    def get_buoihoc_details_for_schedule(self, malhp, ngayhoc):
         """Hàm helper để lấy Thứ và Loại buổi cho bảng lịch tổng quan."""
         try:
             # Tạo truy vấn trực tiếp thay vì gọi hàm từ db module
             query = """
                 SELECT bh.Thu, bh.MaLoaiBuoiDiemDanh
                 FROM buoihoc bh
                 WHERE bh.MaLopHocPhan = %s AND bh.NgayHoc = %s
                 LIMIT 1
             """
             # Sử dụng hàm thực thi query riêng (nếu có) hoặc kết nối tạm thời
             connection = db.connect_db()
             if not connection: return "?", "?"
             cursor = connection.cursor()
             cursor.execute(query, (malhp, ngayhoc))
             result = cursor.fetchone()
             cursor.close()
             connection.close()

             if result:
                  thu_int = result[0]
                  maloaibuoi = result[1]
                  thu_str = {2: "T2", 3: "T3", 4: "T4", 5: "T5", 6: "T6", 7: "T7", 8: "CN"}.get(thu_int, "?")
                  loaibuoi_str = self.loaibuoi_list.get(maloaibuoi, "?") # Dùng cache
                  return thu_str, loaibuoi_str
             return "?", "?"
         except Error as e:
             print(f"Lỗi lấy chi tiết buổi học cho lịch: {e}")
             return "?", "?"
         except Exception as e:
             print(f"Lỗi khác khi lấy chi tiết buổi học: {e}")
             return "?", "?"
         
    # --- Đặt hàm này BÊN TRONG lớp AdminAcademic ---
    def _get_key_from_value(self, mapping, value):
        """
        mapping: dict {key: display_value}
        value: giá trị hiển thị lấy từ combobox/tree
        Trả về key hoặc None nếu không tìm thấy.
        """
        if not value or value == '':
            return None

        # So khớp chính xác value trong dictionary
        for k, v in mapping.items():
            if v == value:
                return k # Trả về key (có thể là tuple, int, str)

        # Xử lý đặc biệt cho Lớp (self.lop_list) nếu value chỉ là mã (DH22TIN01)
        if mapping is self.lop_list and isinstance(value, str):
            # Thử tìm key có display name bắt đầu bằng value (phần mã)
            for k, v in mapping.items():
                # v có dạng "DH22TIN01 - Tên mô tả"
                if v.startswith(value + " - "):
                    return k

        # Xử lý đặc biệt cho GV, HP (nếu value có dạng "key - rest")
        if isinstance(value, str) and " - " in value:
            possible_key_str = value.split(" - ", 1)[0].strip()
            
            # Thử chuyển key sang int (cho GV, LHP)
            try:
                possible_key_int = int(possible_key_str)
                if possible_key_int in mapping:
                    # Kiểm tra xem value có khớp không (đề phòng trường hợp ID trùng nhưng tên khác)
                    if mapping[possible_key_int] == value:
                        return possible_key_int
            except ValueError:
                pass # Bỏ qua nếu không phải số

            # Thử so sánh key dạng str (cho HP)
            if possible_key_str in mapping:
                if mapping[possible_key_str] == value:
                    return possible_key_str

        # Trường hợp cuối: value có thể chỉ là key (vd: từ treeview)
        # Thử chuyển value sang int nếu key của mapping là int
        try:
            key_int = int(value)
            if key_int in mapping: return key_int
        except (ValueError, TypeError):
            pass
        # Thử so sánh value (dạng str) với key (dạng str)
        if value in mapping: return value


        print(f"Warning: Không tìm thấy key cho value '{value}' trong mapping.") # Debug
        return None