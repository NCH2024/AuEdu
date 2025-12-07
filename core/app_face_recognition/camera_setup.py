# app_face_recognition/camera_setup.py
import cv2
from pygrabber.dshow_graph import FilterGraph 
import core.app_config as app_config
import pythoncom


class CameraManager:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CameraManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, camera_id=None):
        if camera_id is not None:
            self.camera_id = camera_id
        else:
            self.camera_id = getattr(self, "camera_id", 0)

        if not getattr(self, "_initialized", False):
            self.camera = None
            self.is_opened = False
            self.capture_thread = None
            self._initialized = True


    def open_camera(self):
        try:
            if not self.is_opened:
                self.camera = cv2.VideoCapture(self.camera_id)
                
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                
                if not self.camera.isOpened():
                    raise Exception(f"Không thể mở camera với ID {self.camera_id}")
                self.is_opened = True
                print("Camera đã được mở thành công.")
            return True
        except Exception as e:
            print(f"Lỗi khi mở camera: {e}")
            self.is_opened = False
            return False

    def get_frame(self):
        if not self.is_opened or self.camera is None:
            return None
        ret, frame = self.camera.read()
        if not ret:
            # Camera có thể bị ngắt kết nối
            print("Không thể đọc khung hình, camera có thể đã bị ngắt kết nối.")
            self.release_camera()
            return None
        return frame
    
    def get_frame_as_generator(self):
        """
        Tạo một generator để lấy từng khung hình.
        """
        while self.is_opened:
            frame = self.get_frame()
            if frame is None:
                break
            yield frame

    def release_camera(self):
        if self.is_opened and self.camera:
            self.camera.release()
            self.is_opened = False
            self.camera = None
            print("Camera đã được giải phóng.")

    
    @staticmethod
    def list_available_cameras():
        """
        CHỈ liệt kê camera bằng pygrabber, KHÔNG xác thực bằng OpenCV.
        Trả về danh sách các tuple (id, name).
        """
        available_cameras = []
        try:
            pythoncom.CoInitialize()

            graph = FilterGraph()
            device_names = graph.get_input_devices()
            
            # Chỉ cần duyệt qua (enumerate) danh sách tên
            # Index ở đây là index từ list của pygrabber
            for index, name in enumerate(device_names):
                available_cameras.append((index, name))
                
            return available_cameras
        
        except Exception as e:
            # Nếu pygrabber thất bại, không có cách nào khác để lấy tên.
            # Bạn có thể trả về danh sách rỗng hoặc lại dùng fallback.
            print(f"Lỗi nghiêm trọng khi lấy danh sách camera (pygrabber): {e}")
            print("Không thể lấy danh sách tên camera.")
            return [] # Trả về rỗng vì không thể lấy tên