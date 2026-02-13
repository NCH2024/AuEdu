import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, time, timedelta
import threading
import core.database as Db
from gui.base.utils import *
import time as tm
from core.app_config import save_config
from gui.user.lecturer_attendance_searchStudent import * 
from gui.user.lecturer_attendance_setting import * 
from core.app_face_recognition.widget_trainning_face import *
from core.app_face_recognition.camera_setup import CameraManager
from core.app_face_recognition.check_config_attendance import CheckConfigAttendance
from core.theme_manager import Theme, AppFont 


class LecturerAttendance(ctk.CTkFrame):
    def __init__(self, master=None, username=None, config=None,**kwargs):
        kwargs['fg_color'] = Theme.Color.BG
        super().__init__(master, **kwargs)
        self.username = username; self.parent = master; self.AppConfig = config; self.available_cameras = []; self.controller = None
        self.widget_color = Theme.Color.BG_CARD; self.txt_color_title = Theme.Color.PRIMARY 
        self.attendance_processor = None; self.camera_window = None

        self.title_widget = ctk.CTkLabel(self, text="Dashboard > ĐIỂM DANH SINH VIÊN", font=AppFont.H3, text_color=Theme.Color.TEXT)
        self.title_widget.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nw")

        # MENU TRÁI
        self.widget_menu = ctk.CTkFrame(self, fg_color="transparent", width=250)
        self.widget_menu.grid(row=1, column=0, rowspan=2, sticky="nsw")
        self.widget_menu.grid_columnconfigure(0, weight=1)

        # Block 1
        self.widget_menu_advanced = WigdetFrame(self.widget_menu, widget_color=self.widget_color)
        self.widget_menu_advanced.grid(row=0, column=0, pady=5, sticky="nsew")
        LabelCustom(self.widget_menu_advanced, "CHỨC NĂNG NÂNG CAO", font_size=12, font_weight="bold", text_color=self.txt_color_title).pack(pady=5, padx=10, anchor="w")
        ButtonTheme(self.widget_menu_advanced, "Tra cứu sinh viên", command=self.show_searchStudent).pack(pady=(0, 10), padx=10, fill="x")

        # Block 2
        self.widget_menu_face = WigdetFrame(self.widget_menu, widget_color=self.widget_color)
        self.widget_menu_face.grid(row=1, column=0, pady=(0,5), sticky="nsew")
        LabelCustom(self.widget_menu_face, "CẬP NHẬT SINH TRẮC HỌC", font_size=12, font_weight="bold", text_color=self.txt_color_title).pack(pady=5, padx=10, anchor="w")
        ButtonTheme(self.widget_menu_face, "Đào tạo dữ liệu khuôn mặt", command=self.show_tranning_face).pack(pady=(0, 10), padx=10, fill="x")

        # Block 3
        self.widget_menu_devices = WigdetFrame(self.widget_menu, widget_color=self.widget_color)
        self.widget_menu_devices.grid(row=2, column=0, pady=(0,5), sticky="nsew")
        LabelCustom(self.widget_menu_devices, "THIẾT BỊ", font_size=12, font_weight="bold", text_color=self.txt_color_title).pack(pady=5, padx=10, anchor="w")
        self.widget_menu_devices_cbx_camera = ComboboxTheme(self.widget_menu_devices, values=["Đang kiểm tra..."], state="readonly")
        self.widget_menu_devices_cbx_camera.pack(pady=(0, 10), padx=10, fill="x")
        self.check_camera()
        ButtonTheme(self.widget_menu_devices, "Lưu Camera", fg_color=Theme.Color.SUCCESS, command=self.save_camera_setting).pack(pady=(0, 5), padx=10, fill="x")
        ButtonTheme(self.widget_menu_devices, "Test Camera", fg_color=Theme.Color.INFO, command=self.test_camera).pack(pady=(0, 5), padx=10, fill="x")
        LabelCustom(self.widget_menu_devices, text="(*) Lưu Camera trước khi Test!", font_size=12, text_color=Theme.Color.TEXT_SUB).pack(pady=(0, 10), padx=10)

        # KHUNG PHẢI
        self.widget_attendance_options = ctk.CTkFrame(self, fg_color="transparent")
        self.widget_attendance_options.grid(row=1, column=1, sticky="nsew")
        self.widget_attendance_options.grid_columnconfigure(0, weight=3); self.widget_attendance_options.grid_columnconfigure(1, weight=1)

        # Left Options
        self.widget_attendance_options_left = WigdetFrame(self.widget_attendance_options, widget_color=self.widget_color)
        self.widget_attendance_options_left.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.widget_attendance_options_left.grid_columnconfigure((0, 1), weight=1)
        LabelCustom(self.widget_attendance_options_left, "THÔNG TIN ĐIỂM DANH", font_size=12, font_weight="bold", text_color=self.txt_color_title).grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        self.widget_attendance_options_left_cbxClass = ComboboxTheme(self.widget_attendance_options_left, values=["Đang tải..."], state="readonly", command=self.on_class_selected); self.widget_attendance_options_left_cbxClass.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.widget_attendance_options_left_cbxSubject = ComboboxTheme(self.widget_attendance_options_left, values=["Đang tải..."], state="disabled", command=self.on_subject_selected); self.widget_attendance_options_left_cbxSubject.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.widget_attendance_options_left_cbxDate = ComboboxTheme(self.widget_attendance_options_left, values=["Đang tải..."], state="disabled", command=self.on_date_selected); self.widget_attendance_options_left_cbxDate.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.widget_attendance_options_left_cbxSession = ComboboxTheme(self.widget_attendance_options_left, values=["Đang tải..."], state="disabled"); self.widget_attendance_options_left_cbxSession.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.widget_attendance_options_left_btnSeen = ButtonTheme(self.widget_attendance_options_left, text="Xem Danh Sách", command=self.show_attendance_list); self.widget_attendance_options_left_btnSeen.grid(row=1, column=2, rowspan=2, padx=10, pady=5, sticky="ns")

        # Right Options
        self.widget_attendance_options_right = WigdetFrame(self.widget_attendance_options, widget_color=self.widget_color)
        self.widget_attendance_options_right.grid(row=0, column=1, padx=(0,5), pady=5, sticky="nsew")
        LabelCustom(self.widget_attendance_options_right, "CHẾ ĐỘ", font_size=12, font_weight="bold", text_color=self.txt_color_title).pack(pady=5, padx=10, anchor="w")
        self.attendance_mode_var = ctk.StringVar(value="single")
        # RadioButton với Theme
        ctk.CTkRadioButton(self.widget_attendance_options_right, text="Từng SV", variable=self.attendance_mode_var, value="single", text_color=Theme.Color.TEXT, fg_color=Theme.Color.PRIMARY, hover_color=Theme.Color.PRIMARY_HOVER).pack(pady=2, padx=20, anchor="w")
        ctk.CTkRadioButton(self.widget_attendance_options_right, text="Cả lớp", variable=self.attendance_mode_var, value="all", text_color=Theme.Color.TEXT, fg_color=Theme.Color.PRIMARY, hover_color=Theme.Color.PRIMARY_HOVER).pack(pady=2, padx=20, anchor="w")
        self.btn_attendance = ButtonTheme(self.widget_attendance_options_right, text="Bắt đầu\nĐiểm danh", fg_color=Theme.Color.PRIMARY, command=self.attendance_student)
        self.btn_attendance.pack(pady=10, padx=10, fill="x")

        # LIST VIEW
        self.widget_list_attendance = ctk.CTkFrame(self, fg_color=Theme.Color.BG_CARD, border_color=Theme.Color.BORDER, border_width=1)
        self.widget_list_attendance.grid(row=2, column=1, pady=(0,5), padx=5, sticky="nsew")
        self.widget_list_attendance.grid_columnconfigure(0, weight=1); self.widget_list_attendance.grid_rowconfigure(1, weight=1)
        LabelCustom(self.widget_list_attendance, "DANH SÁCH SINH VIÊN", font_size=12, text_color=Theme.Color.TEXT).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.widget_list_attendance_table = ctk.CTkFrame(self.widget_list_attendance, fg_color="transparent")
        self.widget_list_attendance_table.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        self.table = CustomTable(master=self.widget_list_attendance_table, columns=["MSSV", "Họ Tên", "Ngày sinh", "Giới tính", "Trạng thái", "Thời gian", "Ghi Chú", "Lớp"], column_widths=[70, 220, 110, 80, 180, 180, 200, 110], data=[])
        self.table.pack(expand=True, fill="both")

        self.grid_rowconfigure(1, weight=0); self.grid_rowconfigure(2, weight=1); self.grid_columnconfigure(1, weight=1)
        
        self.populate_comboboxes()
        self.widget_menu_devices_cbx_camera.set("⏳ Đang quét camera...")
        self.widget_menu_devices_cbx_camera.configure(state="disabled")
        self.btn_attendance.configure(state="disabled")
        threading.Thread(target=self.thread_load_cameras, daemon=True).start()

    def thread_load_cameras(self):
        """Hàm chạy ngầm để quét camera"""
        # Đây là tác vụ nặng, chạy ở luồng phụ
        cameras = CameraManager.list_available_cameras()
        
        # Load xong thì quay về luồng chính để cập nhật UI
        self.after(0, self.update_camera_ui, cameras)
        
    def update_camera_ui(self, cameras):
        """Cập nhật giao diện sau khi tìm thấy camera"""
        self.available_cameras = cameras
        
        if not self.available_cameras:
            ToastNotification(self, "Không tìm thấy camera nào.", duration=5000)
            self.widget_menu_devices_cbx_camera.set("Không có camera")
            self.widget_menu_devices_cbx_camera.configure(state="disabled")
            self.btn_attendance.configure(state="disabled") 
        else:
            # Có camera -> Nạp vào list
            self.camera_ids = [cam[0] for cam in self.available_cameras]
            self.camera_names = [cam[1] for cam in self.available_cameras]
            
            # Kiểm tra config cũ
            saved_camera_id = self.AppConfig.camera_config.selected_camera_id
            
            # Enable lại các nút
            self.widget_menu_devices_cbx_camera.configure(values=self.camera_names, state="readonly")
            self.btn_attendance.configure(state="normal") # Cho phép điểm danh
            
            if saved_camera_id in self.camera_ids:
                idx = self.camera_ids.index(saved_camera_id)
                self.widget_menu_devices_cbx_camera.set(self.camera_names[idx])
            else:
                self.widget_menu_devices_cbx_camera.set(self.camera_names[0])
                # Tự động chọn cái đầu tiên nếu cái cũ không thấy
                self.AppConfig.camera_config.selected_camera_id = self.camera_ids[0]
                save_config(self.AppConfig)
                
            ToastNotification(self, "Đã kết nối Camera!", duration=2000)

    def show_searchStudent(self):
        LecturerAttendance_SearchStudent.show_window(parent=self, username=self.username)
        
    def show_tranning_face(self):
        loading = LoadingDialog(self, "Đang khởi tạo...", mode="indeterminate")
        self.after(100, self._load_tranning_face, loading)

    def _load_tranning_face(self, loading):
        from core.app_face_recognition.controller import MainController
        try:
            if not self.controller:
                self.controller = MainController(
                    model_path="models",
                    sounds_path="resources/sound",
                    liveness_model_path="models/AntiSpoofing_bin_1.5_128.onnx",
                    app_config=self.AppConfig,
                )
            loading.stop()
            WidgetTranningFace.show_window(
                parent=self,
                username=self.username,
                controller=self.controller,
                config=self.AppConfig
            )
        except Exception as e:
            loading.stop()
            ToastNotification(self, f"Lỗi khởi tạo mô hình: {e}", duration=4000)

    def get_name_and_id_camera_setting(self):
        return CameraManager.list_available_cameras()

    def save_camera_setting(self):
        selected_name = self.widget_menu_devices_cbx_camera.get()
        for id, name in self.available_cameras:
            if name == selected_name:
                self.AppConfig.camera_config.selected_camera_id = id
                save_config(self.AppConfig)
                ToastNotification(self, f"Đã lưu camera: {name}", duration=2000)
                break
        
    def test_camera(self):
        loading = LoadingDialog(self, "Đang kiểm tra camera...")
        def run_test():
            saved_camera_id = self.AppConfig.camera_config.selected_camera_id
            camtest = CameraManager(camera_id=saved_camera_id)
            try:
                camtest.open_camera()
                self.after(0, lambda: loading.update_progress(0.3))
                if not camtest.is_opened:
                    self.after(200, lambda: ToastNotification(self, "Lỗi: Không thể kết nối đến camera.", duration=4000))
                    return
                ok = True
                for i in range(5):
                    frame = camtest.get_frame()
                    if frame is None or frame.size == 0:
                        ok = False
                        break
                    tm.sleep(0.1)
                self.after(0, lambda: loading.update_progress(0.8))
                if ok:
                    self.after(200, lambda: ToastNotification(self, "Camera hoạt động tốt!", duration=2000))
                else:
                    self.after(200, lambda: ToastNotification(self, "Lỗi: Không nhận được hình ảnh từ camera.", duration=4000))
            finally:
                camtest.release_camera()
                self.after(600, loading.destroy)
        threading.Thread(target=run_test, daemon=True).start()

    def check_camera(self):
        if not self.available_cameras:
            self.widget_menu_devices_cbx_camera.set("Camera không khả dụng")
            self.widget_menu_devices_cbx_camera.configure(state="disabled") 
            return
        self.widget_menu_devices_cbx_camera.configure(values=self.camera_names, state="readonly")
        selected_id = self.AppConfig.camera_config.selected_camera_id
        if selected_id in self.camera_ids:
            self.widget_menu_devices_cbx_camera.set(self.camera_names[self.camera_ids.index(selected_id)])
        else:
            self.widget_menu_devices_cbx_camera.set(self.camera_names[0])

    def on_class_selected(self, selected_class):
        self.widget_attendance_options_left_cbxSubject.configure(state="disabled")
        self.widget_attendance_options_left_cbxDate.configure(state="disabled")
        self.widget_attendance_options_left_cbxSession.configure(state="disabled")
        self.widget_attendance_options_left_cbxSubject.set("Đang tải...")
        self.widget_attendance_options_left_cbxDate.set("Đang tải...")
        self.widget_attendance_options_left_cbxSession.set("Đang tải...")
        thread = threading.Thread(target=self._load_data_for_selection, args=(selected_class,))
        thread.daemon = True 
        thread.start()

    def _load_data_for_selection(self, selected_class):
        subjects = Db.get_subjects_by_class(self.username, selected_class)
        dates, sessions = [], []
        default_subject, default_date, default_session = "Không có", "Không có", "Không có"
        if subjects:
            default_subject = subjects[0]
            dates = Db.get_dates_of_subject(self.username, default_subject)
            if dates:
                default_date = dates[0]
                sessions = Db.get_sessions_of_date(self.username, default_subject, default_date)
                if sessions:
                    default_session = sessions[0]
        self.after(0, self._update_comboboxes_from_thread, subjects, default_subject, dates, default_date, sessions, default_session)

    def _update_comboboxes_from_thread(self, subjects, default_subject, dates, default_date, sessions, default_session):
        if subjects:
            self.widget_attendance_options_left_cbxSubject.configure(values=subjects, state="readonly")
            self.widget_attendance_options_left_cbxSubject.set(default_subject)
        else:
            self.widget_attendance_options_left_cbxSubject.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxSubject.set("Không có")
        if dates:
            self.widget_attendance_options_left_cbxDate.configure(values=dates, state="readonly")
            self.widget_attendance_options_left_cbxDate.set(default_date)
        else:
            self.widget_attendance_options_left_cbxDate.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxDate.set("Không có")
        if sessions:
            self.widget_attendance_options_left_cbxSession.configure(values=sessions, state="readonly")
            self.widget_attendance_options_left_cbxSession.set(default_session)
        else:
            self.widget_attendance_options_left_cbxSession.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxSession.set("Không có")
        self.show_attendance_list()

    def on_subject_selected(self, selected_subject):
        if not selected_subject or "Đang tải" in selected_subject or selected_subject == "Không có": return
        self.widget_attendance_options_left_cbxDate.configure(state="disabled")
        self.widget_attendance_options_left_cbxDate.set("Đang tải...")
        self.widget_attendance_options_left_cbxSession.configure(state="disabled")
        self.widget_attendance_options_left_cbxSession.set("Đang tải...")
        thread = threading.Thread(target=self._load_data_for_subject, args=(selected_subject,))
        thread.daemon = True
        thread.start()

    def _load_data_for_subject(self, selected_subject):
        dates = Db.get_dates_of_subject(self.username, selected_subject)
        sessions = []
        default_date, default_session = "Không có", "Không có"
        if dates:
            default_date = dates[0]
            sessions = Db.get_sessions_of_date(self.username, selected_subject, default_date)
            if sessions: default_session = sessions[0]
        self.after(0, self._update_date_session_from_thread, dates, default_date, sessions, default_session)

    def _update_date_session_from_thread(self, dates, default_date, sessions, default_session):
        if dates:
            self.widget_attendance_options_left_cbxDate.configure(values=dates, state="readonly")
            self.widget_attendance_options_left_cbxDate.set(default_date)
        else:
            self.widget_attendance_options_left_cbxDate.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxDate.set("Không có")
        if sessions:
            self.widget_attendance_options_left_cbxSession.configure(values=sessions, state="readonly")
            self.widget_attendance_options_left_cbxSession.set(default_session)
        else:
            self.widget_attendance_options_left_cbxSession.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxSession.set("Không có")
        self.show_attendance_list()

    def on_date_selected(self, selected_date):
        if not selected_date or "Đang tải" in selected_date or selected_date == "Không có": return
        self.widget_attendance_options_left_cbxSession.configure(state="disabled")
        self.widget_attendance_options_left_cbxSession.set("Đang tải...")
        thread = threading.Thread(target=self._load_data_for_date, args=(selected_date,))
        thread.daemon = True
        thread.start()

    def _load_data_for_date(self, selected_date):
        subject = self.widget_attendance_options_left_cbxSubject.get()
        sessions = Db.get_sessions_of_date(self.username, subject, selected_date)
        default_session = sessions[0] if sessions else "Không có"
        self.after(0, self._update_session_from_thread, sessions, default_session)

    def _update_session_from_thread(self, sessions, default_session):
        if sessions:
            self.widget_attendance_options_left_cbxSession.configure(values=sessions, state="readonly")
            self.widget_attendance_options_left_cbxSession.set(default_session)
        else:
            self.widget_attendance_options_left_cbxSession.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxSession.set("Không có")
        self.show_attendance_list()

    def populate_comboboxes(self):
        self.all_classes = Db.get_classes_of_lecturer(self.username)
        if self.all_classes:
            self.widget_attendance_options_left_cbxClass.configure(values=self.all_classes, state="readonly")
            default_class = self.all_classes[0]
            self.widget_attendance_options_left_cbxClass.set(default_class)
            self.on_class_selected(default_class)
        else:
            for cbx in [self.widget_attendance_options_left_cbxClass, self.widget_attendance_options_left_cbxSubject, self.widget_attendance_options_left_cbxDate, self.widget_attendance_options_left_cbxSession]:
                cbx.configure(values=["Không có"], state="disabled")
                cbx.set("Không có")
            ToastNotification(self, "Thông báo: Giảng viên chưa được phân công lớp học phần.", duration=4000)
            self.show_attendance_list()

    def show_attendance_list(self):
        class_name = self.widget_attendance_options_left_cbxClass.get()
        subject_name = self.widget_attendance_options_left_cbxSubject.get()
        date = self.widget_attendance_options_left_cbxDate.get()
        session = self.widget_attendance_options_left_cbxSession.get()
        if not all([class_name, subject_name, date, session]) or "Không có" in [class_name, subject_name, date, session]:
            data = [[None]*9]
        else:
            data = Db.get_attendance_list_of_class(class_name, subject_name, date, session)
            if not data: data = [[None]*9]
        self.table.update_data(data)
        
    def attendance_student(self):
        def run_attendance():
            class_name = self.widget_attendance_options_left_cbxClass.get()
            subject_name = self.widget_attendance_options_left_cbxSubject.get()
            date_str = self.widget_attendance_options_left_cbxDate.get()
            session_name = self.widget_attendance_options_left_cbxSession.get()
            if "Đang tải" in class_name or "Không có" in class_name or not all([class_name, subject_name, date_str, session_name]):
                self.after(0, lambda: ToastNotification(self, "Vui lòng chọn đầy đủ thông tin điểm danh.", duration=3000))
                return
            ma_buoi_hoc = Db.get_ma_buoi_hoc(class_name, subject_name, date_str, session_name)
            if ma_buoi_hoc is None:
                self.after(0, lambda: ToastNotification(self, "Lỗi: Không tìm thấy thông tin buổi học.", duration=3000))
                return
            if hasattr(self, 'CheckConfigAttendace_frame') and self.CheckConfigAttendace_frame.winfo_exists():
                return
            self.CheckConfigAttendace_frame = CheckConfigAttendance(
                master=self,
                appconfig=self.AppConfig,
                class_name=class_name,
                date_str=date_str,
                session=ma_buoi_hoc,
                mode_attendace=self.attendance_mode_var.get(),
                username=self.username,
            )
            self.CheckConfigAttendace_frame.grid(row=0, column=0, rowspan=3, columnspan=2, sticky="nsew")
        threading.Thread(target=run_attendance, daemon=True).start()