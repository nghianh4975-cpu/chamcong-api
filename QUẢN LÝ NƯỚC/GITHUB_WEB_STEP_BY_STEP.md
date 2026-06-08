# Hướng dẫn upload code lên GitHub qua Web (không cần Git CLI)

## TRƯỚC KHI BẮT ĐẦU: Tải file ZIP project

1. Mở File Explorer
2. Điều hướng tới: `C:\Users\MSI PC\OneDrive\Máy tính\QUẢN LÝ NƯỚC`
3. Nén toàn bộ thư mục (không nén chính thư mục đó) thành file ZIP
   - Chọn TẤT CẢ file và thư mục BÊN TRONG (backend, frontend, v.v.)
   - Click chuột phải → "Send to" → "Compressed (zipped) folder"
   - Đặt tên: `chamcong-api.zip`
4. Giải nén file ZIP đó ra một thư mục mới tên `chamcong-api-upload`

---

## BƯỚC 1: Tạo Repository mới trên GitHub

1. Mở trình duyệt → https://github.com → Đăng nhập
2. Click **New repository** (nút màu xanh lá)
3. Điền thông tin:
   - **Repository name:** `chamcong-api`
   - **Description:** `He thong cham cong thong minh`
   - **Public** hoặc **Private** (chọn Private để bảo mật)
   - ✅ **KHÔNG tick** "Add a README file"
   - ✅ **KHÔNG tick** "Add .gitignore"
   - ✅ **KHÔNG tick** "Choose a license"
4. Click **Create repository**

---

## BƯỚC 2: Upload files lên GitHub

Trang repository mới tạo sẽ hiện ra, làm theo:

1. Kéo thả TẤT CẢ file và thư mục từ thư mục `chamcong-api-upload` vào khung upload
   - Hoặc click **uploading an existing file** để chọn file

2. **LƯU Ý QUAN TRỌNG:** Cần upload đầy đủ các thư mục sau:
   ```
   backend/
   frontend/
   ```

3. Đợi upload xong (có thể mất 1-2 phút)

4. Click **Commit changes**

---

## BƯỚC 3: Kết nối Railway với GitHub

1. Mở **Railway Dashboard** → https://railway.app
2. Chọn project backend của bạn
3. Vào tab **Settings** → **GitHub**
4. Click **Connect GitHub repository**
5. Chọn repo `chamcong-api` vừa tạo
6. Railway sẽ tự động deploy từ GitHub

---

## BƯỚC 4: Cấu hình biến môi trường trên Railway

1. Trong Railway → chọn **project backend**
2. Vào tab **Variables**
3. **Sửa** `DATABASE_URL`:
   - Xóa giá trị cũ: `sqlite:///chamcong.db`
   - Paste connection string PostgreSQL từ ảnh bạn đã gửi
   - (Dạng: `postgresql://postgres:xxx@xxx.railway.internal:5432/railway`)
4. Click **Save Changes**

Railway sẽ tự Redeploy sau khi lưu.

---

## BƯỚC 5: Kiểm tra

1. Vào tab **Deployments** trong Railway
2. Đợi status chuyển sang **màu xanh** (thành công)
3. Click vào deployment → copy URL
4. Mở URL đó trong trình duyệt → đăng nhập `admin` / `admin123`

---

## NẾU GẶP LỖI

### Lỗi: "Repository not found"
→ Kiểm tra lại tên repo trong Railway Settings → GitHub

### Lỗi: "DATABASE_URL not set"
→ Quay lại BƯỚC 4, đảm bảo paste đúng connection string PostgreSQL

### Lỗi: Database trắng sau deploy
→ Đăng nhập bằng `admin` / `admin123` → tạo lại nhân viên và dữ liệu

---

## SAU KHI DEPLOY THÀNH CÔNG

Dữ liệu PostgreSQL sẽ **KHÔNG bị mất** khi redeploy nữa!
