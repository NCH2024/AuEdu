from gui.base.utils import *
import customtkinter as ctk
import threading
from tkinter import messagebox
from core.app_face_recognition.widget_attendance_face import WidgetAttendanceFace
from core.app_face_recognition.controller import MainController


class CheckConfigAttendance(ctk.CTkFrame):
    def __init__(
        self,
        master,
        appconfig=None,
        class_name=None,
        date_str=None,
        session=None,
        mode_attendace=None,
        username=None,
    ):
        super().__init__(master)
        self.appconfig = appconfig
        self.class_name = class_name
        self.date_str = date_str
        self.session = session
        self.mode_attdenace = mode_attendace
        self.username = username
        self.controller = None
        self.widget_color = "#05243F"
        self.text_color = "#2DFCB0"
        self.text_color_w = "#FFFFFF"

        self.configure(fg_color=self.widget_color)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.setup_ui()
        self.start_loading_process()

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=self.widget_color)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        middle_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="#07355F",
            corner_radius=20,
            border_color=self.text_color,
            border_width=2,
        )
        middle_frame.grid(row=0, column=0, ipadx=40, ipady=30, padx=20, pady=20)
        middle_frame.columnconfigure((0, 1), weight=1)
        middle_frame.rowconfigure((0, 1, 2, 3), weight=1)

        title = LabelCustom(
            middle_frame,
            "LỰA CHỌN HÌNH THỨC ĐIỂM DANH",
            text_color=self.text_color,
            font_size=18,
        )
        title.grid(row=0, column=0, columnspan=2, padx=(10, 0), pady=(10, 0), sticky="nw")

        chedo = "Điểm danh tất cả" if self.mode_attdenace == "all" else "Điểm danh từng người"
        info_str = f"ĐANG THỰC HIỆN ĐIỂM DANH:\nLớp: {self.class_name}\nNgày: {self.date_str}\nChế độ: {chedo}"
        title_note = ctk.CTkLabel(
            middle_frame, text=info_str, text_color=self.text_color_w, justify="left"
        )
        title_note.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        check_frame = ctk.CTkFrame(middle_frame, fg_color="transparent")
        check_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        check_frame.columnconfigure(0, weight=1)

        self.options = ctk.StringVar(value="start")
        label_check = LabelCustom(check_frame, "Vui lòng chọn một hình thức sau:", text_color=self.text_color)
        label_check.pack(pady=(0, 10), anchor="w")

        btn_check_start = ctk.CTkRadioButton(
            check_frame,
            text="Điểm danh đầu buổi",
            text_color="white",
            font=("Arial", 18),
            value="start",
            variable=self.options,
        )
        btn_check_start.pack(pady=5, anchor="w", padx=20)

        btn_check_end = ctk.CTkRadioButton(
            check_frame,
            text="Điểm danh cuối buổi",
            text_color="white",
            font=("Arial", 18),
            value="end",
            variable=self.options,
        )
        btn_check_end.pack(pady=5, anchor="w", padx=20)

        btn_apply = ButtonTheme(middle_frame, "VÀO ĐIỂM DANH", command=self.attendance_student)
        btn_apply.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        btn_exit = ButtonTheme(middle_frame, "QUAY LẠI", command=self.exit_back)
        btn_exit.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        
    def start_loading_process(self):
        # Ẩn giao diện chính, mở dialog tải mô hình
        self.main_frame.grid_remove()
        self.loading_dialog = LoadingDialog(self.winfo_toplevel(), "Đang kiểm tra mô hình...", mode="determinate")

        # Chạy luồng riêng để tải model
        threading.Thread(target=self.load_models_and_controller, daemon=True).start()

    def load_models_and_controller(self):
        try:
            # Import ở đây để tránh lỗi import vòng
            from core.utils import get_base_path
            import os

            base_path = get_base_path()

            # Khởi tạo MainController 1 LẦN DUY NHẤT
            self.controller = MainController(
                model_path=os.path.join(base_path, "models"),
                sounds_path=os.path.join(base_path, "resources", "sound"),
                liveness_model_path=os.path.join(base_path, "models", "AntiSpoofing_bin_1.5_128.onnx"),
                app_config=self.appconfig,
                dialog=self.loading_dialog
            )

            # Controller đã tự load xong, giờ chỉ việc báo hoàn thành
            self.after_idle(self.on_loading_complete)

        except Exception as e:
            self.after_idle(self.on_loading_error, e)

    def update_loading_dialog(self, progress, message):
        try:
            if hasattr(self, "loading_dialog") and self.loading_dialog.winfo_exists():
                self.loading_dialog.update_progress(progress)
                self.loading_dialog.label.configure(text=message)
        except Exception:
            pass

    def on_loading_complete(self):
        if hasattr(self, "loading_dialog"):
            self.loading_dialog.stop()
        self.main_frame.grid()

    def on_loading_error(self, error):
        if hasattr(self, "loading_dialog"):
            self.loading_dialog.stop()
        messagebox.showerror("Lỗi", f"Không thể khởi tạo bộ nhận diện khuôn mặt.\nLỗi: {error}")
        self.destroy()

    def attendance_student(self):
        if not self.controller:
            messagebox.showwarning("Cảnh báo", "Bộ điều khiển chưa sẵn sàng, vui lòng đợi!")
            return

        if hasattr(self, 'attendance_frame') and self.attendance_frame.winfo_exists():
            return

        selected_option = self.options.get()
        self.controller.set_check_in_type(selected_option)

        self.attendance_frame = WidgetAttendanceFace(
            self,
            controller=self.controller,
            username=self.username,
            ma_buoi_hoc=self.session,
            config=self.appconfig,
            option_attendace=self.mode_attdenace,
            check_in_type=selected_option, 
        )

        print(f"đang điểm danh cho {self.session}, {self.class_name}, ở chế độ {self.mode_attdenace}")
        self.controller.start_attendance(self.session, self.class_name)
        self.attendance_frame.grid(row=0, column=0, sticky="nsew")

    def exit_back(self):
        try:
            if self.controller:
                self.controller.stop_attendance()
        except Exception:
            pass
        self.destroy()


