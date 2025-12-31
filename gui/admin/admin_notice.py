import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from datetime import datetime
from PIL import Image
from io import BytesIO
from gui.base.base_frame import BaseFrame
from gui.base.utils import *
import core.database as db
from core.theme_manager import Theme, AppFont 
from mysql.connector import Error
import os

class AdminNotice(BaseFrame):
    def __init__(self, master=None, user=None, **kwargs):
        kwargs['fg_color'] = Theme.Color.BG
        super().__init__(master, **kwargs)
        self.user = user
        self.set_label_title("Dashboard > Trang Chủ > QUẢN LÝ THÔNG BÁO")
        # [GIỮ NGUYÊN INIT NHƯ CŨ]
        try:
            self.temp_notice_dir = os.path.join(get_base_path(), "resources", "temp_notice_images")
            os.makedirs(self.temp_notice_dir, exist_ok=True)
        except Exception: self.temp_notice_dir = "."
        self.selected_notice_id = None; self.current_image_pil = None; self.current_image_blob = None
        self.image_preview_label = None; self.current_ctk_image = None 
        try: db.connect_db(); self.setup_ui(); self._load_notice_data()
        except Exception as e: messagebox.showerror("Lỗi", f"{e}")

    def setup_ui(self):
        Theme.apply_treeview_style(self)
        self.content_frame.grid_columnconfigure(0, weight=1); self.content_frame.grid_columnconfigure(1, weight=2)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Form
        form = ctk.CTkFrame(self.content_frame, fg_color=Theme.Color.BG_CARD, corner_radius=10)
        form.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        form.grid_columnconfigure(0, weight=1); form.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(form, text="Tạo/Chỉnh sửa Thông báo:", font=AppFont.H3, text_color=Theme.Color.TEXT).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(form, text="Tiêu đề:", font=AppFont.BODY).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.notice_title_entry = ctk.CTkEntry(form); self.notice_title_entry.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(form, text="Nội dung:", font=AppFont.BODY).grid(row=3, column=0, padx=10, sticky="nw")
        self.notice_content_textbox = ctk.CTkTextbox(form, height=200, font=AppFont.BODY, wrap="word"); self.notice_content_textbox.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        img_ctrl = ctk.CTkFrame(form, fg_color="transparent"); img_ctrl.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        ButtonTheme(img_ctrl, text="Chọn ảnh", width=100, command=self._select_image).grid(row=0, column=0, padx=5, sticky="nw")
        ButtonTheme(img_ctrl, text="Xóa ảnh", width=80, fg_color=Theme.Color.DANGER, command=self._remove_image).grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        self.image_preview_label = ctk.CTkLabel(img_ctrl, text="Chưa có ảnh", fg_color=Theme.Color.BG, text_color="gray", height=150, corner_radius=5)
        self.image_preview_label.grid(row=0, column=1, rowspan=2, padx=10, sticky="ew"); img_ctrl.grid_columnconfigure(1, weight=1)
        
        btn = ctk.CTkFrame(form, fg_color="transparent"); btn.grid(row=7, column=0, columnspan=2, pady=10, padx=5, sticky="w")
        ButtonTheme(btn, text="Thêm", width=100, fg_color=Theme.Color.SUCCESS, command=self._add_notice).pack(side="left", padx=5)
        ButtonTheme(btn, text="Cập nhật", width=100, fg_color=Theme.Color.INFO, command=self._update_notice).pack(side="left", padx=5)
        ButtonTheme(btn, text="Xóa", width=100, fg_color=Theme.Color.DANGER, command=self._delete_notice).pack(side="left", padx=5)
        ButtonTheme(btn, text="Làm mới", width=100, fg_color=Theme.Color.NEUTRAL, command=self._clear_notice_form).pack(side="left", padx=5)

        # Table
        table = ctk.CTkFrame(self.content_frame, fg_color=Theme.Color.BG_CARD, corner_radius=10)
        table.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        table.grid_rowconfigure(1, weight=1); table.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(table, text="Danh sách Thông báo:", font=AppFont.H3, text_color=Theme.Color.TEXT).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self._create_notice_table(table)

    def _create_notice_table(self, p):
        cont = ctk.CTkFrame(p, fg_color="transparent"); cont.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        cont.grid_rowconfigure(0, weight=1); cont.grid_columnconfigure(0, weight=1)
        self.notice_table = ttk.Treeview(cont, columns=("id", "td", "nd", "img"), show="headings")
        self.notice_table.grid(row=0, column=0, sticky="nsew")
        for c, t in [("id","ID"), ("td","Tiêu đề"), ("nd","Ngày đăng"), ("img","Hình ảnh")]:
            self.notice_table.heading(c, text=t)
        self.notice_table.bind("<<TreeviewSelect>>", self._select_notice_tree)

    def _load_notice_data(self):
        """Tải dữ liệu thông báo lên Treeview."""
        self._clear_notice_table()
        try:
            self.notice_image_blobs = {} 
            notice_data = db.get_all_thongbao() 
            if notice_data:
                for notice in notice_data:
                    notice_id, tieu_de, noi_dung, ngay_dang_obj, image_blob = notice
                    ngay_dang_formatted = ngay_dang_obj.strftime('%d/%m/%Y %H:%M') if ngay_dang_obj else ''
                    co_anh_text = "[Ảnh]" if image_blob else ""
                    self.notice_image_blobs[notice_id] = {'blob': image_blob, 'content': noi_dung}
                    self.notice_table.insert("", "end", iid=notice_id, values=(notice_id, tieu_de, ngay_dang_formatted, co_anh_text))
        except Error as e: messagebox.showerror("Lỗi tải Thông báo", f"Lỗi CSDL: {e}", parent=self)
        except Exception as e: messagebox.showerror("Lỗi tải Thông báo", f"Lỗi không xác định: {e}", parent=self)

    def _clear_notice_table(self):
        """Xóa dữ liệu trong bảng thông báo."""
        for item in self.notice_table.get_children(): self.notice_table.delete(item)
        self.notice_image_blobs = {} 
        
    def _remove_image(self):
        """Xóa ảnh đang preview, dọn dẹp file tạm và cập nhật UI."""
        self.current_image_pil = None
        self.current_image_blob = None
        old_ctk_image = self.current_ctk_image
        self.current_ctk_image = None 

        if self.image_preview_label and self.image_preview_label.winfo_exists():
            try:
                self.image_preview_label.configure(image=None, text="Chưa có ảnh")
                self.update_idletasks()
            except tk.TclError as e:
                 print(f"Lỗi khi cấu hình label trong _remove_image: {e}")

        # Dọn dẹp file preview tạm
        try:
            # Thử xóa file dựa trên ID đang chọn (nếu có)
            if self.selected_notice_id:
                 filename = f"notice_{self.selected_notice_id}_preview.png"
                 temp_path = os.path.join(self.temp_notice_dir, filename)
                 if os.path.exists(temp_path):
                     os.remove(temp_path)
            
            # Luôn thử xóa file "temp_selected" (dùng khi chọn file mới)
            temp_selected_path = os.path.join(self.temp_notice_dir, "temp_selected_preview.png")
            if os.path.exists(temp_selected_path):
                os.remove(temp_selected_path)
            
            # Luôn thử xóa file "temp_blob" (dùng khi có lỗi)
            temp_blob_path = os.path.join(self.temp_notice_dir, "temp_blob_preview.png")
            if os.path.exists(temp_blob_path):
                os.remove(temp_blob_path)
                
        except Exception as e:
            print(f"Lỗi khi xóa file ảnh tạm: {e}")
        
        if old_ctk_image:
            del old_ctk_image



    def _display_image_preview(self, image_source):
        """
        Hiển thị ảnh (từ PIL hoặc BLOB) lên label preview.
        Ý tưởng: Lưu ảnh ra file tạm rồi tải lại từ file đó.
        """
        if not hasattr(self, 'image_preview_label') or not self.image_preview_label or not self.image_preview_label.winfo_exists():
            print("Warning: image_preview_label không tồn tại.")
            return

        img_to_display_pil = None
        new_ctk_image = None
        saved_path = None # Đường dẫn file tạm

        try:
            # Xác định tên file và tạo đối tượng PIL
            if isinstance(image_source, Image.Image):
                # Nguồn là file dialog (_select_image)
                img_to_display_pil = image_source.copy()
                saved_path = os.path.join(self.temp_notice_dir, "temp_selected_preview.png")

            elif isinstance(image_source, bytes) and image_source:
                # Nguồn là BLOB từ DB (_select_notice_tree)
                if not self.selected_notice_id:
                    filename = "temp_blob_preview.png"
                else:
                    filename = f"notice_{self.selected_notice_id}_preview.png"
                
                saved_path = os.path.join(self.temp_notice_dir, filename)
                img_to_display_pil = Image.open(BytesIO(image_source))

            else:
                self._remove_image() # Không có ảnh
                return

            # Lưu file ảnh PIL xuống đĩa
            if img_to_display_pil and saved_path:
                try:
                    img_save = img_to_display_pil.copy()
                    if img_save.mode == 'RGBA':
                        img_save = img_save.convert('RGB')
                    img_save.save(saved_path, format='PNG')
                except Exception as e:
                    print(f"Lỗi khi lưu ảnh preview tạm thời: {e}")
                    saved_path = None # Nếu lỗi thì fallback
            else:
                saved_path = None

            # *** LOGIC QUAN TRỌNG: Tải lại ảnh từ file đã lưu (nếu thành công) ***
            if saved_path and os.path.exists(saved_path):
                preview_height = 150
                
                # Sử dụng ImageProcessor để tải và xử lý từ ĐƯỜNG DẪN
                img_processor = ImageProcessor(saved_path)
                
                # === SỬA LỖI TẠI ĐÂY ===
                # Giả định ImageProcessor tải ảnh vào thuộc tính 'image'
                if not hasattr(img_processor, 'image') or img_processor.image is None:
                    raise ValueError("ImageProcessor không tải được ảnh từ file tạm")
                
                # Lấy kích thước từ thuộc tính .size của ảnh PIL, không phải .get_size()
                original_width, original_height = img_processor.image.size 
                # ======================

                if original_height == 0: raise ValueError("Chiều cao ảnh bằng 0.")
                
                ratio = preview_height / original_height
                preview_width = int(original_width * ratio)
                if preview_width <= 0: preview_width = 1

                # Tạo CTkImage mới từ processor (đã chứa ảnh)
                new_ctk_image = img_processor.resize(preview_width, preview_height).to_ctkimage()

                self.current_ctk_image = new_ctk_image
                self.image_preview_label.configure(image=self.current_ctk_image, text="")
                
                # Vẫn lưu PIL gốc để dùng cho việc CẬP NHẬT DB
                self.current_image_pil = img_to_display_pil
            
            else:
                # Fallback: Nếu lưu file lỗi, dùng logic cũ (in-memory)
                if img_to_display_pil:
                    print("Fallback: Lưu file lỗi, sử dụng logic in-memory.")
                    preview_height = 150
                    if img_to_display_pil.height == 0: raise ValueError("Chiều cao ảnh bằng 0.")
                    ratio = preview_height / img_to_display_pil.height
                    preview_width = int(img_to_display_pil.width * ratio)
                    if preview_width <= 0: preview_width = 1
                    
                    img_copy = img_to_display_pil.copy()
                    # Khởi tạo ImageProcessor từ đối tượng PIL
                    new_ctk_image = ImageProcessor(img_copy).resize(preview_width, preview_height).to_ctkimage()
                    self.current_ctk_image = new_ctk_image
                    self.image_preview_label.configure(image=self.current_ctk_image, text="")
                    self.current_image_pil = img_to_display_pil
                else:
                    self._remove_image()

        except Exception as e:
             messagebox.showerror("Lỗi Hiển Thị Ảnh", f"Lỗi khi tạo ảnh preview: {e}", parent=self)
             self._remove_image()
        
    def _select_notice_tree(self, event=None):
        """Hiển thị thông tin thông báo đã chọn lên form."""
        selected_item_id = self.notice_table.focus() 
        if not selected_item_id:
            self.selected_notice_id = None
            return

        try:
            self.selected_notice_id = int(selected_item_id)
            item_values = self.notice_table.item(selected_item_id, "values")
            tieu_de = item_values[1]
            cached_data = self.notice_image_blobs.get(self.selected_notice_id)
            noi_dung = cached_data['content'] if cached_data else ""
            image_blob = cached_data['blob'] if cached_data else None
            self.current_image_blob = image_blob 

            self.notice_title_entry.delete(0, "end"); self.notice_title_entry.insert(0, tieu_de)
            self.notice_content_textbox.delete("1.0", "end"); self.notice_content_textbox.insert("1.0", noi_dung)
            self._display_image_preview(image_blob) # <<< Gọi hàm đã sửa
            
        except (ValueError, IndexError, KeyError) as e:
            messagebox.showerror("Lỗi", f"Dữ liệu thông báo không hợp lệ: {e}", parent=self)
            self._clear_notice_form()
        except Exception as e:
            messagebox.showerror("Lỗi Hiển Thị Chi Tiết TB", f"Lỗi không xác định: {e}", parent=self)
            self._clear_notice_form()

    def _clear_notice_form(self):
        """Xóa trắng form quản lý thông báo."""
        
        # Gọi _remove_image TRƯỚC khi set self.selected_notice_id = None
        # để nó có thể tìm và xóa đúng file temp
        self._remove_image() 
        
        self.selected_notice_id = None
        self.notice_title_entry.delete(0, "end")
        self.notice_content_textbox.delete("1.0", "end")
        
        if self.notice_table.focus():
            self.notice_table.selection_remove(self.notice_table.focus())

    def _select_image(self):
        """Mở dialog chọn file ảnh và hiển thị preview."""
        file_path = filedialog.askopenfilename(
            title="Chọn hình ảnh",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            try:
                self.current_image_pil = Image.open(file_path)
                self._display_image_preview(self.current_image_pil) # <<< Gọi hàm đã sửa
                self.current_image_blob = None 
            except Exception as e:
                messagebox.showerror("Lỗi Mở Ảnh", f"Không thể mở hoặc xử lý file ảnh:\n{e}", parent=self)
                self.current_image_pil = None
                self._remove_image() 

    def _convert_pil_to_blob(self, pil_image):
        """Chuyển đổi ảnh PIL sang dạng BLOB (bytes) để lưu vào DB."""
        if not pil_image: return None
        try:
            if pil_image.mode == 'RGBA': pil_image = pil_image.convert('RGB')
            img_byte_arr = BytesIO()
            # Ưu tiên PNG nếu ảnh có độ trong suốt (dù đã convert), nếu không thì JPG
            img_format = 'PNG' if 'A' in pil_image.mode else 'JPEG'
            pil_image.save(img_byte_arr, format=img_format, quality=85 if img_format=='JPEG' else None) 
            return img_byte_arr.getvalue()
        except Exception as e: print(f"Lỗi chuyển đổi PIL sang BLOB: {e}"); return None

    def _add_notice(self):
        # (Giữ nguyên)
        try:
            tieu_de = self.notice_title_entry.get().strip(); noi_dung = self.notice_content_textbox.get("1.0", "end-1c").strip()
            if not tieu_de or not noi_dung: messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Tiêu đề và Nội dung."); return
            image_blob = self._convert_pil_to_blob(self.current_image_pil)
            if db.add_thongbao(tieu_de, noi_dung, image_blob): 
                 messagebox.showinfo("Thành công", f"Thêm thông báo '{tieu_de}' thành công."); self._clear_notice_form(); self._load_notice_data()
            else: messagebox.showerror("Lỗi", "Thêm thông báo thất bại.")
        except Error as e: messagebox.showerror("Lỗi CSDL", f"Lỗi khi thêm thông báo: {e}", parent=self)
        except Exception as e: messagebox.showerror("Lỗi", f"Lỗi không xác định khi thêm thông báo: {e}", parent=self)

    def _update_notice(self):
        # (Giữ nguyên)
        if not self.selected_notice_id: messagebox.showwarning("Chưa chọn", "Vui lòng chọn thông báo từ bảng để cập nhật."); return
        try:
            notice_id = self.selected_notice_id; tieu_de = self.notice_title_entry.get().strip(); noi_dung = self.notice_content_textbox.get("1.0", "end-1c").strip()
            if not tieu_de or not noi_dung: messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Tiêu đề và Nội dung."); return
            final_image_blob = None
            if self.current_image_pil: final_image_blob = self._convert_pil_to_blob(self.current_image_pil)
            elif self.current_image_blob: final_image_blob = self.current_image_blob
            if db.update_thongbao(notice_id, tieu_de, noi_dung, final_image_blob): 
                 messagebox.showinfo("Thành công", f"Cập nhật thông báo (ID: {notice_id}) thành công."); self._clear_notice_form(); self._load_notice_data()
            else: messagebox.showerror("Lỗi", "Cập nhật thông báo thất bại.")
        except Error as e: messagebox.showerror("Lỗi CSDL", f"Lỗi khi cập nhật thông báo: {e}", parent=self)
        except Exception as e: messagebox.showerror("Lỗi", f"Lỗi không xác định khi cập nhật thông báo: {e}", parent=self)

    def _delete_notice(self):
        # (Giữ nguyên)
        if not self.selected_notice_id: messagebox.showwarning("Chưa chọn", "Vui lòng chọn thông báo từ bảng để xóa."); return
        notice_id = self.selected_notice_id; tieu_de = self.notice_title_entry.get() 
        if messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc muốn xóa thông báo:\n'{tieu_de}' (ID: {notice_id})?", icon='warning', parent=self):
            try:
                if db.delete_thongbao(notice_id): 
                    messagebox.showinfo("Thành công", f"Xóa thông báo (ID: {notice_id}) thành công."); self._clear_notice_form(); self._load_notice_data()
                else: messagebox.showerror("Lỗi", "Xóa thông báo thất bại.")
            except Error as e: messagebox.showerror("Lỗi CSDL", f"Lỗi khi xóa thông báo: {e}", parent=self)
            except Exception as e: messagebox.showerror("Lỗi", f"Lỗi không xác định khi xóa thông báo: {e}", parent=self)