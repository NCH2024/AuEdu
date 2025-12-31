import customtkinter as ctk
from gui.base.utils import *
from tkinter import messagebox
from core.app_config import save_config
from core.theme_manager import Theme, AppFont # Import Theme

class LecturerAttendance_Setting(ctk.CTkFrame):
    def __init__(self, master=None, AppConfig=None, **kwargs):
        super().__init__(master, **kwargs)
        self.AppConfig = AppConfig
        
        # SỬA: Dùng transparent để ăn theo màu nền của khung cha (BG_CARD)
        self.configure(fg_color="transparent") 
        self.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Lấy giá trị cài đặt ban đầu
        self.value_face_recognition_threshold = self.AppConfig.threshold_security.face_recognition_threshold
        self.value_liveness_threshold = self.AppConfig.threshold_security.liveness_threshold
        self.value_smoothing_threshold = self.AppConfig.threshold_security.smooth_factor
        
        self.setup_ui()
        # Thiết lập trạng thái ban đầu cho công tắc và thanh trượt liveness
        self.update_ui_based_on_config()

    def setup_ui(self):
        # Tiêu đề
        # SỬA: Dùng AppFont và Theme.Color.TEXT
        self.title = ctk.CTkLabel(self, text="> Cài đặt phần mềm", font=AppFont.BODY_BOLD, text_color=Theme.Color.TEXT)
        self.title.grid(row=0, column=0, columnspan=3, padx=10, pady=(20, 5), sticky="w")

        # Phân nhóm
        # SỬA: Màu Primary (Xanh) thay cho #0044FF
        self.name_setting = ctk.CTkLabel(self, text="THIẾT LẬP NHẬN DẠNG", font=AppFont.BODY, text_color=Theme.Color.PRIMARY)
        self.name_setting.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="w")

        # Thanh trượt tỷ lệ nhận diện
        self.slider_accuracy = SliderWithLabel(self, "Tỷ lệ nhận diện khuôn mặt: (Khuyên dùng mức 0.6 - Ngưỡng cao càng khó nhận diện trên thiết bị kém chất lượng)", from_=0.0, to=1.0, initial=self.value_face_recognition_threshold)
        self.slider_accuracy.grid(row=2, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="ew")
        
        # Thanh trượt tỷ lệ chống giả mạo
        self.slider_liveness = SliderWithLabel(self, "Tỷ lệ nhận diện chống giả mạo: (Khuyên dùng mức 0.2 - Ngưỡng càng cao tỉ lệ chống giả càng thấp)", from_=0.0, to=1.0, initial=self.value_liveness_threshold)
        self.slider_liveness.grid(row=3, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="ew")
        
        # Thanh trượt tỷ lệ làm mượt tiêu chí nhận diện
        self.slider_smooth = SliderWithLabel(self, "Làm mượt đầu ra kết quả nhận diện: (Khuyên dùng mức 5 - Ngưỡng cao có thể làm chậm quá trình nhận diện)", from_=0, to = 20, initial=self.value_smoothing_threshold)
        self.slider_smooth.grid(row=4, column=0, columnspan=3, padx=20, pady=(0, 10), sticky="ew")

        # Công tắc bảo vệ
        self.switch_realtime = SwitchOption(self, "Chức năng bảo vệ chống giả mạo: (Tắt sẽ làm giảm bảo mật)", font=AppFont.BODY, command=self.toggle_liveness_protection)
        self.switch_realtime.grid(row=5, column=0, columnspan=3, padx=20, pady=5, sticky="ew")
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=6, column=0, columnspan=3, padx=20, pady=20, sticky="news")
        button_frame.grid_columnconfigure((0,1), weight=1)
        button_frame.grid_rowconfigure(0, weight=1)

        # SỬA: Note dùng màu đỏ cảnh báo hoặc text thường, tránh dùng màu tối cứng (#011752) vì sẽ chìm trong nền đen
        note = ctk.CTkLabel(button_frame, text="LƯU Ý: Bất kỳ thay đổi nào cần phải được lưu trước khi thoát trang này, bạn nên chọn LƯU nếu có thực hiện thay đổi!", font=AppFont.SMALL, text_color=Theme.Color.DANGER)
        note.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

        # SỬA: Dùng màu Theme cho button
        self.reset_btn = ButtonTheme(button_frame, text="Cài lại", fg_color=Theme.Color.INFO, width=100, command=self.reset_settings)
        self.reset_btn.grid(row=0, column=0, sticky="we", padx=(0, 5))

        self.save_btn = ButtonTheme(button_frame, text="LƯU", fg_color=Theme.Color.SUCCESS, width=100, command=self.save_settings)
        self.save_btn.grid(row=0, column=1, padx=(5, 0), sticky="we")
    
    # --- GIỮ NGUYÊN LOGIC ---
    def update_ui_based_on_config(self):
        """Hàm này thiết lập trạng thái ban đầu cho công tắc và slider"""
        if self.value_liveness_threshold >= 1.0: # Coi như >= 1.0 là tắt
            self.switch_realtime.set_value(False) # Công tắc TẮT
            self.slider_liveness.configure(state="disabled") # Mờ thanh trượt đi
        else:
            self.switch_realtime.set_value(True) # Công tắc BẬT
            self.slider_liveness.configure(state="normal") # Thanh trượt bình thường

    def toggle_liveness_protection(self, switch_state):
        """Hàm được gọi mỗi khi công tắc thay đổi trạng thái"""
        if switch_state: # Nếu công tắc được BẬT
            self.slider_liveness.configure(state="normal")
        else: # Nếu công tắc được TẮT
            self.slider_liveness.configure(state="disabled")
            messagebox.showwarning("CẢNH BÁO BẢO MẬT", "Bạn đã tắt chức năng chống giả mạo. Hệ thống sẽ dễ bị tấn công bằng hình ảnh hoặc video.\n\nChỉ nên tắt trong trường hợp camera không đủ chất lượng hoặc để gỡ lỗi.")

    def reset_settings(self):
        """Cải tiến hàm reset để đồng bộ giao diện"""
        self.slider_accuracy.set_value(0.60)
        self.slider_liveness.set_value(0.20)
        self.slider_smooth.set_value(5)
        
        # Bật lại công tắc và thanh trượt khi reset
        self.switch_realtime.set_value(True)
        self.slider_liveness.configure(state="normal")

        messagebox.showinfo("LỜI NHẮC HỆ THỐNG", "Đã khôi phục cài đặt gốc thành công!")

    def save_settings(self):
        """Cải tiến hàm save với logic rõ ràng"""
        acc = self.slider_accuracy.get_value()
        smooth = self.slider_smooth.get_value()
        is_liveness_enabled = self.switch_realtime.get_value()

        # Logic lưu mới, đơn giản và chính xác
        if is_liveness_enabled:
            liveness = self.slider_liveness.get_value()
            self.AppConfig.threshold_security.liveness_threshold = liveness
            liveness_status_str = f"Bật (ngưỡng: {liveness})"
        else:
            self.AppConfig.threshold_security.liveness_threshold = 1.0
            liveness_status_str = "Tắt"

        self.AppConfig.threshold_security.face_recognition_threshold = acc
        self.AppConfig.threshold_security.smooth_factor = smooth
        save_config(self.AppConfig)
        
        messagebox.showinfo("LỜI NHẮC HỆ THỐNG", 
            f"LƯU THÀNH CÔNG!\n\n"
            f"Các cài đặt mới đã được áp dụng:\n"
            f"— Ngưỡng nhận diện: {acc}\n"
            f"— Chống giả mạo: {liveness_status_str}\n"
            f"— Làm mượt kết quả: {smooth}")