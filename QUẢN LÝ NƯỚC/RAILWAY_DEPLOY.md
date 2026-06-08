# ============================================
# Railway Deployment Guide
# ============================================
#
# MỤC TIÊU:
# - Deploy backend FastAPI lên Railway.app (miễn phí)
# - Chỉ cho phép truy cập từ IP quán (whitelist)
# - Link đăng nhập: https://xxx.railway.app
# - Máy POS + điện thoại tại quán truy cập được
# - Người ngoài không truy cập được
#

# ════════════════════════════════════════════
# BƯỚC 1: PUSH CODE LÊN GITHUB
# ════════════════════════════════════════════
#
# 1. Vào https://github.com → Đăng nhập
# 2. Click "New repository"
# 3. Đặt tên: chamcong-api
# 4. Public → Create repository
#
# 5. Trên máy của bạn, mở PowerShell/Terminal:
#

# cd vào thư mục project
cd "c:\Users\MSI PC\OneDrive\Máy tính\QUẢN LÝ NƯỚC"

# Khởi tạo git (nếu chưa có)
git init

# Thêm tất cả file
git add .

# Tạo commit
git commit -m "Initial commit - Cham Cong API"

# Thêm remote (THAY YOUR_USERNAME bằng username GitHub của bạn)
git remote add origin https://github.com/YOUR_USERNAME/chamcong-api.git

# Push lên GitHub
git branch -M main
git push -u origin main

# → Nhập username + token GitHub khi được hỏi
# → Tạo token: https://github.com/settings/tokens (chọn repo)


# ════════════════════════════════════════════
# BƯỚC 2: DEPLOY LÊN RAILWAY
# ════════════════════════════════════════════

# 1. Vào https://railway.app
# 2. Đăng nhập bằng GitHub
# 3. Click "New Project" → "Deploy from GitHub repo"
# 4. Chọn repo "chamcong-api"
# 5. Railway sẽ tự nhận diện Python → Deploy!

# Nếu Railway không nhận, tạo Procfile trong thư mục gốc:
# web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT


# ════════════════════════════════════════════
# BƯỚC 3: CẤU HÌNH BIẾN MÔI TRƯỜNG
# ════════════════════════════════════════════
#
# Trong Railway Dashboard → Project → chamcong-api → Variables
# Thêm các biến sau:

# ┌──────────────────┬─────────────────────────────────────────────┐
# │ Key               │ Value                                        │
# ├──────────────────┼─────────────────────────────────────────────┤
# │ DATABASE_URL      │ sqlite:///chamcong.db                        │
# │ PORT              │ 8000                                         │
# │ SECRET_KEY        │ (tự điền ngẫu nhiên, hoặc click Add Variable)│
# │ ALLOWED_IPS       │ (XEM BƯỚC 4)                               │
# │ WORK_START_TIME   │ 08:00                                        │
# │ WORK_END_TIME     │ 17:00                                        │
# │ LATE_TOLERANCE   │ 5                                            │
# └──────────────────┴─────────────────────────────────────────────┘

# Click "Add Variable" sau mỗi dòng
# Railway sẽ tự deploy lại


# ════════════════════════════════════════════
# BƯỚC 4: CẤU HÌNH IP WHITELIST
# ════════════════════════════════════════════
#
# Tìm IP WAN quán:
# → Trên máy tính tại quán, mở trình duyệt
# → Truy cập: https://whatismyip.com
# → Ghi lại IP (VD: 113.185.42.37)
#
# Điền vào ALLOWED_IPS trong Railway:
#   113.185.42.37
#
# → Máy từ IP khác sẽ bị chặn với thông báo:
#   "Truy cap bi chan. Chi may tinh tai quan moi duoc phep truy cap."


# ════════════════════════════════════════════
# BƯỚC 5: LẤY URL DEPLOY
# ════════════════════════════════════════════
#
# Sau khi deploy xong:
# 1. Trong Railway Dashboard → Project → chamcong-api
# 2. Click vào Deployment đang chạy
# 3. Copy URL (VD: https://chamcong-api.up.railway.app)
#
# Hoặc:
# Settings → Networking → Public Networking → Add Domain
# Đặt domain tùy chỉnh (VD: chamcong.yourdomain.com)


# ════════════════════════════════════════════
# BƯỚC 6: CẬP NHẬT FRONTEND
# ════════════════════════════════════════════
#
# Sửa file: frontend/js/app.js
# Tìm dòng:
const RENDER_API_URL = '';
# Đổi thành URL Railway của bạn:
const RENDER_API_URL = 'https://chamcong-api.up.railway.app';

# Commit và push:
git add frontend/js/app.js
git commit -m "Update API_BASE to Railway URL"
git push

# Railway sẽ tự deploy lại


# ════════════════════════════════════════════
# TEST
# ════════════════════════════════════════════

# ✅ Từ máy tại quán (IP trong whitelist):
# → Mở: https://chamcong-api.up.railway.app
# → Đăng nhập: admin / admin123

# ❌ Từ máy khác (IP không trong whitelist):
# → Nhận: 403 Forbidden
# → "Truy cap bi chan. Chi may tinh tai quan moi duoc phep truy cap."


# ════════════════════════════════════════════
# CẤU HÌNH POSTGRESQL TRÊN RAILWAY (TÙY CHỌN)
# ════════════════════════════════════════════
#
# Nếu muốn dùng PostgreSQL thay vì SQLite:
#
# 1. Railway Dashboard → New → Database → PostgreSQL
# 2. Tạo xong → Copy "Connection String"
#    (bắt đầu bằng postgresql://...)
# 3. Paste vào DATABASE_URL trong Variables:
#    postgresql://user:password@host:5432/dbname
#
# ⚠️ Lưu ý: Railway PostgreSQL free chỉ có 1GB storage


# ════════════════════════════════════════════
# MÁY POS SETUP
# ════════════════════════════════════════════
#
# Máy POS tại quán:
# 1. Mở Chrome/Edge
# 2. Truy cập: https://chamcong-api.up.railway.app/pos
# 3. Hiển thị mã QR cho nhân viên quét
#
# Hoặc nhân viên đăng nhập tài khoản riêng:
# https://chamcong-api.up.railway.app


# ════════════════════════════════════════════
# LƯU Ý QUAN TRỌNG
# ════════════════════════════════════════════
#
# 1. Railway free tier:
#    - 500 giờ/tháng (đủ cho 1 app chạy 24/7)
#    - 3 project free
#    - Cold start nhanh hơn Render (~10s)
#
# 2. IP WAN có thể THAY ĐỔI:
#    - Mỗi khi modem/router quán restart, IP WAN có thể đổi
#    - Cập nhật lại ALLOWED_IPS trong Railway
#    - Hoặc mua IP tĩnh từ nhà mạng
#
# 3. Database:
#    - SQLite: đơn giản, nhưng data có thể mất khi restart
#    - PostgreSQL: persistent, cần cấu hình thêm
#
# 4. Bảo mật:
#    - Đổi mật khẩu admin sau khi deploy
#    - Dùng SECRET_KEY ngẫu nhiên
