from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageOps, ImageSequence
import os
from io import BytesIO
import tkinter as tk
from PIL.Image import DecompressionBombError
import threading
from core.utils import get_base_path
import sys
from core.theme_manager import Theme, AppFont
import cv2
import numpy as np

class FullLoadingScreen(ctk.CTkFrame):
    def __init__(self, master, text="Đang khởi tạo hệ thống...", **kwargs):
        super().__init__(master, **kwargs)
        # Phủ kín màn hình cha
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Màu nền đồng bộ với App
        self.configure(fg_color=Theme.Color.BG) 
        
        # Container ở giữa để chứa nội dung
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # 1. Logo hoặc Icon (Nếu em có ảnh logo thì thêm vào đây, tạm thời thầy dùng chữ to)
        # Logo
        base_path = get_base_path()
        try:
            self.bg_ctkimage = ImageProcessor(os.path.join(base_path, "resources","images","logo.png")) \
                                    .crop_to_aspect(467, 213) \
                                    .resize(467, 213) \
                                    .to_ctkimage(size=(467,213))
            self.logo = ctk.CTkLabel(self, image=self.bg_ctkimage, text="")
            self.logo.pack(pady=(30, 20))
        except Exception as e:
            print(f"Lỗi load logo: {e}")
        # self.logo = ctk.CTkLabel(
        #     self.center_frame, 
        #     text="AEDU", 
        #     font=AppFont.H1, 
        #     text_color=Theme.Color.PRIMARY
        # )
        # self.logo.pack(pady=(0, 20))
        
        # 2. Thanh Loading chạy liên tục
        self.progress = ctk.CTkProgressBar(
            self.center_frame, 
            width=300, 
            height=10,
            mode="indeterminate", # Chế độ chạy qua chạy lại (không cần % cụ thể)
            progress_color=Theme.Color.PRIMARY,
            fg_color=Theme.Color.BG_CARD
        )
        self.progress.pack(pady=10)
        self.progress.start() # Bắt đầu chạy
        
        # 3. Dòng chữ thông báo
        self.status_label = ctk.CTkLabel(
            self.center_frame, 
            text=text, 
            font=AppFont.BODY, 
            text_color=Theme.Color.TEXT_SUB
        )
        self.status_label.pack(pady=5)

    def update_status(self, text):
        """Hàm để cập nhật dòng chữ nếu muốn (VD: Đang tải Camera...)"""
        self.status_label.configure(text=text)

