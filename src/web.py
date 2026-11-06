import os
import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from src.config import get_config, BASE_DIR
from src.state import state_manager
from src.camera import CameraWorker

cfg = get_config()

app = FastAPI(title=cfg.app.title, version="2.0.0")

TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
app.mount("/screenshots", StaticFiles(directory=cfg.paths.screenshots_dir), name="screenshots")

camera_worker = CameraWorker()
camera_worker.start()


@app.get("/", response_class=HTMLResponse)
def index_page():
    html_file = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>ProctorAI đang khởi động...</h1>")


def stream_generator():
    try:
        while True:
            frame_bytes = camera_worker.get_jpeg()
            if frame_bytes is not None:
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            time.sleep(0.03)
    except (GeneratorExit, Exception):
        return


@app.on_event("shutdown")
def on_shutdown():
    camera_worker.stop()


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(stream_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/api/status")
def get_system_status():
    return JSONResponse(content=state_manager.get_snapshot_data())


@app.post("/api/toggle_system")
def toggle_system():
    new_state = state_manager.toggle_system()
    return JSONResponse(content={
        "status": "success",
        "system_enabled": new_state,
        "message": "Hệ thống đang hoạt động" if new_state else "Hệ thống đã chuyển sang chế độ chờ"
    })


@app.post("/api/clear")
def clear_session_data():
    state_manager.clear_session()
    return JSONResponse(content={"status": "success", "message": "Đã đặt lại dữ liệu phiên thi thành công"})


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)
