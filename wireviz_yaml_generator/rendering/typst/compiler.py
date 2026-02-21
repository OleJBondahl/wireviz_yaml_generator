"""Typst PDF compiler for harness documentation.

Assembles a Typst document from title pages, content sections, and wiring
diagrams, then compiles it to PDF using the optional ``typst`` package.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass

from wireviz_yaml_generator.rendering.typst.markdown_converter import (
    markdown_to_typst_content,
    markdown_to_typst_title,
)


@dataclass
class HarnessDocConfig:
    """Configuration for the harness document compiler."""

    title: str = ""
    version: str = "01"
    date: str = ""
    logo_path: str | None = None
    font_family: str = "Times New Roman"
    proprietary_notice: str | None = None
    root_dir: str = "."
    temp_dir: str = "temp"


@dataclass
class _Page:
    """Internal representation of a page in the document."""

    page_type: str  # "title", "toc", "content", "diagram", "custom"
    md_path: str = ""
    image_root: str | None = None
    title: str = ""
    svg_path: str = ""
    typst_content: str = ""
    toc_columns: int = 2
    toc_depth: int = 3


class HarnessDocCompiler:
    """Assembles and compiles a multi-page harness documentation PDF.

    Usage::

        config = HarnessDocConfig(title="My Harness", version="02", date="19/01/2026")
        compiler = HarnessDocCompiler(config)
        compiler.add_title_page("docs/front.md")
        compiler.add_toc()
        compiler.add_content_page("docs/description.md")
        compiler.add_diagram_page("W001", "drawings/harness/W001.svg")
        compiler.compile("output/harness_doc.pdf")
    """

    def __init__(self, config: HarnessDocConfig) -> None:
        self.config = config
        self._pages: list[_Page] = []

    def add_title_page(self, md_path: str | None = None) -> None:
        """Add a title page, optionally from a Markdown file."""
        self._pages.append(_Page(page_type="title", md_path=md_path or ""))

    def add_toc(self, columns: int = 2, depth: int = 3) -> None:
        """Add a table-of-contents page."""
        self._pages.append(_Page(page_type="toc", toc_columns=columns, toc_depth=depth))

    def add_content_page(self, md_path: str, image_root: str | None = None) -> None:
        """Add a content section from a Markdown file."""
        self._pages.append(_Page(page_type="content", md_path=md_path, image_root=image_root))

    def add_diagram_page(self, title: str, svg_path: str) -> None:
        """Add a wiring diagram page with an SVG image."""
        self._pages.append(_Page(page_type="diagram", title=title, svg_path=svg_path))

    def add_custom_page(self, typst_content: str) -> None:
        """Add a page with raw Typst content."""
        self._pages.append(_Page(page_type="custom", typst_content=typst_content))

    def compile(self, output_path: str) -> None:
        """Assemble Typst content and compile to PDF.

        Raises:
            ImportError: If the ``typst`` package is not installed.
        """
        try:
            import typst as typst_mod  # ty: ignore[unresolved-import]
        except ImportError as err:
            raise ImportError(
                "The 'typst' package is required for PDF compilation. "
                "Install it with: pip install wireviz-yaml-generator[pdf]"
            ) from err

        config = self.config
        temp_dir = os.path.join(config.root_dir, config.temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        # Copy template to temp dir so Typst can resolve it
        template_path = self._get_template_path()
        template_dest = os.path.join(temp_dir, "harness_doc.typ")
        shutil.copy2(template_path, template_dest)

        content = self._build_typst_content(template_dest)

        typst_mod.compile(
            content.encode("utf-8"),
            output=output_path,
            root=config.root_dir,
        )

    def build_typst_string(self) -> str:
        """Build the full Typst document string without compiling.

        Useful for testing and debugging the generated Typst content.
        """
        config = self.config
        temp_dir = os.path.join(config.root_dir, config.temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        template_path = self._get_template_path()
        template_dest = os.path.join(temp_dir, "harness_doc.typ")
        shutil.copy2(template_path, template_dest)

        return self._build_typst_content(template_dest)

    def _get_template_path(self) -> str:
        """Resolve the path to the harness_doc.typ template."""
        here = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(here, "templates", "harness_doc.typ")

    def _build_typst_content(self, template_path: str) -> str:
        """Assemble the full Typst document string."""
        config = self.config

        # Template path relative to root_dir
        template_rel = os.path.relpath(template_path, config.root_dir).replace("\\", "/")

        # Logo path relative to template dir (Typst resolves image() from template location)
        template_dir = os.path.dirname(os.path.abspath(template_path))
        logo_arg = "none"
        if config.logo_path:
            logo_rel = os.path.relpath(os.path.abspath(config.logo_path), template_dir).replace("\\", "/")
            logo_arg = f'"{logo_rel}"'

        content = f'''#import "{template_rel}": harness_doc

#show: harness_doc.with(
  title: "{config.title}",
  version: "{config.version}",
  date: "{config.date}",
  logo_path: {logo_arg},
  font_family: "{config.font_family}",
)
'''

        for page in self._pages:
            content += self._render_page(page)

        return content

    def _render_page(self, page: _Page) -> str:
        """Render a single page to Typst markup."""
        if page.page_type == "title":
            return self._render_title_page(page)
        elif page.page_type == "toc":
            return self._render_toc(page)
        elif page.page_type == "content":
            return self._render_content_page(page)
        elif page.page_type == "diagram":
            return self._render_diagram_page(page)
        elif page.page_type == "custom":
            return self._render_custom_page(page)
        return ""

    def _render_title_page(self, page: _Page) -> str:
        config = self.config
        parts: list[str] = []

        parts.append("\n#v(4cm)")
        parts.append(f'#align(center)[#text(2em, weight: "bold")[{config.title}]]')
        parts.append("#v(5cm)")

        if page.md_path:
            parts.append(markdown_to_typst_title(page.md_path, notice=config.proprietary_notice))
        elif config.proprietary_notice:
            from wireviz_yaml_generator.rendering.typst.markdown_converter import _notice_block

            parts.append(_notice_block(config.proprietary_notice))
            parts.append("#pagebreak()")

        return "\n".join(parts)

    def _render_toc(self, page: _Page) -> str:
        return f"""
#columns({page.toc_columns})[#outline(title: "Table of Contents", indent: auto, depth: {page.toc_depth})]
#pagebreak()
"""

    def _render_content_page(self, page: _Page) -> str:
        return markdown_to_typst_content(page.md_path, image_root=page.image_root)

    def _render_diagram_page(self, page: _Page) -> str:
        svg_rel = self._rel_path(page.svg_path)
        return f"""
#block(breakable: false)[
  === {page.title}
  #align(left)[Length:]
  #image("{svg_rel}", width: 100%)
]
#v(2cm)
"""

    def _render_custom_page(self, page: _Page) -> str:
        result = page.typst_content
        result += "\n#pagebreak(weak: true)\n"
        return result

    def _rel_path(self, path: str) -> str:
        """Convert a path to a Typst-friendly relative path from root_dir."""
        if os.path.isabs(path):
            path = os.path.relpath(path, self.config.root_dir)
        return path.replace("\\", "/")
