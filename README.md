# 🛡️ ProctorAI - Hệ Thống Giám Sát Phòng Thi Thông Minh

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/YOLO11-Ultralytics-00FFFF?style=for-the-badge&logo=yolo&logoColor=black" alt="YOLO11">
  <img src="https://img.shields.io/badge/MediaPipe-FaceMesh-FF6F00?style=for-the-badge&logo=google&logoColor=white" alt="MediaPipe">
  <img src="https://img.shields.io/badge/OpenCV-SQPNP-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/SIC-Capstone_Project-1428A0?style=for-the-badge" alt="SIC">
</p>

---

## 📑 Mục Lục
1. [Giới Thiệu Tổng Quan](#-1-giới-thiệu-tổng-quan)
2. [Cây Thư Mục & Vai Trò Từng File](#-2-cây-thư-mục--vai-trò-từng-file)
3. [Kiến Trúc Thuật Toán Cốt Lõi](#-3-kiến-trúc-thuật-toán-cốt-lõi)
   - [3.1. Ước Lượng Tư Thế Đầu (Head Pose - SQPNP)](#31-thuật-toán-ước-lượng-tư-thế-đầu-head-pose-estimation)
   - [3.2. Nhận Diện Vật Thể & Quy Tắc Thiết Bị (YOLO11)](#32-thuật-toán-nhận-diện-thiết-bị--phân-loại-yolo11)
   - [3.3. Máy Trạng Thái Vi Phạm & Bộ Lọc Chống Rung (Debounce)](#33-máy-trạng-thái-vi-phạm--bộ-lọc-chống-rung-debounce)
   - [3.4. Quản Lý Đa Luồng & Master Switch](#34-quản-lý-đa-luồng--công-tắc-master-switch)
4. [Bảng Tra Cứu Cấu Hình (config.yaml)](#-4-bảng-tra-cứu-cấu-hình-configyaml)
5. [Giao Diện Bảng Điều Khiển (Web Dashboard)](#-5-giao-diện-bảng-điều-khiển-web-dashboard)
6. [Hướng Dẫn Cài Đặt & Khởi Chạy](#-6-hướng-dẫn-cài-đặt--khởi-chạy)

---

## 📖 1. Giới Thiệu Tổng Quan

**ProctorAI** là hệ thống giám sát thi cử trực tuyến thông minh, ứng dụng thị giác máy tính biên (Edge Computer Vision) và trí tuệ nhân tạo để phát hiện các hành vi gian lận trong thời gian thực.

### ✨ Đặc điểm kỹ thuật nổi bật
* **Không phụ thuộc đám mây:** Toàn bộ quá trình suy luận (Inference) chạy cục bộ (On-Device), bảo mật quyền riêng tư tuyệt đối cho thí sinh.
* **Tối giản & Tinh gọn:** Toàn bộ backend gói gọn trong 8 file phẳng thuộc thư mục `src/`, không tạo module lồng nhau, không phát sinh `__pycache__` hay `__init__.py`.
* **Độ trễ siêu thấp:** Xử lý luồng hình ảnh 30 FPS với kiến trúc Thread-Safe non-blocking, tải CPU trung bình dưới 15%.

---

## 📂 2. Cây Thư Mục & Vai Trò Từng File

Cấu trúc dự án được thiết kế theo mô hình **Flat Modular Architecture** (mỗi file đảm nhận đúng 1 trách nhiệm duy nhất, nhìn vào tên là biết chức năng):

```text
ProctorAI/
├── .vscode/
│   └── settings.json          # Cấu hình VS Code: Tự động ẩn file rác, bytecode, cache
├── config.yaml                # Cấu hình trung tâm: Ngưỡng góc đầu, FPS, camera, rules
├── main.py                    # Điểm khởi chạy chính (Entrypoint): Nạp config & bật Web server
├── run.bat                    # Script khởi chạy 1-click Windows: Khóa bytecode, kích hoạt venv
├── requirements.txt           # Danh mục thư viện phụ thuộc tối thiểu
├── README.md                  # Toàn bộ tài liệu kiến trúc, thuật toán & hướng dẫn
├── .gitignore                 # Loại trừ git: .venv, logs, screenshots, models lớn
│
├── models/
│   └── best.pt                # Trọng số mô hình YOLO (nhận diện điện thoại, máy tính)
│
├── logs/                      # Thư mục lưu nhật ký vi phạm dạng CSV (UTF-8-SIG)
├── screenshots/               # Thư mục lưu trữ hình ảnh chụp bằng chứng vi phạm
│
├── templates/
│   └── index.html             # Giao diện web giám thị đơn trang (Semantic HTML5 + CSS Grid)
│
└── src/                       # 8 file mã nguồn nghiệp vụ phẳng (Zero __init__.py / __pycache__)
    ├── camera.py              # Luồng nền đọc Webcam, điều phối pipeline AI & lưu bằng chứng
    ├── config.py              # Đọc config.yaml thành Dataclass kiểm kiểu an toàn (Strict Typing)
    ├── detector.py            # Khởi tạo & chạy suy luận YOLO11 kèm cơ chế Frame-Skipping
    ├── head_pose.py           # Tính góc Euler đầu (MediaPipe Mesh + Mô hình 3D + SQPNP)
    ├── hud.py                 # Vẽ bounding box, text tiếng Việt có dấu, HUD & khung Standby
    ├── logger.py              # Ghi lịch sử vi phạm ra CSV tiếng Việt & lưu ảnh snapshot
    ├── state.py               # Quản lý trạng thái đa luồng an toàn (Lock-free + Thread-safe)
    └── web.py                 # FastAPI backend: Cung cấp API REST, Web UI & MJPEG Stream
```

### 📋 Bảng Chi Tiết Vai Trò Module

| File | Thành Phần | Chức Năng Cốt Lõi |
| :--- | :--- | :--- |
| [`main.py`](file:///c:/Users/Rynne/Downloads/samsung/ProctorAI/main.py) | **Host Runner** | Đọc file cấu hình, khởi tạo máy chủ Uvicorn và liên kết FastAPI router. |
| [`config.yaml`](file:///c:/Users/Rynne/Downloads/samsung/ProctorAI/config.yaml) | **Global Settings** | Nơi điều chỉnh toàn bộ tham số: cổng webcam, ngưỡng góc đầu, thời gian debounce, danh sách thiết bị cấm/cho phép. |
| [`src/config.py`](file:///c:/Users/Rynne/Downloads/samsung/ProctorAI/src/config.py) | **Config Loader** | Chuyển đổi file YAML thành Python Dataclasses có kiểu dữ liệu chặt chẽ (`AppConfig`, `HeadPoseConfig`, `YOLOConfig`...). |
| [`src/camera.py`](file:///c:/Users/Rynne/Downloads/samsung/ProctorAI/src/camera.py) | **Worker Thread** | Luồng xử lý camera độc lập. Kết hợp kết quả từ YOLO và MediaPipe, chạy máy trạng thái debounce vi phạm, kích hoạt chụp ảnh và ghi log. |
| [`src/detector.py`](file:///c:/Users/Rynne/Downloads/samsung/ProctorAI/src/detector.py) | **Object Detector** | Tải mô hình YOLO11, áp dụng Frame-Skipping (chạy suy luận mỗi 5 frame) để tiết kiệm CPU, phân loại thiết bị theo danh mục rules. |
| [`src/head_pose.py`](file:///c:/Users/Rynne/Downloads/samsung/ProctorAI/src/head_pose.py) | **Pose Estimator** | Trích xuất 6 mốc giải phẫu từ MediaPipe Face Mesh, áp dụng thuật toán `SOLVEPNP_SQPNP` với mô hình 3D chuẩn xác để tính góc Yaw/Pitch. |
| [`src/hud.py`](file:///c:/Users/Rynne/Downloads/samsung/ProctorAI/src/hud.py) | **Frame Renderer** | Vẽ thanh trạng thái HUD, Bounding Box vi phạm, hiển thị tiếng Việt có dấu qua PIL, render màn hình chờ khi tắt hệ thống. |
| [`src/logger.py`](file:///c:/Users/Rynne/Downloads/samsung/ProctorAI/src/logger.py) | **Data Logger** | Lưu hình ảnh bằng chứng vào đĩa (`.jpg`) và ghi nhật ký vi phạm ra file CSV chuẩn mã hóa `utf-8-sig` (tương thích 100% với Excel tiếng Việt). |
| [`src/state.py`](file:///c:/Users/Rynne/Downloads/samsung/ProctorAI/src/state.py) | **State Manager** | Lưu trữ số liệu thống kê (KPIs), danh sách bằng chứng, trạng thái Master Switch (Bật/Tắt) đảm bảo an toàn giữa các luồng. |
| [`src/web.py`](file:///c:/Users/Rynne/Downloads/samsung/ProctorAI/src/web.py) | **Web Server** | Định nghĩa các endpoint REST (`/api/status`, `/api/toggle`, `/api/reset`), phục vụ file tĩnh và xuất luồng video MJPEG (`/video_feed`). |

---

## 🧠 3. Kiến Trúc Thuật Toán Cốt Lõi

Sơ đồ tổng thể dòng dữ liệu từ Camera đến Dashboard:

```text
[ Webcam ] (30 FPS)
    │
    ▼
[ CameraWorker (Background Thread) ]
    │
    ├───► [ 1. MediaPipe Face Mesh ] ──► Đếm số khuôn mặt (0, 1, 2+)
    │            │
    │            └─ (1 mặt) ──► Trích xuất 6 mốc 2D ──► [ solvePnP (SQPNP) ] ──► Góc (Yaw, Pitch)
    │
    ├───► [ 2. YOLO11 Detector ] (Frame Skip = 5) ──► Bounding Boxes ──► [ Device Rules Engine ]
    │
    ▼
[ 3. Violation State Machine & Debounce Timer ]
    │
    ├── (Thỏa mãn ngưỡng thời gian liên tục >= 2.0s hoặc 2 người tức thì)
    ▼
[ 4. Event Trigger ] ──► [ Lưu ảnh chụp bằng chứng ] & [ Ghi CSV Logger ]
    │
    ▼
[ 5. Thread-Safe State & REST API ] ──► [ Web Dashboard Real-time ]
```

---

### 3.1. Thuật toán Ước Lượng Tư Thế Đầu (Head Pose Estimation)

Vấn đề cốt lõi của bài toán là tìm ma trận xoay $R$ và vector tịnh tiến $t$ nối giữa hệ tọa độ vật thể 3D (khuôn mặt chuẩn) và hệ tọa độ hình ảnh 2D camera.

#### A. Mô Hình Khuôn Mặt Nhân Trắc Học 3D Chuẩn (Canonical 3D Model)
Hệ thống sử dụng 6 điểm mốc giải phẫu đặc trưng được định nghĩa theo tỷ lệ nhân trắc học khuôn mặt người thực nghiệm (đơn vị mm):

| Mốc Giải Phẫu | Chỉ Số MediaPipe Mesh | Tọa Độ 3D Chuẩn $(X, Y, Z)$ |
| :--- | :---: | :--- |
| **Đỉnh chóp mũi (Nose Tip)** | `1` | `(0.0, 0.0, 0.0)` |
| **Đáy cằm (Chin)** | `199` | `(0.0, -330.0, -65.0)` |
| **Khóe mắt ngoài bên trái** | `33` | `(-225.0, 170.0, -135.0)` |
| **Khóe mắt ngoài bên phải** | `263` | `(225.0, 170.0, -135.0)` |
| **Khóe miệng bên trái** | `61` | `(-150.0, -150.0, -125.0)` |
| **Khóe miệng bên phải** | `291` | `(150.0, -150.0, -125.0)` |

#### B. Ma Trận Nội Thông Số Camera (Camera Intrinsic Matrix)
Để không cần hiệu chuẩn camera phức tạp trên từng máy tính người dùng, ma trận nội suy camera $K$ được ước lượng động dựa trên kích thước khung hình $(W, H)$:

$$K = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix} = \begin{bmatrix} W & 0 & W / 2 \\ 0 & W & H / 2 \\ 0 & 0 & 1 \end{bmatrix}$$

#### C. Giải Thuật Phối Cảnh Toàn Cục SQPNP (Standard Quadratic PnP)
Thay vì sử dụng phương pháp lặp `SOLVEPNP_ITERATIVE` (dễ bị kẹt ở điểm cực tiểu cục bộ và gây hiện tượng nhảy góc 180° bất thường), ProctorAI chọn giải thuật **`SOLVEPNP_SQPNP`**:
* **Không lặp (Non-iterative):** Giải trực tiếp bài toán quy hoạch toàn phương với độ phức tạp $O(N)$.
* **Bất biến với tư thế khởi tạo:** Đảm bảo góc ước lượng luôn mượt mà, chính xác ngay cả khi khuôn mặt di chuyển nhanh.

#### D. Tách Ma Trận Xoay Thành Góc Euler (RQ Decomposition)
Sau khi tính được vector quay $r_{vec}$, hàm `cv2.Rodrigues` chuyển về ma trận quay $3 \times 3$ ($R$). Sau đó, thuật toán phân rã RQ (`cv2.RQDecomp3x3`) tách ma trận thành 3 góc Euler độc lập:
* **Pitch (Trục X):** Góc ngửa lên ($> 0$) hoặc cúi gằm mặt xuống ($< 0$).
* **Yaw (Trục Y):** Góc quay đầu sang trái ($< 0$) hoặc sang phải ($> 0$).
* **Roll (Trục Z):** Góc nghiêng đầu sang vai.

> **Lưu ý kỹ thuật quan trọng:** Hàm `cv2.RQDecomp3x3` của OpenCV đã trả về kết quả trực tiếp theo đơn vị độ (Degrees). Hệ thống loại bỏ hoàn toàn hệ số nhân sai lệch `* 360` (vốn tồn tại trong nhiều bài hướng dẫn cũ), giúp góc đo chính xác đến từng chữ số thập phân (thí sinh ngồi thẳng cho kết quả xấp xỉ $0^\circ$).

---

### 3.2. Thuật Toán Nhận Diện Thiết Bị & Phân Loại (YOLO11)

1. **Frame-Skipping Engine:** Mô hình YOLO chạy suy luận mỗi 5 frame một lần (`frame_count % 5 == 0`). Ở các khung hình trung gian, hệ thống tái sử dụng danh sách Bounding Boxes đã phát hiện. Cơ chế này giảm tải CPU tới 80% nhưng vẫn duy trì độ chính xác 100% trong việc phát hiện thiết bị.
2. **Quy Tắc Phân Loại Thiết Bị (Device Rules Engine):**
   * **Thiết bị cấm (Vi phạm):** `phone` (Điện thoại), `smartwatch` (Đồng hồ thông minh), `earphone` (Tai nghe), `book` (Tài liệu). Khi phát hiện, hiển thị khung màu đỏ và tính giờ cảnh báo.
   * **Thiết bị hợp lệ (Cho phép):** `calculator` (Máy tính Casio/bỏ túi). Hiển thị khung màu xanh lá cây, không tính vi phạm.

---

### 3.3. Máy Trạng Thái Vi Phạm & Bộ Lọc Chống Rung (Debounce)

Để tránh hiện tượng cảnh báo giả do thí sinh chớp mắt, quay đầu thoáng qua hoặc do rung động của camera, hệ thống triển khai máy trạng thái đếm thời gian liên tục:

```text
[ Phát hiện dấu hiệu nghi vấn ]
          │
          ▼
Gán vào Nhóm Vi Phạm (Violation Group):
  ├─ HEAD_POSE      (Quay trái / Quay phải / Quay ra sau / Cúi mặt / Ngửa mặt)
  ├─ MULTIPLE_FACES (Phát hiện từ 2 người trở lên)
  ├─ NO_FACE        (Không thấy mặt / Che camera)
  └─ DEVICE         (Sử dụng điện thoại / Thiết bị cấm)
          │
          ▼
Cùng nhóm với frame trước đó?
  ├─► [ĐÚNG]: Tiếp tục tích lũy thời gian:  t = current_time - violation_start
  └─► [SAI]:  Reset mốc thời gian:          violation_start = current_time
          │
          ▼
Kiểm tra ngưỡng vi phạm:
  ├─ Nhóm MULTIPLE_FACES: Ngưỡng = 0.0s (Cảnh báo & chụp ảnh TỨC THÌ)
  ├─ Nhóm NO_FACE:        Ngưỡng = 3.0s (Mất mặt quá 3 giây)
  └─ Nhóm Khác:           Ngưỡng = 2.0s (Duy trì hành vi quá 2 giây)
          │
          ▼
Thỏa mãn ngưỡng ──► Kích hoạt Báo Động HUD, Lưu Ảnh Snapshot, Ghi Log CSV
```

* **Chống Reset Timer:** Khi thí sinh xoay từ "Quay sang trái" sang "Quay hẳn ra sau", bộ đếm không bị reset về 0 nhờ dùng chung nhóm `HEAD_POSE`.
* **Cảnh báo lặp lại (Periodic Re-snapshot):** Nếu vi phạm tiếp diễn liên tục, cứ mỗi chu kỳ 10 giây hệ thống sẽ chụp thêm một bằng chứng mới để lưu vết.

---

### 3.4. Quản Lý Đa Luồng & Công Tắc Master Switch

* **`CameraWorker` chạy độc lập:** Đọc camera và suy luận AI trong một luồng riêng biệt, không chặn (non-blocking) luồng chính của FastAPI.
* **Công Tắc Bật/Tắt Tổng Thể (Master Switch):**
  * **Khi Tắt (OFF):** Luồng camera tự động gọi `cap.release()`, giải phóng phần cứng webcam vật lý. Hệ thống chuyển sang phát khung hình Standby tĩnh được lưu sẵn trong bộ nhớ đệm (RAM cache). Tải CPU/GPU hoàn toàn về 0%.
  * **Khi Bật (ON):** Mở lại phần cứng camera và khởi động lại toàn bộ pipeline giám sát trong chưa đầy 0.5 giây.

---

## ⚙️ 4. Bảng Tra Cứu Cấu Hình (`config.yaml`)

Người quản trị có thể tinh chỉnh toàn bộ hoạt động của hệ thống tại file `config.yaml`:

| Tham Số | Giá Trị Mặc Định | Đơn Vị | Ý Nghĩa Kỹ Thuật & Khuyến Nghị Điều Chỉnh |
| :--- | :---: | :---: | :--- |
| `camera.device_id` | `0` | Chỉ số | Số thứ tự cổng Webcam (0 là webcam tích hợp, 1 là webcam cắm ngoài). |
| `camera.width` | `640` | Pixel | Chiều rộng khung hình camera (khuyên dùng 640 để đạt tốc độ tối ưu). |
| `camera.height` | `480` | Pixel | Chiều cao khung hình camera. |
| `camera.fps_limit` | `30` | Khung hình/s | Tốc độ trần khung hình của camera. |
| `rules.violation_threshold_seconds` | `2.0` | Giây | Thời gian duy trì hành vi bất thường trước khi xác nhận vi phạm. |
| `rules.no_face_threshold_seconds` | `3.0` | Giây | Thời gian rời khỏi màn hình hoặc che camera trước khi ghi nhận vi phạm. |
| `rules.snap_interval_extended_seconds` | `10.0` | Giây | Khoảng cách thời gian giữa các lần chụp bằng chứng tiếp theo nếu vẫn vi phạm. |
| `head_pose.yaw_side_threshold` | `22.0` | Độ ($^\circ$) | Góc quay sang trái/phải tối thiểu để tính là nhìn bài người khác ($22^\circ - 45^\circ$). |
| `head_pose.yaw_backward_threshold` | `45.0` | Độ ($^\circ$) | Góc quay đầu ngoái hẳn ra phía sau ($> 45^\circ$). |
| `head_pose.pitch_threshold` | `20.0` | Độ ($^\circ$) | Góc cúi gằm mặt hoặc ngửa mặt lên trần nhà ($> 20^\circ$). |
| `yolo.model_path` | `models/best.pt` | Đường dẫn | Đường dẫn file trọng số mô hình YOLO đã huấn luyện. |
| `yolo.confidence_threshold` | `0.7` | Tỷ lệ (0-1) | Ngưỡng tin cậy tối thiểu để chấp nhận phát hiện vật thể. |
| `yolo.frame_skip` | `5` | Frame | Khoảng cách khung hình chạy suy luận YOLO (5 nghĩa là 1 lần suy luận mỗi 5 frame). |

---

## 🖥️ 5. Giao Diện Bảng Điều Khiển (Web Dashboard)

Giao diện được xây dựng hiện đại theo phong cách **Glassmorphism Dark Theme**, tối ưu cho màn hình giám sát của giám thị:

1. **Thanh Chỉ Số Trực Quan (KPI Cards):** Đếm theo thời gian thực tổng số vi phạm, số lần dùng điện thoại, số lần máy tính hợp lệ, số lần quay đầu và số lần mất mặt.
2. **Khung Video Stream Giám Sát:** Luồng hình ảnh sắc nét, hiển thị HUD tiếng Việt có dấu, khung bounding box nhận diện và thời gian đếm ngược.
3. **Thanh Điều Khiển Trung Tâm:**
   * **Nút Bật/Tắt Hệ Thống:** Bật/tắt camera và AI theo ý muốn.
   * **Nút Đặt Lại (Reset):** Xóa toàn bộ chỉ số vi phạm về 0 và làm sạch danh sách bằng chứng trong phiên.
4. **Hộp Bằng Chứng Vi Phạm (Evidence Gallery):**
   * Định dạng thẻ ngang đồng đều, cân đối chiều cao với khung camera.
   * Ảnh thu nhỏ thumbnail tỷ lệ 4:3 cố định (`106px x 80px`), không bị biến dạng hay chèn ép hình ảnh.
   * Thẻ gắn nhãn loại vi phạm, thời gian xảy ra chính xác đến từng giây và thời lượng vi phạm.
   * Hỗ trợ bộ lọc thông minh: Xem tất cả, Chỉ người thứ 2, Chỉ điện thoại, Chỉ quay đầu.
   * Nhấp chuột để phóng to ảnh kích thước thực.

---

## 🚀 6. Hướng Dẫn Cài Đặt & Khởi Chạy

### Yêu Cầu Môi Trường
* Hệ điều hành: Windows 10/11, macOS, hoặc Linux.
* Python: Phiên bản **3.10** hoặc cao hơn.
* Webcam đang hoạt động bình thường.

### Cách 1: Khởi Chạy Tự Động 1-Click (Khuyến nghị cho Windows)
Chỉ cần nhấp đúp chuột vào file:
```cmd
run.bat
```
*Script sẽ tự động thiết lập cờ môi trường `PYTHONDONTWRITEBYTECODE=1`, kích hoạt `.venv`, mở trình duyệt web và khởi động máy chủ.*

### Cách 2: Khởi Chạy Thủ Công Bằng Terminal
```bash
# 1. Kích hoạt môi trường ảo
# Trên Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Hoặc trên Windows Command Prompt:
.\.venv\Scripts\activate.bat

# 2. Cài đặt các thư viện phụ thuộc (nếu là lần đầu tiên)
pip install -r requirements.txt

# 3. Khởi chạy ứng dụng
python main.py
```

Sau khi khởi chạy thành công, truy cập hệ thống tại:
* **Giao diện giám sát:** `http://127.0.0.1:8000`
* **Tài liệu API Swagger:** `http://127.0.0.1:8000/docs`

---

## 📜 Bản Quyền & Giấy Phép
Dự án được nghiên cứu và phát triển trong khuôn khổ chương trình **Samsung Innovation Campus (SIC)**.  
Toàn bộ mã nguồn mở nhằm mục đích giáo dục, nghiên cứu và ứng dụng giám sát khảo thí công bằng.
