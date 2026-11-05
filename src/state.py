import threading
from typing import Dict, List, Any


class ProctoringState:
    """Quản lý trạng thái đa luồng Thread-safe cho hệ thống giám sát thi."""

    def __init__(self):
        self._lock = threading.Lock()
        self.system_enabled: bool = True  # Master Switch
        self.stats: Dict[str, int] = {
            "total_violations": 0,
            "phone": 0,
            "calculator": 0,
            "head_pose": 0,
            "no_face": 0,
            "multiple_faces": 0,
            "other_devices": 0
        }
        self.snapshots_history: List[Dict[str, Any]] = []

    def toggle_system(self) -> bool:
        """Đổi trạng thái Master Switch Bật / Tắt."""
        with self._lock:
            self.system_enabled = not self.system_enabled
            return self.system_enabled

    def set_system_enabled(self, enabled: bool) -> bool:
        with self._lock:
            self.system_enabled = enabled
            return self.system_enabled

    def is_active(self) -> bool:
        with self._lock:
            return self.system_enabled

    def record_violation(self, violation_type: str, duration: float, file_name: str) -> None:
        """Ghi nhận thống kê vi phạm động và lưu vào lịch sử snapshot."""
        v_lower = violation_type.lower()
        
        if "người" in v_lower:
            category = "multiple_faces"
        elif "thoại" in v_lower or "phone" in v_lower:
            category = "phone"
        elif "máy tính" in v_lower or "calculator" in v_lower:
            category = "calculator"
        elif "mất mặt" in v_lower or "che camera" in v_lower or "face" in v_lower:
            category = "face"
        elif any(k in v_lower for k in ["tai nghe", "earphone", "đồng hồ", "watch", "tài liệu", "book"]):
            category = "other_devices"
        else:
            category = "pose"

        with self._lock:
            self.stats["total_violations"] += 1
            if category in self.stats:
                self.stats[category] += 1
            else:
                self.stats[category] = 1

            snapshot_item = {
                "id": len(self.snapshots_history) + 1,
                "timestamp": file_name.replace("violation_", "").replace(".jpg", ""),
                "type": violation_type,
                "category": category,
                "duration": "TỨC THỜI" if duration == 0.0 else f"{duration:.2f}s",
                "image_url": f"/screenshots/{file_name}"
            }
            self.snapshots_history.insert(0, snapshot_item)
            if len(self.snapshots_history) > 100:
                self.snapshots_history.pop()

    def get_snapshot_data(self) -> Dict[str, Any]:
        """Lấy dữ liệu an toàn phục vụ API trả về cho Frontend."""
        with self._lock:
            return {
                "system_enabled": self.system_enabled,
                "stats": dict(self.stats),
                "snapshots": list(self.snapshots_history)
            }

    def clear_session(self) -> None:
        """Đặt lại toàn bộ số liệu thống kê và danh sách bằng chứng về 0."""
        with self._lock:
            self.snapshots_history.clear()
            self.stats = {
                "total_violations": 0,
                "phone": 0,
                "calculator": 0,
                "head_pose": 0,
                "no_face": 0,
                "multiple_faces": 0,
                "other_devices": 0
            }


state_manager = ProctoringState()
