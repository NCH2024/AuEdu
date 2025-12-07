import customtkinter as ctk
from PIL import Image, ImageSequence, ImageTk
import os
from io import BytesIO
import tkinter as tk
from PIL.Image import DecompressionBombError
import threading
from core.utils import get_base_path
import sys


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
    def __init__(self, master, image_folder, size=(500, 300), delay=2000, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.size = size
        self.delay = delay
        self._fg_color = "transparent"
        
        # <<< Thêm kiểm tra thư mục tồn tại >>>
        if not os.path.isdir(image_folder):
             print(f"Lỗi: Thư mục slideshow '{image_folder}' không tồn tại.")
             self.images, self.gif_frames, self.files = [], {}, []
        else:
             self.images, self.gif_frames, self.files = self.load_images(image_folder)
             
        self.index = 0
        self.job = None # Lưu ID của after job
        self.gif_index = 0

        # <<< Kiểm tra self.files trước khi tạo label và nút >>>
        if not self.files:
            # Hiển thị thông báo nếu không có ảnh
            self.label = ctk.CTkLabel(self, text="Không tìm thấy ảnh trong thư mục slideshow.", text_color="gray")
            self.label.pack(expand=True, fill="both")
            # Không tạo nút nếu không có ảnh
            self.prev_btn = None
            self.next_btn = None
            return # Dừng init sớm

        # Tạo label và nút nếu có ảnh
        self.label = ctk.CTkLabel(self, text="")
        self.label.pack(expand=True, fill="both")

        # Nút Prev
        self.prev_btn = ctk.CTkButton(
            self, text="<", width=30, height=30,
            # bg_color="white", # bg_color không dùng cho CTkButton, dùng fg_color hoặc transparent
            fg_color="white", text_color="#00234E", # Ví dụ màu text
            font=("Bahnschrift", 30), corner_radius=15, # Giảm radius
            command=self.prev_image
        )
        self.prev_btn.place(relx=0.05, rely=0.5, anchor="w") # Canh giữa theo chiều dọc

        # Nút Next
        self.next_btn = ctk.CTkButton(
            self, text=">", width=30, height=30,
            fg_color="white", text_color="#00234E",
            font=("Bahnschrift", 30), corner_radius=15,
            command=self.next_image
        )
        self.next_btn.place(relx=0.95, rely=0.5, anchor="e") # Canh giữa theo chiều dọc

        # Chỉ bắt đầu slideshow nếu có ảnh
        self.show_image(0)
        # Bỏ play_slideshow() vì show_image đã gọi after
    

    def load_images(self, folder):
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        if not files: # Trả về rỗng nếu không có file hợp lệ
            return [], {}, []
            
        static_images, gif_images = [], {}
        valid_files = [] # Chỉ lưu tên file hợp lệ

        for fname in sorted(files):
            path = os.path.join(folder, fname)
            try:
                if fname.lower().endswith(".gif"):
                    gif = Image.open(path)
                    frames, durations = [], []
                    for frame in ImageSequence.Iterator(gif):
                        # <<< Xử lý lỗi Potential Decompression Bomb >>>
                        try:
                            # Chuyển đổi an toàn hơn
                            frm = frame.copy().convert("RGBA") 
                            frm = ImageProcessor(frm).resize_and_pad(self.size[0], self.size[1]).get_pil_image() # Dùng resize_and_pad
                            frames.append(ctk.CTkImage(light_image=frm, size=self.size))
                            durations.append(frame.info.get("duration", 100))
                        except DecompressionBombError:
                             print(f"Cảnh báo: Bỏ qua frame có thể là Decompression Bomb trong {fname}")
                             continue # Bỏ qua frame này
                        except Exception as e_frame:
                             print(f"Lỗi xử lý frame trong GIF {fname}: {e_frame}")
                             continue # Bỏ qua frame này
                             
                    if frames: # Chỉ thêm nếu có frame hợp lệ
                        gif_images[fname] = {"frames": frames, "durations": durations}
                        static_images.append(None) # Placeholder cho ảnh tĩnh
                        valid_files.append(fname)
                    else:
                        print(f"Cảnh báo: Không thể tải frame nào từ GIF {fname}")
                        
                else: # Ảnh tĩnh
                    img = Image.open(path)
                     # <<< Xử lý lỗi Potential Decompression Bomb >>>
                    try:
                        # Kiểm tra kích thước trước khi resize
                        if img.width * img.height > 89478485: # Giới hạn pixel (ví dụ)
                             raise DecompressionBombError("Ảnh quá lớn")
                        # Dùng ImageProcessor để resize_and_pad
                        processed_img = ImageProcessor(img).resize_and_pad(self.size[0], self.size[1]).get_pil_image()
                        static_images.append(ctk.CTkImage(light_image=processed_img, size=self.size))
                        gif_images[fname] = None # Placeholder cho gif
                        valid_files.append(fname)
                    except DecompressionBombError as e_bomb:
                         print(f"Cảnh báo: Bỏ qua ảnh tĩnh có thể là Decompression Bomb {fname}: {e_bomb}")
                         continue # Bỏ qua file này
                    except Exception as e_img:
                         print(f"Lỗi xử lý ảnh tĩnh {fname}: {e_img}")
                         continue # Bỏ qua file này
            except Exception as e_open:
                print(f"Lỗi khi mở file {fname}: {e_open}")
                continue # Bỏ qua file lỗi

        return static_images, gif_images, valid_files # Trả về danh sách file hợp lệ

    def cancel_job(self):
        """Hủy bỏ tác vụ 'after' đang chờ."""
        if self.job:
            try:
                self.after_cancel(self.job)
            except tk.TclError: # Bắt lỗi nếu job đã bị hủy hoặc không hợp lệ
                pass
            self.job = None

    def show_image(self, idx):
        # <<< Kiểm tra widget tồn tại >>>
        if not self.winfo_exists() or not self.files:
            self.cancel_job()
            return

        self.cancel_job() # Hủy job cũ trước khi tạo job mới
        
        # <<< Đảm bảo index hợp lệ >>>
        idx = idx % len(self.files)
        self.index = idx 
        
        fname = self.files[idx]
        
        try:
            if fname.lower().endswith(".gif") and fname in self.gif_frames and self.gif_frames[fname]:
                self.gif_index = 0
                self.play_gif(fname)
            elif idx < len(self.images) and self.images[idx]: # Kiểm tra index và image tồn tại
                self.label.configure(image=self.images[idx])
                # Lên lịch cho ảnh tiếp theo
                self.job = self.after(self.delay, self.next_image)
            else:
                 # Trường hợp ảnh không load được (None trong list) -> chuyển tiếp
                 print(f"Ảnh tại index {idx} ({fname}) không hợp lệ, chuyển tiếp.")
                 self.job = self.after(100, self.next_image) # Chuyển nhanh hơn
        except tk.TclError as e:
             print(f"Lỗi TclError khi hiển thị ảnh {fname}: {e}")
             self.cancel_job() # Hủy job nếu có lỗi
        except Exception as e:
             print(f"Lỗi không xác định khi hiển thị ảnh {fname}: {e}")
             self.cancel_job()


    def play_gif(self, fname):
        # <<< Kiểm tra widget tồn tại >>>
        if not self.winfo_exists() or fname not in self.gif_frames or not self.gif_frames[fname]:
            self.cancel_job()
            return

        gif_data = self.gif_frames[fname]
        frames = gif_data.get("frames", [])
        durations = gif_data.get("durations", [])

        # Kiểm tra frame và duration hợp lệ
        if not frames or not durations or len(frames) != len(durations):
             print(f"Dữ liệu GIF không hợp lệ cho {fname}, chuyển tiếp.")
             self.job = self.after(100, self.next_image) # Chuyển nhanh
             return

        # Nếu hết frame -> chuyển sang ảnh/gif tiếp theo
        if self.gif_index >= len(frames):
            self.gif_index = 0
            self.job = self.after(self.delay, self.next_image)
            return

        # <<< Kiểm tra index hợp lệ >>>
        if self.gif_index < 0: self.gif_index = 0
        
        try:
            current_frame = frames[self.gif_index]
            current_delay = durations[self.gif_index]
            
            # Đảm bảo delay hợp lệ
            if not isinstance(current_delay, int) or current_delay <= 0:
                current_delay = 100 # Mặc định 100ms
                
            self.label.configure(image=current_frame)

            self.gif_index += 1
            # Lên lịch cho frame tiếp theo
            self.job = self.after(current_delay, lambda: self.play_gif(fname))
            
        except tk.TclError as e:
             print(f"Lỗi TclError khi play GIF frame {self.gif_index} của {fname}: {e}")
             self.cancel_job() # Hủy job nếu có lỗi
        except IndexError:
             print(f"Lỗi IndexError khi truy cập frame/duration {self.gif_index} của {fname}")
             self.cancel_job()
             self.job = self.after(100, self.next_image) # Chuyển nhanh
        except Exception as e:
             print(f"Lỗi không xác định khi play GIF {fname}: {e}")
             self.cancel_job()

    def next_image(self):
        if not self.files: return # Không làm gì nếu không có ảnh
        next_idx = (self.index + 1) % len(self.files)
        self.show_image(next_idx)

    def prev_image(self):
        if not self.files: return # Không làm gì nếu không có ảnh
        prev_idx = (self.index - 1) % len(self.files)
        self.show_image(prev_idx)

    # <<< Thêm phương thức destroy >>>
    def destroy(self):
        """Hủy bỏ job trước khi hủy widget."""
        print("Hủy ImageSlideshow...")
        self.cancel_job()
        # Hủy các widget con một cách an toàn
        for child in self.winfo_children():
            try:
                child.destroy()
            except tk.TclError:
                pass # Bỏ qua nếu widget đã bị hủy
        super().destroy() # Gọi hàm destroy của lớp cha
class WigdetFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        width=None,
        height=None,
        radius=20,
        widget_color="#2DFCB0",
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
        font=("Bahnschrift", 16, "normal"),
        fg_color="green",
        hover_color="darkblue",
        border_color="white",
        border_width=2,
        height=40,
        width=200,
        image=None,  
        command=None,
        corner_radius=10,
        **kwargs
    ):
        super().__init__(
            master=master,
            text=text,
            font=font,
            fg_color=fg_color,
            hover_color=hover_color,
            border_color=border_color,
            border_width=border_width,
            height=height,
            width=width,
            image=image,  
            command=command,
            corner_radius=corner_radius,
            **kwargs
        )

