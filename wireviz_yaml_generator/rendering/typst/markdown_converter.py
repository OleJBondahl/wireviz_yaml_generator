"""Simple Markdown to Typst converter for harness documentation pages.

Supports headings, bold, bullet lists, images (with optional width),
pipe-delimited tables, and plain paragraphs.

Based on PySchemaElectrical's markdown_converter, extended with image
and bullet list support.
"""

from __future__ import annotations

import re


def markdown_to_typst_title(
    md_path: str,
    notice: str | None = None,
) -> str:
    """Convert a Markdown file to centered Typst markup for a title page.

    Args:
        md_path: Path to the Markdown file.
        notice: Optional proprietary-notice text placed at the bottom of the page.

    Returns:
        Typst markup string (including trailing pagebreak).
    """
    try:
        with open(md_path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Warning: {md_path} not found, skipping title page.")
        return ""

    typst_lines = _convert_lines(lines, centered=True, outlined=False)

    if notice:
        typst_lines.append(_notice_block(notice))

    typst_lines.append("#pagebreak()")
    return "\n".join(typst_lines)


def markdown_to_typst_content(
    md_path: str,
    image_root: str | None = None,
) -> str:
    """Convert a Markdown file to normal-flow Typst markup for content sections.

    Args:
        md_path: Path to the Markdown file.
        image_root: Optional root directory for resolving relative image paths.

    Returns:
        Typst markup string (including trailing pagebreak).
    """
    try:
        with open(md_path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Warning: {md_path} not found, skipping content page.")
        return ""

    typst_lines = _convert_lines(lines, centered=False, image_root=image_root)
    typst_lines.append("#pagebreak()")
    return "\n".join(typst_lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)(?:\{width=(\d+%?)\})?")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _heading(level: int, text: str, outlined: bool) -> str:
    """Emit a Typst heading, optionally excluded from the outline."""
    converted = _convert_inline(text)
    if outlined:
        return f"{'=' * level} {converted}"
    return f"#heading(level: {level}, outlined: false)[{converted}]"


def _convert_lines(
    lines: list[str],
    *,
    centered: bool = False,
    image_root: str | None = None,
    outlined: bool = True,
) -> list[str]:
    """Convert markdown lines to Typst markup."""
    typst_lines: list[str] = []

    if centered:
        typst_lines.append(r"#set align(center)")

    in_table = False
    table_rows: list[str] = []

    for line in lines:
        stripped = line.rstrip("\n")
        content = stripped.strip()

        if not content:
            if in_table:
                typst_lines.extend(_flush_table(table_rows))
                in_table = False
                table_rows = []
            continue

        # Headings
        if content.startswith("### "):
            if in_table:
                typst_lines.extend(_flush_table(table_rows))
                in_table = False
                table_rows = []
            typst_lines.append(_heading(3, content[4:], outlined))
            continue
        if content.startswith("## "):
            if in_table:
                typst_lines.extend(_flush_table(table_rows))
                in_table = False
                table_rows = []
            typst_lines.append(_heading(2, content[3:], outlined))
            continue
        if content.startswith("# "):
            if in_table:
                typst_lines.extend(_flush_table(table_rows))
                in_table = False
                table_rows = []
            typst_lines.append(_heading(1, content[2:], outlined))
            continue

        # Images
        img_match = _IMAGE_RE.match(content)
        if img_match:
            if in_table:
                typst_lines.extend(_flush_table(table_rows))
                in_table = False
                table_rows = []
            typst_lines.append(_convert_image(img_match, image_root))
            continue

        # Bullet lists
        if content.startswith("* ") or content.startswith("- "):
            if in_table:
                typst_lines.extend(_flush_table(table_rows))
                in_table = False
                table_rows = []
            typst_lines.append(f"- {_convert_inline(content[2:])}")
            continue

        # Tables
        if content.startswith("|"):
            if "---" in content:
                continue  # skip separator rows
            in_table = True
            table_rows.append(content)
            continue

        # Plain paragraph
        if in_table:
            typst_lines.extend(_flush_table(table_rows))
            in_table = False
            table_rows = []
        typst_lines.append(_convert_inline(content))
        typst_lines.append(r"#parbreak()")

    if in_table:
        typst_lines.extend(_flush_table(table_rows))

    if centered:
        typst_lines.append(r"#set align(start)")

    return typst_lines


def _convert_inline(text: str) -> str:
    """Convert inline markdown (bold) to Typst."""
    return _BOLD_RE.sub(r"*\1*", text)


def _convert_image(match: re.Match[str], image_root: str | None) -> str:
    """Convert a markdown image to a Typst #image() call."""
    path = match.group(2)
    width = match.group(3) or "100%"

    if image_root and not path.startswith("/"):
        path = f"{image_root.rstrip('/')}/{path}"

    # Strip leading slash for Typst relative paths
    if path.startswith("/"):
        path = path[1:]

    return f'#image("{path}", width: {width})'


def _flush_table(rows: list[str]) -> list[str]:
    """Convert accumulated Markdown table rows to a Typst table."""
    if not rows:
        return []

    first_cols = [c.strip() for c in rows[0].split("|") if c.strip()]
    num_cols = max(len(first_cols), 1)

    result: list[str] = []
    result.append(f"#table(columns: {num_cols}, stroke: 0.5pt, inset: 5pt,")
    col_aligns = ", ".join(["left"] * num_cols)
    result.append(f"  align: ({col_aligns}),")

    for row in rows:
        cols = [c.strip() for c in row.split("|") if c.strip()]
        for col in cols:
            result.append(f"  [{_convert_inline(col)}],")

    result.append(")")
    return result


def _notice_block(notice: str) -> str:
    """Generate a Typst notice block placed at the bottom of the page."""
    return f"""
#place(
  bottom + center,
  dy: -40mm,
  float: false,
  block(
    fill: luma(240),
    inset: 12pt,
    radius: 4pt,
    stroke: 1pt + luma(150),
    text(size: 9pt, style: "italic")[
      {notice}
    ]
  )
)
"""
