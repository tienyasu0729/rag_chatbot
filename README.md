# RAG Chatbot

Du an FastAPI cho chatbot tu van xe hoi, dung RAG + Text-to-SQL + pricing API.

## Cau truc Docker deploy

Stack da duoc tach thanh 3 service ro rang:

1. `app`
   API FastAPI chay trong image tu `Dockerfile`.
2. `qdrant`
   Vector database, dung image chinh chu `qdrant/qdrant`.
3. `redis`
   Session cache va retry queue, dung image chinh chu `redis:7-alpine`.

Tat ca noi chung qua network noi bo `rag_network`.

## Thu muc env deploy

Env deploy duoc tach rieng theo tung service:

- `deploy/env/app.env`
- `deploy/env/qdrant.env`
- `deploy/env/redis.env`

File mau:

- `deploy/env/app.env.example`
- `deploy/env/qdrant.env.example`
- `deploy/env/redis.env.example`

Luu y quan trong:

- Trong Docker, `QDRANT_HOST` phai la `qdrant`, khong dung `localhost`.
- Trong Docker, `REDIS_HOST` phai la `redis`, khong dung `localhost`.
- `SQL_SERVER_HOST` phai la host/IP thuc ma Ubuntu container truy cap duoc.
- Tren Linux/Ubuntu, `host.docker.internal` co the khong co san. Neu SQL Server nam ngoai Docker, hay doi thanh IP private, DNS noi bo, hoac ten may SQL that.

## Chay local bang Docker Compose

CPU mode:

```bash
docker compose up -d --build
```

Neu may Ubuntu co GPU va da cai NVIDIA Container Toolkit:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

## Push/Pull de deploy Ubuntu

### 1. Build va push image app

Chi `app` la image tu source code cua ban. `qdrant` va `redis` dung image co san, khong can tu build lai.

```bash
docker build -t your-registry/rag-chatbot-app:latest .
docker push your-registry/rag-chatbot-app:latest
```

### 2. Tren Ubuntu server

Copy cac file sau len server:

- `docker-compose.yml`
- `docker-compose.gpu.yml` neu can GPU
- thu muc `deploy/env/`

Sua `docker-compose.yml` neu muon pull image thay vi build local:

```yaml
  app:
    image: your-registry/rag-chatbot-app:latest
    # bo khoi build:
```

Sau do chay:

```bash
docker compose pull
docker compose up -d
```

## Loi ich cua cach tach nay

- Fix tung service de hon: app, qdrant, redis tach biet.
- Env ro rang theo tung service, khong tron lung tung.
- Ket noi noi bo on dinh qua ten service Docker.
- De doi image app ma khong anh huong du lieu Redis/Qdrant.

## Bao mat

Repo hien co secret that trong `.env` va `deploy/env/app.env`. Truoc khi push len Git hoac chia se cho nguoi khac, nen rotate va dua secret sang secret manager hoac file env private khong commit.
