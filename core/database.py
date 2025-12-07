'''
FILE NAME: core/database.py
CODE BY: Nguyễn Chánh Hiệp 
DATE: 22/06/2025
DESCRIPTION:
        + Đây là file chứa các hàm tương tác với cơ sở dữ liệu
        + Định nghĩa các hàm lấy dữ liệu, lưu trữ dữ liệu
        + Các hàm này sẽ được sử dụng để hỗ trợ cho các model và controller
VERSION: 1.0.0
'''
from socket import timeout
import mysql.connector
from core.utils import *
from PIL import Image
from datetime import datetime, timedelta
import io
import json
import pickle
import numpy as np
import core.app_config as AppConfig


def connect_db():
    """
    Kết nối đến cơ sở dữ liệu MySQL.
    (Đã cập nhật để đọc từ config.json trong AppData)
    """
    # Tải config mỗi lần gọi
    try:
        config = AppConfig.load_config()
        db_settings = {
            'host': config.database.host,
            'user': config.database.username,
            'password': config.database.password,
            'database': config.database.database_name,
            'port': config.database.port,
            'ssl_disabled': False
        }
    except Exception as e:
        print(f"Không thể đọc DB config từ app_config: {e}")
        return None

    try:
        connection = mysql.connector.connect(**db_settings)
        return connection
    except mysql.connector.Error as err:
        # In lỗi cụ thể để người dùng biết
        print(f"Lỗi kết nối CSDL: {err}")
        print(f"Hãy kiểm tra file config.json trong %APPDATA%/DACS2_App")
        return None
    
# DB_CONFIG = {
#         'host': 'localhost',
#         'user': 'root',
#         'password': '1234',
#         'database': 'da2'
#         }


# def connect_db():
#     """
#     Kết nối đến cơ sở dữ liệu MySQL.
#     Trả về một kết nối vào cơ sở dữ liệu.
#     """
#     try:
#         connection = mysql.connector.connect(**DB_CONFIG)
#         return connection
#     except mysql.connector.Error as err:
#         print(f"Error: {err}")
#         return None
    
    
# ĐOẠN KẾT NỐI DƯỚI ĐÂY ĐANG THỬ NGHIỆM CHO CLOUD DATABASE AIVEN (Do vẫn còn lỗi nên chưa áp dụng thực tế)
# DB_CONFIG = {
#     'host': 'mysql-bd31deb-chanhhiep-04d9.k.aivencloud.com',
#     'user': 'avnadmin',
#     'password': 'AVNS_fYJ141qHPpEqOQlsKk1',
#     'database': 'da2',
#     'port': 25447,
#     'ssl_disabled': False
# }

# def connect_db():
#     try:
#         connection = mysql.connector.connect(**DB_CONFIG)
#         if connection.is_connected():
#             return connection
#     except Error as err:
#         print(f"Database connection error: {err}")
#         return None


    
def login(username, password):
    conn = connect_db()
    if conn is None:
        return False
    cursor = conn.cursor(buffered=True)

    cursor.execute("SELECT TenDangNhap, MatKhau, VaiTro FROM taikhoan WHERE TenDangNhap = %s", (username,))
    result = cursor.fetchone()

    if not result:
        return False

    user_id, bcrypt_password, role = result
        
    print(f"user_id: {user_id}, role: {role}")

    if check_password(password, bcrypt_password):
        return user_id, role
    else:
        return False
    
def update_password(username, new_password):
    """Cập nhật mật khẩu mới cho người dùng sau khi đã mã hóa."""
    conn = None # Khởi tạo để dùng trong finally
    try:
        conn = connect_db()
        if conn is None:
            print("Lỗi: Không thể kết nối tới cơ sở dữ liệu.")
            return False
        
        cursor = conn.cursor()

        # 1. Gọi hàm mã hóa từ file utils.py của bạn
        hashed_new_password = bcrypt_password(new_password)

        # 2. Chuẩn bị và thực thi câu lệnh UPDATE an toàn
        sql_query = "UPDATE taikhoan SET MatKhau = %s WHERE TenDangNhap = %s"
        cursor.execute(sql_query, (hashed_new_password, username))

        # 3. Xác nhận và lưu thay đổi vào CSDL
        conn.commit()
        
        print(f"Đã cập nhật mật khẩu thành công cho người dùng: {username}")
        return True

    except mysql.connector.Error as err:
        # Nếu có lỗi, hủy bỏ các thay đổi
        if conn:
            conn.rollback()
        print(f"Có lỗi xảy ra khi cập nhật mật khẩu: {err}")
        return False
        
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_username(tendangnhap):
    conn = connect_db()
    if conn is None:
        return False
    cursor = conn.cursor(buffered=True)

    cursor.execute("SELECT gv.TenGiangVien FROM taikhoan tk JOIN giangvien gv ON tk.MaGV = gv.MaGV WHERE tk.TenDangNhap = %s;", (tendangnhap,))
    result = cursor.fetchone()

    if result:
        return result[0]
    else :
        return False


def get_info_lecturer(tendangnhap):
    conn = connect_db()
    if conn is None:
        return False
    cursor = conn.cursor(buffered=True)
    cursor.execute("SELECT gv.MaGV, gv.TenGiangVien, gv.SDT, gv.MaKhoa, gv.NamSinh, gv.GhiChu FROM taikhoan tk JOIN giangvien gv ON tk.MaGV = gv.MaGV WHERE tk.TenDangNhap = %s;", (tendangnhap,))
    result = cursor.fetchone()
    
    MaGV, TenGiangVien, SDT, MaKhoa, NamSinh, GhiChu = result
    if result:
        return MaGV, TenGiangVien, SDT, MaKhoa, NamSinh, GhiChu
    else:
        return False
    

def get_thongbao():
    conn = connect_db()
    if conn is None:
        return False
    cursor = conn.cursor(buffered=True)
    cursor.execute("SELECT thongbao_id, TieuDeThongBao, NoiDung, NgayDang, HinhAnh FROM thongbao order by NgayDang DESC")
    results = []

    for row in cursor.fetchall():
        thongbao_id, title, content, ngay_dang, image_blob = row
        # Chuyển ảnh blob thành PIL Image
        image = None
        if image_blob:
            try:
                image = Image.open(io.BytesIO(image_blob))
            except Exception as e:
                print(f"Lỗi khi mở ảnh thông báo (ID: {thongbao_id}): {e}. Bỏ qua ảnh này.")
        else:
            image = None
        
        results.append((thongbao_id, title, content, ngay_dang, image))

    cursor.close()
    conn.close()
    return results



        
def get_schedule(tendangnhap):
    conn = connect_db()
    cursor = conn.cursor(buffered=True)
    cursor.execute("SELECT * FROM view_lichphancong WHERE TenDangNhap = %s;", (tendangnhap, ))
    data = []
    
    for row in cursor.fetchall():
        tendangnhap, tenlop, tenhocphan, hocky, sobuoi = row
        data.append((tenlop, tenhocphan, hocky, sobuoi))
        
    if data:
        return data
    else:
        return False
    
def get_classes_of_lecturer(username):
    conn = connect_db()
    cursor = conn.cursor(buffered=True)
    cursor.execute("""
        SELECT DISTINCT TenLop 
        FROM view_lichphancong
        WHERE TenDangNhap = %s;
    """, (username,))
    result = cursor.fetchall()
    conn.close()
    return [row[0] for row in result]

def get_subjects_by_class(username, class_name):
    conn = connect_db()
    cursor = conn.cursor(buffered=True)
    cursor.execute("""
        SELECT DISTINCT TenHocPhan 
        FROM view_lichphancong
        WHERE TenDangNhap = %s AND TenLop = %s;
    """, (username, class_name))
    result = cursor.fetchall()
    conn.close()
    return [row[0] for row in result]


def get_schedule_by_week(class_name, subject_name, week_offset=0):
    conn = connect_db()
    cursor = conn.cursor(buffered=True)

    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=6)

    cursor.execute("""
        SELECT TenLop, TenHocPhan, MaBuoiHoc, NgayHoc, Thu, GhiChu, MaLoaiBuoiDiemDanh, MaLopHocPhan, TietHoc
        FROM view_lichdiemdanh_lop
        WHERE TenLop = %s AND TenHocPhan = %s
            AND NgayHoc BETWEEN %s AND %s
        ORDER BY NgayHoc ASC;

         """, (class_name, subject_name, start_of_week.date(), end_of_week.date()))

    result = cursor.fetchall()
    conn.close()

    return result

def get_subject_detail_from_hocphan(subject_name):
    conn = connect_db()
    cursor = conn.cursor(buffered=True)
    cursor.execute("""
        SELECT MaHocPhan, TenHocPhan, SoTinChi, TongSoTiet
        FROM hocphan
        WHERE TenHocPhan = %s
        LIMIT 1
    """, (subject_name,))
    row = cursor.fetchone()
    return row if row else ("", "", "", "")

def get_student_by_id(maSV):
    conn = connect_db()
    cursor = conn.cursor(buffered=True)
    cursor.execute("""
        SELECT 
            sv.MaSV, 
            b.TenBac,         -- Tên bậc học
            nk.TenNienKhoa,   -- Tên niên khoá
            n.TenNganh,       -- Tên ngành
            sv.MaBac,
            sv.MaNienKhoa,
            sv.MaNganh,
            sv.STTLop,
            sv.HoTenSV,
            sv.NamSinh,
            sv.DiaChi,
            sv.GioiTinh,
            sv.GhiChu
        FROM sinhvien sv
        LEFT JOIN bac b ON sv.MaBac = b.MaBac
        LEFT JOIN nienkhoa nk ON sv.MaNienKhoa = nk.MaNienKhoa
        LEFT JOIN nganh n ON sv.MaNganh = n.MaNganh
        WHERE sv.MaSV = %s
    """, (maSV,))
    return cursor.fetchone()

def get_subjects_of_lecturer(username):
    conn = connect_db()
    cursor = conn.cursor(buffered=True)
    cursor.execute("""
        SELECT DISTINCT hp.TenHocPhan
        FROM taikhoan tk
        JOIN giangvien gv ON tk.MaGV = gv.MaGV
        JOIN lophocphan lhp ON lhp.MaGV = gv.MaGV
        JOIN hocphan hp ON lhp.MaHocPhan = hp.MaHocPhan
        WHERE tk.TenDangNhap = %s
    """, (username,))
    result = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return result

