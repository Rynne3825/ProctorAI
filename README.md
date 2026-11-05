# 🛡️ ProctorAI - Hệ Thống Giám Sát Phòng Thi Thông Minh

> **Dự Án Capstone:** Samsung Innovation Campus (SIC)  
> **Kiến Trúc:** Clean Modular Architecture (FastAPI + YOLO11 + MediaPipe Face Mesh)  
> **Phiên Bản:** 2.0.0

---

## 📖 1. Giới Thiệu Tổng Quan

**ProctorAI** là giải pháp phần mềm thị giác máy tính thông minh hỗ trợ giám thị tự động phát hiện các hành vi gian lận trong phòng thi trực tuyến hoặc phòng máy theo thời gian thực (Real-time).

### Các tính năng nhận diện cốt lõi:
1. 📱 **Phát hiện thiết bị cấm:** Nhận diện điện thoại di động và phân biệt với máy tính cầm tay hợp lệ bằng mô hình học sâu **YOLO11**. Dễ dàng cấu hình mở rộng thêm thiết bị mới (Smartwatch, Tai nghe, Tài liệu...).
2. 🔄 **Ước lượng hướng đầu (Head Pose Estimation):** Ứng dụng **MediaPipe Face Mesh** kết hợp giải thuật phối cảnh 3D-sang-2D **solvePnP** của OpenCV để tính toán góc Euler (Pitch: cúi/ngửa mặt, Yaw: quay đầu trái/phải/quay ra sau).
3. 🚫 **Phát hiện che camera / rời vị trí:** Tự động cảnh báo khi mất mặt hoặc camera bị che khuất quá ngưỡng thời gian quy định.
4. 📸 **Chụp bằng chứng tự động:** Chụp ảnh khoảnh khắc vi phạm (có kèm thông tin thời gian, thời lượng) và tự động ghi nhật ký vào file CSV chuẩn `utf-8-sig` (tương thích tuyệt đối với Microsoft Excel tiếng Việt).
5. 🎛️ **Công tắc Master Bật/Tắt Tổng Thể (Master Power Switch):** 1 click để kích hoạt toàn bộ luồng camera + AI; khi tắt hệ thống tự động giải phóng camera phần cứng và đưa tải CPU/GPU về 0%.

---

## 📂 2. Cấu Trúc Thư Mục Module Hóa

```
ProctorAI/
├── .venv/                         # Môi trường ảo Python 3.10 có sẵn
├── config.yaml                    # File cấu hình tập trung (ngưỡng vi phạm, camera, AI)
├── main.py                        # Điểm khởi chạy máy chủ chính
├── run.bat                        # Script 1-click kích hoạt venv & mở trình duyệt
├── requirements.txt               # Danh mục thư viện phụ thuộc
├── README.md                      # Tài liệu hướng dẫn
├── .gitignore                     # Cấu hình bỏ qua file tạm, cache, logs
│
├── models/
│   └── best.pt                    # Trọng số YOLO11 suy luận chính thức (5.48 MB)
│
├── logs/                          # Thư mục lưu nhật ký vi phạm (CSV utf-8-sig)
├── screenshots/                   # Thư mục lưu ảnh chụp bằng chứng vi phạm
│
├── static/
│   ├── css/
│   │   └── style.css              # Giao diện Dark Modern Dashboard
│   └── js/
│       └── app.js                 # Xử lý logic Master Switch, Polling KPI & Gallery
│
├── templates/
│   └── index.html                 # Khung HTML ngữ nghĩa chuẩn SEO & responsive
│
└── src/
    ├── __init__.py
    ├── config.py                  # Dataclass load cấu hình từ YAML
    ├── core/
    │   ├── __init__.py
    │   ├── state.py               # Quản lý trạng thái đa luồng & Master Switch
    │   └── logger.py              # Xử lý ghi CSV & lưu ảnh snapshot
    ├── vision/
    │   ├── __init__.py
    │   ├── head_pose.py           # Ước lượng hướng đầu (MediaPipe + solvePnP)
    │   ├── yolo_detector.py       # Bộ nhận diện thiết bị YOLO linh hoạt
    │   ├── hud_renderer.py        # Vẽ giao diện tiếng Việt & bounding box lên video
    │   └── camera_worker.py       # Luồng Camera nền & pipeline suy luận
    └── web/
        ├── __init__.py
        └── app.py                 # FastAPI backend server & streaming routes
```

---

## 🚀 3. Hướng Dẫn Khởi Chạy

### Cách 1: Chạy 1-Click (Khuyến nghị trên Windows)
Nhấp đúp chuột vào file **`run.bat`**:
* Hệ thống sẽ tự động kích hoạt môi trường ảo `.venv`.
* Tự động bật trình duyệt web tại địa chỉ: `http://127.0.0.1:8000`.
* Khởi động máy chủ Uvicorn tốc độ cao.

### Cách 2: Chạy thủ công từ Terminal
```powershell
# 1. Kích hoạt môi trường ảo
.\.venv\Scripts\activate

# 2. Khởi chạy ứng dụng
python main.py
```

---

## ⚙️ 4. Tùy Biến Cấu Hình (`config.yaml`)

Bạn có thể thay đổi các tham số hoạt động mà **không cần chỉnh sửa mã nguồn Python**:

```yaml
camera:
  device_id: 0                     # Cổng webcam (0: webcam mặc định)
  width: 640                       # Độ phân giải chiều rộng
  height: 480                      # Độ phân giải chiều cao
  fps_limit: 30                    # Giới hạn khung hình/giây

rules:
  violation_threshold_seconds: 2.0 # Giây vi phạm liên tục trước khi cảnh báo
  no_face_threshold_seconds: 3.0   # Giây mất mặt trước khi cảnh báo

head_pose:
  yaw_backward_threshold: 25.0     # Góc quay đầu ra sau (độ)
  yaw_side_threshold: 10.0         # Góc quay đầu sang trái/phải (độ)
  pitch_threshold: 10.0            # Góc cúi/ngửa mặt (độ)

yolo:
  model_path: "models/best.pt"     # Đường dẫn mô hình YOLO
  confidence_threshold: 0.7        # Ngưỡng tin cậy tối thiểu
  frame_skip: 5                    # Quét YOLO mỗi 5 frame để giảm tải CPU
```

---

## 📊 5. Bản Quyền & Giấy Phép
Dự án được phát triển phục vụ chương trình **Samsung Innovation Campus**.
Mã nguồn được tái cấu trúc sạch đẹp, sẵn sàng mở rộng và bảo trì lâu dài.
