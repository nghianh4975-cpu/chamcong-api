from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Response, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, date, timedelta, time, timezone
import secrets
import hashlib
from backend.database import get_db
from backend.models import User, Employee, AttendanceRecord, AttendanceStatus as AS, DailyPOSKey
from backend.schemas import (
    CheckInRequest, CheckInResponse, PassTimeAmountRequest,
    AttendanceRecordCreate, AttendanceRecordUpdate, AttendanceRecordResponse
)
from backend.auth import get_current_user, require_role, get_client_ip
from backend.config import settings
from backend.utils.qr_generator import generate_qr_code
from backend.services.settings_service import (
    get_work_start_time, get_work_end_time, get_late_tolerance,
    get_shifts, get_shift_by_id, get_default_shift
)

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


# ---------- helper ----------
VN_TZ = timezone(timedelta(hours=7))


def _get_or_create_daily_key(db: Session) -> DailyPOSKey:
    today = date.today()
    key = db.query(DailyPOSKey).filter(DailyPOSKey.date == today).first()
    if key:
        return key

    # Sinh token ngày + PIN 1 lần
    raw_token = secrets.token_hex(8)           # 16 ký tự hex
    raw_pin = secrets.randbelow(900000) + 100000  # 6 chữ số ngẫu nhiên
    pin_str = str(raw_pin)

    daily_token = hashlib.sha256(raw_token.encode()).hexdigest()[:16].upper()
    qr_data = f"POS:{today.isoformat()}:{daily_token}"

    key = DailyPOSKey(
        qr_data=qr_data,
        daily_token=raw_token,   # server giữ secret để verify
        one_time_pin=pin_str,
        date=today,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


def _verify_and_invalidate(db: Session, qr_data: str, employee_code: str, pin_code: str) -> Employee:
    today = date.today()
    key = db.query(DailyPOSKey).filter(
        DailyPOSKey.date == today,
        DailyPOSKey.qr_data == qr_data
    ).first()

    if not key:
        raise ValueError("Mã QR không hợp lệ hoặc đã hết hạn")

    # Verify: PIN + employee
    employee = db.query(Employee).filter(
        Employee.employee_code == employee_code,
        Employee.pin_code == pin_code
    ).first()

    if not employee:
        raise ValueError("Mã nhân viên hoặc mã PIN không đúng")

    # Check xem nhân viên này đã dùng mã này chưa
    if key.used:
        raise ValueError("Mã QR đã được sử dụng. Vui lòng liên hệ admin.")

    return employee, key


def parse_time(t_str: str) -> time:
    parts = t_str.split(":")
    h, m = int(parts[0]), int(parts[1])
    return time(h, m)


def _time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def determine_status(check_in: datetime, check_out: Optional[datetime], db: Session, shift_id: str = "default") -> AS:
    if shift_id == "default":
        work_start_str = get_work_start_time(db)
        work_end_str = get_work_end_time(db)
        tolerance = get_late_tolerance(db)
    else:
        shift = get_shift_by_id(db, shift_id)
        if shift:
            work_start_str = shift["start"]
            work_end_str = shift["end"]
            tolerance = get_late_tolerance(db)
        else:
            work_start_str = get_work_start_time(db)
            work_end_str = get_work_end_time(db)
            tolerance = get_late_tolerance(db)

    work_start = parse_time(work_start_str)
    work_end = parse_time(work_end_str)
    check_in_local = check_in.replace(tzinfo=None) if check_in.tzinfo else check_in
    start_dt = datetime.combine(check_in.date(), work_start)
    tolerance_dt = start_dt + timedelta(minutes=tolerance)

    if check_in_local > tolerance_dt:
        base_status = AS.LATE
    else:
        base_status = AS.ON_TIME

    if check_out:
        out_time = check_out.time()
        # Cross-midnight shift (e.g. Ca 3: 22:00 -> 06:00)
        start_min = _time_to_minutes(work_start)
        end_min = _time_to_minutes(work_end)
        out_min = _time_to_minutes(out_time)
        if start_min > end_min:
            # Shift crosses midnight
            if out_min < start_min and out_min >= end_min:
                base_status = AS.EARLY_LEAVE
        else:
            if out_min < end_min:
                base_status = AS.EARLY_LEAVE

    return base_status


# ---------- endpoints ----------

@router.get("/pos-qr")
async def get_pos_qr(db: Session = Depends(get_db)):
    key = _get_or_create_daily_key(db)
    img_buffer = generate_qr_code(key.qr_data)
    return Response(
        content=img_buffer.getvalue(),
        media_type="image/png",
        headers={"Content-Disposition": 'inline; filename="pos_qr.png"'}
    )


@router.get("/pos-key-info")
async def get_pos_key_info(db: Session = Depends(get_db)):
    """Trả về thông tin key hôm nay (không có PIN) để frontend tự refresh khi đổi ngày."""
    key = _get_or_create_daily_key(db)
    return {
        "date": key.date.isoformat(),
        "token": key.qr_data,
    }


@router.post("/pos-scan-reveal")
async def pos_scan_reveal(
    request: Request,
    data: CheckInRequest,
    db: Session = Depends(get_db)
):
    """
    Khi quét QR → frontend gọi endpoint này để:
    1. Xác nhận QR đúng máy hôm nay
    2. Trả về Mã NV + Mã PIN 1 lần cho nhân viên nhập
    3. Link đăng nhập
    PIN ở đây là PIN tạm của ngày hôm nay (one_time_pin), dùng thay thế pin_code cố định.
    """
    if not data.qr_data:
        raise HTTPException(status_code=400, detail="Thiếu mã QR")

    today = date.today()

    # Parse QR: POS:YYYY-MM-DD:TOKEN
    parts = data.qr_data.split(":")
    if len(parts) != 3 or parts[0] != "POS":
        raise HTTPException(status_code=400, detail="Mã QR không hợp lệ")

    qr_date = parts[1]
    qr_token = parts[2]

    # Verify token đúng ngày
    key = db.query(DailyPOSKey).filter(
        DailyPOSKey.date == today,
        DailyPOSKey.qr_data == data.qr_data
    ).first()

    if not key:
        raise HTTPException(status_code=400, detail="Mã QR không đúng ngày hoặc đã hết hạn")

    if key.used:
        raise HTTPException(status_code=400, detail="Mã QR đã được sử dụng")

    # Lấy request IP
    client_ip = get_client_ip(request)

    # Lấy shifts để frontend hiển thị
    shifts = get_shifts(db)

    return {
        "valid": True,
        "reveal": {
            "employee_code_prompt": "Nhập mã nhân viên của bạn",
            "pin_prompt": "Nhập mã PIN 1 lần bên dưới",
            "one_time_pin": key.one_time_pin,
            "login_url": f"https://{client_ip}:8443",
        },
        "shifts": shifts,
    }


@router.post("/check-in", response_model=CheckInResponse)
async def check_in(
    request: Request,
    data: CheckInRequest,
    db: Session = Depends(get_db)
):
    client_ip = get_client_ip(request)
    employee = None
    daily_key = None

    if data.qr_data:
        parts = data.qr_data.split(":")

        if len(parts) == 3 and parts[0] == "POS":
            today = date.today()
            daily_key = db.query(DailyPOSKey).filter(
                DailyPOSKey.date == today,
                DailyPOSKey.qr_data == data.qr_data
            ).first()

            if not daily_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mã QR POS không hợp lệ hoặc đã hết hạn ngày"
                )

            if not data.employee_code or not data.pin_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Thiếu mã nhân viên hoặc mã PIN"
                )

            employee = db.query(Employee).filter(
                Employee.employee_code == data.employee_code
            ).first()

            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Mã nhân viên không đúng"
                )

            if data.pin_code != daily_key.one_time_pin:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Mã nhân viên hoặc mã PIN không đúng"
                )

            # NOTE: KHÔNG đánh dấu used=True ở đây nữa
            # Mỗi nhân viên dùng PIN 1 lần riêng → key chỉ bị vô hiệu khi đã check-out

        elif len(parts) >= 2 and parts[0] == "CHAMCONG":
            employee = db.query(Employee).filter(
                Employee.employee_code == parts[1]
            ).first()

    # Fallback: nhập tay không QR
    if not employee and data.employee_code:
        employee = db.query(Employee).filter(
            Employee.employee_code == data.employee_code,
            Employee.pin_code == data.pin_code
        ).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mã nhân viên hoặc mã PIN không đúng"
        )

    today = date.today()
    now = datetime.now(VN_TZ)
    shift_id = data.shift or "default"

    # Full-time: 1 bản ghi/ngày. Part-time: nhiều bản ghi theo ca.
    emp_type = employee.employee_type or "fulltime"

    if emp_type == "fulltime":
        # Full-time: tìm bản ghi hôm nay (bất kể ca nào)
        existing = db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == today
        ).first()

        if existing and existing.check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bạn đã chấm công vào lúc {existing.check_in.strftime('%H:%M:%S')}. "
                       f"Hãy dùng chấm công ra."
            )

        if existing:
            existing.check_in = now
            existing.status = determine_status(now, existing.check_out, db, shift_id)
            record = existing
        else:
            record = AttendanceRecord(
                employee_id=employee.id,
                date=today,
                shift=shift_id,
                check_in=now,
                status=determine_status(now, None, db, shift_id),
                device_ip=client_ip
            )
            db.add(record)
    else:
        # Part-time: tìm bản ghi theo đúng ca hôm nay
        existing = db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == today,
            AttendanceRecord.shift == shift_id
        ).first()

        if existing and existing.check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ca {shift_id} đã chấm vào lúc {existing.check_in.strftime('%H:%M:%S')}. "
                       f"Hãy dùng chấm ra."
            )

        if existing:
            existing.check_in = now
            existing.status = determine_status(now, existing.check_out, db, shift_id)
            record = existing
        else:
            record = AttendanceRecord(
                employee_id=employee.id,
                date=today,
                shift=shift_id,
                check_in=now,
                status=determine_status(now, None, db, shift_id),
                device_ip=client_ip
            )
            db.add(record)

    db.commit()
    db.refresh(record)
    return CheckInResponse(
        success=True,
        message=f"Chấm công vào thành công",
        employee_name=employee.full_name,
        time=now,
        status=determine_status(now, None, db, shift_id).value
    )


