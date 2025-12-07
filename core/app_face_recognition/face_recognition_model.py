import os
import cv2
import threading
import time
import numpy as np
import concurrent.futures
import torch
import shutil
import pygame
from ultralytics import YOLO
from insightface.app import FaceAnalysis
from collections import deque
from gui.base.utils import *
from tkinter import messagebox


import core.database as Db
from core.app_face_recognition.liveness_antispoof import LivenessAntiSpoof


class FaceRecognitionModel:
    """
    Full FaceRecognitionModel integrated with LivenessAntiSpoof (probability-based).
    - process_frame(frame, ma_buoi_hoc=None, mode="multi_person")
      returns (annotated_frame, newly_recognized_list, total_recognized_count)
    """

    def __init__(
        self,
        sounds_path,
        model_path,
        liveness_model_path=None,
        device=None,
        similarity_threshold=None,
        threshold_security=None,
        smooth_factor=None,
        frame_skip=5,
    ):
        self.model_path = model_path
        self.sounds_path = sounds_path
        self.similarity_threshold = float(similarity_threshold)
        self.threshold_security = float(threshold_security)
        self.smooth_factor = int(smooth_factor)
        self.frame_skip = int(frame_skip)
        self.liveness_history = {}
        
        self.check_in_type = None
        
        self.yolo = None
        self.face_model = None

        # DB
        self.db = Db

        # models
        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")

        # liveness (optional)
        self.liveness = None
        if liveness_model_path:
            try:
                self.liveness = LivenessAntiSpoof(liveness_model_path, device=self.device)
            except Exception:
                self.liveness = None

        # known faces
        encs, ids = self.db.load_face_encodings()
        if isinstance(encs, list):
            encs = np.array(encs)
        if encs is None:
            encs = np.zeros((0, 512), dtype=np.float32)
            ids = []
        self.known_face_encodings = encs
        self.known_face_ids = ids

        # runtime state
        self.recognized_students = set()
        self.track_data = {}  # track_id -> info dict
        self.lock = threading.Lock()

        # executor
        self._create_executor()

        # sounds
        
        self.sound_success = os.path.join(self.sounds_path, "success.wav")
        self.sound_fail = os.path.join(self.sounds_path, "fail.wav")

    # ---------------- helpers ----------------
    def _ensure_models(self, dialog=None):
        def update(msg, progress=None):
            print("[ModelLoad]", msg)
            if dialog:
                try:
                    dialog.label.configure(text=msg)
                    if progress is not None:
                        dialog.update_progress(progress)
                except Exception:
                    pass

        try:
            os.makedirs(self.model_path, exist_ok=True)

            yolo_path = os.path.join(self.model_path, "yolov8n.pt")
            insight_root = os.path.join(self.model_path, "models_insightface")
            insight_path = os.path.join(insight_root, "buffalo_l")

            # --- Hiện thông báo nếu lần đầu ---
            if not os.path.exists(yolo_path) and not os.path.exists(insight_path):
                if dialog:
                    try: dialog.withdraw()
                    except: pass
                messagebox.showinfo(
                    "LỜI NHẮC PHẦN MỀM",
                    "Lần đầu sử dụng, cần tải mô hình nhận dạng. Vui lòng đợi vài phút.",
                    icon="info",
                )
                if dialog:
                    try: dialog.deiconify()
                    except: pass

            # --- YOLO ---
            if not os.path.exists(yolo_path):
                update("Đang tải YOLO...", 0.2)
                model = YOLO("yolov8n.pt")  # tự tải về từ ultralytics
                try:
                    src = getattr(model, "ckpt_path", None)
                    if src and os.path.exists(src):
                        shutil.copy(src, yolo_path)
                except Exception:
                    pass
                update("Đã tải YOLO xong.", 0.4)
            else:
                update("Đã có YOLO.", 0.4)

            # --- INSIGHTFACE ---
            if not os.path.exists(insight_path):
                update("Đang tải InsightFace...", 0.6)
                tmp = FaceAnalysis(name="buffalo_l", root=self.model_path)
                ctx_id = 0 if "cuda" in str(self.device) else -1
                tmp.prepare(ctx_id=ctx_id)
                update("InsightFace sẵn sàng.", 0.8)
            else:
                update("Đã có InsightFace.", 0.8)

            # --- Khởi tạo thực tế ---
            yolo_abs = os.path.join(self.model_path, "yolov8n.pt")
            self.yolo = YOLO(yolo_abs)
            ctx_id = 0 if "cuda" in str(self.device) else -1
            self.face_model = FaceAnalysis(name="buffalo_l", root=self.model_path)
            self.face_model.prepare(ctx_id=ctx_id)

            print(f"[DEBUG]  YOLO loaded: {self.yolo is not None}, InsightFace loaded: {self.face_model is not None}")
            update(" Hoàn tất kiểm tra mô hình.", 1.0)
            return True

        except Exception as e:
            update(f"Lỗi tải mô hình: {e}")
            self.yolo = None
            self.face_model = None
            return False

        finally:
            if dialog:
                try: dialog.after(1000, dialog.stop)
                except Exception:
                    pass



    def _create_executor(self):
        try:
            if getattr(self, "executor", None) is None or getattr(self.executor, "_shutdown", False):
                self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 2)
                self.processing_futures = {}
        except Exception:
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
            self.processing_futures = {}

    def _safe_play_sound(self, kind="success"):
        file = self.sound_success if kind == "success" else self.sound_fail
        try:
            if os.path.exists(file):
                threading.Thread(target=lambda: (pygame.mixer.music.load(file), pygame.mixer.music.play()), daemon=True).start()
        except Exception:
            pass

    def _find_best_match(self, embedding):
        if self.known_face_encodings.shape[0] == 0:
            return None, 0.0
        denom = (np.linalg.norm(self.known_face_encodings, axis=1) * (np.linalg.norm(embedding) + 1e-8)) + 1e-12
        sims = np.dot(self.known_face_encodings, embedding) / denom
        idx = int(np.argmax(sims))
        return self.known_face_ids[idx], float(sims[idx])
    
    def _find_best_match_on_subset(self, embedding, known_encs_subset, known_ids_subset):
        """
        Phiên bản _find_best_match hoạt động trên tập con dữ liệu embeddings.
        """
        if known_encs_subset.shape[0] == 0:
            return None, 0.0
        
        # Công thức Cosine Similarity trên tập con
        denom = (np.linalg.norm(known_encs_subset, axis=1) * (np.linalg.norm(embedding) + 1e-8)) + 1e-12
        sims = np.dot(known_encs_subset, embedding) / denom
        
        idx = int(np.argmax(sims))
        return known_ids_subset[idx], float(sims[idx])

    def reload_known_faces(self):
        encs, ids = self.db.load_face_encodings()
        if isinstance(encs, list):
            encs = np.array(encs)
        if encs is None:
            encs = np.zeros((0, 512), dtype=np.float32)
            ids = []
        with self.lock:
            self.known_face_encodings = encs
            self.known_face_ids = ids

    # ---------------- lifecycle ----------------
    def stop(self):
        # cancel pending futures
        for f in list(getattr(self, "processing_futures", {}).values()):
            try:
                f.cancel()
            except Exception:
                pass

        # shutdown executor
        try:
            if getattr(self, "executor", None):
                self.executor.shutdown(wait=False)
        except Exception:
            pass

        with self.lock:
            self.track_data.clear()
            self.recognized_students.clear()
            self.processing_futures = {}

        # recreate executor for next start
        try:
            self._create_executor()
        except Exception:
            pass

    # ---------------- public ----------------
    def process_frame(self, frame, ma_buoi_hoc=None, mode="multi_person"):
        if self.yolo is None or self.face_model is None:
            print("[ERROR] Mô hình chưa được khởi tạo đầy đủ.")
            return frame, [], 0

        self._create_executor()
        if mode == "one_person":
            return self.process_frame_one_person(frame, ma_buoi_hoc)
        else:
            return self.process_frame_multi_person(frame, ma_buoi_hoc)

    def process_frame_one_person(self, frame, ma_buoi_hoc=None):
        return self._generic_process(frame, ma_buoi_hoc, single=True)

    def process_frame_multi_person(self, frame, ma_buoi_hoc=None):
        return self._generic_process(frame, ma_buoi_hoc, single=False)

    # ---------------- core pipeline ----------------
    def _generic_process(self, frame, ma_buoi_hoc, single=False):
        if self.yolo is None or self.face_model is None:
            print("[ERROR] Mô hình chưa được khởi tạo đầy đủ.")
            return frame, [], 0
        
        results = self.yolo.track(frame, tracker='bytetrack.yaml', imgsz=320, classes=0, persist=True, verbose=False, device=self.device)
        boxes = results[0].boxes if results and results[0].boxes is not None else []

        # collect current ids
        current_ids = set()
        for b in boxes:
            if b.id is None:
                continue
            try:
                current_ids.add(int(b.id[0]))
            except Exception:
                pass

        # cleanup tracks left frame
        with self.lock:
            for tid in list(self.track_data.keys()):
                if tid not in current_ids:
                    fut = self.processing_futures.pop(tid, None)
                    if fut:
                        try:
                            fut.cancel()
                        except Exception:
                            pass
                    self.track_data.pop(tid, None)

        # select targets
        if single and boxes:
            largest = max(boxes, key=lambda b: ((b.xyxy[0][2] - b.xyxy[0][0]) * (b.xyxy[0][3] - b.xyxy[0][1])))
            target_boxes = [largest] if largest.id is not None else []
        else:
            target_boxes = [b for b in boxes if b.id is not None]

        h, w = frame.shape[:2]
        for b in target_boxes:
            try:
                tid = int(b.id[0])
            except Exception:
                continue
            xy = b.xyxy.cpu().numpy().astype(int)[0]
            x1, y1, x2, y2 = xy
            with self.lock:
                info = self.track_data.setdefault(
                    tid,
                    {"frame_count": 0, "label": "Detecting...", "face_bbox": None, "color": (255, 255, 0), "newly_recognized": False, "person_bbox": (x1, y1, x2, y2)},
                )
                info["person_bbox"] = (x1, y1, x2, y2)
                info["frame_count"] += 1
                submit_now = (info["frame_count"] % self.frame_skip == 0)

            if submit_now:
                cx1, cy1 = max(0, x1), max(0, y1)
                cx2, cy2 = min(w, x2), min(h, y2)
                crop = frame[cy1:cy2, cx1:cx2]
                if getattr(self, "executor", None) is not None:
                    fut = self.processing_futures.get(tid)
                    if fut is None or fut.done():
                        try:
                            self.processing_futures[tid] = self.executor.submit(self._recognize_worker, tid, crop.copy(), (cx1, cy1, cx2, cy2), ma_buoi_hoc, single)
                        except RuntimeError:
                            pass

        # collect finished futures
        for tid, fut in list(self.processing_futures.items()):
            if fut.done():
                try:
                    res = fut.result()
                    if res:
                        with self.lock:
                            self.track_data[tid].update(res)
                except Exception:
                    pass
                finally:
                    self.processing_futures.pop(tid, None)

        # draw frame: draw person box (no text) and draw face box + label only if available
        out = frame.copy()
        newly_ids = []
        with self.lock:
            for tid, info in self.track_data.items():
                px1, py1, px2, py2 = info.get("person_bbox", (0, 0, 0, 0))
                cv2.rectangle(out, (px1, py1), (px2, py2), (100, 100, 100), 1)
                label = info.get("label", "Detecting...")
                color = info.get("color", (255, 255, 0))
                fb = info.get("face_bbox")
                if fb:
                    fx1, fy1, fx2, fy2 = fb
                    cv2.rectangle(out, (fx1, fy1), (fx2, fy2), color, 1)
                    cv2.putText(out, label, (fx1, fy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

                if info.get("newly_recognized"):
                    lbl = info.get("label", "")
                    if lbl.startswith("MSV:"):
                        try:
                            sid = int(lbl.split(":", 1)[1].strip())
                            newly_ids.append(sid)
                        except Exception:
                            pass
                    info["newly_recognized"] = False

        return out, newly_ids, len(self.recognized_students)

    def _recognize_worker(self, track_id, person_crop, person_bbox_abs, ma_buoi_hoc, single_mode):
        try:
            faces = self.face_model.get(person_crop)
            if not faces:
                return {"label": "NoFace", "color": (128, 128, 128), "face_bbox": None}
            
            face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            fx1 = int(face.bbox[0]) + person_bbox_abs[0]
            fy1 = int(face.bbox[1]) + person_bbox_abs[1]
            fx2 = int(face.bbox[2]) + person_bbox_abs[0]
            fy2 = int(face.bbox[3]) + person_bbox_abs[1]

            bx1, by1 = max(0, int(face.bbox[0])), max(0, int(face.bbox[1]))
            bx2, by2 = min(person_crop.shape[1], int(face.bbox[2])), min(person_crop.shape[0], int(face.bbox[3]))
            face_crop = person_crop[by1:by2, bx1:bx2]
            emb = face.embedding

            # --- Xử lý Liveness ---
            if self.liveness and face_crop.size > 0:
                result = self.liveness.predict(face_crop)
                if result is None:
                    return {"label": "ERR", "color": (0, 0, 255), "face_bbox": None}
                else:
                    prob_real = float(result['score']) if result['label'] == 0 else 1.0 - float(result['score'])
                    hist = self.liveness_history.setdefault(track_id, deque(maxlen=self.smooth_factor))
                    hist.append(prob_real)
                    
                    if len(hist) < self.smooth_factor:
                        return {"label": "Checking...", "color": (255, 165, 0), "face_bbox": (fx1, fy1, fx2, fy2)}

                    mean_prob = float(np.mean(hist))
                    LIVENESS_THRESHOLD = self.threshold_security
                    
                    if mean_prob > LIVENESS_THRESHOLD:
                        with self.lock:
                            self.track_data[track_id]["label"] = "FAKE"
                            self.track_data[track_id]["color"] = (0, 0, 255)
                        return {"label": "FAKE", "color": (0, 0, 255), "face_bbox": (fx1, fy1, fx2, fy2)}
            
            # --- Logic nhận dạng ---
            best_id, sim = self._find_best_match(emb)
            if best_id is not None and sim >= self.similarity_threshold:
                newly = False
                if best_id not in self.recognized_students:
                    self.recognized_students.add(best_id)
                    newly = True
                
                #  GHI NHẬN ĐIỂM DANH - SỬA LỖI
                try:
                    if ma_buoi_hoc is not None:
                        # Xác định lần điểm danh (1 hoặc 2)
                        if self.check_in_type == "start":
                            so_lan = 1
                        elif self.check_in_type == "end":
                            so_lan = 2
                        else:
                            so_lan = 1  # Mặc định lần 1
                        
                        # print(f"Đang điểm danh: MSSV={best_id}, Buổi={ma_buoi_hoc}, Lần={so_lan}")
                        
                        #  GỌI HÀM VỚI THAM SỐ ĐÚNG
                        success, message = self.db.record_attendance(
                            ma_sv=int(best_id), 
                            ma_buoi_hoc=ma_buoi_hoc, 
                            so_lan=so_lan,
                            ma_trang_thai="CM"
                        )
                        
                        # if not success:
                        #     print(f"Điểm danh thất bại: {message}")
                        # else:
                        #     print(f" {message}")
                            
                except Exception as e:
                    print(f"Lỗi khi ghi điểm danh: {e}")
                    import traceback
                    traceback.print_exc()

                if newly and single_mode:
                    self._safe_play_sound("success")

                return {
                    "label": f"MSV: {best_id}", 
                    "color": (0, 255, 0), 
                    "face_bbox": (fx1, fy1, fx2, fy2), 
                    "newly_recognized": newly
                }
            else:
                return {"label": "UNKNOWN", "color": (128, 0, 255), "face_bbox": (fx1, fy1, fx2, fy2)}
        
        except Exception as e:
            print(f"Lỗi trong _recognize_worker: {e}")
            import traceback
            traceback.print_exc()
            return {"label": "ERR", "color": (0, 0, 255), "face_bbox": None}

    # ---------------- training ----------------
    def start_training(self, student_id, frame_generator, mode="quick"):
        """
        Train face for a student.
        mode: "quick" (30 frames) or "full" (60 frames)
        Yield: (progress, message)
        """
        num_frames = 30 if mode == "quick" else 60
        embeddings = []
        frames = []
        found_frames = 0
        max_total_frames = num_frames * 3
        
        print(f"Bắt đầu quá trình đào tạo cho sinh viên ID: {student_id}")

        try:
            frame_count = 0
            for frame in frame_generator:
                if found_frames >= num_frames:
                    break
                
                frame_count += 1
                if frame_count > max_total_frames:
                    print("LỖI: Hết thời gian chờ, không thể tìm thấy đủ khuôn mặt.")
                    yield 100, "error: Hết thời gian chờ, không thể tìm thấy khuôn mặt"
                    return

                faces = self.face_model.get(frame)
                if len(faces) > 0:
                    print(f"Đã tìm thấy {len(faces)} khuôn mặt trong khung hình số {frame_count}.")
                    
                    # Get the largest face
                    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                    emb = face.embedding
                    
                    if emb is not None:
                        embeddings.append(emb)
                        frames.append(frame)
                        found_frames += 1
                        print(f"Đã lấy embedding thành công. Tổng số embedding: {len(embeddings)}")
                    else:
                        print(f"LỖI: Embedding rỗng trong khung hình số {frame_count}.")
                else:
                    print(f"KHÔNG TÌM THẤY KHUÔN MẶT trong khung hình số {frame_count}. Bỏ qua.")

                # Yield progress (0-99%) for the capture phase
                progress = int((found_frames / num_frames) * 99)
                yield progress, "Đang thu thập dữ liệu khuôn mặt..."
            
            # --- PHASE 2: PROCESSING AND SAVING TO DB ---
            yield 99, "Đang xử lý và lưu dữ liệu..."

            print(f"DEBUG: Vòng lặp kết thúc. Tổng số embedding hợp lệ: {len(embeddings)}")
            
            if len(embeddings) == 0:
                print("LỖI: Không có embedding hợp lệ nào được thu thập.")
                yield 100, "Không lấy được embedding"
                return

            embeddings_array = np.array(embeddings)
            print(f"DEBUG: Đã chuyển đổi list thành numpy array, kích thước: {embeddings_array.shape}")
            
            avg_emb = np.mean(embeddings_array, axis=0)
            print(f"Đã tính toán embedding trung bình, kích thước: {avg_emb.shape}")
            # 1. Lọc bỏ embedding của chính sinh viên đang được cập nhật/thêm mới.
            known_encs = self.known_face_encodings
            known_ids = self.known_face_ids
            
            known_encs_filtered = []
            known_ids_filtered = []
            
            # Duyệt qua tất cả các ID đã biết trong CSDL
            for i, existing_id in enumerate(known_ids):
                # Nếu ID đã biết KHÁC với ID đang được đào tạo, thì giữ lại để kiểm tra
                # Chúng ta chuyển cả hai về dạng string để so sánh an toàn
                if str(existing_id) != str(student_id):
                    known_encs_filtered.append(known_encs[i])
                    known_ids_filtered.append(existing_id)
            
            known_encs_filtered = np.array(known_encs_filtered)
            
            # 2. Thực hiện tìm kiếm trùng khớp trên tập dữ liệu ĐÃ LỌC
            # (Sử dụng hàm _find_best_match_on_subset nếu bạn đã thêm nó, hoặc logic tương đương)
            # Nếu chưa thêm hàm _find_best_match_on_subset, ta sẽ dùng logic bên dưới
            
            best_id, sim = None, 0.0
            if known_encs_filtered.shape[0] > 0:
                # Tái tạo logic tìm kiếm khớp tốt nhất chỉ trên tập con đã lọc
                denom = (np.linalg.norm(known_encs_filtered, axis=1) * (np.linalg.norm(avg_emb) + 1e-8)) + 1e-12
                sims = np.dot(known_encs_filtered, avg_emb) / denom
                idx = int(np.argmax(sims))
                best_id = known_ids_filtered[idx]
                sim = float(sims[idx])

            print(f"DEBUG: Kết quả kiểm tra trùng lặp (trên ID khác): ID={best_id}, Sim={sim:.4f}")

            # 3. So sánh độ tương đồng
            if best_id is not None and sim >= self.similarity_threshold:
                print(f"LỖI: Phát hiện trùng lặp với MSSV đã tồn tại: {best_id}")
                # Trả về thông báo lỗi theo yêu cầu
                yield 100, f"DỮ LIỆU TRÙNG LẶP, đã có khuôn mặt này cho MSSV: {best_id}"
                return
            image_blob = None
            if len(frames) > 0:
                try:
                    first_frame = frames[0]
                    _, buffer = cv2.imencode(".jpg", first_frame)
                    image_blob = buffer.tobytes()
                    print(f"Đã tạo ảnh đại diện thành công, kích thước blob: {len(image_blob)} bytes")
                except Exception as e:
                    print(f"LỖI: Không tạo được ảnh đại diện: {e}")

            success = False
            if image_blob is not None:
                print(f"Đang gọi hàm lưu dữ liệu vào DB với student_id: {student_id}")
                success = self.db.update_student_face_data(
                    student_id,
                    avg_emb,
                    image_blob,
                    time.strftime("%Y-%m-%d %H:%M:%S")
                )
                print(f"Hàm lưu DB trả về: {success}")
            else:
                print("LỖI: Không có image_blob để lưu vào DB. Dữ liệu sẽ không được lưu.")
            
            if success:
                print("THÀNH CÔNG: Đã lưu dữ liệu khuôn mặt vào DB.")
                self.reload_known_faces()
                yield 100, "success"
            else:
                print("THẤT BẠI: Lỗi khi lưu dữ liệu khuôn mặt vào DB.")
                yield 100, "fail"

        except Exception as e:
            print(f"LỖI NGHIÊM TRỌNG trong start_training: {e}")
            yield 100, f"error: {str(e)}"