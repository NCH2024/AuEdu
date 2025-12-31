import customtkinter as ctk
from tkinter import ttk, messagebox
from gui.base.base_frame import BaseFrame
from gui.base.base_datepicker import DatePicker
from gui.base.utils import *
import core.database as db
from core.theme_manager import Theme, AppFont
from mysql.connector import Error

class AdminLecturerManager(BaseFrame):
    def __init__(self, master=None, user=None, **kwargs):
        kwargs['fg_color'] = Theme.Color.BG 
        super().__init__(master, **kwargs)
        self.user = user
        self.set_label_title("Dashboard > Trang Chủ > QUẢN LÝ GIẢNG VIÊN & KHOA")
        # [GIỮ NGUYÊN CÁC BIẾN INIT VÀ TRY/EXCEPT NHƯ CŨ]
        self.khoa_list = {}; self.giangvien_list = {}
        self.selected_khoa_id = None; self.selected_gv_id = None; self.collapsible_frames = []
        try: db.connect_db(); self.setup_ui(); self.load_all_combobox_data(); self._load_initial_lecturer_data(); self._load_khoa_data()
        except Exception as e: messagebox.showerror("Lỗi", f"{e}")

    def setup_ui(self):
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)
        top_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent"); top_frame.grid(row=0, column=0, sticky="new")
        top_frame.grid_columnconfigure(0, weight=1)
        main_table_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent"); main_table_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        main_table_frame.grid_columnconfigure(0, weight=1); main_table_frame.grid_rowconfigure(1, weight=1)
        
        self._create_main_lecturer_table_view(main_table_frame)
        
        s1 = CollapsibleFrame(top_frame, title="1. Quản lý Giảng viên", color=Theme.Color.BG_CARD, controller=self); s1.grid(row=0, column=0, sticky="new", pady=(0,5))
        self.collapsible_frames.append(s1); self._create_lecturer_section(s1.content_frame)
        
        s2 = CollapsibleFrame(top_frame, title="2. Quản lý Khoa", color=Theme.Color.BG_CARD, controller=self); s2.grid(row=1, column=0, sticky="new", pady=(0,5))
        self.collapsible_frames.append(s2); self._create_department_section(s2.content_frame)

    def on_expand(self, f):
        for frame in self.collapsible_frames:
            if frame is not f and frame.is_expanded: frame.collapse()

    def _create_lecturer_section(self, p):
        p.configure(fg_color="transparent"); p.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkLabel(p, text="Thông tin giảng viên:", font=AppFont.BODY_BOLD, text_color=Theme.Color.TEXT).grid(row=0, column=0, columnspan=3, pady=(5,10), sticky="w")
        def lbl(r, c, txt): ctk.CTkLabel(p, text=txt, font=AppFont.BODY).grid(row=r, column=c, padx=10, sticky="w")
        
        lbl(1, 0, "Mã GV:"); self.gv_id_entry = ctk.CTkEntry(p, placeholder_text="Nhập mã...", width=150); self.gv_id_entry.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        lbl(1, 1, "Họ và Tên:"); self.gv_name_entry = ctk.CTkEntry(p, placeholder_text="Nhập tên...", width=250); self.gv_name_entry.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="w")
        lbl(3, 0, "Năm Sinh:"); self.gv_dob_datepicker = DatePicker(p, width=150); self.gv_dob_datepicker.set_date_format("%Y-%m-%d"); self.gv_dob_datepicker.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        lbl(3, 1, "Số ĐT:"); self.gv_phone_entry = ctk.CTkEntry(p, width=150); self.gv_phone_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        lbl(3, 2, "Khoa:"); self.gv_khoa_cbx = ComboboxTheme(p, values=[], width=200); self.gv_khoa_cbx.grid(row=4, column=2, padx=10, pady=5, sticky="w")
        lbl(5, 0, "Ghi Chú:"); self.gv_note_entry = ctk.CTkEntry(p, width=300); self.gv_note_entry.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky="we")

        btn = ctk.CTkFrame(p, fg_color="transparent"); btn.grid(row=7, column=0, columnspan=3, pady=10, padx=5, sticky="w")
        ButtonTheme(btn, text="Tìm GV", fg_color=Theme.Color.WARNING, width=100, command=self._search_lecturer).pack(side="left", padx=5)
        ButtonTheme(btn, text="Thêm GV", fg_color=Theme.Color.SUCCESS, width=100, command=self._add_lecturer).pack(side="left", padx=5)
        ButtonTheme(btn, text="Cập nhật", fg_color=Theme.Color.INFO, width=100, command=self._update_lecturer).pack(side="left", padx=5)
        ButtonTheme(btn, text="Xoá GV", fg_color=Theme.Color.DANGER, hover_color="#B71C1C", width=100, command=self._delete_lecturer).pack(side="left", padx=5)
        ButtonTheme(btn, text="Làm mới", fg_color=Theme.Color.NEUTRAL, width=100, command=self._clear_lecturer_form).pack(side="left", padx=5)

    def _create_department_section(self, p):
        p.configure(fg_color="transparent"); p.grid_columnconfigure(0, weight=1); p.grid_columnconfigure(1, weight=1)
        left = ctk.CTkFrame(p, fg_color="transparent"); left.grid(row=0, column=0, padx=10, sticky="nsew")
        ctk.CTkLabel(left, text="Thông tin khoa:", font=AppFont.BODY_BOLD).grid(row=0, column=0, pady=5, sticky="w")
        
        ctk.CTkLabel(left, text="Mã Khoa:", font=AppFont.BODY).grid(row=1, column=0, sticky="w")
        self.khoa_id_entry = ctk.CTkEntry(left, width=150); self.khoa_id_entry.grid(row=2, column=0, pady=5, sticky="w")
        ctk.CTkLabel(left, text="Tên Khoa:", font=AppFont.BODY).grid(row=3, column=0, sticky="w")
        self.khoa_name_entry = ctk.CTkEntry(left, width=250); self.khoa_name_entry.grid(row=4, column=0, pady=5, sticky="w")
        ctk.CTkLabel(left, text="Ghi Chú:", font=AppFont.BODY).grid(row=5, column=0, sticky="w")
        self.khoa_note_entry = ctk.CTkEntry(left, width=250); self.khoa_note_entry.grid(row=6, column=0, pady=5, sticky="w")
        
        btn = ctk.CTkFrame(left, fg_color="transparent"); btn.grid(row=7, column=0, pady=10, sticky="w")
        ButtonTheme(btn, text="Thêm", fg_color=Theme.Color.SUCCESS, width=80, command=self._add_department).pack(side="left", padx=5)
        ButtonTheme(btn, text="Sửa", fg_color=Theme.Color.INFO, width=80, command=self._update_department).pack(side="left", padx=5)
        ButtonTheme(btn, text="Xóa", fg_color=Theme.Color.DANGER, width=80, command=self._delete_department).pack(side="left", padx=5)
        
        right = ctk.CTkFrame(p, fg_color="transparent"); right.grid(row=0, column=1, padx=10, sticky="nsew")
        self.khoa_tree = ttk.Treeview(right, columns=("ma", "ten", "ghichu"), show="headings", height=6); self.khoa_tree.pack(expand=True, fill="both")
        self.khoa_tree.heading("ma", text="Mã"); self.khoa_tree.heading("ten", text="Tên Khoa")
        self.khoa_tree.bind("<<TreeviewSelect>>", self._select_khoa_tree)

    def _create_main_lecturer_table_view(self, p):
        head = ctk.CTkFrame(p, fg_color="transparent"); head.pack(fill="x", pady=5)
        LabelCustom(head, text="DANH SÁCH GIẢNG VIÊN", font_size=16, font_weight="bold", text_color=Theme.Color.PRIMARY).pack(side="left", padx=10)
        
        ButtonTheme(head, text="Refresh", width=80, height=28, fg_color=Theme.Color.NEUTRAL, command=self._refresh_lecturer_table).pack(side="right", padx=5)
        ButtonTheme(head, text="Lọc", width=70, height=28, command=self._filter_lecturers_by_khoa).pack(side="right", padx=5)
        self.filter_khoa_cbx = ComboboxTheme(head, values=["Tất cả Khoa"], width=180); self.filter_khoa_cbx.pack(side="right", padx=5); self.filter_khoa_cbx.set("Tất cả Khoa")
        
        table = ctk.CTkFrame(p, fg_color=Theme.Color.BG_CARD); table.pack(fill="both", expand=True, padx=5, pady=5)
        self.lecturer_table = ttk.Treeview(table, columns=("ma", "ten", "sdt", "ns", "kh", "gc"), show="headings"); self.lecturer_table.pack(side="left", fill="both", expand=True)
        for c, t in zip(["ma", "ten", "sdt", "ns", "kh", "gc"], ["Mã GV", "Họ Tên", "SĐT", "Năm Sinh", "Khoa", "Ghi Chú"]):
            self.lecturer_table.heading(c, text=t); self.lecturer_table.column(c, width=100)
        sb = ttk.Scrollbar(table, orient="vertical", command=self.lecturer_table.yview); sb.pack(side="right", fill="y"); self.lecturer_table.configure(yscrollcommand=sb.set)
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