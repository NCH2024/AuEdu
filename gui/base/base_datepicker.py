import tkinter as tk
import customtkinter as ctk
from datetime import datetime, date 
import calendar # <<< Import calendar ở đây
from tkinter import messagebox

from core.theme_manager import Theme 

class DatePicker(ctk.CTkFrame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        # Entry hiển thị ngày
        self.date_entry = ctk.CTkEntry(self, width=kwargs.get('width', 120)) # Cho phép đặt width
        self.date_entry.grid(row=0, column=0, sticky="ew", padx=(5,0), pady=5) # Giảm padx phải
        # Nút mở lịch
        self.calendar_button = ctk.CTkButton(self, text="▼", width=25, height=25, command=self.open_calendar) # Kích thước nhỏ hơn
        self.calendar_button.grid(row=0, column=1, sticky="w", padx=(1,5), pady=5) # Đặt sticky w
        # Cấu hình grid cho DatePicker frame
        self.grid_columnconfigure(0, weight=1) # Entry co dãn

        # Thuộc tính cơ bản
        self.popup = None
        self.selected_date = None
        self.date_format = "%Y-%m-%d" # Mặc định format SQL
        self.allow_manual_input = True
        # Ngày hiện tại (chỉ để khởi tạo tháng/năm)
        today = datetime.now()
        self.current_year = today.year
        self.current_month = today.month

    def set_date_format(self, date_format):
        # Cập nhật format và hiển thị lại nếu có ngày
        old_format = self.date_format
        self.date_format = date_format
        current_val = self.date_entry.get()
        if current_val:
             try:
                 date_obj = datetime.strptime(current_val, old_format)
                 self.date_entry.delete(0, tk.END)
                 self.date_entry.insert(0, date_obj.strftime(self.date_format))
             except ValueError:
                 self.clear() # Xóa nếu format cũ không parse được

    def set_localization(self, localization):
        import locale
        try:
            locale.setlocale(locale.LC_ALL, localization)
            locale.setlocale(locale.LC_NUMERIC, "C")
        except locale.Error as e:
            print(f"Warning: Could not set locale '{localization}'. {e}")

    def open_calendar(self):
        if self.popup is not None and self.popup.winfo_exists():
             self.popup.destroy()
        self.popup = ctk.CTkToplevel(self)
        self.popup.title("Chọn ngày")
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.popup.geometry(f"+{x}+{y}")
        self.popup.resizable(False, False)
        self.popup.after(100, lambda: self.popup.focus_force())
        self.popup.grab_set()

        current_entry_date = self.get_date_object()
        if current_entry_date:
            self.current_year = current_entry_date.year
            self.current_month = current_entry_date.month
        else:
            today = datetime.now()
            self.current_year = today.year
            self.current_month = today.month

        self.build_calendar()

    def build_calendar(self):
        for widget in self.popup.winfo_children():
             widget.destroy()
        self.calendar_frame = ctk.CTkFrame(self.popup)
        self.calendar_frame.grid(row=0, column=0, padx=5, pady=5)
        header_frame = ctk.CTkFrame(self.calendar_frame)
        header_frame.grid(row=0, column=0, columnspan=7, pady=(0, 5), sticky="ew")
        header_frame.grid_columnconfigure((0, 4), weight=0) # Nút prev/next
        header_frame.grid_columnconfigure((1, 2, 3), weight=1) # Entry month/year/go

        prev_month_button = ctk.CTkButton(header_frame, text="<", width=25, command=self.prev_month)
        prev_month_button.grid(row=0, column=0, padx=(5, 2))
        self.month_entry = ctk.CTkEntry(header_frame, width=40, justify="center")
        self.month_entry.insert(0, str(self.current_month))
        self.month_entry.grid(row=0, column=1, padx=2, sticky='e') # Căn phải entry tháng
        self.year_entry = ctk.CTkEntry(header_frame, width=60, justify="center")
        self.year_entry.insert(0, str(self.current_year))
        self.year_entry.grid(row=0, column=2, padx=2, sticky='w') # Căn trái entry năm
        update_btn = ctk.CTkButton(header_frame, text="Đi", width=25, command=self.update_calendar_from_entry) # Đổi text Go
        update_btn.grid(row=0, column=3, padx=2)
        next_month_button = ctk.CTkButton(header_frame, text=">", width=25, command=self.next_month)
        next_month_button.grid(row=0, column=4, padx=(2, 5))

        days_frame = ctk.CTkFrame(self.calendar_frame)
        days_frame.grid(row=1, column=0, columnspan=7)
        days_short = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"] # Tiếng Việt
        for i, day_name in enumerate(days_short):
            lbl = ctk.CTkLabel(days_frame, text=day_name, width=30, anchor="center") # Tăng width
            lbl.grid(row=0, column=i, padx=1, pady=1)

        month_calendar = calendar.monthcalendar(self.current_year, self.current_month)
        for week_num, week_days in enumerate(month_calendar):
            for day_num, day in enumerate(week_days):
                col_index = (day_num + calendar.MONDAY) % 7 # Điều chỉnh cột theo T2 là đầu tuần
                if day == 0:
                    ctk.CTkLabel(days_frame, text="", width=30).grid(row=week_num + 1, column=col_index) # Tăng width
                else:
                    # ...
                    btn = ctk.CTkButton(
                        days_frame, text=str(day), width=30, height=28,
                        command=lambda d=day: self.select_date(d),
                        fg_color="transparent",
                        
                        text_color=Theme.Color.TEXT, 
                        hover_color=Theme.Color.SECONDARY,
                        border_width=0, corner_radius=4
                    )
                    # ...
                    today = datetime.now()
                    try:
                        current_day_dt = datetime(self.current_year, self.current_month, day)
                        # Highlight ngày được chọn (nếu có)
                        if self.selected_date and current_day_dt.date() == self.selected_date.date():
                            btn.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
                        # Highlight ngày hôm nay (nếu chưa chọn ngày nào)
                        elif current_day_dt.date() == today.date() and not self.selected_date:
                             btn.configure(border_width=1, border_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"])
                    except ValueError:
                         btn.configure(state="disabled")

                    btn.grid(row=week_num + 1, column=col_index, padx=1, pady=1)

    def update_calendar_from_entry(self):
        try:
            month = int(self.month_entry.get())
            year = int(self.year_entry.get())
            if 1 <= month <= 12 and 1900 <= year <= 2100:
                datetime(year, month, 1) # Kiểm tra ngày hợp lệ
                self.current_month = month
                self.current_year = year
                self.build_calendar()
            else:
                raise ValueError("Tháng hoặc năm không hợp lệ")
        except ValueError:
            messagebox.showerror("Lỗi nhập liệu", "Vui lòng nhập tháng (1-12) và năm (1900-2100) hợp lệ.", parent=self.popup)
            self.month_entry.delete(0, tk.END); self.month_entry.insert(0, str(self.current_month))
            self.year_entry.delete(0, tk.END); self.year_entry.insert(0, str(self.current_year))

    def prev_month(self):
        if self.current_month == 1: self.current_month, self.current_year = 12, self.current_year - 1
        else: self.current_month -= 1
        if self.current_year < 1900: self.current_year = 1900
        self.build_calendar()

    def next_month(self):
        if self.current_month == 12: self.current_month, self.current_year = 1, self.current_year + 1
        else: self.current_month += 1
        if self.current_year > 2100: self.current_year = 2100
        self.build_calendar()

    def select_date(self, day):
        try:
            self.selected_date = datetime(self.current_year, self.current_month, day)
            self.date_entry.configure(state="normal")
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, self.selected_date.strftime(self.date_format))
            if not self.allow_manual_input: self.date_entry.configure(state="disabled")
            if self.popup and self.popup.winfo_exists(): self.popup.grab_release(); self.popup.destroy()
            self.popup = None
        except Exception as e:
            print(f"Error selecting date: {e}")
            if self.popup and self.popup.winfo_exists(): self.popup.grab_release(); self.popup.destroy()
            self.popup = None

    def get_date(self): return self.date_entry.get()

    def get_date_object(self):
        date_str = self.date_entry.get()
        if not date_str: return None
        try: return datetime.strptime(date_str, self.date_format)
        except (ValueError, TypeError): return None

    def set_date_obj(self, date_obj):
         # SỬA LỖI isinstance: Dùng `date` trực tiếp
        if date_obj and (isinstance(date_obj, datetime) or isinstance(date_obj, date)):
            if isinstance(date_obj, date) and not isinstance(date_obj, datetime):
                 date_obj = datetime.combine(date_obj, datetime.min.time())
            self.selected_date = date_obj
            self.current_year = date_obj.year
            self.current_month = date_obj.month
            self.date_entry.configure(state="normal")
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, date_obj.strftime(self.date_format))
            if not self.allow_manual_input: self.date_entry.configure(state="disabled")
        else:
            self.clear()

    def clear(self):
        self.selected_date = None
        self.date_entry.configure(state="normal")
        self.date_entry.delete(0, tk.END)
        if not self.allow_manual_input: self.date_entry.configure(state="disabled")

    def set_allow_manual_input(self, value):
        self.allow_manual_input = value
        self.date_entry.configure(state="normal" if value else "disabled")
