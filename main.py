import uvicorn
from src.config import get_config
from src.web.app import app

if __name__ == "__main__":
    cfg = get_config()
    print("=" * 60)
    print(f"🚀 {cfg.app.title}")
    print(f"📡 Truy cập Web Dashboard tại: http://{cfg.app.host}:{cfg.app.port}")
    print("=" * 60)
    uvicorn.run(app, host=cfg.app.host, port=cfg.app.port, log_level="info")
