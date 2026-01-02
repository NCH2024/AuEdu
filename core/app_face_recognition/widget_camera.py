import customtkinter as ctk
from gui.base.utils import *
from PIL import Image
from customtkinter import CTkImage
from core.app_face_recognition.camera_setup import CameraManager
from tkinter import messagebox
from core.utils import get_base_path
import cv2
from core.theme_manager import Theme, AppFont # <--- IMPORT THEME

class WidgetCamera(ctk.CTkFrame):
    def __init__(self, master=None, camera_manager=None, open_as_toplevel=True, flip_camera=False, **kwargs):
        kwargs['corner_radius'] = 0
        super().__init__(master, **kwargs)
        self.camera_manager = camera_manager
        self.flip_camera = flip_camera
        self.is_playing = True
        self.ctk_img_instance = None
        self.master = master
        
        # SỬA: Dùng màu Theme thay vì mã cứng
        self.widget_color = Theme.Color.PRIMARY 
        self._fg_color = Theme.Color.BG_CARD 
        
        self.configure(fg_color=self._fg_color)
        
        # Bố cục chính
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        # --- Frame hiển thị hình ảnh ---
        # SỬA: Màu nền đen cho khung video là hợp lý, giữ nguyên hoặc dùng Theme.Color.BG
        self.widget_videoCapture = ctk.CTkFrame(self, fg_color="black", corner_radius=0)
        self.widget_videoCapture.grid(row=0, column=0, padx=10, pady=(10,10), sticky="news")
        self.widget_videoCapture.grid_propagate(False)
        self.widget_videoCapture.grid_columnconfigure(0, weight=1)
        self.widget_videoCapture.grid_rowconfigure(0, weight=1)
        
        self.camera_label = ctk.CTkLabel(self.widget_videoCapture, text="")
        self.camera_label.grid(row=0, column=0, sticky="nsew")
        
        # --- Frame dưới (Nút thoát) ---
        if open_as_toplevel:
            self.widget_groupBtn = ctk.CTkFrame(self, fg_color="transparent")
            self.widget_groupBtn.grid(row=1, column=0, padx=50, pady=(0,10), sticky="we")
            self.widget_groupBtn.grid_columnconfigure(0, weight=1)
            self.widget_groupBtn.grid_columnconfigure(1, weight=1)
            
            try:
                # SỬA: Đường dẫn os.path.join cho chuẩn
                base_path = get_base_path()
                exit_img = Image.open(os.path.join(base_path, "resources", "images", "cross.png"))
                self.exit_img = ImageProcessor(exit_img).to_ctkimage()
            except Exception: # Bắt rộng hơn để tránh lỗi
                self.exit_img = None

            # SỬA: Dùng ButtonTheme
            self.exit_btn = ButtonTheme(self.widget_groupBtn, 
                                        text="", 
                                        image=self.exit_img,
                                        fg_color="transparent", 
                                        hover_color=Theme.Color.DANGER, # Màu đỏ khi hover thoát
                                        width=35,
                                        command=self.close_window)
            self.exit_tooltip = Tooltip(self.exit_btn, "Thoát cửa sổ Camera")
            self.exit_btn.pack(side="right", padx=10, pady=10)
        
    def set_image(self, frame):
        if frame is not None:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            label_w = self.camera_label.winfo_width()
            label_h = self.camera_label.winfo_height()

            if label_w > 0 and label_h > 0:
                img.thumbnail((label_w, label_h), Image.Resampling.LANCZOS)
                self.ctk_img_instance = ctk.CTkImage(light_image=img, dark_image=img, size=img.size) # Fix dark_image
                self.camera_label.configure(image=self.ctk_img_instance, text="")
            else:
                self.after(20, lambda: self.set_image(frame))
        else:
            self.camera_label.configure(text="Không nhận được tín hiệu", image=None)

    def close_window(self):
        self.is_playing = False
        if self.camera_manager:
            self.camera_manager.release_camera()
        if self.master and isinstance(self.master, ctk.CTkToplevel):
            self.master.destroy()
            WidgetCamera._window_instance = None

    _window_instance = None
    @classmethod
    def show_window(cls, parent=None, camera_manager=None):
        if cls._window_instance and cls._window_instance.winfo_exists():
            cls._window_instance.focus_force()
            return
        
        top = ctk.CTkToplevel(parent)
        cls._window_instance = top
        window_width = 350
        window_height = 420
        # ... (Phần tính toán center giữ nguyên)
        screen_width = top.winfo_screenwidth()
        screen_height = top.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        top.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        
        top.title("CAMERA")
        # SỬA: Màu nền Toplevel
        top.configure(fg_color=Theme.Color.BG)
        
        if parent:
            top.transient(parent.winfo_toplevel())
        
        top.lift()
        top.focus_force()
        camera_widget = cls(master=top, camera_manager=camera_manager)
        camera_widget.grid(row=0, column=0, sticky="nsew")
        top.protocol("WM_DELETE_WINDOW", camera_widget.close_window)