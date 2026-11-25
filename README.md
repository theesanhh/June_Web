# June OMS V1

Ứng dụng web nội bộ chạy local cho cửa hàng June. Phần đầu tiên gồm giao diện kiểm tra trạng thái, API FastAPI, SQLite và migration bằng Alembic.

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

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

- Trang chính [June OMS](http://127.0.0.1:8000/)
- Trạng thái API [Health](http://127.0.0.1:8000/api/health)
- Tài liệu API [Swagger UI](http://127.0.0.1:8000/docs)

SQLite mặc định lưu tại `data/june.sqlite3`. Có thể đặt biến môi trường `JUNE_DB_PATH` trước khi chạy cả Alembic và Uvicorn để dùng cùng một tệp khác. Phần này không cần dịch vụ ngoài hoặc khóa API.

Khi sửa giao diện, giữ FastAPI chạy và mở PowerShell thứ hai trong `frontend`. Chạy `npm run dev` và dùng URL do Vite in ra. Vite chuyển các yêu cầu `/api` tới FastAPI trên cổng 8000.

## Tiến độ

Đã triển khai giao diện trạng thái, cấu hình build, kiểm tra API đọc SQLite, migration thiết lập cửa hàng và nhật ký Uvicorn. Đăng nhập Admin, giao diện cài đặt và sao lưu local là các phần tiếp theo của nền tảng. Các module nghiệp vụ chưa được triển khai.