class ComboboxTheme(ctk.CTkComboBox):
    def __init__(
        self,
        master,
        values=[],
        command=None,
        font=("Bahnschrift", 16, "normal"),
        fg_color="white",
        border_color="#022965",
        border_width=1,
        button_color="#007F3A",
        button_hover_color="#005C2D",
        dropdown_font=("Bahnschrift", 14),
        text_color="black",
        **kwargs
    ):
        super().__init__(
            master=master,
            values=values,
            font=font,
            fg_color=fg_color,
            border_color=border_color,
            border_width=border_width,
            button_color=button_color,
            button_hover_color=button_hover_color,
            dropdown_font=dropdown_font,
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
    def __init__(
        self,
        master,
        text,
        value=None,
        text_color="#00224E",
        value_color="#0412A9",
        font_family="Bahnschrift",
        font_size=16,
        font_weight="bold",
        value_weight="normal",
        wraplength=300,
        row_pad_y=2,
        pack_pady=1,
        pack_padx=25,
        pack_anchor="w",
        fg_color="#2DFCB0", 
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        label_font = (font_family, font_size, font_weight)
        value_font = (font_family, font_size, value_weight)

        # Label bên trái
        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=label_font,
            text_color=text_color,
            wraplength=wraplength,
            fg_color="transparent",
            anchor="w"
        )
        self.label.grid(row=0, column=0, sticky="nw", padx=(0, 10), pady=row_pad_y)

        # Nếu có giá trị thì tạo label bên phải
        if value:
            self.value = ctk.CTkLabel(
                self,
                text=value,
                font=value_font,
                text_color=value_color,
                wraplength=wraplength,
                fg_color="transparent",
                justify="left",
                anchor="w"
            )
            self.value.grid(row=0, column=1, sticky="nw", pady=row_pad_y)

        # Gói gọn nguyên frame ra ngoài
        self.pack(pady=pack_pady, padx=pack_padx, anchor=pack_anchor)
        
    def set_text(self, text):
        self.label.configure(text=text)


class CustomTable(ctk.CTkFrame):
    """
    NÂNG CẤP MỚI:
    - Hỗ trợ scroll theo cả chiều dọc và chiều ngang
    - Header cố định khi scroll dọc (sticky header)
    - Tương thích ngược 100% với code cũ
    """
    def __init__(self, master, columns, data, 
                 header_color="#013A63", row_color="#E8F8F5",
                 header_text_color="white", row_text_color="black",
                 column_widths=None,
                 scroll=True,
                 table_width=None, table_height=None,
                 highlight_columns=None, highlight_color="#FFF2B2",
                 **kwargs):

        super().__init__(master, fg_color="transparent", **kwargs)

        self.columns = columns
        self.data = data
        self.header_color = header_color
        self.row_color = row_color
        self.header_text_color = header_text_color
        self.row_text_color = row_text_color
        self.column_widths = column_widths
        self.scroll = scroll
        self.table_width = table_width
        self.table_height = table_height
        self.highlight_columns = highlight_columns or []
        self.highlight_color = highlight_color
        
        # NÂNG CẤP: Thêm container riêng cho header và data
        self.header_container = None
        self.data_container = None
        self.canvas = None
        self.scrollbar_y = None
        self.scrollbar_x = None
        
        self._data_widgets = []  # Lưu trữ các widget của hàng dữ liệu

        self.after(1, self._init_render)

    def _init_render(self):
        """Khởi tạo và render bảng"""
        self.update_idletasks()
        
        if self.scroll:
            self._setup_scrollable_table()
        else:
            # Giữ nguyên cách cũ cho scroll=False
            self.header_container = self
            self.data_container = self
            self._create_header()
            self._create_data_rows()

    def _setup_scrollable_table(self):
        """
        NÂNG CẤP: Thiết lập bảng với scroll 2 chiều và header cố định
        """
        # Cấu hình grid cho frame chính
        self.grid_rowconfigure(0, weight=0)  # Header (không co giãn)
        self.grid_rowconfigure(1, weight=1)  # Data area (co giãn)
        self.grid_columnconfigure(0, weight=1)
        
        # ============ HEADER CỐ ĐỊNH ============
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=(0, 15))  # padx để tránh scrollbar dọc
        self.header_container = self.header_frame
        
        # ============ DATA AREA VỚI SCROLL 2 CHIỀU ============
        # Frame chứa canvas và scrollbars
        self.data_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.data_frame.grid(row=1, column=0, sticky="nsew")
        self.data_frame.grid_rowconfigure(0, weight=1)
        self.data_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas để chứa nội dung data
        self.canvas = ctk.CTkCanvas(self.data_frame, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar dọc
        self.scrollbar_y = ctk.CTkScrollbar(self.data_frame, orientation="vertical", command=self.canvas.yview)
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        
        # Scrollbar ngang
        self.scrollbar_x = ctk.CTkScrollbar(self.data_frame, orientation="horizontal", command=self.canvas.xview)
        self.scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        # Cấu hình canvas
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)
        
        # Frame bên trong canvas để chứa data rows
        self.data_inner_frame = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.data_inner_frame, anchor="nw")
        
        self.data_container = self.data_inner_frame
        
        # Bind sự kiện để cập nhật scrollregion và đồng bộ header
        self.data_inner_frame.bind("<Configure>", self._on_data_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Bind scroll chuột (chỉ scroll dọc)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Tạo header và data
        self._create_header()
        self._create_data_rows()
        
        # Đồng bộ độ rộng header với data lần đầu
        self.after(100, self._sync_header_scroll)

    def _on_data_frame_configure(self, event):
        """Cập nhật scrollregion khi data frame thay đổi kích thước"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Điều chỉnh độ rộng của data_inner_frame theo canvas"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_mousewheel(self, event):
        """Xử lý scroll chuột"""
        if self.canvas and self.canvas.winfo_exists():
            # Windows/MacOS
            if event.num == 4 or event.delta > 0:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.canvas.yview_scroll(1, "units")

    def _sync_header_scroll(self):
        """
        NÂNG CẤP: Đồng bộ scroll ngang giữa header và data
        """
        if not self.scroll or not self.canvas:
            return
            
        def on_canvas_xscroll(*args):
            # Khi canvas scroll ngang, di chuyển header theo
            if len(args) >= 2:
                try:
                    fraction = float(args[0])
                    # Tính toán vị trí x cần di chuyển header
                    total_width = self.data_inner_frame.winfo_width()
                    visible_width = self.canvas.winfo_width()
                    if total_width > visible_width:
                        offset = -fraction * (total_width - visible_width)
                        self.header_frame.place(x=offset, y=0)
                except:
                    pass
        
        # Ghi đè callback của scrollbar ngang
        self.canvas.configure(xscrollcommand=lambda *args: (
            self.scrollbar_x.set(*args),
            on_canvas_xscroll(*args)
        ))

    def _create_header(self):
        """Tạo header (giữ nguyên logic cũ)"""
        if not self.column_widths:
            self.update_idletasks()
            num_cols = len(self.columns)
            current_container_width = self.header_container.winfo_width()
            col_width = int(current_container_width / num_cols) if current_container_width > 1 else 100
            self.column_widths = [col_width] * num_cols

        for i, width in enumerate(self.column_widths):
            self.header_container.grid_columnconfigure(i, minsize=width)
            if self.scroll and self.data_container != self.header_container:
                # Đồng bộ column width cho data container
                self.data_container.grid_columnconfigure(i, minsize=width)

        for col_index, col_name in enumerate(self.columns):
            label = ctk.CTkLabel(
                self.header_container, text=col_name,
                font=("Bahnschrift", 14, "bold"),
                text_color=self.header_text_color,
                fg_color=self.header_color,
                height=30,
                anchor="center"
            )
            label.grid(row=0, column=col_index, padx=1, pady=1, sticky="nsew")

    def _clear_data_rows(self):
        """Xóa các widget của hàng dữ liệu"""
        for row_widgets in self._data_widgets:
            for widget in row_widgets:
                widget.destroy()
        self._data_widgets = []

    def _create_data_rows(self):
        """Tạo các hàng dữ liệu (giữ nguyên logic cũ)"""
        for row_index, row_data in enumerate(self.data, start=1):
            row_widgets = []
            for col_index, cell in enumerate(row_data):
                bg_color = self.highlight_color if col_index in self.highlight_columns else self.row_color
                display_text = str(cell) if cell is not None else "-"
                
                label = ctk.CTkLabel(
                    self.data_container, text=display_text,
                    font=("Bahnschrift", 13),
                    text_color=self.row_text_color,
                    fg_color=bg_color,
                    height=28,
                    anchor="w"
                )
                label.grid(row=row_index - 1, column=col_index, padx=1, pady=1, sticky="nsew")
                row_widgets.append(label)
            self._data_widgets.append(row_widgets)

    def update_data(self, new_data):
        """Cập nhật dữ liệu bảng (giữ nguyên logic cũ)"""
        self.data = new_data
        
        # Chỉ xóa các hàng dữ liệu cũ, giữ lại header
        self._clear_data_rows()
        
        # Tạo các hàng dữ liệu mới
        if self.data_container and self.data_container.winfo_exists():
            self._create_data_rows()
            
        # Cập nhật scrollregion nếu có canvas
        if self.canvas and self.canvas.winfo_exists():
            self.data_inner_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                
class NotifyCard(ctk.CTkFrame):
    def __init__(self, master, title, content,
                 ngay_dang, 
                 image_pil, 
                 on_click=None, 
                 height=150, 
                 width=250, 
                text_btn="Xem chi tiết", **kwargs):
        super().__init__(master, fg_color="white", corner_radius=15, **kwargs)

        if image_pil:
            img = ImageProcessor(image_pil).crop_to_aspect(4, 3).to_ctkimage(size=(width, height))
        else:
            img = None

        self.image_label = ctk.CTkLabel(self, image=img, text="", width=width, height=height, corner_radius=10)
        self.image_label.image = img
        self.image_label.grid(row=0, column=0, rowspan=3, padx=0, pady=0)

        self.title_label = ctk.CTkLabel(self, text=title, font=("Bahnschrift", 16, "bold"), text_color="#FF2020", wraplength=370)
        self.title_label.grid(row=0, column=1, sticky="w", padx=20, pady=(10, 0))

        self.date_label = ctk.CTkLabel(self, text=ngay_dang.strftime("%d/%m/%Y %H:%M"), font=("Bahnschrift", 12), text_color="#3E3E3E")
        self.date_label.grid(row=1, column=1, sticky="w", padx=20, pady=2)

        self.detail_btn = ctk.CTkButton(self, text=text_btn, command=on_click)
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

        ctk.CTkLabel(top, text=title, font=("Bahnschrift", 16, "bold"), wraplength=300).pack(pady=10)
        ctk.CTkLabel(top, text=content, font=("Bahnschrift", 14), wraplength=450, justify="left").pack(pady=10)

class SliderWithLabel(ctk.CTkFrame):
    def __init__(self, master, label_text, from_=0, to=1, initial=0.5, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.is_integer_slider = isinstance(from_, int) and isinstance(to, int)
        
        # Lưu lại màu sắc ban đầu để có thể khôi phục
        self.label_color = "#060056"
        self.value_color = "green"

        self.label = ctk.CTkLabel(self, text=label_text, text_color=self.label_color, font=("Bahnschrift", 14))
        self.label.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 0))

        self.min_label = ctk.CTkLabel(self, text=str(from_), font=("Bahnschrift", 13), text_color=self.value_color)
        self.min_label.grid(row=1, column=0, sticky="w", padx=(10, 5))

        if self.is_integer_slider:
            steps = to - from_
        else:
            steps = 100

        self.slider = ctk.CTkSlider(
            self, from_=from_, to=to, number_of_steps=steps,
            command=self.update_label, height=15, progress_color="#007BC7",
            button_color="#00358B", button_hover_color="#002448"
        )
        self.slider.grid(row=1, column=1, sticky="ew", padx=5)

        self.max_label = ctk.CTkLabel(self, text=str(to), font=("Bahnschrift", 13), text_color=self.value_color)
        self.max_label.grid(row=1, column=2, sticky="e", padx=(5, 10))

        self.value_label = ctk.CTkLabel(self, text="", text_color=self.value_color, font=("Bahnschrift", 13, "bold"))
        self.value_label.grid(row=2, column=0, columnspan=3, pady=(2, 10))

        self.grid_columnconfigure(1, weight=1)
        self.command = command
        
        self.set_value(initial)

    # --- HÀM MỚI ĐƯỢC THÊM VÀO ĐỂ SỬA LỖI ---
    def configure(self, **kwargs):
        """Ghi đè hàm configure để xử lý thuộc tính 'state' một cách đặc biệt."""
        if "state" in kwargs:
            new_state = kwargs.pop("state") # Lấy giá trị state và xóa nó khỏi kwargs
            self.slider.configure(state=new_state) # Áp dụng state cho slider bên trong

            # Cải tiến UI: Làm mờ cả các label cho trực quan
            if new_state == "disabled":
                disabled_color = "#9B9B9B" # Màu xám mờ
                self.label.configure(text_color=disabled_color)
                self.min_label.configure(text_color=disabled_color)
                self.max_label.configure(text_color=disabled_color)
                self.value_label.configure(text_color=disabled_color)
            else: # new_state == "normal"
                self.label.configure(text_color=self.label_color)
                self.min_label.configure(text_color=self.value_color)
                self.max_label.configure(text_color=self.value_color)
                self.value_label.configure(text_color=self.value_color)

        # Gọi hàm configure của lớp cha (CTkFrame) với các tham số còn lại (nếu có)
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
    def __init__(self, master, text, initial=True, command=None, wraplenght=500, text_color="#310148", font=("Bahnschrift", 13), **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.label = ctk.CTkLabel(self, text=text, text_color=text_color, font=font, wraplength=wraplenght, anchor="w", justify="left")
        self.label.pack(side="left", padx=(10, 5), pady=5)

        self.switch = ctk.CTkSwitch(self, text="BẬT" if initial else "TẮT", progress_color="#00D084", font=font, text_color=text_color)
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
        
import customtkinter as ctk

class LoadingDialog(ctk.CTkToplevel):
    def __init__(self, 
                 parent, 
                 message="Đang xử lý...", 
                 progress_color="#012C49", 
                 mode="determinate", 
                 height_progress=18,
                 temp_topmost_off: bool = False): # <-- THAM SỐ MỚI
        
        super().__init__(parent)
        self.geometry("500x200")
        self.title("")
        self.resizable(False, False)
        self.overrideredirect(True)
        self.configure(bg="#F2F2F2", fg_color="#F2F2F2")
        self.attributes("-transparentcolor", "#F2F2F2")
        self.attributes("-alpha", 0.93)

        # Luôn nằm trên cùng và modal
        self.attributes("-topmost", True)
        self.grab_set() # <-- Đây cũng là một phần của vấn đề

        # Container
        self.container = ctk.CTkFrame(self, corner_radius=20, fg_color="white")
        self.container.pack(expand=True, fill="both", padx=20, pady=20)

        # Label
        self.label = ctk.CTkLabel(
            self.container,
            text=message,
            font=("Bahnschrift", 20, "bold"),
            text_color="#002F6C"
        )
        self.label.pack(pady=(30, 20))

        # ProgressBar
        self.progressbar = ctk.CTkProgressBar(
            self.container,
            width=400,
            height=height_progress,
            corner_radius=10,
            progress_color=progress_color,
            fg_color="#E0E0E0",
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

        self.configure(fg_color="#000945")

        # Label nội dung
        self.label = ctk.CTkLabel(self, text=message, text_color="#A0FB3E", font=("Bahnschrift", 15, "bold"), corner_radius=20)
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
    def __init__(self, master, title="", color="#FFFFFF", controller=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.title = title
        self.controller = controller
        self.is_expanded = False
        self.color = color

        self.header_frame = ctk.CTkFrame(self, fg_color=self.color, corner_radius=10, cursor="hand2")
        self.header_frame.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame, text=self.title, font=("Bahnschrift", 16, "bold"), text_color="#05243F", cursor="hand2"
        )
        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.toggle_button = ctk.CTkButton(
            self.header_frame, text="⇣", font=("Bahnschrift", 18, "bold"), width=30, height=30,
            fg_color="#05243F", hover_color="#214768", command=None, cursor="hand2"
        )
        self.toggle_button.grid(row=0, column=1, padx=10, pady=5, sticky="e")

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
