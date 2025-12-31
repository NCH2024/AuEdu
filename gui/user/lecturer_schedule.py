import customtkinter as ctk
from datetime import datetime, timedelta
from core.database import *
from gui.base.utils import *
from core.theme_manager import Theme, AppFont, ColorPalette

class LecturerSchedule(ctk.CTkFrame):
    def __init__(self, master, lecturer_username=None, **kwargs):
        # Màu nền chính
        kwargs['fg_color'] = Theme.Color.BG
        kwargs['corner_radius'] = 0
        super().__init__(master, **kwargs)
        
        self.username = lecturer_username
        self.week_offset = 0

        self.widget_color = Theme.Color.BG_CARD
        self.data = self.getSchedule(self.username)

        # Cấu hình lưới
        self.grid_rowconfigure((0,1,4), weight=0)
        self.grid_rowconfigure(3, weight=1) # Phần lịch (row 3) giãn ra
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header_label = ctk.CTkLabel(
            self, text="Dashboard > LỊCH ĐIỂM DANH THEO TUẦN",
            font=AppFont.H3,
            text_color=Theme.Color.TEXT
        )
        self.header_label.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        # Frame chính chứa chọn lớp, học phần...
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=1, column=0, pady=0, sticky="ew")
        self.top_frame.grid_columnconfigure(0, weight=1)
        self.top_frame.grid_columnconfigure(1, weight=1)

        # 1. Bảng danh sách lớp (Trái)
        self.schedule_wrapper = WigdetFrame(self.top_frame, widget_color=self.widget_color)
        self.schedule_wrapper.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        self.schedule_wrapper.grid_columnconfigure(0, weight=1)

        LabelCustom(self.schedule_wrapper, "PHÂN CÔNG ĐIỂM DANH CÁC LỚP:", font_size=12, font_weight="bold", text_color=Theme.Color.PRIMARY).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.tb_frame_wrapper = ctk.CTkFrame(self.schedule_wrapper, fg_color="transparent", height=150)
        self.tb_frame_wrapper.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.tb_frame_wrapper.grid_columnconfigure(0, weight=1)
        self.tb_frame_wrapper.grid_rowconfigure(0, weight=1)

        # Bảng (Đã dùng theme)
        self.tb_schedule = CustomTable(
            self.tb_frame_wrapper,
            columns=["LỚP", "HỌC PHẦN", "HỌC KỲ", "SỐ BUỔI"],
            column_widths=[90, 180, 80, 70],
            data=self.data
        )
        self.tb_schedule.pack(fill="both", expand=True)

        # 2. Thông tin chi tiết (Phải)
        self.info_SubjectofSchedule = WigdetFrame(self.top_frame, widget_color=self.widget_color)
        self.info_SubjectofSchedule.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

        LabelCustom(self.info_SubjectofSchedule, text="THÔNG TIN HỌC PHẦN TÌM KIẾM:", font_size=12, font_weight="bold", text_color=Theme.Color.PRIMARY, pack_padx=10, pack_pady=5)
        self.title_Subject = LabelCustom(self.info_SubjectofSchedule, text="Học phần: ", value="None", pack_padx=10, pack_pady=2)
        self.code_Subject = LabelCustom(self.info_SubjectofSchedule, text="Mã học phần: ", value="None", pack_padx=10, pack_pady=2)
        self.credit_Subject = LabelCustom(self.info_SubjectofSchedule, text="Số tín chỉ: ", value="None", pack_padx=10, pack_pady=2)
        self.total_hours_Subject = LabelCustom(self.info_SubjectofSchedule, text="Tổng số tiết: ", value="None", pack_padx=10, pack_pady=2)

        # 3. Thanh công cụ (Toolbar)
        self.toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        # Dropdown (Thay bằng ComboboxTheme)
        self.class_dropdown = ComboboxTheme(self.toolbar_frame, values=["Đang tải..."], command=self.on_class_selected, width=150)
        self.class_dropdown.pack(side="left", padx=5)

        self.subject_dropdown = ComboboxTheme(self.toolbar_frame, values=["Đang tải..."], width=200)
        self.subject_dropdown.pack(side="left", padx=5)

        # Buttons (Thay bằng ButtonTheme)
        ButtonTheme(self.toolbar_frame, text="Xem lịch", width=100, command=self.refresh_data).pack(side="left", padx=5)
        
        ButtonTheme(self.toolbar_frame, text="Tuần sau ➡", width=100, command=self.next_week, fg_color=Theme.Color.BG_CARD, text_color=Theme.Color.TEXT, hover_color=Theme.Color.SECONDARY).pack(side="right", padx=5)
        ButtonTheme(self.toolbar_frame, text="⬅ Tuần trước", width=100, command=self.prev_week, fg_color=Theme.Color.BG_CARD, text_color=Theme.Color.TEXT, hover_color=Theme.Color.SECONDARY).pack(side="right", padx=5)


        # 4. Lịch dạng lưới (Phần chính)
        self.schedule_frame = ctk.CTkFrame(self, fg_color=Theme.Color.BG_CARD) # Nền lịch dùng màu Card
        self.schedule_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        self.schedule_frame.grid_columnconfigure((0,1,2,3,4,5,6,7), weight=1)
        self.schedule_frame.grid_rowconfigure((1,2,3), weight=1)

        self.day_labels = []
        self.grid_cells = {}

        # 5. Ghi chú dưới cùng
        self.note_frame = ctk.CTkFrame(self, fg_color=Theme.Color.BG_CARD, corner_radius=12)
        self.note_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        self.note_title = ctk.CTkLabel(
            self.note_frame,
            text="📌 GHI CHÚ TUẦN NÀY",
            font=AppFont.BODY_BOLD,
            text_color=Theme.Color.PRIMARY,
            anchor="w"
        )
        self.note_title.pack(padx=15, pady=(8, 0), anchor="w")

        self.note_bar = ctk.CTkLabel(
            self.note_frame,
            text="",
            font=AppFont.BODY,
            text_color=Theme.Color.TEXT,
            anchor="w",
            justify="left",
            wraplength=800
        )
        self.note_bar.pack(padx=30, pady=(5, 10), anchor="w")

        # Render và nạp dữ liệu
        self.load_classes()
        self.render_schedule_grid()
        self.refresh_data()

    def load_classes(self):
        classes = get_classes_of_lecturer(self.username)
        if classes:
            self.class_dropdown.configure(values=classes)
            self.class_dropdown.set(classes[0])
            self.on_class_selected(classes[0])
        else:
            self.class_dropdown.set("Không có lớp")
            self.class_dropdown.configure(state="disabled")

    def on_class_selected(self, selected_class):
        subjects = get_subjects_by_class(self.username, selected_class)
        if subjects:
            self.subject_dropdown.configure(values=subjects)
            self.subject_dropdown.set(subjects[0])
            self.update_subject_detail(subjects[0])
        else:
             self.subject_dropdown.set("Không có môn")
             self.subject_dropdown.configure(state="disabled")

    def render_schedule_grid(self):
        for widget in self.schedule_frame.winfo_children():
            widget.destroy()

        # 1. Xác định bộ màu dựa trên chế độ Sáng/Tối
        mode = ctk.get_appearance_mode()
        is_dark = mode == "Dark"

        # Màu tiêu đề cột (Ca học)
        col_header_fg = Theme.Color.SECONDARY
        col_header_text = Theme.Color.TEXT

        # Màu cột đầu tiên (Sáng/Chiều/Tối)
        row_header_fg = "#2B2B2B" if is_dark else "#E0E0E0"
        row_header_text = ColorPalette.WHITE if is_dark else "#05243F"

        # Màu nền các ô lịch (Cells)
        if is_dark:
            # Dark Mode: Màu nền tối hơn, chữ sáng
            # Dùng 3 tông màu tối phân biệt Sáng/Chiều/Tối
            buoi_colors = ["#1A3B5C", "#144239", "#2D3A2F"] 
            cell_text_color = "#E0E0E0" # Trắng xám
        else:
            # Light Mode: Màu Pastel cũ
            buoi_colors = ["#D1E8FF", "#C4F5E9", "#D6F8D6"]
            cell_text_color = "#000D4C" # Xanh đậm

        weekday_map = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]

        # Hàng tiêu đề (Header)
        for col in range(8):
            header = "Ca" if col == 0 else ""
            header_cell = ctk.CTkLabel(
                self.schedule_frame,
                text=header,
                font=AppFont.BODY_BOLD,
                text_color=col_header_text,
                fg_color=col_header_fg,
                corner_radius=8,
                anchor="center",
            )
            header_cell.grid(row=0, column=col, padx=2, pady=2, sticky="nsew")
            if col != 0:
                self.day_labels.append(header_cell)

        buoi_labels = ["Sáng", "Chiều", "Tối"]

        for row, (buoi, color) in enumerate(zip(buoi_labels, buoi_colors), start=1):
            # Cột đầu tiên (Tên buổi)
            buoi_label = ctk.CTkLabel(
                self.schedule_frame,
                text=buoi,
                font=AppFont.BODY_BOLD,
                text_color=row_header_text, # Dùng màu động
                fg_color=row_header_fg,     # Dùng màu động
                corner_radius=6,
                width=80
            )
            buoi_label.grid(row=row, column=0, padx=2, pady=2, sticky="nsew")

            # Các ô dữ liệu
            for col in range(1, 8):
                cell = ctk.CTkFrame(
                    self.schedule_frame,
                    fg_color=color, # Màu nền ô thay đổi theo Mode
                    corner_radius=6,
                    height=80
                )
                cell.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
                # Lưu thêm biến cell_text_color vào cell để dùng khi render text
                cell.text_color_config = cell_text_color 
                self.grid_cells[(col - 1, buoi)] = cell

    def update_header_dates(self):
        today = datetime.today() + timedelta(weeks=self.week_offset)
        start_of_week = today - timedelta(days=today.weekday())

        weekday_map = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
        for i in range(7):
            if self.day_labels[i]:
                date_str = f"{weekday_map[i]}\n{(start_of_week + timedelta(days=i)).strftime('%d/%m')}"
                self.day_labels[i].configure(text=date_str)

    def refresh_data(self):
        for frame in self.grid_cells.values():
            for widget in frame.winfo_children():
                widget.destroy()

        class_name = self.class_dropdown.get().strip()
        subject_name = self.subject_dropdown.get().strip()
        if not class_name or not subject_name or "Không có" in class_name:
            return
        data = get_schedule_by_week(class_name, subject_name, self.week_offset)
        self.display_schedule(data)
        self.update_subject_detail(subject_name)
        self.update_header_dates()

    def display_schedule(self, data):
        buoi_map = {"BS": "Sáng", "BC": "Chiều", "BT": "Tối"}
        notes = []

        for record in data:
            _, ten_hp, _, ngay, thu, ghichu, ma_loai, _, tiet = record
            weekday = ngay.weekday()
            buoi = buoi_map.get(ma_loai, "")

            if (weekday, buoi) in self.grid_cells:
                cell_frame = self.grid_cells[(weekday, buoi)]
                
                # Lấy màu chữ đã config từ lúc render grid
                text_col = getattr(cell_frame, 'text_color_config', Theme.Color.TEXT)

                # Tạo label hiển thị trong ô
                label = ctk.CTkLabel(
                    cell_frame,
                    text=f"{ten_hp}\nTiết: {tiet}",
                    font=AppFont.SMALL,
                    text_color=text_col, # Áp dụng màu chữ động
                    justify="center",
                    wraplength=120
                )
                label.pack(expand=True, fill="both", padx=2, pady=2)

            if ghichu and ghichu.strip():
                note_text = f"• {ten_hp} ({ngay.strftime('%d/%m')}): {ghichu.strip()}"
                notes.append(note_text)

        if notes:
            formatted_notes = "\n".join(notes)
            self.note_bar.configure(text=formatted_notes, font=AppFont.BODY)
        else:
            self.note_bar.configure(text="• Không có ghi chú nào trong tuần này.", font=(AppFont.NAME, 14, "italic"))

    def next_week(self):
        self.week_offset += 1
        self.refresh_data()

    def prev_week(self):
        self.week_offset -= 1
        self.refresh_data()

    def getSchedule(self, username):
        data = get_schedule(username)
        return data if data else [["", "", "", ""]]

    def update_subject_detail(self, subject_name):
        ma_hp, ten_hp, tinchi, tongtiet = get_subject_detail_from_hocphan(subject_name)
        self.title_Subject.value.configure(text=ten_hp)
        self.code_Subject.value.configure(text=ma_hp)
        self.credit_Subject.value.configure(text=str(tinchi))
        self.total_hours_Subject.value.configure(text=str(tongtiet))