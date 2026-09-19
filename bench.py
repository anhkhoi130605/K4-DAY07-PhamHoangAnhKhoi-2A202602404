#!/usr/bin/env python3

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Cấu hình UTF-8 cho stdout/stderr trên Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, HeadingChunker, RecursiveChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

# ==============================================================================
# ⚙️ CẤU HÌNH CHIẾN LƯỢC CHUNKING (MỖI THÀNH VIÊN BẬT ĐÚNG 1 CHIẾN LƯỢC)
# Nhóm 4 người: FixedSize (có overlap), RecursiveChunker, HeadingChunker (bắt buộc)
# ==============================================================================

# --- CHIẾN LƯỢC 1 (Vai bắt buộc L3A — Giao cho Thành viên 2): HeadingChunker ---
STRATEGY_NAME = "HeadingChunker (mục/Điều khoản, max_chunk=500)"
chunker = HeadingChunker(max_chunk_size=500)

# --- CHIẾN LƯỢC 2 (Giao cho Thành viên 3): RecursiveChunker ---
# STRATEGY_NAME = "RecursiveChunker (chunk_size=400, separators=['\\n\\n', '\\n', '. ', ' '])"
# chunker = RecursiveChunker(chunk_size=400, separators=["\n\n", "\n", ". ", " "])

# --- CHIẾN LƯỢC 3 (Giao cho Thành viên 4): FixedSizeChunker (có overlap) ---
# STRATEGY_NAME = "FixedSizeChunker (chunk_size=300, overlap=50)"
# chunker = FixedSizeChunker(chunk_size=300, overlap=50)


# ==============================================================================
# 📋 BỘ 5 BENCHMARK QUERIES & GOLD ANSWERS (CẢ NHÓM DÙNG CHUNG)
# ==============================================================================

BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "category_type": "Tra cứu số liệu",
        "query": "Mức học bổng khuyến khích học tập loại xuất sắc của UEH bằng bao nhiêu phần trăm suất học bổng toàn phần?",
        "filter": None,
        "gold_doc": "hoc-bong-khuyen-khich-hoc-tap-76",
        "gold_answer": "Bằng 150% suất học bổng toàn phần, áp dụng cho sinh viên có kết quả học tập từ loại xuất sắc và điểm rèn luyện đạt xuất sắc.",
    },
    {
        "id": "Q2",
        "category_type": "Quy trình & Thời hạn",
        "query": "Thời hạn để sinh viên nộp đề nghị phúc khảo điểm thi kết thúc học phần là bao lâu?",
        "filter": None,
        "gold_doc": "phuc-khao-diem-thi-47",
        "gold_answer": "Trong vòng bốn mươi (40) ngày làm việc kể từ ngày thi. (Các trường hợp quá thời hạn, thông tin không chính xác sẽ không được tổ chức phúc khảo).",
    },
    {
        "id": "Q3",
        "category_type": "Liệt kê thông tin",
        "query": "Giờ mở cửa của Thư viện thông minh UEH tại cơ sở Nguyễn Tri Phương (tòa nhà B1 lầu 6) như thế nào?",
        "filter": None,
        "gold_doc": "93",
        "gold_answer": "Tại cơ sở Nguyễn Tri Phương (UEH Smart Library - tòa nhà B1 lầu 6): Thứ Hai đến Thứ Sáu: 08:00 đến 20:00; Thứ Bảy: 08:00 đến 16:00.",
    },
    {
        "id": "Q4",
        "category_type": "Hỏi hình thức nộp tiền",
        "query": "Sinh viên có thể đóng học phí qua những hình thức nào theo hướng dẫn của UEH?",
        "filter": None,
        "gold_doc": "dong-hoc-phi-35",
        "gold_answer": "Đóng qua cổng payment, đóng qua hình thức chuyển khoản, đóng trực tiếp tại hệ thống ngân hàng OCB (tiền mặt).",
    },
    {
        "id": "Q5",
        "category_type": "Hỏi điều kiện (Cần Filter)",
        "query": "Sinh viên cần thỏa mãn những điều kiện gì về kết quả học tập và rèn luyện để được xét học bổng khuyến khích?",
        "filter": {"audience": "student"},
        "gold_doc": "hoc-bong-khuyen-khich-hoc-tap-76",
        "gold_answer": "Có kết quả học tập và kết quả rèn luyện từ loại khá trở lên; đạt từ 5 điểm trở lên (thang 10) đối với tất cả học phần trong kỳ; số tín chỉ đăng ký >= 15 tín chỉ; không bị kỷ luật từ khiển trách trở lên.",
    },
]


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Tách frontmatter YAML và nội dung body từ file Markdown."""
    metadata: dict[str, str] = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            body = parts[2]
            for line in raw_yaml.splitlines():
                line = line.strip()
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    metadata[key] = val

    return metadata, body.strip()


def load_and_chunk_corpus(data_dir: Path, active_chunker) -> list[Document]:
    """Đọc toàn bộ file Markdown, thực hiện chunking và bọc vào Document."""
    all_chunks: list[Document] = []
    files = sorted(data_dir.glob("*.md"))

    if not files:
        raise FileNotFoundError(f"Không tìm thấy file .md nào trong {data_dir}")

    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)

        doc_id = metadata.get("doc_id") or file_path.stem
        # Bổ sung các metadata cốt lõi
        base_meta = {
            **metadata,
            "doc_id": doc_id,
            "source": str(file_path),
            "file_name": file_path.name,
        }

        # Thực hiện chia nhỏ văn bản ngoài store
        chunks = active_chunker.chunk(body)

        for i, chunk_text in enumerate(chunks):
            chunk_doc = Document(
                id=f"{doc_id}#{i}",
                content=chunk_text,
                metadata={**base_meta, "chunk_index": i},
            )
            all_chunks.append(chunk_doc)

    return all_chunks


def setup_embedder():
    """Khởi tạo mô hình embedding dựa trên cấu hình môi trường hoặc mock."""
    load_dotenv(override=True)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()

    if provider == "local":
        try:
            model = os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL)
            print(f"🚀 Khởi tạo Local Embedding (model: {model})...")
            return LocalEmbedder(model_name=model)
        except Exception as e:
            print(f"⚠️ Lỗi khởi tạo Local Embedder: {e}. Fallback về MockEmbedder.")
            return _mock_embed
    elif provider == "openai":
        try:
            model = os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
            print(f"🚀 Khởi tạo OpenAI Embedding API (model: {model})...")
            return OpenAIEmbedder(model_name=model)
        except Exception as e:
            print(f"⚠️ Lỗi khởi tạo OpenAI Embedder: {e}. Fallback về MockEmbedder.")
            return _mock_embed
    elif provider == "gemini":
        try:
            model = os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL)
            print(f"🚀 Khởi tạo Gemini Embedding API (model: {model})...")
            return GeminiEmbedder(model_name=model)
        except Exception as e:
            print(f"⚠️ Lỗi khởi tạo Gemini Embedder: {e}. Fallback về MockEmbedder.")
            return _mock_embed

    print("ℹ️ Chế độ Embedding: Mock Embedder (giả lập)")
    return _mock_embed


def mock_eval_llm(prompt: str) -> str:
    """Mock LLM tạo câu trả lời ngắn phục vụ demo đánh giá."""
    preview = prompt[:200].replace("\n", " ")
    return f"[RAG Agent] Trích xuất từ ngữ cảnh: {preview}..."


def main() -> None:
    data_dir = Path("data/quy-dinh-dai-hoc")
    print("=" * 75)
    print("📊 HỆ THỐNG ĐÁNH GIÁ CHẤT LƯỢNG RETRIEVAL (BENCHMARK RAG)")
    print(f"📁 Thư mục dữ liệu : {data_dir}")
    print(f"⚙️ Chiến lược chia : {STRATEGY_NAME}")
    print("=" * 75)

    # 1. Nạp và chunk tài liệu
    documents = load_and_chunk_corpus(data_dir, chunker)
    total_chunks = len(documents)
    avg_len = sum(len(d.content) for d in documents) / total_chunks if total_chunks else 0

    print(f"\n✓ Đã nạp và chia nhỏ thành công: {total_chunks} chunks")
    print(f"✓ Độ dài trung bình mỗi chunk   : {avg_len:.1f} ký tự")

    # 2. Khởi tạo EmbeddingStore và nạp documents
    embedder = setup_embedder()
    store = EmbeddingStore(collection_name="ueh_benchmark", embedding_fn=embedder)
    store.add_documents(documents)
    print(f"✓ Đã lưu trữ {store.get_collection_size()} records trong EmbeddingStore")

    agent = KnowledgeBaseAgent(store=store, llm_fn=mock_eval_llm)

    # 3. Chạy 5 câu hỏi benchmark
    print("\n" + "=" * 75)
    print("🔍 CHẠY ĐÁNH GIÁ 5 BENCHMARK QUERIES")
    print("=" * 75)

    hit_at_1_count = 0
    hit_at_3_count = 0
    results_summary = []

    for item in BENCHMARK_QUERIES:
        q_id = item["id"]
        q_text = item["query"]
        q_filter = item["filter"]
        gold_doc = item["gold_doc"]
        gold_ans = item["gold_answer"]

        print(f"\n[{q_id}] ({item['category_type']})")
        print(f"  Câu hỏi   : {q_text}")
        if q_filter:
            print(f"  Filter    : {q_filter}")
        print(f"  Tài liệu  : {gold_doc}")
        print(f"  Gold Ans  : {gold_ans}")

        # Tìm kiếm với search_with_filter
        search_results = store.search_with_filter(q_text, top_k=3, metadata_filter=q_filter)

        retrieved_docs = [r["metadata"].get("doc_id") for r in search_results]
        is_hit_1 = bool(retrieved_docs and retrieved_docs[0] == gold_doc)
        is_hit_3 = bool(gold_doc in retrieved_docs)

        if is_hit_1:
            hit_at_1_count += 1
        if is_hit_3:
            hit_at_3_count += 1

        top1_score = search_results[0]["score"] if search_results else 0.0
        top1_content = search_results[0]["content"] if search_results else "N/A"

        print(f"  Top-1 Ret : doc_id='{retrieved_docs[0] if retrieved_docs else 'N/A'}' | score={top1_score:.4f} | {'✓ ĐÚNG' if is_hit_1 else '✗ TRƯỢT'}")
        print(f"  Top-3 Ret : {retrieved_docs} | {'✓ HIT@3' if is_hit_3 else '✗ MISS'}")

        # In snippet top-1
        snippet = top1_content[:150].replace("\n", " ")
        print(f"  Snippet   : \"{snippet}...\"")

        # Câu trả lời từ agent
        agent_answer = agent.answer(q_text, top_k=3)
        print(f"  Agent Ans : {agent_answer[:160]}...")

        results_summary.append({
            "id": q_id,
            "query": q_text,
            "top1_doc": retrieved_docs[0] if retrieved_docs else "N/A",
            "top1_score": top1_score,
            "hit_1": is_hit_1,
            "hit_3": is_hit_3,
            "top1_snippet": snippet,
        })

    # 4. Bảng tổng kết
    hit_1_pct = (hit_at_1_count / len(BENCHMARK_QUERIES)) * 100
    hit_3_pct = (hit_at_3_count / len(BENCHMARK_QUERIES)) * 100

    print("\n" + "=" * 75)
    print("📈 BẢNG TỔNG HỢP KẾT QUẢ TRUY XUẤT (DÙNG CHO BÁO CÁO CÁ NHÂN & NHÓM)")
    print("=" * 75)
    print(f"Chiến lược: {STRATEGY_NAME}")
    print(f"Tổng số chunk: {total_chunks} | Độ dài trung bình: {avg_len:.1f} ký tự")
    print(f"Hit@1 (Chính xác ở Top-1): {hit_at_1_count}/{len(BENCHMARK_QUERIES)} ({hit_1_pct:.1f}%)")
    print(f"Hit@3 (Xuất hiện trong Top-3): {hit_at_3_count}/{len(BENCHMARK_QUERIES)} ({hit_3_pct:.1f}%)\n")

    print("| # | Câu hỏi (Query) | Top-1 Doc | Score | Relevant? |")
    print("|---|-----------------|-----------|-------|-----------|")
    for r in results_summary:
        print(f"| {r['id']} | {r['query'][:38]}... | {r['top1_doc']} | {r['top1_score']:.3f} | {'Có' if r['hit_1'] else 'Không'} |")
    print("=" * 75)


if __name__ == "__main__":
    main()
