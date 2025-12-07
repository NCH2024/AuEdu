# (Đặt ở đầu file admin_lecturer_manager.py)
import customtkinter as ctk
from tkinter import ttk, messagebox
import tkinter as tk
from datetime import datetime, date
from gui.base.base_frame import BaseFrame
from gui.base.base_datepicker import DatePicker
from gui.base.utils import *
import core.database as db
from mysql.connector import Error

class AdminLecturerManager(BaseFrame):
    def __init__(self, master=None, user=None, **kwargs):
        super().__init__(master, **kwargs)
        self.user = user
        self.set_label_title("Dashboard > Trang Chủ > QUẢN LÝ GIẢNG VIÊN & KHOA")

        # --- Cache dữ liệu ---
        self.khoa_list = {}      # {MaKhoa: TenKhoa}
        self.giangvien_list = {} # {MaGV: TenGV} - Chỉ để tham khảo, không dùng cho combobox GV

        # --- Trạng thái chọn ---
        self.selected_khoa_id = None # MaKhoa
        self.selected_gv_id = None   # MaGV

        self.collapsible_frames = []

        try:
            db.connect_db() # Chỉ kiểm tra kết nối
            self.setup_ui()
            self.load_all_combobox_data()
            self._load_initial_lecturer_data() # Load bảng GV ban đầu
            self._load_khoa_data() # Load bảng Khoa ban đầu
        except Error as e:
             messagebox.showerror("Lỗi kết nối CSDL", f"Không thể kết nối CSDL: {e}\nVui lòng kiểm tra cấu hình.")
             # Disable widgets nếu lỗi kết nối
             for child in self.winfo_children():
                try: child.configure(state="disabled")
                except tk.TclError: pass
        except Exception as e:
             messagebox.showerror("Lỗi khởi tạo", f"Lỗi không xác định: {e}")

    # ===================================================================
    # SETUP UI
    # ===================================================================
    def setup_ui(self):
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=0) # Hàng 0 (collapsible)
        self.content_frame.grid_rowconfigure(1, weight=1) # Hàng 1 (bảng chính)

        top_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=0, pady=0, sticky="new")
        top_frame.grid_columnconfigure(0, weight=1)

        main_table_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_table_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        main_table_frame.grid_columnconfigure(0, weight=1)
        main_table_frame.grid_rowconfigure(1, weight=1)
        self._create_main_lecturer_table_view(main_table_frame) # Tạo bảng GV chính

        # Mục 1: Quản lý Giảng viên
        section_lecturer_manager = CollapsibleFrame(top_frame, title="1. Quản lý Giảng viên", color="#E0F7FA", controller=self)
        section_lecturer_manager.grid(row=0, column=0, sticky="new", pady=(0,5))
        self.collapsible_frames.append(section_lecturer_manager)
        self._create_lecturer_section(section_lecturer_manager.content_frame)

        # Mục 2: Quản lý Khoa
        section_department_manager = CollapsibleFrame(top_frame, title="2. Quản lý Khoa", color="#FFF9C4", controller=self)
        section_department_manager.grid(row=1, column=0, sticky="new", pady=(0,5))
        self.collapsible_frames.append(section_department_manager)
        self._create_department_section(section_department_manager.content_frame)

    def on_expand(self, expanded_frame):
        for frame in self.collapsible_frames:
            if frame is not expanded_frame and frame.is_expanded:
                frame.collapse()

    # ===================================================================
    # TẠO CÁC PHẦN UI CON
    # ===================================================================

    def _create_lecturer_section(self, parent_frame):
        """Tạo UI cho mục 'Quản lý Giảng viên'."""
        parent_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(parent_frame, text="Thông tin giảng viên:", font=("Bahnschrift", 16, "bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(5,10), sticky="w")

        # --- Hàng 1: Mã GV (Nhập/Tìm), Họ Tên ---
        ctk.CTkLabel(parent_frame, text="Mã Giảng viên (Tìm kiếm/Thêm/Sửa):", font=("Bahnschrift", 12)).grid(row=1, column=0, padx=(10,2), pady=(0,2), sticky="w")
        self.gv_id_entry = ctk.CTkEntry(parent_frame, placeholder_text="Nhập Mã GV...", width=150)
        self.gv_id_entry.grid(row=2, column=0, padx=(10,2), pady=(0,5), sticky="w")

        ctk.CTkLabel(parent_frame, text="Họ và Tên:", font=("Bahnschrift", 12)).grid(row=1, column=1, padx=2, pady=(0,2), sticky="w")
        self.gv_name_entry = ctk.CTkEntry(parent_frame, placeholder_text="Nhập họ và tên...", width=250)
        self.gv_name_entry.grid(row=2, column=1, columnspan=2, padx=2, pady=(0,5), sticky="w") # Kéo dài ô tên

        # --- Hàng 2: Năm Sinh, SĐT, Khoa ---
        ctk.CTkLabel(parent_frame, text="Năm Sinh:", font=("Bahnschrift", 12)).grid(row=3, column=0, padx=(10,2), pady=(0,2), sticky="w")
        self.gv_dob_datepicker = DatePicker(parent_frame, width=150)
        self.gv_dob_datepicker.set_date_format("%Y-%m-%d") # Format SQL
        self.gv_dob_datepicker.grid(row=4, column=0, padx=(10,2), pady=(0,5), sticky="w")

        ctk.CTkLabel(parent_frame, text="Số Điện Thoại:", font=("Bahnschrift", 12)).grid(row=3, column=1, padx=2, pady=(0,2), sticky="w")
        self.gv_phone_entry = ctk.CTkEntry(parent_frame, placeholder_text="Nhập SĐT...", width=150)
        self.gv_phone_entry.grid(row=4, column=1, padx=2, pady=(0,5), sticky="w")

        ctk.CTkLabel(parent_frame, text="Thuộc Khoa:", font=("Bahnschrift", 12)).grid(row=3, column=2, padx=2, pady=(0,2), sticky="w")
        self.gv_khoa_cbx = ComboboxTheme(parent_frame, values=[], width=200) # Load từ khoa_list
        self.gv_khoa_cbx.grid(row=4, column=2, padx=2, pady=(0,5), sticky="w")

        # --- Hàng 3: Ghi chú ---
        ctk.CTkLabel(parent_frame, text="Ghi Chú:", font=("Bahnschrift", 12)).grid(row=5, column=0, padx=(10,2), pady=(0,2), sticky="w")
        self.gv_note_entry = ctk.CTkEntry(parent_frame, placeholder_text="Nhập ghi chú...", width=300)
        self.gv_note_entry.grid(row=6, column=0, columnspan=3, padx=(10,2), pady=(0,5), sticky="we")

        # --- Hàng 4: Nút bấm ---
        btn_frame_gv = ctk.CTkFrame(parent_frame, fg_color="transparent")
        btn_frame_gv.grid(row=7, column=0, columnspan=3, pady=10, padx=5, sticky="w")

        self.gv_search_btn = ctk.CTkButton(btn_frame_gv, text="Tìm GV", fg_color="#ff9800", hover_color="#e68a00", width=100, command=self._search_lecturer)
        self.gv_search_btn.pack(side="left", padx=5)
        self.gv_add_btn = ctk.CTkButton(btn_frame_gv, text="Thêm GV", fg_color="#4CAF50", hover_color="#45A049", width=100, command=self._add_lecturer)
        self.gv_add_btn.pack(side="left", padx=5)
        self.gv_update_btn = ctk.CTkButton(btn_frame_gv, text="Cập nhật GV", fg_color="#2196F3", hover_color="#2f61d6b9", width=100, command=self._update_lecturer)
        self.gv_update_btn.pack(side="left", padx=5)
        self.gv_delete_btn = ctk.CTkButton(btn_frame_gv, text="Xoá GV", fg_color="#f44336", hover_color="#da190b", width=100, command=self._delete_lecturer)
        self.gv_delete_btn.pack(side="left", padx=5)
        self.gv_clear_btn = ctk.CTkButton(btn_frame_gv, text="Làm mới Form", fg_color="#607D8B", hover_color="#546E7A", width=100, command=self._clear_lecturer_form)
        self.gv_clear_btn.pack(side="left", padx=5)

        ctk.CTkLabel(parent_frame, text="(*) Nhập Mã GV rồi nhấn 'Tìm GV'.\n(*) Dùng các ô dưới để thêm/sửa/xoá (chọn GV từ bảng dưới để sửa/xoá).", font=("Bahnschrift", 11), text_color="blue", justify="left").grid(row=8, column=0, columnspan=3, padx=10, pady=(0,5), sticky="w")


    def _create_department_section(self, parent_frame):
        """Tạo UI cho mục 'Quản lý Khoa'."""
        parent_frame.grid_columnconfigure(0, weight=1) # Cột trái cho input/button
        parent_frame.grid_columnconfigure(1, weight=1) # Cột phải cho treeview
        parent_frame.grid_rowconfigure(0, weight=1)

        # --- Khung trái ---
        left_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_frame.grid_columnconfigure(0, weight=1) # Cho phép entry co giãn

        ctk.CTkLabel(left_frame, text="Thông tin khoa:", font=("Bahnschrift", 16, "bold")).grid(row=0, column=0, columnspan=2, padx=5, pady=(5,10), sticky="w")

        ctk.CTkLabel(left_frame, text="Mã Khoa:", font=("Bahnschrift", 12)).grid(row=1, column=0, padx=5, pady=(0,2), sticky="w")
        self.khoa_id_entry = ctk.CTkEntry(left_frame, placeholder_text="Nhập Mã Khoa (VD: CNTT)...", width=150)
        self.khoa_id_entry.grid(row=2, column=0, padx=5, pady=(0,5), sticky="w")

        ctk.CTkLabel(left_frame, text="Tên Khoa:", font=("Bahnschrift", 12)).grid(row=3, column=0, padx=5, pady=(0,2), sticky="w")
        self.khoa_name_entry = ctk.CTkEntry(left_frame, placeholder_text="Nhập tên khoa...")
        self.khoa_name_entry.grid(row=4, column=0, columnspan=2, padx=5, pady=(0,5), sticky="ew") # Co giãn theo chiều ngang

        ctk.CTkLabel(left_frame, text="Ghi Chú:", font=("Bahnschrift", 12)).grid(row=5, column=0, padx=5, pady=(0,2), sticky="w")
        self.khoa_note_entry = ctk.CTkEntry(left_frame, placeholder_text="Nhập ghi chú...")
        self.khoa_note_entry.grid(row=6, column=0, columnspan=2, padx=5, pady=(0,5), sticky="ew")

        btn_frame_khoa = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame_khoa.grid(row=7, column=0, columnspan=2, pady=10, sticky="w")

        self.khoa_add_btn = ctk.CTkButton(btn_frame_khoa, text="Thêm Khoa", fg_color="#4CAF50", hover_color="#45A049", width=120, command=self._add_department)
        self.khoa_add_btn.pack(side="left", padx=5)
        self.khoa_update_btn = ctk.CTkButton(btn_frame_khoa, text="Cập nhật Khoa", fg_color="#2196F3", hover_color="#2f61d6b9", width=120, command=self._update_department)
        self.khoa_update_btn.pack(side="left", padx=5)
        self.khoa_delete_btn = ctk.CTkButton(btn_frame_khoa, text="Xoá Khoa", fg_color="#f44336", hover_color="#da190b", width=120, command=self._delete_department)
        self.khoa_delete_btn.pack(side="left", padx=5)
        self.khoa_clear_btn = ctk.CTkButton(btn_frame_khoa, text="Làm mới Form", fg_color="#607D8B", hover_color="#546E7A", width=120, command=self._clear_department_form)
        self.khoa_clear_btn.pack(side="left", padx=5)

        ctk.CTkLabel(left_frame, text="(*) Chọn Khoa từ bảng bên phải để sửa/xoá.", font=("Bahnschrift", 11), text_color="blue", justify="left").grid(row=8, column=0, columnspan=2, padx=5, pady=(0,5), sticky="w")

        # --- Khung phải (Treeview Khoa) ---
        right_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        khoa_cols = ("ma_khoa", "ten_khoa", "ghi_chu")
        self.khoa_tree = ttk.Treeview(right_frame, columns=khoa_cols, show="headings", height=8)
        self.khoa_tree.grid(row=0, column=0, sticky="nsew")

        self.khoa_tree.heading("ma_khoa", text="Mã Khoa")
        self.khoa_tree.heading("ten_khoa", text="Tên Khoa")
        self.khoa_tree.heading("ghi_chu", text="Ghi Chú")
        self.khoa_tree.column("ma_khoa", width=100, anchor="w", stretch=False)
        self.khoa_tree.column("ten_khoa", width=250, anchor="w")
        self.khoa_tree.column("ghi_chu", width=200, anchor="w")

        khoa_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.khoa_tree.yview)
        khoa_scrollbar.grid(row=0, column=1, sticky="ns")
        self.khoa_tree.configure(yscrollcommand=khoa_scrollbar.set)

        self.khoa_tree.bind("<<TreeviewSelect>>", self._select_khoa_tree)

    def _create_main_lecturer_table_view(self, parent_frame):
        """Tạo UI cho phần Bảng hiển thị thông tin Giảng viên chính."""
        frame_label_table = ctk.CTkFrame(parent_frame, fg_color="transparent")
        frame_label_table.grid(row=0, column=0, padx=5, pady=(0,5), sticky="ew")
        frame_label_table.grid_columnconfigure(0, weight=1)
        frame_label_table.grid_columnconfigure(1, weight=0)

        LabelCustom(frame_label_table, text="BẢNG HIỂN THỊ THÔNG TIN GIẢNG VIÊN", value="(*) Hiển thị toàn bộ giảng viên hoặc kết quả tìm kiếm/lọc.", wraplength=600 ).grid(row=0, column=0, padx=10, pady=0, sticky="w")

        frame_filter_controls = ctk.CTkFrame(frame_label_table, fg_color="transparent")
        frame_filter_controls.grid(row=0, column=1, padx=10, pady=0, sticky="e")

        self.filter_khoa_cbx = ComboboxTheme(frame_filter_controls, values=["Tất cả Khoa"], width=180)
        self.filter_khoa_cbx.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.filter_khoa_cbx.set("Tất cả Khoa")

        self.filter_lecturer_table_btn = ButtonTheme(frame_filter_controls, text="Lọc", width=80, height=28, command=self._filter_lecturers_by_khoa)
        self.filter_lecturer_table_btn.grid(row=0, column=1, padx=5, pady=5, sticky="e")
        self.refresh_lecturer_table_btn = ButtonTheme(frame_filter_controls, text="Làm mới", width=100, height=28, fg_color="#757575", hover_color="#616161", command=self._refresh_lecturer_table)
        self.refresh_lecturer_table_btn.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        table_container_frame = ctk.CTkFrame(parent_frame, fg_color="white")
        table_container_frame.grid(row=1, column=0, padx=5, pady=(0,5), sticky="nsew")
        table_container_frame.grid_columnconfigure(0, weight=1)
        table_container_frame.grid_rowconfigure(0, weight=1)

        lecturer_cols = ("ma_gv", "ten_gv", "sdt", "nam_sinh", "ten_khoa", "ghi_chu")
        self.lecturer_table = ttk.Treeview(table_container_frame, columns=lecturer_cols, show="headings")
        self.lecturer_table.grid(row=0, column=0, sticky="nsew")

        self.lecturer_table.heading("ma_gv", text="Mã GV")
        self.lecturer_table.heading("ten_gv", text="Họ và Tên")
        self.lecturer_table.heading("sdt", text="SĐT")
        self.lecturer_table.heading("nam_sinh", text="Năm Sinh")
        self.lecturer_table.heading("ten_khoa", text="Khoa")
        self.lecturer_table.heading("ghi_chu", text="Ghi Chú")

        self.lecturer_table.column("ma_gv", width=80, anchor="center", stretch=False)
        self.lecturer_table.column("ten_gv", width=250, anchor="w")
        self.lecturer_table.column("sdt", width=120, anchor="center")
        self.lecturer_table.column("nam_sinh", width=100, anchor="center", stretch=False)
        self.lecturer_table.column("ten_khoa", width=200, anchor="w")
        self.lecturer_table.column("ghi_chu", width=300, anchor="w")

        lecturer_scrollbar = ttk.Scrollbar(table_container_frame, orient="vertical", command=self.lecturer_table.yview)
        lecturer_scrollbar.grid(row=0, column=1, sticky="ns")
        self.lecturer_table.configure(yscrollcommand=lecturer_scrollbar.set)

        self.lecturer_table.bind("<<TreeviewSelect>>", self._select_lecturer_table)


    # ===================================================================
    # TẢI DỮ LIỆU BAN ĐẦU VÀ LÀM MỚI
    # ===================================================================

    def load_all_combobox_data(self):
        """Tải dữ liệu cho combobox Khoa."""
        try:
            khoa_data = db.get_all_khoa_simple()
            self.khoa_list = {row[0]: row[1] for row in khoa_data} if khoa_data else {}
            khoa_values = [''] + list(self.khoa_list.values()) # Thêm lựa chọn trống

            # Cập nhật combobox trong form giảng viên
            self.gv_khoa_cbx.configure(values=khoa_values)
            self.gv_khoa_cbx.set('')

            # Cập nhật combobox lọc trong bảng chính
            filter_khoa_values = ["Tất cả Khoa"] + list(self.khoa_list.values())
            self.filter_khoa_cbx.configure(values=filter_khoa_values)
            self.filter_khoa_cbx.set("Tất cả Khoa")

        except Error as e:
            messagebox.showerror("Lỗi tải dữ liệu Khoa", f"Lỗi CSDL: {e}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi tải dữ liệu Khoa", f"Lỗi không xác định: {e}", parent=self)

    def _load_initial_lecturer_data(self):
        """Load dữ liệu ban đầu cho bảng giảng viên."""
        self._refresh_lecturer_table()

    def _refresh_lecturer_table(self):
        """Làm mới bảng giảng viên, tải lại tất cả GV từ DB."""
        self._clear_lecturer_table()
        self.filter_khoa_cbx.set("Tất cả Khoa")
        try:
            lecturer_data = db.get_all_lecturers_detailed() # Cần hàm này (JOIN với khoa)
            if lecturer_data:
                for gv in lecturer_data:
                    # gv tuple: (MaGV, TenGiangVien, SDT, NamSinh, MaKhoa, TenKhoa, GhiChu)
                    namsinh_formatted = gv[3].strftime('%d/%m/%Y') if gv[3] else ''
                    # Cột table: ma_gv, ten_gv, sdt, nam_sinh, ten_khoa, ghi_chu
                    self.lecturer_table.insert("", "end", values=(
                        gv[0], gv[1], gv[2] or '', namsinh_formatted, gv[5] or 'Chưa phân Khoa', gv[6] or ''
                    ))
        except Error as e:
            messagebox.showerror("Lỗi tải DS Giảng viên", f"Lỗi CSDL: {e}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi tải DS Giảng viên", f"Lỗi không xác định: {e}", parent=self)

    def _load_khoa_data(self):
        """Tải dữ liệu cho bảng Khoa."""
        self._clear_khoa_tree()
        try:
            khoa_data = db.get_all_khoa_details() # Cần hàm này
            if khoa_data:
                for khoa in khoa_data:
                    # khoa tuple: (MaKhoa, TenKhoa, GhiChu)
                    self.khoa_tree.insert("", "end", values=(khoa[0], khoa[1], khoa[2] or ''))
        except Error as e:
            messagebox.showerror("Lỗi tải DS Khoa", f"Lỗi CSDL: {e}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi tải DS Khoa", f"Lỗi không xác định: {e}", parent=self)

    # ===================================================================
    # XỬ LÝ SỰ KIỆN VÀ LOGIC NGHIỆP VỤ
    # ===================================================================

    # --- Giảng viên ---
    def _select_lecturer_table(self, event=None):
        """Hiển thị thông tin giảng viên đã chọn từ bảng chính lên form GV."""
        selected_item = self.lecturer_table.focus()
        if not selected_item:
            self.selected_gv_id = None
            return

        values = self.lecturer_table.item(selected_item, "values")
        # values: ("ma_gv", "ten_gv", "sdt", "nam_sinh", "ten_khoa", "ghi_chu")
        try:
            self.selected_gv_id = int(values[0])

            # Lấy chi tiết GV từ DB để có MaKhoa gốc (nếu cần) và kiểm tra dữ liệu mới nhất
            gv_detail = db.get_lecturer_detail(self.selected_gv_id) # Cần hàm này
            if not gv_detail:
                messagebox.showerror("Lỗi", f"Không tìm thấy thông tin chi tiết cho giảng viên {self.selected_gv_id}", parent=self)
                self._clear_lecturer_form()
                return
            # gv_detail: (MaGV, TenGiangVien, SDT, MaKhoa, NamSinh, GhiChu)

            self.gv_id_entry.delete(0, "end"); self.gv_id_entry.insert(0, str(gv_detail[0]))
            self.gv_name_entry.delete(0, "end"); self.gv_name_entry.insert(0, gv_detail[1] or '')
            self.gv_phone_entry.delete(0, "end"); self.gv_phone_entry.insert(0, str(gv_detail[2] or ''))

            # Xử lý Năm Sinh
            try:
                namsinh_obj = gv_detail[4] # Đây có thể là date object hoặc None
                self.gv_dob_datepicker.set_date_obj(namsinh_obj)
            except Exception as e_date:
                self.gv_dob_datepicker.clear()
                print(f"Lỗi khi đặt năm sinh GV: {e_date}") # In lỗi thay vì messagebox chồng chéo

            self.gv_khoa_cbx.set(self.khoa_list.get(gv_detail[3], '')) # Lấy TenKhoa từ cache
            self.gv_note_entry.delete(0, "end"); self.gv_note_entry.insert(0, gv_detail[5] or '')

            self.gv_id_entry.configure(state="disabled") # Vô hiệu hóa Mã GV khi sửa/xóa

        except (ValueError, IndexError) as e:
            messagebox.showerror("Lỗi Dữ Liệu", f"Dữ liệu giảng viên không hợp lệ: {e}", parent=self)
            self._clear_lecturer_form()
        except Exception as e:
            messagebox.showerror("Lỗi Hiển Thị Chi Tiết GV", f"Lỗi không xác định: {e}", parent=self)
            self._clear_lecturer_form()

    def _clear_lecturer_form(self):
        """Xóa trắng form quản lý giảng viên và kích hoạt lại ô Mã GV."""
        self._refresh_lecturer_table()
        self.selected_gv_id = None
        self.gv_id_entry.delete(0, "end")
        self.gv_name_entry.delete(0, "end")
        self.gv_dob_datepicker.clear() # Gọi hàm clear của DatePicker
        self.gv_phone_entry.delete(0, "end")
        self.gv_khoa_cbx.set('') # Set về trống
        self.gv_note_entry.delete(0, "end")

        # <<< Dòng quan trọng để kích hoạt lại ô Mã GV >>>
        self.gv_id_entry.configure(state="normal")

        # Bỏ chọn trong bảng chính (nếu đang chọn)
        if self.lecturer_table.focus():
            self.lecturer_table.selection_remove(self.lecturer_table.focus())

    def _add_lecturer(self):
        try:
            magv_str = self.gv_id_entry.get().strip()
            tengv = self.gv_name_entry.get().strip()
            sdt_str = self.gv_phone_entry.get().strip()
            namsinh_obj = self.gv_dob_datepicker.get_date_object()
            namsinh_str = namsinh_obj.strftime('%Y-%m-%d') if namsinh_obj else None
            ten_khoa = self.gv_khoa_cbx.get()
            makhoa = self._get_key_from_value(self.khoa_list, ten_khoa)
            ghichu = self.gv_note_entry.get().strip()

            if not magv_str or not tengv:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Mã Giảng viên và Họ tên.")
                return

            try: magv = int(magv_str)
            except ValueError:
                 messagebox.showerror("Lỗi định dạng", "Mã Giảng viên phải là một số nguyên.")
                 return

            # Kiểm tra SĐT (nếu nhập)
            sdt = None
            if sdt_str:
                try: sdt = int(sdt_str)
                except ValueError:
                     messagebox.showerror("Lỗi định dạng", "Số Điện Thoại phải là số.")
                     return

            # Kiểm tra GV tồn tại
            if db.get_lecturer_detail(magv):
                 messagebox.showerror("Lỗi", f"Mã Giảng viên {magv} đã tồn tại.")
                 return

            # Gọi hàm add_lecturer
            if db.add_lecturer(magv, tengv, sdt, makhoa, namsinh_str, ghichu):
                 messagebox.showinfo("Thành công", f"Thêm giảng viên '{tengv}' (Mã: {magv}) thành công.")
                 self._clear_lecturer_form()
                 self._refresh_lecturer_table()
                 # Lưu ý: Cần thêm chức năng tạo tài khoản nếu muốn GV đăng nhập
            else:
                 messagebox.showerror("Lỗi", "Thêm giảng viên thất bại.")

        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi thêm giảng viên: {e}", parent=self)
        except AttributeError as ae:
            if "'NoneType' object has no attribute 'strftime'" in str(ae):
                 messagebox.showerror("Lỗi Ngày Sinh", "Định dạng Năm sinh không hợp lệ hoặc bị bỏ trống.", parent=self)
            else:
                 messagebox.showerror("Lỗi", f"Lỗi thuộc tính khi thêm giảng viên: {ae}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định khi thêm giảng viên: {e}", parent=self)

    def _update_lecturer(self):
        if not self.selected_gv_id:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn giảng viên từ bảng dưới để cập nhật.")
            return

        try:
            magv = self.selected_gv_id # Mã GV không đổi
            tengv = self.gv_name_entry.get().strip()
            sdt_str = self.gv_phone_entry.get().strip()
            namsinh_obj = self.gv_dob_datepicker.get_date_object()
            namsinh_str = namsinh_obj.strftime('%Y-%m-%d') if namsinh_obj else None
            ten_khoa = self.gv_khoa_cbx.get()
            makhoa = self._get_key_from_value(self.khoa_list, ten_khoa)
            ghichu = self.gv_note_entry.get().strip()

            if not tengv:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Họ tên.")
                return

            sdt = None
            if sdt_str:
                try: sdt = int(sdt_str)
                except ValueError:
                     messagebox.showerror("Lỗi định dạng", "Số Điện Thoại phải là số.")
                     return

            # Gọi hàm update_lecturer
            if db.update_lecturer(magv, tengv, sdt, makhoa, namsinh_str, ghichu):
                 messagebox.showinfo("Thành công", f"Cập nhật giảng viên (Mã: {magv}) thành công.")
                 self._clear_lecturer_form()
                 self._refresh_lecturer_table()
            else:
                 messagebox.showerror("Lỗi", "Cập nhật giảng viên thất bại.")

        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi cập nhật giảng viên: {e}", parent=self)
        except AttributeError as ae:
            if "'NoneType' object has no attribute 'strftime'" in str(ae):
                 messagebox.showerror("Lỗi Ngày Sinh", "Định dạng Năm sinh không hợp lệ hoặc bị bỏ trống.", parent=self)
            else:
                 messagebox.showerror("Lỗi", f"Lỗi thuộc tính khi cập nhật giảng viên: {ae}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định khi cập nhật giảng viên: {e}", parent=self)

    def _delete_lecturer(self):
        if not self.selected_gv_id:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn giảng viên từ bảng để xóa.")
            return

        magv = self.selected_gv_id
        # Lấy tên từ bảng
        selected_item = self.lecturer_table.focus()
        tengv = ""
        if selected_item:
             values = self.lecturer_table.item(selected_item, "values")
             tengv = values[1] if len(values) > 1 else f"Mã {magv}"
        else: tengv = f"Mã {magv}"

        # Kiểm tra nếu là admin (MaGV = 1) thì không cho xóa
        if magv == 1:
            messagebox.showerror("Không thể xóa", "Không được phép xóa tài khoản quản trị viên (admin).", parent=self)
            return

        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa giảng viên '{tengv}' (Mã: {magv})?\nLƯU Ý: Hành động này sẽ xóa cả tài khoản đăng nhập và có thể ảnh hưởng đến các lớp/lớp học phần đã phân công.", icon='warning', parent=self):
            try:
                # Gọi hàm delete_lecturer (cần xử lý xóa tài khoản và FK trong DB)
                success, message = db.delete_lecturer(magv)
                if success:
                    messagebox.showinfo("Thành công", f"Xóa giảng viên (Mã {magv}) thành công.")
                    self._clear_lecturer_form()
                    self._refresh_lecturer_table()
                    self.load_all_combobox_data() # Load lại combobox phòng trường hợp GV bị xóa khỏi lớp nào đó
                else:
                    messagebox.showerror("Lỗi", f"Xóa giảng viên thất bại: {message}")
            except Error as e:
                messagebox.showerror("Lỗi CSDL", f"Lỗi khi xóa giảng viên: {e}", parent=self)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi không xác định khi xóa giảng viên: {e}", parent=self)

    def _search_lecturer(self):
        """Tìm kiếm giảng viên bằng Mã GV nhập trong gv_id_entry."""
        magv_str = self.gv_id_entry.get().strip()
        if not magv_str:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Mã GV để tìm kiếm.")
            return

        try: magv = int(magv_str)
        except ValueError:
            messagebox.showerror("Lỗi định dạng", "Mã Giảng viên phải là một số nguyên.")
            return

        self._clear_lecturer_table()
        try:
            gv_data = db.get_lecturer_detail_joined(magv) # Dùng hàm join để lấy TenKhoa
            if gv_data:
                # gv_data: (MaGV, TenGiangVien, SDT, NamSinh, MaKhoa, TenKhoa, GhiChu)
                namsinh_formatted = gv_data[3].strftime('%d/%m/%Y') if gv_data[3] else ''
                self.lecturer_table.insert("", "end", values=(
                    gv_data[0], gv_data[1], gv_data[2] or '', namsinh_formatted, gv_data[5] or 'Chưa phân Khoa', gv_data[6] or ''
                ))
                # Tự động chọn dòng
                item_id = self.lecturer_table.get_children()[0]
                if item_id:
                    self.lecturer_table.focus(item_id)
                    self.lecturer_table.selection_set(item_id)
                    self._select_lecturer_table()
            else:
                messagebox.showinfo("Không tìm thấy", f"Không tìm thấy giảng viên với Mã {magv}.")
                self._refresh_lecturer_table()

        except Error as e:
            messagebox.showerror("Lỗi tìm kiếm Giảng viên", f"Lỗi CSDL: {e}", parent=self)
            self._refresh_lecturer_table()
        except Exception as e:
            messagebox.showerror("Lỗi tìm kiếm Giảng viên", f"Lỗi không xác định: {e}", parent=self)
            self._refresh_lecturer_table()

    # --- Khoa ---
    def _select_khoa_tree(self, event=None):
        """Hiển thị thông tin Khoa đã chọn từ khoa_tree lên form Khoa."""
        selected_item = self.khoa_tree.focus()
        if not selected_item:
            self.selected_khoa_id = None
            return

        values = self.khoa_tree.item(selected_item, "values")
        # values: ("ma_khoa", "ten_khoa", "ghi_chu")
        try:
            self.selected_khoa_id = values[0]
            self.khoa_id_entry.delete(0, "end"); self.khoa_id_entry.insert(0, values[0])
            self.khoa_name_entry.delete(0, "end"); self.khoa_name_entry.insert(0, values[1])
            self.khoa_note_entry.delete(0, "end"); self.khoa_note_entry.insert(0, values[2])
            self.khoa_id_entry.configure(state="disabled") # Vô hiệu hóa Mã Khoa khi sửa/xóa

        except (IndexError) as e:
            messagebox.showerror("Lỗi Dữ Liệu", f"Dữ liệu Khoa không hợp lệ: {e}", parent=self)
            self._clear_department_form()
        except Exception as e:
            messagebox.showerror("Lỗi Hiển Thị Chi Tiết Khoa", f"Lỗi không xác định: {e}", parent=self)
            self._clear_department_form()

    def _clear_department_form(self):
        """Xóa trắng form quản lý Khoa."""
        self.selected_khoa_id = None
        self.khoa_id_entry.delete(0, "end")
        self.khoa_name_entry.delete(0, "end")
        self.khoa_note_entry.delete(0, "end")
        self.khoa_id_entry.configure(state="normal") # Kích hoạt lại ô Mã Khoa
        if self.khoa_tree.focus():
            self.khoa_tree.selection_remove(self.khoa_tree.focus())

    def _add_department(self):
        try:
            makhoa = self.khoa_id_entry.get().strip().upper() # Chuẩn hóa Mã Khoa
            tenkhoa = self.khoa_name_entry.get().strip()
            ghichu = self.khoa_note_entry.get().strip()

            if not makhoa or not tenkhoa:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Mã Khoa và Tên Khoa.")
                return

            # Kiểm tra Mã Khoa tồn tại
            if db.get_khoa_detail(makhoa): # Cần hàm get_khoa_detail
                 messagebox.showerror("Lỗi", f"Mã Khoa '{makhoa}' đã tồn tại.")
                 return

            if db.add_khoa(makhoa, tenkhoa, ghichu):
                 messagebox.showinfo("Thành công", f"Thêm Khoa '{tenkhoa}' thành công.")
                 self._clear_department_form()
                 self._load_khoa_data() # Load lại bảng Khoa
                 self.load_all_combobox_data() # Load lại tất cả combobox (bao gồm Khoa)
            else:
                 messagebox.showerror("Lỗi", "Thêm Khoa thất bại.")

        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi thêm Khoa: {e}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định khi thêm Khoa: {e}", parent=self)

    def _update_department(self):
        if not self.selected_khoa_id:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn Khoa từ bảng bên phải để cập nhật.")
            return

        try:
            makhoa = self.selected_khoa_id # Mã Khoa không đổi
            tenkhoa_new = self.khoa_name_entry.get().strip()
            ghichu_new = self.khoa_note_entry.get().strip()

            if not tenkhoa_new:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Tên Khoa.")
                return

            if db.update_khoa(makhoa, tenkhoa_new, ghichu_new):
                 messagebox.showinfo("Thành công", f"Cập nhật Khoa '{tenkhoa_new}' thành công.")
                 self._clear_department_form()
                 self._load_khoa_data()
                 self.load_all_combobox_data()
                 self._refresh_lecturer_table() # Cập nhật bảng GV vì TenKhoa có thể thay đổi
            else:
                 messagebox.showerror("Lỗi", "Cập nhật Khoa thất bại.")

        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi cập nhật Khoa: {e}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định khi cập nhật Khoa: {e}", parent=self)

    def _delete_department(self):
        if not self.selected_khoa_id:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn Khoa từ bảng để xóa.")
            return

        makhoa = self.selected_khoa_id
        tenkhoa = self.khoa_name_entry.get()

        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa Khoa '{tenkhoa}' (Mã: {makhoa})?\nLƯU Ý: Hành động này có thể thất bại nếu Khoa đang có Giảng viên hoặc Lớp.", icon='warning', parent=self):
            try:
                if db.delete_khoa(makhoa):
                    messagebox.showinfo("Thành công", f"Xóa Khoa '{tenkhoa}' thành công.")
                    self._clear_department_form()
                    self._load_khoa_data()
                    self.load_all_combobox_data()
                    self._refresh_lecturer_table() # GV thuộc khoa này sẽ mất TenKhoa
                else:
                    messagebox.showerror("Lỗi", f"Xóa Khoa thất bại. Khoa có thể đang được sử dụng bởi Giảng viên hoặc Lớp.")
            except Error as e:
                messagebox.showerror("Lỗi CSDL", f"Lỗi khi xóa Khoa: {e}", parent=self)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi không xác định khi xóa Khoa: {e}", parent=self)

    # --- Bảng chính (Lọc GV) ---
    def _filter_lecturers_by_khoa(self):
        """Lọc danh sách giảng viên trong bảng chính theo Khoa đã chọn."""
        selected_khoa_display = self.filter_khoa_cbx.get()
        self._clear_lecturer_table()

        if selected_khoa_display == "Tất cả Khoa":
            self._refresh_lecturer_table()
            return

        makhoa = self._get_key_from_value(self.khoa_list, selected_khoa_display)
        if makhoa is None and selected_khoa_display != "Tất cả Khoa": # Xử lý trường hợp Khoa không hợp lệ
            messagebox.showwarning("Lỗi", "Khoa được chọn không hợp lệ.", parent=self)
            self._refresh_lecturer_table() # Hiển thị lại tất cả
            return

        try:
            lecturer_data = db.get_lecturers_by_khoa(makhoa) # Cần hàm này
            if lecturer_data:
                for gv in lecturer_data:
                    namsinh_formatted = gv[3].strftime('%d/%m/%Y') if gv[3] else ''
                    self.lecturer_table.insert("", "end", values=(
                        gv[0], gv[1], gv[2] or '', namsinh_formatted, gv[5] or '', gv[6] or ''
                    ))
        except Error as e:
            messagebox.showerror("Lỗi lọc Giảng viên", f"Lỗi CSDL: {e}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi lọc Giảng viên", f"Lỗi không xác định: {e}", parent=self)

    def _clear_lecturer_table(self):
        """Xóa tất cả dữ liệu trong bảng giảng viên chính."""
        for item in self.lecturer_table.get_children():
            self.lecturer_table.delete(item)

    def _clear_khoa_tree(self):
        """Xóa tất cả dữ liệu trong bảng khoa."""
        for item in self.khoa_tree.get_children():
            self.khoa_tree.delete(item)

    # ===================================================================
    # HÀM HỖ TRỢ (HELPER)
    # ===================================================================
    def _get_key_from_value(self, mapping_dict, display_value):
        # (Giữ nguyên logic hàm _get_key_from_value đã cung cấp)
        if not display_value or display_value == '': return None
        # Xử lý GV: "ID - Tên"
        if mapping_dict is self.giangvien_list and ' - ' in display_value:
             try: return int(display_value.split(' - ')[0])
             except ValueError: return None
        # Xử lý các dict khác (Khoa)
        for k, v in mapping_dict.items():
            if v == display_value: return k
        return None