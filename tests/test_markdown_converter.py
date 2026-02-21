"""Tests for the Markdown to Typst converter."""

import os

from wireviz_yaml_generator.rendering.typst.markdown_converter import (
    markdown_to_typst_content,
    markdown_to_typst_title,
)


def _write_md(tmp_path, content: str) -> str:
    """Helper to write markdown content to a temp file."""
    md_file = os.path.join(str(tmp_path), "test.md")
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(content)
    return md_file


class TestHeadings:
    def test_h1(self, tmp_path):
        md = _write_md(tmp_path, "# Title\n")
        result = markdown_to_typst_content(md)
        assert "= Title" in result

    def test_h2(self, tmp_path):
        md = _write_md(tmp_path, "## Section\n")
        result = markdown_to_typst_content(md)
        assert "== Section" in result

    def test_h3(self, tmp_path):
        md = _write_md(tmp_path, "### Subsection\n")
        result = markdown_to_typst_content(md)
        assert "=== Subsection" in result


class TestInlineFormatting:
    def test_bold(self, tmp_path):
        md = _write_md(tmp_path, "This is **bold** text\n")
        result = markdown_to_typst_content(md)
        assert "*bold*" in result
        assert "**bold**" not in result

    def test_bold_in_heading(self, tmp_path):
        md = _write_md(tmp_path, "## **Important** Section\n")
        result = markdown_to_typst_content(md)
        assert "== *Important* Section" in result


class TestBulletLists:
    def test_asterisk_bullets(self, tmp_path):
        md = _write_md(tmp_path, "* Item one\n* Item two\n")
        result = markdown_to_typst_content(md)
        assert "- Item one" in result
        assert "- Item two" in result

    def test_dash_bullets(self, tmp_path):
        md = _write_md(tmp_path, "- Item one\n- Item two\n")
        result = markdown_to_typst_content(md)
        assert "- Item one" in result
        assert "- Item two" in result


class TestImages:
    def test_image_default_width(self, tmp_path):
        md = _write_md(tmp_path, "![alt text](images/photo.png)\n")
        result = markdown_to_typst_content(md)
        assert '#image("images/photo.png", width: 100%)' in result

    def test_image_with_width(self, tmp_path):
        md = _write_md(tmp_path, "![alt](path/img.svg){width=50%}\n")
        result = markdown_to_typst_content(md)
        assert '#image("path/img.svg", width: 50%)' in result

    def test_image_with_leading_slash(self, tmp_path):
        md = _write_md(tmp_path, "![alt](/drawings/resources/example.svg){width=100%}\n")
        result = markdown_to_typst_content(md)
        assert '#image("drawings/resources/example.svg", width: 100%)' in result

    def test_image_with_root(self, tmp_path):
        md = _write_md(tmp_path, "![alt](photo.png)\n")
        result = markdown_to_typst_content(md, image_root="assets/img")
        assert '#image("assets/img/photo.png", width: 100%)' in result


class TestTables:
    def test_simple_table(self, tmp_path):
        md = _write_md(
            tmp_path,
            "|Col1|Col2|\n|---|---|\n|A|B|\n|C|D|\n",
        )
        result = markdown_to_typst_content(md)
        assert "#table(columns: 2" in result
        assert "[Col1]," in result
        assert "[A]," in result
        assert "[D]," in result

    def test_table_skips_separator(self, tmp_path):
        md = _write_md(
            tmp_path,
            "|H1|H2|\n|---|---|\n|V1|V2|\n",
        )
        result = markdown_to_typst_content(md)
        assert "---" not in result


class TestTitleMode:
    def test_title_centered(self, tmp_path):
        md = _write_md(tmp_path, "## Revision Table\n")
        result = markdown_to_typst_title(md)
        assert "#set align(center)" in result
        assert "#set align(start)" in result
        assert "#pagebreak()" in result

    def test_title_with_notice(self, tmp_path):
        md = _write_md(tmp_path, "## Title\n")
        result = markdown_to_typst_title(md, notice="CONFIDENTIAL")
        assert "CONFIDENTIAL" in result
        assert "#place(" in result


class TestContentMode:
    def test_content_not_centered(self, tmp_path):
        md = _write_md(tmp_path, "## Section\n")
        result = markdown_to_typst_content(md)
        assert "#set align(center)" not in result

    def test_content_has_pagebreak(self, tmp_path):
        md = _write_md(tmp_path, "Some text\n")
        result = markdown_to_typst_content(md)
        assert "#pagebreak()" in result


class TestMissingFile:
    def test_missing_title_file(self):
        result = markdown_to_typst_title("/nonexistent/file.md")
        assert result == ""

    def test_missing_content_file(self):
        result = markdown_to_typst_content("/nonexistent/file.md")
        assert result == ""


class TestMixedContent:
    def test_full_document(self, tmp_path):
        md = _write_md(
            tmp_path,
            "# Main Title\n\nSome paragraph.\n\n"
            "* Bullet one\n* Bullet two\n\n"
            "## Section\n\n"
            "|A|B|\n|---|---|\n|1|2|\n\n"
            "![img](photo.png){width=80%}\n",
        )
        result = markdown_to_typst_content(md)
        assert "= Main Title" in result
        assert "Some paragraph." in result
        assert "- Bullet one" in result
        assert "== Section" in result
        assert "#table(" in result
        assert '#image("photo.png", width: 80%)' in result
