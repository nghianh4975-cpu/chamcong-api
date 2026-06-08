"""
Migration: Add admin_deduction fields to salary_records
Chạy: python -m backend.migrations.add_admin_deduction
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.database import engine


def run_migration():
    with engine.connect() as conn:
        # Check if columns exist
        result = conn.execute(text("PRAGMA table_info(salary_records)"))
        columns = [row[1] for row in result.fetchall()]

        if "admin_deduction" not in columns:
            conn.execute(text("ALTER TABLE salary_records ADD COLUMN admin_deduction FLOAT DEFAULT 0"))
            print("[OK] Added admin_deduction column")
        else:
            print("[SKIP] admin_deduction column already exists")

        if "admin_deduction_reason" not in columns:
            conn.execute(text("ALTER TABLE salary_records ADD COLUMN admin_deduction_reason TEXT"))
            print("[OK] Added admin_deduction_reason column")
        else:
            print("[SKIP] admin_deduction_reason column already exists")

    print("Migration completed!")


if __name__ == "__main__":
    run_migration()
