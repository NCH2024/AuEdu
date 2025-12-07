import customtkinter as ctk
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from datetime import datetime
import calendar

# Thiết lập backend cho matplotlib
matplotlib.use('TkAgg')

# Thiết lập font cho matplotlib (sử dụng font có sẵn trong Windows)
plt.rcParams['font.family'] = ['Bahnschrift', 'Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class CircularProgressChart(ctk.CTkFrame):
    """Widget biểu đồ tròn tiến độ với văn bản ở giữa"""
    def __init__(self, master, title, value, max_value=100, color="#4CAF50", 
                 size=(150, 150), font_size=24, **kwargs):
        super().__init__(master, **kwargs)
        
        self.title = title
        self.value = value
        self.max_value = max_value
        self.color = color
        self.size = size
        self.font_size = font_size
        
        self.create_chart()
    
    def create_chart(self):
        # Tạo figure với kích thước nhỏ
        fig = Figure(figsize=(self.size[0]/80, self.size[1]/80), dpi=80)
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        
        # Tính phần trăm
        percentage = (self.value / self.max_value) * 100 if self.max_value > 0 else 0
        
        # Tạo dữ liệu cho biểu đồ tròn
        sizes = [percentage, 100 - percentage]
        colors = [self.color, '#E0E0E0']
        
        # Vẽ biểu đồ tròn với lỗ ở giữa
        wedges, texts = ax.pie(sizes, colors=colors, startangle=90, 
                              counterclock=False, wedgeprops=dict(width=0.3))
        
        # Thêm văn bản ở giữa
        ax.text(0, 0.1, f"{int(percentage)}%", ha='center', va='center', 
               fontsize=self.font_size, fontweight='bold', color=self.color)
        ax.text(0, -0.15, f"{self.value}/{self.max_value}", ha='center', va='center', 
               fontsize=12, color='#666666')
        
        # Ẩn các thành phần không cần thiết
        ax.axis('equal')
        ax.set_title(self.title, fontsize=12, fontweight='bold', pad=10)
        
        # Tạo canvas
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def destroy(self):
        """Hủy bỏ biểu đồ và các tài nguyên liên quan."""
        if self.canvas and self.canvas.get_tk_widget().winfo_exists():
            self.canvas.get_tk_widget().destroy()
        self.canvas = None
        super().destroy()
    
    def update_data(self, value, max_value=None):
        """Cập nhật dữ liệu biểu đồ"""
        self.value = value
        if max_value is not None:
            self.max_value = max_value
        
        # Xóa canvas cũ
        self.canvas.get_tk_widget().destroy()
        # Tạo lại biểu đồ
        self.create_chart()

class BarChart(ctk.CTkFrame):
    """Widget biểu đồ cột"""
    def __init__(self, master, title, data_dict, color="#2196F3", 
                 size=(400, 200), **kwargs):
        super().__init__(master, **kwargs)
        
        self.title = title
        self.data_dict = data_dict  # {"label": value}
        self.color = color
        self.size = size
        
        self.create_chart()
    
    def create_chart(self):
        fig = Figure(figsize=(self.size[0]/80, self.size[1]/80), dpi=80)
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        
        labels = list(self.data_dict.keys())
        values = list(self.data_dict.values())
        
        bars = ax.bar(labels, values, color=self.color, alpha=0.7)
        
        # Thêm giá trị lên đầu cột
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                   f'{value}', ha='center', va='bottom', fontweight='bold')
        
        ax.set_title(self.title, fontsize=14, fontweight='bold', pad=15)
        ax.set_ylabel('Số lượng')
        
        # Cải thiện giao diện
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.setp(ax.get_xticklabels(), rotation=0, ha="center")
        fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def destroy(self):
        """Hủy bỏ biểu đồ và các tài nguyên liên quan."""
        if self.canvas and self.canvas.get_tk_widget().winfo_exists():
            self.canvas.get_tk_widget().destroy()
        self.canvas = None
        super().destroy()
    
    def update_data(self, data_dict):
        """Cập nhật dữ liệu biểu đồ"""
        self.data_dict = data_dict
        self.canvas.get_tk_widget().destroy()
        self.create_chart()