@router.post("/check-out", response_model=CheckInResponse)
async def check_out(
    request: Request,
    data: CheckInRequest,
    db: Session = Depends(get_db)
):
    client_ip = get_client_ip(request)
    employee = None

    if data.qr_data:
        parts = data.qr_data.split(":")
        if len(parts) >= 2 and parts[0] == "CHAMCONG":
            employee = db.query(Employee).filter(
                Employee.employee_code == parts[1]
            ).first()

    if data.employee_code and not employee:
        employee = db.query(Employee).filter(
            Employee.employee_code == data.employee_code
        ).first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy nhân viên"
        )

    today = date.today()
    now = datetime.now(VN_TZ)
    shift_id = data.shift or "default"

    emp_type = employee.employee_type or "fulltime"

    if emp_type == "fulltime":
        record = db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == today
        ).first()
    else:
        # Part-time: tìm đúng ca
        record = db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.date == today,
            AttendanceRecord.shift == shift_id
        ).first()

    if not record or not record.check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn chưa chấm công vào hôm nay"
        )

    record.check_out = now
    record.status = determine_status(record.check_in, now, db, record.shift)
    record.device_ip = client_ip

    # Đánh dấu POS key đã dùng khi check-out xong (chỉ cho part-time)
    if data.qr_data and emp_type == "parttime":
        parts = data.qr_data.split(":")
        if len(parts) == 3 and parts[0] == "POS":
            daily_key = db.query(DailyPOSKey).filter(
                DailyPOSKey.date == today,
                DailyPOSKey.qr_data == data.qr_data
            ).first()
            if daily_key:
                daily_key.used = True

    db.commit()

    return CheckInResponse(
        success=True,
        message=f"Chấm công ra thành công",
        employee_name=employee.full_name,
        time=now,
        status=record.status.value
    )


