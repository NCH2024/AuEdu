import customtkinter as ctk 
from gui.base.utils import *
from core.utils import get_base_path
from PIL import Image
import os
from core.theme_manager import *

class BaseFrame(ctk.CTkFrame):
    def __init__(self, master=None, **kwargs):
        kwargs['fg_color'] = Theme.Color.BG
        kwargs['corner_radius'] = 0
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.widget_color = Theme.Color.BG
        self.text_color = Theme.Color.TEXT
        self.text_color_w = Theme.Color.TEXT_SUB

        self.grid_columnconfigure(0, weight=0, minsize=500)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0, minsize=500)
        self.grid_rowconfigure(2, weight=1)

        self.label_title = ctk.CTkLabel(
            self,
            text="Base Frame",
            font=AppFont.H3,
            text_color=self.text_color
        )
        self.label_title.grid(row=0, column=0, pady=(0,5), padx=(10,0), sticky="nw")
        
        try:
            base_path = get_base_path()
            exit_img = Image.open(os.path.join(base_path, "resources/images/cross.png"))
            self.exit_img = ImageProcessor(exit_img)\
                         .crop_to_aspect(80, 80) \
                         .resize(20, 20) \
                         .to_ctkimage()
                                                    
        except FileNotFoundError:
            self.exit_img = None
        self.close_button = ButtonTheme(self,
                                        text="ESC", 
                                        command=self.on_close, 
                                        fg_color=ColorPalette.DEEP_NAVY, 
                                        hover_color="#939393",
                                        font=AppFont.H3,
                                        border_width=0,
                                        width=40,
                                        height=40,
                                        image=self.exit_img)
        self.close_button.grid(row=0, column=1, pady=(0,5), padx=10, sticky="ne")
        
        self.content_frame = ctk.CTkFrame(self, fg_color=self.widget_color)
        self.content_frame.grid(row=1, column=0,columnspan=2, padx=0, pady=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        
    def on_close(self):
        self.destroy()
        
    def set_label_title(self, title):
        self.label_title.configure(text=title)
    