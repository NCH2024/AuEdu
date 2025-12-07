import customtkinter as ctk
from gui.base.utils import *
from tkinter import messagebox
from core.models import SinhVien
import core.database as Db
from core.utils import *

class LecturerAttendance_SearchStudent(ctk.CTkFrame):
    def __init__(self, master=None, username=None, **kwargs):
        super().__init__(master, **kwargs)
        self.username = username 
        self.session_map = {}
        # Màu nền trắng tổng thể
        self.configure(fg_color="white")

        # Biến màu sắc
        self.widget_color = "#2DFCB0"
        self.txt_color_title = "#1736FF"

        # Bố cục tổng thể
        self.pack(fill="both", expand=True)
        self.grid_columnconfigure(0, weight=70)  # bên trái to hơn
        self.grid_columnconfigure(1, weight=30)  # bên phải nhỏ hơn
        self.grid_rowconfigure(1, weight=1)     # cho phép dãn chiều cao nội dung

        # === TIÊU ĐỀ ===
        self.txt_title = LabelCustom(self, "Dashboard > Điểm danh sinh viên > Tra cứu sinh viên",
                                     wraplength=600, font_size=16, text_color="#05243F")
        self.txt_title.grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="nw")

        # === KHUNG TRÁI ===
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=1, column=0, padx=(15, 7), pady=10, sticky="nsew")
        self.left_frame.grid_rowconfigure(0, weight=0)  # info sv
        self.left_frame.grid_rowconfigure(1, weight=1)  # info điểm danh
        self.left_frame.grid_columnconfigure(0, weight=1)

        # --- THÔNG TIN SINH VIÊN ---
        self.widget_student = ctk.CTkFrame(self.left_frame, fg_color="white", height=300, border_color=self.widget_color, border_width=2)
        self.widget_student.grid(row=0, column=0, sticky="nsew", pady=(0, 7))
        self.widget_student.grid_propagate(False)  # Giữ đúng chiều cao
        self.widget_student.grid_columnconfigure(0, weight=10)
        self.widget_student.grid_columnconfigure(1, weight=90)
        self.widget_student.grid_rowconfigure(0, weight=0)
        self.widget_student.grid_rowconfigure(1, weight=1)
        
        self.widget_student_title = LabelCustom(self.widget_student, "THÔNG TIN SINH VIÊN", font_size=12, text_color=self.txt_color_title)
        self.widget_student_title.grid(row=0, column=0, columnspan=2, padx=5, pady=2, sticky="nw")
        
        # --- Khung chứa ảnh sinh viên ---
        self.widget_student_image = ctk.CTkFrame(self.widget_student, fg_color="transparent")
        self.widget_student_image.grid(row=1, column=0, padx=(2,0), pady=2, sticky="nsew")
        
        self.bg_ctkimage = ImageProcessor("resources/images/avatar_default.jpeg") \
                                .crop_to_aspect(160, 180) \
                                .resize(160, 180) \
                                .to_ctkimage(size=(160,180))
        self.bg_label = ctk.CTkLabel(self.widget_student_image, image=self.bg_ctkimage, text="")
        self.bg_label.pack(anchor="n", pady=5) 
        
        # --- khung chứ thông tin sinh viên ---
        self.widget_student_info = ctk.CTkFrame(self.widget_student, fg_color="transparent")
        self.widget_student_info.grid(row=1, column=1, padx=2, pady=2, sticky="nsew")
        
        self.txt_HoTen = LabelCustom(self.widget_student_info, "Họ và Tên: ", value="---")
        self.txt_Class = LabelCustom(self.widget_student_info, "Lớp: ", value="---")
        self.txt_Birthday = LabelCustom(self.widget_student_info, "Năm sinh: ", value="---")
        self.txt_Level = LabelCustom(self.widget_student_info, "Bậc học: ", value="---")
        self.txt_SchoolYear = LabelCustom(self.widget_student_info, "Niên khoá: ", value="---")
        self.txt_Specialized = LabelCustom(self.widget_student_info, "Chuyên ngành: ", value="---")
        self.txt_Notes = LabelCustom(self.widget_student_info, "Ghi chú: ", value="---")

       # --- THÔNG TIN ĐIỂM DANH ---
        self.widget_aboutAttendance = ctk.CTkFrame(
            self.left_frame,
            fg_color="white",
            border_color=self.widget_color,
            border_width=2,
            height=120
        )
        self.widget_aboutAttendance.grid(row=1, column=0, sticky="nsew")
        self.widget_aboutAttendance.grid_columnconfigure((0, 1), weight=1)
        self.widget_aboutAttendance.grid_propagate(False)

        self.widget_aboutAttendance_title = LabelCustom(
            self.widget_aboutAttendance,
            "THÔNG TIN ĐIỂM DANH",
            font_size=12,
            text_color=self.txt_color_title
        )
        self.widget_aboutAttendance_title.pack(anchor="w", padx=5, pady=(5, 2))

        # --- GOM NHÓM KHUNG THÔNG TIN ---
        frame_left_info = ctk.CTkFrame(self.widget_aboutAttendance, fg_color="transparent")
        frame_right_info = ctk.CTkFrame(self.widget_aboutAttendance, fg_color="transparent")
        frame_left_info.pack(side="left", padx=(5, 0), pady=0)
        frame_right_info.pack(side="left", padx=(0, 5), pady=0)

        # === BÊN TRÁI: Học phần, Ngày, Buổi ===
        self.widget_aboutAttendance_subject = LabelCustom(frame_left_info, "Học phần:", value="---", font_size=14, wraplength=150)
        self.widget_aboutAttendance_subject.pack(anchor="w", pady=(0, 1))
        self.widget_aboutAttendance_date = LabelCustom(frame_left_info, "Ngày:", value="---", font_size=14, wraplength=150)
        self.widget_aboutAttendance_date.pack(anchor="w", pady=(0, 1))
        self.widget_aboutAttendance_session = LabelCustom(frame_left_info, "Buổi:", value="---", font_size=14, wraplength=150)
        self.widget_aboutAttendance_session.pack(anchor="w", pady=(0, 1))

        # === BÊN PHẢI: Thời gian điểm danh, Trạng thái ===
        self.widget_aboutAttendance_timeAttendance = LabelCustom(
            frame_right_info,
            "Thời gian điểm danh:",
            value="None",
            text_color="red",
            font_size=14, wraplength=150
        )
        self.widget_aboutAttendance_timeAttendance.pack(anchor="w", pady=(0, 1))

        self.widget_aboutAttendance_state = LabelCustom(
            frame_right_info,
            "Trạng thái:",
            value="None",
            text_color="red",
            font_size=14, wraplength=150
        )
        self.widget_aboutAttendance_state.pack(anchor="w", pady=(0, 1))


        # === KHUNG PHẢI ===
        self.widget_search = ctk.CTkFrame(self, fg_color=self.widget_color, width=300)
        self.widget_search.grid(row=1, column=1, padx=(7, 15), pady=10, sticky="nsew")
        self.widget_search.grid_propagate(False)
        self.widget_search.grid_columnconfigure((0,1), weight=1)
        self.widget_search.grid_rowconfigure(0, weight=0)
        
        self.widget_search_title = LabelCustom(self.widget_search, "TÌM KIẾM", font_size=12, text_color=self.txt_color_title)
        self.widget_search_title.grid(row=0, column=0, columnspan=2, padx=5, pady=0, sticky="nw")
        
        self.ent_IDStudent = ctk.CTkEntry(self.widget_search, placeholder_text="Nhập vào MSSV", 
                                            width=150, height=40, font=("Bahnschrift", 14))
        self.ent_IDStudent.grid(row=1, column=0, padx=(10,0), pady=0, sticky="nw")
        
        # Kết nối nút Tìm kiếm nhanh với chức năng tra cứu sinh viên
        self.btn_searchQuickly = ButtonTheme(self.widget_search, "Tìm kiếm nhanh", width=100, command=self.search_student)
        self.btn_searchQuickly.grid(row=1, column=1, padx=(0,10), pady=0, sticky="ne")
        
        self.widget_search_title = LabelCustom(self.widget_search, "TÌM KIẾM THÔNG TIN ĐIỂM DANH", font_size=12, text_color=self.txt_color_title)
        self.widget_search_title.grid(row=2, column=0, columnspan=2, padx=5, pady=(10,2), sticky="nw")
        
        self.cbx_subject = ComboboxTheme(self.widget_search, values=["None"], command=self.on_subject_selected)
        self.cbx_subject.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="nwe")
        
        self.cbx_date = ComboboxTheme(self.widget_search, values=["None"], command=self.on_date_selected)
        self.cbx_date.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="nwe")
        
        self.cbx_session = ComboboxTheme(self.widget_search, values=["None"])
        self.cbx_session.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="nwe")
        
        self.btn_searchAll = ButtonTheme(self.widget_search, "Tìm kiếm điểm danh", width=100, command=self.search_attendance)
        self.btn_searchAll.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="new")
        
        self.note = LabelCustom(self.widget_search, "\nHƯỚNG DẪN:\n\n1. Giảng viên nhập vào ô MSSV và bấm Tìm kiếm nhanh để xem thông tin sinh viên.\n\n2. Nếu muốn xem quá trình điểm danh tại một thời điểm của sinh viên, vui lòng nhập đầy đủ MSSV và chọn các thành phần phù hợp rồi mới bấm Tìm kiếm điểm danh.", font_size=10 , wraplength=300)
        self.note.grid(row=7, column=0, columnspan=2, padx=10, pady=5, sticky="wse")

        # Khởi tạo combobox động
        self.init_subjects()

    
    # ==== HÀM CHỨC NĂNG ====
    def _fix_none(self, val):
        return "Chưa có dữ liệu" if val is None or (isinstance(val, str) and val.strip() == "") else str(val)

    def init_subjects(self):
        subjects = Db.get_subjects_of_lecturer(self.username)
        if subjects:
            self.cbx_subject.configure(values=subjects)
            self.cbx_subject.set(subjects[0])
            self.on_subject_selected(subjects[0])
        else:
            self.cbx_subject.configure(values=["None"])
            self.cbx_subject.set("None")
            self.cbx_date.configure(values=["None"])
            self.cbx_date.set("None")
            self.cbx_session.configure(values=["None"])
            self.cbx_session.set("None")

    def on_subject_selected(self, ten_hocphan):
        if ten_hocphan == "None":
            self.cbx_date.configure(values=["None"])
            self.cbx_date.set("None")
            self.cbx_session.configure(values=["None"])
            self.cbx_session.set("None")
            return
        dates = Db.get_dates_of_subject(self.username, ten_hocphan)
        if dates:
            self.cbx_date.configure(values=dates)
            self.cbx_date.set(dates[0])
            self.on_date_selected(dates[0])
        else:
            self.cbx_date.configure(values=["None"])
            self.cbx_date.set("None")
            self.cbx_session.configure(values=["None"])
            self.cbx_session.set("None")

    def on_date_selected(self, ngay):
        ten_hocphan = self.cbx_subject.get()
        if ngay == "None" or ten_hocphan == "None":
            self.cbx_session.configure(values=["None"])
            self.cbx_session.set("None")
            return
        
        self.session_map = Db.get_loai_diem_danh(self.username, ten_hocphan, ngay)

        if self.session_map:
            self.cbx_session.configure(values=list(self.session_map.keys()))
            self.cbx_session.set(list(self.session_map.keys())[0])
        else:
            self.cbx_session.configure(values=["None"])
            self.cbx_session.set("None")


    def search_attendance(self):
        self.search_student()
        maSV = self.ent_IDStudent.get().strip()
        ten_hocphan = self.cbx_subject.get()
        ngay = self.cbx_date.get()
        selected_session_name = self.cbx_session.get()
        buoi = self.session_map.get(selected_session_name)

        # Kiểm tra đầu vào
        if not maSV or ten_hocphan == "None" or ngay == "None" or buoi is None:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập MSSV và chọn đầy đủ học phần, ngày, buổi!")
            return


        # 🛠️ Chuyển định dạng ngày để MySQL hiểu
        ngay_mysql = convert_to_mysql_date(ngay)
        if not ngay_mysql:
            messagebox.showerror("Lỗi ngày tháng", f"Không thể chuyển định dạng ngày: {ngay}")
            return

        result = Db.get_attendance_of_student(maSV, ten_hocphan, ngay_mysql, buoi)

        # Hiển thị dữ liệu
        if result:
            self.widget_aboutAttendance_subject.value.configure(text=self._fix_none(result[0]))
            self.widget_aboutAttendance_date.value.configure(text=self._fix_none(result[1]))
            self.widget_aboutAttendance_session.value.configure(text=self._fix_none(result[2]))
            self.widget_aboutAttendance_timeAttendance.value.configure(text=self._fix_none(result[3]))
            self.widget_aboutAttendance_state.value.configure(text=self._fix_none(result[4]))
        else:
            self.widget_aboutAttendance_subject.value.configure(text="Không có dữ liệu")
            self.widget_aboutAttendance_date.value.configure(text="Không có dữ liệu")
            self.widget_aboutAttendance_session.value.configure(text="Không có dữ liệu")
            self.widget_aboutAttendance_timeAttendance.value.configure(text="Không có dữ liệu")
            self.widget_aboutAttendance_state.value.configure(text="Không có dữ liệu")
                


    def _fix_none(self, val):
        return "Chưa có dữ liệu" if val is None or (isinstance(val, str) and val.strip() == "") else str(val)
    def search_student(self):
        maSV = self.ent_IDStudent.get().strip()
        if not maSV:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập MSSV.")
            return
        sv_tuple = Db.get_student_by_id(maSV)
        if not sv_tuple:
            messagebox.showinfo("Không tìm thấy", f"Không tìm thấy sinh viên với MSSV {maSV}.")
            self.clear_info()
            return

        # Lấy các trường tên riêng biệt ra biến
        ten_bac = self._fix_none(sv_tuple[1])
        ten_nienkhoa = self._fix_none(sv_tuple[2])
        ten_nganh = self._fix_none(sv_tuple[3])

        # Tạo SinhVien chỉ với các trường đúng định nghĩa (giả sử đúng thứ tự cũ)
        sv = SinhVien(
            MaSV=sv_tuple[0],
            MaBac=sv_tuple[4],
            MaNienKhoa=sv_tuple[5],
            MaNganh=sv_tuple[6],
            STTLop=sv_tuple[7],
            HoTenSV=sv_tuple[8],
            NamSinh=sv_tuple[9],
            DiaChi=sv_tuple[10],
            GioiTinh=sv_tuple[11],
            GhiChu=sv_tuple[12]
        )
        # Cập nhật giao diện, dùng _fix_none cho tất cả trường
        self.txt_Level.value.configure(text=ten_bac)
        self.txt_SchoolYear.value.configure(text=ten_nienkhoa)
        self.txt_Specialized.value.configure(text=ten_nganh)
        self.txt_Class.value.configure(text=f"{self._fix_none(sv.MaBac)}{self._fix_none(sv.MaNienKhoa)}{self._fix_none(sv.MaNganh)}{self._fix_none(sv.STTLop)}")
        self.txt_HoTen.value.configure(text=self._fix_none(sv.HoTenSV))
        self.txt_Birthday.value.configure(text=self._fix_none(sv.NamSinh))
        self.txt_Notes.value.configure(text=self._fix_none(sv.GhiChu))

    def clear_info(self):
        for lbl in [
            self.txt_HoTen, self.txt_Class, self.txt_Birthday, 
            self.txt_Level, self.txt_SchoolYear, self.txt_Specialized, self.txt_Notes
        ]:
            lbl.value.configure(text="")

    # ==== CHẾ ĐỘ HIỂN THỊ DẠNG CỬA SỔ ====
    _window_instance = None

    @classmethod
    def show_window(cls, parent=None, username=None):
        if cls._window_instance is None or not cls._window_instance.winfo_exists():
            top = ctk.CTkToplevel()
            top.geometry("950x600")
            top.title("Tra cứu sinh viên")
            top.configure(fg_color="white")
            if parent:
                top.transient(parent.winfo_toplevel())
            top.lift()
            top.focus_force()
            cls._window_instance = top

            # Truyền username vào đây
            cls(master=top, username=username)

            def on_close():
                cls._window_instance.destroy()
                cls._window_instance = None

            top.protocol("WM_DELETE_WINDOW", on_close)
        else:
            cls._window_instance.focus_force()