import customtkinter as ctk
from gui.admin.admin_students_manager import AdminStudentsManager
from gui.admin.admin_lecturer_manager import AdminLecturerManager
from gui.base.utils import NotifyList
from gui.admin.admin_academic import AdminAcademic
from gui.admin.admin_notice import AdminNotice
from gui.base.utils import *
from gui.base.base_chart import *
import core.database as Db
from core.utils import get_base_path
from core.theme_manager import Theme, AppFont 
import os

class AdminGeneral(ctk.CTkFrame):
    def __init__(self, master=None, user=None, **kwargs):
        super().__init__(master, **kwargs)
        self.user = user
        self.configure(fg_color=Theme.Color.BG, corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.text_color = Theme.Color.PRIMARY 
        self.widget_color = Theme.Color.BG_CARD 

        self.setup_ui()
        self.load_overview_data()

    def create_overview_section(self):
        overview_frame = WigdetFrame(
            self, row=1, column=0, columnspan=2,
            widget_color=self.widget_color,
            sticky="ew", padx=10, pady=5,
            width=800, height=150, radius=10
        )
        LabelCustom(overview_frame, "TỔNG QUAN", font_size=14, font_weight="bold", text_color=self.text_color, pack_pady=5)
        cards_frame = ctk.CTkFrame(overview_frame, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=5)
        for i in range(4): cards_frame.grid_columnconfigure(i, weight=1, minsize=200)
        cards_frame.grid_rowconfigure(0, weight=1)

        self.card_total_students = StatsSummaryCard(cards_frame, title="Tổng số sinh viên", value="0 Sinh Viên", color=Theme.Color.SUCCESS, icon_text="🪪", width=200, height=120)
        self.card_total_students.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.card_total_class = StatsSummaryCard(cards_frame, title="Tổng số lớp học", value="0 Lớp", color=Theme.Color.INFO, icon_text="🏫", width=200, height=120)
        self.card_total_class.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.card_progress = StatsSummaryCard(cards_frame, title="Tiến độ hoàn thành", value="0%", color=Theme.Color.WARNING, icon_text="📊", width=200, height=120)
        self.card_progress.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        self.card_improvement = StatsSummaryCard(cards_frame, title="Dữ Liệu Nâng Cao", value="Thông Số", subtitle="Admin Only", color="#9C27B0", icon_text="⚙️", width=200, height=120)
        self.card_improvement.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

    def setup_ui(self):
        self.title = ctk.CTkLabel(self, text="Dashboard > Trang Chủ", font=AppFont.H3, text_color=Theme.Color.TEXT)
        self.title.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.create_overview_section()
        
        path_adminStudentManager = os.path.join(get_base_path(), "resources","images","students.png")
        path_adminLectuterManager = os.path.join(get_base_path(), "resources","images","teacher.png")
        path_adminAcademicManager = os.path.join(get_base_path(), "resources","images","class.png")
        path_adminNoticeManager = os.path.join(get_base_path(), "resources","images","notice.png")
        
        dataButton_left = [
            (path_adminStudentManager, "SINH VIÊN•LỚP", lambda: self.show_AdminStudentsManager()),
            (path_adminLectuterManager, "GIẢNG VIÊN•KHOA", lambda: self.show_AdminLecturerManager()),
        ]
        dataButton_right = [
            (path_adminAcademicManager, "HỌC VỤ", lambda: self.show_AdminAcademic()),
            (path_adminNoticeManager, "THÔNG BÁO", lambda: self.show_AdminNotice()),
        ]

        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.grid(row=2, column=0, pady=20, sticky="n")
        self.center_frame.grid_columnconfigure(0, weight=1)

        self.button_frame_group = ctk.CTkFrame(self.center_frame, fg_color="transparent", corner_radius=10, border_color=Theme.Color.BORDER, border_width=1)
        self.button_frame_group.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        self.button_frame_group.grid_columnconfigure((0, 1), weight=1)

        self.label_group = ctk.CTkLabel(self.button_frame_group, text="Quản Lý", font=AppFont.H3, text_color=self.text_color)
        self.label_group.grid(row=0, column=0, columnspan=2, padx=10, pady=(5, 2), sticky="w")

        self.label_note = ctk.CTkLabel(self.button_frame_group, text="(*) Vui lòng chọn mục bạn muốn quản lý", font=AppFont.BODY, text_color=Theme.Color.TEXT_SUB)
        self.label_note.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="w")

        self.frame_button_left = ctk.CTkFrame(self.button_frame_group, fg_color="transparent")
        self.frame_button_left.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.show_button_group(self.frame_button_left, dataButton_left)

        self.frame_button_right = ctk.CTkFrame(self.button_frame_group, fg_color="transparent")
        self.frame_button_right.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.show_button_group(self.frame_button_right, dataButton_right)
        
        self.info_notify = ctk.CTkFrame(self, fg_color=Theme.Color.BG_CARD)
        self.info_notify.grid(row=2, column=1, padx=(5,10), pady=10, sticky="nsew")
        LabelCustom(self.info_notify, "THÔNG BÁO", font_size=12, font_weight="bold", text_color=Theme.Color.RED_ALERT, pack_pady=0, pack_padx=20)
        LabelCustom(self.info_notify, "Cán bộ giảng viên hãy lưu ý thông báo mới nhất!", font_size=12, pack_pady=0, pack_padx=20, row_pad_y=0, text_color=Theme.Color.TEXT)
        notifies = NotifyList(self.info_notify, data=Db.get_thongbao())
        notifies.pack(fill="both", expand=True, padx=20, pady=20)

    def show_button_group(self, frame, databutton):
        for i, (img_path, text, command) in enumerate(databutton):
            tempFrame = ctk.CTkFrame(frame, fg_color="transparent")
            tempFrame.grid(row=i, column=0, padx=5, pady=8, sticky="ew")
            btn = ButtonTheme(tempFrame, text=text, command=command, font=AppFont.BODY_BOLD, fg_color=Theme.Color.PRIMARY, hover_color=Theme.Color.PRIMARY_HOVER, text_color=Theme.Color.BG, height=60, anchor="w")
            btn.grid(row=0, column=0, padx=8, pady=6, sticky="ew")
            if img_path:
                img = ImageProcessor(img_path).resize(40, 40).to_white_icon().to_ctkimage()
                btn.configure(image=img, compound="left", anchor="w", border_spacing=10); btn.image = img
            tempFrame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    def load_overview_data(self):
        try:
            stats = Db.get_admin_statistics_overview()
            if stats:
                self.card_total_class.update_value(str(stats['tong_so_lop']))
                self.card_total_students.update_value(str(stats['tong_so_sinh_vien']))
                self.card_progress.update_value(f"{stats['tien_do_hoan_thanh']}%")
        except Exception as e: print(f"Lỗi: {e}")

    def show_AdminStudentsManager(self): AdminStudentsManager(master=self, user=self.user).grid(row=0, column=0, rowspan=3, columnspan=2, padx=10, pady=10, sticky="nsew")
    def show_AdminLecturerManager(self): AdminLecturerManager(master=self, user=self.user).grid(row=0, column=0, rowspan=3, columnspan=2, padx=10, pady=10, sticky="nsew")
    def show_AdminAcademic(self): AdminAcademic(master=self, user=self.user).grid(row=0, column=0, rowspan=3, columnspan=2, padx=10, pady=10, sticky="nsew")
    def show_AdminNotice(self): AdminNotice(master=self, user=self.user).grid(row=0, column=0, rowspan=3, columnspan=2, padx=10, pady=10, sticky="nsew")