class CalendarSchedule(ctk.CTkFrame):
    def __init__(self, master=None, title=None, month_year=None, 
                 schedule_dates=None, highlight_color="green", **kwargs):
        super().__init__(master, **kwargs)

        self.title = title
        self.highlight_color = highlight_color

        # Luôn là dict
        if isinstance(schedule_dates, dict):
            self.schedule_dates = schedule_dates
        else:
            self.schedule_dates = {}

        if month_year:
            self.current_month, self.current_year = month_year
        else:
            now = datetime.now()
            self.current_month, self.current_year = now.month, now.year

        self.day_widgets = {}

        # header
        self.header = ctk.CTkFrame(self)
        self.header.pack(fill="x", pady=5)

        self.prev_btn = ctk.CTkButton(self.header, text="<", width=40, command=self.prev_month)
        self.prev_btn.pack(side="left", padx=2)

        self.month_label = ctk.CTkLabel(self.header, text="", font=("Arial", 14, "bold"))
        self.month_label.pack(side="left", expand=True)

        self.next_btn = ctk.CTkButton(self.header, text=">", width=40, command=self.next_month)
        self.next_btn.pack(side="right", padx=2)

        self.days_frame = ctk.CTkFrame(self)
        self.days_frame.pack(fill="both", expand=True)

        self.refresh_calendar()

    def set_schedule_dates(self, month, year, dates):
        """Set ngày học cho 1 tháng cụ thể"""
        if not isinstance(self.schedule_dates, dict):
            self.schedule_dates = {}
        self.schedule_dates[(month, year)] = dates
        self.current_month = month
        self.current_year = year
        self.refresh_calendar()

    def refresh_calendar(self):
        for widget in self.days_frame.winfo_children():
            widget.destroy()
        self.day_widgets.clear()

        self.month_label.configure(
            text=f"{calendar.month_name[self.current_month]} {self.current_year}"
        )

        month_key = (self.current_month, self.current_year)
        dates = self.schedule_dates.get(month_key, [])

        cal = calendar.monthcalendar(self.current_year, self.current_month)
        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day == 0:
                    lbl = ctk.CTkLabel(self.days_frame, text="", width=40, height=40)
                else:
                    lbl = ctk.CTkLabel(self.days_frame, text=str(day), width=40, height=40, fg_color="white")
                    self.day_widgets[day] = lbl
                    if day in dates:
                        lbl.configure(fg_color=self.highlight_color, text_color="white")
                lbl.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.refresh_calendar()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.refresh_calendar()

class StatsSummaryCard(ctk.CTkFrame):
    """Widget thẻ tóm tắt thống kê với icon và số liệu"""
    def __init__(self, master, title, value, subtitle="", 
                 color="#2196F3", icon_text="📊", width=200, height=120, **kwargs):
        super().__init__(master, fg_color="white", corner_radius=10, 
                        width=width, height=height, **kwargs)
        
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.color = color
        self.icon_text = icon_text
        
        self.create_card()
    
    def create_card(self):
        # Container chính
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Icon
        icon_label = ctk.CTkLabel(main_frame, text=self.icon_text,
                                font=("Arial", 24))
        icon_label.pack(anchor="w")
        
        # Giá trị chính
        value_label = ctk.CTkLabel(main_frame, text=str(self.value),
                                 font=("Bahnschrift", 28, "bold"),
                                 text_color=self.color)
        value_label.pack(anchor="w")
        
        # Tiêu đề
        title_label = ctk.CTkLabel(main_frame, text=self.title,
                                 font=("Bahnschrift", 12, "bold"),
                                 text_color="#666666")
        title_label.pack(anchor="w")
        
        # Phụ đề (nếu có)
        if self.subtitle:
            subtitle_label = ctk.CTkLabel(main_frame, text=self.subtitle,
                                        font=("Bahnschrift", 10),
                                        text_color="#999999")
            subtitle_label.pack(anchor="w")

    
    def update_value(self, new_value, new_subtitle=""):
        """Cập nhật giá trị"""
        self.value = new_value
        if new_subtitle:
            self.subtitle = new_subtitle
        
        # --- CẢI TIẾN: Cập nhật an toàn hơn để tránh lỗi TclError khi widget bị hủy ---
        try:
            # Kiểm tra xem widget có còn tồn tại không trước khi thao tác
            if self.winfo_exists():
                # Xóa và tạo lại các widget con
                for widget in self.winfo_children():
                    widget.destroy()
                self.create_card()
        except tk.TclError:
            # Bỏ qua lỗi nếu widget đã bị hủy trong quá trình cập nhật
            pass