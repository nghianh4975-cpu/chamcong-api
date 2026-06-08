from sqlalchemy.orm import Session
from backend.models import Setting

DEFAULT_SETTINGS = {
    "work_start_time": {"value": "08:00", "description": "Giờ bắt đầu làm việc"},
    "work_end_time": {"value": "17:00", "description": "Giờ kết thúc làm việc"},
    "late_tolerance_minutes": {"value": 5, "description": "Thời gian cho phép đi muộn (phút)"},
    "working_days": {"value": [1, 2, 3, 4, 5], "description": "Ngày làm việc trong tuần (1=Thứ 2)"},
    "late_deduction_per_minute": {"value": 5000, "description": "Tiền trừ mỗi phút đi muộn"},
    "absent_deduction_per_day": {"value": 150000, "description": "Tiền trừ mỗi ngày vắng"},
    "overtime_rate_per_hour": {"value": 30000, "description": "Tiền làm thêm giờ mỗi giờ"},
}


def _build_cache(db: Session) -> dict:
    """Load all settings from DB into a dict (creates defaults if missing)."""
    cache = dict(DEFAULT_SETTINGS)
    for key, data in DEFAULT_SETTINGS.items():
        existing = db.query(Setting).filter(Setting.key == key).first()
        if existing:
            cache[key] = {"value": existing.value, "description": existing.description or data["description"]}
        else:
            s = Setting(key=key, value=data["value"], description=data["description"])
            db.add(s)
    db.commit()
    return cache


# Module-level cache — refreshed when settings are updated
_settings_cache: dict = {}


def load_settings(db: Session) -> dict:
    global _settings_cache
    _settings_cache = _build_cache(db)
    return _settings_cache


def get_setting_value(db: Session, key: str, default=None):
    if _settings_cache:
        entry = _settings_cache.get(key)
        if entry is not None:
            return entry["value"] if isinstance(entry, dict) else entry
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        return setting.value
    if key in DEFAULT_SETTINGS:
        return DEFAULT_SETTINGS[key]["value"]
    return default


def get_work_start_time(db: Session) -> str:
    return get_setting_value(db, "work_start_time", "08:00")


def get_work_end_time(db: Session) -> str:
    return get_setting_value(db, "work_end_time", "17:00")


def get_late_tolerance(db: Session) -> int:
    return get_setting_value(db, "late_tolerance_minutes", 5)
