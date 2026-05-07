# Deploy Ubuntu VPS

Muc tieu:

- `rag-chatbot-app` chay Docker, bind localhost `127.0.0.1:8000`
- `qdrant` chay Docker cung compose
- `SQL Server` va `Redis` tai su dung tren host VPS
- frontend `used-cars-frontend` goi truc tiep qua Docker network toi `http://rag-chatbot-app:8000`

## File can sua tren VPS

- `deploy/env/app.vps.env`
  - file cau hinh chinh
- `docker-compose.vps.yml`
  - thuong khong can sua

## Chay tren VPS

```bash
mkdir -p /opt/rag-chatbot/deploy/env
cd /opt/rag-chatbot
```

Copy len VPS cac file:

- `docker-compose.vps.yml`
- `deploy/env/app.vps.env` hoac copy tu `app.vps.env.example` roi sua

Lenh chay:

```bash
docker compose -f docker-compose.vps.yml pull
docker compose -f docker-compose.vps.yml up -d
```

Kiem tra:

```bash
docker compose -f docker-compose.vps.yml logs --tail=100 app
curl -I http://127.0.0.1:8000/health
curl -I http://127.0.0.1/ai-health
```

## Luu y ket noi voi frontend da deploy

Frontend `used-cars` nen cau hinh:

- `AI_CHAT_UPSTREAM=http://rag-chatbot-app:8000`

Va 2 compose can cung tham gia external network `app-shared`. Khi do frontend se goi duoc ngay qua:

- `/ai-chat/...`
- `/ai-health`

Khong can rebuild frontend neu bien nay da duoc dat san tren VPS.

## Bat chatbot tren giao dien frontend

Tren VPS dang chay `used-cars`, sua file:

- `/opt/used-cars/used-cars/docker/.env.frontend`

Can chac cac bien nay dung:

```env
VITE_AI_CHATBOT_ENABLED=true
AI_CHAT_UPSTREAM=http://rag-chatbot-app:8000
```

Sau do restart frontend:

```bash
cd /opt/used-cars
docker compose -f docker-compose.vps.yml up -d frontend
```