def get_dates_of_subject(username, ten_hocphan):
    conn = connect_db()
    cursor = conn.cursor(buffered=True)
    cursor.execute("""
        SELECT DISTINCT bh.NgayHoc
        FROM taikhoan tk
        JOIN giangvien gv ON tk.MaGV = gv.MaGV
        JOIN lophocphan lhp ON lhp.MaGV = gv.MaGV
        JOIN hocphan hp ON lhp.MaHocPhan = hp.MaHocPhan
        JOIN buoihoc bh ON bh.MaLopHocPhan = lhp.MaLopHocPhan
        WHERE tk.TenDangNhap = %s AND hp.TenHocPhan = %s
        ORDER BY bh.NgayHoc DESC
    """, (username, ten_hocphan))
    result = [row[0].strftime("%d/%m/%Y") if hasattr(row[0], 'strftime') else str(row[0]) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return result

def get_sessions_of_date(username, ten_hocphan, ngay):
    conn = connect_db()
    cursor = conn.cursor(buffered=True)
    try:
        date_obj = datetime.strptime(ngay, "%d/%m/%Y")
        ngay_sql = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return []

    cursor.execute("""
        select concat(Min(ct.MaTiet), '-' , Max(ct.MaTiet))
        from taikhoan tk
        join giangvien gv on tk.MaGV = gv.MaGV
        join lophocphan lhp on lhp.MaGV = gv.MaGV
        join hocphan hp on hp.MaHocPhan = lhp.MaHocPhan
        join buoihoc bh on bh.MaLopHocPhan = lhp.MaLopHocPhan
        join chitietbuoihoc ct on ct.MaBuoiHoc = bh.MaBuoiHoc
        where 
            tk.TenDangNhap = %s AND
            hp.TenHocPhan = %s AND
            bh.NgayHoc = %s
            
    """, (username, ten_hocphan, ngay_sql))

    result = [str(row[0]) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return result



def get_loai_diem_danh(username, ten_hocphan, ngay):
    conn = connect_db()
    cursor = conn.cursor(buffered=True)

    try:
        date_obj = datetime.strptime(ngay, "%d/%m/%Y")
        ngay_sql = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        print("Lỗi định dạng ngày!")
        return []

    cursor.execute("""
        SELECT DISTINCT ldd.MaLoaiBuoiDiemDanh, ldd.TenLoaiBuoiDiemDanh
        FROM taikhoan tk
        JOIN giangvien gv ON tk.MaGV = gv.MaGV
        JOIN lophocphan lhp ON lhp.MaGV = gv.MaGV
        JOIN hocphan hp ON lhp.MaHocPhan = hp.MaHocPhan
        JOIN buoihoc bh ON bh.MaLopHocPhan = lhp.MaLopHocPhan
        JOIN loaibuoidiemdanh ldd ON bh.MaLoaiBuoiDiemDanh = ldd.MaLoaiBuoiDiemDanh
        WHERE tk.TenDangNhap = %s AND hp.TenHocPhan = %s AND bh.NgayHoc = %s
    """, (username, ten_hocphan, ngay_sql))

    result = cursor.fetchall()
    cursor.close()
    conn.close()

    # Lưu dưới dạng dict: {tên: mã}
    return {ten: ma for ma, ten in result}

def get_attendance_of_student(maSV, ten_hocphan, ngay, buoi):  
    conn = connect_db()
    cursor = conn.cursor(buffered=True)
    cursor.execute("""
                        SELECT 
                            hp.TenHocPhan,
                            bh.NgayHoc,
                            bh.MaLoaiBuoiDiemDanh,
                            dd.ThoiGianGhiNhan,
                            tt.TenTrangThai
                        FROM buoihoc bh
                        JOIN lophocphan lhp ON bh.MaLopHocPhan = lhp.MaLopHocPhan
                        JOIN hocphan hp ON lhp.MaHocPhan = hp.MaHocPhan
                        LEFT JOIN diemdanhsv dd ON dd.MaBuoiHoc = bh.MaBuoiHoc AND dd.MaSV = %s
                        LEFT JOIN trangthaidiemdanh tt ON dd.MaTrangThai = tt.MaTrangThai
                        WHERE TRIM(hp.TenHocPhan) = %s
                        AND bh.NgayHoc = %s
                        AND UPPER(TRIM(bh.MaLoaiBuoiDiemDanh)) = UPPER(%s)
                    """, (maSV, ten_hocphan.strip(), ngay, buoi.strip()))
    
    result = cursor.fetchone()
    return result

def get_attendance_list_of_class(class_name, subject_name, ngay, buoi):
    conn = connect_db()
    cursor = conn.cursor(buffered=True) # Sử dụng buffered=True để tránh lỗi nếu có nhiều kết quả

    try:
        # Chuyển đổi ngày sang định dạng 'YYYY-MM-DD' để phù hợp với tham số DATE của Stored Procedure
        date_obj = datetime.strptime(ngay, "%d/%m/%Y")
        ngay_sql = date_obj.strftime("%Y-%m-%d")
    except ValueError:
        print("Lỗi định dạng ngày. Vui lòng nhập ngày theo định dạng dd/mm/YYYY (ví dụ: 15/01/2025).")
        if conn:
            conn.close()
        return []

    try:
        # Gọi Stored Procedure và truyền các tham số
        # Tên Stored Procedure là GetAttendanceListByClass
        # Tham số truyền vào phải đúng thứ tự: class_name, subject_name, ngay, buoi
        call_proc_sql = "CALL GetAttendanceListByClass(%s, %s, %s, %s);"
        
        # Thực thi Stored Procedure với các tham số đã chuẩn bị
        cursor.execute(call_proc_sql, (class_name, subject_name, ngay_sql, buoi))

        # Lấy tất cả kết quả trả về từ Stored Procedure
        results = cursor.fetchall()
        
    except Exception as e:
        # Xử lý lỗi nếu có vấn đề khi gọi Stored Procedure
        print(f"Lỗi khi gọi Stored Procedure 'GetAttendanceListByClass': {e}")
        results = [] # Trả về danh sách rỗng nếu có lỗi
    finally:
        # Đảm bảo kết nối database luôn được đóng
        if conn:
            conn.close()
    
    return results

def get_data_face_trainning(MaSV):
    conn = connect_db()
    if conn is None:
        return None

    try:
        cursor = conn.cursor(buffered=True)
        query = "SELECT AnhDaiDien, FaceEncoding, ThoiGianTao FROM dulieukhuonmat WHERE MaSV = %s"
        cursor.execute(query, (MaSV,))
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as err:
        print(f"Lỗi khi truy vấn dữ liệu khuôn mặt cho MaSV {MaSV}: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def load_face_encodings():
    """
    Tải tất cả các FaceEncoding và MaSV tương ứng từ bảng dulieukhuonmat vào bộ nhớ.
    Trả về hai danh sách: known_face_encodings và known_face_student_ids.
    """
    known_face_encodings = []
    known_face_student_ids = []
    conn = connect_db()
    if conn is None:
        return known_face_encodings, known_face_student_ids

    try:
        cursor = conn.cursor(buffered=True)
        query = "SELECT MaSV, FaceEncoding FROM dulieukhuonmat"
        cursor.execute(query)

        for (ma_sv, face_encoding_blob) in cursor:
            try:
                # Giải mã dữ liệu BLOB thành mảng numpy
                face_encoding_array = pickle.loads(face_encoding_blob)
                known_face_encodings.append(face_encoding_array)
                known_face_student_ids.append(ma_sv)
            except Exception as e:
                print(f"Lỗi khi giải mã FaceEncoding cho MaSV {ma_sv}: {e}")
                continue

    except mysql.connector.Error as err:
        print(f"Lỗi khi truy vấn dữ liệu khuôn mặt: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
    print(f"Đã tải {len(known_face_encodings)} khuôn mặt từ CSDL.")
    return known_face_encodings, known_face_student_ids

def save_face_encoding(ma_sv, face_encoding_array, ghi_chu=None):
    """
    Lưu một FaceEncoding mới hoặc cập nhật FaceEncoding nếu MaSV đã tồn tại.
    """
    conn = connect_db()
    if conn is None:
        return False

    try:
        cursor = conn.cursor(buffered=True)
        face_encoding_blob = pickle.dumps(face_encoding_array)

        # Kiểm tra xem MaSV đã tồn tại chưa
        check_query = "SELECT COUNT(*) FROM dulieukhuonmat WHERE MaSV = %s"
        cursor.execute(check_query, (ma_sv,))
        if cursor.fetchone()[0] > 0:
            # Nếu đã tồn tại, cập nhật
            update_query = """
                UPDATE dulieukhuonmat
                SET FaceEncoding = %s, ThoiGianTao = NOW(), GhiChu = %s
                WHERE MaSV = %s
            """
            cursor.execute(update_query, (face_encoding_blob, ghi_chu, ma_sv))
            print(f"Đã cập nhật FaceEncoding cho MaSV {ma_sv} thành công.")
        else:
            # Nếu chưa tồn tại, thêm mới
            insert_query = """
                INSERT INTO dulieukhuonmat (MaSV, FaceEncoding, ThoiGianTao, GhiChu)
                VALUES (%s, %s, NOW(), %s)
            """
            cursor.execute(insert_query, (ma_sv, face_encoding_blob, ghi_chu))
            print(f"Đã lưu FaceEncoding cho MaSV {ma_sv} thành công.")
        
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"Lỗi khi lưu/cập nhật FaceEncoding cho MaSV {ma_sv}: {err}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_student_info_by_ma_sv(ma_sv):
    """
    Lấy thông tin chi tiết của sinh viên để hiển thị trên bảng điểm danh
    khi sinh viên được nhận dạng (ví dụ: Tên, Năm Sinh, Giới tính).
    """
    conn = connect_db()
    if conn is None:
        return None

    student_info = None
    try:
        cursor = conn.cursor(buffered=True)
        query = """
            SELECT HoTenSV, NamSinh, GioiTinh
            FROM sinhvien
            WHERE MaSV = %s
        """
        cursor.execute(query, (ma_sv,))
        result = cursor.fetchone()
        if result:
            student_info = {
                "TenSV": result[0],
                "NamSinh": result[1],
                "GioiTinh": result[2]
            }
    except mysql.connector.Error as err:
        print(f"Lỗi khi lấy thông tin sinh viên cho MaSV {ma_sv}: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return student_info


def record_attendance(ma_sv, ma_buoi_hoc, so_lan, ma_trang_thai="CM"):
    """
    Ghi nhận điểm danh cho sinh viên.
    
    Args:
        ma_sv: Mã sinh viên
        ma_buoi_hoc: Mã buổi học
        so_lan: Lần điểm danh (1=đầu buổi, 2=cuối buổi)
        ma_trang_thai: Mã trạng thái (mặc định "CM" = Có mặt)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    conn = connect_db()
    if not conn:
        return (False, "Lỗi kết nối CSDL.")
    
    cursor = conn.cursor(buffered=True)
    try:
        # ✅ BƯỚC 1: Kiểm tra xem sinh viên đã điểm danh LẦN NÀY chưa
        cursor.execute("""
            SELECT COUNT(*) 
            FROM diemdanhsv 
            WHERE MaSV = %s 
              AND MaBuoiHoc = %s 
              AND SoLanDiemDanh = %s
        """, (ma_sv, ma_buoi_hoc, so_lan))
        
        da_diem_danh_lan_nay = cursor.fetchone()[0] > 0
        
        if da_diem_danh_lan_nay:
            print(f"⚠️ Sinh viên {ma_sv} đã điểm danh lần {so_lan} rồi. Bỏ qua.")
            return (False, f"Sinh viên {ma_sv} đã điểm danh lần {so_lan} rồi.")
        
        # ✅ BƯỚC 2: Lấy cấu hình số lần điểm danh cho buổi học này
        cursor.execute("""
            SELECT cd.SoLanDiemDanh
            FROM cauhinh_diemdanh cd
            JOIN buoihoc bh ON cd.MaLoaiBuoiDiemDanh = bh.MaLoaiBuoiDiemDanh
            WHERE bh.MaBuoiHoc = %s
        """, (ma_buoi_hoc,))  # ✅ Sửa lỗi dấu phẩy
        
        result = cursor.fetchone()
        if not result:
            return (False, "Không tìm thấy cấu hình điểm danh cho buổi học này.")
        
        so_lan_yeu_cau = result[0]
        
        # ✅ BƯỚC 3: Kiểm tra xem số lần yêu cầu có hợp lệ không
        if so_lan > so_lan_yeu_cau:
            return (False, f"Buổi học này chỉ yêu cầu điểm danh {so_lan_yeu_cau} lần. Không thể điểm danh lần {so_lan}.")
        
        # ✅ BƯỚC 4: Thực hiện INSERT
        cursor.execute("""
            INSERT INTO diemdanhsv 
            (MaBuoiHoc, MaSV, SoLanDiemDanh, MaTrangThai, ThoiGianGhiNhan) 
            VALUES (%s, %s, %s, %s, NOW())
        """, (ma_buoi_hoc, ma_sv, so_lan, ma_trang_thai))  # ✅ Sửa lỗi dấu phẩy
        
        conn.commit()
        print(f"✅ Điểm danh thành công: MSSV={ma_sv}, Buổi={ma_buoi_hoc}, Lần={so_lan}")
        
        return (True, f"Điểm danh thành công cho sinh viên {ma_sv}, lần {so_lan}.")

    except mysql.connector.IntegrityError as e:
        print(f"Lỗi IntegrityError: {e}")
        conn.rollback()
        return (False, f"Sinh viên đã điểm danh lần {so_lan} rồi (duplicate key).")
    
    except mysql.connector.Error as e:
        print(f"Lỗi MySQL khi ghi nhận điểm danh: {e}")
        conn.rollback()
        return (False, f"Lỗi hệ thống: {str(e)}")
    
    except Exception as e:
        print(f"Lỗi không xác định: {e}")
        conn.rollback()
        return (False, f"Lỗi không xác định: {str(e)}")
    
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_ma_lop_hoc_phan(class_name_str, subject_name):
    """
    Lấy MaLopHocPhan dựa trên chuỗi lớp (ví dụ: DH21TINTT01) và tên học phần.
    Hữu ích khi bạn cần MaLopHocPhan để ghi nhận điểm danh.
    """
    conn = connect_db()
    if conn is None:
        return None

    ma_lop_hoc_phan = None
    try:
        cursor = conn.cursor(buffered=True)
        # Phân tích class_name_str để lấy các thành phần
        ma_bac = class_name_str[0:2]
        ma_nien_khoa = class_name_str[2:4]
        # Giả định MaNganh có thể có độ dài thay đổi, lấy phần còn lại trước 2 ký tự cuối
        ma_nganh = class_name_str[4:-2] 
        stt_lop = class_name_str[-2:]

        query = """
            SELECT lhp.MaLopHocPhan
            FROM lophocphan lhp
            JOIN hocphan hp ON lhp.MaHocPhan = hp.MaHocPhan
            WHERE lhp.MaBac = %s AND lhp.MaNienKhoa = %s AND lhp.MaNganh = %s AND lhp.STTLop = %s
            AND hp.TenHocPhan = %s
        """
        cursor.execute(query, (ma_bac, ma_nien_khoa, ma_nganh, stt_lop, subject_name))
        result = cursor.fetchone()
        if result:
            ma_lop_hoc_phan = result[0]
    except mysql.connector.Error as err:
        print(f"Lỗi khi lấy MaLopHocPhan: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return ma_lop_hoc_phan

def get_ma_loai_diem_danh(ten_loai_diem_danh):
    """
    Lấy MaLoaiBuoiDiemDanh từ TenLoaiBuoiDiemDanh.
    """
    conn = connect_db()
    if conn is None:
        return None
    
    ma_loai = None
    try:
        cursor = conn.cursor(buffered=True)
        query = "SELECT MaLoaiBuoiDiemDanh FROM loaibuoidiemdanh WHERE TenLoaiBuoiDiemDanh = %s"
        cursor.execute(query, (ten_loai_diem_danh,))
        result = cursor.fetchone()
        if result:
            ma_loai = result[0]
    except mysql.connector.Error as err:
        print(f"Lỗi khi lấy MaLoaiBuoiDiemDanh: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return ma_loai



def update_student_face_data(ma_sv, avg_emb, image_blob, thoi_gian_cap_nhat):
    """
    Saves or updates a student's face data (embedding and image) in the database.
    """
    conn = connect_db()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor(buffered=True)
        
        # CHUYỂN ĐỔI numpy array THÀNH chuỗi bytes bằng pickle
        embedding_blob = pickle.dumps(avg_emb)
        print(f"Đã chuyển đổi embedding thành blob. Kích thước: {len(embedding_blob)} bytes")

        # Check if the student ID already has a face record
        check_query = "SELECT COUNT(*) FROM dulieukhuonmat WHERE MaSV = %s"
        cursor.execute(check_query, (ma_sv,))
        record_exists = cursor.fetchone()[0] > 0
        print(f"Bản ghi cho MaSV {ma_sv} đã tồn tại: {record_exists}")

        if record_exists:
            # If a record exists, update it
            update_query = """
                UPDATE dulieukhuonmat
                SET FaceEncoding = %s, AnhDaiDien = %s, ThoiGianTao = %s
                WHERE MaSV = %s
            """
            cursor.execute(update_query, (embedding_blob, image_blob, thoi_gian_cap_nhat, ma_sv))
            print(f"Đã cập nhật dữ liệu khuôn mặt cho MaSV {ma_sv} thành công.")
        else:
            # If no record exists, insert a new one
            insert_query = """
                INSERT INTO dulieukhuonmat (MaSV, FaceEncoding, AnhDaiDien, ThoiGianTao)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (ma_sv, embedding_blob, image_blob, thoi_gian_cap_nhat))
            print(f"Đã thêm dữ liệu khuôn mặt mới cho MaSV {ma_sv} thành công.")
        
        conn.commit()
        print("Đã commit thay đổi vào CSDL.")
        return True
    
    except mysql.connector.Error as err:
        print(f"Lỗi MySQL khi lưu dữ liệu khuôn mặt cho MaSV {ma_sv}: {err}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"Lỗi chung khi lưu dữ liệu khuôn mặt cho MaSV {ma_sv}: {e}")
        conn.rollback()
        return False
        
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            
def get_student_face_data(ma_sv):
    conn = connect_db()
    cursor = conn.cursor(buffered=True)
    cursor.execute("""
        SELECT AnhDaiDien, FaceEncoding, ThoiGianTao
        FROM dulieukhuonmat
        WHERE MaSV=%s
    """, (ma_sv,))
    conn.commit()
    cursor.close()
    conn.close()
    
def get_time_of_buoihoc(mabuoihoc):
    conn = connect_db()
    if conn is None:
        return None
    cursor = conn.cursor(buffered=True)
    cursor.execute("""
        SELECT 
        MIN(t.ThoiGianDB) AS TGBD,
        MAX(t.ThoiGianKT) AS TGKT,
        NgayHoc,
        CONCAT(min(ctbh.MaTiet), '-', max(ctbh.MaTiet)) as Tiet
        FROM buoihoc bh
        JOIN chitietbuoihoc ct ON bh.MaBuoiHoc = ct.MaBuoiHoc
        JOIN tiet t ON ct.MaTiet = t.MaTiet
        JOIN chitietbuoihoc ctbh ON ct.MaTiet = ctbh.MaTiet
        WHERE bh.MaBuoiHoc = %s
        GROUP BY bh.MaBuoiHoc;
    """, (mabuoihoc,))
    result = cursor.fetchone()
    conn.close()
    return result


def get_ma_buoi_hoc(class_name, subject_name, date_str, session_name):
    """
    Lấy MaBuoiHoc từ CSDL.
    """
    conn = connect_db()
    if conn is None:
        return None

    # --- Bước 1: Phân tích chuỗi tên lớp (class_name) ---
    # Ví dụ: "DH21TINTT01"
    # try:
    #     ma_bac = class_name[0:2]          # -> "DH"
    #     # MaNienKhoa trong CSDL là kiểu INT [cite: 182]
    #     ma_nien_khoa = int(class_name[2:4]) # -> 21 
    #     ma_nganh = class_name[4:-2]       # -> "TINTT"
    #     stt_lop = class_name[-2:]         # -> "01"
    # except (IndexError, ValueError) as e:
    #     # Xử lý nếu chuỗi class_name không đúng định dạng
    #     print(f"Lỗi nghiêm trọng: Định dạng tên lớp '{class_name}' không hợp lệ. Không thể phân tích. Lỗi: {e}")
    #     return None
        
    # --- Bước 2: Chuyển đổi định dạng ngày ---
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        ngay_sql = date_obj.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        print(f"Lỗi: Định dạng ngày không hợp lệ: {date_str}")
        return None

    ma_buoi_hoc = None
    try:
        cursor = conn.cursor(buffered=True)
        # --- Bước 3: Truy vấn với các thành phần đã phân tích ---
        query = """
            SELECT MaBuoiHoc
            FROM view_lichdiemdanh_lop
            WHERE TenLop = %s
            AND TenHocPhan = %s
            AND NgayHoc = %s
            AND TietHoc = %s
            LIMIT 1;
        """
        # Các tham số truyền vào phải đúng thứ tự
        params = (class_name, subject_name, ngay_sql, session_name)
        cursor.execute(query, params)
        result = cursor.fetchone()

        if result:
            ma_buoi_hoc = result[0]

    except mysql.connector.Error as err:
        print(f"Lỗi khi truy vấn MaBuoiHoc: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            
    return ma_buoi_hoc

def get_total_students_by_class(class_name):
    conn = connect_db()
    if conn is None:
        return None

    # --- Bước 1: Phân tích chuỗi tên lớp (class_name) ---
    # Ví dụ: "DH21TINTT01"
    try:
        ma_bac = class_name[0:2]          # -> "DH"
        # MaNienKhoa trong CSDL là kiểu INT [cite: 182]
        ma_nien_khoa = int(class_name[2:4]) # -> 21 
        ma_nganh = class_name[4:-2]       # -> "TINTT"
        stt_lop = class_name[-2:]         # -> "01"
    except (IndexError, ValueError) as e:
        # Xử lý nếu chuỗi class_name không đúng định dạng
        print(f"Lỗi nghiêm trọng: Định dạng tên lớp '{class_name}' không hợp lệ. Không thể phân tích. Lỗi: {e}")
        return None
    
    tong_sv = None
    try:
        cursor = conn.cursor(buffered=True)
        query = """
            SELECT count(*) as TongSV
            FROM sinhvien
            WHERE MaBac = %s
                    AND MaNienKhoa = %s
                    AND MaNganh = %s
                    AND STTLop = %s
        """
        # Các tham số truyền vào phải đúng thứ tự
        params = (ma_bac, ma_nien_khoa, ma_nganh, stt_lop)
        cursor.execute(query, params)
        result = cursor.fetchone()

        if result:
            tong_sv = result[0]

    except mysql.connector.Error as err:
        print(f"Lỗi khi truy vấn MaBuoiHoc: {err}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return tong_sv

def get_attendace_success(MaSV, MaBuoiHoc):
    """
    Lấy thông tin điểm danh thành công của sinh viên.
    
    Args:
        MaSV: Mã sinh viên
        MaBuoiHoc: Mã buổi học
    
    Returns:
        tuple: (HoTenSV, ThoiGianGhiNhan, AnhDaiDien) hoặc None
    """
    conn = connect_db()
    if conn is None:
        return None

    attendance_status = None
    try:
        cursor = conn.cursor(buffered=True) 
        query = """
            SELECT 
                sv.HoTenSV,
                ddsv.ThoiGianGhiNhan,
                dlkm.AnhDaiDien
            FROM 
                sinhvien sv 
            JOIN diemdanhsv ddsv ON sv.MaSV = ddsv.MaSV
            JOIN dulieukhuonmat dlkm ON dlkm.MaSV = sv.MaSV
            WHERE
                sv.MaSV = %s
                AND ddsv.MaBuoiHoc = %s
            ORDER BY ddsv.ThoiGianGhiNhan DESC
            LIMIT 1
        """
        cursor.execute(query, (MaSV, MaBuoiHoc))
        result = cursor.fetchone()

        if result:
            attendance_status = (result[0], result[1], result[2])

    except mysql.connector.Error as err:
        print(f"Lỗi khi truy vấn trạng thái điểm danh: {err}")
        return None
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn and conn.is_connected():
                conn.close()
        except Exception:
            pass

    return attendance_status

def get_lecturer_classes_for_filter(username):
    """
    Lấy danh sách lớp mà giảng viên được phân công để làm bộ lọc
    Trả về: list tên lớp (format: DH21TINTT01)
    """
    conn = connect_db()
    if conn is None:
        return []
    
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("""
            SELECT DISTINCT TenLop
            FROM view_lichphancong
            WHERE TenDangNhap = %s
            ORDER BY TenLop
        """, (username,))
        
        results = cursor.fetchall()
        return [row[0] for row in results]
        
    except mysql.connector.Error as err:
        print(f"Lỗi khi lấy danh sách lớp: {err}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_attendance_chart_by_class_subject(username, class_name=None, subject_name=None, days_back=30):
    """
    Lấy dữ liệu biểu đồ cột điểm danh theo lớp và môn học cụ thể
    Trả về: dict {ngày: số_sinh_viên_đi_học}
    """
    conn = connect_db()
    if conn is None:
        return {}
    
    try:
        cursor = conn.cursor(buffered=True)
        
        # Điều kiện cơ bản
        base_conditions = ["tk.TenDangNhap = %s"]
        params = [username]
        
        # Thêm điều kiện lớp nếu có
        if class_name:
            # Phân tích tên lớp
            try:
                ma_bac = class_name[0:2]
                ma_nien_khoa = int(class_name[2:4])
                ma_nganh = class_name[4:-2]
                stt_lop = class_name[-2:]
                
                base_conditions.extend([
                    "lhp.MaBac = %s", "lhp.MaNienKhoa = %s",
                    "lhp.MaNganh = %s", "lhp.STTLop = %s"
                ])
                params.extend([ma_bac, ma_nien_khoa, ma_nganh, stt_lop])
            except (IndexError, ValueError):
                print(f"Lỗi phân tích tên lớp: {class_name}")
                return {}
        
        # Thêm điều kiện môn học nếu có
        if subject_name:
            base_conditions.append("hp.TenHocPhan = %s")
            params.append(subject_name)
        
        # Thêm điều kiện thời gian
        base_conditions.append("bh.NgayHoc >= DATE_SUB(CURDATE(), INTERVAL %s DAY)")
        params.append(days_back)
        
        query = f"""
            SELECT 
                DATE_FORMAT(bh.NgayHoc, '%d/%m') as NgayDinhDang,
                COUNT(DISTINCT CASE 
                    WHEN tt.TenTrangThai IN ('Có mặt', 'Đi muộn') 
                    THEN dd.MaSV END) as SoSVDiHoc
            FROM taikhoan tk
            JOIN giangvien gv ON tk.MaGV = gv.MaGV
            JOIN lophocphan lhp ON lhp.MaGV = gv.MaGV
            JOIN hocphan hp ON lhp.MaHocPhan = hp.MaHocPhan
            JOIN buoihoc bh ON bh.MaLopHocPhan = lhp.MaLopHocPhan
            LEFT JOIN diemdanhsv dd ON dd.MaBuoiHoc = bh.MaBuoiHoc
            LEFT JOIN trangthaidiemdanh tt ON dd.MaTrangThai = tt.MaTrangThai
            WHERE {' AND '.join(base_conditions)}
            GROUP BY bh.NgayHoc
            ORDER BY bh.NgayHoc ASC
            LIMIT 10
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        chart_data = {}
        for row in results:
            ngay = row[0] or "N/A"
            so_sv = row[1] or 0
            chart_data[ngay] = so_sv
            
        return chart_data
        
    except mysql.connector.Error as err:
        print(f"Lỗi khi lấy dữ liệu biểu đồ: {err}")
        return {}
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_average_attendance_by_class_subject(username, class_name=None, subject_name=None):
    """
    Tính tỷ lệ trung bình sinh viên đi học theo lớp và môn học
    Trả về: (trung_binh_sv_di_hoc, tong_sv_lop)
    """
    conn = connect_db()
    if conn is None:
        return (0, 0)
    
    try:
        cursor = conn.cursor(buffered=True)
        
        base_conditions = ["tk.TenDangNhap = %s", "bh.NgayHoc <= CURDATE()"]
        params = [username]
        
        if class_name:
            try:
                ma_bac = class_name[0:2]
                ma_nien_khoa = int(class_name[2:4])
                ma_nganh = class_name[4:-2]
                stt_lop = class_name[-2:]
                
                base_conditions.extend([
                    "lhp.MaBac = %s", "lhp.MaNienKhoa = %s",
                    "lhp.MaNganh = %s", "lhp.STTLop = %s"
                ])
                params.extend([ma_bac, ma_nien_khoa, ma_nganh, stt_lop])
            except (IndexError, ValueError):
                return (0, 0)
        
        if subject_name:
            base_conditions.append("hp.TenHocPhan = %s")
            params.append(subject_name)
        
        query = f"""
            SELECT 
                AVG(daily_attendance.so_sv_di_hoc) as TrungBinhDiHoc,
                AVG(daily_attendance.tong_sv_lop) as TrungBinhTongSV
            FROM (
                SELECT 
                    bh.NgayHoc,
                    COUNT(DISTINCT CASE 
                        WHEN tt.TenTrangThai IN ('Có mặt', 'Đi muộn') 
                        THEN dd.MaSV END) as so_sv_di_hoc,
                    (SELECT COUNT(*) FROM sinhvien sv2 
                     WHERE sv2.MaBac = lhp.MaBac AND sv2.MaNienKhoa = lhp.MaNienKhoa
                       AND sv2.MaNganh = lhp.MaNganh AND sv2.STTLop = lhp.STTLop
                    ) as tong_sv_lop
                FROM taikhoan tk
                JOIN giangvien gv ON tk.MaGV = gv.MaGV
                JOIN lophocphan lhp ON lhp.MaGV = gv.MaGV
                JOIN hocphan hp ON lhp.MaHocPhan = hp.MaHocPhan
                JOIN buoihoc bh ON bh.MaLopHocPhan = lhp.MaLopHocPhan
                LEFT JOIN diemdanhsv dd ON dd.MaBuoiHoc = bh.MaBuoiHoc
                LEFT JOIN trangthaidiemdanh tt ON dd.MaTrangThai = tt.MaTrangThai
                WHERE {' AND '.join(base_conditions)}
                GROUP BY lhp.MaLopHocPhan, bh.NgayHoc, bh.MaBuoiHoc
            ) as daily_attendance
        """
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if result and result[0] is not None:
            return int(result[0]), int(result[1] or 0)
        
        return (0, 0)
        
    except mysql.connector.Error as err:
        print(f"Lỗi khi tính trung bình điểm danh: {err}")
        return (0, 0)
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_completion_statistics_by_class_subject(username, class_name=None, subject_name=None):
    """
    Lấy thống kê buổi hoàn thành theo lớp và môn học cụ thể
    Trả về: (so_buoi_da_day, tong_so_buoi)
    """
    conn = connect_db()
    if conn is None:
        return (0, 0)
    
    try:
        cursor = conn.cursor(buffered=True)
        
        base_conditions = ["tk.TenDangNhap = %s"]
        params = [username]
        
        if class_name:
            try:
                ma_bac = class_name[0:2]
                ma_nien_khoa = int(class_name[2:4])
                ma_nganh = class_name[4:-2]
                stt_lop = class_name[-2:]
                
                base_conditions.extend([
                    "lhp.MaBac = %s", "lhp.MaNienKhoa = %s",
                    "lhp.MaNganh = %s", "lhp.STTLop = %s"
                ])
                params.extend([ma_bac, ma_nien_khoa, ma_nganh, stt_lop])
            except (IndexError, ValueError):
                return (0, 0)
        
        if subject_name:
            base_conditions.append("hp.TenHocPhan = %s")
            params.append(subject_name)
        
        query = f"""
            SELECT 
                COUNT(CASE WHEN bh.NgayHoc <= CURDATE() THEN 1 END) as SoBuoiDaDay,
                COUNT(bh.MaBuoiHoc) as TongSoBuoi
            FROM taikhoan tk
            JOIN giangvien gv ON tk.MaGV = gv.MaGV
            JOIN lophocphan lhp ON lhp.MaGV = gv.MaGV
            JOIN hocphan hp ON lhp.MaHocPhan = hp.MaHocPhan
            LEFT JOIN buoihoc bh ON bh.MaLopHocPhan = lhp.MaLopHocPhan
            WHERE {' AND '.join(base_conditions)}
        """
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if result:
            return result[0] or 0, result[1] or 0
        return (0, 0)
        
    except mysql.connector.Error as err:
        print(f"Lỗi khi lấy thống kê hoàn thành: {err}")
        return (0, 0)
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_all_schedule_dates_by_class_subject(username, class_name=None, subject_name=None):
    """
    Lấy TẤT CẢ các ngày có lịch học của môn học (không giới hạn tháng)
    Trả về: dict {tháng: [danh_sách_ngày]}
    """
    conn = connect_db()
    if conn is None:
        return {}
    
    try:
        cursor = conn.cursor(buffered=True)
        
        base_conditions = ["tk.TenDangNhap = %s"]
        params = [username]
        
        if class_name:
            # Thêm điều kiện lớp
            ma_bac = class_name[0:2]
            ma_nien_khoa = int(class_name[2:4])
            ma_nganh = class_name[4:-2]
            stt_lop = class_name[-2:]
            
            base_conditions.extend([
                "lhp.MaBac = %s", "lhp.MaNienKhoa = %s",
                "lhp.MaNganh = %s", "lhp.STTLop = %s"
            ])
            params.extend([ma_bac, ma_nien_khoa, ma_nganh, stt_lop])
        
        if subject_name:
            base_conditions.append("hp.TenHocPhan = %s")
            params.append(subject_name)
        
        query = f"""
            SELECT 
                YEAR(bh.NgayHoc) as Nam,
                MONTH(bh.NgayHoc) as Thang, 
                DAY(bh.NgayHoc) as Ngay,
                bh.NgayHoc
            FROM taikhoan tk
            JOIN giangvien gv ON tk.MaGV = gv.MaGV
            JOIN lophocphan lhp ON lhp.MaGV = gv.MaGV
            JOIN hocphan hp ON lhp.MaHocPhan = hp.MaHocPhan
            JOIN buoihoc bh ON bh.MaLopHocPhan = lhp.MaLopHocPhan
            WHERE {' AND '.join(base_conditions)}
            ORDER BY bh.NgayHoc
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Trả về tất cả ngày học
        all_dates = []
        for row in results:
            nam, thang, ngay, ngay_hoc = row
            all_dates.append({
                'nam': nam, 
                'thang': thang, 
                'ngay': ngay,
                'ngay_hoc': ngay_hoc
            })
            
        return all_dates
        
    except mysql.connector.Error as err:
        print(f"Lỗi khi lấy tất cả lịch học: {err}")
        return []
def get_lecturer_statistics_overview(username):
    """
    Lấy thống kê tổng quan cho giảng viên từ VIEW có sẵn
    """
    conn = connect_db()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT * FROM view_thongke_tongquan_giangvien WHERE TenDangNhap = %s", (username,))
        result = cursor.fetchone()
        
        if result:
            return {
                'tong_lop': result[1] or 0,          # SoLopPhanCong
                'tong_hoc_phan': result[2] or 0,     # SoHocPhan  
                'tien_do_hoan_thanh': result[3] or 0, # TienDoHoanThanh
                'thoi_gian_con_lai': max(0, result[4] or 0), # ThoiGianConLai
                'thoi_gian_ket_thuc':  result[5],  # ThoiGianKetThuc
                'so_buoi_da_day': result[6] or 0,    # SoBuoiDaDay
                'tong_so_buoi': result[7] or 0       # TongSoBuoi
            }
        return {
            'tong_lop': 0, 'tong_hoc_phan': 0, 'tien_do_hoan_thanh': 0,
            'thoi_gian_con_lai': 0, 'so_buoi_da_day': 0, 'tong_so_buoi': 0
        }
        
    except mysql.connector.Error as err:
        print(f"Lỗi khi lấy thống kê tổng quan: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            
def get_admin_statistics_overview():
    """
    Lấy thống kê tổng quan cho Admin từ VIEW có sẵn
    """
    conn = connect_db()
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT * FROM view_thongke_tongquan_admin")
        result = cursor.fetchone()
        
        if result:
            return {
                'tong_so_lop': result[0] or 0,
                'tong_so_sinh_vien': result[1] or 0,
                'tien_do_hoan_thanh': result[2] or 0
            }
        return {
            'tong_so_lop': 0, 'tong_so_sinh_vien': 0, 'tien_do_hoan_thanh': 0
        }
    except mysql.connector.Error as err:
        print(f"Lỗi khi lấy thống kê tổng quan: {err}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            


def report_attendance_details_of_subject(MaLopHocPhan):
    conn = connect_db()
    if conn is None:
        return {"student_data": [], "static_data": {}}
    
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("CALL sp_ChiTietDiemDanhSinhVien(%s);", (MaLopHocPhan,))
        rows = cursor.fetchall()
        students = []
        for r in rows:
            students.append({
                'ma_sv': r[1],            # MaSV
                'ho_dem': r[2],          # HoDem
                'ten': r[3],             # Ten
                #'ngay_sinh': r[4],      
                'ket_qua': r[5],         # KetQua
                'dynamic_col': r[6] or "{}",  # JSON string
            })
        return {"student_data": students, "static_data": {}}
    except mysql.connector.Error as err:
        print(f"Lỗi khi lấy chi tiết điểm danh: {err}")
        return {"student_data": [], "static_data": {}}
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass


def report_attendance_details_of_subject_title(user, subject_name):
    conn = connect_db()
    if conn is None:
        return {}

    try:
        cursor = conn.cursor(dictionary=True)
        sql = """
            SELECT TenHocPhan,
                   TenGiangVien,
                   TenLop,
                   MaHocKy,
                   CONCAT(NamBD,'-',NamKT) as NamHoc
            FROM view_tieudebaocao_hocphan_giangvien
            WHERE TenDangNhap = %s
              AND TenHocPhan = %s
            LIMIT 1
        """
        cursor.execute(sql, (user, subject_name))
        row = cursor.fetchone()
        if not row:
            return {}

        return {
            'ten_hoc_phan': row.get('TenHocPhan'),
            'ten_giang_vien': row.get('TenGiangVien'),
            'hoc_ky': row.get('MaHocKy'),
            'nam_hoc': row.get('NamHoc'),
            'ten_lop': row.get('TenLop'),
        }

    except mysql.connector.Error as err:
        print(f"Lỗi khi lấy tiêu đề điểm danh: {err}")
        return {}
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass

def get_manager_table_student_total(malop):
    """
    Lấy danh sách tất cả các sinh viên trong data sinh viên trong hệ thống để hiển thị trên bảng quản lý.
    """
    conn = connect_db()
    cursor = conn.cursor(buffered=True)
    if conn is None:
        return []
    students = [] 
    if not malop:
        query = "SELECT * FROM view_total_sinhvien"
        cursor.execute(query)
        result = cursor.fetchall()
        for row in result:  
            students.append({
                "MaSV": row[0],
                "HoDem": row[1],
                "Ten": row[2],
                "GioiTinh": row[3],
                "NamSinh": row[4],
                "MaLop": row[5],
                "DiaChi": row[6],
                "GhiChu": row[7]
            })
    elif malop:
        query = "SELECT * FROM view_total_sinhvien WHERE MaLop = %s"
        cursor.execute(query, (malop,))
        result = cursor.fetchall()
        for row in result:  
            students.append({
                "MaSV": row[0],
                "HoDem": row[1],
                "Ten": row[2],
                "GioiTinh": row[3],
                "NamSinh": row[4],
                "MaLop": row[5],
                "DiaChi": row[6],
                "GhiChu": row[7]
            })
    else:
        print(f"Lỗi khi lấy danh sách sinh viên")

    if conn and conn.is_connected():
        cursor.close()
        conn.close()
    return students 

# -----------------------------------------------------
# CÁC HÀM MỚI CHO QUẢN LÝ HỌC VỤ (ADMIN)
# -----------------------------------------------------
from mysql.connector import Error

def _execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """Hàm helper chung để thực thi query (phiên bản không dùng self)."""
    conn = connect_db()
    if not conn:
        return None if (commit or fetch_one or fetch_all) else None
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        if commit:
            conn.commit()
            # Nếu INSERT cần lastrowid, caller có thể gọi riêng (xem ví dụ add_lophocphan)
            return True
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
        return cursor
    except Error as e:
        print(f"Lỗi khi thực thi query: {e}")
        if commit and conn.is_connected():
            conn.rollback()
        return None
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            if conn and conn.is_connected():
                conn.close()
        except:
            pass

# ----- QUẢN LÝ HỌC PHẦN -----
def get_all_hocphan():
    query = "SELECT MaHocPhan, TenHocPhan, SoTinChi, TongSoTiet, MaLoaiHP FROM hocphan ORDER BY TenHocPhan"
    return _execute_query(query, fetch_all=True)

def get_all_hocphan_simple():
    query = "SELECT MaHocPhan, TenHocPhan FROM hocphan ORDER BY TenHocPhan"
    return _execute_query(query, fetch_all=True)

def add_hocphan(mahp, tenhp, sotc, tongtiet, maloaihp):
    query = "INSERT INTO hocphan (MaHocPhan, TenHocPhan, SoTinChi, TongSoTiet, MaLoaiHP) VALUES (%s, %s, %s, %s, %s)"
    params = (mahp, tenhp, sotc, tongtiet, maloaihp)
    return _execute_query(query, params=params, commit=True)

def update_hocphan(mahp, tenhp, sotc, tongtiet, maloaihp):
    query = """
        UPDATE hocphan
        SET TenHocPhan = %s, SoTinChi = %s, TongSoTiet = %s, MaLoaiHP = %s
        WHERE MaHocPhan = %s
    """
    params = (tenhp, sotc, tongtiet, maloaihp, mahp)
    return _execute_query(query, params=params, commit=True)

def delete_hocphan(mahp):
    query = "DELETE FROM hocphan WHERE MaHocPhan = %s"
    params = (mahp,)
    return _execute_query(query, params=params, commit=True)

# ----- QUẢN LÝ LỚP HỌC PHẦN -----
def get_all_lophocphan():
    query = """
        SELECT lhp.MaLopHocPhan, lhp.MaHocPhan, hp.TenHocPhan,
                lhp.MaBac, lhp.MaNienKhoa, lhp.MaNganh, lhp.STTLop,
                lhp.SoBuoi, lhp.TietMoiBuoi, lhp.MaGV, gv.TenGiangVien,
                lhp.MaHocKy, lhp.NamDB, lhp.NamKT
        FROM lophocphan lhp
        JOIN hocphan hp ON lhp.MaHocPhan = hp.MaHocPhan
        JOIN giangvien gv ON lhp.MaGV = gv.MaGV
        ORDER BY lhp.MaLopHocPhan
    """
    return _execute_query(query, fetch_all=True)

def get_lophocphan_by_id(malhp):
    query = """
        SELECT MaLopHocPhan, MaHocPhan, MaBac, MaNienKhoa, MaNganh, STTLop,
                SoBuoi, TietMoiBuoi, MaGV, MaHocKy, NamDB, NamKT
        FROM lophocphan WHERE MaLopHocPhan = %s
    """
    return _execute_query(query, params=(malhp,), fetch_one=True)

def get_all_lophocphan_simple():
    query = "SELECT MaLopHocPhan, MaHocPhan FROM lophocphan ORDER BY MaLopHocPhan"
    results = _execute_query(query, fetch_all=True)
    return {row[0]: f"{row[0]} - ({row[1]})" for row in results} if results else {}

def add_lophocphan(mahp, mabac, mank, manganh, sttlop, sobuoi, tietmoibuoi, magv, mahky, nambd, namkt):
    query = """
        INSERT INTO lophocphan (MaHocPhan, MaBac, MaNienKhoa, MaNganh, STTLop,
                                SoBuoi, TietMoiBuoi, MaGV, MaHocKy, NamDB, NamKT)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (mahp, mabac, mank, manganh, sttlop, sobuoi, tietmoibuoi, magv, mahky, nambd, namkt)
    # Trường hợp cần lastrowid: mở connection riêng để lấy cursor.lastrowid
    conn = connect_db()
    if not conn:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"Lỗi khi thêm lớp học phần: {e}")
        if conn.is_connected():
            conn.rollback()
        return None
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            if conn.is_connected():
                conn.close()
        except:
            pass

def update_lophocphan(malhp, mahp, mabac, mank, manganh, sttlop, sobuoi, tietmoibuoi, magv, mahky, nambd, namkt):
    query = """
        UPDATE lophocphan SET
            MaHocPhan = %s, MaBac = %s, MaNienKhoa = %s, MaNganh = %s, STTLop = %s,
            SoBuoi = %s, TietMoiBuoi = %s, MaGV = %s, MaHocKy = %s, NamDB = %s, NamKT = %s
        WHERE MaLopHocPhan = %s
    """
    params = (mahp, mabac, mank, manganh, sttlop, sobuoi, tietmoibuoi, magv, mahky, nambd, namkt, malhp)
    return _execute_query(query, params=params, commit=True)

def delete_lophocphan(malhp):
    conn = connect_db()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM diemdanhsv WHERE MaBuoiHoc IN (SELECT MaBuoiHoc FROM buoihoc WHERE MaLopHocPhan = %s)", (malhp,))
        cursor.execute("DELETE FROM chitietbuoihoc WHERE MaBuoiHoc IN (SELECT MaBuoiHoc FROM buoihoc WHERE MaLopHocPhan = %s)", (malhp,))
        cursor.execute("DELETE FROM buoihoc WHERE MaLopHocPhan = %s", (malhp,))
        cursor.execute("DELETE FROM dangkyhocthem WHERE MaLopHocPhan = %s", (malhp,))
        cursor.execute("DELETE FROM lophocphan WHERE MaLopHocPhan = %s", (malhp,))
        conn.commit()
        return True
    except Error as e:
        print(f"Lỗi khi xóa lớp học phần và dữ liệu liên quan: {e}")
        if conn.is_connected():
            conn.rollback()
        return False
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            if conn.is_connected():
                conn.close()
        except:
            pass

# ----- QUẢN LÝ BUỔI HỌC & XẾP LỊCH -----
def get_buoihoc_by_lhp(malhp):
    query = """
        SELECT bh.MaBuoiHoc, bh.NgayHoc, bh.Thu, bh.MaLoaiBuoiDiemDanh,
                GROUP_CONCAT(ctbh.MaTiet ORDER BY ctbh.MaTiet SEPARATOR ',') AS TietHoc
        FROM buoihoc bh
        LEFT JOIN chitietbuoihoc ctbh ON bh.MaBuoiHoc = ctbh.MaBuoiHoc
        WHERE bh.MaLopHocPhan = %s
        GROUP BY bh.MaBuoiHoc, bh.NgayHoc, bh.Thu, bh.MaLoaiBuoiDiemDanh
        ORDER BY bh.NgayHoc
    """
    return _execute_query(query, params=(malhp,), fetch_all=True)

def add_buoihoc_with_procedure(malhp, ngayhoc, thu, maloai_dd, tiet_hoc_list):
    conn = connect_db()
    if not conn:
        return False, "Không kết nối CSDL"
    cursor = conn.cursor()
    try:
        tiet_hoc_str = ','.join(map(str, tiet_hoc_list))
        # args: p_MaLopHocPhan, p_NgayHoc, p_Thu, p_MaLoaiDD, p_TietHocList, p_Success (OUT), p_Message (OUT)
        args = [malhp, ngayhoc, thu, maloai_dd, tiet_hoc_str, 0, '']
        result_args = cursor.callproc('sp_XepLichHoc_v2', args)
        # Kết quả ở result_args (vị trí 5 và 6)
        p_success = result_args[5]
        p_message = result_args[6]
        if p_success:
            conn.commit()
            return True, p_message
        else:
            conn.rollback()
            return False, p_message
    except Error as e:
        print(f"Lỗi khi gọi Stored Procedure sp_XepLichHoc_v2: {e}")
        if conn.is_connected():
            conn.rollback()
        return False, f"Lỗi CSDL: {e}"
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            if conn.is_connected():
                conn.close()
        except:
            pass

def delete_buoihoc(mabuoi):
    conn = connect_db()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM diemdanhsv WHERE MaBuoiHoc = %s", (mabuoi,))
        cursor.execute("DELETE FROM chitietbuoihoc WHERE MaBuoiHoc = %s", (mabuoi,))
        cursor.execute("DELETE FROM buoihoc WHERE MaBuoiHoc = %s", (mabuoi,))
        conn.commit()
        return True
    except Error as e:
        print(f"Lỗi khi xóa buổi học: {e}")
        if conn.is_connected():
            conn.rollback()
        return False
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            if conn.is_connected():
                conn.close()
        except:
            pass

def get_master_schedule():
    query = "SELECT * FROM view_chitietlichhoc_v2 ORDER BY NgayHoc, TietBatDau"
    return _execute_query(query, fetch_all=True)

# ----- LẤY DỮ LIỆU COMBOBOX -----
def get_all_giangvien_simple():
    query = "SELECT MaGV, TenGiangVien FROM giangvien ORDER BY TenGiangVien"
    return _execute_query(query, fetch_all=True)

def get_all_hocky_simple():
    query = "SELECT MaHocKy, TenHocKy FROM hocky ORDER BY MaHocKy"
    return _execute_query(query, fetch_all=True)

def get_all_loaihocphan_simple():
    query = "SELECT MaLoaiHP, TenLoaiHP FROM loaihocphan ORDER BY TenLoaiHP"
    return _execute_query(query, fetch_all=True)

def get_all_bac_simple():
    query = "SELECT MaBac, TenBac FROM bac ORDER BY MaBac"
    return _execute_query(query, fetch_all=True)

def get_all_nienkhoa_simple():
    query = "SELECT MaNienKhoa, TenNienKhoa FROM nienkhoa ORDER BY MaNienKhoa"
    return _execute_query(query, fetch_all=True)

def get_all_nganh_simple():
    query = "SELECT MaNganh, TenNganh FROM nganh ORDER BY TenNganh"
    return _execute_query(query, fetch_all=True)

def get_all_lop_simple_dict():
    query = """
        SELECT MaBac, MaNienKhoa, MaNganh, STTLop, TenLop
        FROM lop ORDER BY MaBac, MaNienKhoa, MaNganh, STTLop
    """
    results = _execute_query(query, fetch_all=True)
    lop_dict = {}
    if results:
        for row in results:
            key = (row[0], row[1], row[2], row[3])
            display = f"{row[0]}{row[1]}{row[2]}{row[3]} - {row[4]}"
            lop_dict[key] = display
    return lop_dict

def get_all_loaibuoidiemdanh_simple():
    query = "SELECT MaLoaiBuoiDiemDanh, TenLoaiBuoiDiemDanh FROM loaibuoidiemdanh"
    return _execute_query(query, fetch_all=True)

def get_all_tiet_simple():
    query = "SELECT MaTiet, CONCAT(TenTiet, ' (', TIME_FORMAT(ThoiGianDB, '%H:%i'), '-', TIME_FORMAT(ThoiGianKT, '%H:%i'), ')') FROM tiet ORDER BY MaTiet"
    return _execute_query(query, fetch_all=True)

# ----- QUẢN LÝ CÀI ĐẶT LOẠI HỌC PHẦN -----
def get_loaihocphan_cauhinh():
    query = """
        SELECT lhp.MaLoaiHP, lhp.TenLoaiHP, COALESCE(lhpc.TyLeDiHocToiThieu, 0) AS TyLe
        FROM loaihocphan lhp
        LEFT JOIN loaihocphan_cauhinh lhpc ON lhp.MaLoaiHP = lhpc.MaLoaiHP
        ORDER BY lhp.MaLoaiHP
    """
    return _execute_query(query, fetch_all=True)

def update_loaihocphan_cauhinh(maloaihp, tyle):
    query_check = "SELECT 1 FROM loaihocphan_cauhinh WHERE MaLoaiHP = %s"
    exists = _execute_query(query_check, params=(maloaihp,), fetch_one=True)
    if exists:
        query = "UPDATE loaihocphan_cauhinh SET TyLeDiHocToiThieu = %s WHERE MaLoaiHP = %s"
        params = (tyle, maloaihp)
    else:
        query = "INSERT INTO loaihocphan_cauhinh (MaLoaiHP, TyLeDiHocToiThieu) VALUES (%s, %s)"
        params = (maloaihp, tyle)
    return _execute_query(query, params=params, commit=True)

def get_all_bac_simple():
    """Lấy Mã bậc và Tên bậc."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MaBac, TenBac FROM bac")
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy danh sách bậc học: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_all_nienkhoa_simple():
    """Lấy Mã niên khóa và Tên niên khóa."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MaNienKhoa, TenNienKhoa FROM nienkhoa ORDER BY MaNienKhoa")
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy danh sách niên khóa: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_all_nganh_simple():
    """Lấy Mã ngành và Tên ngành."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MaNganh, TenNganh FROM nganh")
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy danh sách ngành học: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_all_khoa_simple():
    """Lấy Mã khoa và Tên khoa."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MaKhoa, TenKhoa FROM khoa")
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy danh sách khoa: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_all_giangvien_simple():
    """Lấy Mã GV và Tên GV (không bao gồm admin)."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # Loại trừ GV có MaGV = 1 (admin)
        cursor.execute("SELECT MaGV, TenGiangVien FROM giangvien WHERE MaGV != 1 ORDER BY TenGiangVien")
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy danh sách giảng viên: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_all_lop_simple():
    """Lấy thông tin cơ bản của tất cả các lớp để tạo tên hiển thị."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # Lấy đủ thông tin để tạo khóa và tên hiển thị
        cursor.execute("SELECT MaBac, MaNienKhoa, MaNganh, STTLop, TenLop, MaGV, MaKhoa FROM lop ORDER BY MaBac, MaNienKhoa, MaNganh, STTLop")
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy danh sách lớp đơn giản: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ================================================
# HÀM XỬ LÝ LỚP HỌC (Bảng `lop`)
# ================================================

def get_lop_detail_by_key(key_tuple):
    """Lấy chi tiết một lớp dựa vào khóa chính (MaBac, MaNK, MaNganh, STTLop)."""
    if len(key_tuple) != 4: return None
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT MaBac, MaNienKhoa, MaNganh, STTLop, TenLop, MaGV, MaKhoa FROM lop WHERE MaBac = %s AND MaNienKhoa = %s AND MaNganh = %s AND STTLop = %s"
        cursor.execute(query, key_tuple)
        result = cursor.fetchone()
        return result
    except Error as e:
        print(f"Lỗi khi lấy chi tiết lớp: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def add_lop(mabac, mank, manganh, sttlop, tenlop, magv, makhoa):
    """Thêm một lớp mới vào CSDL."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO lop (MaBac, MaNienKhoa, MaNganh, STTLop, TenLop, MaGV, MaKhoa) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        # Xử lý MaGV nếu là None (chưa gán)
        magv_insert = magv if magv is not None else None 
        cursor.execute(query, (mabac, mank, manganh, sttlop, tenlop, magv_insert, makhoa))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"Lỗi khi thêm lớp: {e}")
        conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def update_lop(mabac, mank, manganh, sttlop, tenlop, magv, makhoa):
    """Cập nhật thông tin một lớp (không cập nhật khóa chính)."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = "UPDATE lop SET TenLop = %s, MaGV = %s, MaKhoa = %s WHERE MaBac = %s AND MaNienKhoa = %s AND MaNganh = %s AND STTLop = %s"
        magv_update = magv if magv is not None else None
        cursor.execute(query, (tenlop, magv_update, makhoa, mabac, mank, manganh, sttlop))
        conn.commit()
        # rowcount có thể là 0 nếu không có gì thay đổi, vẫn coi là thành công nếu không lỗi
        return True 
    except Error as e:
        print(f"Lỗi khi cập nhật lớp: {e}")
        conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def delete_lop(mabac, mank, manganh, sttlop):
    """Xóa một lớp. Sẽ thất bại nếu có ràng buộc khóa ngoại (vd: sinh viên)."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = "DELETE FROM lop WHERE MaBac = %s AND MaNienKhoa = %s AND MaNganh = %s AND STTLop = %s"
        cursor.execute(query, (mabac, mank, manganh, sttlop))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        # Bắt lỗi ràng buộc khóa ngoại cụ thể nếu cần (error code 1451)
        if e.errno == 1451:
             print(f"Không thể xóa lớp: Có dữ liệu sinh viên hoặc lớp học phần liên quan.")
        else:
             print(f"Lỗi khi xóa lớp: {e}")
        conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def search_lop_by_name_or_key(search_term):
    """Tìm kiếm lớp theo Tên lớp hoặc Mã lớp (ví dụ: DH22TIN01)."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # Thử khớp với mã lớp được tạo tự động trước
        query = """
            SELECT MaBac, MaNienKhoa, MaNganh, STTLop, TenLop, MaGV, MaKhoa 
            FROM lop 
            WHERE CONCAT(MaBac, MaNienKhoa, MaNganh, STTLop) LIKE %s 
            OR TenLop LIKE %s
            ORDER BY MaBac, MaNienKhoa, MaNganh, STTLop
        """
        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_term, search_pattern)) # Tìm chính xác mã trước, sau đó tìm gần đúng tên
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi tìm kiếm lớp: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            
def get_all_lop_details():
    """Lấy chi tiết tất cả các lớp."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT MaBac, MaNienKhoa, MaNganh, STTLop, TenLop, MaGV, MaKhoa FROM lop ORDER BY MaBac, MaNienKhoa, MaNganh, STTLop"
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy chi tiết tất cả lớp: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ================================================
# HÀM XỬ LÝ SINH VIÊN (Bảng `sinhvien` và view)
# ================================================

def add_sinhvien(mssv, mabac, mank, manganh, sttlop, hoten, ngaysinh, diachi, gioitinh, ghichu):
    """Thêm sinh viên mới."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO sinhvien (MaSV, MaBac, MaNienKhoa, MaNganh, STTLop, HoTenSV, NamSinh, DiaChi, GioiTinh, GhiChu) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (mssv, mabac, mank, manganh, sttlop, hoten, ngaysinh, diachi, gioitinh, ghichu))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"Lỗi khi thêm sinh viên: {e}")
        conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def update_sinhvien(mssv, mabac, mank, manganh, sttlop, hoten, ngaysinh, diachi, gioitinh, ghichu):
    """Cập nhật thông tin sinh viên."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = """
            UPDATE sinhvien 
            SET MaBac = %s, MaNienKhoa = %s, MaNganh = %s, STTLop = %s, 
                HoTenSV = %s, NamSinh = %s, DiaChi = %s, GioiTinh = %s, GhiChu = %s
            WHERE MaSV = %s
        """
        cursor.execute(query, (mabac, mank, manganh, sttlop, hoten, ngaysinh, diachi, gioitinh, ghichu, mssv))
        conn.commit()
        # rowcount có thể là 0 nếu không có gì thay đổi
        return True 
    except Error as e:
        print(f"Lỗi khi cập nhật sinh viên: {e}")
        conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def delete_sinhvien(mssv):
    """Xóa sinh viên và các dữ liệu liên quan (điểm danh, khuôn mặt)."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        
        # Xóa các bảng phụ thuộc trước (nếu có lỗi FK, xử lý ở đây)
        # Lưu ý: Nên dùng transaction
        conn.start_transaction()
        
        # 1. Xóa điểm danh
        cursor.execute("DELETE FROM diemdanhsv WHERE MaSV = %s", (mssv,))
        # 2. Xóa dữ liệu khuôn mặt
        cursor.execute("DELETE FROM dulieukhuonmat WHERE MaSV = %s", (mssv,))
        # 3. Xóa đăng ký học thêm (nếu có)
        cursor.execute("DELETE FROM dangkyhocthem WHERE MaSV = %s", (mssv,))
        
        # 4. Xóa sinh viên
        cursor.execute("DELETE FROM sinhvien WHERE MaSV = %s", (mssv,))
        
        rowcount = cursor.rowcount # Lấy rowcount của lệnh xóa cuối cùng
        
        conn.commit()
        return rowcount > 0
    except Error as e:
        print(f"Lỗi khi xóa sinh viên và dữ liệu liên quan: {e}")
        conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_student_detail_from_view(mssv):
    """Lấy chi tiết sinh viên từ view_total_sinhvien."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # Đảm bảo tên cột khớp với view
        query = """
            SELECT MaSV, TenLop, HoDem, Ten, NamSinh, DiaChi, GioiTinh, GhiChu 
            FROM view_total_sinhvien 
            WHERE MaSV = %s
        """
        cursor.execute(query, (mssv,))
        result = cursor.fetchone()
        return result
    except Error as e:
        print(f"Lỗi khi lấy chi tiết sinh viên từ view: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_all_students_from_view():
    """Lấy tất cả sinh viên từ view_total_sinhvien."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = """
            SELECT MaSV, TenLop, HoDem, Ten, NamSinh, DiaChi, GioiTinh, GhiChu 
            FROM view_total_sinhvien 
            ORDER BY Ten, HoDem 
        """ # Sắp xếp theo Tên, Họ đệm
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy tất cả sinh viên từ view: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_students_by_class_from_view(ten_lop):
    """Lọc sinh viên theo tên lớp từ view_total_sinhvien."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = """
            SELECT MaSV, TenLop, HoDem, Ten, NamSinh, DiaChi, GioiTinh, GhiChu 
            FROM view_total_sinhvien 
            WHERE TenLop = %s
            ORDER BY Ten, HoDem
        """
        cursor.execute(query, (ten_lop,))
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lọc sinh viên theo lớp từ view: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            
# ================================================
# HÀM XỬ LÝ KHOA (Bảng `khoa`)
# ================================================

def get_all_khoa_simple():
    """Lấy Mã khoa và Tên khoa."""
    # Hàm này đã có, đảm bảo nó tồn tại và hoạt động
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MaKhoa, TenKhoa FROM khoa ORDER BY TenKhoa")
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy danh sách khoa: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_all_khoa_details():
    """Lấy chi tiết tất cả các khoa."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MaKhoa, TenKhoa, GhiChu FROM khoa ORDER BY TenKhoa")
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy chi tiết khoa: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_khoa_detail(makhoa):
    """Lấy chi tiết một khoa dựa vào Mã Khoa."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MaKhoa, TenKhoa, GhiChu FROM khoa WHERE MaKhoa = %s", (makhoa,))
        result = cursor.fetchone()
        return result
    except Error as e:
        print(f"Lỗi khi lấy chi tiết khoa '{makhoa}': {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def add_khoa(makhoa, tenkhoa, ghichu):
    """Thêm một khoa mới."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO khoa (MaKhoa, TenKhoa, GhiChu) VALUES (%s, %s, %s)"
        cursor.execute(query, (makhoa, tenkhoa, ghichu if ghichu else None))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"Lỗi khi thêm khoa: {e}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_khoa(makhoa, tenkhoa, ghichu):
    """Cập nhật thông tin một khoa."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = "UPDATE khoa SET TenKhoa = %s, GhiChu = %s WHERE MaKhoa = %s"
        cursor.execute(query, (tenkhoa, ghichu if ghichu else None, makhoa))
        conn.commit()
        return True # Giả sử thành công nếu không có lỗi
    except Error as e:
        print(f"Lỗi khi cập nhật khoa: {e}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def delete_khoa(makhoa):
    """Xóa một khoa. Sẽ thất bại nếu có ràng buộc khóa ngoại (vd: giảng viên)."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = "DELETE FROM khoa WHERE MaKhoa = %s"
        cursor.execute(query, (makhoa,))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        if e.errno == 1451: # Lỗi khóa ngoại
             print(f"Không thể xóa khoa '{makhoa}': Khoa đang được sử dụng.")
        else:
             print(f"Lỗi khi xóa khoa: {e}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# ================================================
# HÀM XỬ LÝ GIẢNG VIÊN (Bảng `giangvien`)
# ================================================

def get_all_lecturers_detailed():
    """Lấy danh sách chi tiết tất cả giảng viên (JOIN với Khoa)."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # Lấy cả MaKhoa và TenKhoa
        query = """
            SELECT gv.MaGV, gv.TenGiangVien, gv.SDT, gv.NamSinh, gv.MaKhoa, k.TenKhoa, gv.GhiChu
            FROM giangvien gv
            LEFT JOIN khoa k ON gv.MaKhoa = k.MaKhoa
            WHERE gv.MaGV != 1 -- Loại trừ admin
            ORDER BY gv.TenGiangVien
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy danh sách giảng viên chi tiết: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_lecturer_detail(magv):
    """Lấy chi tiết một giảng viên."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT MaGV, TenGiangVien, SDT, MaKhoa, NamSinh, GhiChu FROM giangvien WHERE MaGV = %s"
        cursor.execute(query, (magv,))
        result = cursor.fetchone()
        return result
    except Error as e:
        print(f"Lỗi khi lấy chi tiết giảng viên '{magv}': {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_lecturer_detail_joined(magv):
    """Lấy chi tiết một giảng viên bao gồm Tên Khoa."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = """
            SELECT gv.MaGV, gv.TenGiangVien, gv.SDT, gv.NamSinh, gv.MaKhoa, k.TenKhoa, gv.GhiChu
            FROM giangvien gv
            LEFT JOIN khoa k ON gv.MaKhoa = k.MaKhoa
            WHERE gv.MaGV = %s
        """
        cursor.execute(query, (magv,))
        result = cursor.fetchone()
        return result
    except Error as e:
        print(f"Lỗi khi lấy chi tiết giảng viên (join) '{magv}': {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def add_lecturer(magv, tengv, sdt, makhoa, namsinh, ghichu):
    """Thêm giảng viên mới."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO giangvien (MaGV, TenGiangVien, SDT, MaKhoa, NamSinh, GhiChu)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (magv, tengv, sdt, makhoa, namsinh, ghichu if ghichu else None))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"Lỗi khi thêm giảng viên: {e}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_lecturer(magv, tengv, sdt, makhoa, namsinh, ghichu):
    """Cập nhật thông tin giảng viên."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = """
            UPDATE giangvien
            SET TenGiangVien = %s, SDT = %s, MaKhoa = %s, NamSinh = %s, GhiChu = %s
            WHERE MaGV = %s
        """
        cursor.execute(query, (tengv, sdt, makhoa, namsinh, ghichu if ghichu else None, magv))
        conn.commit()
        return True # Thành công nếu không lỗi
    except Error as e:
        print(f"Lỗi khi cập nhật giảng viên: {e}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def delete_lecturer(magv):
    """Xóa giảng viên và tài khoản liên quan. Trả về (success, message)."""
    conn = connect_db()
    if conn is None: return False, "Không thể kết nối CSDL."
    try:
        cursor = conn.cursor()
        conn.start_transaction()

        # 1. Xóa tài khoản trước (FK từ taikhoan -> giangvien)
        cursor.execute("DELETE FROM taikhoan WHERE MaGV = %s", (magv,))
        
        # 2. Xóa giảng viên (sẽ thất bại nếu GV là GVCN hoặc được phân công LHP)
        cursor.execute("DELETE FROM giangvien WHERE MaGV = %s", (magv,))
        rowcount = cursor.rowcount

        conn.commit()
        if rowcount > 0:
            return True, "Xóa giảng viên và tài khoản thành công."
        else:
            # Có thể GV không tồn tại?
            return False, "Không tìm thấy giảng viên để xóa."

    except Error as e:
        conn.rollback()
        if e.errno == 1451: # Lỗi khóa ngoại
             # Kiểm tra xem lỗi FK đến từ bảng nào
             if 'fk_lop_gv' in e.msg:
                 return False, "Không thể xóa: Giảng viên đang là GVCN của một lớp."
             elif 'fk_lophocphan_gv' in e.msg:
                 return False, "Không thể xóa: Giảng viên đang được phân công dạy lớp học phần."
             else:
                 return False, f"Lỗi ràng buộc khóa ngoại: {e.msg}"
        else:
             print(f"Lỗi khi xóa giảng viên: {e}")
             return False, f"Lỗi CSDL: {e.msg}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def get_lecturers_by_khoa(makhoa):
    """Lọc giảng viên theo Khoa (JOIN với Khoa)."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = """
            SELECT gv.MaGV, gv.TenGiangVien, gv.SDT, gv.NamSinh, gv.MaKhoa, k.TenKhoa, gv.GhiChu
            FROM giangvien gv
            LEFT JOIN khoa k ON gv.MaKhoa = k.MaKhoa
            WHERE gv.MaKhoa = %s AND gv.MaGV != 1
            ORDER BY gv.TenGiangVien
        """
        cursor.execute(query, (makhoa,))
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lọc giảng viên theo khoa '{makhoa}': {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- Sửa hàm get_all_lop_simple cho AdminAcademic ---
def get_all_lop_simple():
    """
    Lấy thông tin cơ bản của lớp, trả về dict {key_tuple: display_string_with_description}.
    Hàm này được dùng bởi AdminAcademic.
    """
    query = """
        SELECT MaBac, MaNienKhoa, MaNganh, STTLop, TenLop
        FROM lop ORDER BY MaBac, MaNienKhoa, MaNganh, STTLop
    """
    conn = connect_db()
    if conn is None: return {} # Trả về dict rỗng nếu lỗi
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        lop_dict = {}
        if results:
            for row in results:
                key = (row[0], row[1], row[2], row[3])
                # Display có cả tên mô tả
                display = f"{row[0]}{row[1]}{row[2]}{row[3]} - {row[4]}"
                lop_dict[key] = display
        return lop_dict
    except Error as e:
        print(f"Lỗi khi lấy danh sách lớp đơn giản (cho Academic): {e}")
        return {} # Trả về dict rỗng nếu lỗi
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ================================================
# HÀM XỬ LÝ THÔNG BÁO (Bảng `thongbao`)
# ================================================

def add_thongbao(tieu_de, noi_dung, image_blob):
    """Thêm một thông báo mới."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO thongbao (TieuDeThongBao, NoiDung, NgayDang, HinhAnh)
            VALUES (%s, %s, NOW(), %s)
        """
        cursor.execute(query, (tieu_de, noi_dung, image_blob))
        conn.commit()
        return cursor.lastrowid is not None # Trả về True nếu insert thành công
    except Error as e:
        print(f"Lỗi khi thêm thông báo: {e}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def update_thongbao(thongbao_id, tieu_de, noi_dung, image_blob):
    """Cập nhật thông báo."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = """
            UPDATE thongbao
            SET TieuDeThongBao = %s, NoiDung = %s, HinhAnh = %s, NgayDang = NOW()
            WHERE thongbao_id = %s
        """
        cursor.execute(query, (tieu_de, noi_dung, image_blob, thongbao_id))
        conn.commit()
        return True # Giả sử thành công nếu không lỗi
    except Error as e:
        print(f"Lỗi khi cập nhật thông báo: {e}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def delete_thongbao(thongbao_id):
    """Xóa một thông báo."""
    conn = connect_db()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = "DELETE FROM thongbao WHERE thongbao_id = %s"
        cursor.execute(query, (thongbao_id,))
        conn.commit()
        return cursor.rowcount > 0 # Trả về True nếu có dòng bị xóa
    except Error as e:
        print(f"Lỗi khi xóa thông báo: {e}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_all_thongbao():
    """Lấy tất cả thông báo để hiển thị trên bảng."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        # Lấy cả BLOB ảnh
        query = """
            SELECT thongbao_id, TieuDeThongBao, NoiDung, NgayDang, HinhAnh
            FROM thongbao
            ORDER BY NgayDang DESC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Lỗi khi lấy danh sách thông báo: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_thongbao_detail(thongbao_id):
    """Lấy chi tiết một thông báo (bao gồm cả ảnh blob)."""
    conn = connect_db()
    if conn is None: return None
    try:
        cursor = conn.cursor()
        query = "SELECT TieuDeThongBao, NoiDung, NgayDang, HinhAnh FROM thongbao WHERE thongbao_id = %s"
        cursor.execute(query, (thongbao_id,))
        result = cursor.fetchone()
        return result # Trả về tuple (tieu_de, noi_dung, ngay_dang, image_blob) hoặc None
    except Error as e:
        print(f"Lỗi khi lấy chi tiết thông báo '{thongbao_id}': {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
