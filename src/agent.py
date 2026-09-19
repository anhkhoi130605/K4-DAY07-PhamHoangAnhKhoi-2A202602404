from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Truy xuất top-k chunk liên quan từ store
        results = self.store.search(query=question, top_k=top_k)

        # Trích xuất nội dung từ các records trả về
        context_blocks: list[str] = []
        for res in results:
            content = res.get("content") or res.get("text") or str(res)
            if content:
                context_blocks.append(content.strip())

        context = "\n\n".join(context_blocks)

        # 2. Xây dựng prompt chứa context và câu hỏi
        prompt = (
            "Dựa vào các thông tin ngữ cảnh dưới đây để trả lời câu hỏi. "
            "Nếu thông tin không đủ, hãy trả lời trung thực rằng bạn không biết.\n\n"
            f"--- Ngữ cảnh ---\n{context}\n\n"
            f"--- Câu hỏi ---\n{question}\n\n"
            "--- Câu trả lời ---"
        )

        # 3. Gọi LLM để sinh câu trả lời
        return self.llm_fn(prompt)