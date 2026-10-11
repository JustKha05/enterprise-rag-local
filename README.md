# Enterprise RAG Assistant

Ứng dụng hỏi đáp tài liệu chạy local với Ollama, Qdrant và FastAPI.
Người dùng chọn bộ tài liệu, đặt câu hỏi và kiểm tra nguồn hỗ trợ câu trả lời.

Project sử dụng các model pretrained, chưa fine-tune và không cần API
inference trả phí.

## Tính năng

- Giao diện web bằng tiếng Việt.
- Chọn NIST CSF 2.0 hoặc Kubernetes Deployments.
- Truy xuất tài liệu và tạo câu trả lời có nhãn nguồn.
- Xem nội dung nguồn, liên kết gốc và số trang PDF.
- Hiển thị thời gian tìm tài liệu và tạo câu trả lời.
- Đánh giá bốn model bằng cùng bộ bằng chứng được lưu cố định.

## Dữ liệu

| Bộ tài liệu | Phạm vi | Phiên bản |
|---|---|---|
| NIST | Functions, Profiles, Tiers, quản lý rủi ro an ninh mạng | CSF 2.0 |
| Kubernetes | Deployments, rollout, rollback, revision | Snapshot `e96866675691ab050bc2f5dffc19f21f9fc8c646` |

Tài liệu synthetic được dùng cho các lượt kiểm thử phát triển riêng.

## Ngôn ngữ

- Giao diện web: tiếng Anh.
- Tài liệu NIST và Kubernetes: tiếng Anh.
- Câu hỏi tiếng Anh đã được kiểm thử.
- Truy xuất với câu hỏi tiếng Việt và các ngôn ngữ khác chưa được đánh giá.
- Model được yêu cầu trả lời theo ngôn ngữ câu hỏi; chất lượng ngoài tiếng Anh chưa được xác nhận.

## Kiến trúc

Tài liệu → loader → chia chunk → embedding → Qdrant
→ truy xuất bằng chứng → Ollama → API → web.

Embedding: `sentence-transformers/all-MiniLM-L6-v2`,
384 chiều, cosine similarity.

## Model

| Ollama tag | Vai trò trong project | Reasoning |
|---|---|---|
| `phi4-mini:3.8b` | Lựa chọn nhẹ để so sánh | Không cấu hình riêng |
| `qwen3:8b` | Lựa chọn mặc định cho API demo | Tắt |
| `deepseek-r1:8b` | So sánh với reasoning | Bật |
| `gemma4:12b` | So sánh model lớn hơn | Tắt |

Model được chọn khi khởi động server qua `GENERATION_MODEL`.

## Đánh giá NIST — lượt v2

Sáu câu hỏi phát triển/model, cùng bằng chứng truy xuất `top-k=6`
và cùng nội dung prompt.

| Model | Trung bình/câu | Tổng thời gian 6 câu | Vấn đề quan sát được |
|---|---:|---:|---|
| Phi | 87,72 giây | 8,77 phút | Q05 từ chối sai; lỗi citation và nhãn A/B |
| Qwen | 191,38 giây | 19,14 phút | Q02 citation chưa hỗ trợ đầy đủ |
| DeepSeek | 290,17 giây | 29,02 phút | Q02 thiếu điều kiện; Q04 gắn thừa nguồn |
| Gemma | 399,30 giây | 39,93 phút | Q04 có diễn đạt rộng hơn bằng chứng |

Tổng thời gian gọi model của lượt NIST v2: khoảng 1,61 giờ.

Thời gian gồm xử lý prompt và sinh output, không gồm tải model,
index tài liệu hoặc các lượt thử khác. DeepSeek bật reasoning và
có giới hạn output 1200 token; các model còn lại là 400 token.
Đây là so sánh các cấu hình sử dụng thực tế.

Máy đánh giá: Windows, RAM 15,7 GB, inference bằng CPU.

Đây là kết quả phát triển trên bộ nhỏ, không phải benchmark độc lập.
Chưa công bố accuracy tổng hợp hoặc memory benchmark.

## Cài đặt

Cần Python, Docker Desktop và Ollama.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

docker compose up -d
ollama pull qwen3:8b
```

Index hai bộ tài liệu:

```powershell
$env:QDRANT_COLLECTION = "nist_csf2_minilm_v1"
.\.venv\Scripts\python.exe -m scripts.index_nist

$env:QDRANT_COLLECTION = "kubernetes_minilm_v1"
.\.venv\Scripts\python.exe -m scripts.index_kubernetes
```

Các file nguồn và metadata tương ứng phải có trong `data/raw/`.

## Chạy web

```powershell
$env:GENERATION_MODEL = "qwen3:8b"

.\.venv\Scripts\python.exe -m uvicorn app.api.main:app `
    --host 127.0.0.1 `
    --port 8000
```

- Web: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- `GET /health`: trạng thái API và cấu hình.
- `POST /ask`: câu hỏi, bộ tài liệu và số đoạn truy xuất.

## Cách dùng

1. Chọn bộ tài liệu.
2. Nhập câu hỏi hoặc chọn câu hỏi mẫu.
3. Chờ hệ thống xử lý.
4. Đọc câu trả lời và mở nguồn tương ứng để kiểm tra.

Ví dụ NIST:
`Should CSF Tiers replace an organization's cybersecurity risk management methodology?`

Ví dụ Kubernetes:
`How do I roll back nginx-deployment to revision 2?`

## Giới hạn

- Chạy CPU nên một câu hỏi có thể mất vài phút.
- Mỗi lần xử lý một câu hỏi; request khác nhận HTTP 503 khi đang bận.
- Câu trả lời và citation vẫn có thể sai.
- Mỗi câu hỏi độc lập, chưa có bộ nhớ hội thoại.
- Không chứa thông tin nội bộ riêng của doanh nghiệp.
- Chưa có upload tài liệu hoặc truy vấn kết hợp hai bộ.
- Bản hiện tại phục vụ local, chưa phải triển khai production.