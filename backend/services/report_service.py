from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional, List
from datetime import date, datetime, timedelta
from backend.models import Employee, AttendanceRecord, AttendanceStatus


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    async def get_monthly_report(self, month: str, department: Optional[str] = None) -> dict:
        year, mon = map(int, month.split("-"))
        start_date = date(year, mon, 1)
        if mon == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, mon + 1, 1) - timedelta(days=1)

        emp_query = self.db.query(Employee).filter(Employee.is_active == True)
        if department:
            emp_query = emp_query.filter(Employee.department == department)
        employees = emp_query.all()

        att_query = self.db.query(AttendanceRecord).filter(
            AttendanceRecord.date >= start_date,
            AttendanceRecord.date <= end_date
        )
        records = att_query.all()

        emp_ids = [e.id for e in employees]
        total_employees = len(emp_ids)
        days_in_range = (end_date - start_date).days + 1

        total_present = sum(1 for r in records if r.check_in)
        total_absent = total_employees - total_present
        total_late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
        total_early_leave = sum(1 for r in records if r.status == AttendanceStatus.EARLY_LEAVE)

        on_time_rate = round(total_present / total_present * 100, 1) if total_present > 0 else 0
        total_late_minutes = sum(
            max(0, int((r.check_in - datetime.combine(r.date, datetime.min.time()).replace(hour=8)).total_seconds() / 60 - 5))
            for r in records if r.status == AttendanceStatus.LATE and r.check_in
        )

        data = []
        for emp in employees:
            emp_records = [r for r in records if r.employee_id == emp.id]
            present_days = sum(1 for r in emp_records if r.check_in)
            late_days = sum(1 for r in emp_records if r.status == AttendanceStatus.LATE)
            late_mins = sum(
                max(0, int((r.check_in - datetime.combine(r.date, datetime.min.time()).replace(hour=8)).total_seconds() / 60 - 5))
                for r in emp_records if r.status == AttendanceStatus.LATE and r.check_in
            )
            data.append({
                "employee_id": emp.id,
                "employee_code": emp.employee_code,
                "full_name": emp.full_name,
                "department": emp.department,
                "present_days": present_days,
                "absent_days": days_in_range - present_days,
                "late_days": late_days,
                "total_late_minutes": late_mins,
                "status": "Đi làm" if present_days > 0 else "Vắng",
            })

        return {
            "month": month,
            "total_employees": total_employees,
            "total_present": total_present,
            "total_absent": total_absent,
            "total_late": total_late,
            "total_early_leave": total_early_leave,
            "on_time_rate": on_time_rate,
            "total_late_minutes": total_late_minutes,
            "data": data,
        }

    async def get_department_report(self, month: str) -> List[dict]:
        year, mon = map(int, month.split("-"))
        start_date = date(year, mon, 1)
        if mon == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, mon + 1, 1) - timedelta(days=1)

        departments = self.db.query(Employee.department).distinct().all()
        results = []

        for (dept,) in departments:
            emps = self.db.query(Employee).filter(
                Employee.department == dept,
                Employee.is_active == True
            ).all()
            emp_ids = [e.id for e in emps]

            records = self.db.query(AttendanceRecord).filter(
                AttendanceRecord.employee_id.in_(emp_ids),
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date
            ).all()

            total_emp = len(emp_ids)
            total_attendance = len(records)
            total_present = sum(1 for r in records if r.check_in)
            total_late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
            attendance_rate = round(total_present / total_attendance * 100, 1) if total_attendance > 0 else 0
            on_time_rate = round((total_present - total_late) / total_present * 100, 1) if total_present > 0 else 0

            avg_late = sum(
                max(0, int((r.check_in - datetime.combine(r.date, datetime.min.time()).replace(hour=8)).total_seconds() / 60))
                for r in records if r.status == AttendanceStatus.LATE and r.check_in
            ) / max(1, total_late)

            results.append({
                "department": dept,
                "month": month,
                "total_employees": total_emp,
                "attendance_rate": attendance_rate,
                "on_time_rate": on_time_rate,
                "avg_late_minutes": round(avg_late, 1),
            })

        return results

    async def get_trend(self, months: int, employee_id: Optional[int] = None) -> dict:
        results = []
        today = date.today()

        for i in range(months - 1, -1, -1):
            m = (today.month - i - 1) % 12 + 1
            y = today.year - ((today.month - i - 1) // 12)
            month_str = f"{y}-{m:02d}"
            start = date(y, m, 1)
            if m == 12:
                end = date(y + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(y, m + 1, 1) - timedelta(days=1)

            query = self.db.query(AttendanceRecord).filter(
                AttendanceRecord.date >= start,
                AttendanceRecord.date <= end
            )
            if employee_id:
                query = query.filter(AttendanceRecord.employee_id == employee_id)

            records = query.all()
            total = len(records)
            present = sum(1 for r in records if r.check_in)
            late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
            rate = round(present / total * 100, 1) if total > 0 else 0
            results.append({
                "month": month_str,
                "total": total,
                "present": present,
                "late": late,
                "on_time_rate": rate,
            })

        return {"trend": results}

    async def get_summary(self, date_from: Optional[str], date_to: Optional[str]) -> dict:
        f_date = date.fromisoformat(date_from) if date_from else (date.today() - timedelta(days=30))
        t_date = date.fromisoformat(date_to) if date_to else date.today()

        total_employees = self.db.query(Employee).filter(Employee.is_active == True).count()
        records = self.db.query(AttendanceRecord).filter(
            AttendanceRecord.date >= f_date,
            AttendanceRecord.date <= t_date
        ).all()

        total = len(records)
        present = sum(1 for r in records if r.check_in)
        late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
        early = sum(1 for r in records if r.status == AttendanceStatus.EARLY_LEAVE)
        absent = total_employees - present

        return {
            "date_from": str(f_date),
            "date_to": str(t_date),
            "total_employees": total_employees,
            "total_records": total,
            "present": present,
            "late": late,
            "early_leave": early,
            "absent": absent,
            "on_time_rate": round(present / max(1, total) * 100, 1),
        }
