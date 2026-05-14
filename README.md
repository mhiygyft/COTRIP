# Novaryo Travel Booking Platform

Novaryo là nền tảng đặt dịch vụ du lịch được xây dựng bằng Django. Repo có các module chính cho khách sạn, chuyến bay, gói du lịch, hoạt động, booking, review và loyalty.

## Yêu cầu môi trường

- Python 3.11 trở lên
- pip
- PostgreSQL 15 nếu chạy theo cấu hình mặc định
- Redis nếu muốn chạy Celery/cache theo cấu hình đầy đủ
- Docker Desktop nếu muốn chạy bằng Docker Compose

> Ghi chú: `Dockerfile` dùng image `python:3.11-slim`, còn README cũ ghi Python 3.13. Với local development, nên dùng Python 3.11+ để tương thích rộng hơn với Dockerfile hiện tại.

## Cách 1: Chạy local bằng SQLite

Cách này phù hợp nhất để kiểm tra nhanh trên máy local vì không cần cài PostgreSQL.

### 1. Tạo file môi trường

Copy file mẫu:

```bash
cp .env.example .env
```

Nếu dùng PowerShell trên Windows:

```powershell
Copy-Item .env.example .env
```

Mở file `.env` và chỉnh các giá trị tối thiểu:

```env
SECRET_KEY=dev-secret-key-change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
USE_SQLITE=True
REDIS_URL=redis://localhost:6379/0
```

### 2. Tạo virtual environment

Linux/macOS:

```bash
python -m venv venv
source venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Nếu PowerShell chặn script, chạy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 3. Cài dependency

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Chạy migration

```bash
python manage.py migrate
```

Nếu cần tài khoản admin:

```bash
python manage.py createsuperuser
```

### 5. Chạy server

```bash
python manage.py runserver
```

Mở các URL sau:

- Website: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Swagger API docs: http://127.0.0.1:8000/api/docs/
- ReDoc API docs: http://127.0.0.1:8000/api/redoc/

## Cách 2: Chạy local bằng PostgreSQL

Nếu muốn chạy gần giống môi trường Docker/production hơn, dùng PostgreSQL.

### 1. Tạo database PostgreSQL

Tạo database và user theo cấu hình bạn muốn, ví dụ:

```sql
CREATE DATABASE novaryo;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE novaryo TO postgres;
```

### 2. Cấu hình `.env`

```env
SECRET_KEY=dev-secret-key-change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
USE_SQLITE=False
DB_NAME=novaryo
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

### 3. Cài dependency, migrate và chạy server

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Trên Windows PowerShell, dùng lệnh activate:

```powershell
.\venv\Scripts\Activate.ps1
```

## Cách 3: Chạy bằng Docker Compose

Repo có sẵn `docker-compose.yml` với các service:

- `db`: PostgreSQL 15
- `redis`: Redis 7
- `web`: Django development server
- `celery`: Celery worker
- `celery-beat`: Celery beat

Chạy:

```bash
docker compose up --build
```

Sau khi container chạy, mở:

- Website: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- API docs: http://127.0.0.1:8000/api/docs/

Chạy migration trong container:

```bash
docker compose exec web python manage.py migrate
```

Tạo admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

Nếu muốn dừng toàn bộ service:

```bash
docker compose down
```

Nếu muốn xóa cả volume database:

```bash
docker compose down -v
```

## Lệnh hữu ích khi phát triển

Tạo migration mới:

```bash
python manage.py makemigrations
```

Áp dụng migration:

```bash
python manage.py migrate
```

Collect static files:

```bash
python manage.py collectstatic
```

Mở Django shell:

```bash
python manage.py shell
```

Chạy Celery worker nếu Redis đang chạy:

```bash
celery -A novaryo worker -l info
```

Chạy Celery beat:

```bash
celery -A novaryo beat -l info
```

## Cấu trúc thư mục chính

```text
.
├── activities/        # Module hoạt động và trải nghiệm
├── bookings/          # Module quản lý booking
├── flights/           # Module chuyến bay
├── hotels/            # Module khách sạn
├── loyalty/           # Module điểm thưởng/thành viên
├── novaryo/           # Settings, URLs, WSGI/ASGI
├── packages/          # Module gói du lịch
├── reviews/           # Module đánh giá
├── docker-compose.yml
├── Dockerfile
├── manage.py
└── requirements.txt
```

## Xử lý lỗi thường gặp

### Lỗi thiếu `SECRET_KEY`

Thông báo thường gặp:

```text
decouple.UndefinedValueError: SECRET_KEY not found
```

Cách xử lý: tạo file `.env` từ `.env.example` và đảm bảo có dòng:

```env
SECRET_KEY=dev-secret-key-change-me
```

### Lỗi không kết nối được PostgreSQL

Nếu chỉ muốn chạy nhanh ở local, bật SQLite:

```env
USE_SQLITE=True
```

Nếu dùng PostgreSQL, kiểm tra lại các biến:

```env
DB_NAME=novaryo
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432
```

### Lỗi thiếu module `users` hoặc `payments`

File `novaryo/settings.py` và `novaryo/urls.py` hiện có khai báo app `users` và `payments`. Nếu khi chạy gặp lỗi dạng:

```text
ModuleNotFoundError: No module named 'users'
ModuleNotFoundError: No module named 'payments'
```

hãy kiểm tra lại source code, branch hoặc gói tải về vì thư mục hiện tại cần có đủ các app được khai báo trong settings/urls. Nếu hai app đó không còn được dùng, cần bỏ chúng khỏi `INSTALLED_APPS` và `urlpatterns` tương ứng.

### Lỗi Redis khi chạy Celery

Đảm bảo Redis đang chạy ở:

```text
redis://localhost:6379/0
```

Nếu không dùng Celery trong lúc phát triển giao diện/API cơ bản, bạn có thể chỉ chạy Django server trước.

## Ghi chú license

Repo gốc ghi rõ dự án thuộc bản quyền của tác giả. Trước khi dùng cho mục đích thương mại, phân phối lại hoặc chỉnh sửa công khai, cần kiểm tra và tuân thủ điều khoản license đi kèm repo.
