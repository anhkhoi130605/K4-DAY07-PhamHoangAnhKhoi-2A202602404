# Ngày 7 — Bài tập
## Nền tảng Dữ liệu: Embedding & Vector Store | Bài tập thực hành

---

## Phần 1 — Khởi động (Cá nhân)

### Bài tập 1.1 — Cosine Similarity (Độ tương tự Cosine) bằng ngôn ngữ đời thường

Không yêu cầu toán học — hãy giải thích về mặt khái niệm:

- Điều gì xảy ra khi hai đoạn văn bản có độ tương tự cosine cao?
- Đưa ra một ví dụ cụ thể về hai câu sẽ có độ tương tự CAO và hai câu sẽ có độ tương tự THẤP.
- Tại sao độ tương tự cosine lại được ưu tiên hơn khoảng cách Euclid (Euclidean distance) đối với text embeddings?

> **Ghi kết quả vào:** Báo cáo — Phần 1 (Khởi động)

- Khi hai đoạn văn bản có độ tương tự cosine cao (tiến gần về 1), điều đó có nghĩa là chúng rất tương đồng về mặt ý nghĩa hoặc chủ đề trong không gian ngữ nghĩa, ngay cả khi chúng sử dụng các từ ngữ hoàn toàn khác nhau. Model vector hóa hiểu rằng hai đoạn văn này đang hướng về cùng một góc nhìn hoặc ngữ cảnh.
- Độ tương tự CAO:
    
    Câu A: "Hôm nay trời nhiều mây và có thể sẽ mưa to."
    
    Câu B: "Dự báo thời tiết báo sắp có dông lớn chiều nay."
    (Hai câu dùng từ vựng khác nhau nhưng mang cùng một thông tin/ngữ cảnh).
    
    Độ tương tự THẤP:
    
    Câu A: "Hôm nay trời nhiều mây và có thể sẽ mưa to."
    
    Câu B: "Công thức làm món sườn xào chua ngọt rất đơn giản."
    (Hai câu nói về hai chủ đề tách biệt hoàn toàn, không liên quan ngữ nghĩa).
- Cosine Similarity chỉ đo góc, bỏ qua độ dài: Khoảng cách Euclid đo độ lệch tuyệt đối giữa hai điểm trong không gian, do đó rất nhạy cảm với độ dài văn bản. Một câu ngắn và một đoạn văn dài nói về cùng một chủ đề (ví dụ: một câu tóm tắt và một bài báo chi tiết) sẽ bị khoảng cách Euclid đánh giá là "xa nhau" chỉ vì đoạn dài chứa nhiều từ hơn, làm độ dài vector bị phóng to.

  Tập trung vào ngữ nghĩa cốt lõi: Cosine Similarity chỉ quan tâm đến hướng đi (góc giữa hai vector) chứ không quan tâm độ dài (magnitude). Nhờ vậy, nó nhận diện chính xác hai văn bản có cùng ý nghĩa dù độ dài của chúng chênh lệch lớn.
### Bài tập 1.2 — Bài toán tính toán Chunking

