from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models import User, Setting
from backend.schemas import SettingResponse, SettingUpdate
from backend.auth import require_role

router = APIRouter(prefix="/api/settings", tags=["Settings"])

DEFAULT_SETTINGS = {
    "work_start_time": {"value": "08:00", "description": "Giờ bắt đầu làm việc"},
    "work_end_time": {"value": "17:00", "description": "Giờ kết thúc làm việc"},
    "late_tolerance_minutes": {"value": 5, "description": "Thời gian cho phép đi muộn (phút)"},
    "working_days": {"value": [1, 2, 3, 4, 5], "description": "Ngày làm việc trong tuần (1=Thứ 2)"},
    "late_deduction_per_minute": {"value": 5000, "description": "Tiền trừ mỗi phút đi muộn"},
    "absent_deduction_per_day": {"value": 150000, "description": "Tiền trừ mỗi ngày vắng"},
    "overtime_rate_per_hour": {"value": 30000, "description": "Tiền làm thêm giờ mỗi giờ"},
}


@router.get("", response_model=List[SettingResponse])
async def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    for key, data in DEFAULT_SETTINGS.items():
        existing = db.query(Setting).filter(Setting.key == key).first()
        if not existing:
            s = Setting(key=key, value=data["value"], description=data["description"])
            db.add(s)
    db.commit()

    settings = db.query(Setting).all()
    return [
        {
            "id": s.id,
            "key": s.key,
            "value": s.value,
            "description": s.description,
        }
        for s in settings
    ]


@router.put("", response_model=List[SettingResponse])
async def update_settings(
    data: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            s = Setting(key=key, value=value)
            db.add(s)

    db.commit()
    settings = db.query(Setting).all()
    return [
        {
            "id": s.id,
            "key": s.key,
            "value": s.value,
            "description": s.description,
        }
        for s in settings
    ]


def get_setting_value(db: Session, key: str, default=None):
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        return setting.value
    if key in DEFAULT_SETTINGS:
        return DEFAULT_SETTINGS[key]["value"]
    return default
