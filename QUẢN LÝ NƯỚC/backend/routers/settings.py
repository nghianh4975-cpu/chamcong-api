from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models import User, Setting
from backend.schemas import SettingResponse, SettingUpdate
from backend.auth import require_role
from backend.services.settings_service import DEFAULT_SETTINGS, load_settings, get_setting_value

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=List[SettingResponse])
async def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    settings = db.query(Setting).all()
    if not settings:
        load_settings(db)
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
    # Refresh cache so attendance.py picks up new settings immediately
    load_settings(db)

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
