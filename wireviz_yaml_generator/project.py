"""High-level Project API for the WireViz YAML Generator.

Orchestrates the entire pipeline: data source -> YAML -> WireViz SVG -> PDF.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from wireviz_yaml_generator.exceptions import ConfigurationError
from wireviz_yaml_generator.workflow_manager import WorkflowManager


class Project:
    """High-level orchestrator for harness documentation generation.

    Accepts CSV or SQLite input, generates WireViz YAML and SVG diagrams,
    manufacturing attachments (BOM, labels), and optionally compiles
    everything into a PDF document via Typst.

    Example::

        project = Project(
            title="Juicebox Cabinet Harness Documentation",
            version="02",
            date="19/01/2026",
            logo="src/ZENLogo.png",
            db="data/master.db", # choose between db or csv
            csv="data/master.csv",
            cable_start=1,
            cable_end=44,
            skip_cables=[10, 21, 32, 43],
        )
        project.front_page("docs/front.md")
        project.content_page("docs/description.md")
        project.build(pdf_path="output/harness_doc.pdf")
    """

    def __init__(
        self,
        *,
        title: str,
        version: str = "01",
        date: str = "",
        logo: str | None = None,
        font: str = "Times New Roman",
        proprietary_notice: str | None = None,
        # Data source (exactly one required)
        db: str | None = None,
        csv: str | None = None,
        auto_generate_cable_des: bool = False,
        # Cable selection
        cable_prefix: str = "W",
        cable_start: int = 0,
        cable_end: int = 50,
        skip_cables: list[int] | None = None,
        # Pin ordering
        pins_last: list[str] | None = None,
        # Display
        cable_titles: dict[str, str] | None = None,
        # Output directories
        yaml_dir: str = "drawings/src",
        drawings_dir: str = "drawings/harness",
        attachments_dir: str = "attachments",
        resources_dir: str = "drawings/resources",
    ) -> None:
        if db and csv:
            raise ConfigurationError("Specify either db= or csv=, not both.")
        if not db and not csv:
            raise ConfigurationError("Specify either db= or csv= as data source.")

        self.title = title
        self.version = version
        self.date = date
        self.logo = logo
        self.font = font
        self.proprietary_notice = proprietary_notice

        self._db = db
        self._csv = csv
        self._auto_generate_cable_des = auto_generate_cable_des
        self._cable_prefix = cable_prefix
        self._pins_last = pins_last
        self._cable_titles = cable_titles or {}

        self.cable_start = cable_start
        self.cable_end = cable_end
        self.skip_cables = skip_cables or []

        self.yaml_dir = yaml_dir
        self.drawings_dir = drawings_dir
        self.attachments_dir = attachments_dir
        self.resources_dir = resources_dir

        self._front_page_md: str | None = None
        self._content_pages: list[str] = []

    def front_page(self, md_path: str) -> None:
        """Set the front page markdown file."""
        self._front_page_md = md_path

    def content_page(self, md_path: str) -> None:
        """Add a content section from markdown. Can be called multiple times."""
        self._content_pages.append(md_path)

    def build(
        self,
        pdf_path: str | None = None,
        create_bom: bool = True,
        create_labels: bool = True,
    ) -> None:
        """Run the full pipeline: YAML -> SVG -> attachments -> PDF."""
        data_source = self._create_data_source()
        cable_filters = self._build_cable_filters()
        workflow = WorkflowManager(data_source)

        # Scan for available connector images
        resource_path = Path(self.resources_dir)
        available_images = self._get_available_images(resource_path)

        # Ensure output directories exist
        Path(self.yaml_dir).mkdir(parents=True, exist_ok=True)
        Path(self.drawings_dir).mkdir(parents=True, exist_ok=True)
        Path(self.attachments_dir).mkdir(parents=True, exist_ok=True)

        # Attachments (BOM / Labels)
        if create_bom or create_labels:
            workflow.run_attachment_workflow(
                cable_filters,
                self.attachments_dir,
                create_bom=create_bom,
                create_labels=create_labels,
            )

        # YAML + SVG generation
        wireviz_executable = shutil.which("wireviz")
        svg_paths: list[tuple[str, str]] = []  # (cable_des, svg_path)

        for cable_filter in cable_filters:
            if not data_source.check_cable_existence(cable_filter):
                print(f"   Skipping {cable_filter}. No data found.")
                continue

            yaml_filepath = str(Path(self.yaml_dir) / f"{cable_filter}.yaml")

            workflow.run_yaml_workflow(cable_filter, yaml_filepath, available_images, pins_last=self._pins_last)

            if wireviz_executable:
                svg_path = str(Path(self.drawings_dir) / f"{cable_filter}.svg")
                command = [
                    wireviz_executable,
                    yaml_filepath,
                    "--format",
                    "s",
                    "--output-dir",
                    self.drawings_dir,
                ]
                try:
                    subprocess.run(command, check=True, capture_output=True, text=True)
                    svg_paths.append((cable_filter, svg_path))
                    print(f"   Diagram generated for {cable_filter}")
                except subprocess.CalledProcessError as e:
                    print(f"   WireViz Error for {cable_filter}: {e.stderr}")
            else:
                # No wireviz CLI, check if SVG already exists
                svg_path = str(Path(self.drawings_dir) / f"{cable_filter}.svg")
                if Path(svg_path).exists():
                    svg_paths.append((cable_filter, svg_path))

        # PDF generation
        if pdf_path is not None:
            self._build_pdf(pdf_path, svg_paths)

    def _create_data_source(self):
        """Create the appropriate data source."""
        if self._db:
            from wireviz_yaml_generator.data_access import SqliteDataSource

            return SqliteDataSource(self._db)
        else:
            from wireviz_yaml_generator.csv_data_source import CsvDataSource

            assert self._csv is not None
            return CsvDataSource(
                self._csv,
                auto_generate_cable_des=self._auto_generate_cable_des,
                cable_prefix=self._cable_prefix,
            )

    def _build_cable_filters(self) -> list[str]:
        """Build the list of cable designators to process."""
        return [
            f"{self._cable_prefix}{i:03d}"
            for i in range(self.cable_start, self.cable_end + 1)
            if i not in self.skip_cables
        ]

    def _get_available_images(self, resource_path: Path) -> set[str]:
        """Scan a directory for available connector image files."""
        if not resource_path.is_dir():
            return set()
        return {f.name for f in resource_path.glob("*.png")}

    def _build_pdf(self, pdf_path: str, svg_paths: list[tuple[str, str]]) -> None:
        """Compile the PDF document from collected content."""
        from wireviz_yaml_generator.rendering.typst.compiler import (
            HarnessDocCompiler,
            HarnessDocConfig,
        )

        config = HarnessDocConfig(
            title=self.title,
            version=self.version,
            date=self.date,
            logo_path=self.logo,
            font_family=self.font,
            proprietary_notice=self.proprietary_notice,
            root_dir=".",
        )

        compiler = HarnessDocCompiler(config)

        # Title page
        compiler.add_title_page(self._front_page_md)

        # Table of contents
        compiler.add_toc()

        # Content pages
        for md_path in self._content_pages:
            compiler.add_content_page(md_path)

        # Diagram pages
        for cable_des, svg_path in svg_paths:
            title = cable_des
            if cable_des in self._cable_titles:
                title = f"{cable_des} ({self._cable_titles[cable_des]})"
            compiler.add_diagram_page(title, svg_path)

        # Ensure output directory exists
        Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)

        compiler.compile(pdf_path)
        print(f"   PDF generated: {pdf_path}")