class ImageProcessor:
    def __init__(self, image_input):
        """
        Khởi tạo ImageProcessor từ đường dẫn file, bytes, hoặc đối tượng PIL.Image.
        """
        if isinstance(image_input, Image.Image):
            self.image = image_input
        elif isinstance(image_input, bytes):
            self.image = Image.open(BytesIO(image_input))
        else:
            # Mở ảnh và chuyển đổi sang chế độ RGBA để đảm bảo tính nhất quán
            self.image = Image.open(image_input).convert("RGBA")

    def crop_to_aspect(self, target_width, target_height):
        orig_width, orig_height = self.image.size
        target_ratio = target_width / target_height
        orig_ratio = orig_width / orig_height

        if orig_ratio > target_ratio:
            new_width = int(orig_height * target_ratio)
            left = (orig_width - new_width) // 2
            right = left + new_width
            top = 0
            bottom = orig_height
        else:
            new_height = int(orig_width / target_ratio)
            top = (orig_height - new_height) // 2
            bottom = top + new_height
            left = 0
            right = orig_width

        self.image = self.image.crop((left, top, right, bottom))
        return self

    def resize(self, width, height):
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.ANTIALIAS
        self.image = self.image.resize((width, height), resample)
        return self

 # --- PHƯƠNG THỨC MỚI VÀ DUY NHẤT BẠN CẦN GỌI ---
    def resize_and_pad(self, target_width, target_height, background_color=(0, 0, 0, 0)):
        """
        Thay đổi kích thước ảnh để vừa với khung và thêm padding để đạt đúng kích thước cuối cùng.
        - Giữ nguyên tỷ lệ khung hình, không làm méo ảnh.
        - Không cắt xén dữ liệu.
        - Ảnh cuối cùng sẽ có kích thước chính xác là (target_width, target_height).
        - background_color: Tuple (R, G, B, A) cho màu nền. Mặc định là trong suốt.
        """
        # 1. Tính toán kích thước co giãn mà không làm méo
        orig_width, orig_height = self.image.size
        if orig_width == 0 or orig_height == 0:
            # Nếu ảnh không hợp lệ, tạo ảnh nền trống
            self.image = Image.new('RGBA', (target_width, target_height), background_color)
            return self

        width_ratio = target_width / orig_width
        height_ratio = target_height / orig_height
        scale_ratio = min(width_ratio, height_ratio)

        new_width = int(orig_width * scale_ratio)
        new_height = int(orig_height * scale_ratio)

        # 2. Co giãn ảnh về kích thước mới bằng thuật toán làm mịn ảnh tốt nhất
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.ANTIALIAS
        resized_image = self.image.resize((new_width, new_height), resample)

        # 3. Tạo một ảnh nền mới với kích thước đích và màu nền
        # Chế độ 'RGBA' là quan trọng để hỗ trợ màu trong suốt
        new_background = Image.new('RGBA', (target_width, target_height), background_color)

        # 4. Tính toán vị trí để dán ảnh đã co giãn vào giữa ảnh nền
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2

        # 5. Dán ảnh lên nền.
        # Tham số thứ 3 (mask) là chính ảnh đã co giãn để xử lý độ trong suốt đúng cách
        new_background.paste(resized_image, (paste_x, paste_y), resized_image)

        # 6. Cập nhật ảnh của đối tượng thành ảnh đã được xử lý hoàn chỉnh
        self.image = new_background
        return self

    def to_ctkimage(self, size=None):
        """
        Chuyển đổi PIL Image thành CTkImage.
        Lưu ý: Khi dùng với resize_and_pad, không cần truyền 'size' nữa.
        """
        final_size = size if size else self.image.size
        return ctk.CTkImage(light_image=self.image, dark_image=self.image, size=final_size)

    def to_photoimage(self):
        return ImageTk.PhotoImage(self.image)

    def save(self, path):
        self.image.save(path)

    def get_pil_image(self):
        return self.image
    
    # (Code này nằm trong class ImageProcessor, file gui/base/utils.py)

    def save_to_dir(self, filename, directory="image_student"):  
        # SỬA LỖI: Luôn sử dụng get_base_path() làm gốc
        base_path = get_base_path()
        # Nối đường dẫn gốc với thư mục mặc định
        full_directory_path = os.path.join(base_path, directory)

        # Phần còn lại giữ nguyên
        if not os.path.exists(full_directory_path):
            os.makedirs(full_directory_path)

        full_path = os.path.join(full_directory_path, filename)
        self.image.save(full_path)
        return full_path
    
    def to_white_icon(self):
        """
        Chuyển toàn bộ vùng có màu (alpha > 0) thành trắng, giữ nguyên độ trong suốt.
        """
        # Đảm bảo ảnh ở chế độ RGBA
        img = self.image.convert("RGBA")
        datas = img.getdata()
        new_data = []
        for item in datas:
            r, g, b, a = item
            # nếu pixel có độ trong suốt khác 0, đổi màu về trắng
            if a > 0:
                new_data.append((255, 255, 255, a))
            else:
                new_data.append((r, g, b, a))
        img.putdata(new_data)
        self.image = img
        return self

