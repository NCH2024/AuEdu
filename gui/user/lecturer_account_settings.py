import customtkinter as ctk
from gui.base.utils import *
from tkinter import messagebox
import core.database as db
import re
from core.app_config import save_config
from core.theme_manager import Theme, AppFont # Import Theme

class LecturerAccount_Setting(ctk.CTkFrame):
    def __init__(self, master=None, user=None, AppConfig=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        # Bỏ weight cho các hàng để giao diện không bị giãn cách
        self.grid_rowconfigure((0,1,2,3,4,5,6,7,8,9), weight=0) 
        
        self.user = user
        self.AppConfig = AppConfig

        # --- Giao diện ---
        # SỬA: Màu text theo Theme
        self.title = ctk.CTkLabel(self, text="> Cài đặt Tài khoản", font=AppFont.BODY_BOLD, text_color=Theme.Color.TEXT)
        self.title.grid(row=0, column=0, columnspan=2, padx=15, pady=(20, 5), sticky="w")

        # SỬA: Màu Primary
        self.name_setting = ctk.CTkLabel(self, text="THIẾT LẬP CHUNG", font=AppFont.BODY, text_color=Theme.Color.PRIMARY)
        self.name_setting.grid(row=1, column=0, padx=20, pady=(5, 15), sticky="nw")
        
        # SỬA: Khung info dùng BG_CARD, không dùng "white"
        self.user_info = ctk.CTkFrame(self, fg_color=Theme.Color.BG_CARD, corner_radius=6)
        self.user_info.grid(row=2, column=0, padx=20, columnspan=2, sticky="ew")
        self.user_info_name = LabelCustom(self.user_info, "Username:", value=self.user)
        self.user_info_name.pack(padx=10, pady=10, anchor="w") # LabelCustom cần pack/grid
        
        self.password_setting = ctk.CTkLabel(self, text="THIẾT LẬP MẬT KHẨU", font=AppFont.BODY, text_color=Theme.Color.PRIMARY)
        self.password_setting.grid(row=4, column=0, padx=20, pady=(15, 5), sticky="nw")
        
        # --- CẢI TIẾN BỐ CỤC ---
        # SỬA: Dùng AppFont cho Entry
        # Ô mật khẩu cũ
        self.password_entry_old = ctk.CTkEntry(self, placeholder_text="Nhập mật khẩu cũ", show="*", 
                                             width=200, height=40, font=AppFont.BODY)
        self.password_entry_old.grid(row=5, column=0, columnspan=2, padx=20, sticky="ew")
        
        # Ô mật khẩu mới
        self.password_entry_new = ctk.CTkEntry(self, placeholder_text="Nhập mật khẩu mới", show="*", 
                                             width=200, height=40, font=AppFont.BODY)
        self.password_entry_new.grid(row=6, column=0, columnspan=2, padx=20, pady=(10,0), sticky="ew")

        # Tạo một frame để chứa ô nhập lại và checkbox
        repeat_pass_frame = ctk.CTkFrame(self, fg_color="transparent")
        repeat_pass_frame.grid(row=7, column=0, columnspan=2, padx=20, pady=(10,0), sticky="ew")
        repeat_pass_frame.grid_columnconfigure(0, weight=1) 

        # Ô nhập lại mật khẩu mới
        self.password_entry_new_repeat = ctk.CTkEntry(repeat_pass_frame, placeholder_text="Nhập lại mật khẩu mới", show="*", 
                                                    width=200, height=40, font=AppFont.BODY)
        self.password_entry_new_repeat.grid(row=0, column=0, sticky="ew")
        
        # Checkbox "Hiện mật khẩu"
        # SỬA: Checkbox dùng màu text theo Theme
        self.show_password_checkbox = ctk.CTkCheckBox(repeat_pass_frame, text="Hiện mật khẩu", 
                                                    font=AppFont.BODY,
                                                    text_color=Theme.Color.TEXT,
                                                    command=self.toggle_password_visibility)
        self.show_password_checkbox.grid(row=0, column=1, padx=(10, 0))
        
        # SỬA: Checkbox lưu đăng nhập
        self.save_login = ctk.CTkCheckBox(self, text="Lưu đăng nhập mật khẩu mới cho lần kế tiếp", 
                                          font=AppFont.BODY, text_color=Theme.Color.TEXT)
        self.save_login.grid(row=8, column=0, padx=20, pady=(10,0), sticky="nw")

        # Nút Lưu
        # SỬA: Dùng màu Primary
        self.save_btn = ButtonTheme(self, text="LƯU THAY ĐỔI TÀI KHOẢN", fg_color=Theme.Color.PRIMARY, command=self.on_check)
        self.save_btn.grid(row=9, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

    # --- GIỮ NGUYÊN LOGIC ---
    def toggle_password_visibility(self):
        """Được gọi bởi checkbox để thay đổi trạng thái hiển thị của các ô mật khẩu."""
        is_checked = self.show_password_checkbox.get()
        if is_checked:
            self.password_entry_old.configure(show="")
            self.password_entry_new.configure(show="")
            self.password_entry_new_repeat.configure(show="")
        else:
            self.password_entry_old.configure(show="*")
            self.password_entry_new.configure(show="*")
            self.password_entry_new_repeat.configure(show="*")
            
    def validate_password(self, password):
        """Sử dụng Regex để kiểm tra các quy tắc bảo mật."""
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,16}$"
        if re.match(pattern, password):
            return (True, "Mật khẩu hợp lệ.")
        else:
            return (False, "Mật khẩu không hợp lệ. Vui lòng đảm bảo:\n\n"
                            "— Độ dài từ 8 đến 16 ký tự.\n"
                            "— Chứa ít nhất một chữ viết thường (a-z).\n"
                            "— Chứa ít nhất một chữ viết HOA (A-Z).\n"
                            "— Chứa ít nhất một chữ số (0-9).")

    def on_check(self):
        try:
            old_pass = self.password_entry_old.get()
            new_pass = self.password_entry_new.get()
            repeat_pass = self.password_entry_new_repeat.get()

            if not old_pass or not new_pass or not repeat_pass:
                messagebox.showwarning("CẢNH BÁO", "Bạn phải điền đầy đủ cả ba ô mật khẩu!")
                return

            check_pass_old = db.login(self.user, old_pass)
            if not check_pass_old:
                messagebox.showerror("LỖI", "Mật khẩu cũ không đúng, vui lòng thử lại!")
                return

            is_valid, message = self.validate_password(new_pass)
            if not is_valid:
                messagebox.showwarning("MẬT KHẨU KHÔNG HỢP LỆ", message)
                return
                
            if new_pass != repeat_pass:
                messagebox.showerror("LỖI", "Mật khẩu nhập lại không trùng khớp!")
                return
            
            def save_update():
                try:
                    if self.save_login.get():
                        self.AppConfig.login_info.username = self.user
                        self.AppConfig.login_info.password = self.password_entry_new.get()
                        save_config(self.AppConfig)
                        update_success = db.update_password(self.user, new_pass)
                        if update_success:
                            return (True, "Cập nhật mật khẩu thành công, ghi nhớ đăng nhập cho lần kết tiếp!")
                        
                    else:
                        self.AppConfig.login_info.username = None
                        self.AppConfig.login_info.password = None
                        save_config(self.AppConfig)
                        update_success = db.update_password(self.user, new_pass)
                        if update_success:
                            return (True, "Cập nhật mật khẩu thành công, không ghi nhớ đăng nhập!")
                    
                except Exception as e:
                    return (False, f"Lỗi khi cập nhật mật khẩu: {e}")
                
            key_save, message_save = save_update()
                
            if key_save:
                messagebox.showinfo("THÀNH CÔNG", message_save)
                self.password_entry_old.delete(0, 'end')
                self.password_entry_new.delete(0, 'end')
                self.password_entry_new_repeat.delete(0, 'end')
            else:
                messagebox.showerror("LỖI HỆ THỐNG", message_save)

        except Exception as e:
            print(f"Đã xảy ra một lỗi không mong muốn: {e}")
            messagebox.showerror("LỖI HỆ THỐNG", f"Đã có lỗi xảy ra: {e}")