@router.get("", response_model=List[AttendanceRecordResponse])
async def list_attendance(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    employee_id: Optional[int] = Query(None),
    department: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    query = db.query(AttendanceRecord)

    if date_from:
        query = query.filter(AttendanceRecord.date >= date_from)
    if date_to:
        query = query.filter(AttendanceRecord.date <= date_to)
    if employee_id:
        query = query.filter(AttendanceRecord.employee_id == employee_id)
    if status_filter:
        query = query.filter(AttendanceRecord.status == status_filter)

    if department:
        query = query.join(Employee).filter(Employee.department == department)

    records = query.order_by(AttendanceRecord.date.desc()).offset(skip).limit(limit).all()

    result = []
    for r in records:
        emp = db.query(Employee).filter(Employee.id == r.employee_id).first()
        result.append({
            "id": r.id,
            "employee_id": r.employee_id,
            "date": r.date,
            "shift": r.shift or "default",
            "check_in": r.check_in,
            "check_out": r.check_out,
            "status": r.status,
            "device_ip": r.device_ip,
            "notes": r.notes,
            "pass_time_amount": r.pass_time_amount,
            "created_at": r.created_at,
            "employee": employee_to_dict(emp) if emp else None
        })
    return result


@router.get("/my", response_model=List[dict])
async def my_attendance(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.employee_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tài khoản không liên kết nhân viên")

    query = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == current_user.employee_id
    )
    if date_from:
        query = query.filter(AttendanceRecord.date >= date_from)
    if date_to:
        query = query.filter(AttendanceRecord.date <= date_to)

    records = query.order_by(AttendanceRecord.date.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": r.id,
            "date": r.date,
            "shift": r.shift or "default",
            "check_in": r.check_in,
            "check_out": r.check_out,
            "status": r.status.value,
        }
        for r in records
    ]


