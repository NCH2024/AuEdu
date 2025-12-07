import customtkinter as ctk
from datetime import datetime, timedelta
from core.database import *
from gui.base.utils import *

class LecturerSchedule(ctk.CTkFrame):
    def __init__(self, master, lecturer_username=None, **kwargs):
        super().__init__(master, **kwargs)
        self.username = lecturer_username
        self.week_offset = 0
        self.configure(fg_color="transparent")

        self.widget_color = "#2DFCB0"
        self.data = self.getSchedule(self.username)

        # Cấu hình lưới
        self.grid_rowconfigure((0,1,4), weight=1)
        self.grid_rowconfigure((2), weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header_label = ctk.CTkLabel(
            self, text="Dashboard > LỊCH ĐIỂM DANH THEO TUẦN",
            font=("Bahnschrift", 20, "bold"),
            text_color="#05243F"
        )
        self.header_label.grid(row=0, column=0, padx=10, pady=5, sticky="nw")

        # Frame chính chứa chọn lớp, học phần, bảng phân công và thông tin học phần
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=1, column=0, pady=10, sticky="nesw")
        self.top_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=0)

        # Phân công điểm danh bọc bằng Frame
        self.schedule_wrapper = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.schedule_wrapper.grid(row=0, column=0, columnspan=3, padx=10, sticky="nwe")
        self.schedule_wrapper.grid_columnconfigure(0, weight=1)

        self.info_schedule = ctk.CTkFrame(self.schedule_wrapper, fg_color=self.widget_color)
        self.info_schedule.grid(row=0, column=0, sticky="nwe")
        self.info_schedule.grid_columnconfigure(0, weight=1)

        self.slogan_label = ctk.CTkLabel(
            self.info_schedule,
            text="PHÂN CÔNG ĐIỂM DANH CÁC LỚP:",
            font=("Bahnschrift", 12, "bold"),
            text_color="#011EB1"
        )
        self.slogan_label.grid(row=0, column=0, padx=20, pady=(5, 0), sticky="w")

        self.tb_frame_wrapper = ctk.CTkFrame(self.info_schedule, fg_color="transparent")
        self.tb_frame_wrapper.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.tb_frame_wrapper.grid_columnconfigure(0, weight=1)
        self.tb_frame_wrapper.grid_rowconfigure(0, weight=1)

        self.tb_schedule = CustomTable(
            self.tb_frame_wrapper,
            columns=["LỚP", "HỌC PHẦN", "HỌC KỲ", "SỐ BUỔI"],
            column_widths=[100, 200, 100, 80],
            data=self.data,
            # table_height=150,
            # table_width=485
        )
        self.tb_schedule.grid(row=0, column=0, padx=10, pady=5,sticky="nsew")

        # Thông tin học phần
        self.info_SubjectofSchedule = WigdetFrame(self.top_frame, width=500, height=240, widget_color=self.widget_color)
        self.info_SubjectofSchedule.grid(row=0, column=4, columnspan=3, padx=10, pady=10, sticky="nws")

        self.slogan_subject = LabelCustom(self.info_SubjectofSchedule, text="THÔNG TIN HỌC PHẦN TÌM KIẾM:", font_size=12, pack_padx=10)
        self.title_Subject = LabelCustom(self.info_SubjectofSchedule, text="Học phần: ", value="None", pack_padx=10, pack_pady=2)
        self.code_Subject = LabelCustom(self.info_SubjectofSchedule, text="Mã học phần: ", value="None", pack_padx=10, pack_pady=2)
        self.credit_Subject = LabelCustom(self.info_SubjectofSchedule, text="Số tín chỉ: ", value="None", pack_padx=10, pack_pady=2)
        self.total_hours_Subject = LabelCustom(self.info_SubjectofSchedule, text="Tổng số tiết: ", value="None", pack_padx=10, pack_pady=2)

        # Dropdown chọn lớp và học phần
        self.class_dropdown = ctk.CTkOptionMenu(self.top_frame, values=[], command=self.on_class_selected)
        self.class_dropdown.grid(row=2, column=0, padx=5, pady=(5, 10))

        self.subject_dropdown = ctk.CTkOptionMenu(self.top_frame, values=[])
        self.subject_dropdown.grid(row=2, column=1, padx=5, pady=(5, 10))

        self.search_btn = ctk.CTkButton(self.top_frame, text="Xem lịch", command=self.refresh_data)
        self.search_btn.grid(row=2, column=2, padx=10, pady=(5, 10))

        self.prev_btn = ctk.CTkButton(self.top_frame, text="⬅ Tuần trước", command=self.prev_week)
        self.prev_btn.grid(row=2, column=3, padx=10, pady=(5, 10))

        self.next_btn = ctk.CTkButton(self.top_frame, text="Tuần sau ➡", command=self.next_week)
        self.next_btn.grid(row=2, column=4, padx=10, pady=(5, 10))

        # Lịch dạng lưới theo tuần
        self.schedule_frame = ctk.CTkFrame(self, fg_color="#E8F6F3")
        self.schedule_frame.grid(row=3, column=0, sticky="nsew")
        self.schedule_frame.grid_columnconfigure((0,1,2,3,4,5,6,7), weight=1)

        self.day_labels = []
        self.grid_cells = {}

        # Ghi chú dưới cùng
        self.note_frame = ctk.CTkFrame(self, fg_color="#001933", corner_radius=12)
        self.note_frame.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="ew")

        self.note_title = ctk.CTkLabel(
            self.note_frame,
            text="📌 GHI CHÚ TUẦN NÀY",
            font=("Bahnschrift", 12, "bold"),
            text_color="#85FF21",
            anchor="w"
        )
        self.note_title.pack(padx=15, pady=(8, 0), anchor="w")

        self.note_bar = ctk.CTkLabel(
            self.note_frame,
            text="",
            font=("Bahnschrift", 14),
            text_color="white",
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

    def on_class_selected(self, selected_class):
        subjects = get_subjects_by_class(self.username, selected_class)
        if subjects:
            self.subject_dropdown.configure(values=subjects)
            self.subject_dropdown.set(subjects[0])
            self.update_subject_detail(subjects[0])

    def render_schedule_grid(self):
        for widget in self.schedule_frame.winfo_children():
            widget.destroy()

        weekday_map = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]

        for col in range(8):
            header = "Ca" if col == 0 else ""
            header_cell = ctk.CTkLabel(
                self.schedule_frame,
                text=header,
                font=("Bahnschrift", 14, "bold"),
                text_color="white",
                fg_color="#300047",
                corner_radius=8,
                anchor="center",
            )
            header_cell.grid(row=0, column=col, padx=2, pady=2, sticky="nsew")
            if col != 0:
                self.day_labels.append(header_cell)

        buoi_labels = ["Sáng", "Chiều", "Tối"]
        buoi_colors = ["#AED6F1", "#91E4D8", "#9FF9C6"]

        for row, (buoi, color) in enumerate(zip(buoi_labels, buoi_colors), start=1):
            buoi_label = ctk.CTkLabel(
                self.schedule_frame,
                text=buoi,
                font=("Bahnschrift", 13, "bold"),
                text_color="black",
                fg_color="#D5DBDB",
                corner_radius=6,
                width=80
            )
            buoi_label.grid(row=row, column=0, padx=2, pady=2, sticky="nsew")

            for col in range(1, 8):
                cell = ctk.CTkFrame(
                    self.schedule_frame,
                    fg_color=color,
                    corner_radius=6,
                    height=60
                )
                cell.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
                self.grid_cells[(col - 1, buoi)] = cell

    def update_header_dates(self):
        today = datetime.today() + timedelta(weeks=self.week_offset)
        start_of_week = today - timedelta(days=today.weekday())

        weekday_map = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
        for i in range(7):
            if self.day_labels[i]:
                date_str = f"{weekday_map[i]}\n{(start_of_week + timedelta(days=i)).strftime('%d/%m/%Y')}"
                self.day_labels[i].configure(text=date_str)

    def refresh_data(self):
        for frame in self.grid_cells.values():
            for widget in frame.winfo_children():
                widget.destroy()

        class_name = self.class_dropdown.get().strip()
        subject_name = self.subject_dropdown.get().strip()
        if not class_name or not subject_name:
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
                label = ctk.CTkLabel(
                    self.grid_cells[(weekday, buoi)],
                    text=f"{ten_hp}\n\nTiết: {tiet}",
                    font=("Bahnschrift", 13),
                    text_color="#000D4C",
                    justify="center"
                )
                label.pack(expand=True)

            if ghichu and ghichu.strip():
                note_text = f"• {ten_hp} ({ngay.strftime('%d/%m')}): {ghichu.strip()}"
                notes.append(note_text)

        if notes:
            formatted_notes = "\n".join(notes)
            self.note_bar.configure(text=formatted_notes, font=("Bahnschrift", 14, "normal"))
        else:
            self.note_bar.configure(text="• Không có ghi chú nào trong tuần này.", font=("Bahnschrift", 14, "italic"))

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