class ImageSlideshow(ctk.CTkFrame):
    def __init__(self, master, image_folder, delay=3000, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.grid_propagate(False)
        self.pack_propagate(False)

        self.image_folder = image_folder
        self.delay = delay
        self.current_idx = 0
        self.files = []
        
        self.job_id = None
        self.video_cap = None 
        self.is_playing_video = False
        self.current_size = (0, 0)
        
        # Biến lưu tham số crop để không phải tính lại mỗi frame (Tối ưu hiệu năng)
        self.crop_params = None 
        
        self.load_files()
        
        self.label = ctk.CTkLabel(self, text="", fg_color="transparent")
        self.label.pack(expand=True, fill="both")
        
        self.create_nav_buttons()
        self.bind("<Configure>", self.on_resize)
        
        if self.files:
            self.show_slide(0)

    def load_files(self):
        valid_img = {".png", ".jpg", ".jpeg", ".gif"}
        valid_video = {".mp4", ".avi", ".mov", ".mkv"}
        if os.path.exists(self.image_folder):
            for f in sorted(os.listdir(self.image_folder)):
                ext = os.path.splitext(f)[1].lower()
                if ext in valid_img or ext in valid_video:
                    self.files.append(f)

    def create_nav_buttons(self):
        if not self.files: return
        style = {
            "width": 30, "height": 30, "corner_radius": 0,
            "bg_color": Theme.Color.BG_CARD,
            "fg_color": Theme.Color.BG_CARD, "text_color": Theme.Color.TEXT,
            "hover_color": Theme.Color.PRIMARY, "font": AppFont.H2
        }
        self.btn_prev = ctk.CTkButton(self, text="<", command=self.prev_slide, **style)
        self.btn_prev.place(relx=0.02, rely=0.5, anchor="w")
        self.btn_next = ctk.CTkButton(self, text=">", command=self.next_slide, **style)
        self.btn_next.place(relx=0.98, rely=0.5, anchor="e")

    def on_resize(self, event):
        if event.width < 10 or event.height < 10: return
        self.current_size = (event.width, event.height)
        
        # Tính toán lại tham số crop ngay khi resize
        self.recalc_crop_params()
        
        if not self.is_playing_video:
            self.show_current_static_image()

    def recalc_crop_params(self):
        """Tính toán trước tham số resize/crop để dùng cho OpenCV"""
        if self.current_size == (0, 0): return

        target_w, target_h = self.current_size
        img_w, img_h = 0, 0

        # Lấy kích thước nguồn
        if self.is_playing_video and self.video_cap:
            img_w = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            img_h = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        elif self.files:
            pass

        if img_w == 0 or img_h == 0: return

        # Thuật toán Cover (Lấp đầy)
        ratio = max(target_w / img_w, target_h / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        
        # Tọa độ cắt giữa
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        
        # Lưu lại: (width mới, height mới, x_cat, y_cat, width_cat, height_cat)
        self.crop_params = (new_w, new_h, left, top, target_w, target_h)

    def show_slide(self, idx):
        self.cleanup_current_slide()
        
        idx = idx % len(self.files)
        self.current_idx = idx
        f = self.files[idx]
        path = os.path.join(self.image_folder, f)
        ext = os.path.splitext(f)[1].lower()
        
        if ext in {".mp4", ".avi", ".mov", ".mkv"}:
            self.is_playing_video = True
            self.video_cap = cv2.VideoCapture(path)
            self.recalc_crop_params() # Tính toán crop cho video mới
            self.play_video_frame()
        else:
            self.is_playing_video = False
            self.show_current_static_image()
            self.job_id = self.after(self.delay, self.next_slide)

    def play_video_frame(self):
        if not self.video_cap or not self.video_cap.isOpened():
            self.next_slide()
            return

        ret, frame = self.video_cap.read()
        if not ret:
            self.next_slide()
            return
            
        # --- TỐI ƯU HÓA BẰNG OPENCV (NHANH HƠN 10 LẦN PIL) ---
        if self.crop_params:
            new_w, new_h, left, top, target_w, target_h = self.crop_params
            
            # 1. Resize bằng OpenCV (Cực nhanh)
            # Chỉ resize nếu kích thước khác biệt đáng kể
            if frame.shape[1] != new_w or frame.shape[0] != new_h:
                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # 2. Crop bằng Numpy Slicing (Tức thì)
            # Cắt lấy vùng giữa: frame[y:y+h, x:x+w]
            frame = frame[top:top+target_h, left:left+target_w]
        
        # 3. Convert BGR -> RGB để hiển thị đúng màu
        # OpenCV dùng BGR, Tkinter dùng RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 4. Tạo Image và hiển thị
        pil_img = Image.fromarray(frame)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
        
        self.label.configure(image=ctk_img)
        self.label.image = ctk_img # Giữ tham chiếu
        
        # Lặp lại sau 33ms (~30 FPS)
        self.job_id = self.after(33, self.play_video_frame)

    def show_current_static_image(self):
        if self.current_size == (0, 0): return
        f = self.files[self.current_idx]
        path = os.path.join(self.image_folder, f)
        
        try:
            # Với ảnh tĩnh, dùng ImageOps.fit của PIL vẫn đủ nhanh và tiện
            pil_img = Image.open(path)
            w, h = self.current_size
            fitted_img = ImageOps.fit(pil_img, (w, h), method=Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=fitted_img, dark_image=fitted_img, size=(w, h))
            self.label.configure(image=ctk_img)
            self.label.image = ctk_img
        except Exception: pass

    def cleanup_current_slide(self):
        if self.job_id:
            self.after_cancel(self.job_id)
            self.job_id = None
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
        self.is_playing_video = False

    def next_slide(self):
        self.show_slide(self.current_idx + 1)

    def prev_slide(self):
        self.show_slide(self.current_idx - 1)

    def destroy(self):
        self.cleanup_current_slide()
        super().destroy()
             
class WigdetFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        width=100, 
        height=100, 
        radius=20,
        widget_color=Theme.Color.BG_CARD,
        row=0,
        column=0,
        rowspan=1,
        columnspan=1,
        sticky="n",  # mặc định canh trên
        padx=10,
        pady=10,
        grid_propagate=True,
        **kwargs
    ):
        super().__init__(master, width=width, height=height, corner_radius=radius, fg_color=widget_color, **kwargs)

        self.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, sticky=sticky, padx=padx, pady=pady)
        self.grid_propagate(grid_propagate) 


