#!/usr/bin/env python3
"""
Script làm sạch dữ liệu văn bản Markdown trong thư mục data/quy-dinh-dai-hoc/.

Chức năng:
1. Giữ nguyên vẹn 100% khối metadata YAML (Frontmatter: --- ... ---).
2. Loại bỏ các dòng rác từ giao diện web portal UEH:
   - "Kho tri thức - UEH"
   - "Đang xử lý..."
   - "Danh mục" và dòng lặp lại tiêu đề ngay sau đó
   - Footer thừa: "Bạn còn thắc mắc cần hỗ trợ, để UEH trả lời cho bạn nhé!"
   - Bản quyền footer, link hỗ trợ cuối trang
3. Chuẩn hóa khoảng trắng: thay thế non-breaking space (\\xa0), strip khoảng trắng thừa.
4. Rút gọn nhiều dòng trống liên tiếp thành tối đa 1 dòng trống (\\n\\n).
5. Giữ nguyên cấu trúc văn bản: các đề mục (#, ##, ###), các Điều khoản và mốc số liệu.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Các mẫu dòng rác ở đầu và cuối trang web
HEADER_BOILERPLATE_PATTERNS = [
    r"^kho tri thức\s*-\s*ueh\s*$",
    r"^đang xử lý\.*$",
    r"^danh mục\s*$",
]

FOOTER_TRIGGER_PATTERNS = [
    r"bạn còn thắc mắc cần hỗ trợ",
    r"© \d{4} - đại học kinh tế tp\.?\s*hồ chí minh",
    r"cổng hỗ trợ chăm sóc và hỗ trợ người học",
]


def clean_markdown_body(body: str, title: str = "") -> str:
    """Làm sạch phần thân của văn bản Markdown, loại bỏ rác UI."""
    # Thay non-breaking space bằng space thường
    body = body.replace("\xa0", " ")

    lines = [line.rstrip() for line in body.splitlines()]

    # Bỏ các dòng rác ở đầu trang
    cleaned_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        line_clean = line.strip().lower()

        # Kiểm tra dòng rác header
        is_header_junk = any(re.match(p, line_clean) for p in HEADER_BOILERPLATE_PATTERNS)
        # Kiểm tra dòng lặp lại tiêu đề ngay sau danh mục
        is_duplicate_title = bool(title and line_clean == title.strip().lower())

        if is_header_junk or is_duplicate_title:
            i += 1
            continue

        # Kiểm tra xem đã chạm đến footer rác hay chưa
        is_footer_junk = any(re.search(p, line_clean) for p in FOOTER_TRIGGER_PATTERNS)
        if is_footer_junk:
            # Dừng lại, không lấy các dòng từ footer trở đi
            break

        cleaned_lines.append(line)
        i += 1

    # Nối lại và rút gọn các dòng trống liên tiếp
    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_file(path: Path) -> tuple[int, int]:
    """Làm sạch một file markdown, giữ nguyên frontmatter."""
    raw = path.read_text(encoding="utf-8")

    # Tách frontmatter và body
    frontmatter = ""
    body = raw
    title = ""

    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            frontmatter = f"---{parts[1]}---\n\n"
            body = parts[2]

            # Lấy title từ frontmatter để kiểm tra dòng lặp
            title_m = re.search(r'^title:\s*["\']?(.*?)["\']?$', parts[1], re.MULTILINE)
            if title_m:
                title = title_m.group(1).strip()

    cleaned_body = clean_markdown_body(body, title=title)
    cleaned_content = f"{frontmatter}{cleaned_body}\n"

    old_len = len(raw)
    new_len = len(cleaned_content)

    path.write_text(cleaned_content, encoding="utf-8")
    return old_len, new_len


def main() -> None:
    parser = argparse.ArgumentParser(description="Làm sạch rác UI trong các file Markdown cào về.")
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("data/quy-dinh-dai-hoc"),
        help="Thư mục chứa các file .md cần làm sạch (mặc định: data/quy-dinh-dai-hoc)",
    )
    args = parser.parse_args()

    target_dir = args.dir
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"Thư mục không tồn tại: {target_dir}")
        return

    files = sorted(target_dir.glob("*.md"))
    if not files:
        print(f"Không tìm thấy file .md nào trong {target_dir}")
        return

    print(f"=== BẮT ĐẦU LÀM SẠCH DỮ LIỆU TẠI: {target_dir} ===")
    print(f"Tìm thấy {len(files)} file .md\n")

    total_old = 0
    total_new = 0

    for f in files:
        old_size, new_size = clean_file(f)
        diff = old_size - new_size
        pct = (diff / old_size * 100) if old_size else 0
        total_old += old_size
        total_new += new_size
        print(f"  ✓ {f.name:<45} | {old_size:>6} -> {new_size:>6} ký tự (giảm {diff:>4} ký tự, -{pct:.1f}%)")

    total_diff = total_old - total_new
    total_pct = (total_diff / total_old * 100) if total_old else 0
    print("-" * 75)
    print(f"TỔNG CỘNG: {total_old} -> {total_new} ký tự (Đã loại bỏ {total_diff} ký tự rác, -{total_pct:.1f}%)")
    print("=== HOÀN THÀNH LÀM SẠCH ===")


if __name__ == "__main__":
    main()
