# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** BetBetBet  
**Thành viên:** 
1. Nguyễn Trung Kiên (Lead / System Architect) — MSSV: 2A202602764
2. Phạm Hoàng Anh Khôi (Phụ trách HeadingChunker — Vai bắt buộc L3A) — MSSV: 2A202602404
3. Hoàng Văn Tài (Phụ trách RecursiveChunker) — MSSV: 2A202602400
4. Bùi Đăng Khoa (Phụ trách FixedSizeChunker) — MSSV: 2A202602617
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 35** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) .

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy chế đào tạo, học bổng & dịch vụ sinh viên Đại học Kinh tế TP. Hồ Chí Minh (UEH)

**Tại sao nhóm chọn chủ đề này?**
> Văn bản quy chế và hướng dẫn sinh viên của UEH có cấu trúc pháp lý rõ ràng (phân cấp theo Mục, Điều khoản, Quy trình), chứa nhiều dữ liệu định lượng quan trọng (tỷ lệ học bổng, thời hạn nộp đơn phúc khảo, các cổng nộp học phí) và phục vụ nhiều nhóm đối tượng (`audience`: sinh viên, cán bộ viên chức). Đây là tập dữ liệu thực tế lý tưởng để đánh giá khả năng bảo toàn ngữ cảnh của các chiến lược chunking và hiệu quả của cơ chế lọc tiền xử lý (metadata pre-filtering).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|:--------:|-----------------|
| 1 | Chương trình chuẩn (CTTT quốc tế UEH) (`23`) | `https://hotro.ueh.edu.vn/bai-viet/23` | 2026-09-19 / 2024-2025 | 1,033 | `audience: student`, `dept: academic-affairs`, `cat: curriculum` |
| 2 | Thư viện UEH (`93`) | `https://hotro.ueh.edu.vn/bai-viet/93` | 2026-09-19 / 2024-2025 | 2,233 | `audience: student`, `dept: library`, `cat: facilities` |
| 3 | Đánh giá kết quả rèn luyện SV (`danh-gia-ket-qua-ren-luyen-sinh-vien-72`) | `https://hotro.ueh.edu.vn/bai-viet/danh-gia-ket-qua-ren-luyen-sinh-vien-72` | 2026-09-19 / 2024-2025 | 6,605 | `audience: student`, `dept: student-affairs`, `cat: conduct` |
| 4 | Đóng học phí (`dong-hoc-phi-35`) | `https://hotro.ueh.edu.vn/bai-viet/dong-hoc-phi-35` | 2026-09-19 / 2024-2025 | 3,656 | `audience: student`, `dept: finance`, `cat: tuition` |
| 5 | Học bổng Khuyến khích học tập (`hoc-bong-khuyen-khich-hoc-tap-76`) | `https://hotro.ueh.edu.vn/bai-viet/hoc-bong-khuyen-khich-hoc-tap-76` | 2026-09-19 / 2024-2025 | 4,721 | `audience: student`, `dept: student-affairs`, `cat: scholarship` |
| 6 | Phúc khảo điểm thi (`phuc-khao-diem-thi-47`) | `https://hotro.ueh.edu.vn/bai-viet/phuc-khao-diem-thi-47` | 2026-09-19 / 2024-2025 | 660 | `audience: student`, `dept: testing`, `cat: examination` |
| 7 | Quy định đăng ký học phần (`quy-dinh-ve-dang-ky-hoc-phan-571`) | `https://hotro.ueh.edu.vn/bai-viet/quy-dinh-ve-dang-ky-hoc-phan-571` | 2026-09-19 / 2024-2025 | 8,491 | `audience: student`, `dept: academic-affairs`, `cat: registration` |
| 8 | Thông tin Trạm Y tế (`thong-tin-tram-y-te-99`) | `https://hotro.ueh.edu.vn/bai-viet/thong-tin-tram-y-te-99` | 2026-09-19 / 2024-2025 | 3,027 | `audience: student`, `dept: health`, `cat: medical` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng từ Cổng hỗ trợ người học UEH (`hotro.ueh.edu.vn`), không chứa dữ liệu cá nhân hay thông tin nội bộ mật.
- [x] Mỗi tài liệu có đủ `doc_id`, `source_url`, `retrieved_at`, `document_version` trong phần frontmatter YAML và được đồng bộ trong `sources.csv`.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | String | `hoc-bong-khuyen-khich-hoc-tap-76` | Định danh tài liệu nguồn duy nhất để xác định chunk thuộc văn bản nào và đo lường Hit@1/Hit@3 |
| `title` | String | `Học bổng Khuyến khích học tập` | Hiển thị tiêu đề chuẩn cho Agent trích dẫn nguồn khi trả lời người dùng |
| `source_url` | String | `https://hotro.ueh.edu.vn/bai-viet/76` | Cung cấp link gốc minh bạch, phục vụ kiểm chứng thực tế và dẫn nguồn (citation) |
| `retrieved_at` | String | `2026-09-19` | Kiểm soát tính cập nhật và hiệu lực của thông tin quy chế theo mốc thời gian |
| `document_version`| String | `2024-2025` | Phân biệt phiên bản quy định giữa các năm học, tránh lấy nhầm quy định cũ đã hết hiệu lực |
| `audience` | String | `student` / `faculty` | **Cốt lõi cho Metadata Filtering**: Ngăn ngừa truy xuất nhầm quy định của nhóm người học này sang nhóm người khác |
| `department` | String | `finance`, `student-affairs`, `library` | Cho phép lọc tìm kiếm theo phòng ban phụ trách chuyên môn |
| `category` | String | `scholarship`, `tuition`, `registration` | Phân loại chủ đề nghiệp vụ để thu hẹp không gian tìm kiếm trước khi tính cosine similarity |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

