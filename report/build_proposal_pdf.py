#!/usr/bin/env python3

from __future__ import annotations

import pathlib
import re
import textwrap


ROOT = pathlib.Path(__file__).resolve().parent
INPUT = ROOT / "proposal.tex"
OUTPUT = ROOT / "proposal.pdf"

PAGE_WIDTH = 595
PAGE_HEIGHT = 842
LEFT = 52
RIGHT = 52
TOP = 54
BOTTOM = 54
BODY_SIZE = 10
BODY_LEADING = 12
TITLE_SIZE = 16
TITLE_LEADING = 20
META_SIZE = 10
META_LEADING = 13
SECTION_SIZE = 12
SECTION_LEADING = 15
SUBSECTION_SIZE = 10
SUBSECTION_LEADING = 13
BODY_WIDTH = 100
TITLE_WIDTH = 50
SECTION_WIDTH = 78


def escape_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def strip_latex(text: str) -> str:
    text = text.replace("``", '"').replace("''", '"')
    text = re.sub(r"\\texttt\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\url\{([^}]*)\}", r"\1", text)
    text = text.replace(r"\#", "#")
    text = text.replace(r"\_", "_")
    text = text.replace(r"--", "-")
    text = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", text)
    return text.strip()


def extract_braced(line: str) -> str:
    m = re.search(r"\{(.*)\}", line)
    return strip_latex(m.group(1)) if m else ""


def wrap(text: str, width: int, first_prefix: str = "", rest_prefix: str = "") -> list[str]:
    return textwrap.wrap(
        text,
        width=width,
        initial_indent=first_prefix,
        subsequent_indent=rest_prefix,
        break_long_words=True,
        break_on_hyphens=False,
    )