- Một tài liệu có độ dài 10,000 ký tự. Bạn tiến hành chia nhỏ (chunk) với `chunk_size=500` (kích thước chunk), `overlap=50` (độ chồng chéo). Bạn dự kiến sẽ có bao nhiêu chunks?
- Công thức: `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
- Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk sẽ thay đổi như thế nào? Tại sao bạn lại muốn tăng độ chồng chéo?

> **Ghi kết quả vào:** Báo cáo — Phần 1 (Khởi động)

- Dự kiến sẽ có 23 chunks
- Số lượng chunk sẽ tăng lên từ 23 thành 25 chunks
- Bảo toàn ngữ cảnh liền mạch: Tránh tình trạng thông tin quan trọng bị cắt đứt gãy ở ranh giới giữa hai chunk (ví dụ: một câu dài, một định nghĩa, hoặc mối liên hệ giữa chủ ngữ ở chunk trước và vị ngữ ở chunk sau).

    Tăng độ chính xác khi truy vấn (Retrieval): Giúp embedding vector của mỗi chunk chứa đựng đầy đủ ngữ cảnh hơn, từ đó cải thiện điểm tương đồng ngữ nghĩa (cosine similarity) khi tìm kiếm thông tin bằng RAG.

    Đánh đổi: Tăng overlap sẽ sinh ra nhiều chunk hơn, kéo theo chi phí tính toán embedding và dung lượng lưu trữ vector database tăng nhẹ.

## Phần 2 — Lập trình cốt lõi (Cá nhân)

Hoàn thành tất cả các TODOs trong `src/chunking.py`, `src/store.py`, và `src/agent.py`. `Document` dataclass và `FixedSizeChunker` đã được triển khai sẵn làm ví dụ — hãy đọc kỹ để hiểu cấu trúc trước khi lập trình phần còn lại.

Chạy `pytest tests/` để kiểm tra tiến độ.

### Danh sách cần làm (Checklist)
- [x] `Document` dataclass — ĐÃ TRIỂN KHAI SẴN
- [x] `FixedSizeChunker` — ĐÃ TRIỂN KHAI SẴN
- [ ] `SentenceChunker` — tách dựa trên ranh giới câu, nhóm lại thành các chunks
- [ ] `RecursiveChunker` — thử nghiệm các dấu phân cách (separators) theo thứ tự, thực hiện đệ quy trên các đoạn có kích thước quá lớn
- [ ] `compute_similarity` — công thức tính độ tương tự cosine kèm cơ chế bảo vệ chia cho 0
- [ ] `ChunkingStrategyComparator` — gọi cả ba chiến lược, tính toán các chỉ số thống kê
- [ ] `EmbeddingStore.__init__` — khởi tạo store (lưu trữ trong bộ nhớ hoặc ChromaDB)
- [ ] `EmbeddingStore.add_documents` — nhúng (embed) và lưu trữ từng tài liệu
- [ ] `EmbeddingStore.search` — nhúng truy vấn, xếp hạng theo tích vô hướng (dot product)
- [ ] `EmbeddingStore.get_collection_size` — trả về số lượng
- [ ] `EmbeddingStore.search_with_filter` — lọc theo siêu dữ liệu (metadata), sau đó tìm kiếm
- [ ] `EmbeddingStore.delete_document` — xóa tất cả các chunks của một doc_id
- [ ] `KnowledgeBaseAgent.answer` — truy xuất (retrieve) + tạo prompt + gọi LLM

> **Nộp code:** thư mục `src/`
> **Ghi lại hướng tiếp cận vào:** Báo cáo — Phần 4 (Hướng tiếp cận của tôi)

---

## Phần 3 — So Sánh Chiến Lược Truy Xuất (Nhóm)

### Bài tập 3.0 — Chuẩn Bị Tài Liệu (Giờ đầu tiên)

Mỗi nhóm chọn một chủ đề (domain) và chuẩn bị bộ tài liệu:

**Bước 1 — Chọn chủ đề:** FAQ (Câu hỏi thường gặp), SOP (Quy trình chuẩn), chính sách, tài liệu kỹ thuật, công thức nấu ăn, luật, y tế, v.v.

**Bước 2 — Thu thập 5-10 tài liệu.** Chỉ dùng nguồn công khai hoặc nguồn nhóm có quyền sử dụng; lưu dưới dạng `.txt` hoặc `.md` vào thư mục `data/`.

**Quy tắc dữ liệu bắt buộc:**
- Không đưa dữ liệu cá nhân, thông tin đăng nhập, hồ sơ nội bộ hoặc nội dung có quyền sử dụng không rõ ràng vào repo.
- Với mỗi tài liệu, ghi `source_url`, `retrieved_at` (ngày lấy) và `document_version` hoặc ngày hiệu lực nếu nguồn có nêu.
- Đưa ba trường trên vào siêu dữ liệu (metadata) khi nạp (ingest); chúng giúp kiểm tra độ mới và truy vết câu trả lời.

> **Mẹo chuyển PDF sang Markdown:**
> - `pip install marker-pdf` → `marker_single input.pdf output/` (chất lượng cao, giữ cấu trúc)
> - `pip install pymupdf4llm` → `pymupdf4llm.to_markdown("input.pdf")` (nhanh, đơn giản)
> - Hoặc sao chép-dán (copy-paste) nội dung từ PDF/web vào file `.txt`

Ghi vào bảng:

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bước 3 — Thiết kế cấu trúc metadata (metadata schema):** Mỗi tài liệu cần `source_url`, `retrieved_at`, `document_version` và ít nhất 2 trường hữu ích cho việc truy xuất (ví dụ: `audience`, `department`, `category`, `language`, `difficulty`).

> **Ghi kết quả vào:** Báo cáo — Phần 2 (Lựa chọn tài liệu)

---

### Bài tập 3.1 — Thiết Kế Chiến Lược Truy Xuất (Mỗi người thử riêng)

Mỗi thành viên **tự chọn chiến lược riêng** để thử nghiệm trên cùng bộ tài liệu của nhóm.

**Bước 1 — Đường cơ sở (Baseline):** Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu. Ghi lại kết quả.

**Bước 2 — Chọn hoặc thiết kế chiến lược của bạn:**
- Dùng 1 trong 3 chiến lược có sẵn (built-in strategies) với tham số tối ưu, HOẶC
- Thiết kế chiến lược tùy chỉnh cho chủ đề của bạn (ví dụ: chia nhỏ theo cặp Câu hỏi-Đáp án, theo các phần (sections), theo tiêu đề (headers))
- Mỗi thành viên nên thử một chiến lược **khác nhau** để có cơ sở so sánh

```python
class CustomChunker:
    """Chiến lược chia nhỏ tùy chỉnh cho [chủ đề của bạn].

    Lý do thiết kế: [giải thích tại sao chiến lược này phù hợp với dữ liệu của bạn]
    """

    def chunk(self, text: str) -> list[str]:
        # Viết mã nguồn của bạn ở đây
        ...
