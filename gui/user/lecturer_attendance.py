# FILE NAME: 

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



class LecturerAttendance(ctk.CTkFrame):
    def __init__(self, master=None, username=None, config=None,**kwargs):
        super().__init__(master, **kwargs)
        self.username = username
        self.parent = master
        self._border_width = 1
        self._border_color = "white"
        self._fg_color = "white"
        self.AppConfig = config
        self.available_cameras = []
        self.controller = None

        # Biến màu sắc
        self.widget_color = "#2DFCB0"
        self.txt_color_title = "#0412A9"

        # Khởi tạo các đối tượng xử lý
        self.attendance_processor = None
        self.camera_window = None # Biến để lưu trữ cửa sổ camera Toplevel


        # Tiêu đề
        self.title_widget = ctk.CTkLabel(
            self,
            text="Dashboard > ĐIỂM DANH SINH VIÊN",
            font=("Bahnschrift", 20, "bold"),
            text_color="#05243F"
        )
        self.title_widget.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nw")

        # === MENU TRÁI ===
        self.widget_menu = ctk.CTkFrame(self, fg_color="transparent", width=250)
        self.widget_menu.grid(row=1, column=0, rowspan=2, pady=0, padx=0, sticky="nsw")
        self.widget_menu.grid_rowconfigure((0, 1, 2), weight=1)
        self.widget_menu.grid_columnconfigure(0, weight=1)
        self.widget_menu.grid_propagate(False)

        # --- Menu nâng cao ---
        self.widget_menu_advanced = ctk.CTkFrame(self.widget_menu, fg_color=self.widget_color)
        self.widget_menu_advanced.grid(row=0, column=0, padx=0, pady=5, sticky="nsew")
        self.widget_menu_advanced.grid_propagate(False)
        self.widget_menu_advanced.grid_columnconfigure(0, weight=1)

        self.title_wm_advanced = LabelCustom(self.widget_menu_advanced, "CHỨC NĂNG NÂNG CAO", font_size=12, font_weight="bold", text_color=self.txt_color_title)
        self.title_wm_advanced.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="nw")

        # self.widget_menu_advanced_btn_historyAttendance = ButtonTheme(self.widget_menu_advanced, "Xem lịch sử điểm danh")
        # self.widget_menu_advanced_btn_historyAttendance.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        # Nút chức năng sẽ được phát triển trong thời gian tới!

        self.widget_menu_advanced_btn_searchStudent = ButtonTheme(self.widget_menu_advanced, "Tra cứu sinh viên", command=self.show_searchStudent)
        self.widget_menu_advanced_btn_searchStudent.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")


        # --- Menu sinh trắc học ---
        self.widget_menu_face = ctk.CTkFrame(self.widget_menu, fg_color=self.widget_color)
        self.widget_menu_face.grid(row=1, column=0, padx=0, pady=(0,5), sticky="nsew")
        self.widget_menu_face.grid_columnconfigure(0, weight=1)
        self.widget_menu_face.grid_propagate(False)

        self.title_wm_face = LabelCustom(self.widget_menu_face, "CẬP NHẬT SINH TRẮC HỌC", font_size=12, font_weight="bold", text_color=self.txt_color_title)
        self.title_wm_face.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="nw")

        self.widget_menu_face_trainFace = ButtonTheme(self.widget_menu_face, "Đào tạo dữ liệu khuôn mặt", command=self.show_tranning_face)
        self.widget_menu_face_trainFace.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        # self.widget_menu_face_seenDataFace = ButtonTheme(self.widget_menu_face, "Xem dữ liệu khuôn mặt")
        # self.widget_menu_face_seenDataFace.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        # Nút chức năng phát sẽ được phát triển trong thời gian tới!

        # --- Menu thiết bị ---
        self.widget_menu_devices = ctk.CTkFrame(self.widget_menu, fg_color=self.widget_color)
        self.widget_menu_devices.grid(row=2, column=0, padx=0, pady=(0,5), sticky="nsew")
        self.widget_menu_devices.grid_columnconfigure(0, weight=1)
        self.widget_menu_devices.grid_propagate(False)

        self.title_wm_devives = LabelCustom(self.widget_menu_devices, "THIẾT BỊ", font_size=12, font_weight="bold", text_color=self.txt_color_title)
        self.title_wm_devives.grid(row=0, column=0, padx=10, pady=0, sticky="nw")

        self.widget_menu_devices_cbx_camera = ComboboxTheme(self.widget_menu_devices, values="Đang kiểm tra camera...", state="readonly")
        self.widget_menu_devices_cbx_camera.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.widget_menu_devices_cbx_camera_tooltip = Tooltip(self.widget_menu_devices_cbx_camera, text="Chọn camera và nhấn 'Lưu Camera' để lưu cài đặt camera.")
        self.check_camera()  # Kiểm tra và cập nhật danh sách camera

        # THAY ĐỔI: Gán command cho nút Test Camera
        self.widget_menu_devices_testCamera = ButtonTheme(self.widget_menu_devices, "Lưu Camera", fg_color="#0099FF", hover_color="#003462", command=self.save_camera_setting)
        self.widget_menu_devices_testCamera.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        self.widget_menu_devices_testCamera = ButtonTheme(self.widget_menu_devices, "Test Camera", fg_color="#0099FF", hover_color="#003462", command=self.test_camera)
        self.widget_menu_devices_testCamera.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        self.widget_menu_devices_testCamera_note = LabelCustom(self.widget_menu_devices, text="(*) Vui lòng LƯU Camera trước khi Test!", font_size=12)
        self.widget_menu_devices_testCamera_note.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # === KHUNG PHẢI - THÔNG TIN ĐIỂM DANH ===
        self.widget_attendance_options = ctk.CTkFrame(self, fg_color="transparent", height=120)
        self.widget_attendance_options.grid(row=1, column=1, pady=0, padx=0, sticky="nsew")
        self.widget_attendance_options.grid_columnconfigure((0,1), weight=1)
        self.widget_attendance_options.grid_rowconfigure(0, weight=1)
        self.widget_attendance_options.grid_propagate(False)

        # --- Menu chọn thông tin ----
        self.widget_attendance_options_left = ctk.CTkFrame(
            self.widget_attendance_options,
            fg_color=self.widget_color,
            width=500,
            height=140  # tăng chiều cao nhẹ
        )
        self.widget_attendance_options_left.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.widget_attendance_options_left.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.widget_attendance_options_left.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.widget_attendance_options_left.grid_propagate(False)

        # Tiêu đề
        self.widget_attendance_options_left_title = LabelCustom(
            self.widget_attendance_options_left,
            "THÔNG TIN ĐIỂM DANH",
            font_size=12,
            font_weight="bold",
            text_color=self.txt_color_title
        )
        self.widget_attendance_options_left_title.grid(row=0, column=0, columnspan=4, padx=10, pady=0, sticky="nw")

        # Tạo combobox LỚP
        self.widget_attendance_options_left_cbxClass = ComboboxTheme(
            self.widget_attendance_options_left, values=["Đang tải..."], state="readonly"
        )
        self.widget_attendance_options_left_cbxClass.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.widget_attendance_options_left_cbxClass.configure(command=self.on_class_selected)

        # Tạo combobox HỌC PHẦN
        self.widget_attendance_options_left_cbxSubject = ComboboxTheme(
            self.widget_attendance_options_left, values=["Đang tải..."], state="disabled"
        )
        self.widget_attendance_options_left_cbxSubject.grid(row=1, column=1, padx=5, pady=(0, 10), sticky="ew")
        self.widget_attendance_options_left_cbxSubject.configure(command=self.on_subject_selected)

        # Tạo combobox NGÀY
        self.widget_attendance_options_left_cbxDate = ComboboxTheme(
            self.widget_attendance_options_left, values=["Đang tải..."], state="disabled"
        )
        self.widget_attendance_options_left_cbxDate.grid(row=2, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.widget_attendance_options_left_cbxDate.configure(command=self.on_date_selected)

        # Tạo combobox BUỔI
        self.widget_attendance_options_left_cbxSession = ComboboxTheme(
            self.widget_attendance_options_left, values=["Đang tải..."], state="disabled"
        )
        self.widget_attendance_options_left_cbxSession.grid(row=2, column=1, padx=5, pady=(0, 5), sticky="ew")


        # Label ghi chú
        self.widget_attendance_options_left_note = ctk.CTkLabel(
            self.widget_attendance_options_left,
            text="*Click vào nút trên để kiểm tra/Xem thông tin đã chọn",
            font=("Bahnschrift", 10),
            text_color="black",
            wraplength=200,
            justify="center"
        )
        self.widget_attendance_options_left_note.grid(row=2, column=2, columnspan=2, padx=5, pady=(0, 0), sticky="ew")

        # Nút Xem Danh sách
        self.widget_attendance_options_left_btnSeen = ButtonTheme(
            self.widget_attendance_options_left,
            text="Xem Danh sách",
            fg_color="#0099FF",
            hover_color="#003462",
            width=80,
            height=40, 
            command=self.show_attendance_list
        )
        self.widget_attendance_options_left_btnSeen.grid(row=1, column=2, columnspan=2, padx=30, pady=5, sticky="n")


        # --- Menu điểm danh ---
        self.widget_attendance_options_right = ctk.CTkFrame(self.widget_attendance_options, fg_color=self.widget_color, height=120)
        self.widget_attendance_options_right.grid(row=0, column=1, padx=(0,5), pady=5, sticky="nsew")
        self.widget_attendance_options_right.grid_columnconfigure((0,1), weight=1)
        self.widget_attendance_options_right.grid_propagate(False)

        self.widget_attendance_options_right_title = LabelCustom(self.widget_attendance_options_right, "ĐIỂM DANH", font_size=12, font_weight="bold", text_color=self.txt_color_title)
        self.widget_attendance_options_right_title.grid(row=0, column=0, columnspan=2, padx=10, pady=0, sticky="nw")

        self.attendance_mode_var = ctk.StringVar(value="single")
        self.radio_single = ctk.CTkRadioButton(self.widget_attendance_options_right, text="Điểm danh từng SV", variable=self.attendance_mode_var, value="single")
        self.radio_single.grid(row=1, column=0, padx=20, pady=(5, 2), sticky="w")

        self.radio_all = ctk.CTkRadioButton(self.widget_attendance_options_right, text="Điểm danh cả lớp", variable=self.attendance_mode_var, value="all")
        self.radio_all.grid(row=2, column=0, padx=20, pady=(0, 5), sticky="w")

        # THAY ĐỔI: Gán command cho nút Điểm danh
        self.btn_attendance = ButtonTheme(self.widget_attendance_options_right, text="Điểm danh", fg_color="#0099FF", hover_color="#003462", width=120, command=self.attendance_student)
        self.btn_attendance.grid(row=1, column=1, rowspan=3, padx=10, pady=5, sticky="e")

        # === KHUNG PHẢI - DANH SÁCH SINH VIÊN ===
        self.widget_list_attendance = ctk.CTkFrame(self, fg_color="white", border_color=self.widget_color, border_width=2)
        self.widget_list_attendance.grid(row=2, column=1, pady=(0,5), padx=5, sticky="nsew")
        self.widget_list_attendance.grid_columnconfigure((0,1), weight=1)
        self.widget_list_attendance.grid_rowconfigure(1, weight=1)

        self.widget_list_attendance_title = LabelCustom(self.widget_list_attendance, "DANH SÁCH SINH VIÊN ĐIỂM DANH", font_size=12)
        self.widget_list_attendance_title.grid(row=0, column=0, padx=10, pady=3, sticky="nw")
        
        self.widget_list_attendance_table = ctk.CTkFrame(self.widget_list_attendance, fg_color="transparent")
        self.widget_list_attendance_table.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nwse")
        self.widget_list_attendance_table.grid_rowconfigure(0, weight=1)
        self.widget_list_attendance_table.grid_columnconfigure(0, weight=1)

        
        self.table = CustomTable(master=self.widget_list_attendance_table, columns=[
                                "MSSV",
                                "Họ Tên Sinh Viên", 
                                "Ngày sinh", 
                                "Giới tính", 
                                "Trạng thái điểm danh",
                                "Thời gian điểm danh",
                                "Ghi Chú", 
                                "Sinh viên lớp"
                                ],
                                 column_widths=[70, 220, 110, 80, 180, 180, 200, 110],
                                 data=[[None,None, None, None, None, None, None, None]],
                                 scroll=True,
                                 highlight_columns=[4, 5],
                                 highlight_color="#BEF2D2"
                                 )
        self.table.grid(padx=0, pady=0, sticky="nsew")
        

        # === THIẾT LẬP LƯỚI TỔNG ===
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # +++ HÀM LOAD DATA +++
        # Load combobox
        self.populate_comboboxes()
        
        
        # +++ LOAD CAMERA +++
        self.available_cameras = self.get_name_and_id_camera_setting()  # Lấy danh sách camera có sẵn
        
        # --- CẢI TIẾN: Kiểm tra camera khi khởi tạo ---
        if not self.available_cameras:
            ToastNotification(self, "Không tìm thấy camera nào. Vui lòng kiểm tra kết nối camera.", duration=5000)
            self.widget_menu_devices_cbx_camera.set("Không có camera")
            self.widget_menu_devices_cbx_camera.configure(state="disabled")
            self.widget_menu_devices_testCamera.configure(state="disabled")
            self.btn_attendance.configure(state="disabled") # Vô hiệu hóa nút điểm danh
            return
        
        # Tách riêng ID và tên camera để dễ dùng
        self.camera_ids = [cam[0] for cam in self.available_cameras]   # [0, 1, 2]
        self.camera_names = [cam[1] for cam in self.available_cameras] # ["USB Cam", "Built-in Cam"]

        # Kiểm tra xem camera đã lưu có còn tồn tại không
        saved_camera_id = self.AppConfig.camera_config.selected_camera_id
        if saved_camera_id not in self.camera_ids:
            # Nếu không, chọn camera đầu tiên trong danh sách làm mặc định và lưu lại
            ToastNotification(self, "Camera đã lưu không còn tồn tại. Đã chọn camera mặc định.", duration=3000)
            self.AppConfig.camera_config.selected_camera_id = self.camera_ids[0]
            save_config(self.AppConfig)
        self.check_camera()


    # === CÁC HÀM CHỨC NĂNG NÚT ===
    def show_searchStudent(self):
        LecturerAttendance_SearchStudent.show_window(parent=self, username=self.username)
        
        
    def show_tranning_face(self):
        # Hiển thị dialog loading
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

            # Khi controller đã sẵn sàng -> tắt dialog
            loading.stop()

            # Mở cửa sổ training
            WidgetTranningFace.show_window(
                parent=self,
                username=self.username,
                controller=self.controller,
                config=self.AppConfig
            )
        except Exception as e:
            loading.stop()
            from tkinter import messagebox
            messagebox.showerror("Lỗi", f"Không thể khởi tạo mô hình.\n{e}")

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
            print(f"Đang kiểm tra camera với ID: {self.AppConfig.camera_config.selected_camera_id}")
            camtest = CameraManager(camera_id=self.AppConfig.camera_config.selected_camera_id)
            # --- CẢI TIẾN: Thêm kiểm tra an toàn trước khi test camera ---
            # 1. Kiểm tra xem có camera nào không
            if not self.available_cameras:
                self.after(100, lambda: messagebox.showerror("Lỗi", "Không tìm thấy camera nào trên hệ thống."))
                self.after(200, loading.destroy)
                return

            # 2. Kiểm tra xem ID camera đã lưu có hợp lệ không
            saved_camera_id = self.AppConfig.camera_config.selected_camera_id
            if saved_camera_id not in self.camera_ids:
                self.after(100, lambda: messagebox.showerror("Lỗi", f"ID camera đã lưu ({saved_camera_id}) không hợp lệ.\nVui lòng chọn lại camera và nhấn 'Lưu Camera'."))
                self.after(200, loading.destroy)
                return

            print(f"Đang kiểm tra camera với ID: {saved_camera_id}")
            camtest = CameraManager(camera_id=saved_camera_id)

            try:
                camtest.open_camera()
                self.after(0, lambda: loading.update_progress(0.3))
                self.after(0, lambda: loading.update_progress(0.3)) # Cập nhật tiến trình

                if not camtest.is_opened:
                    self.after(200, lambda: messagebox.showerror("Lỗi", "Không thể kết nối đến camera."))
                    return

                ok = True
                for i in range(5):
                    frame = camtest.get_frame()
                    if frame is None or frame.size == 0:
                        ok = False
                        break
                    tm.sleep(0.1)  # đợi chút giữa các lần đọc

                self.after(0, lambda: loading.update_progress(0.8))

                if ok:
                    self.after(0, lambda: loading.update_progress(1.0))
                    self.after(200, lambda: ToastNotification(self, "Camera đã được kết nối thành công!", duration=2000))
                else:
                    self.after(0, lambda: loading.update_progress(1.0))
                    self.after(200, lambda: messagebox.showerror("Lỗi", "Không thể đọc khung hình từ camera. Vui lòng kiểm tra lại."))

            finally:
                camtest.release_camera()
                self.after(600, loading.destroy)

        threading.Thread(target=run_test, daemon=True).start()

        
    # === CÁC HÀM CHỨC NĂNG (ĐÃ CẢI TIẾN) ===
    def check_camera(self):
        if not self.available_cameras:
            self.widget_menu_devices_cbx_camera.set("Thiết bị camera không khả dụng")
            self.widget_menu_devices_cbx_camera.configure(state="disabled") # Vô hiệu hóa nếu không có camera
            return
        
        self.widget_menu_devices_cbx_camera.configure(values=self.camera_names, state="readonly") # Đảm bảo có thể chọn
        selected_id = self.AppConfig.camera_config.selected_camera_id
        if selected_id in self.camera_ids:
            self.widget_menu_devices_cbx_camera.set(self.camera_names[self.camera_ids.index(selected_id)])
        else:
            self.widget_menu_devices_cbx_camera.set(self.camera_names[0])


    def on_class_selected(self, selected_class):
        """
        Khi một lớp được chọn, bắt đầu một luồng mới để tải dữ liệu
        mà không làm treo giao diện.
        """
        # (Tùy chọn) Vô hiệu hóa các combobox để người dùng không thao tác khi đang tải
        self.widget_attendance_options_left_cbxSubject.configure(state="disabled")
        self.widget_attendance_options_left_cbxDate.configure(state="disabled")
        self.widget_attendance_options_left_cbxSession.configure(state="disabled")
        # Hiển thị trạng thái đang tải, ví dụ:
        self.widget_attendance_options_left_cbxSubject.set("Đang tải...")
        self.widget_attendance_options_left_cbxDate.set("Đang tải...")
        self.widget_attendance_options_left_cbxSession.set("Đang tải...")


        # Tạo và bắt đầu luồng mới
        thread = threading.Thread(target=self._load_data_for_selection, args=(selected_class,))
        thread.daemon = True  # Đảm bảo luồng sẽ tắt khi chương trình chính tắt
        thread.start()

    def _load_data_for_selection(self, selected_class):
        """
        Hàm này chạy trong luồng nền để lấy dữ liệu từ DB.
        """
        # 1. Lấy danh sách môn học
        subjects = Db.get_subjects_by_class(self.username, selected_class)
        dates = []
        sessions = []
        
        default_subject = "Không có"
        default_date = "Không có"
        default_session = "Không có"

        if subjects:
            default_subject = subjects[0]
            # 2. Lấy danh sách ngày
            dates = Db.get_dates_of_subject(self.username, default_subject)
            if dates:
                default_date = dates[0]
                # 3. Lấy danh sách buổi
                sessions = Db.get_sessions_of_date(self.username, default_subject, default_date)
                if sessions:
                    default_session = sessions[0]

        # Dữ liệu đã sẵn sàng, yêu cầu luồng chính cập nhật giao diện
        self.after(0, self._update_comboboxes_from_thread, 
                  subjects, default_subject, 
                  dates, default_date, 
                  sessions, default_session)

    def _update_comboboxes_from_thread(self, subjects, default_subject, dates, default_date, sessions, default_session):
        """
        Hàm này được gọi bởi luồng chính để cập nhật an toàn các widget.
        """
        # Cập nhật combobox Môn học
        if subjects:
            self.widget_attendance_options_left_cbxSubject.configure(values=subjects, state="readonly")
            self.widget_attendance_options_left_cbxSubject.set(default_subject)
        else:
            self.widget_attendance_options_left_cbxSubject.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxSubject.set("Không có")

        # Cập nhật combobox Ngày
        if dates:
            self.widget_attendance_options_left_cbxDate.configure(values=dates, state="readonly")
            self.widget_attendance_options_left_cbxDate.set(default_date)
        else:
            self.widget_attendance_options_left_cbxDate.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxDate.set("Không có")
        
        # Cập nhật combobox Buổi
        if sessions:
            self.widget_attendance_options_left_cbxSession.configure(values=sessions, state="readonly")
            self.widget_attendance_options_left_cbxSession.set(default_session)
        else:
            self.widget_attendance_options_left_cbxSession.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxSession.set("Không có")


        # Cuối cùng, cập nhật bảng điểm danh
        self.show_attendance_list()


    def on_subject_selected(self, selected_subject):
        """(Luồng chính) Bắt đầu luồng tải dữ liệu cho Ngày và Buổi."""
        if not selected_subject or "Đang tải" in selected_subject or selected_subject == "Không có":
            return

        # Vô hiệu hóa các widget phụ thuộc
        self.widget_attendance_options_left_cbxDate.configure(state="disabled")
        self.widget_attendance_options_left_cbxDate.set("Đang tải...")
        self.widget_attendance_options_left_cbxSession.configure(state="disabled")
        self.widget_attendance_options_left_cbxSession.set("Đang tải...")

        # Bắt đầu luồng mới
        thread = threading.Thread(target=self._load_data_for_subject, args=(selected_subject,))
        thread.daemon = True
        thread.start()

    def _load_data_for_subject(self, selected_subject):
        """(Luồng nền) Lấy danh sách Ngày và Buổi từ DB."""
        dates = Db.get_dates_of_subject(self.username, selected_subject)
        sessions = []
        default_date = "Không có"
        default_session = "Không có"

        if dates:
            default_date = dates[0]
            sessions = Db.get_sessions_of_date(self.username, selected_subject, default_date)
            if sessions:
                default_session = sessions[0]

        # Yêu cầu luồng chính cập nhật giao diện
        self.after(0, self._update_date_session_from_thread, 
                  dates, default_date, 
                  sessions, default_session)

    def _update_date_session_from_thread(self, dates, default_date, sessions, default_session):
        """(Luồng chính) Cập nhật combobox Ngày và Buổi."""
        # Cập nhật combobox Ngày
        if dates:
            self.widget_attendance_options_left_cbxDate.configure(values=dates, state="readonly")
            self.widget_attendance_options_left_cbxDate.set(default_date)
        else:
            self.widget_attendance_options_left_cbxDate.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxDate.set("Không có")

        # Cập nhật combobox Buổi
        if sessions:
            self.widget_attendance_options_left_cbxSession.configure(values=sessions, state="readonly")
            self.widget_attendance_options_left_cbxSession.set(default_session)
        else:
            self.widget_attendance_options_left_cbxSession.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxSession.set("Không có")

        # Cập nhật bảng
        self.show_attendance_list()

    def on_date_selected(self, selected_date):
        """(Luồng chính) Bắt đầu luồng tải dữ liệu cho Buổi học."""
        if not selected_date or "Đang tải" in selected_date or selected_date == "Không có":
            return

        # Vô hiệu hóa widget phụ thuộc
        self.widget_attendance_options_left_cbxSession.configure(state="disabled")
        self.widget_attendance_options_left_cbxSession.set("Đang tải...")

        # Bắt đầu luồng mới
        thread = threading.Thread(target=self._load_data_for_date, args=(selected_date,))
        thread.daemon = True
        thread.start()

    def _load_data_for_date(self, selected_date):
        """(Luồng nền) Lấy danh sách Buổi từ DB."""
        # Phải lấy môn học hiện tại từ combobox
        subject = self.widget_attendance_options_left_cbxSubject.get()
        
        sessions = Db.get_sessions_of_date(self.username, subject, selected_date)
        default_session = sessions[0] if sessions else "Không có"

        # Yêu cầu luồng chính cập nhật giao diện
        self.after(0, self._update_session_from_thread, sessions, default_session)

    def _update_session_from_thread(self, sessions, default_session):
        """(Luồng chính) Cập nhật combobox Buổi."""
        if sessions:
            self.widget_attendance_options_left_cbxSession.configure(values=sessions, state="readonly")
            self.widget_attendance_options_left_cbxSession.set(default_session)
        else:
            self.widget_attendance_options_left_cbxSession.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxSession.set("Không có")
        
        # Cập nhật bảng
        self.show_attendance_list()

    def populate_comboboxes(self):
        """
        Hàm khởi tạo, load dữ liệu lần đầu cho tất cả các combobox.
        Logic được rút gọn vì các hàm on_..._selected đã xử lý chuỗi.
        """
        self.all_classes = Db.get_classes_of_lecturer(self.username)
        if self.all_classes:
            self.widget_attendance_options_left_cbxClass.configure(values=self.all_classes, state="readonly")
            default_class = self.all_classes[0]
            self.widget_attendance_options_left_cbxClass.set(default_class)
            self.on_class_selected(default_class)
        else:
            self.widget_attendance_options_left_cbxClass.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxClass.set("Không có")
            # Vô hiệu hóa các combobox còn lại nếu không có lớp nào
            self.widget_attendance_options_left_cbxSubject.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxSubject.set("Không có")
            self.widget_attendance_options_left_cbxDate.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxDate.set("Không có")
            self.widget_attendance_options_left_cbxSession.configure(values=["Không có"], state="disabled")
            self.widget_attendance_options_left_cbxSession.set("Không có")
            messagebox.showinfo("Thông báo", "Giảng viên này chưa được phân công lớp học phần nào.")
            self.show_attendance_list() # Cập nhật bảng với dữ liệu trống

    def show_attendance_list(self):
        class_name = self.widget_attendance_options_left_cbxClass.get()
        subject_name = self.widget_attendance_options_left_cbxSubject.get()
        date = self.widget_attendance_options_left_cbxDate.get()
        session = self.widget_attendance_options_left_cbxSession.get()
        
        # Kiểm tra nếu thiếu thông tin hoặc thông tin là "Không có" thì không load
        if not all([class_name, subject_name, date, session]) or \
           "Không có" in [class_name, subject_name, date, session]:
            data = [[None, None, None, None, None, None, None, None, None]]
        else:
            data = Db.get_attendance_list_of_class(class_name, subject_name, date, session)
            if not data: # Nếu không có dữ liệu trả về từ DB
                data = [[None, None, None, None, None, None, None, None, None]]


        self.table.update_data(data)
        
            
    def check_option_attendace(self):
        if self.attendance_mode_var.get() == "single":
            ToastNotification(self, "Đã chọn chế độ điểm danh cho từng sinh viên", duration=5000)
        else:
            ToastNotification(self, "Đã chọn chế độ điểm danh cả lớp", duration=5000)
        
        
    def attendance_student(self):
        def run_attendance():
            # --- BƯỚC 1: Lấy thông tin từ các combobox ---
            class_name = self.widget_attendance_options_left_cbxClass.get()
            subject_name = self.widget_attendance_options_left_cbxSubject.get()
            date_str = self.widget_attendance_options_left_cbxDate.get()
            session_name = self.widget_attendance_options_left_cbxSession.get()
            
        
            # --- BƯỚC 2: Kiểm tra thông tin có hợp lệ không ---
            if "Đang tải" in class_name or "Không có" in class_name or not all([class_name, subject_name, date_str, session_name]):
                messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn đầy đủ thông tin Lớp, Học phần, Ngày và Buổi học trước khi điểm danh.")
                return
            # --- BƯỚC 3: Gọi hàm mới để lấy Mã Buổi Học ---
            ma_buoi_hoc = Db.get_ma_buoi_hoc(class_name, subject_name, date_str, session_name)
            if ma_buoi_hoc is None:
                messagebox.showerror("Lỗi", f"Không tìm thấy thông tin buổi học tương ứng trong CSDL.\nVui lòng kiểm tra lại.")
                return
            
            def to_time(value):
                if isinstance(value, timedelta):
                    # chuyển timedelta -> time
                    total_seconds = int(value.total_seconds())
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    return time(hour=hours, minute=minutes, second=seconds)
                return value
                        
            thoi_gian = Db.get_time_of_buoihoc(ma_buoi_hoc)
            start, end, date, _ = thoi_gian
            start_time = to_time(start)
            end_time = to_time(end)   
            now_time = datetime.now().time()
            now_date = datetime.now().date()
            print(F"Thông tin kiểm tra {start_time} <= {now_time} <= {end_time} ")
            
            if not (start_time <= now_time <= end_time) or now_date != date:
                messagebox.showerror("Cảnh Báo Điểm Danh", "Bạn đang điểm danh KHÔNG ĐÚNG buổi hoặc tiết học hiện tại!\nVui lòng kiểm tra lại và thử lại sau.")
                return
            
            # In ra để kiểm tra (tùy chọn)
            print(f"Chuẩn bị điểm danh cho Mã Buổi Học: {ma_buoi_hoc}")
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
        
        
   