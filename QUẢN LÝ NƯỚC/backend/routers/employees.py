from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
from backend.database import get_db
from backend.models import User, Employee, AttendanceRecord, SalaryRecord
from backend.schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeWithUser
)
from backend.auth import get_current_user, require_role, get_password_hash
from backend.utils.qr_generator import generate_qr_code
import io

router = APIRouter(prefix="/api/employees", tags=["Employees"])


def employee_to_response(emp: Employee) -> dict:
    return {
        "id": emp.id,
        "employee_code": emp.employee_code,
        "full_name": emp.full_name,
        "department": emp.department,
        "position": emp.position,
        "email": emp.email,
        "phone": emp.phone,
        "base_salary": emp.base_salary,
        "allowances": emp.allowances or {},
        "employee_type": emp.employee_type or "fulltime",
        "hourly_rate": emp.hourly_rate or 0,
        "is_active": emp.is_active,
        "created_at": emp.created_at,
    }


@router.get("", response_model=List[EmployeeResponse])
async def list_employees(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    department: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    query = db.query(Employee)
    if search:
        query = query.filter(
            or_(
                Employee.full_name.ilike(f"%{search}%"),
                Employee.employee_code.ilike(f"%{search}%"),
                Employee.email.ilike(f"%{search}%")
            )
        )
    if department:
        query = query.filter(Employee.department == department)
    if is_active is not None:
        query = query.filter(Employee.is_active == is_active)

    employees = query.order_by(Employee.created_at.desc()).offset(skip).limit(limit).all()
    return [employee_to_response(e) for e in employees]


@router.get("/departments", response_model=List[str])
async def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    depts = db.query(Employee.department).distinct().all()
    return [d[0] for d in depts if d[0]]


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    emp_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    existing = db.query(Employee).filter(
        or_(
            Employee.employee_code == emp_data.employee_code,
            Employee.email == emp_data.email if emp_data.email else False
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã nhân viên hoặc email đã tồn tại"
        )

    employee = Employee(
        employee_code=emp_data.employee_code,
        full_name=emp_data.full_name,
        department=emp_data.department,
        position=emp_data.position,
        email=emp_data.email,
        phone=emp_data.phone,
        pin_code=emp_data.pin_code,
        base_salary=emp_data.base_salary,
        allowances=emp_data.allowances,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)

    if emp_data.password:
        user = User(
            username=emp_data.employee_code,
            password_hash=get_password_hash(emp_data.password),
            role="employee",
            employee_id=employee.id
        )
        db.add(user)
        db.commit()

    return employee_to_response(employee)


@router.get("/{emp_id}", response_model=EmployeeResponse)
async def get_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value == "employee" and current_user.employee_id != emp_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền")
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhân viên")
    return employee_to_response(employee)


@router.put("/{emp_id}", response_model=EmployeeResponse)
async def update_employee(
    emp_id: int,
    emp_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhân viên")

    update_data = emp_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(employee, key, value)

    db.commit()
    db.refresh(employee)
    return employee_to_response(employee)


@router.delete("/{emp_id}")
async def delete_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay nhan vien")

    # Xoa cac bang ghi lien quan truoc
    db.query(AttendanceRecord).filter(AttendanceRecord.employee_id == emp_id).delete()
    db.query(SalaryRecord).filter(SalaryRecord.employee_id == emp_id).delete()
    db.delete(employee)
    db.commit()
    return {"success": True, "message": "Xoa nhan vien thanh cong"}


@router.get("/{emp_id}/qr-code")
async def get_employee_qr(
    emp_id: int,
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Khong tim thay nhan vien")

    qr_data = f"CHAMCONG:{employee.employee_code}"
    img_buffer = generate_qr_code(qr_data)

    return Response(
        content=img_buffer.getvalue(),
        media_type="image/png",
        headers={"Content-Disposition": f'inline; filename="qr_{employee.employee_code}.png"'}
    )
