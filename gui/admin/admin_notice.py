
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
from datetime import datetime, date
from PIL import Image
from io import BytesIO
from gui.base.base_frame import BaseFrame
from gui.base.base_datepicker import DatePicker
from gui.base.utils import *
import core.database as db
from mysql.connector import Error
import os

class AdminNotice(BaseFrame):
    def __init__(self, master=None, user=None, **kwargs):
        super().__init__(master, **kwargs)
        self.user = user
        self.set_label_title("Dashboard > Trang Chủ > QUẢN LÝ THÔNG BÁO")
        
        try:
            self.temp_notice_dir = os.path.join(get_base_path(), "resources", "temp_notice_images")
            os.makedirs(self.temp_notice_dir, exist_ok=True)
        except Exception as e:
            print(f"Không thể tạo thư mục tạm: {e}")
            self.temp_notice_dir = "." # Fallback

        # --- Trạng thái ---
        self.selected_notice_id = None
        self.current_image_pil = None
        self.current_image_blob = None
        self.image_preview_label = None
        self.current_ctk_image = None # <<< Thêm dòng này để giữ tham chiếu CTkImage

        try:
            db.connect_db()
            self.setup_ui()
            self._load_notice_data()
        except Error as e:
             messagebox.showerror("Lỗi kết nối CSDL", f"Không thể kết nối CSDL: {e}\nVui lòng kiểm tra cấu hình.")
             for child in self.winfo_children():
                try: child.configure(state="disabled")
                except tk.TclError: pass
        except Exception as e:
             messagebox.showerror("Lỗi khởi tạo", f"Lỗi không xác định: {e}")

    # ... (setup_ui, on_expand, _create_notice_table giữ nguyên) ...
    def setup_ui(self):
        # Frame chính chia làm 2 cột: Trái (Form), Phải (Bảng)
        self.content_frame.grid_columnconfigure(0, weight=1) # Cột form
        self.content_frame.grid_columnconfigure(1, weight=2) # Cột bảng (rộng hơn)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # --- Frame Trái (Form Nhập liệu) ---
        form_frame = ctk.CTkFrame(self.content_frame, fg_color="white", corner_radius=10)
        form_frame.grid(row=0, column=0, padx=(5,2), pady=5, sticky="nsew")
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_rowconfigure(1, weight=0) # Tiêu đề
        form_frame.grid_rowconfigure(3, weight=1) # Nội dung (co giãn chính)
        form_frame.grid_rowconfigure(5, weight=0) # Image preview (không co giãn nhiều)
        form_frame.grid_rowconfigure(7, weight=0) # Buttons

        ctk.CTkLabel(form_frame, text="Tạo/Chỉnh sửa Thông báo:", font=("Bahnschrift", 16, "bold")).grid(
            row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        ctk.CTkLabel(form_frame, text="Tiêu đề:", font=("Bahnschrift", 13)).grid(
            row=1, column=0, padx=(10,2), pady=(5, 2), sticky="w")
        self.notice_title_entry = ctk.CTkEntry(form_frame, placeholder_text="Nhập tiêu đề thông báo...")
        self.notice_title_entry.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(form_frame, text="Nội dung:", font=("Bahnschrift", 13)).grid(
            row=3, column=0, padx=(10,2), pady=(0, 2), sticky="nw") # nw để label ở trên
        self.notice_content_textbox = ctk.CTkTextbox(form_frame, height=200, font=("Bahnschrift", 13), wrap="word")
        self.notice_content_textbox.grid(row=4, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="nsew")

        ctk.CTkLabel(form_frame, text="Hình ảnh:", font=("Bahnschrift", 13)).grid(
            row=5, column=0, padx=(10,2), pady=(0, 2), sticky="nw")
        
        image_control_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        image_control_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        image_control_frame.grid_columnconfigure(1, weight=1) # Preview co giãn

        self.select_image_btn = ctk.CTkButton(image_control_frame, text="Chọn ảnh", width=100, command=self._select_image)
        self.select_image_btn.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nw")

        self.image_preview_label = ctk.CTkLabel(image_control_frame, text="Chưa có ảnh", fg_color="#EAEAEA", text_color="gray", height=150, corner_radius=5)
        self.image_preview_label.grid(row=0, column=1, pady=5, sticky="ew")

        self.remove_image_btn = ctk.CTkButton(image_control_frame, text="Xóa ảnh", width=80, fg_color="#f44336", hover_color="#da190b", command=self._remove_image)
        self.remove_image_btn.grid(row=1, column=0, padx=(0, 10), pady=5, sticky="nw")
        
        btn_frame_notice = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame_notice.grid(row=7, column=0, columnspan=2, pady=10, padx=5, sticky="w")

        self.notice_add_btn = ctk.CTkButton(btn_frame_notice, text="Thêm", fg_color="#4CAF50", hover_color="#45A049", width=100, command=self._add_notice)
        self.notice_add_btn.pack(side="left", padx=5)
        self.notice_update_btn = ctk.CTkButton(btn_frame_notice, text="Cập nhật", fg_color="#2196F3", hover_color="#2f61d6b9", width=100, command=self._update_notice)
        self.notice_update_btn.pack(side="left", padx=5)
        self.notice_delete_btn = ctk.CTkButton(btn_frame_notice, text="Xóa", fg_color="#f44336", hover_color="#da190b", width=100, command=self._delete_notice)
        self.notice_delete_btn.pack(side="left", padx=5)
        self.notice_clear_btn = ctk.CTkButton(btn_frame_notice, text="Làm mới", fg_color="#607D8B", hover_color="#546E7A", width=100, command=self._clear_notice_form)
        self.notice_clear_btn.pack(side="left", padx=5)

        # --- Frame Phải (Bảng Hiển thị) ---
        table_frame = ctk.CTkFrame(self.content_frame, fg_color="white", corner_radius=10)
        table_frame.grid(row=0, column=1, padx=(2,5), pady=5, sticky="nsew")
        table_frame.grid_rowconfigure(1, weight=1) # Hàng bảng co giãn
        table_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(table_frame, text="Danh sách Thông báo:", font=("Bahnschrift", 16, "bold")).grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self._create_notice_table(table_frame) # Gọi hàm tạo bảng

    def _create_notice_table(self, parent_frame):
        # (Giữ nguyên)
        table_container = ctk.CTkFrame(parent_frame, fg_color="transparent")
        table_container.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        notice_cols = ("id", "tieu_de", "ngay_dang", "co_anh")
        self.notice_table = ttk.Treeview(table_container, columns=notice_cols, show="headings")
        self.notice_table.grid(row=0, column=0, sticky="nsew")
        self.notice_table.heading("id", text="ID"); self.notice_table.heading("tieu_de", text="Tiêu đề"); self.notice_table.heading("ngay_dang", text="Ngày đăng"); self.notice_table.heading("co_anh", text="Hình ảnh")
        self.notice_table.column("id", width=50, anchor="center", stretch=False); self.notice_table.column("tieu_de", width=300, anchor="w"); self.notice_table.column("ngay_dang", width=150, anchor="center"); self.notice_table.column("co_anh", width=80, anchor="center", stretch=False)
        notice_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.notice_table.yview); notice_scrollbar.grid(row=0, column=1, sticky="ns"); self.notice_table.configure(yscrollcommand=notice_scrollbar.set)
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