from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        # TODO: split into sentences, group into chunks
        if not text or not text.strip():
            return []
        raw_sentences = re.split(r"(?<=[.!?])\s", text.strip())
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        if not sentences:
            return []
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunk_str = " ".join(group).strip()
            if chunk_str:
                chunks.append(chunk_str)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text.strip(), self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

            # Nếu không còn separator nào, bắt buộc cắt cưỡng bức theo chunk_size
        if not remaining_separators:
            return [
                current_text[i: i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]

        # Nếu separator là rỗng "", cắt trực tiếp từng ký tự
        if sep == "":
            return [
                current_text[i: i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        splits = current_text.split(sep)
        chunks: list[str] = []
        buffer = ""

        for s in splits:
            if not s:
                continue

            # Đoạn con này bản thân nó vượt quá chunk_size -> đệ quy tiếp với separator cấp thấp hơn
            if len(s) > self.chunk_size:
                if buffer:
                    chunks.append(buffer)
                    buffer = ""
                sub_chunks = self._split(s, next_seps)
                chunks.extend(sub_chunks)
                continue

            # Thử gộp đoạn con vào buffer hiện tại
            candidate = f"{buffer}{sep}{s}" if buffer else s
            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                buffer = s

        if buffer:
            chunks.append(buffer)

        # Kiểm tra lại xem có chunk nào còn sót lại lớn hơn chunk_size hay không
        final_chunks: list[str] = []
        for c in chunks:
            c = c.strip()
            if not c:
                continue
            if len(c) > self.chunk_size and next_seps:
                final_chunks.extend(self._split(c, next_seps))
            else:
                final_chunks.append(c)

        return final_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # TODO: implement cosine similarity formula
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = _dot(vec_a, vec_b)
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=max(1, chunk_size // 10)),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        results: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            lengths = [len(c) for c in chunks] if chunks else [0]
            results[name] = {
                "count": len(chunks),
                "avg_length": sum(lengths) / len(lengths) if chunks else 0.0,
                "chunks": chunks,
            }

        return results


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