@router.put("/{record_id}", response_model=dict)
async def update_attendance(
    record_id: int,
    data: AttendanceRecordUpdate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bản ghi")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)

    if record.check_in and record.check_out:
        record.status = determine_status(record.check_in, record.check_out, db, record.shift)
    elif record.check_in:
        record.status = determine_status(record.check_in, None, db, record.shift)

    record.created_by = current_user.id
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "employee_id": record.employee_id,
        "date": record.date,
        "check_in": record.check_in,
        "check_out": record.check_out,
        "status": record.status.value,
        "notes": record.notes,
    }


def employee_to_dict(emp: Employee) -> dict:
    if not emp:
        return None
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
        "is_active": emp.is_active,
        "created_at": emp.created_at,
    }


# ---------- admin endpoints ----------

@router.post("/admin/pos-reset")
async def admin_reset_pos_key(
    date_str: Optional[str] = Query(None, description="Ngày cần reset (YYYY-MM-DD), mặc định hôm nay"),
    action: str = Query("regenerate", description="regenerate = tạo mã mới, reopen = mở lại mã cũ"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    """
    Admin: Reset hoặc mở lại mã POS QR cho một ngày.
    - regenerate: xóa mã cũ, tạo mã mới cho ngày đó
    - reopen: đánh dấu used=False để mã cũ có thể dùng lại
    """
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    if action == "reopen":
        key = db.query(DailyPOSKey).filter(DailyPOSKey.date == target_date).first()
        if not key:
            raise HTTPException(status_code=404, detail="Không tìm thấy mã POS cho ngày này")
        key.used = False
        db.commit()
        return {"success": True, "action": "reopen", "date": target_date.isoformat(), "message": "Đã mở lại mã POS"}

    elif action == "regenerate":
        db.query(DailyPOSKey).filter(DailyPOSKey.date == target_date).delete()
        db.commit()
        key = _get_or_create_daily_key(db)
        return {
            "success": True,
            "action": "regenerate",
            "date": target_date.isoformat(),
            "qr_data": key.qr_data,
            "pin": key.one_time_pin,
            "message": "Đã tạo mã POS mới"
        }

    raise HTTPException(status_code=400, detail="action phải là 'regenerate' hoặc 'reopen'")


@router.post("/admin/attendance")
async def admin_create_attendance(
    record: AttendanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    """Admin: Tạo bản ghi chấm công thủ công cho nhân viên."""
    emp = db.query(Employee).filter(Employee.id == record.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")

    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == record.employee_id,
        AttendanceRecord.date == record.date
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Đã có bản ghi chấm công cho nhân viên này vào ngày {record.date}"
        )

    db_record = AttendanceRecord(
        employee_id=record.employee_id,
        date=record.date,
        check_in=record.check_in,
        check_out=record.check_out,
        status=record.status or AS.ON_TIME,
        notes=f"[Admin tạo] {record.notes or ''}",
        created_by=current_user.id
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return {"success": True, "id": db_record.id, "message": "Đã tạo bản ghi chấm công"}


@router.put("/admin/attendance/{record_id}")
async def admin_update_attendance(
    record_id: int,
    data: AttendanceRecordUpdate,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db)
):
    """Admin: Sửa giờ chấm công cho nhân viên."""
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        # Attach timezone to naive datetime inputs from admin
        if key in ("check_in", "check_out") and value and not hasattr(value, 'tzinfo'):
            value = value.replace(tzinfo=VN_TZ)
        setattr(record, key, value)

    if record.check_in and record.check_out:
        record.status = determine_status(record.check_in, record.check_out, db, record.shift)
    elif record.check_in:
        record.status = determine_status(record.check_in, None, db, record.shift)

    record.created_by = current_user.id
    db.commit()
    db.refresh(record)
    return {"success": True, "message": "Đã cập nhật bản ghi"}


# ---------- employee endpoints ----------

@router.post("/my/pass-time-amount")
async def submit_pass_time_amount(
    data: PassTimeAmountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Nhân viên: Nhập số tiền pass time cho ngày hôm nay."""
    if not current_user.employee_id:
        raise HTTPException(status_code=400, detail="Tài khoản không liên kết nhân viên")

    today = date.today()
    record = db.query(AttendanceRecord).filter(
        AttendanceRecord.employee_id == current_user.employee_id,
        AttendanceRecord.date == today
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Bạn chưa chấm công hôm nay")

    record.pass_time_amount = data.amount
    if data.notes:
        record.notes = (record.notes or "") + f" | Pass time: {data.amount:,.0f}đ - {data.notes}"
    db.commit()
    return {"success": True, "amount": data.amount, "message": "Đã ghi nhận số tiền part-time"}


@router.get("/admin/part-time")
async def admin_list_part_time(
    date: Optional[str] = Query(None, description="Ngay can xem (YYYY-MM-DD), mac dinh hom nay"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    """Admin: Xem & nhap so tien part-time theo ngay."""
    target_date = date.fromisoformat(date) if date else date.today()
    records = db.query(AttendanceRecord).options(
        joinedload(AttendanceRecord.employee)
    ).filter(
        AttendanceRecord.date == target_date,
        AttendanceRecord.employee.has(employee_type="parttime")
    ).all()
    return [{
        "id": r.id,
        "date": r.date.isoformat(),
        "shift": r.shift or "default",
        "pass_time_amount": r.pass_time_amount,
        "notes": r.notes,
        "employee": {
            "id": r.employee.id,
            "employee_code": r.employee.employee_code,
            "full_name": r.employee.full_name,
            "department": r.employee.department,
        } if r.employee else None
    } for r in records]


@router.put("/admin/part-time/{record_id}")
async def admin_update_part_time_amount(
    record_id: int,
    amount: float = Body(..., ge=0, description="So tien part-time (VNĐ)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager"))
):
    """Admin: Nhap so tien cho ban ghi part-time."""
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Khong tim thay ban ghi")
    record.pass_time_amount = amount
    db.commit()
    return {"success": True, "amount": amount}
