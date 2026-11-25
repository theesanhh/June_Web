# June OMS V1

Ứng dụng web nội bộ chạy local cho cửa hàng June. Nền tảng gồm API FastAPI, SQLite, migration Alembic và một tài khoản Admin dùng chung.

## Cài đặt trên Windows

Cần Python 3.11 trở lên và Node.js 22 LTS. Chạy PowerShell tại thư mục gốc của dự án.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
Push-Location frontend
npm ci
npm run build
Pop-Location
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m pytest -q
```

## Chạy local

Sau khi chạy migration, đặt mật khẩu Admin từ PowerShell tương tác. Mật khẩu dài 12–128 ký tự và được nhập ẩn.

```powershell
.\.venv\Scripts\python.exe -m backend.set_admin_password
```

Chạy lại lệnh trên để đổi mật khẩu và thu hồi mọi phiên đang hoạt động. Phiên đăng nhập hết hạn sau 8 giờ.

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

- Trang chính [June OMS](http://127.0.0.1:8000/)
- Trạng thái API [Health](http://127.0.0.1:8000/api/health)
- Tài liệu API [Swagger UI](http://127.0.0.1:8000/docs)

SQLite mặc định lưu tại `data/june.sqlite3`. Nếu dùng tệp khác, đặt cùng giá trị `JUNE_DB_PATH` cho Alembic, lệnh đặt mật khẩu và Uvicorn. Phần này không cần dịch vụ ngoài hoặc khóa API.

Khi sửa giao diện, giữ FastAPI chạy và mở PowerShell thứ hai trong `frontend`. Chạy `npm run dev` và dùng URL do Vite in ra. Vite chuyển các yêu cầu `/api` tới FastAPI trên cổng 8000.

## Tiến độ

Đã triển khai giao diện trạng thái, migration SQLite, đăng nhập và đăng xuất Admin. Giao diện cài đặt và sao lưu local là các phần tiếp theo của nền tảng. Các module nghiệp vụ chưa được triển khai.
