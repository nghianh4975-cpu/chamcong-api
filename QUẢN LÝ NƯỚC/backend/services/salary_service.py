from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime, date, timedelta
from backend.models import Employee, AttendanceRecord, AttendanceStatus, SalaryRecord, SalaryStatus, Setting
from backend.routers.settings import get_setting_value


class SalaryService:
    def __init__(self, db: Session):
        self.db = db

    def get_setting(self, key: str, default=None):
        return get_setting_value(self.db, key, default)

    async def calculate_month_salary(self, month: str, department: Optional[str] = None) -> List[dict]:
        year, mon = map(int, month.split("-"))
        start_date = date(year, mon, 1)
        if mon == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, mon + 1, 1) - timedelta(days=1)

        working_days = self.get_setting("working_days", [1, 2, 3, 4, 5])
        work_days_count = sum(1 for i in range(1, end_date.day + 1)
                               if date(year, mon, i).weekday() + 1 in working_days)

        query = self.db.query(Employee).filter(Employee.is_active == True)
        if department:
            query = query.filter(Employee.department == department)
        employees = query.all()

        records = []
        for emp in employees:
            attendance = self.db.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id == emp.id,
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date
            ).all()

            total_late_minutes = 0
            absent_days = 0
            actual_days = len(attendance)
            overtime_hours = 0.0

            for record in attendance:
                if record.status == AttendanceStatus.ABSENT:
                    absent_days += 1
                elif record.check_in:
                    work_start_str = self.get_setting("work_start_time", "08:00")
                    h, m = map(int, work_start_str.split(":"))
                    start_dt = datetime.combine(record.date, datetime.min.time()).replace(hour=h, minute=m)
                    late_diff = (record.check_in - start_dt).total_seconds() / 60
                    tolerance = self.get_setting("late_tolerance_minutes", 5)
                    if late_diff > tolerance > 0:
                        total_late_minutes += int(late_diff - tolerance)

                if record.check_out:
                    work_end_str = self.get_setting("work_end_time", "17:00")
                    h, m = map(int, work_end_str.split(":"))
                    end_dt = datetime.combine(record.date, datetime.min.time()).replace(hour=h, minute=m)
                    out_diff = (record.check_out - end_dt).total_seconds() / 3600
                    if out_diff > 0:
                        overtime_hours += out_diff

            emp_type = emp.employee_type or "fulltime"
            base_salary = emp.base_salary or 0
            hourly_rate = emp.hourly_rate or 0
            allowances = sum((emp.allowances or {}).values())
            total_hours = 0.0

            # --- FULL TIME: tinh luong theo ngay ---
            if emp_type == "fulltime":
                daily_rate = base_salary / work_days_count if work_days_count > 0 else 0
                late_deduction = (total_late_minutes / 60) * self.get_setting("late_deduction_per_minute", 5000) * 60 / 60
                absent_deduction = absent_days * daily_rate
                overtime_pay = overtime_hours * self.get_setting("overtime_rate_per_hour", 30000)
                gross = base_salary + allowances - late_deduction - absent_deduction + overtime_pay
                net = max(0, gross)
            # --- PART TIME: tinh = tong gio lam x luong/gio ---
            else:
                for r in attendance:
                    if r.check_in and r.check_out:
                        total_hours += (r.check_out - r.check_in).total_seconds() / 3600
                salary_from_hours = total_hours * hourly_rate
                gross = salary_from_hours
                net = salary_from_hours
                daily_rate = 0
                late_deduction = 0
                absent_deduction = 0
                overtime_pay = 0

            existing = self.db.query(SalaryRecord).filter(
                SalaryRecord.employee_id == emp.id,
                SalaryRecord.month == month
            ).first()

            if existing:
                existing.base_salary = base_salary
                existing.allowances = allowances
                existing.working_days = work_days_count
                existing.actual_days = actual_days
                existing.late_minutes = total_late_minutes
                existing.late_deduction = late_deduction
                existing.absent_days = absent_days
                existing.absent_deduction = absent_deduction
                existing.overtime_hours = overtime_hours
                existing.overtime_pay = overtime_pay
                existing.gross_salary = gross
                existing.net_salary = net
                record = existing
            else:
                record = SalaryRecord(
                    employee_id=emp.id,
                    month=month,
                    base_salary=base_salary,
                    allowances=allowances,
                    working_days=work_days_count,
                    actual_days=actual_days,
                    late_minutes=total_late_minutes,
                    late_deduction=late_deduction,
                    absent_days=absent_days,
                    absent_deduction=absent_deduction,
                    overtime_hours=overtime_hours,
                    overtime_pay=overtime_pay,
                    gross_salary=gross,
                    net_salary=net,
                )
                self.db.add(record)

            self.db.commit()
            self.db.refresh(record)

            emp_dict = {
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
            records.append({
                "id": record.id,
                "employee_id": record.employee_id,
                "month": record.month,
                "base_salary": record.base_salary,
                "allowances": record.allowances,
                "working_days": record.working_days,
                "actual_days": record.actual_days,
                "late_minutes": record.late_minutes,
                "late_deduction": record.late_deduction,
                "absent_days": record.absent_days,
                "absent_deduction": record.absent_deduction,
                "overtime_hours": record.overtime_hours,
                "overtime_pay": record.overtime_pay,
                "pass_time_total": total_hours,
                "gross_salary": record.gross_salary,
                "net_salary": record.net_salary,
                "status": record.status,
                "notes": record.notes,
                "employee": emp_dict,
            })

        return records