So sánh định lượng 4 chiến lược của các thành viên trên 2 tài liệu tiêu biểu (`hoc-bong-khuyen-khich-hoc-tap-76` và `dong-hoc-phi-35`):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|-----------------------|:--------------:|:-----------------:|--------------------------|
| `hoc-bong-khuyen-khich-hoc-tap-76` | FixedSizeChunker (`size=300, ov=50`) | 18 | 291.8 ký tự | Kém (ranh giới cắt ngang điều kiện, đứt gãy câu) |
| `hoc-bong-khuyen-khich-hoc-tap-76` | FixedSizeChunker (`size=500, ov=100`) | 11 | 491.2 ký tự | Trung bình (giảm đứt gãy nhờ overlap nhưng loãng vector) |
| `hoc-bong-khuyen-khich-hoc-tap-76` | RecursiveChunker (`chunk_size=400`) | 15 | 291.7 ký tự | Tốt (bảo toàn cấu trúc đoạn và danh sách gạch đầu dòng) |
| `hoc-bong-khuyen-khich-hoc-tap-76` | HeadingChunker (`max_chunk=500`) | 10 | 466.6 ký tự | Xuất sắc (bảo toàn từng Điều, tái tiêm tiêu đề Điều vào mảnh con) |
| `dong-hoc-phi-35` | FixedSizeChunker (`size=300, ov=50`) | 14 | 289.4 ký tự | Kém (xé ngang quy trình các bước nộp tiền) |
| `dong-hoc-phi-35` | FixedSizeChunker (`size=500, ov=100`) | 9 | 466.8 ký tự | Trung bình (bao phủ đủ bước nhưng chunk dài, nhiều nhiễu) |
| `dong-hoc-phi-35` | RecursiveChunker (`chunk_size=400`) | 11 | 307.4 ký tự | Tốt (gom gọn từng bước hướng dẫn thanh toán) |
| `dong-hoc-phi-35` | HeadingChunker (`max_chunk=500`) | 8 | 436.2 ký tự | Xuất sắc (chia đúng từng Phương thức thanh toán riêng biệt) |

### Chiến lược của từng thành viên

> Nhóm phân công rõ ràng: Lead (Kiên) phụ trách kiến trúc RAG Pipeline, làm sạch dữ liệu và xây dựng bộ Benchmark 5 câu hỏi; 3 thành viên còn lại chia nhau kiểm tra 3 chiến lược chunking trong `bench.py` (bao gồm vai bắt buộc HeadingChunker).

**Nguyễn Trung Kiên (Lead)**
- **Vai trò:** Thiết kế toàn bộ hạ tầng RAG, làm sạch và chuẩn hóa 8 tài liệu quy định UEH, xây dựng bộ 5 Benchmark Queries & Gold Answers, viết kịch bản đánh giá tự động `bench.py` và chủ trì Báo cáo nhóm.

