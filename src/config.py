import os
from dataclasses import dataclass, field
from typing import Dict, Any
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class AppConfig:
    title: str = "ProctorAI - Hệ Thống Giám Sát Phòng Thi Thông Minh"
    host: str = "127.0.0.1"
    port: int = 8000


@dataclass
class CameraConfig:
    device_id: int = 0
    width: int = 640
    height: int = 480
    fps_limit: int = 30


@dataclass
class RulesConfig:
    violation_threshold_seconds: float = 2.0
    no_face_threshold_seconds: float = 3.0
    snap_interval_extended_seconds: float = 10.0


@dataclass
class HeadPoseConfig:
    yaw_backward_threshold: float = 25.0
    yaw_side_threshold: float = 10.0
    pitch_threshold: float = 10.0


@dataclass
class YoloConfig:
    model_path: str = "models/best.pt"
    confidence_threshold: float = 0.7
    frame_skip: int = 5
    device_rules: Dict[str, Any] = field(default_factory=lambda: {
        "phone": {
            "label": "ĐIỆN THOẠI",
            "is_violation": True,
            "warning_text": "Sử dụng ĐIỆN THOẠI",
            "color": [0, 0, 255]
        },
        "calculator": {
            "label": "MÁY TÍNH CẦM TAY",
            "is_violation": False,
            "warning_text": "MÁY TÍNH (HỢP LỆ)",
            "color": [0, 255, 0]
        }
    })


@dataclass
class PathsConfig:
    screenshots_dir: str = "screenshots"
    logs_dir: str = "logs"
    font_path: str = "C:/Windows/Fonts/arialbd.ttf"


@dataclass
class SystemConfig:
    app: AppConfig = field(default_factory=AppConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    rules: RulesConfig = field(default_factory=RulesConfig)
    head_pose: HeadPoseConfig = field(default_factory=HeadPoseConfig)
    yolo: YoloConfig = field(default_factory=YoloConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)


_CONFIG_INSTANCE = None


def get_config(config_file: str = "config.yaml") -> SystemConfig:
    global _CONFIG_INSTANCE
    if _CONFIG_INSTANCE is not None:
        return _CONFIG_INSTANCE

    full_path = os.path.join(BASE_DIR, config_file)
    cfg = SystemConfig()

    if os.path.exists(full_path):
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            if "app" in data:
                cfg.app = AppConfig(**data["app"])
            if "camera" in data:
                cfg.camera = CameraConfig(**data["camera"])
            if "rules" in data:
                cfg.rules = RulesConfig(**data["rules"])
            if "head_pose" in data:
                cfg.head_pose = HeadPoseConfig(**data["head_pose"])
            if "yolo" in data:
                cfg.yolo = YoloConfig(**data["yolo"])
            if "paths" in data:
                cfg.paths = PathsConfig(**data["paths"])
        except Exception as e:
            print(f"⚠️ Không thể đọc {config_file}, sử dụng cấu hình mặc định: {e}")

    # Chuẩn hóa đường dẫn tương đối theo BASE_DIR
    if not os.path.isabs(cfg.yolo.model_path):
        cfg.yolo.model_path = os.path.join(BASE_DIR, cfg.yolo.model_path)
    if not os.path.isabs(cfg.paths.screenshots_dir):
        cfg.paths.screenshots_dir = os.path.join(BASE_DIR, cfg.paths.screenshots_dir)
    if not os.path.isabs(cfg.paths.logs_dir):
        cfg.paths.logs_dir = os.path.join(BASE_DIR, cfg.paths.logs_dir)

    os.makedirs(cfg.paths.screenshots_dir, exist_ok=True)
    os.makedirs(cfg.paths.logs_dir, exist_ok=True)

    _CONFIG_INSTANCE = cfg
    return _CONFIG_INSTANCE