class ButtonTheme(ctk.CTkButton):
    def __init__(
        self,
        master,
        text,
        font=None,             
        fg_color=None,         
        hover_color=None,
        text_color=None,       
        border_color=None,
        border_width=0,
        height=40,
        width=150,             
        image=None,  
        command=None,
        corner_radius=10,
        **kwargs
    ):
        if font is None: font = AppFont.BODY_BOLD
        if fg_color is None: fg_color = Theme.Color.PRIMARY
        if border_color is None: border_color = Theme.Color.BORDER

        # Lấy màu Hover chuẩn từ Theme thay vì dùng Secondary
        if hover_color is None:
            hover_color = Theme.Color.PRIMARY_HOVER 
        # --------------------

        # Logic màu chữ tương phản (giữ nguyên cái nãy thầy chỉ)
        if text_color is None:
            text_color = Theme.Color.BG 

        super().__init__(
            master=master,
            text=text,
            font=font,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            border_color=border_color,
            border_width=border_width,
            height=height,
            width=width,
            image=image,  
            command=command,
            corner_radius=corner_radius,
            **kwargs
        )

# Trong gui/base/utils.py

class ComboboxTheme(ctk.CTkComboBox):
    def __init__(
        self,
        master,
        values=[],
        command=None,
        font=None,
        fg_color=None,
        border_color=None,
        border_width=1,
        button_color=None,
        button_hover_color=None,
        dropdown_fg_color=None, 
        dropdown_text_color=None,
        dropdown_hover_color=None,
        text_color=None,
        **kwargs
    ):
        if font is None: font = AppFont.BODY
        
        # 1. Nền ô nhập (Input): BG_CARD
        if fg_color is None: fg_color = Theme.Color.BG_CARD         
        
        # 2. Viền ngoài: BORDER (Trắng/Xám)
        if border_color is None: border_color = Theme.Color.BORDER  

        # 3. Nút Mũi Tên
        if button_color is None: 
            button_color = Theme.Color.SECONDARY
            
        if button_hover_color is None: 
            button_hover_color = Theme.Color.PRIMARY_HOVER 
        
        if text_color is None: text_color = Theme.Color.TEXT
        
        # Dropdown
        if dropdown_fg_color is None: dropdown_fg_color = Theme.Color.BG_CARD
        if dropdown_text_color is None: dropdown_text_color = Theme.Color.TEXT
        if dropdown_hover_color is None: dropdown_hover_color = Theme.Color.SECONDARY 
        
        super().__init__(
            master=master,
            values=values,
            font=font,
            fg_color=fg_color,
            border_color=border_color,
            border_width=border_width,
            button_color=button_color,
            button_hover_color=button_hover_color,
            dropdown_fg_color=dropdown_fg_color,
            dropdown_text_color=dropdown_text_color,
            dropdown_hover_color=dropdown_hover_color,
            text_color=text_color,
            command=command,
            **kwargs
        )

class Tooltip:
    def __init__(self, widget, text, delay=200):
        self.widget = widget
        self.text = text
        self.delay = delay  # milliseconds
        self.tooltip_window = None
        self.task_id = None

        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.task_id:
            self.widget.after_cancel(self.task_id)
        self.task_id = self.widget.after(self.delay, self._show)

    def _show(self):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Loại bỏ thanh tiêu đề và viền
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(self.tooltip_window, text=self.text, fg_color="white", bg_color="white", corner_radius=0)
        label.pack(padx=5, pady=5)

    def hide_tooltip(self, event=None):
        if self.task_id:
            self.widget.after_cancel(self.task_id)
            self.task_id = None
        if self.tooltip_window:
            self.tooltip_window.destroy()

class LabelCustom(ctk.CTkFrame):
    def __init__(self, master, text, value=None, 
                 text_color=None, value_color=None, # Cho phép None để lấy mặc định
                 font_family=AppFont.NAME, # Dùng font từ config
                 font_size=16, font_weight="bold", value_weight="normal",
                 wraplength=300, row_pad_y=2, pack_pady=1, pack_padx=25, pack_anchor="w", 
                 fg_color="transparent", **kwargs):
        
        super().__init__(master, fg_color=fg_color, **kwargs)

        # Logic chọn màu thông minh
        if text_color is None: text_color = Theme.Color.TEXT
        if value_color is None: value_color = Theme.Color.PRIMARY # Giá trị nổi bật bằng màu chủ đạo

        # Tạo font object
        label_font = (font_family, font_size, font_weight)
        value_font = (font_family, font_size, value_weight)

        # Label bên trái
        self.label = ctk.CTkLabel(self, text=text, font=label_font, text_color=text_color,
                                  wraplength=wraplength, fg_color="transparent", anchor="w")
        self.label.grid(row=0, column=0, sticky="nw", padx=(0, 10), pady=row_pad_y)

        # Label giá trị bên phải
        if value:
            self.value = ctk.CTkLabel(self, text=value, font=value_font, text_color=value_color,
                                      wraplength=wraplength, fg_color="transparent", justify="left", anchor="w")
            self.value.grid(row=0, column=1, sticky="nw", pady=row_pad_y)

        self.pack(pady=pack_pady, padx=pack_padx, anchor=pack_anchor)

    def set_text(self, text):
        self.label.configure(text=text)

