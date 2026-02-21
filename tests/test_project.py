"""Tests for the Project high-level API."""

from unittest.mock import MagicMock, patch

import pytest
from wireviz_yaml_generator.exceptions import ConfigurationError
from wireviz_yaml_generator.project import Project


class TestConstructorValidation:
    def test_no_data_source_raises(self):
        with pytest.raises(ConfigurationError, match="db= or csv="):
            Project(title="Test")

    def test_both_data_sources_raises(self):
        with pytest.raises(ConfigurationError, match="not both"):
            Project(title="Test", db="test.db", csv="test.csv")

    def test_db_source_accepted(self):
        p = Project(title="Test", db="test.db")
        assert p._db == "test.db"
        assert p._csv is None

    def test_csv_source_accepted(self):
        p = Project(title="Test", csv="test.csv")
        assert p._csv == "test.csv"
        assert p._db is None


class TestCableFilters:
    def test_basic_range(self):
        p = Project(title="Test", db="test.db", cable_start=1, cable_end=3)
        filters = p._build_cable_filters()
        assert filters == ["W001", "W002", "W003"]

    def test_skip_cables(self):
        p = Project(title="Test", db="test.db", cable_start=1, cable_end=5, skip_cables=[2, 4])
        filters = p._build_cable_filters()
        assert filters == ["W001", "W003", "W005"]

    def test_empty_range(self):
        p = Project(title="Test", db="test.db", cable_start=5, cable_end=3)
        filters = p._build_cable_filters()
        assert filters == []

    def test_zero_padded(self):
        p = Project(title="Test", db="test.db", cable_start=1, cable_end=1)
        filters = p._build_cable_filters()
        assert filters == ["W001"]


class TestPageRegistration:
    def test_front_page(self):
        p = Project(title="Test", db="test.db")
        assert p._front_page_md is None
        p.front_page("docs/front.md")
        assert p._front_page_md == "docs/front.md"

    def test_content_pages(self):
        p = Project(title="Test", db="test.db")
        assert p._content_pages == []
        p.content_page("docs/desc.md")
        p.content_page("docs/notes.md")
        assert p._content_pages == ["docs/desc.md", "docs/notes.md"]


class TestBuildOrchestration:
    @patch("wireviz_yaml_generator.project.WorkflowManager")
    @patch("wireviz_yaml_generator.project.shutil.which", return_value=None)
    def test_build_without_pdf(self, mock_which, mock_wf_cls, tmp_path):
        """build() without pdf_path skips PDF generation."""
        mock_source = MagicMock()
        mock_source.check_cable_existence.return_value = True

        mock_wf = MagicMock()
        mock_wf_cls.return_value = mock_wf

        p = Project(
            title="Test",
            db="test.db",
            cable_start=1,
            cable_end=2,
            yaml_dir=str(tmp_path / "yaml"),
            drawings_dir=str(tmp_path / "drawings"),
            attachments_dir=str(tmp_path / "attachments"),
            resources_dir=str(tmp_path / "resources"),
        )

        with (
            patch.object(p, "_create_data_source", return_value=mock_source),
            patch.object(p, "_build_pdf") as mock_pdf,
        ):
            p.build(pdf_path=None, create_bom=True, create_labels=True)
            mock_pdf.assert_not_called()

        mock_wf.run_attachment_workflow.assert_called_once()
        assert mock_wf.run_yaml_workflow.call_count == 2

    @patch("wireviz_yaml_generator.project.WorkflowManager")
    @patch("wireviz_yaml_generator.project.shutil.which", return_value=None)
    def test_build_skips_nonexistent_cables(self, mock_which, mock_wf_cls, tmp_path):
        """build() skips cables where check_cable_existence returns False."""
        mock_source = MagicMock()
        mock_source.check_cable_existence.side_effect = lambda c: c == "W001"

        mock_wf = MagicMock()
        mock_wf_cls.return_value = mock_wf

        p = Project(
            title="Test",
            db="test.db",
            cable_start=1,
            cable_end=3,
            yaml_dir=str(tmp_path / "yaml"),
            drawings_dir=str(tmp_path / "drawings"),
            attachments_dir=str(tmp_path / "attachments"),
            resources_dir=str(tmp_path / "resources"),
        )

        with patch.object(p, "_create_data_source", return_value=mock_source):
            p.build(pdf_path=None)

        # Only W001 should be processed
        assert mock_wf.run_yaml_workflow.call_count == 1
        assert mock_wf.run_yaml_workflow.call_args[0][0] == "W001"

    @patch("wireviz_yaml_generator.project.WorkflowManager")
    @patch("wireviz_yaml_generator.project.shutil.which", return_value="/usr/bin/wireviz")
    @patch("wireviz_yaml_generator.project.subprocess.run")
    def test_build_with_wireviz(self, mock_run, mock_which, mock_wf_cls, tmp_path):
        """build() invokes wireviz subprocess for each cable."""
        mock_source = MagicMock()
        mock_source.check_cable_existence.return_value = True

        mock_wf = MagicMock()
        mock_wf_cls.return_value = mock_wf

        p = Project(
            title="Test",
            db="test.db",
            cable_start=1,
            cable_end=1,
            yaml_dir=str(tmp_path / "yaml"),
            drawings_dir=str(tmp_path / "drawings"),
            attachments_dir=str(tmp_path / "attachments"),
            resources_dir=str(tmp_path / "resources"),
        )

        with patch.object(p, "_create_data_source", return_value=mock_source):
            p.build(pdf_path=None)

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "/usr/bin/wireviz" in call_args[0][0]
        assert "--format" in call_args[0][0]
        assert "s" in call_args[0][0]


class TestAutoGenerateCableDes:
    def test_csv_with_auto_generate(self):
        p = Project(title="Test", csv="test.csv", auto_generate_cable_des=True)
        assert p._auto_generate_cable_des is True


class TestBuildPdf:
    @patch("wireviz_yaml_generator.project.WorkflowManager")
    @patch("wireviz_yaml_generator.project.shutil.which", return_value=None)
    def test_build_calls_pdf(self, mock_which, mock_wf_cls, tmp_path):
        """build() with pdf_path calls _build_pdf."""
        mock_source = MagicMock()
        mock_source.check_cable_existence.return_value = False

        mock_wf = MagicMock()
        mock_wf_cls.return_value = mock_wf

        p = Project(
            title="Test",
            db="test.db",
            cable_start=1,
            cable_end=1,
            yaml_dir=str(tmp_path / "yaml"),
            drawings_dir=str(tmp_path / "drawings"),
            attachments_dir=str(tmp_path / "attachments"),
            resources_dir=str(tmp_path / "resources"),
        )

        with (
            patch.object(p, "_create_data_source", return_value=mock_source),
            patch.object(p, "_build_pdf") as mock_pdf,
        ):
            p.build(pdf_path="output.pdf")
            mock_pdf.assert_called_once_with("output.pdf", [])
