import customtkinter as ctk
from gui.base.utils import WigdetFrame as WF, LabelCustom as LBL, ComboboxTheme, ButtonTheme as BT, LoadingDialog
from gui.base.base_chart import BarChart, CircularProgressChart, StatsSummaryCard
from datetime import datetime
import core.database as Db
import threading



class LecturerStatistical(ctk.CTkFrame):
    def __init__(self, master=None, username=None,  **kwargs):
        super().__init__(master, **kwargs)
        
        # Xử lý username/user
        self.master = master
        self.username = username
        
        # Cấu hình giao diện
        self._border_width = 1
        self._border_color = "white"
        self._fg_color = "white"
        self.widget_color = "#05243F"
        
        # Biến lưu trữ
        self.loading_dialog = None
        self.current_class = None
        self.current_subject = None
        self.total_students_current_class = 0
        
        # Cấu hình layout
        self.grid_rowconfigure((0, 1), weight=0)
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Tạo giao diện
        self.create_header()
        self.create_overview_section()
        self.create_class_subject_statistics_section()
        
        # Tự động load dữ liệu
        self.auto_load_first_class_subject()

    def create_header(self):
        """Tạo tiêu đề"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="Dashboard > THỐNG KÊ ĐIỂM DANH", 
            font=("Bahnschrift", 20, "bold"), 
            text_color="#05243F"
        )
        title_label.pack(side="left")

    def create_overview_section(self):
        """Tạo phần tổng quan với các thẻ thống kê"""
        overview_frame = WF(
            self, row=1, column=0, columnspan=2,
            widget_color=self.widget_color,
            sticky="ew", padx=10, pady=5,
            width=800, height=150, radius=10
        )
        
        LBL(overview_frame, "TỔNG QUAN", font_size=14, font_weight="bold", 
           text_color="#DEE4FF", pack_pady=5)
        
        cards_frame = ctk.CTkFrame(overview_frame, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=10)
        
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1, minsize=200)
        cards_frame.grid_rowconfigure(0, weight=1)
        
        # Thẻ tổng số lớp
        self.card_total_classes = StatsSummaryCard(
            cards_frame, title="Tổng số lớp điểm danh", value="0",
            subtitle="", color="#4CAF50", icon_text="📚", width=200, height=120
        )
        self.card_total_classes.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Thẻ thời gian còn lại
        self.card_time_remaining = StatsSummaryCard(
            cards_frame, title="Thời gian còn lại của học kỳ này", value="0 Tuần",
            color="#2196F3", icon_text="⏰", width=200, height=120
        )
        self.card_time_remaining.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Thẻ tiến độ
        self.card_progress = StatsSummaryCard(
            cards_frame, title="Tiến độ hoàn thành", value="0%",
            color="#FF9800", icon_text="📊", width=200, height=120
        )
        self.card_progress.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        # Thẻ nâng cao
        self.card_improvement = StatsSummaryCard(
            cards_frame, title="Quan Sát Dữ Liệu Nâng Cao", value="Thông Số Hệ Thống",
            subtitle="Chức năng dành cho người quản trị", color="#9C27B0", icon_text="⚙️", width=200, height=120
        )
        self.card_improvement.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

    def create_class_subject_statistics_section(self):
        """Tạo phần thống kê theo lớp học phần — CHỈ GIỮ BIỂU ĐỒ"""
        main_stats_frame = WF(
            self, row=2, column=0, columnspan=2,
            widget_color="#05243F",
            sticky="nsew", padx=10, pady=5,
            width=1200, height=500, radius=10
        )
        
        LBL(main_stats_frame, "THỐNG KÊ THEO LỚP HỌC PHẦN", font_size=14, 
           font_weight="bold", text_color="#E0E2EE", pack_pady=5)
        
        # Bộ lọc
        filter_frame = ctk.CTkFrame(main_stats_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Chọn lớp:", font=("Bahnschrift", 12), text_color="#C5E4EF").pack(side="left", padx=(0, 5))
        self.class_combo = ComboboxTheme(filter_frame, values=["Đang tải..."], width=150, command=self.on_class_changed)
        self.class_combo.set("Đang tải...")
        self.class_combo.pack(side="left", padx=5)

        ctk.CTkLabel(filter_frame, text="Chọn môn học:", font=("Bahnschrift", 12), text_color="#C5E4EF").pack(side="left", padx=(20, 5))
        self.subject_combo = ComboboxTheme(filter_frame, values=["Đang tải..."], width=150, command=self.on_subject_changed)
        self.subject_combo.set("Đang tải...")
        self.subject_combo.pack(side="left", padx=5)

        refresh_btn = ctk.CTkButton(filter_frame, text="Refresh", fg_color="transparent", corner_radius=5, border_color="white", border_width=2, width=100, command=self.refresh_class_subject_data)
        refresh_btn.pack(side="right", padx=5)
        
        # Container biểu đồ — chiếm toàn bộ không gian
        content_frame = ctk.CTkFrame(main_stats_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(2, weight=0, minsize=850)

        
        charts_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        charts_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        charts_frame.grid_columnconfigure((0, 1), weight=1)
        charts_frame.grid_rowconfigure((0), weight=1)
        
        button_group = ctk.CTkFrame(content_frame, fg_color="transparent", border_color="#31FCA1", border_width=3, corner_radius=10)
        button_group.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        button_group.grid_columnconfigure((0), weight=1)
        button_group.grid_rowconfigure((0), weight=1)
        
        # Biểu đồ cột
        self.students_bar_chart = BarChart(
            charts_frame, title="Tổng sinh viên: 0", data_dict={}, color="#4CAF50"
        )
        self.students_bar_chart.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        # Biểu đồ tròn 1: Buổi hoàn thành
        self.completion_chart = CircularProgressChart(
            charts_frame, title="Buổi hoàn thành", value=0, max_value=1, color="#2196F3", size=(200, 200)
        )
        self.completion_chart.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Biểu đồ tròn 2: Tỉ lệ đi học
        self.attendance_chart = CircularProgressChart(
            charts_frame, title="Tỉ lệ đi học", value=0, max_value=1, color="#4CAF50", size=(200, 200)
        )
        self.attendance_chart.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        # Nhóm nút chức năng báo cáo
        report_group = ctk.CTkFrame(
            button_group, fg_color="white",
            border_color="#05243F", border_width=2,
            corner_radius=10
        )
        report_group.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        report_group.grid_columnconfigure((0, 1), weight=1)

        # Tiêu đề nhóm
        title_label = ctk.CTkLabel(
            report_group, text="📑 BÁO CÁO THỐNG KÊ",
            font=("Bahnschrift", 16, "bold"), text_color="#05243F"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 15))

        # Danh sách các báo cáo
        reports = [
            # ("Xuất báo cáo tổng thể", "Xuất", lambda: export_total(self.master)),
            ("Xuất báo cáo chi tiết", "Chi tiết", lambda: export_detail(self)),
            # ("Báo cáo theo lớp học phần", "Theo lớp", None),
            # ("Báo cáo điểm danh theo tuần", "Theo tuần", None),
            # ("Báo cáo điểm danh theo học kỳ", "Theo kỳ", None),
            # ("Xuất danh sách lớp", "Danh sách", None),
        ]

        for i, (label_text, btn_text, func) in enumerate(reports, start=1):
            lbl = ctk.CTkLabel(
                report_group, text=label_text,
                font=("Bahnschrift", 14), text_color="#05243F"
            )
            lbl.grid(row=i, column=0, padx=5, pady=5, sticky="w")

            btn = BT(
                report_group, text=btn_text, width=180, command=func
            )
            btn.grid(row=i, column=1, padx=5, pady=5, sticky="e")

        # Nhóm nút chức năng mẫu
        templet_group = ctk.CTkFrame(
            button_group, fg_color="white",
            border_color="#05243F", border_width=2,
            corner_radius=10
        )
        templet_group.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        templet_group.grid_columnconfigure((0, 1), weight=1)

        # Tiêu đề nhóm
        title_label = ctk.CTkLabel(
            templet_group, text="📑 BIỂU MẪU",
            font=("Bahnschrift", 16, "bold"), text_color="#05243F"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 15))

        # Danh sách các báo cáo
        reports = [
            ("Mẫu danh sách lớp", "Danh sách"),
            ("Mẫu báo cáo điểm danh", "Điểm danh")
        ]

        for i, (label_text, btn_text) in enumerate(reports, start=1):
            lbl = ctk.CTkLabel(
                templet_group, text=label_text,
                font=("Bahnschrift", 14), text_color="#05243F"
            )
            lbl.grid(row=i, column=0, padx=5, pady=5, sticky="w")

            btn = BT(
                templet_group, text=btn_text, width=180
            )
            btn.grid(row=i, column=1, padx=5, pady=5, sticky="e")



    def on_class_changed(self, selected_class):
        """Khi chọn lớp"""
        self.current_class = selected_class
        self.total_students_current_class = Db.get_total_students_by_class(selected_class) or 0
        
        # Load danh sách môn học
        subjects = Db.get_subjects_by_class(self.username, selected_class)
        if subjects:
            self.subject_combo.configure(values=subjects)
            first_subject = subjects[0]
            self.subject_combo.set(first_subject)
            self.current_subject = first_subject
        else:
            self.subject_combo.configure(values=["Không có môn học"])
            self.subject_combo.set("Không có môn học")
            self.current_subject = None
        
        self.update_class_subject_data()

    def on_subject_changed(self, selected_subject):
        """Khi chọn môn học"""
        self.current_subject = selected_subject
        self.update_class_subject_data()

    def update_class_subject_data(self):
        """Cập nhật dữ liệu theo lớp & môn đã chọn"""
        if not self.current_class or not self.current_subject:
            return
            
        try:
            # 1. Biểu đồ cột
            chart_data = self.get_attendance_chart_data()
            title = f"Lớp {self.current_class}: {self.total_students_current_class} sinh viên"
            self.students_bar_chart.title = title
            self.students_bar_chart.update_data(chart_data if chart_data else {"Chưa có dữ liệu": 0})
            
            # 2. Biểu đồ tròn - buổi hoàn thành
            completed, total = self.get_completion_statistics()
            self.completion_chart.update_data(completed, total or 1)  # Tránh chia cho 0
            
            # 3. Biểu đồ tròn - tỉ lệ đi học
            avg_attendance, total_students = self.get_average_attendance_rate()
            self.attendance_chart.update_data(avg_attendance, total_students or 1)
            
        except Exception as e:
            print(f"Lỗi cập nhật dữ liệu thống kê: {e}")

    def get_attendance_chart_data(self):
        """Lấy dữ liệu biểu đồ cột"""
        try:
            return Db.get_attendance_chart_by_class_subject(
                self.username, self.current_class, self.current_subject, 90
            )
        except Exception as e:
            print(f"Lỗi lấy dữ liệu biểu đồ: {e}")
            return {}

    def get_completion_statistics(self):
        """Lấy số buổi đã hoàn thành"""
        try:
            return Db.get_completion_statistics_by_class_subject(
                self.username, self.current_class, self.current_subject
            )
        except Exception as e:
            print(f"Lỗi lấy thống kê hoàn thành: {e}")
            return 0, 1

    def get_average_attendance_rate(self):
        """Lấy tỉ lệ đi học trung bình"""
        try:
            return Db.get_average_attendance_by_class_subject(
                self.username, self.current_class, self.current_subject
            )
        except Exception as e:
            print(f"Lỗi lấy tỉ lệ đi học: {e}")
            return 0, 1

    def refresh_class_subject_data(self):
        """Làm mới dữ liệu"""
        self.update_class_subject_data()

    def load_overview_data(self):
        """Load dữ liệu tổng quan"""
        try:
            stats = Db.get_lecturer_statistics_overview(self.username)
            if stats:
                self.card_total_classes.update_value(
                    str(stats['tong_lop']),
                    f"{stats['tien_do_hoan_thanh']}% ({stats['tong_lop']} Lớp)"
                )
                self.card_time_remaining.update_value(f"{stats['thoi_gian_con_lai']} Tuần", f"Đến hết {str(stats['thoi_gian_ket_thuc'])}")
                self.card_progress.update_value(f"{stats['tien_do_hoan_thanh']}%", f"Hoàn thành {stats['so_buoi_da_day']}/{stats['tong_so_buoi']} buổi")
        except Exception as e:
            print(f"Lỗi load dữ liệu tổng quan: {e}")

    def auto_load_first_class_subject(self):
        """Tự động load lớp & môn đầu tiên"""
        try:
            self.load_overview_data()
            
            classes_list = Db.get_lecturer_classes_for_filter(self.username)
            if not classes_list:
                self.class_combo.configure(values=["Không có lớp"])
                self.class_combo.set("Không có lớp")
                self.subject_combo.configure(values=["Không có môn học"])
                self.subject_combo.set("Không có môn học")
                return
            
            first_class = classes_list[0]
            self.class_combo.configure(values=classes_list)
            self.class_combo.set(first_class)
            self.current_class = first_class
            self.total_students_current_class = Db.get_total_students_by_class(first_class) or 0
            
            subjects = Db.get_subjects_by_class(self.username, first_class)
            if subjects:
                first_subject = subjects[0]
                self.subject_combo.configure(values=subjects)
                self.subject_combo.set(first_subject)
                self.current_subject = first_subject
            else:
                self.subject_combo.configure(values=["Không có môn học"])
                self.subject_combo.set("Không có môn học")
                self.current_subject = None
            
            self.update_class_subject_data()
            
        except Exception as e:
            print(f"Lỗi auto load: {e}")
            
#+++++++++++++++++++++ Tạo dialog chờ ++++++++++++++++++++++++++++++++
    def _start_dialog(self):
            """Hiển thị dialog tải và khởi chạy tác vụ nặng trong một luồng riêng."""
            self.loading_dialog = LoadingDialog(self, message="Đang tạo báo cáo...", mode="indeterminate", height_progress=10)

            
            
#+=========================Chức năng nút==================================+#
def export_total(master):
    from gui.user.lecturer_popup_report import PopUpReport
    overlay = PopUpReport(master=master, option="total")
    
def export_detail(view):
    from gui.user.lecturer_popup_report import PopUpReport
    def task():
        try:
            overlay = PopUpReport(
                master=view.master,
                option="detail",
                class_name=view.current_class,
                subject_name=view.current_subject,
                username=view.username,
            )
        finally:
            view.after(100, lambda: view.loading_dialog.stop())

    view._start_dialog()
    threading.Thread(target=task, daemon=True).start()

    
    




