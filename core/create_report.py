import os
import shutil
import tempfile
import json
from datetime import datetime
import xlwings as xw
from PIL import ImageGrab 

class ExcelReportFiller:
    def __init__(self, template_path, sheet_name="form_details"):
        self.template_path = os.path.abspath(template_path).replace("/", "\\")
        self.temp_file_path = None
        self.app = None
        self.wb = None
        self.sheet_name = sheet_name

    def __enter__(self):
        try:
            temp_dir = tempfile.gettempdir()
            self.temp_file_path = os.path.join(
                temp_dir,
                f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsm"
            )
            shutil.copy2(self.template_path, self.temp_file_path)
            print(f"Đã copy file mẫu ra: {self.temp_file_path}")

            # Mở Excel ở chế độ ẩn, không hiển thị cửa sổ
            self.app = xw.App(visible=False, add_book=False) 
            self.app.display_alerts = False
            self.wb = self.app.books.open(self.temp_file_path)
            print(f"Đã mở file tạm ở chế độ ẩn: {self.temp_file_path}")
        except Exception as e:
            self.__exit__(None, None, None)
            raise e
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.wb:
                self.wb.save()
                self.wb.close()
        finally:
            if self.app:
                self.app.quit()
            print("Đã đóng file và kết thúc tiến trình Excel.")

    def get_temp_file_path(self):
        return self.temp_file_path

    # --- PHƯƠNG THỨC MỚI ĐỂ CHỤP ẢNH SHEET ---
    def capture_sheet_as_image(self, output_image_path, capture_range="A1:P50"):
        """
        Chụp một vùng của sheet và lưu thành file ảnh.
        - capture_range: Vùng cần chụp, ví dụ "A1:O50". Bạn cần điều chỉnh cho phù hợp.
        """
        if not self.wb:
            raise RuntimeError("Workbook chưa mở.")
        
        try:
            ws = self.wb.sheets[self.sheet_name]
            
            # Copy vùng được chọn dưới dạng ảnh vào clipboard
            # Appearance=1 (xlScreen), Format=2 (xlPicture)
            ws.range(capture_range).api.CopyPicture(Appearance=1, Format=2)
            
            # Đợi một chút để clipboard sẵn sàng
            self.app.api.Wait(100)

            # Lấy ảnh từ clipboard
            img = ImageGrab.grabclipboard()

            if img:
                img.save(output_image_path)
                print(f"Đã chụp ảnh sheet và lưu tại: {output_image_path}")
                return output_image_path
            else:
                print("Không có ảnh trong clipboard để lưu.")
                return None
        except Exception as e:
            print(f"Lỗi khi chụp ảnh sheet: {e}")
            return None

    def fill_data(self, static_data, student_data):
        # ... (giữ nguyên toàn bộ code của hàm fill_data)
        if not self.wb:
            raise RuntimeError("Workbook chưa mở.")

        try:
            ws = self.wb.sheets[self.sheet_name]
        except Exception:
            raise ValueError(f"Không tìm thấy sheet '{self.sheet_name}'")

        # --- dữ liệu tĩnh ---
        defined_name_map = {
            'ten_hoc_phan': 'F5',
            'ten_giang_vien': 'F6',
            'hoc_ky': 'I6',
            'nam_hoc': 'L5',
            'lop': 'I5',
        }
        for name, cell in defined_name_map.items():
            if name in static_data:
                ws.range(cell).value = static_data[name]

        # --- dữ liệu sinh viên ---
        if not student_data or not student_data[0].get("dynamic_col"):
            print("Không có dữ liệu điểm danh.")
            return

        # danh sách ngày
        dynamic_col_data = json.loads(student_data[0]['dynamic_col'])
        dates = sorted(dynamic_col_data.keys(), key=lambda d: datetime.strptime(d, '%d/%m/%Y'))
        num_days = len(dates)

        data_start_row = 10
        fixed_content_row = 21   # dòng cố định
        start_col_index = ws.range("E9").column
        tien_do_col_index = ws.range("O9").column

        # --- chèn thêm cột ngày trước cột Tiến độ ---
        current_days = tien_do_col_index - start_col_index
        cols_to_insert = num_days - current_days
        if cols_to_insert > 0:
            ws.api.Range(
                ws.api.Cells(9, tien_do_col_index),
                ws.api.Cells(9, tien_do_col_index + cols_to_insert - 1)
            ).EntireColumn.Insert(Shift=1)  # xlToRight
            tien_do_col_index += cols_to_insert
            print(f"Đã chèn {cols_to_insert} cột, cột Tiến độ dời sang {tien_do_col_index}")

        # ghi header ngày
        for i, date_str in enumerate(dates):
            ws.cells(9, start_col_index + i).value = date_str

        # --- điền dữ liệu sv ---
        for i, student in enumerate(student_data):
            row_to_fill = data_start_row + i

            # giữ nguyên dòng 21
            if row_to_fill >= fixed_content_row:
                ws.api.Rows(fixed_content_row).Insert()
                fixed_content_row += 1
                print(f"Đã chèn dòng tại {fixed_content_row}")

            ws.cells(row_to_fill, 1).value = i + 1
            ws.cells(row_to_fill, 2).value = student['ma_sv']
            ws.cells(row_to_fill, 3).value = student['ho_dem']
            ws.cells(row_to_fill, 4).value = student['ten']

            # tiến độ
            ws.cells(row_to_fill, tien_do_col_index).value = student.get('ket_qua', '')

            # dữ liệu điểm danh
            attendance_data = json.loads(student['dynamic_col'])
            for col_index, date_str in enumerate(dates):
                ws.cells(row_to_fill, start_col_index + col_index).value = attendance_data.get(date_str, "")
                
        try:
            self.wb.macro("Modules.FixPageA4")()
            print("Đã chạy macro FixPageA4 sau khi điền dữ liệu.")
        except Exception as e:
            print(f"Lỗi khi chạy macro FixPageA4: {e}")
            
    def save(self, output_path):
        if self.wb:
            self.wb.save(output_path)
            print(f"File đã lưu tại: {output_path}")