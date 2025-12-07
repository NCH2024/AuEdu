from dataclasses import dataclass, asdict
import json
import os
import base64

# HÀM MỚI: Lấy đường dẫn an toàn trong AppData
def get_user_config_path():
    """
    Lấy đường dẫn file config trong thư mục AppData của người dùng.
    Thư mục này luôn có quyền ghi.
    """
    app_data_dir = os.path.join(os.environ['APPDATA'], 'AUEDU')
    # Tự động tạo thư mục nếu chưa có
    os.makedirs(app_data_dir, exist_ok=True)
    return os.path.join(app_data_dir, 'config.json')

# Đường dẫn file config GIỜ ĐÂY sẽ trỏ đến AppData
CONFIG_PATH = get_user_config_path()

@dataclass
class LoginInfo:
    username: str = None    
    password: str = None

@dataclass
class CameraConfig:
    # Gán giá trị mặc định hợp lý
    selected_camera_id: int = 0 

@dataclass
class ThresholdSecurity:
    face_recognition_threshold: float = 0.60
    liveness_threshold: float = 0.40
    smooth_factor: int = 5

# --- PHẦN MỚI ---
@dataclass
class DatabaseConfig:
    # host: str = "localhost"
    # port: int = 3306
    # username: str = "root"
    # password: str = "1234"
    # database_name: str = "da2" #ĐÂY LÀ KẾT NỐI CỤC BỘ
    
    host: str = "mysql-bd31deb-chanhhiep-04d9.k.aivencloud.com"
    port: int = 25447
    username: str = "avnadmin"
    password: str = base64.b64decode("QVZOU19mWUoxNDFxSFBwRXFPUWxzS2sx").decode()
    database_name: str = "da2"
# --- KẾT THÚC PHẦN MỚI ---

@dataclass
class AppConfig:
    login_info: LoginInfo
    camera_config: CameraConfig
    threshold_security: ThresholdSecurity
    database: DatabaseConfig 

# Hàm chuyển từ dict -> dataclass (Đã cập nhật)
def dict_to_config(data: dict) -> AppConfig:
    return AppConfig(
        login_info=LoginInfo(**data.get("login_info", {})),
        camera_config=CameraConfig(**data.get("camera_config", {})),
        threshold_security=ThresholdSecurity(**data.get("threshold_security", {})),
        database=DatabaseConfig(**data.get("database", {})) 
    )

# Hàm load config TỪ AppData (Đã chỉnh sửa)
def load_config() -> AppConfig:
    config_file = get_user_config_path() # Sử dụng hàm mới
    
    if not os.path.exists(config_file):
        # NẾU FILE CHƯA TỒN TẠI: Tạo config mặc định và lưu lại
        print(f"Không tìm thấy file config, đang tạo file mới tại: {config_file}")
        default_config = AppConfig(
            login_info=LoginInfo(username=None, password=None),
            camera_config=CameraConfig(selected_camera_id=0),
            threshold_security=ThresholdSecurity(
                face_recognition_threshold=0.60,
                liveness_threshold=0.20,
                smooth_factor=5
            ),
            database=DatabaseConfig()
        )
        save_config(default_config) # Lưu file mặc định
        return default_config

    # NẾU FILE ĐÃ TỒN TẠI: Load file như bình thường
    try:
        with open(config_file, "r") as f:
            data = json.load(f)
            config = dict_to_config(data)

            # Kiểm tra và gán giá trị mặc định nếu các key bị thiếu
            if not hasattr(config, 'login_info') or config.login_info.username is None:
                config.login_info = LoginInfo()
            if not hasattr(config, 'camera_config') or config.camera_config.selected_camera_id is None:
                config.camera_config = CameraConfig()
            if not hasattr(config, 'threshold_security') or config.threshold_security.face_recognition_threshold is None:
                config.threshold_security = ThresholdSecurity()
            if not hasattr(config, 'database') or config.database.host is None:
                config.database = DatabaseConfig() 
                
            return config
    except Exception as e:
        print(f"Lỗi khi load config: {e}. Đang trả về config mặc định.")
        # Nếu file config bị lỗi, trả về config mặc định hoàn chỉnh
        return AppConfig(
            login_info=LoginInfo(), 
            camera_config=CameraConfig(), 
            threshold_security=ThresholdSecurity(),
            database=DatabaseConfig() 
        )

# Hàm lưu config VÀO AppData (Đã chỉnh sửa)
def save_config(config: AppConfig):
    config_file = get_user_config_path() # Sử dụng hàm mới
    try:
        with open(config_file, "w") as f:
            json.dump(asdict(config), f, indent=4)
    except Exception as e:
        print(f"Lỗi khi lưu config: {e}")