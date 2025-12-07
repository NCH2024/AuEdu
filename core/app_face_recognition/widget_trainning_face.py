import customtkinter as ctk
from gui.base.utils import *
from tkinter import messagebox
from core.models import SinhVien
import core.database as Db
from core.utils import *
from core.app_face_recognition.widget_camera import WidgetCamera
from core.app_face_recognition.camera_setup import CameraManager
import threading
import pygame
import cv2
from core.utils import get_base_path
import os

class WidgetTranningFace(ctk.CTkFrame):
    def __init__(self, master=None, username=None, controller=None, config=None, **kwargs):
        super().__init__(master, **kwargs)
        self.username = username
        self.controller = controller
        self.session_map = {}
        self.camera_manager = CameraManager(camera_id=config.camera_config.selected_camera_id)
        self.camera_widget = None
        self.is_camera_open = False
        self.toplevel_window = None

        base_path = get_base_path()
        self.sound_error = os.path.join(base_path, "./resources/sound/error.wav")
        self.sound_fail = os.path.join(base_path, "./resources/sound/fail.wav")
        self.sound_success = os.path.join(base_path, "./resources/sound/success.wav")


        self.configure(fg_color="white")
        self.widget_color = "#2DFCB0"
        self.txt_color_title = "#1736FF"

        # Cấu hình bố cục 3 cột ngay từ đầu
        self.pack(fill="both", expand=True)
        self.grid_columnconfigure(0, weight=0, minsize=700) # Cột 1 (cố định)
        self.grid_columnconfigure(1, weight=1) # Cột 2 (co giãn)
        self.grid_columnconfigure(2, weight=0, minsize=350) # Cột 3 (cố định)
        self.grid_rowconfigure(1, weight=1)

        # === TIÊU ĐỀ ===
        self.txt_title = LabelCustom(self, "Dashboard > Điểm danh sinh viên > Đào tạo dữ liệu khuôn mặt",wraplength=600, font_size=16, text_color="#05243F")
        self.txt_title.grid(row=0, column=0, columnspan=3, padx=15, pady=(10, 5), sticky="nw")

        # === KHUNG TRÁI (THÔNG TIN SINH VIÊN) ===
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=1, column=0, padx=(15, 7), pady=10, sticky="nsew")
        self.left_frame.grid_rowconfigure(0, weight=0)
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_propagate(False)

        # --- THÔNG TIN SINH VIÊN ---
        self.widget_student = ctk.CTkFrame(self.left_frame, fg_color="white", height=300, border_color=self.widget_color, border_width=2)
        self.widget_student.grid(row=0, column=0, sticky="nsew", pady=(0, 7))
        self.widget_student.grid_columnconfigure(0, weight=10)
        self.widget_student.grid_columnconfigure(1, weight=90)
        self.widget_student.grid_rowconfigure(0, weight=0)
        self.widget_student.grid_rowconfigure(1, weight=1)
        self.widget_student.grid_propagate(False)

        self.widget_student_title = LabelCustom(self.widget_student, "THÔNG TIN SINH VIÊN", font_size=12, text_color=self.txt_color_title)
        self.widget_student_title.grid(row=0, column=0, columnspan=2, padx=5, pady=2, sticky="nw")

        self.widget_student_image = ctk.CTkFrame(self.widget_student, fg_color="transparent")
        self.widget_student_image.grid(row=1, column=0, padx=(2,0), pady=2, sticky="nsew")

        self.bg_ctkimage = ImageProcessor(os.path.join(base_path,"resources/images/avatar_default.jpeg")) \
                                        .crop_to_aspect(160, 180) \
                                        .resize(160, 180) \
                                        .to_ctkimage(size=(160,180))
        self.bg_label = ctk.CTkLabel(self.widget_student_image, image=self.bg_ctkimage, text="")
        self.bg_label.pack(anchor="n", pady=5)

        self.widget_student_info = ctk.CTkFrame(self.widget_student, fg_color="transparent")
        self.widget_student_info.grid(row=1, column=1, padx=2, pady=2, sticky="nsew")

        self.txt_HoTen = LabelCustom(self.widget_student_info, "Họ và Tên: ", value="---")
        self.txt_Class = LabelCustom(self.widget_student_info, "Lớp: ", value="---")
        self.txt_Birthday = LabelCustom(self.widget_student_info, "Năm sinh: ", value="---")
        self.txt_Level = LabelCustom(self.widget_student_info, "Bậc học: ", value="---")
        self.txt_SchoolYear = LabelCustom(self.widget_student_info, "Niên khoá: ", value="---")
        self.txt_Specialized = LabelCustom(self.widget_student_info, "Chuyên ngành: ", value="---")
        self.txt_Notes = LabelCustom(self.widget_student_info, "Ghi chú: ", value="---")

        # --- THÔNG TIN DỮ LIỆU ---
        self.widget_aboutAttendance = ctk.CTkFrame(
            self.left_frame,
            fg_color="white",
            border_color=self.widget_color,
            border_width=2,
            height=120
        )
        self.widget_aboutAttendance.grid(row=1, column=0, sticky="nsew")
        self.widget_aboutAttendance.grid_columnconfigure((0, 1), weight=1)
        self.widget_aboutAttendance.grid_propagate(False)

        self.widget_aboutAttendance_title = LabelCustom(
            self.widget_aboutAttendance,
            "THÔNG TIN DỮ LIỆU KHUÔN MẶT",
            font_size=12,
            text_color=self.txt_color_title
        )
        self.widget_aboutAttendance_title.pack(anchor="w", padx=5, pady=(5, 2))

        self.widget_aboutAttendance_content1 = LabelCustom(self.widget_aboutAttendance, "DỮ LIỆU KHUÔN MẶT: ", value="---")
        self.widget_aboutAttendance_content2 = LabelCustom(self.widget_aboutAttendance, "THỜI GIAN LƯU TRỮ: ", value="---")

        # === KHUNG PHẢI (CÁC NÚT ĐIỀU KHIỂN) ===
        self.widget_search = ctk.CTkFrame(self, fg_color=self.widget_color)
        self.widget_search.grid(row=1, column=2, padx=(7, 15), pady=10, sticky="nsew")
        self.widget_search.grid_columnconfigure(0, weight=1)
        self.widget_search.grid_columnconfigure(1, weight=1)
        self.widget_search.grid_rowconfigure(0, weight=0)
        self.widget_search.grid_propagate(False)

        self.widget_search_title = LabelCustom(self.widget_search, "ĐÀO TẠO NHẬN DẠNG", font_size=12, text_color=self.txt_color_title)
        self.widget_search_title.grid(row=0, column=0, columnspan=2, padx=5, pady=0, sticky="nw")

        self.ent_IDStudent = ctk.CTkEntry(self.widget_search, placeholder_text="Nhập vào MSSV",
                                          width=100, height=40, font=("Bahnschrift", 12))
        self.ent_IDStudent.grid(row=1, column=0, padx=(10,0), pady=0, sticky="nw")

        self.btn_searchQuickly = ButtonTheme(self.widget_search, "Tìm kiếm", font=("Bahnschrift", 12, "normal"), width=100, command=self.cobo_search_showDataTrain)
        self.btn_searchQuickly.grid(row=1, column=1, padx=(0,10), pady=0, sticky="ne")

        self.widget_search_title = LabelCustom(self.widget_search, "Chọn chế độ đào tạo: ", font_size=12, text_color=self.txt_color_title)
        self.widget_search_title.grid(row=2, column=0, columnspan=2, padx=10, pady=(20, 0), sticky="nw")

        self.cbx_subject = ComboboxTheme(self.widget_search, values=["Đào tạo chuyên sâu", "Đào tạo nhanh"], width=200)
        self.cbx_subject.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="nwe")

        self.cbx_tooltip = Tooltip(self.cbx_subject, "Chọn chế độ đào tạo khuôn mặt cho sinh viên.\nChế độ chuyên sâu sẽ yêu cầu nhiều ảnh hơn và tốn thời gian hơn!")

        self.check_setflip = SwitchOption(self.widget_search, "Lật ảnh (dùng cho camera trước)", wraplenght=110, initial=False, command=self.check_option)
        self.check_setflip.grid(row=4, column=0, columnspan=2, padx=5, pady=20, sticky="nwe")

        self.btn_toggle_camera = ButtonTheme(self.widget_search, "Mở Camera",font=("Bahnschrift", 12, "normal"), width=100,command=self.toggle_camera)
        self.btn_toggle_camera.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="nwe")

        self.btn_tranning = ButtonTheme(self.widget_search, "Đào tạo dữ liệu", font=("Bahnschrift", 12, "normal"),width=100, command=self.train_data)
        self.btn_tranning.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="new")

        self.progress_bar = None


        # Ban đầu, ẩn khung camera
        self.camera_frame = None
        
        self.ent_IDStudent.bind("<Return>", lambda event: self.cobo_search_showDataTrain())

    # === HÀM CHỨC NĂNG ===

    def _fix_none(self, val):
            return "Chưa có dữ liệu" if val is None or (isinstance(val, str) and val.strip() == "") else str(val)
        
    def play_sound(self, path):
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            
    def check_option(self, is_checked=bool):
        if is_checked:
            ToastNotification(self, "Đã bật tùy chọn chức năng lật ảnh", duration=2000)
        else:
            ToastNotification(self, "Đã tắt tùy chọn chức năng lật ảnh", duration=2000)

        # Nếu camera đang mở, cập nhật ngay lập tức
        if self.is_camera_open:
            self.recreate_camera_widget()

    def _update_student_info(self, sv_tuple):
        ten_bac = self._fix_none(sv_tuple[1])
        ten_nienkhoa = self._fix_none(sv_tuple[2])
        ten_nganh = self._fix_none(sv_tuple[3])
        sv = SinhVien(
            MaSV=sv_tuple[0],
            MaBac=sv_tuple[4],
            MaNienKhoa=sv_tuple[5],
            MaNganh=sv_tuple[6],
            STTLop=sv_tuple[7],
            HoTenSV=sv_tuple[8],
            NamSinh=sv_tuple[9],
            DiaChi=sv_tuple[10],
            GioiTinh=sv_tuple[11],
            GhiChu=sv_tuple[12]
        )
        self.txt_Level.value.configure(text=ten_bac)
        self.txt_SchoolYear.value.configure(text=ten_nienkhoa)
        self.txt_Specialized.value.configure(text=ten_nganh)
        self.txt_Class.value.configure(text=f"{self._fix_none(sv.MaBac)}{self._fix_none(sv.MaNienKhoa)}{self._fix_none(sv.MaNganh)}{self._fix_none(sv.STTLop)}")
        self.txt_HoTen.value.configure(text=self._fix_none(sv.HoTenSV))
        self.txt_Birthday.value.configure(text=self._fix_none(sv.NamSinh))
        self.txt_Notes.value.configure(text=self._fix_none(sv.GhiChu))

    def search_student(self):
        maSV = self.ent_IDStudent.get().strip()
        # Gọi hàm từ controller để tìm kiếm
        sv_tuple = Db.get_student_by_id(maSV)

        if not sv_tuple:
            ToastNotification(self, f"Không tìm thấy sinh viên với MSSV {maSV}. Vui lòng nhập MSSV hợp lệ.", duration=3000)
            self.txt_Level.value.configure(text="-----")
            self.txt_SchoolYear.value.configure(text="-----")
            self.txt_Specialized.value.configure(text="-----")
            self.txt_Class.value.configure(text="-----")
            self.txt_HoTen.value.configure(text="-----")
            self.txt_Birthday.value.configure(text="-----")
            self.txt_Notes.value.configure(text="-----")
            threading.Thread(target=lambda: self.play_sound(self.sound_error), daemon=True).start()
            return
        self._update_student_info(sv_tuple)

    def toggle_camera(self):
        window = self.master
        if not self.is_camera_open:
            if self.camera_manager.open_camera():
                self.is_camera_open = True
                self.btn_toggle_camera.configure(text="Đóng Camera")
                self.recreate_camera_widget()

                # Thay đổi kích thước cửa sổ
                window.geometry("1400x520")
            else:
                messagebox.showerror("Lỗi", "Không thể mở camera.")
        else:
            self.is_camera_open = False
            self.btn_toggle_camera.configure(text="Mở Camera")
            self.camera_manager.release_camera()

            # khi đóng
            self.stop_camera_preview()
            if self.camera_widget:
                self.camera_widget.destroy()
            if self.camera_frame:
                self.camera_frame.destroy()

                        
            # Thu nhỏ cửa sổ về kích thước ban đầu
            window.geometry("850x520")

    def recreate_camera_widget(self):
        """Hàm hủy widget camera cũ và tạo lại cái mới với tham số lật ảnh."""
        # Nếu widget camera đã tồn tại, hủy nó đi
        if self.camera_widget:
            self.camera_widget.destroy()
        if self.camera_frame:
            self.camera_frame.destroy()

        # Tạo và đặt lại khung camera
        self.camera_frame = ctk.CTkFrame(self, fg_color=self.widget_color)
        self.camera_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.camera_frame.grid_propagate(False)

        # Lấy trạng thái mới nhất từ nút gạt và tạo widget mới
        self.camera_widget = WidgetCamera(master=self.camera_frame,
                                          camera_manager=self.camera_manager,
                                          open_as_toplevel=False,
                                          flip_camera=self.check_setflip.get_value())
        self.camera_widget.pack(fill="both", expand=True)
        self.start_camera_preview()

    def train_data(self):
        maSV = self.ent_IDStudent.get().strip()
        if not maSV:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập MSSV để đào tạo.")
            return

        sv_tuple = Db.get_student_info_by_ma_sv(maSV)
        print(sv_tuple)
        if not sv_tuple:
            messagebox.showinfo("Không tìm thấy", f"Không tìm thấy sinh viên với MSSV {maSV}. Vui lòng nhập MSSV hợp lệ.")
            return

        if not self.is_camera_open:
            self.toggle_camera()
            if not self.is_camera_open:
                return

        # Lấy chế độ đào tạo từ combobox
        mode = "deep" if self.cbx_subject.get() == "Đào tạo chuyên sâu" else "quick"

        training_generator = self.controller.start_training(
            student_id=maSV,
            frame_generator=self.camera_manager.get_frame_as_generator(), 
            mode=mode
        )

        # Xử lý kết quả từ generator
        self.process_training_frames(training_generator)

    def process_training_frames(self, training_generator):
        """
        Xử lý từng bước của quá trình đào tạo.
        """
        self.progress_bar = ctk.CTkProgressBar(self.widget_search, width=200, progress_color="#040F53")
        self.progress_bar.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky="we")
        self.progress_bar.set(0)  # ban đầu = 0
        try:
            progress, message = next(training_generator)
            if progress < 100:
                self.progress_bar.set(progress / 100.0)

                self.after(50, lambda: self.process_training_frames(training_generator))
            else:
                self.progress_bar.set(1.0)
                if message == "success":
                    self.t = ToastNotification(self, "Thành công, Đào tạo dữ liệu khuôn mặt hoàn tất.", duration=5000)
                    threading.Thread(target=lambda: self.play_sound(self.sound_success), daemon=True).start()
                    self.cobo_search_showDataTrain()
                else:
                    self.t = ToastNotification(self, f"Thất bại, {message}", duration=5000)

                    threading.Thread(target=lambda: self.play_sound(self.sound_fail), daemon=True).start()
        except StopIteration:
            print("Quá trình đào tạo hoàn tất.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")
            threading.Thread(target=lambda: self.play_sound(self.sound_fail), daemon=True).start()

        self.progress_bar = None
        
        
    def setup_image(self, image_data):
        MaSV = self.ent_IDStudent.get().strip()
        if not MaSV:
            self.set_default_image()
            return
        if image_data:
            try:
                # Tạo một instance ImageProcessor từ byte data
                processor = ImageProcessor(image_data)
                
                # Đặt tên file theo mã sinh viên
                filename = f"{MaSV}_avatar.png"
                
                # Lưu ảnh vào thư mục 'image_student' và lấy đường dẫn
                saved_path = processor.save_to_dir(filename)
                
                # Nếu lưu thành công, cập nhật ảnh trên giao diện
                if saved_path:
                    ctk_image = ImageProcessor(saved_path) \
                                            .crop_to_aspect(160, 180) \
                                            .resize(160, 180) \
                                            .to_ctkimage(size=(160, 180))
                    
                    # Cập nhật label với ảnh mới
                    self.bg_label.configure(image=ctk_image)
                    self.bg_label.image = ctk_image # Giữ tham chiếu
                else:
                    self.set_default_image() # Hàm riêng để hiển thị ảnh mặc định

            except Exception as e:
                print(f"Lỗi khi xử lý hoặc lưu ảnh: {e}")
                self.set_default_image()
        else:
            # Nếu không có dữ liệu ảnh, hiển thị ảnh mặc định
            self.set_default_image()
            
    def set_default_image(self):
        self.bg_ctkimage = ImageProcessor(os.path.join(get_base_path(),"resources","images","avatar_default.jpeg")) \
                                        .crop_to_aspect(160, 180) \
                                        .resize(160, 180) \
                                        .to_ctkimage(size=(160, 180))
        self.bg_label.configure(image=self.bg_ctkimage)
        self.bg_label.image = self.bg_ctkimage # Giữ tham chiếu
            
            
    def show_data_train(self):
        MaSV = self.ent_IDStudent.get().strip()
        result = Db.get_data_face_trainning(MaSV)
        if result:
            AnhDaiDien, FaceEncoding, ThoiGianTao = result
            # Cập nhật giao diện với dữ liệu lấy được
            self.setup_image(AnhDaiDien)
            self.widget_aboutAttendance_content2.value.configure(text=f"Thời gian tạo: {ThoiGianTao}")
            if FaceEncoding:
                self.widget_aboutAttendance_content1.value.configure(text="Đã đào tạo dữ liệu khuôn mặt.")
            else:
                self.widget_aboutAttendance_content1.value.configure(text="Chưa có dữ liệu khuôn mặt.")
        else:
            self.set_default_image()
            self.widget_aboutAttendance_content2.value.configure(text="Chưa có thông tin.")
            self.widget_aboutAttendance_content1.value.configure(text="Chưa có dữ liệu khuôn mặt.")
            
    def cobo_search_showDataTrain(self):
        MaSV = self.ent_IDStudent.get().strip()
        if not MaSV:
            ToastNotification(self, "Vui lòng nhập MSSV để tìm kiếm.", duration=2000)
            threading.Thread(target=lambda: self.play_sound(self.sound_error), daemon=True).start()
            return
        self.search_student()
        self.show_data_train() 
    
    # --- preview loop quản lý việc hiển thị live feed vào WidgetCamera ---
    _camera_preview_running = False
    _camera_preview_after_id = None
    _preview_gen = None

    def start_camera_preview(self, interval_ms=30):
        if not self.camera_widget or not self.camera_manager:
            return
        # nếu đang chạy thì thôi
        if getattr(self, "_camera_preview_running", False):
            return
        self._camera_preview_running = True

        def _loop():
            if not self._camera_preview_running or not self.is_camera_open:
                return
            try:
                frame = None
                # ưu tiên method get_frame nếu CameraManager cung cấp
                if hasattr(self.camera_manager, "get_frame"):
                    frame = self.camera_manager.get_frame()
                else:
                    # fallback: dùng generator từ camera_manager
                    try:
                        if getattr(self, "_preview_gen", None) is None:
                            self._preview_gen = self.camera_manager.get_frame_as_generator()
                        frame = next(self._preview_gen)
                    except StopIteration:
                        frame = None
                    except Exception:
                        frame = None

                if frame is not None:
                    # lật nếu người dùng bật
                    if self.check_setflip.get_value():
                        frame = cv2.flip(frame, 1)
                    # gọi set_image trên UI thread
                    try:
                        self.camera_widget.after(0, lambda f=frame: self.camera_widget.set_image(f))
                    except Exception:
                        pass
                else:
                    # nếu không có frame, vẫn gọi để hiển thị text lỗi trong widget
                    try:
                        self.camera_widget.after(0, lambda: self.camera_widget.set_image(None))
                    except Exception:
                        pass
            except Exception as e:
                print("Preview loop error:", e)
            finally:
                # lập lịch lần tiếp theo
                try:
                    self._camera_preview_after_id = self.after(interval_ms, _loop)
                except Exception:
                    self._camera_preview_after_id = None

        _loop()

    def stop_camera_preview(self):
        self._camera_preview_running = False
        if getattr(self, "_preview_gen", None):
            try:
                self._preview_gen.close()
            except Exception:
                pass
            self._preview_gen = None
        if getattr(self, "_camera_preview_after_id", None):
            try:
                self.after_cancel(self._camera_preview_after_id)
            except Exception:
                pass
            self._camera_preview_after_id = None


    _window_instance = None
    @classmethod
    def show_window(cls, parent=None, username=None, controller=None, config=None):
        if cls._window_instance is None or not cls._window_instance.winfo_exists():
            top = ctk.CTkToplevel()
            top.geometry("850x520")
            top.title("Đào tạo dữ liệu khuôn mặt")
            top.configure(fg_color="white")
            if parent:
                top.transient(parent.winfo_toplevel())
            top.lift()
            top.focus_force()
            cls._window_instance = top
                        
            # Truyền controller vào widget_instance khi khởi tạo
            widget_instance = cls(master=top, username=username, controller=controller, config=config)
            widget_instance.toplevel_window = top
                        
            top.protocol("WM_DELETE_WINDOW", widget_instance.on_close)
        else:
            cls._window_instance.focus_force()
                        
    def on_close(self):
        if self.camera_manager:
            self.camera_manager.release_camera()
        if self.toplevel_window:
            self.toplevel_window.destroy()
        self.__class__._window_instance = None
        
