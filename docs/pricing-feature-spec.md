# Đặc tả hiện trạng tính năng định giá xe

## 1. Mục tiêu tài liệu

Tài liệu này mô tả chính xác những phần **đã được triển khai** cho tính năng định giá xe trong repo hiện tại, dựa trên mã nguồn và test đang có. Đây là tài liệu đặc tả theo hiện trạng triển khai, không phải danh sách ý tưởng tương lai.

## 2. Phạm vi đã hoàn thành

Tính năng định giá xe hiện đã làm được các phần sau:

1. Cung cấp API lấy danh sách `subcategory` để phục vụ dropdown chọn dòng xe trên UI.
2. Cung cấp API định giá xe từ:
   - cấu hình xe (`subcategory`, năm, nhiên liệu, hộp số, xuất xứ),
   - bộ ảnh thực tế của xe,
   - tag cho từng ảnh.
3. Chuẩn hóa và gom nhóm ảnh đầu vào trước khi gửi đi phân tích.
4. Phân tích tình trạng xe từ ảnh bằng vision model, có cơ chế fallback khi thiếu cấu hình hoặc khi vision call lỗi.
5. Truy vấn dữ liệu xe tương đồng từ SQL Server để lấy mặt bằng giá thị trường.
6. Đề xuất giá nhập xe bằng LLM, có công thức fallback nếu bước định giá bằng LLM thất bại.
7. Trả về kết quả định giá gồm:
   - đánh giá tình trạng xe,
   - dữ liệu thị trường,
   - giá nhập đề xuất,
   - danh sách xe so sánh nếu người gọi bật cờ `include_comparables`.
8. Có màn hình HTML test thủ công để thao tác upload ảnh và gọi API.

## 3. Thành phần đã triển khai

### 3.1. API backend

- `GET /api/pricing/subcategories`
  - Trả về danh sách `subcategory` đang hoạt động có xe trong dữ liệu.
  - Dùng cho dropdown trên màn hình test định giá.

- `POST /api/pricing/estimate`
  - Nhận dữ liệu multipart form để định giá xe.
  - Endpoint đã được khai báo response model rõ ràng.

- `GET /pricing-ui`
  - Trả về giao diện HTML test thủ công cho tính năng định giá.

## 4. Dữ liệu đầu vào của API định giá

API `POST /api/pricing/estimate` hiện nhận các trường sau:

- `images`: danh sách file ảnh, bắt buộc có ít nhất 1 ảnh.
- `image_tags`: danh sách tag tương ứng với từng ảnh, số lượng phải khớp với `images`.
- `subcategory_id`: mã dòng xe, ưu tiên dùng nếu có.
- `subcategory_name`: tên dòng xe, dùng làm fallback khi không có `subcategory_id`.
- `year`: năm sản xuất.
- `fuel`: loại nhiên liệu.
- `transmission`: loại hộp số.
- `origin`: xuất xứ.
- `include_comparables`: có trả thêm danh sách xe so sánh hay không, mặc định là `false`.

### 4.1. Validation đã có

Các kiểm tra đầu vào hiện đã được triển khai:

1. Bắt buộc có ít nhất 1 ảnh.
2. Số lượng `images` phải bằng số lượng `image_tags`.
3. Bắt buộc phải có ít nhất một trong hai trường:
   - `subcategory_id`
   - `subcategory_name`
4. Bắt buộc phải có `image_tags` cho từng ảnh.

### 4.2. Các tag ảnh đang hỗ trợ

Hệ thống hiện hỗ trợ đúng 3 nhóm ảnh:

- `exterior_overview`
- `interior`
- `detail_damage`

## 5. Luồng xử lý hiện tại

Luồng xử lý của tính năng định giá xe hiện như sau:

1. Nhận request multipart từ UI hoặc client.
2. Validate dữ liệu form.
3. Chuẩn hóa ảnh:
   - đọc từng file,
   - bỏ qua ảnh rỗng hoặc ảnh lỗi,
   - xoay ảnh theo EXIF,
   - convert RGB,
   - resize cạnh lớn nhất về tối đa `768px`.
4. Gom ảnh theo nhóm:
   - `exterior_overview`
   - `interior`
   - `detail_damage`
5. Tạo payload ảnh phục vụ vision:
   - tối đa 4 ảnh ngoại thất được ghép thành 1 grid,
   - tối đa 4 ảnh nội thất được ghép thành 1 grid,
   - tối đa 4 ảnh hư hại chi tiết được gửi riêng từng ảnh.
6. Gọi vision model để đánh giá tình trạng xe từ ảnh.
7. Truy vấn dữ liệu xe tương đồng trong SQL Server để lấy mặt bằng giá thị trường.
8. Gọi LLM để sinh giá nhập đề xuất.
9. Nếu LLM định giá lỗi thì dùng công thức fallback.
10. Trả response JSON cho client.

## 6. Xử lý ảnh đã làm được

### 6.1. Chuẩn hóa ảnh

Phần xử lý ảnh hiện đã làm được:

- đọc nhiều ảnh trong một request;
- bỏ qua ảnh không hợp lệ;
- thống kê:
  - số ảnh hợp lệ (`accepted_count`),
  - số ảnh bị bỏ qua (`skipped_count`),
  - số lượng ảnh theo từng nhóm (`bucket_counts`);
- chuẩn hóa tất cả ảnh về JPEG payload để gửi vision.

### 6.2. Giới hạn payload ảnh

Hệ thống hiện giới hạn payload như sau:

- tối đa 4 ảnh cho grid `exterior_overview`;
- tối đa 4 ảnh cho grid `interior`;
- tối đa 4 ảnh `detail_damage` gửi riêng;
- nếu sau khi lọc mà không còn ảnh hợp lệ thì trả lỗi `Khong co anh hop le de phan tich`.

## 7. Phân tích tình trạng xe từ ảnh

### 7.1. Kết quả phân tích đang trả về

Phần đánh giá tình trạng xe hiện trả về các nhóm dữ liệu sau:

- `condition_score`
- `score_breakdown`
  - `paint_exterior`
  - `body_damage`
  - `interior`
  - `mechanical_visible`
  - `tires_wheels`
- `damage_percentage`
  - `scratch`
  - `dent`
- `risk_flags`
- `damage_summary`

Lưu ý: service vision nội bộ còn xử lý thêm một số field mô tả như `repaint_detected`, `glass_lights_mirrors`, `seat_wear`, `dashboard_steering`, `flood_signs`, nhưng các field này **chưa được đưa ra response API định giá**.

### 7.2. Cơ chế fallback của vision

Hệ thống hiện dùng đánh giá mặc định nếu xảy ra một trong các tình huống:

1. Không có ảnh hợp lệ để phân tích.
2. Chưa cấu hình `VISION_API_KEY`.
3. Chưa cấu hình `VISION_MODEL`.
4. Vision API gọi thất bại hoặc trả dữ liệu không hợp lệ.

### 7.3. Default assessment hiện tại

Khi fallback, hệ thống dùng mặc định:

- `condition_score = 60`
- breakdown:
  - `paint_exterior = 15`
  - `body_damage = 15`
  - `interior = 15`
  - `mechanical_visible = 9`
  - `tires_wheels = 6`
- `damage_percentage`:
  - `scratch = "unknown"`
  - `dent = "unknown"`
- `risk_flags`: chứa lý do fallback nếu có
- `damage_summary`: thông báo rằng đang dùng đánh giá mặc định nên độ tin cậy thấp hơn

## 8. Truy vấn dữ liệu thị trường đã làm được

### 8.1. Nguồn dữ liệu

Tính năng đang truy vấn dữ liệu từ bảng xe trong SQL Server, có join với bảng `Subcategories`.

### 8.2. Điều kiện lọc đang hỗ trợ

Khi lấy xe so sánh, hệ thống hiện lọc theo:

- chỉ lấy xe `is_deleted = 0`;
- chỉ lấy xe có `status` thuộc:
  - `Available`
  - `Sold`
  - `Reserved`
- nếu có `year`: lọc trong khoảng `year - 2` đến `year + 2`;
- nếu có `fuel`: lọc đúng nhiên liệu;
- nếu có `transmission`: lọc đúng hộp số;
- nếu có `origin`: lọc đúng xuất xứ.

### 8.3. Cách match subcategory

Nếu có `subcategory_id`:

- ưu tiên match trực tiếp `v.subcategory_id = ?`

Nếu không có `subcategory_id`, hệ thống fallback theo `subcategory_name` với các mức ưu tiên:

1. `sc.name = ?`
2. `sc.name_normalized = ?`
3. `sc.name LIKE ?`
4. `sc.name_normalized LIKE ?`

Hệ thống có normalize text bỏ dấu để hỗ trợ so khớp tên dòng xe.

### 8.4. Kết quả thị trường trả về

Service hiện trả về:

- `comparable_count`
- `market_min`
- `market_avg`
- `market_max`
- `comparables`: tối đa 10 xe, sắp xếp theo:
  - `priority_match` tăng dần
  - `created_at` giảm dần

Hệ thống cũng có bước khử trùng lặp bằng `ROW_NUMBER() OVER (PARTITION BY id ORDER BY priority_match)`.

## 9. Logic định giá đã làm được

### 9.1. Định giá bằng LLM

Sau khi có:

- cấu hình xe,
- đánh giá tình trạng xe,
- dữ liệu thị trường,

hệ thống gọi LLM để sinh JSON định giá với các trường:

- `suggested_purchase_price`
- `price_range_min`
- `price_range_max`
- `market_avg`
- `market_min`
- `market_max`
- `comparable_count`
- `condition_score`
- `damage_summary`
- `risk_flags`
- `deduction_factors`

Kết quả từ LLM sau đó được normalize lại:

- ép về số nguyên không âm nếu phù hợp;
- tự đảo lại `price_range_min` và `price_range_max` nếu LLM trả ngược;
- fallback `deduction_factors` nếu dữ liệu không đúng kiểu.

### 9.2. Fallback pricing formula

Nếu bước gọi LLM định giá thất bại, hệ thống hiện dùng công thức:

`suggested_purchase_price = market_avg x (condition_score / 100) x 0.85`