def parse_tex(path: pathlib.Path) -> list[tuple[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[tuple[str, str]] = []
    para: list[str] = []
    in_itemize = False
    in_bib = False

    def flush_para() -> None:
        nonlocal para
        if para:
            text = strip_latex(" ".join(part.strip() for part in para))
            if text:
                blocks.append(("body", text))
            para = []

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_para()
            continue
        if line.startswith(r"\documentclass") or line.startswith(r"\usepackage"):
            continue
        if line == r"\begin{document}" or line == r"\end{document}":
            flush_para()
            continue
        if line.startswith(r"\title{"):
            flush_para()
            blocks.append(("title", extract_braced(line)))
            continue
        if line.startswith(r"\author{"):
            flush_para()
            author = extract_braced(line).replace(r"\\", "\n")
            for part in author.split("\n"):
                blocks.append(("meta", part.strip()))
            continue
        if line.startswith(r"\date{"):
            flush_para()
            blocks.append(("meta", extract_braced(line)))
            continue
        if line == r"\maketitle":
            flush_para()
            blocks.append(("maketitle", ""))
            continue
        if line.startswith(r"\section{"):
            flush_para()
            blocks.append(("section", extract_braced(line)))
            continue
        if line.startswith(r"\subsection{"):
            flush_para()
            blocks.append(("subsection", extract_braced(line)))
            continue
        if line.startswith(r"\begin{itemize}"):
            flush_para()
            in_itemize = True
            continue
        if line.startswith(r"\end{itemize}"):
            flush_para()
            in_itemize = False
            continue
        if line.startswith(r"\begin{thebibliography}"):
            flush_para()
            in_bib = True
            blocks.append(("section", "Bibliography"))
            continue
        if line.startswith(r"\end{thebibliography}"):
            flush_para()
            in_bib = False
            continue
        if in_itemize and line.startswith(r"\item "):
            flush_para()
            blocks.append(("bullet", strip_latex(line[len(r"\item "):])))
            continue
        if in_bib and line.startswith(r"\bibitem"):
            flush_para()
            item = re.sub(r"\\bibitem\{[^}]*\}\s*", "", line)
            blocks.append(("bib", strip_latex(item)))
            continue
        para.append(line)

    flush_para()
    return blocks


def render_lines(blocks: list[tuple[str, str]]) -> list[tuple[str, int, str, str]]:
    lines: list[tuple[str, int, str, str]] = []
    header: list[tuple[str, str]] = []
    header_done = False

    def emit_header() -> None:
        nonlocal header_done
        if header_done:
            return
        title_lines = [text for kind, text in header if kind == "title"]
        meta_lines = [text for kind, text in header if kind == "meta"]
        for title in title_lines:
            for line in wrap(title, TITLE_WIDTH):
                lines.append(("Times-Bold", TITLE_SIZE, "center", line))
        if title_lines and meta_lines:
            lines.append(("gap", 6, "", ""))
        for meta in meta_lines:
            lines.append(("Times-Roman", META_SIZE, "center", meta))
        if header:
            lines.append(("gap", 12, "", ""))
        header_done = True

    for kind, text in blocks:
        if kind in {"title", "meta"} and not header_done:
            header.append((kind, text))
            continue
        if kind == "maketitle":
            emit_header()
            continue
        emit_header()
        if kind == "section":
            for line in wrap(text, SECTION_WIDTH):
                lines.append(("Times-Bold", SECTION_SIZE, "left", line))
            lines.append(("gap", 4, "", ""))
        elif kind == "subsection":
            for line in wrap(text, SECTION_WIDTH):
                lines.append(("Times-BoldItalic", SUBSECTION_SIZE, "left", line))
            lines.append(("gap", 3, "", ""))
        elif kind == "bullet":
            for line in wrap(text, BODY_WIDTH, "- ", "  "):
                lines.append(("Times-Roman", BODY_SIZE, "left", line))
            lines.append(("gap", 2, "", ""))
        elif kind == "bib":
            for line in wrap(text, BODY_WIDTH, "", "   "):
                lines.append(("Times-Roman", BODY_SIZE, "left", line))
            lines.append(("gap", 2, "", ""))
        elif kind == "body":
            for line in wrap(text, BODY_WIDTH):
                lines.append(("Times-Roman", BODY_SIZE, "left", line))
            lines.append(("gap", 4, "", ""))
    emit_header()
    if lines and lines[-1][0] == "gap":
        lines.pop()
    return lines


def paginate(lines: list[tuple[str, int, str, str]]) -> list[list[tuple[str, int, str, str]]]:
    pages: list[list[tuple[str, int, str, str]]] = []
    current: list[tuple[str, int, str, str]] = []
    y = PAGE_HEIGHT - TOP
    for font, size, align, text in lines:
        if font == "gap":
            y -= size
            continue
        leading = {
            TITLE_SIZE: TITLE_LEADING,
            META_SIZE: META_LEADING,
            SECTION_SIZE: SECTION_LEADING,
            SUBSECTION_SIZE: SUBSECTION_LEADING,
        }.get(size, BODY_LEADING)
        if y - leading < BOTTOM:
            pages.append(current)
            current = []
            y = PAGE_HEIGHT - TOP
        current.append((font, size, align, text))
        y -= leading
    if current:
        pages.append(current)
    return pages


def line_x(text: str, align: str, size: int) -> int:
    if align == "left":
        return LEFT
    avg = 0.5 * size
    width = int(len(text) * avg)
    return max(LEFT, (PAGE_WIDTH - width) // 2)


def make_stream(page: list[tuple[str, int, str, str]]) -> bytes:
    y = PAGE_HEIGHT - TOP
    commands: list[str] = []
    for font, size, align, text in page:
        leading = {
            TITLE_SIZE: TITLE_LEADING,
            META_SIZE: META_LEADING,
            SECTION_SIZE: SECTION_LEADING,
            SUBSECTION_SIZE: SUBSECTION_LEADING,
        }.get(size, BODY_LEADING)
        x = line_x(text, align, size)
        commands.append(f"BT /{font.replace('-', '')} {size} Tf {x} {y} Td ({escape_text(text)}) Tj ET")
        y -= leading
    return "\n".join(commands).encode("latin-1")


def build_pdf(streams: list[bytes]) -> bytes:
    objects: list[bytes] = []

    def add(obj: bytes) -> int:
        objects.append(obj)
        return len(objects)

    f_regular = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman >>")
    f_bold = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Bold >>")
    f_bolditalic = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-BoldItalic >>")

    contents = []
    for stream in streams:
        contents.append(add(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"))

    page_ids = []
    for content in contents:
        page_ids.append(
            add(
                (
                    "<< /Type /Page /Parent PAGES 0 R "
                    f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                    f"/Resources << /Font << /TimesRoman {f_regular} 0 R /TimesBold {f_bold} 0 R /TimesBoldItalic {f_bolditalic} 0 R >> >> "
                    f"/Contents {content} 0 R >>"
                ).encode("ascii")
            )
        )

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    pages = add(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii"))
    catalog = add(f"<< /Type /Catalog /Pages {pages} 0 R >>".encode("ascii"))

    fixed = [obj.replace(b"PAGES", str(pages).encode("ascii")) for obj in objects]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(fixed, start=1):
        offsets.append(len(out))
        out.extend(f"{idx} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(fixed) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(f"trailer\n<< /Size {len(fixed) + 1} /Root {catalog} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    return bytes(out)


def main() -> None:
    blocks = parse_tex(INPUT)
    lines = render_lines(blocks)
    pages = paginate(lines)
    OUTPUT.write_bytes(build_pdf([make_stream(page) for page in pages]))
    print(f"Wrote {OUTPUT} ({len(pages)} pages)")


if __name__ == "__main__":
    main()
