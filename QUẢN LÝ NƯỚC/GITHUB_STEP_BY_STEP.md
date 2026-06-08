# BƯỚC 1: PUSH CODE LÊN GITHUB - HƯỚNG DẪN CHI TIẾT

Hướng dẫn từng bước để tạo GitHub repo và push code lên.

---

## PHẦN A: TẠO TÀI KHOẢN GITHUB (NẾU CHƯA CÓ)

### A1. Truy cập GitHub
Mở trình duyệt → đi đến: **https://github.com**

### A2. Đăng ký tài khoản
- Click **"Sign up"** (nếu chưa có tài khoản)
- Điền:
  - **Email**: email của bạn (VD: tanphat@gmail.com)
  - **Password**: mật khẩu (ít nhất 8 ký tự)
  - **Username**: tên hiển thị (VD: tanphat123) — **NHỚ username này!**
- Click **"Create account"**
- Xác minh email (GitHub sẽ gửi email, click link trong email)
- Hoàn tất đăng ký

---

## PHẦN B: TẠO REPOSITORY (KHO CHỨA CODE)

### B1. Đăng nhập GitHub
- Vào **https://github.com**
- Đăng nhập bằng email + password đã tạo ở trên

### B2. Tạo Repository mới
Sau khi đăng nhập, bạn sẽ thấy giao diện chính. Làm theo:

**Cách 1: Click nút "+"**
1. Click **"+"** góc trên bên phải (bên cạnh avatar của bạn)
2. Chọn **"New repository"**

**Cách 2: Click trực tiếp**
1. Truy cập: **https://github.com/new**

### B3. Cấu hình Repository
Điền thông tin như hình bên dưới:

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  Repository name:  chamcong-api                              │
│                                                              │
│  Description:     He thong cham cong thong minh              │
│                                                              │
│  ☑ Public                                              ◉     │
│    ○ Private                                           ○     │
│                                                              │
│  ☑ Add a README file                                 ○     │
│    ○ Add .gitignore: None                              ○     │
│                                                              │
│  Click [Create repository]                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Giải thích:**
- **Repository name**: `chamcong-api` (tên kho chứa, không dấu, không khoảng trắng)
- **Description**: mô tả ngắn (điền hoặc bỏ trống)
- **Public**: chọn cái này (miễn phí, ai cũng thấy code — bạn đang dùng Railway nên cần repo public)
- **Add a README file**: ☐ bỏ chọn (vì project của bạn đã có code rồi)

### B4. Click "Create repository"
Sau khi click, GitHub sẽ tạo xong và hiển thị trang trắng như thế này:

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  Quick setup — if you've done this kind of thing before     │
│                                                              │
│  GitHub CLI   HTTPS   SSH                                   │
│                                                              │
│  https://github.com/YOUR_USERNAME/chamcong-api.git          │
│         ▲                                                     │
│         └── Copy URL này (sẽ dùng ở Bước 2)                 │
│                                                              │
│  ...or push an existing repository from the command line     │
│                                                              │
│    git remote add origin https://github.com/YOUR_USERNAME/   │
│    chamcong-api.git                                         │
│    git branch -M main                                       │
│    git push -u origin main                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

✅ **Repository đã tạo xong!** — Giữ nguyên tab này, ta sẽ quay lại.

---

## PHẦN C: CÀI ĐẶT GIT TRÊN MÁY (NẾU CHƯA CÓ)

Git là phần mềm để quản lý code. Kiểm tra xem đã cài chưa:

### C1. Mở PowerShell
Trên máy bạn, nhấn:
- **Windows + R** → gõ `powershell` → Enter
- Hoặc click chuột phải vào nút Start → **Terminal** / **PowerShell**

### C2. Kiểm tra Git
Gõ lệnh sau và nhấn Enter:

```powershell
git --version
```

**Kết quả 1 — Đã cài đặt** (hiển thị version):
```
git version 2.45.0.windows.1
```
→ Bỏ qua bước C3, chuyển sang **Phần D**

**Kết quả 2 — Chưa cài** (báo lỗi):
```
git: The term 'git' is not recognized...
```
→ Làm bước C3

### C3. Cài Git (Windows)
**Cách 1: Winget (nhanh nhất)**
```powershell
winget install Git.Git
```
Sau khi cài xong, **đóng PowerShell → Mở lại** (để Git nhận diện)

**Cách 2: Tải tay**
1. Truy cập: **https://git-scm.com/download/win**
2. Tải file `.exe` về
3. Chạy file → Next → Next → ... → Install
4. Mở lại PowerShell

### C4. Xác nhận đã cài được
```powershell
git --version
```
Nếu hiển thị version (VD: `git version 2.45.0`) → OK!

---

## PHẦN D: PUSH CODE LÊN GITHUB

### D1. Mở PowerShell vào thư mục project
Trong PowerShell, gõ:

```powershell
cd "c:\Users\MSI PC\OneDrive\Máy tính\QUẢN LÝ NƯỚC"
```

Nhấn Enter. Gõ tiếp để kiểm tra đã vào đúng thư mục:

```powershell
dir
```

Bạn sẽ thấy danh sách thư mục/file, gồm:
```
    Directory: C:\Users\MSI PC\OneDrive\Máy tính\QUẢN LÝ NƯỚC

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----         6/6/2026   9:00 AM                backend
d-----         6/6/2026   9:00 AM                frontend
d-----         6/6/2026   9:00 AM                vps
-a----         6/6/2026   9:00 AM           234 .gitignore
-a----         6/6/2026   9:00 AM           512 .env.example
...
```

### D2. Khởi tạo Git Repository (git init)
Gõ lệnh:

```powershell
git init
```

Kết quả:
```
Initialized empty Git repository in C:/Users/MSI PC/OneDrive/Máy tính/QUẢN LÝ NƯỚC/.git/
```

### D3. Thêm tất cả file vào Git (git add)
```powershell
git add .
```

Lệnh này thêm **TẤT CẢ** file trong thư mục vào Git, **NGOẠI TRỪ** các file trong `.gitignore` (như `.env`, `*.db`, `cert.pem`, `key.pem`).

### D4. Tạo Commit đầu tiên (git commit)
```powershell
git commit -m "Initial commit - Cham Cong API"
```

Kết quả:
```
[main (root-commit) abc1234] Initial commit - Cham Cong API
 25 files changed, 3456 insertions(+)
```

### D5. Đặt tên nhánh chính là "main"
```powershell
git branch -M main
```

### D6. Thêm GitHub Repository làm remote (git remote add)

**THAY THẾ** `YOUR_USERNAME` bằng username GitHub của bạn ở **B3**:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/chamcong-api.git
```

Ví dụ: nếu username là `tanphat123`:
```powershell
git remote add origin https://github.com/tanphat123/chamcong-api.git
```

### D7. Push code lên GitHub (git push)

```powershell
git push -u origin main
```

**Kết quả:**
```
Enumerating objects: 30, done.
Counting objects: 100% (30/30), done.
Delta compression using up to 8 threads
Compressing objects: 100% (20/20), done.
Writing objects: 100% (30/30), 2.50 MiB | 1.2 MiB/s, done.
Total 30 (delta 10), reused 0 (delta 0)
remote: Resolving deltas: 100% (10/10), done.
To https://github.com/YOUR_USERNAME/chamcong-api.git
 * [new branch]      main -> main
branch 'main' => tracking set up to 'origin/main'
```

---

## PHẦN E: XÁC NHẬN THÀNH CÔNG

### E1. Quay lại trang GitHub
 Quay lại tab GitHub (đã mở ở **Phần B**).

### E2. Refresh trang
Nhấn **F5** hoặc click **🔄 Refresh**

### E3. Kiểm tra
Bạn sẽ thấy code của mình hiển thị trên GitHub, gồm các thư mục:
```
chamcong-api/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── routers/
│   └── middleware/
├── frontend/
│   ├── index.html
│   ├── pos.html
│   ├── js/
│   └── css/
├── .gitignore
├── Procfile
├── render.yaml
├── requirements.txt
└── ...
```

✅ **Hoàn tất! Code đã lên GitHub!**

---

## PHẦN F: CÁC LỖI THƯỜNG GẶP

### ❌ Lỗi 1: "git: command not found"
→ Git chưa cài. Làm lại **Phần C**

### ❌ Lỗi 2: "Authentication failed" khi push
Cần tạo **Personal Access Token** để push:

1. Trên GitHub → Click avatar → **Settings**
2. Bên trái → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
3. Click **Generate new token (classic)**
4. Điền:
   - **Note**: `chamcong-push`
   - **Expiration**: chọn `30 days` (hoặc `No expiration`)
   - ☑ **repo** → tick chọn
5. Click **Generate token**
6. **COPY token** ngay (chỉ hiển thị 1 lần!)
   - Token sẽ có dạng: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

7. Quay lại PowerShell, gõ lại:
```powershell
git push -u origin main
```

8. Khi hỏi username → nhập **username GitHub** của bạn → Enter
9. Khi hỏi password → **DÁN TOKEN** (không phải mật khẩu GitHub!) → Enter

### ❌ Lỗi 3: "Could not resolve host"
→ Kiểm tra internet. Thử mở trình duyệt vào `https://github.com`

### ❌ Lỗi 4: "src refspec main does not match any"
→ Thử:
```powershell
git status
git push -u origin master
```

---

## TÓM TẮT NHANH CÁC LỆNH

```powershell
# 1. Vào thư mục project
cd "c:\Users\MSI PC\OneDrive\Máy tính\QUẢN LÝ NƯỚC"

# 2. Khởi tạo git
git init

# 3. Thêm tất cả file
git add .

# 4. Tạo commit đầu tiên
git commit -m "Initial commit"

# 5. Đặt tên nhánh
git branch -M main

# 6. Thêm remote (THAY YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/chamcong-api.git

# 7. Push lên GitHub
git push -u origin main
```

Sau khi hoàn thành Bước 1, quay lại **RAILWAY_DEPLOY.md** để làm Bước 2 trở đi.
