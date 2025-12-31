# ===================================================================================
# FILE: PopUpReport.py
# ===================================================================================

# --- Các import từ thư viện chuẩn và bên thứ ba ---
import os
import shutil
import tempfile
import json
from datetime import datetime
from tkinter import filedialog, messagebox
from PIL import ImageGrab 
import win32api
import win32print

from gui.base.base_popup_window import BasePopupWindow
from gui.base.utils import * # Chứa ImageProcessor, ButtonTheme, LabelCustom
from core.database import * # Chứa các hàm report_..., get_ma_lop_hoc_phan
from core.create_report import ExcelReportFiller # Lớp ExcelReportFiller đã được cập nhật


class PopUpReport(BasePopupWindow):
    """
    Cửa sổ Pop-up để xem trước, lưu và in báo cáo điểm danh.
    - Chế độ 'detail': Tạo báo cáo chi tiết, điền dữ liệu vào file Excel,
      chụp ảnh sheet và hiển thị bản xem trước động.
    - Chế độ 'total': Hiển thị ảnh xem trước tĩnh cho báo cáo tổng quan.
    """
    def __init__(self, master=None, config=None, option=None, class_name=None, subject_name=None, username=None, **kwargs):
        super().__init__(master, config, **kwargs)
        
        self.fg_color = Theme.Color.PRIMARY
        
        # --- Lưu các tham số đầu vào ---
        self.option = option
        self.class_name = class_name
        self.subject_name = subject_name
        self.username = username

        # --- Đường dẫn và thuộc tính file ---
        self.template_detail_path = "form/form_dschitiet_ddsv_lophocphan.xlsm"
        self.processed_file_path = None  # Đường dẫn đến file Excel tạm đã được điền dữ liệu
        self.preview_image_path = None   # Đường dẫn đến file ảnh xem trước (có thể là tĩnh hoặc động)

        # --- Cấu hình tiêu đề và ảnh mặc định dựa trên tùy chọn ---
        if option == "total":
            self.label_title.set_text("Dashboard > THONG KE DIEM DANH > BAO CAO TONG QUAN")
            # Sử dụng ảnh tĩnh cho báo cáo tổng quan
            self.preview_image_path = "resources/img_form/total/total.png"
        elif option == "detail":
            self.label_title.set_text("Dashboard > THONG KE DIEM DANH > BAO CAO CHI TIET")
            # Ảnh mặc định, sẽ được cập nhật bằng ảnh chụp từ Excel
            self.preview_image_path = "resources/img_form/details/form_dschitiet_ddsv_lophocphan.png"
        
        # --- CẬP NHẬT: Chuẩn bị dữ liệu và ảnh TRƯỚC KHI dựng giao diện ---
        try:
            if self.option == "detail":
                # Hàm này sẽ điền dữ liệu vào Excel và chụp ảnh xem trước
                self._prepare_detail_report()
        except Exception as e:
            print(f"Lỗi nghiêm trọng khi chuẩn bị báo cáo: {e}")
            messagebox.showerror("Lỗi Tạo Báo Cáo", f"Đã xảy ra lỗi khi chuẩn bị dữ liệu báo cáo:\n{e}")
    
        # Dựng giao diện sau khi đã có dữ liệu và ảnh
        self.setup_frame()
    
    def on_close(self):
        """
        Dọn dẹp tài nguyên trước khi đóng cửa sổ.
        """
        # --- CẬP NHẬT: Xóa file ảnh xem trước tạm thời ---
        # Chỉ xóa nếu đó là file preview được tạo động
        if self.preview_image_path and "preview_report" in self.preview_image_path and os.path.exists(self.preview_image_path):
            try:
                os.remove(self.preview_image_path)
                print(f"Đã xóa file ảnh tạm: {self.preview_image_path}")
            except Exception as e:
                print(f"Lỗi khi xóa file ảnh tạm: {e}")
        
        # Gọi hàm on_close của lớp cha để đóng cửa sổ
        super().on_close()

    def _prepare_detail_report(self):
        """
        Hàm chính để xử lý báo cáo chi tiết:
        1. Lấy dữ liệu từ database.
        2. Mở file Excel mẫu ở chế độ ẩn.
        3. Điền dữ liệu vào file.
        4. Chụp ảnh vùng dữ liệu của sheet.
        5. Lưu đường dẫn file Excel và file ảnh đã xử lý.
        """
        # 1. Lấy dữ liệu từ database
        try:
            title_info = report_attendance_details_of_subject_title(self.username, self.subject_name) or {}
            id_class_subject = get_ma_lop_hoc_phan(self.class_name, self.subject_name)
            report = report_attendance_details_of_subject(id_class_subject) or {}
        except Exception as e:
            raise RuntimeError(f"Lỗi khi truy vấn dữ liệu báo cáo từ database: {e}")

        static_data = {**report.get("static_data", {}), **title_info}
        if 'ten_lop' in static_data and 'lop' not in static_data:
            static_data['lop'] = static_data['ten_lop']

        if not os.path.exists(self.template_detail_path):
            raise FileNotFoundError(f"Không tìm thấy file mẫu: {self.template_detail_path}")

        # 2. Mở, điền dữ liệu và chụp ảnh bằng ExcelReportFiller
        with ExcelReportFiller(self.template_detail_path) as filler:
            # 3. Điền dữ liệu
            student_data = report.get("student_data", [])
            filler.fill_data(static_data, student_data)
            
            # 5. Lưu đường dẫn file Excel tạm
            self.processed_file_path = filler.get_temp_file_path()

            # --- CẬP NHẬT: Chụp ảnh sheet sau khi điền dữ liệu ---
            # Tạo đường dẫn cho file ảnh tạm
            temp_img_path = os.path.join(tempfile.gettempdir(), f"preview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            # Ước tính vùng cần chụp dựa trên số lượng sinh viên
            # Bạn cần điều chỉnh cột cuối (ví dụ: 'Q') và số hàng thêm (ví dụ: 5) cho phù hợp
            num_students = len(student_data)
            capture_range = f"A1:Q{10 + num_students + 5}" 
            
            # 4. Chụp ảnh
            captured_path = filler.capture_sheet_as_image(temp_img_path, capture_range=capture_range)
            
            # 5. Lưu đường dẫn file ảnh nếu chụp thành công
            if captured_path:
                self.preview_image_path = captured_path
            else:
                print("Không chụp được ảnh xem trước, sẽ sử dụng ảnh mặc định.")


    def setup_frame(self):
        """
        Dựng các thành phần giao diện người dùng (khung, nhãn, nút bấm, ảnh xem trước).
        """
        # --- Khung xem trước ---
        show_preview_frame = ctk.CTkFrame(self, fg_color="transparent")
        show_preview_frame.grid(row=0, column=0, padx=(0,0), pady=(0,0), sticky="nsew")
        show_preview_frame.columnconfigure(0, weight=1)
        show_preview_frame.rowconfigure(1, weight=1)
        
        # --- Khung chứa các nút bấm ---
        button_report_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=10, border_color=self.fg_color, border_width=2)
        button_report_frame.grid(row=0, column=1, padx=(5, 30), pady=(60, 20), sticky="nswe")
        button_report_frame.columnconfigure(0, weight=1)
        
        # --- Tiêu đề và mô tả ---
        tile_privew = LabelCustom(show_preview_frame, "BẢN XEM TRƯỚC", value="Bản xem trước được tạo tự động từ file Excel. Giao diện thực tế khi in hoặc xuất file có thể khác biệt đôi chút", text_color="white", wraplength=700)
        tile_privew.grid(row=0, column=0, padx=0, pady=0, sticky="nw")
        
        # --- CẬP NHẬT: Hiển thị ảnh xem trước (động hoặc tĩnh) ---
        # Fallback: Nếu đường dẫn ảnh không hợp lệ, dùng ảnh mặc định để tránh lỗi
        if not self.preview_image_path or not os.path.exists(self.preview_image_path):
            self.preview_image_path = "resources/img_form/details/form_dschitiet_ddsv_lophocphan.png"
            print(f"Không tìm thấy ảnh xem trước, sử dụng ảnh mặc định: {self.preview_image_path}")

        # ctk_image = ImageProcessor(self.preview_image_path) \
        #                          .crop_to_aspect(1180, 840) \
        #                          .resize(750, 500) \
        #                          .to_ctkimage(size=(750, 550))
        display_width, display_height = 750, 550
        ctk_image = ImageProcessor(self.preview_image_path) \
                         .resize_and_pad(display_width, display_height, background_color=(0, 0, 0, 0)) \
                         .to_ctkimage()
                         
        frame_round = ctk.CTkFrame(show_preview_frame, fg_color=Theme.Color.BG_CARD, corner_radius=10, border_color=self.fg_color, border_width=2)
        frame_round.grid(row=1, column=0, padx=0, pady=20, sticky="nsew")
        frame_round.columnconfigure(0, weight=1)
        frame_round.rowconfigure(0, weight=1)
        img_label = ctk.CTkLabel(frame_round, text="", image=ctk_image, fg_color="transparent")
        img_label.grid(row=0, column=0, padx=0, pady=20, sticky="wne")
        
        # --- Các nút bấm và mô tả ---
        tile_btn = LabelCustom(button_report_frame, "Lưu trữ Báo cáo:", value="Vui lòng chọn các phương thức lưu trữ sau:\n1. In báo cáo trực tiếp ra máy in mặc định.\n2. Lưu báo cáo dưới dạng file Excel.", text_color="white", value_color="white", font_size=12, wraplength=230)
        tile_btn.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nw")
        
        btn_print = ButtonTheme(button_report_frame, text="IN BÁO CÁO", width=100, command=self.print_report)
        btn_print.grid(row=1, column=0, padx=10, pady=(10, 5), sticky="nsew")
        
        btn_save = ButtonTheme(button_report_frame, text="LƯU BÁO CÁO", width=100, fg_color=self.fg_color, command=self.save_report)
        btn_save.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="nsew")

    def print_report(self):
        """
        Gửi file Excel đã xử lý đến máy in mặc định của hệ thống.
        """
        if not self.processed_file_path or not os.path.exists(self.processed_file_path):
            messagebox.showerror("Lỗi", "Không tìm thấy file báo cáo để in. Vui lòng thử lại.")
            return

        try:
            current_printer = win32print.GetDefaultPrinter()
            win32api.ShellExecute(0, "print", self.processed_file_path, f'/d:"{current_printer}"', ".", 0)
            messagebox.showinfo("Thông báo", f"Đã gửi yêu cầu in file đến máy in mặc định:\n{current_printer}")
        except Exception as e:
            messagebox.showerror("Lỗi In File", f"Không thể gửi file đến máy in. Lỗi: {e}")

    def save_report(self):
        """
        Mở hộp thoại để người dùng chọn vị trí và lưu file Excel đã xử lý.
        """
        if not self.processed_file_path or not os.path.exists(self.processed_file_path):
            messagebox.showerror("Lỗi", "Không tìm thấy file báo cáo để lưu. Vui lòng thử lại.")
            return

        # Tạo tên file gợi ý
        default_filename = f"BaoCao_{self.class_name}_{self.subject_name}_{datetime.now().strftime('%Y%m%d')}.xlsm"

        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".xlsm",
            filetypes=[("Excel Macro-Enabled Workbook", "*.xlsm"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                # Sao chép file từ thư mục tạm ra vị trí người dùng chọn
                shutil.copy(self.processed_file_path, file_path)
                messagebox.showinfo("Thành công", f"Đã lưu báo cáo thành công tại:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Lỗi Lưu File", f"Không thể lưu file. Lỗi: {e}")