**Phạm Hoàng Anh Khôi (Phụ trách HeadingChunker)**
- **Loại chiến lược:** `HeadingChunker (max_chunk_size=500)`
- **Mô tả & lý do chọn cho chủ đề này:** Tận dụng cấu trúc văn bản pháp lý/quy chế đại học luôn được chia theo các đề mục `#`, `##` và `Điều ...`. Mỗi Điều là một đơn vị ngữ nghĩa độc lập. Nếu Điều dài quá 500 ký tự thì fallback sang Recursive đồng thời **chèn lại tiêu đề Điều vào đầu mỗi mảnh con** để bảo toàn tuyệt đối ngữ cảnh (Context Re-injection).
- **Code snippet:**
```python
class HeadingChunker:
    """
    Chia nhỏ văn bản theo tiêu đề/mục (Heading/Section-based chunking) cho sổ tay hoặc quy định đại học.
    
    Đặc điểm:
    - Nhận diện tiêu đề Markdown (#, ##, ###, ####) hoặc các mục pháp quy (Điều ..., Chương ..., Mục ..., hoặc 1. 2. 3.)
    - Giữ lại Heading ở đầu mỗi chunk để bảo toàn ngữ cảnh phân cấp (Heading Enrichment).
    - Nếu một section quá dài so với max_chunk_size, tự động dùng RecursiveChunker để chia nhỏ tiếp nhưng vẫn giữ heading.
    """

    HEADING_REGEX = re.compile(
        r"^(?:"
        r"#{1,6}\s+.+"                              # Markdown heading: # Title
        r"|(?:Chương\s+[IVXLCDM\d]+[.:]?\s*.*)"    # Tiêu đề Chương (Chương I, Chương 1)
        r"|(?:Điều\s+\d+[.:]?\s*.*)"               # Tiêu đề Điều (Điều 1. Phạm vi)
        r"|(?:Mục\s+\d+[.:]?\s*.*)"                # Tiêu đề Mục
        r"|(?:\d+\.\s+[A-ZÀ-Ỹ].*)"                  # Tiêu đề dạng số: 1. Đăng ký...
        r")$",
        re.IGNORECASE | re.MULTILINE,
    )

    def __init__(self, max_chunk_size: int = 500, min_chunk_size: int = 50) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self._fallback_chunker = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Tách frontmatter nếu có (metadata YAML ở đầu)
        clean_text = text.strip()
        if clean_text.startswith("---"):
            end_fm = clean_text.find("---", 3)
            if end_fm != -1:
                clean_text = clean_text[end_fm + 3 :].strip()

        lines = clean_text.splitlines()
        sections: list[tuple[str, list[str]]] = []
        current_heading = "Mở đầu"
        current_lines: list[str] = []

        for line in lines:
            line_str = line.strip()
            if self.HEADING_REGEX.match(line_str):
                if current_lines:
                    sections.append((current_heading, current_lines))
                    current_lines = []
                current_heading = line_str
            else:
                if line_str:
                    current_lines.append(line_str)

        if current_lines:
            sections.append((current_heading, current_lines))

        # Gom các sections thành chunk, bổ sung prefix heading
        chunks: list[str] = []
        for heading, body_lines in sections:
            body_text = "\n".join(body_lines).strip()
            if not body_text:
                continue

            full_section_text = f"{heading}\n{body_text}" if heading != "Mở đầu" else body_text

            if len(full_section_text) <= self.max_chunk_size:
                chunks.append(full_section_text)
            else:
# Nếu section quá dài, chia nhỏ body nhưng vẫn giữ heading ở đầu mỗi sub-chunk
                sub_chunks = self._fallback_chunker.chunk(body_text)
                for sc in sub_chunks:
                    chunk_with_ctx = f"[{heading}] {sc}" if heading != "Mở đầu" else sc
                    chunks.append(chunk_with_ctx)

        return chunks
```

**Hoàng Văn Tài (Phụ trách RecursiveChunker)**
- **Loại chiến lược:** `RecursiveChunker (chunk_size=400, separators=["\n\n", "\n", ". ", " "])`
- **Mô tả & lý do chọn:** Chia đệ quy phân cấp từ đoạn văn lớn xuống câu và từ, kết hợp cơ chế gom các mảnh nhỏ liền kề cho sát 400 ký tự. Phù hợp cho các tài liệu có cấu trúc đoạn chuẩn, tránh sinh ra chunk vụn.

