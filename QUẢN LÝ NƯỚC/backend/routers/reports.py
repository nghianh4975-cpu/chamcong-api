from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from backend.database import get_db
from backend.models import User, Employee, AttendanceRecord, AttendanceStatus
from backend.auth import require_role
from backend.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/monthly")
async def monthly_report(
    month: str = Query(..., description="Format: YYYY-MM"),
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    service = ReportService(db)
    return await service.get_monthly_report(month, department)


@router.get("/department")
async def department_report(
    month: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    service = ReportService(db)
    return await service.get_department_report(month)


@router.get("/trend")
async def attendance_trend(
    months: int = Query(6, ge=1, le=12),
    employee_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    service = ReportService(db)
    return await service.get_trend(months, employee_id)


@router.get("/summary")
async def attendance_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    service = ReportService(db)
    return await service.get_summary(date_from, date_to)
