🧱 Tầng 1: Cấu trúc dữ liệu nguyên tử (Primitives)
Viên gạch nhỏ nhất chứa dữ liệu chạy xuyên suốt toàn bộ hệ thống.



src/models.py
Xem gì: Lớp 

Document
 gồm 3 thuộc tính: id, content (chuỗi text), và metadata (dict).
Tại sao đọc đầu tiên: Mọi hàm từ chunking, embedding, lưu trữ đến search đều thao tác trên object Document này.
📐 Tầng 2: Toán học & Tiền xử lý văn bản (Chunking & Similarity)
Cách văn bản thô được băm nhỏ và công thức đo khoảng cách ngữ nghĩa.



src/chunking.py
 (Đọc theo thứ tự bên trong file):


compute_similarity
: Công thức Cosine Similarity giữa 2 vector $\frac{\vec{a} \cdot \vec{b}}{|\vec{a}| |\vec{b}|}$ (cốt lõi của tìm kiếm vector).


FixedSizeChunker
: Đã cài sẵn, đọc để hiểu cách lấy cửa sổ trượt ký tự (chunk_size và overlap).


SentenceChunker
: Cắt theo dấu câu (. , ! , ? ).


RecursiveChunker
: Tách đệ quy theo thứ tự phân cách (\n\n $\to$ \n $\to$ .  $\to$  ).


ChunkingStrategyComparator
: Đo lường thống kê (số lượng chunk, độ dài trung bình) của 3 phương pháp trên.
🧬 Tầng 3: Biểu diễn vector (Embeddings)
Biến chuỗi ký tự thành mảng số thực.



src/embeddings.py
Xem gì:


MockEmbedder
: Cơ chế băm text ra vector cố định 64 chiều (dùng để test nhanh không cần internet/API key).
Các class API thật: 

LocalEmbedder
, 

OpenAIEmbedder
, 

GeminiEmbedder
.
Điểm mấu chốt: Tất cả đều là callable nhận vào 1 chuỗi text: str và trả về list[float].
🗄️ Tầng 4: Lưu trữ & Truy xuất (Vector Store)
Kết hợp Document (Tầng 1) + Cosine Similarity (Tầng 2) + Embeddings (Tầng 3).



src/store.py
Xem gì: Lớp 

EmbeddingStore
:
add_documents: Chuyển danh sách Document thành vector rồi lưu vào mảng self._store (hoặc ChromaDB).
search: Lấy vector câu hỏi $\to$ tính dot product với tất cả vector đã lưu $\to$ lấy top_k điểm cao nhất.
search_with_filter: Lọc metadata trước (pre-filter), rồi mới tìm kiếm.
delete_document: Xoá theo doc_id.
🤖 Tầng 5: Ứng dụng tích hợp RAG (Agent)
Sử dụng Vector Store để hỗ trợ trả lời câu hỏi.



src/agent.py
Xem gì: Lớp 

KnowledgeBaseAgent
:
Nhận EmbeddingStore và llm_fn.
Phương thức answer(question): Thực hiện truy xuất top_k chunk từ store $\to$ tạo prompt chứa context $\to$ đưa vào LLM sinh câu trả lời.
🧪 Tầng 6: Kiểm thử & Khởi chạy ứng dụng (Validation & Entrypoint)
Nhìn từ trên xuống để thấy toàn bộ các mảnh ghép hoạt động cùng nhau.



tests/test_solution.py
Xem gì: Lướt qua 42 test cases. Đọc test sẽ thấy chính xác: input đầu vào là gì, output mong đợi ra sao, từng hàm cần trả về format như thế nào.


main.py
Xem gì: Hàm run_manual_demo: cách nó nạp file từ data/ $\to$ tạo Embedder $\to$ nạp vào EmbeddingStore $\to$ gọi KnowledgeBaseAgent.answer().
📋 Tầng 7: Quy chuẩn môn học & Báo cáo
Khi đã nắm toàn bộ code, đọc tiếp tài liệu để biết cần làm gì cho nhóm và nộp bài:



K4_VARIANT.md
: Ràng buộc riêng của lớp L3A (dữ liệu dịch vụ trường học, trường metadata audience).


exercises.md
: Danh sách bài tập cần điền vào báo cáo.


report/REPORT_CANHAN.md
: Nơi ghi nhận bài làm của bạn.