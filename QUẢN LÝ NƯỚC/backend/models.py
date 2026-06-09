from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float, Boolean, Text, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    employee = "employee"


class AttendanceStatus(str, enum.Enum):
    ON_TIME = "ON_TIME"
    LATE = "LATE"
    EARLY_LEAVE = "EARLY_LEAVE"
    ABSENT = "ABSENT"
    COMPLETE = "COMPLETE"


class SalaryStatus(str, enum.Enum):
    draft = "draft"
    confirmed = "confirmed"
    paid = "paid"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.employee)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    employee = relationship("Employee", back_populates="user")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(20), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)
    position = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20))
    pin_code = Column(String(6), nullable=False)
    photo_url = Column(String(255))
    base_salary = Column(Float, default=0)
    allowances = Column(JSON, default=dict)
    employee_type = Column(String(20), default="fulltime")  # fulltime | parttime
    hourly_rate = Column(Float, default=0)  # luong/gio cho part-time (VNĐ/giờ)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="employee", uselist=False)
    attendance_records = relationship("AttendanceRecord", back_populates="employee", cascade="all, delete-orphan")
    salary_records = relationship("SalaryRecord", back_populates="employee", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "employee_code": self.employee_code,
            "full_name": self.full_name,
            "department": self.department,
            "position": self.position,
            "email": self.email,
            "phone": self.phone,
            "base_salary": self.base_salary,
            "allowances": self.allowances or {},
            "employee_type": self.employee_type or "fulltime",
            "hourly_rate": self.hourly_rate or 0,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    shift = Column(String(20), default="default")  # ca làm việc: default | ca1 | ca2 | ca3
    check_in = Column(DateTime(timezone=True))
    check_out = Column(DateTime(timezone=True))
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.ON_TIME)
    device_ip = Column(String(45))
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    pass_time_amount = Column(Float, nullable=True)

    employee = relationship("Employee", back_populates="attendance_records")
    creator = relationship("User", foreign_keys=[created_by])


class SalaryRecord(Base):
    __tablename__ = "salary_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    month = Column(String(7), nullable=False)
    base_salary = Column(Float, default=0)
    allowances = Column(Float, default=0)
    working_days = Column(Float, default=0)
    actual_days = Column(Float, default=0)
    late_minutes = Column(Integer, default=0)
    late_deduction = Column(Float, default=0)
    absent_days = Column(Float, default=0)
    absent_deduction = Column(Float, default=0)
    admin_deduction = Column(Float, default=0)
    admin_deduction_reason = Column(Text, nullable=True)
    overtime_hours = Column(Float, default=0)
    overtime_pay = Column(Float, default=0)
    gross_salary = Column(Float, default=0)
    net_salary = Column(Float, default=0)
    status = Column(Enum(SalaryStatus), default=SalaryStatus.draft)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    employee = relationship("Employee", back_populates="salary_records")


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, index=True, nullable=False)
    value = Column(JSON)
    description = Column(String(255))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DailyPOSKey(Base):
    __tablename__ = "daily_pos_keys"

    id = Column(Integer, primary_key=True, index=True)
    qr_data = Column(String(64), unique=True, nullable=False)
    daily_token = Column(String(16), nullable=False)
    one_time_pin = Column(String(6), nullable=False)
    date = Column(Date, nullable=False, index=True)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
