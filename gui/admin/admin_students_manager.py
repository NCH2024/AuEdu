import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from gui.base.base_frame import BaseFrame
from gui.base.base_datepicker import DatePicker 
from gui.base.utils import * 
import core.database as db
from core.theme_manager import Theme, AppFont
from mysql.connector import Error

class AdminStudentsManager(BaseFrame):
    def __init__(self, master=None, user=None, **kwargs):
        kwargs['fg_color'] = Theme.Color.BG 
        super().__init__(master, **kwargs)
        
        self.user = user
        self.set_label_title("Dashboard > Trang Chủ > QUẢN LÝ SINH VIÊN & LỚP HỌC")
        
        # Init variables
        self.bac_list = {}; self.nienkhoa_list = {}; self.nganh_list = {} 
        self.khoa_list = {}; self.giangvien_list = {}; self.lop_list = {} 
        self.all_lop_display_names = []; self.selected_lop_key = None 
        self.selected_sv_id = None; self.collapsible_frames = []
        
        try:
            db.connect_db()
            self.setup_ui()
            self.load_all_combobox_data()
            self._load_initial_student_data() 
        except Exception as e:
             messagebox.showerror("Lỗi khởi tạo", f"Lỗi: {e}")

    def setup_ui(self):
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1) 
        
        top_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent") 
        top_frame.grid(row=0, column=0, sticky="new")
        top_frame.grid_columnconfigure(0, weight=1)
        
        main_table_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_table_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        main_table_frame.grid_columnconfigure(0, weight=1)
        main_table_frame.grid_rowconfigure(1, weight=1)
        
        self._create_main_table_view(main_table_frame) 
        
        section_class_manager = CollapsibleFrame(top_frame, title="1. Quản lý Lớp học", color=Theme.Color.BG_CARD, controller=self)
        section_class_manager.grid(row=0, column=0, sticky="new", pady=(0,5))
        self.collapsible_frames.append(section_class_manager)
        self._create_class_section(section_class_manager.content_frame)
        
        section_student_manager = CollapsibleFrame(top_frame, title="2. Quản lý Sinh viên", color=Theme.Color.BG_CARD, controller=self)
        section_student_manager.grid(row=1, column=0, sticky="new", pady=(0,5))
        self.collapsible_frames.append(section_student_manager)
        self._create_student_section(section_student_manager.content_frame)
        
        Theme.apply_treeview_style(self)

    def on_expand(self, expanded_frame):
        for frame in self.collapsible_frames:
            if frame is not expanded_frame and frame.is_expanded: frame.collapse()

    def _create_class_section(self, parent_frame):
        parent_frame.configure(fg_color="transparent")
        parent_frame.grid_columnconfigure(1, weight=2) 
        
        left_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(left_frame, text="Thông tin lớp học:", font=AppFont.BODY_BOLD, text_color=Theme.Color.TEXT).grid(row=0, column=0, columnspan=4, pady=(5,10), sticky="w")
        
        def lbl(r, c, text): ctk.CTkLabel(left_frame, text=text, font=AppFont.BODY, text_color=Theme.Color.TEXT).grid(row=r, column=c, padx=2, sticky="w")

        lbl(1, 0, "Bậc học:");        self.class_bac_cbx = ComboboxTheme(left_frame, values=[], width=120); self.class_bac_cbx.grid(row=2, column=0, padx=2, pady=5, sticky="w")
        lbl(1, 1, "Khoá học:");       self.class_nienkhoa_cbx = ComboboxTheme(left_frame, values=[], width=80); self.class_nienkhoa_cbx.grid(row=2, column=1, padx=2, pady=5, sticky="w")
        lbl(1, 2, "Chuyên ngành:");   self.class_nganh_cbx = ComboboxTheme(left_frame, values=[], width=120); self.class_nganh_cbx.grid(row=2, column=2, padx=2, pady=5, sticky="w")
        lbl(3, 2, "STT lớp:");        self.class_stt_cbx = ComboboxTheme(left_frame, values=[f"{i:02d}" for i in range(1, 11)], width=80); self.class_stt_cbx.grid(row=4, column=2, padx=2, pady=5, sticky="w"); self.class_stt_cbx.set("01")
        lbl(1, 3, "Trực thuộc khoa:"); self.class_khoa_cbx = ComboboxTheme(left_frame, values=[], width=120); self.class_khoa_cbx.grid(row=2, column=3, padx=2, pady=5, sticky="w")
        lbl(3, 3, "GV Chủ nhiệm:");   self.class_gv_cbx = ComboboxTheme(left_frame, values=[], width=120); self.class_gv_cbx.grid(row=4, column=3, padx=2, pady=5, sticky="w")
        
        ctk.CTkLabel(left_frame, text="Tên Lớp / Mã:", font=AppFont.BODY, text_color=Theme.Color.TEXT).grid(row=3, column=0, columnspan=2, sticky="w")
        self.class_tenlop_entry = ctk.CTkEntry(left_frame, placeholder_text="Mô tả hoặc mã...", width=300)
        self.class_tenlop_entry.grid(row=4, column=0, columnspan=2, padx=2, pady=5, sticky="w")
        
        # Buttons Class - Dùng biến Theme
        btn_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=4, pady=10, sticky="w")
        
        ButtonTheme(btn_frame, text="Thêm", fg_color=Theme.Color.SUCCESS, width=80, command=self._add_lop).pack(side="left", padx=5)  
        ButtonTheme(btn_frame, text="Cập nhật", fg_color=Theme.Color.INFO, width=80, command=self._update_lop).pack(side="left", padx=5)   
        ButtonTheme(btn_frame, text="Xoá", fg_color=Theme.Color.DANGER, hover_color="#B71C1C", width=80, command=self._delete_lop).pack(side="left", padx=5)
        ButtonTheme(btn_frame, text="Tìm kiếm", fg_color=Theme.Color.WARNING, width=80, command=self._search_lop).pack(side="left", padx=5)    
        ButtonTheme(btn_frame, text="Làm mới", fg_color=Theme.Color.NEUTRAL, width=80, command=self._clear_class_form).pack(side="left", padx=5)
        
        ctk.CTkLabel(left_frame, text="(*) Nhập Tên lớp mô tả khi thêm/sửa.\n(*) Nhập Tên hoặc Mã lớp (VD: DH22TIN01) để Tìm kiếm.", font=AppFont.SMALL_ITALIC, text_color=Theme.Color.TEXT_SUB, justify="left").grid(row=6, column=0, columnspan=4, pady=5, sticky="w")
        
        # Treeview
        right_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        self.class_tree = ttk.Treeview(right_frame, columns=("key", "ten_lop", "ten_gv", "ten_khoa"), show="headings", height=8)
        self.class_tree.grid(row=0, column=0, sticky="nsew")
        self.class_tree.heading("key", text="Mã Lớp"); self.class_tree.heading("ten_lop", text="Tên Lớp")
        self.class_tree.heading("ten_gv", text="GVCN"); self.class_tree.heading("ten_khoa", text="Khoa")
        self.class_tree.bind("<<TreeviewSelect>>", self._select_class_tree)

    def _create_student_section(self, parent_frame):
        parent_frame.configure(fg_color="transparent")
        parent_frame.grid_columnconfigure((0, 1, 2), weight=1) 
        ctk.CTkLabel(parent_frame, text="Thông tin sinh viên:", font=AppFont.BODY_BOLD, text_color=Theme.Color.TEXT).grid(row=0, column=0, columnspan=3, padx=10, pady=(5,10), sticky="w")
        
        def entry(r, c, ph, w=200):
            e = ctk.CTkEntry(parent_frame, placeholder_text=ph, width=w)
            e.grid(row=r+1, column=c, padx=(10,2), pady=5, sticky="w")
            return e
            
        ctk.CTkLabel(parent_frame, text="MSSV:", font=AppFont.BODY).grid(row=1, column=0, padx=10, sticky="w")
        self.sv_id_entry = entry(1, 0, "Nhập MSSV...", 150)
        
        ctk.CTkLabel(parent_frame, text="Họ và Tên:", font=AppFont.BODY).grid(row=3, column=0, padx=10, sticky="w")
        self.sv_name_entry = entry(3, 0, "Nhập họ và tên...", 250)
        
        ctk.CTkLabel(parent_frame, text="Giới Tính:", font=AppFont.BODY).grid(row=3, column=1, padx=2, sticky="w")
        self.sv_gender_cbx = ComboboxTheme(parent_frame, values=["Nam", "Nữ"], width=100); self.sv_gender_cbx.grid(row=4, column=1, padx=2, pady=5, sticky="w"); self.sv_gender_cbx.set("Nam")
        
        ctk.CTkLabel(parent_frame, text="Ngày Sinh:", font=AppFont.BODY).grid(row=5, column=0, padx=10, sticky="w")
        self.sv_dob_entry = DatePicker(parent_frame, width=150); self.sv_dob_entry.set_date_format("%Y-%m-%d"); self.sv_dob_entry.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(parent_frame, text="Thuộc Lớp:", font=AppFont.BODY).grid(row=5, column=1, padx=2, sticky="w")  
        self.sv_lop_cbx = ComboboxTheme(parent_frame, values=[], width=200); self.sv_lop_cbx.grid(row=6, column=1, columnspan=2, padx=2, pady=5, sticky="w") 
        
        ctk.CTkLabel(parent_frame, text="Địa Chỉ:", font=AppFont.BODY).grid(row=7, column=0, padx=10, sticky="w")
        self.sv_address_entry = ctk.CTkEntry(parent_frame, width=300); self.sv_address_entry.grid(row=8, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(parent_frame, text="Ghi Chú:", font=AppFont.BODY).grid(row=7, column=2, padx=2, sticky="w")
        self.sv_note_entry = ctk.CTkEntry(parent_frame, width=200); self.sv_note_entry.grid(row=8, column=2, padx=2, pady=5, sticky="w")
        
        btn_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        btn_frame.grid(row=9, column=0, columnspan=3, pady=10, padx=5, sticky="w")
        
        ButtonTheme(btn_frame, text="Tìm SV", fg_color=Theme.Color.WARNING, width=100, command=self._search_student).pack(side="left", padx=5)
        ButtonTheme(btn_frame, text="Thêm SV", fg_color=Theme.Color.SUCCESS, width=100, command=self._add_sinhvien).pack(side="left", padx=5)
        ButtonTheme(btn_frame, text="Cập nhật", fg_color=Theme.Color.INFO, width=100, command=self._update_sinhvien).pack(side="left", padx=5)
        ButtonTheme(btn_frame, text="Xoá SV", fg_color=Theme.Color.DANGER, hover_color="#B71C1C", width=100, command=self._delete_sinhvien).pack(side="left", padx=5)
        ButtonTheme(btn_frame, text="Làm mới", fg_color=Theme.Color.NEUTRAL, width=100, command=self._clear_student_form).pack(side="left", padx=5)
        
        ctk.CTkLabel(parent_frame, text="(*) Nhập MSSV vào ô trên cùng rồi nhấn 'Tìm SV'.\n(*) Dùng các ô dưới để thêm/sửa/xoá.", font=AppFont.SMALL_ITALIC, text_color=Theme.Color.TEXT_SUB, justify="left").grid(row=10, column=0, columnspan=3, padx=10, pady=5, sticky="w")

    def _create_main_table_view(self, parent_frame):
        frame_head = ctk.CTkFrame(parent_frame, fg_color="transparent")
        frame_head.grid(row=0, column=0, pady=5, sticky="ew") 
        frame_head.grid_columnconfigure(0, weight=1) 
        LabelCustom(frame_head, text="DANH SÁCH SINH VIÊN", font_size=16, font_weight="bold", text_color=Theme.Color.PRIMARY).grid(row=0, column=0, padx=10, sticky="w")
        
        frame_filter = ctk.CTkFrame(frame_head, fg_color="transparent")
        frame_filter.grid(row=0, column=1, padx=10, sticky="e")
        self.filter_class_cbx = ComboboxTheme(frame_filter, values=["Tất cả lớp"], width=150); self.filter_class_cbx.grid(row=0, column=0, padx=5); self.filter_class_cbx.set("Tất cả lớp")
        ButtonTheme(frame_filter, text="Lọc", width=70, height=28, command=self._filter_students_by_class).grid(row=0, column=1, padx=5)
        ButtonTheme(frame_filter, text="Refresh", width=80, height=28, fg_color=Theme.Color.NEUTRAL, command=self._refresh_student_table).grid(row=0, column=2, padx=5)
        
        table_container = ctk.CTkFrame(parent_frame, fg_color=Theme.Color.BG_CARD) 
        table_container.grid(row=1, column=0, padx=5, pady=5, sticky="nsew") 
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(0, weight=1)
        
        self.student_table = ttk.Treeview(table_container, columns=("mssv", "ho_dem", "ten", "gioi_tinh", "ngay_sinh", "ten_lop", "dia_chi", "ghi_chu"), show="headings")
        self.student_table.grid(row=0, column=0, sticky="nsew")
        
        for col, txt, w in [("mssv", "MSSV", 80), ("ho_dem", "Họ Đệm", 150), ("ten", "Tên", 80), ("gioi_tinh", "GT", 60), ("ngay_sinh", "Ngày Sinh", 100), ("ten_lop", "Lớp", 100), ("dia_chi", "Địa Chỉ", 200), ("ghi_chu", "Ghi Chú", 150)]:
            self.student_table.heading(col, text=txt); self.student_table.column(col, width=w)
            
        sb = ttk.Scrollbar(table_container, orient="vertical", command=self.student_table.yview); sb.grid(row=0, column=1, sticky="ns")
        self.student_table.configure(yscrollcommand=sb.set)
        self.student_table.bind("<<TreeviewSelect>>", self._select_student_table)

    def load_all_combobox_data(self):
        try:
            bac_data = db.get_all_bac_simple()
            self.bac_list = {row[0]: row[1] for row in bac_data} if bac_data else {}
            self.class_bac_cbx.configure(values=[''] + list(self.bac_list.values()))
            self.class_bac_cbx.set('')
            nk_data = db.get_all_nienkhoa_simple() 
            self.nienkhoa_list = {row[0]: row[1] for row in nk_data} if nk_data else {}
            self.class_nienkhoa_cbx.configure(values=[''] + list(self.nienkhoa_list.values()))
            self.class_nienkhoa_cbx.set('')
            nganh_data = db.get_all_nganh_simple()
            self.nganh_list = {row[0]: row[1] for row in nganh_data} if nganh_data else {}
            self.class_nganh_cbx.configure(values=[''] + list(self.nganh_list.values()))
            self.class_nganh_cbx.set('')
            khoa_data = db.get_all_khoa_simple()
            self.khoa_list = {row[0]: row[1] for row in khoa_data} if khoa_data else {}
            self.class_khoa_cbx.configure(values=[''] + list(self.khoa_list.values()))
            self.class_khoa_cbx.set('')
            gv_data = db.get_all_giangvien_simple() 
            self.giangvien_list = {row[0]: f"{row[0]} - {row[1]}" for row in gv_data} if gv_data else {}
            self.class_gv_cbx.configure(values=[''] + list(self.giangvien_list.values())) 
            self.class_gv_cbx.set('')
            lop_raw_data = db.get_all_lop_simple() 
            self.lop_list = {}
            self.all_lop_display_names = ["Tất cả lớp"] 
            if lop_raw_data:
                 for row in lop_raw_data:
                     key = (row[0], row[1], row[2], row[3]) 
                     display_name = f"{row[0]}{row[1]}{row[2]}{row[3]}" 
                     self.lop_list[key] = display_name
                     self.all_lop_display_names.append(display_name)
            self.sv_lop_cbx.configure(values=[''] + self.all_lop_display_names[1:]) 
            self.sv_lop_cbx.set('') 
            self.filter_class_cbx.configure(values=self.all_lop_display_names) 
            self.filter_class_cbx.set("Tất cả lớp")
            self._clear_class_form()
        except Error as e:
            messagebox.showerror("Lỗi tải dữ liệu Combobox", f"Lỗi CSDL: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi tải dữ liệu Combobox", f"Lỗi không xác định: {e}")

    def _load_initial_student_data(self):
        self._refresh_student_table()

    def _refresh_student_table(self):
        self._clear_student_table()
        self.filter_class_cbx.set("Tất cả lớp") 
        try:
            student_data = db.get_all_students_from_view() 
            if student_data:
                for sv in student_data:
                    ngay_sinh_obj = sv[4] 
                    ngay_sinh_formatted = ngay_sinh_obj.strftime('%d/%m/%Y') if ngay_sinh_obj else '' 
                    self.student_table.insert("", "end", values=(
                        sv[0], sv[2], sv[3], sv[6], 
                        ngay_sinh_formatted, sv[1], sv[5], sv[7]
                    ))
        except Error as e:
            messagebox.showerror("Lỗi tải DS Sinh viên", f"Lỗi CSDL: {e}", parent=self) # Thêm parent
        except Exception as e:
            messagebox.showerror("Lỗi tải DS Sinh viên", f"Lỗi không xác định: {e}", parent=self) # Thêm parent
    # --- Lớp học (_select_class_tree, _clear_class_form, _add_lop, _update_lop, _delete_lop, _search_lop, _load_class_data, _clear_class_tree giữ nguyên) ---
    def _select_class_tree(self, event=None):
        selected_item = self.class_tree.focus()
        if not selected_item:
            self.selected_lop_key = None
            return
        values = self.class_tree.item(selected_item, "values")
        class_key_str = values[0] 
        try:
            if len(class_key_str) >= 8: 
                mabac = class_key_str[0:2]
                try: 
                    mank_str = class_key_str[2:4]
                    mank = int(mank_str)
                except ValueError:
                     raise ValueError("Mã niên khóa không hợp lệ trong key.")
                remaining_key = class_key_str[4:]
                manganh = None
                sttlop = None
                for ng_key in self.nganh_list.keys():
                    if remaining_key.startswith(ng_key) and len(remaining_key) == len(ng_key) + 2:
                        manganh = ng_key
                        sttlop = remaining_key[len(ng_key):]
                        break
                if not all([mabac, mank is not None, manganh, sttlop]):
                     raise ValueError("Không thể phân tích Mã lớp.")
                self.selected_lop_key = (mabac, mank, manganh, sttlop)
                lop_detail = db.get_lop_detail_by_key(self.selected_lop_key) 
                if lop_detail:
                    self.class_bac_cbx.set(self.bac_list.get(lop_detail[0], ''))
                    self.class_nienkhoa_cbx.set(self.nienkhoa_list.get(lop_detail[1], ''))
                    self.class_nganh_cbx.set(self.nganh_list.get(lop_detail[2], ''))
                    self.class_stt_cbx.set(lop_detail[3])
                    self.class_tenlop_entry.delete(0, "end"); self.class_tenlop_entry.insert(0, lop_detail[4]) 
                    self.class_gv_cbx.set(self.giangvien_list.get(lop_detail[5], ''))
                    self.class_khoa_cbx.set(self.khoa_list.get(lop_detail[6], ''))
                else:
                     self._clear_class_form()
                     messagebox.showwarning("Lỗi", f"Không tìm thấy chi tiết cho lớp {class_key_str}", parent=self)
            else:
                 self._clear_class_form() 
                 messagebox.showwarning("Lỗi", "Mã lớp không đúng định dạng.", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi hiển thị chi tiết lớp", f"Lỗi: {e}", parent=self)
            self._clear_class_form()

    def _clear_class_form(self):
        self.selected_lop_key = None
        self.class_bac_cbx.set('')
        self.class_nienkhoa_cbx.set('')
        self.class_nganh_cbx.set('')
        self.class_stt_cbx.set("01")
        self.class_khoa_cbx.set('')
        self.class_gv_cbx.set('')
        self.class_tenlop_entry.delete(0, "end")
        if self.class_tree.focus():
            self.class_tree.selection_remove(self.class_tree.focus())

    def _add_lop(self):
        try:
            mabac = self._get_key_from_value(self.bac_list, self.class_bac_cbx.get())
            mank = self._get_key_from_value(self.nienkhoa_list, self.class_nienkhoa_cbx.get())
            manganh = self._get_key_from_value(self.nganh_list, self.class_nganh_cbx.get())
            sttlop = self.class_stt_cbx.get()
            makhoa = self._get_key_from_value(self.khoa_list, self.class_khoa_cbx.get())
            gv_val = self.class_gv_cbx.get()
            magv = self._get_key_from_value(self.giangvien_list, gv_val) 
            tenlop_mota = self.class_tenlop_entry.get().strip() 
            if not all([mabac, mank is not None, manganh, sttlop, tenlop_mota, makhoa]):
                messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn Bậc, Niên khóa, Ngành, STT, Khoa và nhập Tên lớp mô tả.")
                return
            existing_lop_key = (mabac, mank, manganh, sttlop)
            if db.get_lop_detail_by_key(existing_lop_key):
                 messagebox.showerror("Lỗi", f"Mã lớp {mabac}{mank}{manganh}{sttlop} đã tồn tại.")
                 return
            if db.add_lop(mabac, mank, manganh, sttlop, tenlop_mota, magv, makhoa):
                 messagebox.showinfo("Thành công", f"Thêm lớp '{tenlop_mota}' thành công.")
                 self.load_all_combobox_data() 
                 self._clear_class_form()
                 self._load_class_data() 
            else:
                 messagebox.showerror("Lỗi", "Thêm lớp thất bại.")
        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi thêm lớp: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")

    def _update_lop(self):
        if not self.selected_lop_key:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn lớp từ bảng bên phải để cập nhật.")
            return
        try:
            mabac, mank, manganh, sttlop = self.selected_lop_key
            tenlop_mota = self.class_tenlop_entry.get().strip()
            makhoa_new = self._get_key_from_value(self.khoa_list, self.class_khoa_cbx.get())
            gv_val_new = self.class_gv_cbx.get()
            magv_new = self._get_key_from_value(self.giangvien_list, gv_val_new) 
            if not tenlop_mota or not makhoa_new:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Tên lớp và chọn Khoa.")
                return
            if db.update_lop(mabac, mank, manganh, sttlop, tenlop_mota, magv_new, makhoa_new):
                 messagebox.showinfo("Thành công", f"Cập nhật lớp '{tenlop_mota}' thành công.")
                 self.load_all_combobox_data()
                 self._clear_class_form()
                 self._load_class_data(f"{mabac}{mank}{manganh}{sttlop}") 
                 self._refresh_student_table() 
            else:
                 messagebox.showerror("Lỗi", "Cập nhật lớp thất bại.")
        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi cập nhật lớp: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")

    def _delete_lop(self):
        if not self.selected_lop_key:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn lớp từ bảng để xóa.")
            return
        tenlop_display = self.lop_list.get(self.selected_lop_key, f"{self.selected_lop_key[0]}{self.selected_lop_key[1]}{self.selected_lop_key[2]}{self.selected_lop_key[3]}")
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa lớp '{tenlop_display}' ({self.selected_lop_key})?\nLƯU Ý: Hành động này có thể thất bại nếu lớp đang có sinh viên.", icon='warning'):
            try:
                if db.delete_lop(self.selected_lop_key[0], self.selected_lop_key[1], self.selected_lop_key[2], self.selected_lop_key[3]):
                    messagebox.showinfo("Thành công", f"Xóa lớp '{tenlop_display}' thành công.")
                    self.load_all_combobox_data()
                    self._clear_class_form()
                    self._load_class_data() 
                    self._refresh_student_table() 
                else:
                    messagebox.showerror("Lỗi", f"Xóa lớp thất bại. Lớp có thể đang chứa sinh viên hoặc dữ liệu liên quan khác.")
            except Error as e:
                messagebox.showerror("Lỗi CSDL", f"Lỗi khi xóa lớp: {e}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")

    def _search_lop(self):
        search_term = self.class_tenlop_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Tên hoặc Mã lớp vào ô trên cùng để tìm kiếm.")
            return
        self._load_class_data(search_term)

    def _load_class_data(self, search_term=None):
        self._clear_class_tree()
        try:
            if search_term:
                class_data = db.search_lop_by_name_or_key(search_term) 
            else:
                class_data = db.get_all_lop_details() 
            if class_data:
                for lop in class_data:
                    key_str = f"{lop[0]}{lop[1]}{lop[2]}{lop[3]}"
                    ten_gv = self.giangvien_list.get(lop[5], 'Chưa gán')
                    ten_khoa = self.khoa_list.get(lop[6], 'Không rõ')
                    self.class_tree.insert("", "end", values=(
                        key_str, lop[4], ten_gv, ten_khoa
                    ))
            elif search_term:
                 messagebox.showinfo("Không tìm thấy", f"Không tìm thấy lớp nào với '{search_term}'.", parent=self)
        except Error as e:
            messagebox.showerror("Lỗi tải danh sách lớp", f"Lỗi CSDL: {e}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi tải danh sách lớp", f"Lỗi không xác định: {e}", parent=self)

    def _clear_class_tree(self):
        for item in self.class_tree.get_children():
            self.class_tree.delete(item)
            
    # --- Sinh viên ---
    def _select_student_table(self, event=None):
        selected_item = self.student_table.focus()
        if not selected_item:
            self.selected_sv_id = None
            return
            
        values = self.student_table.item(selected_item, "values")
        try:
            self.selected_sv_id = int(values[0])
            self.sv_id_entry.delete(0, "end"); self.sv_id_entry.insert(0, values[0])
            self.sv_name_entry.delete(0, "end"); self.sv_name_entry.insert(0, f"{values[1]} {values[2]}") 
            self.sv_gender_cbx.set(values[3])
            
            # --- SỬA LỖI NGÀY SINH & HIỂN THỊ MESSAGEBOX ---
            try: 
                dob_obj = datetime.strptime(values[4], '%d/%m/%Y') if values[4] else None
                self.sv_dob_entry.set_date_obj(dob_obj) 
            except ValueError as ve:
                 self.sv_dob_entry.clear() 
                 # Hiển thị lỗi ngày sinh không hợp lệ
                 messagebox.showwarning("Lỗi Ngày Sinh", f"Ngày sinh '{values[4]}' không hợp lệ. Vui lòng kiểm tra lại.", parent=self)
            except Exception as e_date: # Bắt các lỗi khác từ set_date_obj
                 self.sv_dob_entry.clear()
                 # Hiển thị lỗi chung khi set date
                 messagebox.showerror("Lỗi Hiển Thị Ngày Sinh", f"Lỗi khi đặt ngày sinh: {e_date}", parent=self)
                 
            self.sv_lop_cbx.set(values[5]) 
            self.sv_address_entry.delete(0, "end"); self.sv_address_entry.insert(0, values[6])
            self.sv_note_entry.delete(0, "end"); self.sv_note_entry.insert(0, values[7])

            self.sv_id_entry.configure(state="disabled") 

        except (ValueError, IndexError) as e: # Lỗi parse MSSV hoặc index
            messagebox.showerror("Lỗi Dữ Liệu", f"Dữ liệu sinh viên không hợp lệ: {e}", parent=self)
            self._clear_student_form()
        except Exception as e: # Các lỗi khác
            messagebox.showerror("Lỗi Hiển Thị Chi Tiết SV", f"Lỗi không xác định: {e}", parent=self) 
            self._clear_student_form()

    def _clear_student_form(self):
        """Xóa trắng form quản lý sinh viên và kích hoạt lại ô MSSV."""
        self._refresh_student_table()
        self.selected_sv_id = None
        # self.sv_search_entry.delete(0, "end") # Đã xóa ô tìm kiếm riêng
        self.sv_id_entry.delete(0, "end")
        self.sv_name_entry.delete(0, "end")
        self.sv_gender_cbx.set("Nam")
        self.sv_dob_entry.clear() # Gọi hàm clear của DatePicker
        self.sv_lop_cbx.set('') # Set về trống
        self.sv_address_entry.delete(0, "end")
        self.sv_note_entry.delete(0, "end")

        # <<< Dòng quan trọng để kích hoạt lại ô MSSV >>>
        self.sv_id_entry.configure(state="normal")

        # Bỏ chọn trong bảng chính (nếu đang chọn)
        if self.student_table.focus():
            self.student_table.selection_remove(self.student_table.focus())

    def _add_sinhvien(self):
        # --- SỬA LỖI NGÀY SINH ---
        try:
            mssv_str = self.sv_id_entry.get().strip()
            hoten = self.sv_name_entry.get().strip()
            gioitinh = self.sv_gender_cbx.get()
            ngaysinh_obj = self.sv_dob_entry.get_date_object() # Lấy object
            ngaysinh_str = ngaysinh_obj.strftime('%Y-%m-%d') if ngaysinh_obj else None # Format hoặc None
            lop_display = self.sv_lop_cbx.get()
            diachi = self.sv_address_entry.get().strip()
            ghichu = self.sv_note_entry.get().strip()

            if not mssv_str or not hoten or not lop_display:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập MSSV, Họ tên và chọn Lớp.")
                return
            
            lop_key = self._get_key_from_value(self.lop_list, lop_display)
            if not lop_key:
                 messagebox.showerror("Lỗi", "Lớp được chọn không hợp lệ.")
                 return
            mabac, mank, manganh, sttlop = lop_key
                 
            try: mssv = int(mssv_str)
            except ValueError:
                 messagebox.showerror("Lỗi định dạng", "MSSV phải là một số nguyên.")
                 return
                 
            if db.get_student_detail_from_view(mssv):
                 messagebox.showerror("Lỗi", f"MSSV {mssv} đã tồn tại.")
                 return

            if db.add_sinhvien(mssv, mabac, mank, manganh, sttlop, hoten, ngaysinh_str, diachi, gioitinh, ghichu):
                 messagebox.showinfo("Thành công", f"Thêm sinh viên '{hoten}' (MSSV: {mssv}) thành công.")
                 self._clear_student_form()
                 self._refresh_student_table() 
            else:
                 messagebox.showerror("Lỗi", "Thêm sinh viên thất bại.")

        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi thêm sinh viên: {e}")
        except AttributeError as ae: # Bắt lỗi nếu gọi strftime trên None
            if "'NoneType' object has no attribute 'strftime'" in str(ae):
                 messagebox.showerror("Lỗi Ngày Sinh", "Định dạng ngày sinh không hợp lệ hoặc bị bỏ trống.")
            else:
                 messagebox.showerror("Lỗi", f"Lỗi thuộc tính khi thêm sinh viên: {ae}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định khi thêm sinh viên: {e}")

    def _update_sinhvien(self):
        # --- SỬA LỖI NGÀY SINH ---
        if not self.selected_sv_id:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn sinh viên từ bảng dưới để cập nhật.")
            return

        try:
            mssv = self.selected_sv_id 
            hoten = self.sv_name_entry.get().strip()
            gioitinh = self.sv_gender_cbx.get()
            ngaysinh_obj = self.sv_dob_entry.get_date_object()
            ngaysinh_str = ngaysinh_obj.strftime('%Y-%m-%d') if ngaysinh_obj else None
            lop_display = self.sv_lop_cbx.get()
            diachi = self.sv_address_entry.get().strip()
            ghichu = self.sv_note_entry.get().strip()

            if not hoten or not lop_display:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Họ tên và chọn Lớp.")
                return

            lop_key = self._get_key_from_value(self.lop_list, lop_display)
            if not lop_key:
                 messagebox.showerror("Lỗi", "Lớp được chọn không hợp lệ.")
                 return
            mabac, mank, manganh, sttlop = lop_key
            
            if db.update_sinhvien(mssv, mabac, mank, manganh, sttlop, hoten, ngaysinh_str, diachi, gioitinh, ghichu):
                 messagebox.showinfo("Thành công", f"Cập nhật sinh viên (MSSV: {mssv}) thành công.")
                 self._clear_student_form()
                 self._refresh_student_table()
            else:
                 messagebox.showerror("Lỗi", "Cập nhật sinh viên thất bại.")

        except Error as e:
            messagebox.showerror("Lỗi CSDL", f"Lỗi khi cập nhật sinh viên: {e}")
        except AttributeError as ae: # Bắt lỗi nếu gọi strftime trên None
            if "'NoneType' object has no attribute 'strftime'" in str(ae):
                 messagebox.showerror("Lỗi Ngày Sinh", "Định dạng ngày sinh không hợp lệ hoặc bị bỏ trống.")
            else:
                 messagebox.showerror("Lỗi", f"Lỗi thuộc tính khi cập nhật sinh viên: {ae}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định khi cập nhật sinh viên: {e}")

    def _delete_sinhvien(self):
        # (Giữ nguyên logic hàm _delete_sinhvien đã cung cấp)
        if not self.selected_sv_id:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn sinh viên từ bảng để xóa.")
            return
        mssv = self.selected_sv_id
        selected_item = self.student_table.focus()
        hoten = ""
        if selected_item:
             values = self.student_table.item(selected_item, "values")
             hoten = f"{values[1]} {values[2]}" if len(values) > 2 else f"MSSV {mssv}"
        else: hoten = f"MSSV {mssv}" 
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa sinh viên '{hoten}' (MSSV: {mssv})?\nLƯU Ý: Hành động này sẽ xóa cả dữ liệu điểm danh và khuôn mặt liên quan.", icon='warning'):
            try:
                if db.delete_sinhvien(mssv):
                    messagebox.showinfo("Thành công", f"Xóa sinh viên (MSSV: {mssv}) thành công.")
                    self._clear_student_form()
                    self._refresh_student_table()
                else:
                    messagebox.showerror("Lỗi", "Xóa sinh viên thất bại.")
            except Error as e:
                messagebox.showerror("Lỗi CSDL", f"Lỗi khi xóa sinh viên: {e}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi không xác định khi xóa sinh viên: {e}")

    def _search_student(self):
        # SỬA: Đọc từ sv_id_entry
        mssv_str = self.sv_id_entry.get().strip() 
        if not mssv_str:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập MSSV vào ô MSSV để tìm kiếm.")
            return
            
        try: mssv = int(mssv_str)
        except ValueError:
            messagebox.showerror("Lỗi định dạng", "MSSV phải là một số nguyên.")
            return

        self._clear_student_table() 
        try:
            sv_data = db.get_student_detail_from_view(mssv) 
            if sv_data:
                ngay_sinh_obj = sv_data[4]
                ngay_sinh_formatted = ngay_sinh_obj.strftime('%d/%m/%Y') if ngay_sinh_obj else ''
                self.student_table.insert("", "end", values=(
                    sv_data[0], sv_data[2], sv_data[3], sv_data[6], 
                    ngay_sinh_formatted, sv_data[1], sv_data[5], sv_data[7]
                ))
                # Tự động chọn và load lên form
                item_id = self.student_table.get_children()[0] 
                if item_id: # Kiểm tra xem có item không
                    self.student_table.focus(item_id)
                    self.student_table.selection_set(item_id)
                    self._select_student_table() 
            else:
                messagebox.showinfo("Không tìm thấy", f"Không tìm thấy sinh viên với MSSV {mssv}.")
                self._refresh_student_table() 
        except Error as e:
            messagebox.showerror("Lỗi tìm kiếm sinh viên", f"Lỗi CSDL: {e}")
            self._refresh_student_table() 
        except Exception as e:
            messagebox.showerror("Lỗi tìm kiếm sinh viên", f"Lỗi không xác định: {e}")
            self._refresh_student_table() 

    # --- Bảng chính (Lọc) ---
    def _filter_students_by_class(self):
        # (Giữ nguyên logic hàm _filter_students_by_class đã cung cấp)
        selected_lop_display = self.filter_class_cbx.get()
        self._clear_student_table()
        if selected_lop_display == "Tất cả lớp":
            self._refresh_student_table() 
            return
        try:
            student_data = db.get_students_by_class_from_view(selected_lop_display) 
            if student_data:
                for sv in student_data:
                    ngay_sinh_obj = sv[4]
                    ngay_sinh_formatted = ngay_sinh_obj.strftime('%d/%m/%Y') if ngay_sinh_obj else ''
                    self.student_table.insert("", "end", values=(
                        sv[0], sv[2], sv[3], sv[6], 
                        ngay_sinh_formatted, sv[1], sv[5], sv[7]
                    ))
        except Error as e:
            messagebox.showerror("Lỗi lọc sinh viên", f"Lỗi CSDL: {e}")
        except Exception as e:
            messagebox.showerror("Lỗi lọc sinh viên", f"Lỗi không xác định: {e}")

    def _clear_student_table(self):
        # (Giữ nguyên logic hàm _clear_student_table đã cung cấp)
         for item in self.student_table.get_children():
            self.student_table.delete(item)
    # --- Hàm hỗ trợ (_get_key_from_value giữ nguyên) ---
    def _get_key_from_value(self, mapping_dict, display_value):
        if not display_value or display_value == '': return None 
        if mapping_dict is self.giangvien_list and ' - ' in display_value:
             try: return int(display_value.split(' - ')[0])
             except ValueError: return None 
        if mapping_dict is self.nienkhoa_list:
             for k, v in mapping_dict.items():
                 if v == display_value: return k 
             return None
        for k, v in mapping_dict.items():
            if v == display_value: return k
        if mapping_dict is self.lop_list:
             for k, v in mapping_dict.items():
                 if v == display_value: return k 
        return None