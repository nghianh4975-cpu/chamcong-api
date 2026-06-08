from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"


class AttendanceStatus(str, Enum):
    ON_TIME = "ON_TIME"
    LATE = "LATE"
    EARLY_LEAVE = "EARLY_LEAVE"
    ABSENT = "ABSENT"
    COMPLETE = "COMPLETE"


class SalaryStatus(str, Enum):
    draft = "draft"
    confirmed = "confirmed"
    paid = "paid"


# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Optional[str] = None


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.employee
    employee_id: Optional[int] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: UserRole
    employee_id: Optional[int]
    is_active: bool
    created_at: datetime


# --- Employee ---
class EmployeeBase(BaseModel):
    employee_code: str
    full_name: str
    department: str
    position: str
    email: Optional[str] = None
    phone: Optional[str] = None
    base_salary: float = 0
    allowances: Dict[str, float] = Field(default_factory=dict)
    employee_type: str = "fulltime"
    hourly_rate: float = 0


class EmployeeCreate(EmployeeBase):
    pin_code: str = Field(min_length=4, max_length=6)
    password: Optional[str] = None


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    pin_code: Optional[str] = None
    base_salary: Optional[float] = None
    allowances: Optional[Dict[str, float]] = None
    employee_type: Optional[str] = None
    hourly_rate: Optional[float] = None
    is_active: Optional[bool] = None


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_code: str
    full_name: str
    department: str
    position: str
    email: Optional[str]
    phone: Optional[str]
    base_salary: float
    allowances: Dict[str, float]
    employee_type: str = "fulltime"
    hourly_rate: float = 0
    is_active: bool
    created_at: datetime


class EmployeeWithUser(EmployeeResponse):
    user: Optional[UserResponse] = None


# --- Attendance ---
class CheckInRequest(BaseModel):
    employee_code: Optional[str] = None
    pin_code: Optional[str] = None
    qr_data: Optional[str] = None


class PassTimeAmountRequest(BaseModel):
    amount: float = Field(gt=0, description="Số tiền nhập (VNĐ)")
    notes: Optional[str] = None


class CheckInResponse(BaseModel):
    success: bool
    message: str
    employee_name: Optional[str] = None
    time: Optional[datetime] = None
    status: Optional[str] = None


class AttendanceRecordCreate(BaseModel):
    employee_id: int
    date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: AttendanceStatus = AttendanceStatus.ON_TIME
    notes: Optional[str] = None


class AttendanceRecordUpdate(BaseModel):
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = None
    pass_time_amount: Optional[float] = None


class AttendanceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    date: date
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    status: AttendanceStatus
    device_ip: Optional[str]
    notes: Optional[str]
    created_at: datetime
    employee: Optional[EmployeeResponse] = None
    pass_time_amount: Optional[float] = None


# --- Salary ---
class SalaryRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    month: str
    base_salary: float
    allowances: float
    working_days: float
    actual_days: float
    late_minutes: int
    late_deduction: float
    absent_days: float
    absent_deduction: float
    admin_deduction: float
    admin_deduction_reason: Optional[str] = None
    overtime_hours: float
    overtime_pay: float
    gross_salary: float
    net_salary: float
    status: SalaryStatus
    notes: Optional[str]
    employee: Optional[EmployeeResponse] = None


class AdminDeductionRequest(BaseModel):
    deduction_amount: float = Field(ge=0, description="Số tiền trừ lương (VNĐ)")
    reason: Optional[str] = Field(None, description="Lý do trừ lương")


# --- Reports ---
class MonthlyReport(BaseModel):
    month: str
    total_employees: int
    total_present: int
    total_absent: int
    total_late: int
    total_early_leave: int
    on_time_rate: float
    total_late_minutes: int
    data: List[Dict[str, Any]]


class DepartmentReport(BaseModel):
    department: str
    month: str
    total_employees: int
    attendance_rate: float
    on_time_rate: float
    avg_late_minutes: float


# --- Settings ---
class SettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    value: Any
    description: Optional[str]


class SettingUpdate(BaseModel):
    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None
    late_tolerance_minutes: Optional[int] = None
    working_days: Optional[List[int]] = None
    late_deduction_per_minute: Optional[float] = None
    absent_deduction_per_day: Optional[float] = None
