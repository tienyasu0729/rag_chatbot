# Tài liệu thuyết trình hệ thống RAG Chatbot

## 1) Mục đích tài liệu

Tài liệu này được viết cho 2 nhóm người đọc:

- **Người dùng nghiệp vụ / stakeholder**: cần hiểu hệ thống đang làm được gì, giá trị mang lại ra sao.
- **Người trình bày kỹ thuật**: cần một khung nội dung rõ ràng để nói trọn vẹn trong 10-20 phút.

Phạm vi tài liệu bám theo **mã nguồn hiện tại** trong repo `rag_chatbot`.

---

## 2) Tổng quan hệ thống

Hệ thống hiện có 2 năng lực chính:

1. **AI Chat tư vấn xe**: trả lời câu hỏi về xe dựa trên dữ liệu thực tế trong kho xe (RAG + SQL/MCP).
2. **AI định giá xe từ ảnh**: phân tích tình trạng xe qua ảnh, kết hợp dữ liệu thị trường để đề xuất giá nhập.

Kiến trúc triển khai theo 3 service chính:

- `app` (FastAPI)
- `qdrant` (vector database)
- `redis` (session cache, retry queue)

Nguồn dữ liệu nghiệp vụ chính là **SQL Server**.

---

## 3) Kiến trúc kỹ thuật (dễ hiểu)

## 3.1 Thành phần chính

- **API layer**: nhận request chat, request định giá, health check.
- **Orchestration layer**: phân loại intent, chọn pipeline xử lý phù hợp.
- **Retrieval layer**:
  - Vector retrieval qua Qdrant (cho RAG),
  - SQL/MCP tools (cho thống kê, đếm, list).
- **Generation layer**: LLM sinh câu trả lời tự nhiên hoặc JSON định giá.
- **State layer**: Redis + SQL lưu lịch sử hội thoại, preference người dùng.

## 3.2 Luồng khởi động

Khi app khởi chạy:

1. Load embedding service.
2. Khởi tạo/kiểm tra Qdrant collection.
3. Khởi tạo Redis.
4. Chạy đồng bộ dữ liệu xe theo delta (tránh full re-embed).
5. Bật scheduler để sync định kỳ.

---

## 4) Pipeline AI Chat (RAG + SQL + Personalization)

## 4.1 Các bước xử lý

1. Người dùng gửi tin nhắn vào endpoint chat.
2. Hệ thống phân loại intent: `RAG`, `SQL`, `RECOMMEND`, `CLARIFY`, `OTHER`.
3. Tùy intent:
   - `RAG/RECOMMEND`: tìm xe qua Qdrant + verify lại trạng thái xe từ SQL.
   - `SQL`: gọi MCP tool; nếu không phù hợp thì fallback SQL agent; nếu vẫn fail có DB fallback.
4. Build prompt theo template tương ứng intent.
5. Gọi LLM sinh câu trả lời.
6. Lưu hội thoại và preference.
7. Trả thêm suggested questions để gợi ý vòng chat tiếp theo.

## 4.2 Guardrail quan trọng

- Prompt có quy tắc chặt về **toàn vẹn số liệu**:
  - Không đếm từ sample hiển thị để suy ra tổng,
  - Số liệu tổng phải lấy từ block thống kê thật từ database.
- Nếu retrieval không có dữ liệu phù hợp, bot phải thông báo rõ và gợi ý điều chỉnh tiêu chí.

---

## 5) Pipeline định giá xe từ ảnh

## 5.1 Các bước xử lý

1. Nhận input multipart: ảnh + tag ảnh + cấu hình xe.
2. Validate request (số lượng ảnh/tag, subcategory...).
3. Chuẩn hóa và gom nhóm ảnh (`exterior_overview`, `interior`, `detail_damage`).
4. Gọi vision model phân tích tình trạng xe.
5. Truy vấn dữ liệu xe tương đồng từ SQL để lấy market min/avg/max.
6. Gọi LLM tạo JSON định giá giá nhập.
7. Nếu lỗi LLM, fallback công thức định giá.
8. Trả response gồm:
   - đánh giá tình trạng xe,
   - dữ liệu thị trường,
   - giá nhập đề xuất,
   - danh sách comparables (nếu bật cờ).

## 5.2 Fallback giúp hệ thống ổn định

- Không có ảnh hợp lệ / thiếu cấu hình vision / lỗi vision API -> dùng default assessment.
- Lỗi LLM pricing -> dùng fallback formula:
  - `suggested_purchase_price = market_avg x (condition_score / 100) x 0.85`

---

## 6) Model sử dụng theo từng giai đoạn

Lưu ý: hệ thống lấy model theo biến môi trường, nên có thể thay đổi giữa các môi trường.

## 6.1 Giai đoạn Embedding (RAG indexing + query embedding)

- **Provider**: `openai` — model `text-embedding-3-small` (hoặc `text-embedding-3-large`)
- Cấu hình qua `EMBEDDING_MODEL` và `EMBEDDING_API_KEY` trong `.env`

## 6.2 Giai đoạn LLM cho Chatbot

