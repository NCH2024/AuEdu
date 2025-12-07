"""
Định nghĩa các model Python tương ứng với các bảng trong schema MySQL.
Có thể mở rộng/thay đổi để tích hợp với ORM như SQLAlchemy hoặc Django ORM nếu cần.
"""

from datetime import datetime
from typing import Optional

class Bac:
    def __init__(self, MaBac: str, TenBac: str):
        self.MaBac = MaBac
        self.TenBac = TenBac

class BuoiHoc:
    def __init__(self, MaBuoiHoc: int, MaLopHocPhan: str, Thu: int, NgayHoc: datetime.date, MaLoaiDiemDanh: str, GhiChu: Optional[str]):
        self.MaBuoiHoc = MaBuoiHoc
        self.MaLopHocPhan = MaLopHocPhan
        self.Thu = Thu
        self.NgayHoc = NgayHoc
        self.MaLoaiDiemDanh = MaLoaiDiemDanh
        self.GhiChu = GhiChu

class DiemDanhSV:
    def __init__(self, MaBuoiHoc: int, MaSV: int, MaTrangThai: str, ThoiGianGhiNhan: datetime):
        self.MaBuoiHoc = MaBuoiHoc
        self.MaSV = MaSV
        self.MaTrangThai = MaTrangThai
        self.ThoiGianGhiNhan = ThoiGianGhiNhan

class GiangVien:
    def __init__(self, MaGV: int, TenGiangVien: str, SDT: Optional[int], MaKhoa: Optional[str], NamSinh: Optional[datetime.date], GhiChu: Optional[str]):
        self.MaGV = MaGV
        self.TenGiangVien = TenGiangVien
        self.SDT = SDT
        self.MaKhoa = MaKhoa
        self.NamSinh = NamSinh
        self.GhiChu = GhiChu

class HocKy:
    def __init__(self, MaHocKy: str, TenHocKy: str):
        self.MaHocKy = MaHocKy
        self.TenHocKy = TenHocKy

class HocPhan:
    def __init__(self, MaHocPhan: str, TenHocPhan: str, SoTinChi: int, TongSoTiet: int):
        self.MaHocPhan = MaHocPhan
        self.TenHocPhan = TenHocPhan
        self.SoTinChi = SoTinChi
        self.TongSoTiet = TongSoTiet

class Khoa:
    def __init__(self, MaKhoa: str, TenKhoa: str, GhiChu: Optional[str]):
        self.MaKhoa = MaKhoa
        self.TenKhoa = TenKhoa
        self.GhiChu = GhiChu

class LoaiDiemDanh:
    def __init__(self, MaLoaiDiemDanh: str, TenLoaiDiemDanh: str):
        self.MaLoaiDiemDanh = MaLoaiDiemDanh
        self.TenLoaiDiemDanh = TenLoaiDiemDanh

class Lop:
    def __init__(self, MaBac: str, MaNienKhoa: int, MaNganh: str, STTLop: str, TenLop: str, MaGV: Optional[int], MaKhoa: str):
        self.MaBac = MaBac
        self.MaNienKhoa = MaNienKhoa
        self.MaNganh = MaNganh
        self.STTLop = STTLop
        self.TenLop = TenLop
        self.MaGV = MaGV
        self.MaKhoa = MaKhoa

class LopHocPhan:
    def __init__(self, MaLopHocPhan: str, MaHocPhan: str, MaBac: str, MaNienKhoa: int, MaNganh: str, STTLop: str, SoBuoi: int, TietMoiBuoi: int, MaHocKy: str, MaGV: int):
        self.MaLopHocPhan = MaLopHocPhan
        self.MaHocPhan = MaHocPhan
        self.MaBac = MaBac
        self.MaNienKhoa = MaNienKhoa
        self.MaNganh = MaNganh
        self.STTLop = STTLop
        self.SoBuoi = SoBuoi
        self.TietMoiBuoi = TietMoiBuoi
        self.MaHocKy = MaHocKy
        self.MaGV = MaGV

class Nganh:
    def __init__(self, MaNganh: str, TenNganh: Optional[str]):
        self.MaNganh = MaNganh
        self.TenNganh = TenNganh

class NienKhoa:
    def __init__(self, MaNienKhoa: int, TenNienKhoa: str):
        self.MaNienKhoa = MaNienKhoa
        self.TenNienKhoa = TenNienKhoa

class SinhVien:
    def __init__(self, MaSV: int, MaBac: str, MaNienKhoa: int, MaNganh: str, STTLop: str, HoTenSV: Optional[str], NamSinh: Optional[datetime.date], DiaChi: Optional[str], GioiTinh: Optional[str], GhiChu: Optional[str]):
        self.MaSV = MaSV
        self.MaBac = MaBac
        self.MaNienKhoa = MaNienKhoa
        self.MaNganh = MaNganh
        self.STTLop = STTLop
        self.HoTenSV = HoTenSV
        self.NamSinh = NamSinh
        self.DiaChi = DiaChi
        self.GioiTinh = GioiTinh
        self.GhiChu = GhiChu

class TaiKhoan:
    def __init__(self, TenDangNhap: str, MatKhau: str, MaGV: int, VaiTro: str, GhiChu: Optional[str]):
        self.TenDangNhap = TenDangNhap
        self.MatKhau = MatKhau
        self.MaGV = MaGV
        self.VaiTro = VaiTro
        self.GhiChu = GhiChu

class ThongBao:
    def __init__(self, thongbao_id: int, TieuDeThongBao: str, NgayDang: Optional[datetime], NoiDung: str, HinhAnh: Optional[bytes]):
        self.thongbao_id = thongbao_id
        self.TieuDeThongBao = TieuDeThongBao
        self.NgayDang = NgayDang
        self.NoiDung = NoiDung
        self.HinhAnh = HinhAnh

class TrangThaiDiemDanh:
    def __init__(self, MaTrangThai: str, TenTrangThai: str, GhiChu: Optional[str]):
        self.MaTrangThai = MaTrangThai
        self.TenTrangThai = TenTrangThai
        self.GhiChu = GhiChu