class CustomTable(ctk.CTkFrame):
    """
    Bảng dữ liệu tuỳ chỉnh dùng widget của CustomTkinter để có thể:
    - Bo viền từng ô (Border).
    - Đổi màu chuẩn theo Theme (Sáng/Tối).
    """
    def __init__(self, master, columns, column_widths=None, data=None, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.columns = columns
        self.column_widths = column_widths if column_widths else [100] * len(columns)
        self.command = command # Hàm callback khi click vào dòng (nếu cần)
        self.rows = [] # Chứa các widget dòng
        
        # --- CẤU HÌNH MÀU SẮC TỪ THEME ---
        self.header_color = Theme.Color.PRIMARY
        self.header_text_color = Theme.Color.BG 
        self.cell_bg_color = Theme.Color.BG_CARD
        self.cell_text_color = Theme.Color.TEXT
        self.border_color = Theme.Color.BORDER
        
        # --- 1. HEADER (Tiêu đề cột) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.header_frame.pack(fill="x", anchor="n")
        
        for i, col_name in enumerate(self.columns):
            # Dùng CTkButton với hover=False để giả làm Label có viền và nền đẹp
            width = self.column_widths[i] if i < len(self.column_widths) else 100
            
            lbl = ctk.CTkButton(
                self.header_frame, 
                text=col_name,
                font=AppFont.BODY_BOLD,
                text_color=self.header_text_color,
                fg_color=self.header_color,
                hover=False,              # Không hiệu ứng hover
                corner_radius=0,          # Vuông vức
                width=width,
                height=35,
                border_width=1,           # Có viền
                border_color=self.border_color
            )
            # Nếu là cột cuối thì cho dãn ra
            if i == len(self.columns) - 1:
                lbl.pack(side="left", fill="x", expand=True, padx=(0,0))
            else:
                lbl.pack(side="left", padx=(0,0)) # padx=0 để các ô dính liền nhau tạo border chung

        # --- 2. BODY (Nội dung bảng - Cuộn được) ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_frame.pack(fill="both", expand=True)
        
        # Load dữ liệu ban đầu
        if data:
            self.update_data(data)

    def update_data(self, data):
        """
        Cập nhật dữ liệu mới cho bảng.
        data: List các tuple/list giá trị. Ví dụ: [("SV01", "A"), ("SV02", "B")]
        """
        # 1. Xóa dữ liệu cũ
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.rows.clear()
        
        if not data:
            return

        # 2. Vẽ dữ liệu mới
        for row_idx, row_data in enumerate(data):
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", corner_radius=0)
            row_frame.pack(fill="x", anchor="n")
            self.rows.append(row_frame)
            
            for col_idx, cell_value in enumerate(row_data):
                if col_idx >= len(self.columns): break # Tránh lỗi index
                
                width = self.column_widths[col_idx] if col_idx < len(self.column_widths) else 100
                
                # Dùng CTkButton giả làm ô dữ liệu (Cell)
                # Lý do: CTkLabel không hỗ trợ border_width tốt bằng CTkButton
                cell = ctk.CTkButton(
                    row_frame,
                    text=str(cell_value),
                    font=AppFont.BODY,
                    text_color=self.cell_text_color,
                    fg_color=self.cell_bg_color, # Màu nền ô
                    hover=False,                 # Tắt hover để giống label tĩnh
                    corner_radius=0,
                    width=width,
                    height=30,
                    border_width=1,              # VIỀN TỪNG Ô
                    border_color=self.border_color,
                    anchor="w"                   # Căn trái chữ
                )
                # Thêm padding text chút cho đẹp
                if cell._text_label:
                    cell._text_label.grid_configure(padx=5)
                
                if col_idx == len(self.columns) - 1:
                    cell.pack(side="left", fill="x", expand=True)
                else:
                    cell.pack(side="left")
                
class NotifyCard(ctk.CTkFrame):
    def __init__(self, master, title, content,
                 ngay_dang, 
                 image_pil, 
                 fg_color=None,
                 on_click=None, 
                 height=150, 
                 width=250, 
                text_btn="Xem chi tiết", **kwargs):
        
        super().__init__(master, corner_radius=15, **kwargs)
        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            fg_color = Theme.Color.BG_CARD
        else:
            fg_color = Theme.Color.BG
        self.configure(fg_color=fg_color)
        if image_pil:
            img = ImageProcessor(image_pil).crop_to_aspect(4, 3).to_ctkimage(size=(width, height))
        else:
            img = None

        self.image_label = ctk.CTkLabel(self, image=img, text="", width=width, height=height, corner_radius=10)
        self.image_label.image = img
        self.image_label.grid(row=0, column=0, rowspan=3, padx=0, pady=0)

        # SỬA: Dùng text_color từ Theme (RED_ALERT hoặc DANGER)
        self.title_label = ctk.CTkLabel(self, text=title, font=AppFont.H4, 
                                        text_color=Theme.Color.TEXT, wraplength=470)
        self.title_label.grid(row=0, column=1, sticky="w", padx=20, pady=(10, 0))

        # SỬA: Dùng TEXT_SUB cho ngày tháng
        self.date_label = ctk.CTkLabel(self, text=ngay_dang.strftime("%d/%m/%Y %H:%M"), 
                                       font=AppFont.BODY, text_color=Theme.Color.TEXT_SUB)
        self.date_label.grid(row=1, column=1, sticky="w", padx=20, pady=2)
        
        # SỬA: ButtonTheme mặc định đã có màu chuẩn, nhưng nếu dùng CTkButton thường thì nên set màu
        self.detail_btn = ctk.CTkButton(self, text=text_btn, command=on_click,
                                        fg_color=Theme.Color.PRIMARY, 
                                        hover_color=Theme.Color.PRIMARY_HOVER,
                                        text_color=Theme.Color.BG)
        self.detail_btn.grid(row=2, column=1, sticky="w", padx=20, pady=(5, 5))
        
    def set_up_button(self, fg_color, hover_color, text_color, border_color, border_width):
        self.detail_btn.configure(fg_color = fg_color, hover_color = hover_color, text_color = text_color, border_color = border_color, border_width = border_width)
            



class NotifyList(ctk.CTkFrame):
    def __init__(self, master, data, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", width=680, height=600)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for tb in data:
            thongbao_id, title, content, ngay_dang, image_pil = tb
            card = NotifyCard(scroll_frame, title=title, content=content, ngay_dang=ngay_dang, image_pil=image_pil,
                              on_click=lambda c=content, t=title: self.show_detail(t, c))
            card.pack(fill="x", padx=5, pady=5)
            
    def show_detail(self, title, content):
        top = ctk.CTkToplevel(self)
        top.geometry("600x600")
        top.title(title)
        top.lift() 
        top.focus_force()
        top.attributes("-topmost", True)

        ctk.CTkLabel(top, text=title, font=AppFont.H4, text_color=Theme.Color.TEXT, wraplength=500).pack(pady=10)
        ctk.CTkLabel(top, text=content, font=AppFont.BODY, text_color=Theme.Color.TEXT_SUB, wraplength=450, justify="left").pack(pady=10)

class SliderWithLabel(ctk.CTkFrame):
    def __init__(self, master, label_text, from_=0, to=1, initial=0.5, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.is_integer_slider = isinstance(from_, int) and isinstance(to, int)
        
        # SỬA: Lưu màu từ Theme thay vì mã Hex cứng
        self.label_color = Theme.Color.TEXT
        self.value_color = Theme.Color.SUCCESS  # Màu cho các con số (VD: Xanh lá/Mint)

        self.label = ctk.CTkLabel(self, text=label_text, text_color=self.label_color, font=("Bahnschrift", 14))
        self.label.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 0))

        self.min_label = ctk.CTkLabel(self, text=str(from_), font=AppFont.BODY, text_color=self.value_color)
        self.min_label.grid(row=1, column=0, sticky="w", padx=(10, 5))

        if self.is_integer_slider:
            steps = to - from_
        else:
            steps = 100

        # SỬA: Progress color và Button color theo Theme
        self.slider = ctk.CTkSlider(
            self, from_=from_, to=to, number_of_steps=steps,
            command=self.update_label, height=15, 
            progress_color=Theme.Color.PRIMARY,       # Màu thanh đã trượt
            button_color=Theme.Color.PRIMARY,         # Màu nút tròn
            button_hover_color=Theme.Color.PRIMARY_HOVER
        )
        self.slider.grid(row=1, column=1, sticky="ew", padx=5)

        self.max_label = ctk.CTkLabel(self, text=str(to), font=AppFont.BODY, text_color=self.value_color)
        self.max_label.grid(row=1, column=2, sticky="e", padx=(5, 10))

        self.value_label = ctk.CTkLabel(self, text="", text_color=self.value_color, font=AppFont.BODY_BOLD)
        self.value_label.grid(row=2, column=0, columnspan=3, pady=(2, 10))

        self.grid_columnconfigure(1, weight=1)
        self.command = command
        
        self.set_value(initial)

    def configure(self, **kwargs):
        if "state" in kwargs:
            new_state = kwargs.pop("state")
            self.slider.configure(state=new_state)

            if new_state == "disabled":
                disabled_color = Theme.Color.TEXT_SUB # Dùng màu phụ (xám)
                self.label.configure(text_color=disabled_color)
                self.min_label.configure(text_color=disabled_color)
                self.max_label.configure(text_color=disabled_color)
                self.value_label.configure(text_color=disabled_color)
            else:
                self.label.configure(text_color=self.label_color)
                self.min_label.configure(text_color=self.value_color)
                self.max_label.configure(text_color=self.value_color)
                self.value_label.configure(text_color=self.value_color)

        super().configure(**kwargs)

    def update_label(self, value):
        if self.is_integer_slider:
            processed_value = round(value)
            self.value_label.configure(text=f"{processed_value}")
        else:
            processed_value = round(value, 2)
            self.value_label.configure(text=f"{processed_value:.2f}")

        if self.command:
            self.command(processed_value)

    def get_value(self):
        current_value = self.slider.get()
        if self.is_integer_slider:
            return round(current_value)
        else:
            return round(current_value, 2)

    def set_value(self, value):
        self.slider.set(value)
        self.update_label(value)
class SwitchOption(ctk.CTkFrame):
    def __init__(self, master, text, initial=True, command=None, wraplenght=500, 
                 text_color=None, # Cho phép truyền vào, nếu không thì lấy Theme
                 font=AppFont.BODY, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # SỬA: Lấy mặc định từ Theme
        if text_color is None: text_color = Theme.Color.TEXT
        
        self.label = ctk.CTkLabel(self, text=text, text_color=text_color, font=font, wraplength=wraplenght, anchor="w", justify="left")
        self.label.pack(side="left", padx=(10, 5), pady=5)

        # SỬA: progress_color lấy từ SUCCESS (Màu xanh thành công)
        self.switch = ctk.CTkSwitch(self, text="BẬT" if initial else "TẮT", 
                                    progress_color=Theme.Color.SUCCESS, 
                                    font=font, text_color=text_color)
        self.switch.select() if initial else self.switch.deselect()
        self.switch.pack(side="right", padx=10)

        def on_toggle():
            self.switch.configure(text="BẬT" if self.switch.get() else "TẮT")
            if command:
                command(self.switch.get())

        self.switch.configure(command=on_toggle)

    def get_value(self):
        return self.switch.get()

    def set_value(self, value: bool):
        if value:
            self.switch.select()
        else:
            self.switch.deselect()
        self.switch.configure(text="BẬT" if value else "TẮT")

class LoadingDialog(ctk.CTkToplevel):
    def __init__(self, 
                 parent, 
                 message="Đang xử lý...", 
                 progress_color=None, # Cho phép None để lấy mặc định
                 mode="determinate", 
                 height_progress=18,
                 temp_topmost_off: bool = False):
        
        super().__init__(parent)
        self.geometry("500x200")
        self.title("")
        self.resizable(False, False)
        self.overrideredirect(True)
        
        # --- SỬA MÀU THEO THEME ---
        bg_color = Theme.Color.BG_CARD
        text_color = Theme.Color.TEXT
        p_color = progress_color if progress_color else Theme.Color.PRIMARY
        # --------------------------

        self.configure(bg=bg_color, fg_color=bg_color)
        self.attributes("-transparentcolor", "#F2F2F2") 
        self.attributes("-alpha", 0.95)
        self.attributes("-topmost", True)
        self.grab_set()

        # Container
        self.container = ctk.CTkFrame(self, corner_radius=20, fg_color=bg_color) # Dùng màu Theme
        self.container.pack(expand=True, fill="both", padx=20, pady=20)

        # Label
        self.label = ctk.CTkLabel(
            self.container,
            text=message,
            font=AppFont.H3, # Dùng Font mới
            text_color=text_color # Dùng màu Theme
        )
        self.label.pack(pady=(30, 20))

        # ProgressBar
        self.progressbar = ctk.CTkProgressBar(
            self.container,
            width=400,
            height=height_progress,
            corner_radius=10,
            progress_color=p_color,
            fg_color=Theme.Color.BORDER, # Màu nền thanh progress
            mode=mode
        )
        self.progressbar.pack(pady=(0, 10))

        if mode == "determinate":
            self.progressbar.set(0)
        else:  # indeterminate
            self.progressbar.start()

        self.center_window(parent)

        # <-- THÊM MỚI: Lên lịch tắt topmost sau 1 giây
        if temp_topmost_off:
            self.after(1000, self._disable_topmost)

    def _disable_topmost(self):
        """(Mới) Tắt chế độ luôn hiển thị trên cùng."""
        try:
            self.attributes("-topmost", False)
            print("Đã tắt topmost.") # Thêm để debug
        except Exception:
            # Cửa sổ có thể đã bị hủy trước khi hàm này được gọi
            pass

    def update_progress(self, value: float):
        """Cập nhật tiến trình cho determinate."""
        try:
            if self.progressbar._mode == "determinate" and 0 <= value <= 1:
                self.progressbar.set(value)
        except Exception:
            pass

    def stop(self):
        """Dừng và hủy dialog."""
        try:
            if self.progressbar._mode == "indeterminate":
                self.progressbar.stop()
        except Exception:
            pass
        
        self.grab_release() # <-- Nhớ giải phóng grab
        self.destroy()

    def center_window(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

def resize_crop_to_fill(image, target_width, target_height):
    """Resize hình ảnh để *lấp đầy* khung mà không méo hình (giữ tỷ lệ), có thể bị cắt 2 bên"""
    img_ratio = image.width / image.height
    target_ratio = target_width / target_height

    if img_ratio > target_ratio:
        # Hình rộng hơn khung ➝ cắt 2 bên
        new_height = target_height
        new_width = int(new_height * img_ratio)
    else:
        # Hình cao hơn khung ➝ cắt trên dưới
        new_width = target_width
        new_height = int(new_width / img_ratio)

    resized_img = image.resize((new_width, new_height), Image.LANCZOS)

    # Cắt phần thừa để vừa khít khung
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    return resized_img.crop((left, top, right, bottom))



class ToastNotification(ctk.CTkToplevel):
    def __init__(self, parent, message, duration=2000):
        super().__init__(parent)
        self.duration = duration
        self.opacity = 0.0
        self.offset_y = 50  # ban đầu toast sẽ lệch xuống dưới
        
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", self.opacity)

        self.configure(fg_color=Theme.Color.PRIMARY, padx=10, pady=5, corner_radius=15)

        # Label nội dung
        self.label = ctk.CTkLabel(self, text=message, text_color=Theme.Color.SECONDARY, font=AppFont.H6, corner_radius=20)
        self.label.pack(padx=15, pady=10)

        self.update_idletasks()
        self.toast_width = self.winfo_reqwidth()
        self.toast_height = self.winfo_reqheight()

        # Lấy vị trí gốc của parent
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()

        # Đặt vị trí ban đầu (ẩn một chút bên dưới)
        self.target_x = parent_x + parent_w - self.toast_width - 20
        self.target_y = parent_y + parent_h - self.toast_height - 20
        self.geometry(f"{self.toast_width}x{self.toast_height}+{self.target_x}+{self.target_y + self.offset_y}")

        # Bắt đầu hiệu ứng
        self.animate_in()

    def animate_in(self):
        if self.opacity < 1.0 or self.offset_y > 0:
            self.opacity = min(1.0, self.opacity + 0.1)
            self.offset_y = max(0, self.offset_y - 5)

            self.attributes("-alpha", self.opacity)
            self.geometry(f"{self.toast_width}x{self.toast_height}+{self.target_x}+{self.target_y + self.offset_y}")
            self.after(20, self.animate_in)
        else:
            self.after(self.duration, self.animate_out)

    def animate_out(self):
        if self.opacity > 0:
            self.opacity = max(0.0, self.opacity - 0.05)
            self.attributes("-alpha", self.opacity)
            self.after(20, self.animate_out)
        else:
            self.destroy()
            
class CollapsibleFrame(ctk.CTkFrame):
    def __init__(self, master, title="", color=None, controller=None, **kwargs):
        # SỬA: Mặc định color là trong suốt hoặc BG_CARD
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.title = title
        self.controller = controller
        self.is_expanded = False
        
        # Nếu không truyền color, dùng BG_CARD cho header nổi bật
        self.color = color if color else Theme.Color.BG_CARD

        self.header_frame = ctk.CTkFrame(self, fg_color=self.color, corner_radius=10, cursor="hand2")
        self.header_frame.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame, text=self.title, font=AppFont.H3, 
            text_color=Theme.Color.TEXT, cursor="hand2"
        )
        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # SỬA: Nút mũi tên dùng màu Theme
        self.toggle_button = ctk.CTkButton(
            self.header_frame, text="⇣", font=AppFont.H3, width=30, height=30,
            fg_color=Theme.Color.SECONDARY,          # Màu nền nút
            text_color=Theme.Color.TEXT,             # Màu mũi tên
            hover_color=Theme.Color.PRIMARY_HOVER,   # Màu khi hover
            command=None, cursor="hand2"
        )
        self.toggle_button.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        # SỬA: Content frame cũng nên theo màu nền được truyền vào
        self.content_frame = ctk.CTkFrame(self, fg_color=self.color, corner_radius=10)

        self.header_frame.bind("<Button-1>", self.toggle_event)
        self.title_label.bind("<Button-1>", self.toggle_event)
        self.toggle_button.bind("<Button-1>", self.toggle_event)

    def toggle_event(self, event=None):
        self.toggle()

    def toggle(self):
        if self.is_expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        self.is_expanded = True
        self.toggle_button.configure(text="⇡")
        self.content_frame.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="nsew")
        if self.controller:
            self.controller.on_expand(self)

    def collapse(self):
        self.is_expanded = False
        self.toggle_button.configure(text="⇣")
        self.content_frame.grid_forget()
