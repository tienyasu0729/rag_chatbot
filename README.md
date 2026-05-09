# RAG Chatbot — Tư vấn xe hơi

FastAPI chatbot tư vấn xe hơi, sử dụng RAG + Text-to-SQL + Pricing AI.

**Stack:** FastAPI · Qdrant · Redis · SQL Server · OpenAI-compatible LLM · Embedding API

---

## Yêu cầu hệ thống

| Thành phần | Phiên bản tối thiểu |
|---|---|
| Python | 3.11+ |
| Docker Desktop | 24+ |
| ODBC Driver for SQL Server | 17 hoặc 18 |
| SQL Server | 2019+ (đã có sẵn trong project) |

---

## Cách 1 — Chạy local (Python trực tiếp) ✅ Khuyến nghị khi dev

### Bước 1 — Cài dependencies

```bash
cd D:\Workspace\user-cars-repository\repo-tien_1\rag_chatbot

# Tạo virtualenv (chỉ làm 1 lần)
python -m venv .venv

# Kích hoạt virtualenv
.venv\Scripts\activate          # Windows CMD / PowerShell

# Cài packages
pip install -r requirements.txt
```

> **Lưu ý:** Nếu gặp lỗi `pyodbc` → cần cài [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

---

### Bước 2 — Khởi động Qdrant và Redis qua Docker

Qdrant và Redis chạy qua Docker (đã có `docker-compose.yml`):

```bash
# Chỉ khởi động Qdrant + Redis (không build app)
docker compose up -d qdrant redis
```

Kiểm tra đã chạy:

```bash
docker ps
# Phải thấy: rag-chatbot-qdrant (port 6333) và redis (port 6379)
```

---

### Bước 3 — Cấu hình file `.env`

Sao chép file mẫu và điền thông tin thực:

```bash
copy .env.example .env
```

Các biến **bắt buộc** phải điền:

```dotenv
# SQL Server — kết nối database xe hơi
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_SERVER_DB=usedCars
SQL_SERVER_USER=app_rw_user
SQL_SERVER_PASSWORD=<mật khẩu>
SQL_READONLY_USER=rag_chatbot_readonly
SQL_READONLY_PASSWORD=<mật khẩu>

# LLM Gateway (OpenAI-compatible)
LLM_MODEL=qwen/qwen3-32b
LLM_BASE_URL=https://your-llm-gateway.example.com/v1
API_KEY=<api key>

# Embedding (dùng OpenAI-compatible hoặc local)
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BASE_URL=https://platform.beeknoee.com/api/v1
EMBEDDING_API_KEY=<api key>
QDRANT_COLLECTION=xe_inventory_openai_small

# Vision AI — định giá xe qua ảnh
VISION_BASE_URL=https://platform.beeknoee.com/api/v1
VISION_API_KEY=<api key>
VISION_MODEL=gemini-2.5-flash-lite

# Admin
ADMIN_API_KEY=<chuỗi bí mật tự đặt>
```

> Xem `.env.example` để biết đầy đủ các biến tùy chọn.

---

### Bước 4 — Chạy ứng dụng

```bash
# Đảm bảo virtualenv đang active
.venv\Scripts\activate

# Chạy server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Server khởi động tại: **http://localhost:8000**

Lần đầu chạy sẽ mất 1–3 phút để:
- Load embedding model
- Kết nối Qdrant, khởi tạo collection
- Sync dữ liệu xe từ SQL Server vào Qdrant

---

### Bước 5 — Kiểm tra hoạt động

```bash
# Health check
curl http://localhost:8000/health

# Kết quả mong đợi:
# {"status":"ok","embedding_ready":true,"qdrant_available":true,...}
```

Mở giao diện chat test: **http://localhost:8000/chat**

---

## Cách 2 — Chạy toàn bộ bằng Docker Compose

Dùng khi muốn chạy cả app + Qdrant + Redis trong Docker.

### Bước 1 — Chuẩn bị env cho Docker

```bash
# Sao chép file mẫu
copy deploy\env\app.env.example deploy\env\app.env
copy deploy\env\qdrant.env.example deploy\env\qdrant.env
copy deploy\env\redis.env.example deploy\env\redis.env
```

Điền thông tin vào `deploy/env/app.env` (tương tự `.env` ở trên, nhưng:
- `QDRANT_HOST=qdrant` thay vì `localhost`
- `REDIS_HOST=redis` thay vì `localhost`
- `SQL_SERVER_HOST=host.docker.internal` nếu SQL Server chạy ngoài Docker trên Windows)

### Bước 2 — Build và chạy

```bash
cd D:\Workspace\user-cars-repository\repo-tien_1\rag_chatbot

docker compose up -d --build
```

### Bước 3 — Xem logs

```bash
docker compose logs -f app
```

### Dừng stack

```bash
docker compose down
```

> **Lưu ý:** `docker-compose.yml` chỉ dùng để chạy Qdrant + Redis local (Cách 1) hoặc build toàn bộ stack local. Không có cấu hình deploy VPS.

---

## Embedding

Project dùng **OpenAI-compatible embedding API** (mặc định `text-embedding-3-small` qua Beeknoee).

```dotenv
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BATCH_SIZE=32
EMBEDDING_BASE_URL=https://platform.beeknoee.com/api/v1
EMBEDDING_API_KEY=<api key>
QDRANT_COLLECTION=xe_inventory_openai_small
```

---

## Sync dữ liệu xe vào Qdrant

Khi chạy lần đầu, app tự động sync. Để sync thủ công (admin):

```bash
curl -X POST http://localhost:8000/admin/ai-chat/sync-embeddings \
  -H "X-Admin-Key: <ADMIN_API_KEY>"
```

---

## Các endpoint chính

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/health` | Kiểm tra trạng thái hệ thống |
| `GET` | `/health/llm` | Kiểm tra kết nối LLM |
| `POST` | `/ai-chat/sessions` | Tạo session chat mới |
| `POST` | `/ai-chat/sessions/{id}/messages` | Gửi tin nhắn |
| `GET` | `/ai-chat/sessions/{id}/messages` | Lấy lịch sử chat |
| `DELETE` | `/ai-chat/sessions/{id}` | Xóa session |
| `GET` | `/chat` | Giao diện chat test (HTML) |
| `GET` | `/pricing-ui` | Giao diện định giá xe test |
| `POST` | `/admin/ai-chat/sync-embeddings` | Sync embeddings (admin) |

Swagger UI: **http://localhost:8000/docs**

---

## Tích hợp với used-cars frontend

Bật AI chatbot trong frontend bằng cách sửa file `.env` của project `used-cars`:

```dotenv
# D:\Workspace\user-cars-repository\repo-tien_1\used-cars\.env
VITE_AI_CHATBOT_ENABLED=true
VITE_AI_CHATBOT_HOST=127.0.0.1
VITE_AI_CHATBOT_PORT=8000
```

Sau đó restart Vite dev server.

---

## Xử lý lỗi thường gặp

**`ModuleNotFoundError: No module named 'fastapi'`**
→ Chưa kích hoạt virtualenv hoặc chưa cài packages.
```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

**`pyodbc.Error: ('01000', ...ODBC Driver...)`**
→ Chưa cài ODBC Driver 17 for SQL Server. Tải tại:
https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

**`Qdrant chưa sẵn sàng` / `503`**
→ Qdrant container chưa chạy.
```bash
docker compose up -d qdrant
```

**`Session không tồn tại` / `404`**
→ Redis đã xóa session (TTL hết hạn). Tạo session mới từ frontend.

**`LLM API tạm thời hết quota` / `429`**
→ API key LLM đã hết quota. Kiểm tra `LLM_BASE_URL` và `API_KEY` trong `.env`.

---

## Bảo mật

File `.env` và `deploy/env/app.env` chứa secret thật. **Không commit lên Git.**
Trước khi chia sẻ repo, rotate tất cả API key và mật khẩu.