```

**Bước 3 — So sánh:** So sánh chiến lược tùy chỉnh/được tinh chỉnh (custom/tuned strategy) với đường cơ sở (baseline) trên cùng tài liệu.

> **Ghi kết quả vào:** Báo cáo — Phần 3 (Chiến lược chia nhỏ - Chunking Strategy)

---

### Bài tập 3.2 — Chuẩn Bị Câu Hỏi Đánh Giá (Benchmark Queries)

Mỗi nhóm viết **đúng 5 câu hỏi đánh giá** kèm theo **câu trả lời chuẩn (gold answers)**.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

**Yêu cầu:**
- Câu hỏi phải đa dạng (không hỏi 5 câu có nội dung/cấu trúc giống hệt nhau)
- Câu trả lời chuẩn phải cụ thể và có thể kiểm chứng (verify) từ tài liệu
- Ít nhất 1 câu hỏi yêu cầu lọc bằng metadata (metadata filtering) để trả lời tốt

> **Ghi kết quả vào:** Báo cáo — Phần 6 (Kết quả — Câu hỏi đánh giá & Câu trả lời chuẩn)

---

### Bài tập 3.3 — Dự Đoán Độ Tương Tự Cosine (Cá nhân)

Gọi hàm `compute_similarity()` trên 5 cặp câu. **Trước khi chạy**, hãy dự đoán xem cặp câu nào sẽ có độ tương tự cao nhất/thấp nhất. Ghi lại các dự đoán của bạn và kết quả thực tế. Suy ngẫm xem điều gì khiến bạn ngạc nhiên nhất.

> **Ghi kết quả vào:** Báo cáo — Phần 5 (Dự đoán độ tương tự)

---

### Bài tập 3.4 — Chạy Đánh Giá & So Sánh Trong Nhóm

**Bước 1:** Mỗi thành viên chạy 5 câu hỏi đánh giá với chiến lược riêng. Ghi lại kết quả top-3 cho mỗi câu hỏi.

**Bước 2:** So sánh kết quả trong nhóm:
- Chiến lược nào cho việc truy xuất tốt nhất? Tại sao?
- Có câu hỏi nào mà chiến lược A tốt hơn B nhưng lại ngược lại ở câu hỏi khác không?
- Lọc bằng metadata (Metadata filtering) có giúp ích không?

**Bước 3:** Thảo luận và rút ra bài học — chuẩn bị cho phần demo (thuyết trình) với các nhóm khác.

> **Ghi kết quả vào:** Báo cáo — Phần 6 (Kết quả)
> **Gợi ý đánh giá:** xem danh sách kiểm tra ngắn trong `README.md` mục **Cách Tự Đánh Giá Kết Quả Retrieval** hoặc chi tiết hơn trong file `docs/EVALUATION.md`.

---

### Bài tập 3.5 — Phân Tích Lỗi (Failure Analysis)

Tìm ít nhất **1 trường hợp lỗi (failure case)** trong quá trình so sánh. Mô tả:
- Câu hỏi nào mà quá trình truy xuất gặp thất bại?
- Tại sao? (do chunk quá nhỏ/quá lớn, thiếu metadata, câu hỏi mơ hồ, v.v.)
- Đề xuất cải thiện?

> **Ghi kết quả vào:** Báo cáo — Phần 7 (Những gì tôi học được)
> **Gợi ý:** phân tích lỗi nên tham chiếu từ các góc nhìn như độ chính xác (precision), tính mạch lạc của chunk (chunk coherence), tính hữu dụng của metadata, và chất lượng thông tin nền (grounding quality).

---

## Danh Sách Kiểm Tra Nộp Bài (Submission Checklist)

- [ ] Vượt qua tất cả các bài kiểm thử (tests): `pytest tests/ -v`
- [ ] Cập nhật thư mục `src/` (cá nhân)
- [ ] Hoàn thành báo cáo nhóm (`report/REPORT_NHOM.md` — 1 file/nhóm)
- [ ] Hoàn thành báo cáo cá nhân (`report/REPORT_CANHAN.md` — 1 file/sinh viên)