**Bùi Đăng Khoa (Phụ trách FixedSizeChunker)**
- **Loại chiến lược:** `FixedSizeChunker (chunk_size=300, overlap=50)` (Baseline)
- **Mô tả & lý do chọn:** Cắt cố định 300 ký tự với bước trượt 250 ký tự (overlap 50 ký tự) nhằm bảo toàn ngữ cảnh ở vùng biên giữa hai chunk liền kề, làm mốc cơ sở đánh giá hiện tượng đứt gãy câu so với hai phương pháp phân cấp ngữ nghĩa.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|:---|:---|:---:|:---|:---|
| Phạm Hoàng Anh Khôi | `HeadingChunker (500)` | 10/10 | Giữ trọn vẹn từng Điều luật; tái tiêm tiêu đề giúp mảnh con không mất ngữ cảnh | Phụ thuộc vào chất lượng định dạng tiêu đề Markdown của văn bản |
| Hoàng Văn Tài | `RecursiveChunker (400)` | 10/10 | Không bị chunk vụn; kích thước chunk đồng đều và tự nhiên | Vẫn có thể cắt ngang một Điều luật dài thành 2 phần độc lập |
| Bùi Đăng Khoa | `FixedSize (300, overlap 50)` | 8/10 | Đơn giản, tốc độ chunking nhanh nhất | Thường xuyên cắt đôi từ hoặc câu giữa chừng; số lượng chunk nhiều (114 chunks) |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> `HeadingChunker` là chiến lược vượt trội nhất cho tập văn bản quy định đại học. Vì quy định luôn được soạn thảo theo từng Điều khoản độc lập có chủ đề riêng biệt; việc cắt đúng ranh giới Điều và tái tiêm (re-inject) tiêu đề vào các mảnh con giúp vector embedding giữ trọn vẹn ngữ cảnh nguồn, ngăn chặn hoàn toàn việc retrieval trích xuất các câu cụt không rõ đang áp dụng cho quy định nào.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-----------------|---------------------------------|---------------------------|
| 1 | Mức học bổng khuyến khích học tập loại xuất sắc của UEH bằng bao nhiêu phần trăm suất học bổng toàn phần? | Bằng 150% suất học bổng toàn phần, áp dụng cho sinh viên có kết quả học tập từ loại xuất sắc và điểm rèn luyện đạt xuất sắc. | `hoc-bong-khuyen-khich-hoc-tap-76` |
| 2 | Thời hạn để sinh viên nộp đề nghị phúc khảo điểm thi kết thúc học phần là bao lâu? | Trong vòng bốn mươi (40) ngày làm việc kể từ ngày thi. (Các trường hợp quá thời hạn, thông tin không chính xác sẽ không được tổ chức phúc khảo). | `phuc-khao-diem-thi-47` |
| 3 | Giờ mở cửa của Thư viện thông minh UEH tại cơ sở Nguyễn Tri Phương (tòa nhà B1 lầu 6) như thế nào? | Tại cơ sở Nguyễn Tri Phương (UEH Smart Library - tòa nhà B1 lầu 6): Thứ Hai đến Thứ Sáu: 08:00 đến 20:00; Thứ Bảy: 08:00 đến 16:00. | `93` |
| 4 | Sinh viên có thể đóng học phí qua những hình thức nào theo hướng dẫn của UEH? | Đóng qua cổng payment, đóng qua hình thức chuyển khoản, đóng trực tiếp tại hệ thống ngân hàng OCB (tiền mặt). | `dong-hoc-phi-35` |
| 5 | Sinh viên cần thỏa mãn những điều kiện gì về kết quả học tập và rèn luyện để được xét học bổng khuyến khích? *(Cần filter: `audience="student"`)* | Có kết quả học tập và kết quả rèn luyện từ loại khá trở lên; đạt từ 5 điểm trở lên (thang 10) đối với tất cả học phần trong kỳ; số tín chỉ đăng ký >= 15 tín chỉ; không bị kỷ luật từ khiển trách trở lên. | `hoc-bong-khuyen-khich-hoc-tap-76` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).  
> **Mô hình Embedding:** OpenAI `text-embedding-3-small` (1536 dimensions, đo lường thực tế trên bộ dữ liệu 8 tài liệu UEH).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|:-----------------------------:|---------|
| 1 | Mức học bổng khuyến khích loại xuất sắc | `HeadingChunker (500)` | Có (Top-1, Score: 0.7385) | HeadingChunker đạt điểm cao nhất (0.7385 so với 0.6729 của Recursive) nhờ tái tiêm tiêu đề `# Học bổng Khuyến khích học tập` vào chunk con |
| 2 | Thời hạn nộp đề nghị phúc khảo | `FixedSize (300, ov=50)` & `HeadingChunker` | Có (Top-1, Score: 0.7216 & 0.7078) | Câu ngắn nằm trọn vẹn trong chunk, cả 4 chiến lược đều Hit@1 xuất sắc |
| 3 | Giờ mở cửa Thư viện UEH B1 lầu 6 | `FixedSize (300, ov=50)` & `HeadingChunker` | Có (Top-1, Score: 0.7470 & 0.7450) | Cụm từ "Thư viện B1 lầu 6" khớp chính xác với mục giờ mở cửa của thư viện |
| 4 | Các hình thức nộp học phí UEH | `RecursiveChunker (400)` & `HeadingChunker` | Có (Top-1, Score: 0.7010 & 0.6979) | Gom trọn vẹn 3 hình thức nộp học phí (cổng payment, chuyển khoản, ngân hàng OCB) |
| 5 | Điều kiện xét học bổng (Filter student) | `RecursiveChunker (400)` & `HeadingChunker` | Có (Top-1, Score: 0.7168 & 0.7001) | Filter `audience="student"` loại bỏ hoàn toàn các văn bản ngoài phạm vi sinh viên |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata phát huy tác dụng bảo vệ ngữ cảnh cốt tử ở Câu hỏi 5 (`audience="student"`). Khi kho dữ liệu có nhiều đối tượng người học (sinh viên đại học chính quy, học viên cao học, cán bộ viên chức), việc áp dụng metadata pre-filtering thu hẹp không gian tìm kiếm ngay từ đầu, loại bỏ các chunk điều kiện khen thưởng của cán bộ hay sau đại học, giúp độ chính xác đạt Hit@1 = 100%.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **HeadingChunker kết hợp Context Re-injection đạt chất lượng số 1:** Với điểm Cosine Similarity trung bình 0.718 và tỷ lệ Hit@1 tuyệt đối (5/5), việc tôn trọng cấu trúc pháp lý văn bản và tự động tiêm lại tiêu đề Điều/Mục vào các mảnh con ngăn ngừa hoàn toàn hiện tượng mất ngữ cảnh.
> 2. **Sự đánh đổi lớn của Fixed-size với Overlap:** Cắt cố định 300 ký tự (overlap 50) sinh ra tới 114 chunks (tăng 56% so với 73 chunks của HeadingChunker), làm tăng vọt chi phí API embedding và dung lượng lưu trữ vector mà không đem lại sự vượt trội về độ tương đồng ngữ nghĩa.
> 3. **Hiệu năng vượt trội của mô hình embedding chuyên dụng:** Khi chuyển từ MockEmbedder sang OpenAI `text-embedding-3-small`, điểm tương đồng trung bình nhảy vọt từ mức nhiễu ~0.3 lên ~0.72, và tỷ lệ Hit@1 đạt mức tối đa 100%.

**Bài học rút ra khi so sánh trong nhóm:**
> Khi áp dụng trên cùng một kho văn bản quy định đại học, việc lựa chọn chiến lược chunking quyết định trực tiếp tới chất lượng và chi phí của hệ thống RAG. Chunking phân cấp theo ngữ nghĩa tự nhiên (`HeadingChunker` và `RecursiveChunker`) luôn mang lại sự mạch lạc và tính chuẩn xác cao hơn nhiều so với việc chia nhỏ thô bạo theo độ dài ký tự (`FixedSizeChunker`).

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> 1. Bổ sung trích xuất metadata phong phú hơn ngay từ khâu cào dữ liệu: thêm các trường `academic_year`, `decision_number` (số quyết định) để hỗ trợ lọc tìm kiếm theo năm ban hành quy định.
> 2. Nghiên cứu triển khai kỹ thuật Contextual Retrieval (tiêm tóm tắt tài liệu vào mọi chunk) để các đoạn trích dẫn ngắn vẫn mang đầy đủ ngữ cảnh nguồn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|:----------------:|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 0 / 5 |
| **Tổng phần nhóm** | **35 / 40** |
