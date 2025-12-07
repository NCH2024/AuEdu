import customtkinter as ctk
import core.database as Db
from core.models import GiangVien
from gui.base.utils import WigdetFrame as WF
from gui.base.utils import LabelCustom as LBL
from gui.base.utils import CustomTable as TB
from gui.base.utils import NotifyList, ImageSlideshow # <<< THÊM IMPORT

class LecturerHome(ctk.CTkFrame):
    def __init__(self, master=None, username=None, **kwargs):
        super().__init__(master, **kwargs)
        self.username = username

        self._border_width = 1
        self._border_color = "white"
        self._fg_color = "white"

         # Lấy thông tin giảng viên
        info_tuple = self.getInfoLecturer(self.username)
        if info_tuple:
            # Chuẩn hóa: tạo object model từ dữ liệu trả về
            self.giangvien = GiangVien(
                MaGV=info_tuple[0],
                TenGiangVien=info_tuple[1],
                SDT=info_tuple[2],
                MaKhoa=info_tuple[3],
                NamSinh=info_tuple[4],
                GhiChu=info_tuple[5]
            )
        else:
            self.giangvien = None
        
        # Lấy lịch điểm danh sơ bộ
        self.data = self.getSchedule(self.username)

        # Biến màu sắc
        self.widget_color = "#2DFCB0"

        # Cấu hình grid tổng thể
        self.grid_rowconfigure((0,1), weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure((0,1,2), weight=1)


        # Tiêu đề
        self.title_widget = ctk.CTkLabel(
            self, text="Dashboard > TRANG CHỦ", 
            font=("Bahnschrift", 20, "bold"), 
            text_color="#05243F"
        )
        self.title_widget.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="nw")

        # Widget chứa thông tin giảng viên
        self.info_lecturer = ctk.CTkFrame(self, fg_color=self.widget_color)
        self.info_lecturer.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        '''Widget con của info_lecturer'''
        self.slogan = LBL(self.info_lecturer, "THÔNG TIN GIẢNG VIÊN", font_size=12, font_weight="bold", text_color="#011EB1", pack_pady=0, pack_padx=20)

        # Kiểm tra dữ liệu
        if self.giangvien:
            self.lbl_name = LBL(self.info_lecturer, "Giảng Viên: ", value=self.giangvien.TenGiangVien, font_weight="bold")
            self.lbl_id = LBL(self.info_lecturer, "Mã cán bộ: ", value=self.giangvien.MaGV, font_weight="bold")
            self.lbl_age = LBL(self.info_lecturer, "Năm sinh: ", value=str(self.giangvien.NamSinh), font_weight="bold")
            self.lbl_numberPhone = LBL(self.info_lecturer, "Số điện thoại: ", value=str(self.giangvien.SDT), font_weight="bold")
            self.lbl_faculty = LBL(self.info_lecturer, "Khoa: ", value=self.giangvien.MaKhoa, font_weight="bold")
            self.lbl_notes = LBL(self.info_lecturer, "Thông tin khác: ", value=self.giangvien.GhiChu, font_weight="italic", value_weight="italic")
        else:
            self.lbl_name = LBL(self.info_lecturer, "Giảng Viên: ", value="Không có dữ liệu", font_weight="bold")
            self.lbl_id = LBL(self.info_lecturer, "Mã cán bộ: ", value="Không có dữ liệu", font_weight="bold")
            self.lbl_age = LBL(self.info_lecturer, "Năm sinh: ", value="Không có dữ liệu", font_weight="bold")
            self.lbl_numberPhone = LBL(self.info_lecturer, "Số điện thoại: ", value="Không có dữ liệu", font_weight="bold")
            self.lbl_faculty = LBL(self.info_lecturer, "Khoa: ", value="Không có dữ liệu", font_weight="bold")
            self.lbl_notes = LBL(self.info_lecturer, "Thông tin khác: ", value="Không có dữ liệu", font_weight="italic", value_weight="italic")

        # Widget xem lịch nhanh điểm danh các lớp được phân công
        self.info_schedule = ctk.CTkFrame(self, fg_color=self.widget_color )
        self.info_schedule.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)
        
        self.slogan = LBL(self.info_schedule, "PHÂN CÔNG ĐIỂM DANH CÁC LỚP", font_size=12, font_weight="bold", text_color="#011EB1", pack_pady=0, pack_padx=20, row_pad_y=0)
        self.slogan_second = LBL(self.info_schedule, "Xem nhanh lịch mà bạn được phân công: ", font_size=13, pack_pady=0, pack_padx=30, row_pad_y=0)
        """Thiết lập bảng hiển thị lịch"""
        # Tạo frame con dùng grid
        self.table_wrapper = ctk.CTkFrame(self.info_schedule, fg_color="transparent")
        self.table_wrapper.pack(padx=20, pady=10, fill="both", expand=True)
        self.table_wrapper.grid_rowconfigure(0, weight=1)

        # Thêm bảng vào frame wrapper
        self.tb_schedule = TB(self.table_wrapper, 
                            columns=["LỚP", "HỌC PHẦN", "HỌC KỲ", "SỐ BUỔI"],
                            column_widths=[100, 200, 80, 70],
                            data=self.data,
                            scroll=True)
        self.tb_schedule.grid(row=0, column=0, sticky="nsew")

        # Cấu hình co giãn
        self.table_wrapper.grid_rowconfigure(0, weight=1)
        self.table_wrapper.grid_columnconfigure(0, weight=1)


        

        # Widget xem thông báo từ cơ quan - nhà trường
        self.info_notify = ctk.CTkFrame(self, fg_color=self.widget_color)
        self.info_notify.grid(row=1, column=1, rowspan=2, padx=(5,10), pady=10, sticky="nsew")
        self.slogan = LBL(self.info_notify, "THÔNG BÁO", font_size=12, font_weight="bold", text_color="#FF0000", pack_pady=0, pack_padx=20)
        self.slogan_second = LBL(self.info_notify, "Cán bộ giảng viên hãy lưu ý thông báo mới nhất!", font_size=12, pack_pady=0, pack_padx=20, row_pad_y=0)
        DataNotify = Db.get_thongbao()
        notifies = NotifyList(self.info_notify, data=DataNotify )
        notifies.pack(fill="both", expand=True, padx=20, pady=20)

    def getInfoLecturer(self, username):
        return Db.get_info_lecturer(username) or None
    
    def getSchedule(self, username):
        data = []
        if Db.get_schedule(username):
            data = Db.get_schedule(username)
            return data
        else:
            return [['','','','']]
