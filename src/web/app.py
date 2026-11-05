import os
import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from src.config import get_config, BASE_DIR
from src.core.state import state_manager
from src.vision.camera_worker import CameraWorker

cfg = get_config()

# Khởi tạo FastAPI App
app = FastAPI(
    title=cfg.app.title,
    description="Hệ thống AI giám sát phòng thi thông minh chuẩn Samsung Innovation Campus",
    version="2.0.0"
)

# Thư mục tĩnh và template
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Mount Static Files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/screenshots", StaticFiles(directory=cfg.paths.screenshots_dir), name="screenshots")

# Khởi tạo Camera Worker toàn cục
camera_worker = CameraWorker()
camera_worker.start()


@app.get("/", response_class=HTMLResponse)
def index_page():
    """Phục vụ trang chủ Dashboard."""
    html_file = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>ProctorAI đang khởi động...</h1>")


def stream_generator():
    """Generator truyền luồng video MJPEG từ buffer của CameraWorker."""
    while True:
        frame_bytes = camera_worker.get_jpeg()
        if frame_bytes is not None:
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        time.sleep(0.03)


@app.get("/video_feed")
def video_feed():
    """Endpoint phát luồng MJPEG thời gian thực cho thẻ <img> trên giao diện."""
    return StreamingResponse(
        stream_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/api/status")
def get_system_status():
    """API cung cấp toàn bộ trạng thái Master Switch, 5 thẻ KPI và danh sách bằng chứng."""
    return JSONResponse(content=state_manager.get_snapshot_data())


@app.post("/api/toggle_system")
def toggle_system():
    """Nút Master Bật/Tắt duy nhất điều khiển toàn bộ hệ thống."""
    new_state = state_manager.toggle_system()
    return JSONResponse(content={
        "status": "success",
        "system_enabled": new_state,
        "message": "Hệ thống đang hoạt động" if new_state else "Hệ thống đã chuyển sang chế độ chờ"
    })


@app.post("/api/clear")
def clear_session_data():
    """Đặt lại dữ liệu thống kê và danh sách ảnh của phiên thi hiện tại."""
    state_manager.clear_session()
    return JSONResponse(content={
        "status": "success",
        "message": "Đã đặt lại dữ liệu phiên thi thành công"
    })


@app.get("/favicon.ico")
def favicon():
    """Tránh lỗi 404 trên console trình duyệt."""
    return Response(status_code=204)
