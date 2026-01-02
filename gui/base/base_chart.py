import customtkinter as ctk
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib
import calendar
from datetime import datetime
from core.theme_manager import Theme, AppFont, ColorPalette # Import Theme

# Thiết lập backend
matplotlib.use('TkAgg')

# Thiết lập font
plt.rcParams['font.family'] = ['Bahnschrift', 'Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class CircularProgressChart(ctk.CTkFrame):
    """Widget biểu đồ tròn tiến độ"""
    def __init__(self, master, title, value, max_value=100, color=None, 
                 size=(150, 150), font_size=24, **kwargs):
        # SỬA: Background mặc định trong suốt
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.title = title
        self.value = value
        self.max_value = max_value
        # SỬA: Nếu không truyền màu, lấy màu Primary
        self.color = color if color else Theme.Color.PRIMARY
        self.size = size
        self.font_size = font_size
        
        self.create_chart()
    
    def create_chart(self):
        # Lấy chế độ màu hiện tại
        mode = ctk.get_appearance_mode()
        is_dark = mode == "Dark"
        
        # SỬA: Màu nền và màu chữ động
        bg_color = Theme.Color.BG_CARD # Nền trùng với Card
        text_main_color = Theme.Color.TEXT
        text_sub_color = Theme.Color.TEXT_SUB
        track_color = "#2D2D2D" if is_dark else "#E0E0E0" # Vòng tròn nền

        # Tạo figure
        fig = Figure(figsize=(self.size[0]/80, self.size[1]/80), dpi=80)
        fig.patch.set_facecolor(bg_color) # Set nền Figure
        ax = fig.add_subplot(111)
        
        percentage = (self.value / self.max_value) * 100 if self.max_value > 0 else 0
        
        sizes = [percentage, 100 - percentage]
        colors = [self.color, track_color]
        
        wedges, texts = ax.pie(sizes, colors=colors, startangle=90, 
                              counterclock=False, wedgeprops=dict(width=0.3))
        
        # SỬA: Màu chữ trung tâm
        ax.text(0, 0.1, f"{int(percentage)}%", ha='center', va='center', 
               fontsize=self.font_size, fontweight='bold', color=self.color)
        ax.text(0, -0.15, f"{self.value}/{self.max_value}", ha='center', va='center', 
               fontsize=12, color=text_sub_color)
        
        ax.axis('equal')
        # SỬA: Màu chữ tiêu đề
        ax.set_title(self.title, fontsize=12, fontweight='bold', pad=10, color=text_main_color)
        
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        # SỬA: Pack fill và set background cho widget tk
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=bg_color) 
        widget.pack(fill="both", expand=True)

    def destroy(self):
        if self.canvas and self.canvas.get_tk_widget().winfo_exists():
            self.canvas.get_tk_widget().destroy()
        self.canvas = None
        super().destroy()
    
    def update_data(self, value, max_value=None):
        self.value = value
        if max_value is not None:
            self.max_value = max_value
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.create_chart()

class BarChart(ctk.CTkFrame):
    """Widget biểu đồ cột"""
    def __init__(self, master, title, data_dict, color=None, 
                 size=(400, 200), **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.title = title
        self.data_dict = data_dict
        self.color = color if color else Theme.Color.PRIMARY
        self.size = size
        
        self.create_chart()
    
    def create_chart(self):
        mode = ctk.get_appearance_mode()
        is_dark = mode == "Dark"
        
        # SỬA: Màu sắc động
        bg_color = Theme.Color.BG_CARD
        text_color = Theme.Color.TEXT
        
        fig = Figure(figsize=(self.size[0]/80, self.size[1]/80), dpi=80)
        fig.patch.set_facecolor(bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(bg_color) # Set nền trục
        
        labels = list(self.data_dict.keys())
        values = list(self.data_dict.values())
        
        bars = ax.bar(labels, values, color=self.color, alpha=0.7)
        
        # Text value trên cột
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value}', ha='center', va='bottom', 
                   fontweight='bold', color=text_color) # Màu chữ
        
        # SỬA: Màu tiêu đề và nhãn trục
        ax.set_title(self.title, fontsize=14, fontweight='bold', pad=15, color=text_color)
        ax.set_ylabel('Số lượng', color=text_color)
        
        # SỬA: Màu các trục và tick
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(text_color)
        ax.spines['left'].set_color(text_color)
        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        
        ax.grid(True, alpha=0.3, axis='y', color=text_color)
        
        plt.setp(ax.get_xticklabels(), rotation=0, ha="center")
        fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=bg_color)
        widget.pack(fill="both", expand=True)

    def destroy(self):
        if self.canvas and self.canvas.get_tk_widget().winfo_exists():
            self.canvas.get_tk_widget().destroy()
        self.canvas = None
        super().destroy()
    
    def update_data(self, data_dict):
        self.data_dict = data_dict
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.create_chart()

class StatsSummaryCard(ctk.CTkFrame):
    """Widget thẻ tóm tắt thống kê"""
    def __init__(self, master, title, value, subtitle="", 
                 color=None, icon_text="📊", width=200, height=120, **kwargs):
        super().__init__(master, fg_color=Theme.Color.BG, corner_radius=10, 
                        width=width, height=height, **kwargs)
        
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.color = color if color else Theme.Color.PRIMARY
        self.icon_text = icon_text
        
        self.create_card()
    
    def create_card(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # SỬA: Màu text theo Theme
        icon_label = ctk.CTkLabel(main_frame, text=self.icon_text,
                                font=("Arial", 24), text_color=Theme.Color.TEXT)
        icon_label.pack(anchor="w")
        
        value_label = ctk.CTkLabel(main_frame, text=str(self.value),
                                 font=("Bahnschrift", 28, "bold"),
                                 text_color=self.color)
        value_label.pack(anchor="w")
        
        title_label = ctk.CTkLabel(main_frame, text=self.title,
                                 font=("Bahnschrift", 12, "bold"),
                                 text_color=Theme.Color.TEXT_SUB) # Màu phụ
        title_label.pack(anchor="w")
        
        if self.subtitle:
            subtitle_label = ctk.CTkLabel(main_frame, text=self.subtitle,
                                        font=("Bahnschrift", 10),
                                        text_color=Theme.Color.TEXT_SUB)
            subtitle_label.pack(anchor="w")

    def update_value(self, new_value, new_subtitle=""):
        self.value = new_value
        if new_subtitle:
            self.subtitle = new_subtitle
        try:
            if self.winfo_exists():
                for widget in self.winfo_children():
                    widget.destroy()
                self.create_card()
        except tk.TclError:
            pass

class CalendarSchedule(ctk.CTkFrame):
    """Widget lịch hiển thị lịch học"""
    pass