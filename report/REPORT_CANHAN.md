# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Hoàng Anh Khôi  
**MSSV:** 2A202602404  
**Nhóm:** Bét Bét Bét  
**Ngày:** 20/9/2026  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiến gần về 1.0) thể hiện hai vector có hướng gần như trùng nhau trong không gian vector đa chiều, đồng nghĩa với việc hai đoạn văn bản mang hàm ý hoặc chủ đề ngữ nghĩa rất gần gũi nhau, bất kể độ dài ngắn khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: “Mèo đang ngủ trên thảm”
- Câu B: “Một chú mèo đang nằm lim dim trên tấm thảm”
- Tại sao tương đồng: Cả hai câu đều mô tả hành động tương tự (ngủ/nằm lim dim), chủ thể tương tự (mèo), và địa điểm tương tự (trên thảm).

**Ví dụ có độ tương tự THẤP:**
- Câu A: “Mèo đang ngủ trên thảm”
- Câu B: “Trái cây sấy khô được bày trên kệ gỗ”
- Tại sao khác: Chủ thể, hành động và ngữ cảnh hoàn toàn khác nhau; không có yếu tố chung nào về ý nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị phụ thuộc rất lớn vào độ dài tuyệt đối của văn bản (độ dài vector norm) — một đoạn văn dài và một câu tóm tắt ngắn cùng nói về một nội dung sẽ có khoảng cách Euclid rất xa nhau. Trong khi đó, Cosine Similarity chuẩn hóa độ dài vector và chỉ đo góc giữa chúng, giúp tập trung thuần túy vào sự tương đồng ngữ nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước nhảy (step) giữa các chunk: $\text{step} = \text{chunk\_size} - \text{overlap} = 500 - 50 = 450$ ký tự.
> - Áp dụng công thức: $\text{số lượng chunk} = \left\lceil \frac{\text{độ dài tài liệu} - \text{độ chồng chéo}}{\text{kích thước chunk} - \text{độ chồng chéo}} \right\rceil = \left\lceil \frac{10000 - 50}{500 - 50} \right\rceil = \left\lceil \frac{9950}{450} \right\rceil = \lceil 22.111 \rceil = 23$.
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - Khi overlap tăng lên 100: $\text{số lượng chunk} = \left\lceil \frac{10000 - 100}{500 - 100} \right\rceil = \left\lceil \frac{9900}{400} \right\rceil = \lceil 24.75 \rceil = 25$ chunks (tăng thêm 2 chunks).
> - Tăng độ chồng chéo giúp bảo toàn ngữ cảnh nằm tại ranh giới cắt giữa các chunk liên tiếp, tránh tình trạng một câu hoặc một mệnh đề bị xé đôi làm mất thông tin quan trọng khi retrieval.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex lookbehind `r"(?<=[.!?])\s"` kết hợp tách dấu câu để phân ranh giới câu mà không làm mất dấu kết thúc câu. Xử lý các edge case như chuỗi rỗng/chỉ chứa khoảng trắng, loại bỏ khoảng trắng thừa ở mỗi câu bằng `.strip()`, và gom đúng số lượng câu tối đa (`max_sentences_per_chunk`) vào mỗi chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng chiến lược chia đệ quy ưu tiên từ mức cấu trúc lớn đến nhỏ: `["\n\n", "\n", ". ", " ", ""]`. Base case là khi chuỗi có độ dài nhỏ hơn hoặc bằng `chunk_size` hoặc đã duyệt hết danh sách separator (lúc đó cắt cưỡng bức theo slice). Quá trình gom các đoạn con (splits) sử dụng một `buffer` để ghép các đoạn nhỏ lại với nhau miễn là không vượt quá `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi document được chuyển thành record chuẩn hóa gồm `id`, `content`, `metadata` và `embedding` (sinh ra từ `self._embedding_fn`). Nếu có thư viện ChromaDB thì lưu vào Chroma collection; nếu không có thì lưu vào danh sách RAM `self._store`. Với `search`, câu truy vấn được embed thành vector rồi tính cosine similarity (hoặc dot product khi vector đã chuẩn hóa) với toàn bộ vector trong kho, sau đó sắp xếp giảm dần để lấy ra `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Luôn thực hiện lọc metadata trước (**pre-filtering**) để loại bỏ các chunk không thỏa mãn điều kiện `metadata_filter` rồi mới thực hiện tính toán độ tương đồng vector, giúp tăng tốc độ tìm kiếm và độ chính xác. Với `delete_document`, lọc và xóa tất cả chunk có `metadata['doc_id'] == doc_id` (hoặc `id == doc_id`), trả về `True` nếu có ít nhất một bản ghi bị xóa, ngược lại trả về `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Nhận câu hỏi từ người dùng, gọi `self.store.search(question, top_k)` để thu thập các đoạn context liên quan nhất. Lắp ghép các đoạn văn bản này thành một block `--- Ngữ cảnh ---` rõ ràng kèm lời nhắc hệ thống (chỉ trả lời dựa trên ngữ cảnh được cung cấp, không bịa đặt) và `--- Câu hỏi ---`, sau đó chuyển toàn bộ prompt này cho hàm `self.llm_fn` để sinh câu trả lời hoàn chỉnh.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.7, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\VinUni\K4-DAY07-PhamHoangAnhKhoi-2A202602404
plugins: anyio-4.12.1, langsmith-0.12.4, asyncio-1.4.0
collected 42 items

tests/test_solution.py ..........................................        [100%]

============================= 42 passed in 0.12s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (Mock) | Điểm kỳ vọng (Semantic) | Đúng theo ngữ nghĩa? |
|------|-----------|-----------|---------|---------------------|--------------------------|-----------------------|
| 1 | Sinh viên có thể đăng ký học phần trực tuyến qua portal. | Người học thực hiện đăng ký môn học online trên cổng thông tin. | cao | -0.0055 | ~0.85 – 0.95 | Đúng (ngữ nghĩa) |
| 2 | Quy định về thời hạn đóng học phí học kỳ chính. | Thời gian và mức tiền phải nộp học phí học kỳ này. | cao | -0.0170 | ~0.80 – 0.90 | Đúng (ngữ nghĩa) |
| 3 | Thư viện mở cửa phục vụ bạn đọc mượn giáo trình. | Trạm y tế trường học cung cấp dịch vụ khám chữa bệnh sơ cứu. | thấp | -0.0009 | ~0.10 – 0.25 | Đúng (ngữ nghĩa) |
| 4 | Thủ tục nộp đơn phúc khảo bài thi học phần. | Sinh viên gửi yêu cầu khiếu nại kết quả điểm thi kết thúc môn. | cao | -0.1737 | ~0.80 – 0.92 | Đúng (ngữ nghĩa) |
| 5 | Tiêu chuẩn xét cấp học bổng khuyến khích học tập. | Quy định về việc giữ trật tự và không làm mất sách thư viện. | thấp | 0.1133 | ~0.05 – 0.20 | Đúng (ngữ nghĩa) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là khi dùng `MockEmbedder` (dựa trên thuật toán băm chuỗi MD5), các cặp câu đồng nghĩa 1, 2, 4 lại có điểm tương đồng rất thấp hoặc âm (quanh mức 0). Điều này chỉ ra rằng thuật toán băm cú pháp chỉ so sánh bề mặt ký tự ngẫu nhiên; để hiểu được ngữ nghĩa thực tế (semantic meaning), bắt buộc phải dùng các mô hình ngôn ngữ được huấn luyện trên không gian vector dày đặc (dense embeddings như Sentence-Transformers, OpenAI hoặc Gemini).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`). Dữ liệu thử nghiệm từ thư mục quy định đại học `data/quy-dinh-dai-hoc/`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sinh viên muốn nộp đơn phúc khảo bài thi kết thúc học phần cần làm gì? | `phuc-khao-diem-thi-47.md`: Hướng dẫn sinh viên nộp đơn online trong vòng 7 ngày sau khi công bố điểm thi. | 0.2716 | Có | Sinh viên thực hiện nộp đơn xin phúc khảo trực tuyến trên portal trong thời hạn 7 ngày làm việc kể từ ngày công bố điểm. |
| 2 | Tiêu chuẩn và điều kiện để được xét học bổng khuyến khích học tập là gì? | `hoc-bong-khuyen-khich-hoc-tap-76.md`: Đạt điểm học tập và điểm rèn luyện từ loại Khá trở lên, không nợ môn. | 0.3441 | Có | Sinh viên cần tích lũy đủ số tín chỉ quy định, điểm trung bình học kỳ từ Khá trở lên và điểm rèn luyện loại Khá/Tốt trở lên. |
| 3 | Thư viện cung cấp các dịch vụ mượn tài liệu và đặt phòng học nhóm nào? | `93.md`: Giới thiệu SmartLib, ứng dụng di động UEH Library, dịch vụ mượn sách về nhà và đặt phòng nhóm trực tuyến. | 0.3542 | Có | Thư viện hỗ trợ đọc tại chỗ, mượn về nhà, gia hạn qua ứng dụng UEH Library và đăng ký phòng học nhóm qua cổng thông tin. |
| 4 | Thời hạn và các hình thức đóng học phí dành cho sinh viên quy định ra sao? | `dong-hoc-phi-35.md`: Quy định các đợt nộp học phí, thanh toán qua cổng thanh toán số hoặc chuyển khoản ngân hàng. | 0.3161 | Có | Sinh viên theo dõi thông báo đầu kỳ và nộp học phí đúng hạn qua cổng thanh toán trực tuyến hoặc ngân hàng liên kết. |
| 5 | Quy định số tín chỉ tối đa và tối thiểu khi đăng ký học phần trong một học kỳ? *(Có filter: audience=student)* | `quy-dinh-ve-dang-ky-hoc-phan-571.md`: Sinh viên bình thường đăng ký tối thiểu 14 tín chỉ, tối đa 25 tín chỉ mỗi học kỳ chính. | 0.2923 | Có | Trong học kỳ chính, sinh viên phải đăng ký tối thiểu 14 tín chỉ và tối đa 25 tín chỉ (trừ học kỳ cuối hoặc diện đặc biệt). |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được rằng việc tiền xử lý văn bản (lọc bỏ các thẻ HTML, header/footer của trang web crawl) và chiến lược chia nhỏ chunk theo ngữ cảnh (Recursive/Section chunking) có ảnh hưởng quyết định đến chất lượng RAG hơn cả việc tăng kích thước chunk. Ngoài ra, việc kết hợp metadata filtering trước khi search giúp giảm thiểu triệt để nhiễu thông tin từ các đối tượng không liên quan.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |

