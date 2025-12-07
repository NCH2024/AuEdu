import customtkinter as ctk
import threading
from gui.base.utils import *
from core.database import *
from core.utils import get_base_path
from PIL import Image
import os


class BasePopupWindow(ctk.CTkFrame):
    def __init__(self, master=None, config=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config = config
        self._corner_radius = 0
        self._border_width = 0
        self.widget_color = "#05243F"
        self.text_color = "#2DFCB0"
        self.text_color_w = "#FFFFFF"
    
        
        # làm lớp phủ
        self.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)  
        self.configure(fg_color=self.widget_color)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._setup_ui()

    def _setup_ui(self):
        self.label_title = LabelCustom(
            self,
            text="",
            font_size=18,
            font_weight="bold",
            text_color=self.text_color_w,
            wraplength=600
        )
        self.label_title.grid(row=0, column=0, pady=(10,10), padx=(10,0), sticky="nw")

        try:
            base_path = get_base_path()
            exit_img = Image.open(os.path.join(base_path,"resources/images/cross.png"))
            self.exit_img = ImageProcessor(exit_img)\
                         .crop_to_aspect(80, 80) \
                         .resize(20, 20) \
                         .to_ctkimage()
                                                    
        except FileNotFoundError:
            self.exit_img = None

        self.close_button = ButtonTheme(
            self,
            text="ESC", 
            command=self.on_close, 
            fg_color="transparent", 
            border_color="white",
            border_width=2,
            hover_color="#939393",
            font=("Bahnschrift", 18, "bold"),
            width=40,
            height=40,
            image=self.exit_img
        )
        self.close_button.grid(row=0, column=1, pady=10, padx=10, sticky="ne")

    def on_close(self):
        """Đóng overlay"""
        self.destroy()
        
