# Cham Cong Thong Minh - He Thong Quan Ly Cham Cong

He thong quan ly cham cong va tinh luong danh cho doanh nghiep nho va vua tai Viet Nam.

## Tinh nang chinh

- **Cham cong**: Quet QR Code / Nhap Ma NV + PIN (ho tro dien thoai)
- **Quan ly nhan vien**: Them, sua, xoa, tim kiem nhan vien
- **Bang cham cong**: Loc theo ngay, phong ban, trang thai
- **Tinh luong tu dong**: Tinh luong theo ngay cong, tru di muon, tru vang, lam them
- **Bao cao**: Tong hop, theo phong ban, xu huong, xuat Excel
- **Phan quyen**: Admin / Quan ly / Nhan vien

## Cau truc du an

```
QUAN-LY-NUOC/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Cau hinh
│   ├── database.py          # Ket noi DB
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT authentication
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   └── utils/               # Utilities (QR, Excel)
├── frontend/
│   ├── index.html          # Single page app
│   ├── css/style.css        # Styles
│   └── js/app.js            # Client-side logic
├── SPEC.md                  # Thiet ke he thong
└── requirements.txt
```

## Cai dat

### 1. Cai dat Python

Can Python 3.11+.

```bash
pip install -r requirements.txt
pip install bcrypt>=4.0.0
```

### 2. Khoi dong server

```bash
cd QUAN-LY-NUOC
python backend/main.py
```

Server chay tai: http://localhost:8000

### 3. Truy cap ung dung

- **Admin Dashboard**: http://localhost:8000
  - Tai khoan: `admin`
  - Mat khau: `admin123`

- **Trang cham cong (Nhan vien)**: http://localhost:8000/#/attendance

## Cau hinh

Chinh sua `.env` (hoac `backend/config.py`):

| Bien | Mac dinh | Mo ta |
|------|---------|-------|
| `WORK_START_TIME` | 08:00 | Gio bat dau lam |
| `WORK_END_TIME` | 17:00 | Gio ket thuc lam |
| `LATE_TOLERANCE_MINUTES` | 5 | Thoi gian cho phep di muon |
| `DATABASE_URL` | SQLite | Co the doi sang PostgreSQL |

## Chuyen sang PostgreSQL

1. Tao database PostgreSQL:
```sql
CREATE DATABASE chamcong;
```

2. Doi DATABASE_URL trong config:
```
DATABASE_URL=postgresql://user:password@localhost:5432/chamcong
```

## API Documentation

Sau khi chay server, truy cap:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Huong dan su dung nhanh

### Nhan vien cham cong
1. Nhan vien truy cap trang cham cong
2. Nhap **Ma NV** (vi du: NV001) va **Ma PIN** (vi du: 1234)
3. Nhan **Cham cong vao** / **Cham cong ra**

### Admin them nhan vien
1. Dang nhap tai khoan admin
2. Vao **Nhan vien** > **Them nhan vien**
3. Dien thong tin va nhan **Luu**
4. In ma QR cua nhan vien de dan cho quet

### Tinh luong
1. Vao **Luong** > Chon thang
2. Nhan **Tinh luong** de tao bang luong
3. Nhan **Xuat Excel** de tai ve
