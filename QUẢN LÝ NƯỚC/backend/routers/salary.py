from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, date
from backend.database import get_db
from backend.models import User, Employee, AttendanceRecord, AttendanceStatus, SalaryRecord, SalaryStatus
from backend.schemas import SalaryRecordResponse, AdminDeductionRequest
from backend.auth import require_role, get_current_user
from backend.services.salary_service import SalaryService

router = APIRouter(prefix="/api/salary", tags=["Salary"])


@router.get("", response_model=List[SalaryRecordResponse])
async def list_salary(
    month: Optional[str] = Query(None),
    employee_id: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    query = db.query(SalaryRecord)
    if month:
        query = query.filter(SalaryRecord.month == month)
    if employee_id:
        query = query.filter(SalaryRecord.employee_id == employee_id)
    if department:
        query = query.join(Employee).filter(Employee.department == department)

    records = query.order_by(SalaryRecord.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for r in records:
        emp = db.query(Employee).filter(Employee.id == r.employee_id).first()
        result.append(salary_to_dict(r, emp))
    return result


@router.post("/calculate/{month}", response_model=List[SalaryRecordResponse])
async def calculate_salary(
    month: str,
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    service = SalaryService(db)
    records = await service.calculate_month_salary(month, department)
    return records


@router.get("/{salary_id}", response_model=SalaryRecordResponse)
async def get_salary(
    salary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.query(SalaryRecord).filter(SalaryRecord.id == salary_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bản ghi lương")

    if current_user.role.value == "employee" and current_user.employee_id != record.employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền xem")

    emp = db.query(Employee).filter(Employee.id == record.employee_id).first()
    return salary_to_dict(record, emp)


@router.put("/{salary_id}", response_model=SalaryRecordResponse)
async def update_salary(
    salary_id: int,
    status_update: str = Query(None),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    record = db.query(SalaryRecord).filter(SalaryRecord.id == salary_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bản ghi")

    if status_update:
        try:
            record.status = SalaryStatus(status_update)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trạng thái không hợp lệ")
    if notes is not None:
        record.notes = notes

    db.commit()
    db.refresh(record)

    emp = db.query(Employee).filter(Employee.id == record.employee_id).first()
    return salary_to_dict(record, emp)


@router.put("/{salary_id}/admin-deduction", response_model=SalaryRecordResponse)
async def set_admin_deduction(
    salary_id: int,
    deduction_request: AdminDeductionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    record = db.query(SalaryRecord).filter(SalaryRecord.id == salary_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bản ghi lương")

    record.admin_deduction = deduction_request.deduction_amount
    record.admin_deduction_reason = deduction_request.reason

    record.gross_salary = record.base_salary + record.allowances - record.admin_deduction + record.overtime_pay
    record.net_salary = max(0, record.gross_salary)

    db.commit()
    db.refresh(record)

    emp = db.query(Employee).filter(Employee.id == record.employee_id).first()
    return salary_to_dict(record, emp)


def salary_to_dict(r: SalaryRecord, emp: Optional[Employee]) -> dict:
    return {
        "id": r.id,
        "employee_id": r.employee_id,
        "month": r.month,
        "base_salary": r.base_salary,
        "allowances": r.allowances,
        "working_days": r.working_days,
        "actual_days": r.actual_days,
        "late_minutes": r.late_minutes,
        "late_deduction": 0,
        "absent_days": r.absent_days,
        "absent_deduction": 0,
        "admin_deduction": r.admin_deduction,
        "admin_deduction_reason": r.admin_deduction_reason,
        "overtime_hours": r.overtime_hours,
        "overtime_pay": r.overtime_pay,
        "gross_salary": r.gross_salary,
        "net_salary": r.net_salary,
        "status": r.status,
        "notes": r.notes,
        "employee": emp.to_dict() if emp else None,
    }
