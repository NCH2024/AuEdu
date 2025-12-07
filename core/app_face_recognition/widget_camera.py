import customtkinter as ctk
from gui.base.utils import *
from PIL import Image
from customtkinter import CTkImage
from core.app_face_recognition.camera_setup import CameraManager
from tkinter import messagebox
from core.utils import get_base_path
import cv2

class WidgetCamera(ctk.CTkFrame):
    def __init__(self, master=None, camera_manager=None, open_as_toplevel=True, flip_camera=False, **kwargs):
        super().__init__(master, **kwargs)
        self.camera_manager = camera_manager
        self.flip_camera = flip_camera
        self.is_playing = True
        self.ctk_img_instance = None
        self.master = master
        
        self.widget_color = "#2DFCB0"
        self._fg_color = "#05243F"
        
        self.configure(fg_color=self._fg_color)
        
        # Bố cục chính sử dụng grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0) # Dòng này cho các nút điều khiển
        
        # --- Frame hiển thị hình ảnh trực tiếp ---
        # Loại bỏ kích thước cố định để nó tự co giãn theo master
        self.widget_videoCapture = ctk.CTkFrame(self, fg_color="black", corner_radius=0)
        self.widget_videoCapture.grid(row=0, column=0, padx=10, pady=(10,10), sticky="news")
        self.widget_videoCapture.grid_propagate(False)
        self.widget_videoCapture.grid_columnconfigure(0, weight=1)
        self.widget_videoCapture.grid_rowconfigure(0, weight=1)
        
        self.camera_label = ctk.CTkLabel(self.widget_videoCapture, text="")
        self.camera_label.grid(row=0, column=0, sticky="nsew") # Dùng grid để lấp đầy khung
        
        # --- Frame dưới (chỉ chứa nút Thoát nếu ở chế độ toplevel) ---
        if open_as_toplevel:
            self.widget_groupBtn = ctk.CTkFrame(self, fg_color="transparent")
            self.widget_groupBtn.grid(row=1, column=0, padx=50, pady=(0,10), sticky="we")
            self.widget_groupBtn.grid_columnconfigure(0, weight=1)
            self.widget_groupBtn.grid_columnconfigure(1, weight=1)
            
            try:
                exit_img = Image.open(os.path.jion(get_base_path(),"resources/images/cross.png"))
                self.exit_img = ImageProcessor(exit_img).to_ctkimage()
            except FileNotFoundError:
                self.exit_img = None

            self.exit_btn = ButtonTheme(self.widget_groupBtn, 
                                        text="", 
                                        image=self.exit_img,
                                        fg_color="transparent", 
                                        hover_color=self.widget_color,
                                        width=35,
                                        command=self.close_window)
            self.exit_tooltip = Tooltip(self.exit_btn, "Thoát cửa sổ Camera")
            self.exit_btn.pack(side="right", padx=10, pady=10)
        
        #self.update_video_feed()
    
    # def update_video_feed(self):
    #     if self.is_playing and self.camera_manager and self.camera_manager.is_opened:
    #         frame = self.camera_manager.get_frame()
    #         if frame is not None:
    #             if self.flip_camera:
    #                 img = Image.fromarray(cv2.flip(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 1))
    #             else:
    #                 img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    #             # Lấy kích thước hiện tại của camera_label để resize ảnh
    #             label_w = self.camera_label.winfo_width()
    #             label_h = self.camera_label.winfo_height()
                
    #             if label_w > 0 and label_h > 0:
    #                 img.thumbnail((label_w, label_h), Image.Resampling.LANCZOS)
    #                 self.ctk_img_instance = CTkImage(light_image=img, size=img.size)
    #                 self.camera_label.configure(image=self.ctk_img_instance, text="")
    #         else:
    #             self.camera_label.configure(text="Không nhận được tín hiệu camera", image=None)
    #             self.is_playing = False
    #     else:
    #         self.camera_label.configure(text="Camera đã bị đóng hoặc lỗi", image=None)
        
    #     self.after(20, self.update_video_feed)
        

    def set_image(self, frame):
        if frame is not None:
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            label_w = self.camera_label.winfo_width()
            label_h = self.camera_label.winfo_height()

            if label_w > 0 and label_h > 0:
                img.thumbnail((label_w, label_h), Image.Resampling.LANCZOS)
                self.ctk_img_instance = ctk.CTkImage(light_image=img, size=img.size)
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
        screen_width = top.winfo_screenwidth()
        screen_height = top.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        top.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        top.title("CAMERA")
        top.configure(fg_color="#05243F")
        if parent:
            top.transient(parent.winfo_toplevel())
        
        top.lift()
        top.focus_force()
        camera_widget = cls(master=top, camera_manager=camera_manager)
        camera_widget.grid(row=0, column=0, sticky="nsew")
        top.protocol("WM_DELETE_WINDOW", camera_widget.close_window)