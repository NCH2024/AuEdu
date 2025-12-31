import customtkinter as ctk
from gui.base.utils import WigdetFrame as WF, LabelCustom as LBL, ComboboxTheme, ButtonTheme as BT, LoadingDialog
from gui.base.base_chart import BarChart, CircularProgressChart, StatsSummaryCard
import core.database as Db
import threading
from core.theme_manager import Theme, AppFont

class LecturerStatistical(ctk.CTkFrame):
    def __init__(self, master=None, username=None,  **kwargs):
        kwargs['fg_color'] = Theme.Color.BG 
        kwargs['corner_radius'] = 0
        super().__init__(master, **kwargs)
        
        self.master = master
        self.username = username
        self.widget_color = Theme.Color.BG_CARD
        
        self.loading_dialog = None
        self.current_class = None
        self.current_subject = None
        self.total_students_current_class = 0
        
        self.grid_rowconfigure((0, 1), weight=0)
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.create_header()
        self.create_overview_section()
        self.create_class_subject_statistics_section()
        
        self.auto_load_first_class_subject()

    def create_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(header_frame, text="Dashboard > THỐNG KÊ ĐIỂM DANH", font=AppFont.H3, text_color=Theme.Color.TEXT).pack(side="left")

    def create_overview_section(self):
        overview_frame = WF(self, row=1, column=0, columnspan=2, widget_color=self.widget_color, sticky="ew", padx=10, pady=5, width=800, height=150, radius=10)
        LBL(overview_frame, "TỔNG QUAN", font_size=14, font_weight="bold", text_color=Theme.Color.PRIMARY, pack_pady=5)
        
        cards_frame = ctk.CTkFrame(overview_frame, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=10)
        for i in range(4): cards_frame.grid_columnconfigure(i, weight=1, minsize=200)
        cards_frame.grid_rowconfigure(0, weight=1)
        
        # --- CHỈNH MÀU THEO THEME ---
        self.card_total_classes = StatsSummaryCard(cards_frame, title="Tổng số lớp điểm danh", value="0", subtitle="", color=Theme.Color.SUCCESS, icon_text="📚", width=200, height=120)
        self.card_total_classes.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.card_time_remaining = StatsSummaryCard(cards_frame, title="Thời gian còn lại", value="0 Tuần", color=Theme.Color.INFO, icon_text="⏰", width=200, height=120)
        self.card_time_remaining.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.card_progress = StatsSummaryCard(cards_frame, title="Tiến độ hoàn thành", value="0%", color=Theme.Color.WARNING, icon_text="📊", width=200, height=120)
        self.card_progress.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        self.card_improvement = StatsSummaryCard(cards_frame, title="Dữ Liệu Nâng Cao", value="Thông Số", subtitle="Admin Only", color=Theme.Color.PRIMARY, icon_text="⚙️", width=200, height=120)
        self.card_improvement.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

    def create_class_subject_statistics_section(self):
        main_stats_frame = WF(self, row=2, column=0, columnspan=2, widget_color=self.widget_color, sticky="nsew", padx=10, pady=5, width=1200, height=500, radius=10)
        LBL(main_stats_frame, "THỐNG KÊ THEO LỚP HỌC PHẦN", font_size=14, font_weight="bold", text_color=Theme.Color.PRIMARY, pack_pady=5)
        
        filter_frame = ctk.CTkFrame(main_stats_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Chọn lớp:", font=AppFont.BODY, text_color=Theme.Color.TEXT).pack(side="left", padx=(0, 5))
        self.class_combo = ComboboxTheme(filter_frame, values=["Đang tải..."], width=150, command=self.on_class_changed)
        self.class_combo.pack(side="left", padx=5)

        ctk.CTkLabel(filter_frame, text="Chọn môn học:", font=AppFont.BODY, text_color=Theme.Color.TEXT).pack(side="left", padx=(20, 5))
        self.subject_combo = ComboboxTheme(filter_frame, values=["Đang tải..."], width=200, command=self.on_subject_changed)
        self.subject_combo.pack(side="left", padx=5)

        BT(filter_frame, text="Làm mới", width=100, fg_color=Theme.Color.NEUTRAL, command=self.refresh_class_subject_data).pack(side="right", padx=5)
        
        content_frame = ctk.CTkFrame(main_stats_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        content_frame.grid_columnconfigure((0, 1), weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(2, weight=0, minsize=350)

        charts_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        charts_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        charts_frame.grid_columnconfigure((0, 1), weight=1)
        charts_frame.grid_rowconfigure(0, weight=1)
        
        button_group = ctk.CTkFrame(content_frame, fg_color="transparent", border_color=Theme.Color.BORDER, border_width=2, corner_radius=10)
        button_group.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        button_group.grid_columnconfigure(0, weight=1)
        
        # --- BIỂU ĐỒ DÙNG THEME ---
        self.students_bar_chart = BarChart(charts_frame, title="Tổng sinh viên: 0", data_dict={}, color=Theme.Color.SUCCESS)
        self.students_bar_chart.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        self.completion_chart = CircularProgressChart(charts_frame, title="Buổi hoàn thành", value=0, max_value=1, color=Theme.Color.INFO, size=(180, 180))
        self.completion_chart.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        self.attendance_chart = CircularProgressChart(charts_frame, title="Tỉ lệ đi học", value=0, max_value=1, color=Theme.Color.SUCCESS, size=(180, 180))
        self.attendance_chart.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        LBL(button_group, "📑 BÁO CÁO & BIỂU MẪU", font_size=14, font_weight="bold", text_color=Theme.Color.TEXT, pack_pady=10)
        actions = [("Xuất báo cáo chi tiết", lambda: export_detail(self)), ("Mẫu danh sách lớp", None), ("Mẫu báo cáo điểm danh", None)]
        for text, func in actions:
            BT(button_group, text=text, width=200, command=func).pack(pady=5, padx=20)

    def on_class_changed(self, selected_class):
        self.current_class = selected_class
        self.total_students_current_class = Db.get_total_students_by_class(selected_class) or 0
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
        self.current_subject = selected_subject
        self.update_class_subject_data()

    def update_class_subject_data(self):
        if not self.current_class or not self.current_subject: return
        try:
            chart_data = self.get_attendance_chart_data()
            title = f"Lớp {self.current_class}: {self.total_students_current_class} sinh viên"
            self.students_bar_chart.title = title
            self.students_bar_chart.update_data(chart_data if chart_data else {"Chưa có dữ liệu": 0})
            
            completed, total = self.get_completion_statistics()
            self.completion_chart.update_data(completed, total or 1)
            
            avg_attendance, total_students = self.get_average_attendance_rate()
            self.attendance_chart.update_data(avg_attendance, total_students or 1)
        except Exception as e:
            print(f"Lỗi cập nhật dữ liệu thống kê: {e}")

    def get_attendance_chart_data(self):
        try:
            return Db.get_attendance_chart_by_class_subject(self.username, self.current_class, self.current_subject, 90)
        except: return {}

    def get_completion_statistics(self):
        try:
            return Db.get_completion_statistics_by_class_subject(self.username, self.current_class, self.current_subject)
        except: return 0, 1

    def get_average_attendance_rate(self):
        try:
            return Db.get_average_attendance_by_class_subject(self.username, self.current_class, self.current_subject)
        except: return 0, 1

    def refresh_class_subject_data(self):
        self.update_class_subject_data()

    def load_overview_data(self):
        try:
            stats = Db.get_lecturer_statistics_overview(self.username)
            if stats:
                self.card_total_classes.update_value(str(stats['tong_lop']), f"{stats['tien_do_hoan_thanh']}% ({stats['tong_lop']} Lớp)")
                self.card_time_remaining.update_value(f"{stats['thoi_gian_con_lai']} Tuần", f"Đến hết {str(stats['thoi_gian_ket_thuc'])}")
                self.card_progress.update_value(f"{stats['tien_do_hoan_thanh']}%", f"Hoàn thành {stats['so_buoi_da_day']}/{stats['tong_so_buoi']} buổi")
        except Exception as e: print(f"Lỗi load tổng quan: {e}")

    def auto_load_first_class_subject(self):
        try:
            self.load_overview_data()
            classes_list = Db.get_lecturer_classes_for_filter(self.username)
            if not classes_list:
                self.class_combo.configure(values=["Không có lớp"])
                self.class_combo.set("Không có lớp")
                return
            
            first_class = classes_list[0]
            self.class_combo.configure(values=classes_list)
            self.class_combo.set(first_class)
            self.on_class_changed(first_class)
            
        except Exception as e: print(f"Lỗi auto load: {e}")

    def _start_dialog(self):
            self.loading_dialog = LoadingDialog(self, message="Đang tạo báo cáo...", mode="indeterminate", height_progress=10)

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