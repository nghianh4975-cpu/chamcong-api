from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse, Response
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base
from backend.models import User
from backend.auth import get_password_hash
from backend.routers import auth, employees, attendance, salary, reports, settings
from backend.middleware.ip_whitelist import IPRestrictMiddleware, get_allowed_ips_from_env


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    # Migration: thêm cột pass_time_amount nếu chưa có
    from backend.database import engine as _engine
    from sqlalchemy import text
    with _engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE attendance_records ADD COLUMN pass_time_amount FLOAT"))
            conn.commit()
        except Exception:
            pass  # Cột đã tồn tại

    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            print("Da tao tai khoan admin: admin / admin123")
    finally:
        db.close()
    yield


app = FastAPI(
    title="Cham Cong Thong Minh",
    description="He thong quan ly cham cong va tinh luong",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IP Whitelist Middleware - chỉ cho phép IP quán
allowed_ips = get_allowed_ips_from_env()
if allowed_ips:
    app.add_middleware(IPRestrictMiddleware, allowed_ips=allowed_ips)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(salary.router)
app.include_router(reports.router)
app.include_router(settings.router)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
async def root():
    frontend_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(frontend_path):
        return RedirectResponse(url="/static/index.html")
    return JSONResponse({
        "message": "Cham Cong Thong Minh API",
        "version": "1.0.0",
        "docs": "/docs",
    })


@app.get("/pos", include_in_schema=False)
async def pos_page():
    pos_path = os.path.join(os.path.dirname(BASE_DIR), "frontend", "pos.html")
    if os.path.exists(pos_path):
        with open(pos_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/html")
    return JSONResponse({"error": "POS page not found"}, status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