Sau đó:

- `price_range_min = suggested_purchase_price x 0.95`
- `price_range_max = suggested_purchase_price x 1.05`

Ví dụ theo test hiện có:

- `market_avg = 200,000,000`
- `condition_score = 60`
- `suggested_purchase_price = 102,000,000`
- `price_range_min = 96,900,000`
- `price_range_max = 107,100,000`

### 9.3. Ý nghĩa nghiệp vụ hiện tại

Theo prompt đang dùng, mục tiêu của bước định giá là:

- đề xuất **giá nhập** cho showroom,
- ưu tiên an toàn biên lợi nhuận,
- không sinh nội dung bán hàng.

## 10. Cấu trúc response API hiện tại

API định giá hiện trả về 3 khối chính:

### 10.1. `vehicle_assessment`

- `condition_score`
- `score_breakdown`
- `damage_percentage`
- `risk_flags`
- `damage_summary`

### 10.2. `market_data`

- `comparable_count`
- `min`
- `avg`
- `max`

### 10.3. `pricing`

- `suggested_purchase_price`
- `price_range_min`
- `price_range_max`
- `deduction_factors`

### 10.4. `comparables`

- Chỉ xuất hiện khi `include_comparables = true`.
- Mỗi item hiện có:
  - `id`
  - `title`
  - `price`
  - `year`
  - `fuel`
  - `transmission`
  - `origin`
  - `status`
  - `created_at`
  - `priority_match`

## 11. UI test thủ công đã làm được

File `test_pricing.html` hiện đã hỗ trợ:

1. Tải danh sách `subcategory` từ API.
2. Cho phép chọn `subcategory` từ dropdown.
3. Tự điền `subcategory_id` và `subcategory_name` theo lựa chọn.
4. Nhập tay cấu hình xe:
   - năm sản xuất,
   - nhiên liệu,
   - hộp số,
   - xuất xứ.
5. Upload nhiều ảnh cùng lúc.
6. Gán tag cho từng ảnh.
7. Bật/tắt trả về danh sách xe so sánh.
8. Gọi `POST /api/pricing/estimate`.
9. Hiển thị trạng thái gọi API và JSON kết quả.
10. Làm mới form hoặc xóa kết quả hiển thị.

## 12. Các hành vi đã được test ở mức mã nguồn

Từ các file test hiện có, hệ thống đã có kiểm chứng cho các hành vi sau:

1. Endpoint định giá mặc định **không trả** `comparables` nếu không bật `include_comparables`.
2. Endpoint trả lỗi `422` khi số lượng `images` và `image_tags` không khớp.
3. Truy vấn market data có:
   - dùng `ROW_NUMBER()` để khử trùng lặp,
   - sắp xếp `comparables` theo `priority_match` rồi `created_at`.
4. Định giá fallback trả đúng công thức tính trong test mẫu.
5. Xử lý ảnh:
   - giữ riêng `detail_damage`,
   - giới hạn số payload ảnh theo đúng rule,
   - reject khi tag không khớp.
6. Vision analysis fallback trả về assessment mặc định khi gọi model lỗi.

## 13. Giới hạn hiện tại

Các điểm dưới đây là giới hạn đang thấy từ hiện trạng triển khai:

1. UI hiện là trang test HTML độc lập, chưa phải màn hình production hoàn chỉnh.
2. Một số field phân tích ảnh có trong service vision nhưng chưa được expose ra response API.
3. Độ chính xác định giá phụ thuộc vào:
   - chất lượng ảnh,
   - chất lượng dữ liệu xe trong SQL Server,
   - cấu hình vision model,
   - chất lượng phản hồi từ LLM.
4. Khi thiếu cấu hình vision hoặc vision lỗi, hệ thống vẫn chạy được nhưng phải dùng assessment mặc định, nên độ tin cậy giá đề xuất giảm.
5. Môi trường hiện tại chưa cài `pytest`, nên chưa xác nhận lại được trạng thái pass/fail bằng cách chạy test trực tiếp trong máy ở thời điểm viết tài liệu này.

## 14. Tham chiếu mã nguồn chính

- Router API: `app/routes/pricing_router.py`
- Pricing service: `app/services/pricing.py`
- Image processing: `app/services/image_processor.py`
- Vision analysis: `app/services/vision_analysis.py`
- Response schema: `app/models/schemas.py`
- Test UI: `test_pricing.html`
- Unit test liên quan:
  - `tests/test_pricing.py`
  - `tests/test_pricing_router.py`
  - `tests/test_image_processor.py`
  - `tests/test_vision_analysis.py`

## 15. Kết luận

Tính năng định giá xe hiện đã có đủ luồng end-to-end ở mức kỹ thuật:

- nhận ảnh và cấu hình xe,
- phân tích tình trạng,
- lấy dữ liệu thị trường,
- tính giá nhập đề xuất,
- trả JSON kết quả,
- có UI test để thao tác thủ công.

Nói ngắn gọn, đây là một phiên bản đã có thể dùng để thử nghiệm nghiệp vụ định giá, với cơ chế fallback tương đối đầy đủ khi vision hoặc LLM gặp lỗi.
