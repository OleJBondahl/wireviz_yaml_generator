"""Tests for the HarnessDocCompiler."""

import os

import pytest
from wireviz_yaml_generator.rendering.typst.compiler import (
    HarnessDocCompiler,
    HarnessDocConfig,
)


@pytest.fixture
def config():
    return HarnessDocConfig(
        title="Test Harness",
        version="01",
        date="01/01/2026",
        font_family="Times New Roman",
    )


@pytest.fixture
def config_with_logo(tmp_path):
    logo = os.path.join(str(tmp_path), "logo.png")
    with open(logo, "wb") as f:
        f.write(b"\x89PNG")  # minimal PNG header stub
    return HarnessDocConfig(
        title="Test Harness",
        version="01",
        date="01/01/2026",
        logo_path=logo,
        root_dir=str(tmp_path),
    )


class TestHarnessDocConfig:
    def test_defaults(self):
        cfg = HarnessDocConfig()
        assert cfg.title == ""
        assert cfg.version == "01"
        assert cfg.date == ""
        assert cfg.logo_path is None
        assert cfg.font_family == "Times New Roman"
        assert cfg.proprietary_notice is None
        assert cfg.root_dir == "."
        assert cfg.temp_dir == "temp"


class TestTitlePage:
    def test_title_page_without_md(self, config, tmp_path):
        config.root_dir = str(tmp_path)
        compiler = HarnessDocCompiler(config)
        compiler.add_title_page()
        content = compiler.build_typst_string()
        assert "Test Harness" in content
        assert "#v(4cm)" in content
        assert 'weight: "bold"' in content

    def test_title_page_with_md(self, config, tmp_path):
        config.root_dir = str(tmp_path)
        md_file = os.path.join(str(tmp_path), "front.md")
        with open(md_file, "w") as f:
            f.write("## Revision Table\n|V|Date|\n|---|---|\n|01|2026|\n")
        compiler = HarnessDocCompiler(config)
        compiler.add_title_page(md_file)
        content = compiler.build_typst_string()
        assert "Revision Table" in content
        assert "#table(" in content

    def test_title_page_with_notice(self, tmp_path):
        cfg = HarnessDocConfig(
            title="Test",
            proprietary_notice="CONFIDENTIAL",
            root_dir=str(tmp_path),
        )
        compiler = HarnessDocCompiler(cfg)
        compiler.add_title_page()
        content = compiler.build_typst_string()
        assert "CONFIDENTIAL" in content


class TestToc:
    def test_toc_defaults(self, config, tmp_path):
        config.root_dir = str(tmp_path)
        compiler = HarnessDocCompiler(config)
        compiler.add_toc()
        content = compiler.build_typst_string()
        assert "#columns(2)" in content
        assert "Table of Contents" in content
        assert "depth: 3" in content

    def test_toc_custom(self, config, tmp_path):
        config.root_dir = str(tmp_path)
        compiler = HarnessDocCompiler(config)
        compiler.add_toc(columns=3, depth=2)
        content = compiler.build_typst_string()
        assert "#columns(3)" in content
        assert "depth: 2" in content


class TestContentPage:
    def test_content_page(self, config, tmp_path):
        config.root_dir = str(tmp_path)
        md_file = os.path.join(str(tmp_path), "content.md")
        with open(md_file, "w") as f:
            f.write("## Description\n\nSome text.\n")
        compiler = HarnessDocCompiler(config)
        compiler.add_content_page(md_file)
        content = compiler.build_typst_string()
        assert "== Description" in content
        assert "Some text." in content


class TestDiagramPage:
    def test_diagram_page(self, config, tmp_path):
        config.root_dir = str(tmp_path)
        compiler = HarnessDocCompiler(config)
        compiler.add_diagram_page("W001", "drawings/harness/W001.svg")
        content = compiler.build_typst_string()
        assert "Cable nr: W001" in content
        assert '#image("drawings/harness/W001.svg", width: 100%)' in content
        assert "Length of wires:" in content
        assert "#block(breakable: false)" in content

    def test_diagram_page_absolute_path(self, config, tmp_path):
        config.root_dir = str(tmp_path)
        abs_svg = os.path.join(str(tmp_path), "drawings", "W002.svg")
        compiler = HarnessDocCompiler(config)
        compiler.add_diagram_page("W002", abs_svg)
        content = compiler.build_typst_string()
        assert "Cable nr: W002" in content
        # Path should be converted to relative
        assert str(tmp_path).replace("\\", "/") not in content or "drawings" in content


class TestCustomPage:
    def test_custom_page(self, config, tmp_path):
        config.root_dir = str(tmp_path)
        compiler = HarnessDocCompiler(config)
        compiler.add_custom_page("#text[Custom content here]")
        content = compiler.build_typst_string()
        assert "#text[Custom content here]" in content
        assert "#pagebreak(weak: true)" in content


class TestFullDocument:
    def test_full_assembly(self, config, tmp_path):
        config.root_dir = str(tmp_path)
        md_file = os.path.join(str(tmp_path), "front.md")
        with open(md_file, "w") as f:
            f.write("## Revisions\n")

        compiler = HarnessDocCompiler(config)
        compiler.add_title_page(md_file)
        compiler.add_toc()
        compiler.add_diagram_page("W001", "drawings/W001.svg")
        content = compiler.build_typst_string()

        # Check template import
        assert "#import" in content
        assert "harness_doc" in content
        assert "#show: harness_doc.with(" in content

        # Check config values appear
        assert 'title: "Test Harness"' in content
        assert 'version: "01"' in content
        assert 'date: "01/01/2026"' in content


class TestLogoHandling:
    def test_no_logo(self, config, tmp_path):
        config.root_dir = str(tmp_path)
        compiler = HarnessDocCompiler(config)
        content = compiler.build_typst_string()
        assert "logo_path: none" in content

    def test_with_logo(self, config_with_logo):
        compiler = HarnessDocCompiler(config_with_logo)
        content = compiler.build_typst_string()
        assert "logo_path: none" not in content
        assert 'logo_path: "' in content


class TestTemplatePath:
    def test_template_exists(self):
        compiler = HarnessDocCompiler(HarnessDocConfig())
        path = compiler._get_template_path()
        assert os.path.exists(path)
        assert path.endswith("harness_doc.typ")


class TestCompileRequiresTypst:
    def test_compile_import_error(self, config, tmp_path, monkeypatch):
        """compile() raises ImportError when typst is not installed."""
        config.root_dir = str(tmp_path)
        compiler = HarnessDocCompiler(config)

        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "typst":
                raise ImportError("No module named 'typst'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        with pytest.raises(ImportError, match="typst"):
            compiler.compile(os.path.join(str(tmp_path), "out.pdf"))