Sử dụng `LLM_MODEL` qua OpenAI-compatible gateway cho:

- fallback intent classification khi rule-based không chắc chắn,
- tool selection cho MCP,
- SQL generation cho SQL agent,
- final response generation.

Model ví dụ trong env mẫu: `qwen/qwen3-32b`.

## 6.3 Giai đoạn Vision cho Pricing

Sử dụng `VISION_MODEL` qua `VISION_BASE_URL` (OpenAI-compatible chat completion có ảnh).

Ví dụ trong deploy env mẫu: `gemini-2.5-flash-lite`.

## 6.4 Giai đoạn LLM định giá

Sử dụng `LLM_MODEL` để sinh JSON pricing (giá nhập đề xuất, range, deduction factors...).

Nếu lỗi thì fallback công thức, không phụ thuộc model.

---

## 7) Điểm mạnh, hạn chế, rủi ro

## 7.1 Điểm mạnh

- Kiến trúc module hóa rõ: chat, pricing, mcp, pipeline, db.
- Có nhiều tầng fallback giúp tránh chết dịch vụ.
- Có cơ chế sync delta embeddings giảm chi phí khởi động lại.
- Có test cho nhiều phần pricing quan trọng.

## 7.2 Hạn chế hiện tại

- Chưa thấy reranker chuyên biệt cho retrieval.
- Một số field vision nội bộ chưa expose hết ra API response.
- UI hiện thiên về test (`/chat`, `/pricing-ui`) hơn là production UX hoàn chỉnh.

## 7.3 Rủi ro cần quản trị

- Quản lý secret (API key, DB credential) cần chặt.
- Chất lượng đầu ra phụ thuộc chất lượng ảnh và dữ liệu thị trường.
- Cần benchmark định lượng cho RAG quality và pricing quality.

---

## 8) Hướng dẫn demo cho người trình bày

## 8.1 Chuẩn bị trước demo

1. Đảm bảo Qdrant + Redis + app đã chạy.
2. Kiểm tra:
   - `GET /health`
   - `GET /health/llm`
3. Mở:
   - `GET /chat` để demo chat,
   - `GET /pricing-ui` để demo định giá ảnh.

## 8.2 Kịch bản demo gợi ý (5-7 phút)

1. Chat câu hỏi tư vấn chung (RECOMMEND).
2. Chat câu hỏi thống kê (SQL).
3. Chat câu hỏi về mẫu xe cụ thể (RAG).
4. Upload ảnh định giá và đọc kết quả market + pricing.

---

## 9) Kịch bản thuyết trình 15 phút (nói theo slide)

- **Phút 0-2**: Bài toán và mục tiêu hệ thống.
- **Phút 2-5**: Kiến trúc tổng thể và thành phần chính.
- **Phút 5-8**: Pipeline AI Chat + guardrail dữ liệu.
- **Phút 8-11**: Pipeline AI Pricing từ ảnh + fallback.
- **Phút 11-13**: Model mapping theo giai đoạn.
- **Phút 13-15**: Điểm mạnh, hạn chế, roadmap nâng cấp.

---

## 10) Bộ câu hỏi phản biện và trả lời ngắn

1. **Hệ thống dùng model nào?**  
   -> Theo env: embedding (`text-embedding-3-small` hoặc `text-embedding-3-large`), LLM (`LLM_MODEL`), vision (`VISION_MODEL`).

2. **Nếu Qdrant hoặc Vision bị lỗi thì sao?**  
   -> Hệ thống chạy degraded/fallback, vẫn trả response có kiểm soát.

3. **Làm sao hạn chế bot bịa số liệu?**  
   -> Prompt guardrail bắt buộc lấy số liệu từ thống kê DB block.

4. **Đã có đo chất lượng chưa?**  
   -> Có test chức năng; nên bổ sung bộ eval định lượng riêng cho RAG và pricing accuracy.

---

## 11) Tham chiếu mã nguồn chính (để tra cứu khi cần)

- `app/main.py`
- `app/config.py`
- `app/services/embedding.py`
- `app/services/rag.py`
- `app/services/intent.py`
- `app/services/mcp_dispatcher.py`
- `app/services/sql_agent.py`
- `app/services/preference.py`
- `app/services/pricing.py`
- `app/services/vision_analysis.py`
- `app/routes/pricing_router.py`
- `app/pipeline/sync.py`
- `app/db/qdrant.py`
- `docker-compose.yml`
- `docs/pricing-feature-spec.md`

---

## 12) Kết luận ngắn gọn

Hệ thống hiện đã đạt mức **end-to-end thực dụng** cho cả tư vấn xe và định giá xe:

- có retrieval từ dữ liệu thật,
- có lớp thống kê SQL chính xác,
- có cá nhân hóa theo preference hội thoại,
- có pricing theo ảnh + market,
- có fallback nhiều tầng để vận hành ổn định.

Để tiến lên production scale, ưu tiên tiếp theo là:

1. tăng cường bảo mật và secret management,
2. bổ sung eval định lượng chất lượng mô hình,
3. tăng quan sát vận hành và chuẩn hóa quy trình release.
