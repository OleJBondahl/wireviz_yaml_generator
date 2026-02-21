"""CSV Data Source — reads a denormalized CSV file as an alternative to SQLite."""

import csv
from pathlib import Path

from .exceptions import DataSourceError
from .models import CableRow, ConnectorRow, DesignatorRow, NetRow

REQUIRED_COLUMNS = frozenset(
    {
        "cable_des",
        "comp_des_1",
        "conn_des_1",
        "pin_1",
        "comp_des_2",
        "conn_des_2",
        "pin_2",
    }
)


class CsvDataSource:
    """Reads a single denormalized CSV file and provides the same interface as SqliteDataSource.

    Each CSV row represents one wire connection with optional inline connector/cable metadata.
    Data is parsed once at construction time and served from memory.

    Required columns (must be present as headers):
        cable_des, comp_des_1, conn_des_1, pin_1, comp_des_2, conn_des_2, pin_2

    Empty-value behavior:
        cable_des       — must be non-empty unless auto_generate_cable_des=True
        comp_des_1/2    — required (non-empty)
        pin_1/2         — required (non-empty)
        net_name        — optional (defaults to "" if column absent)
        conn_des_1/2    — can be empty (component has no sub-connector)
        conn_mpn_1/2    — can be empty/omitted (no designator entry for that side)
        pincount, mate_mpn, pin_mpn — can be empty/omitted (connector skipped in catalog)
        wire_gauge, length — can be empty/omitted (cable skipped in cable table)
        conn_description, conn_manufacturer, cable_note — can be empty/omitted (defaults to "")
    """

    def __init__(
        self,
        csv_filepath: str,
        *,
        auto_generate_cable_des: bool = False,
        cable_prefix: str = "W",
    ) -> None:
        path = Path(csv_filepath)
        if not path.exists():
            raise DataSourceError(f"CSV file not found: {csv_filepath}")

        try:
            with path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    raise DataSourceError(f"CSV file is empty: {csv_filepath}")

                columns = set(reader.fieldnames)
                missing = REQUIRED_COLUMNS - columns
                if missing:
                    raise DataSourceError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

                self._rows: list[dict[str, str]] = list(reader)
        except DataSourceError:
            raise
        except Exception as e:
            raise DataSourceError(f"Failed to read CSV file '{csv_filepath}': {e}") from e

        if not self._rows:
            raise DataSourceError(f"CSV file has no data rows: {csv_filepath}")

        auto_counter = 0
        prev_comp_des = None
        for row in self._rows:
            cable_des = row.get("cable_des", "").strip()
            if not cable_des:
                if not auto_generate_cable_des:
                    raise DataSourceError(
                        "Row has empty 'cable_des' value. Set auto_generate_cable_des=True to auto-assign designators."
                    )
                # Group consecutive rows with the same comp_des_1 under one cable
                comp_des = row.get("comp_des_1", "").strip()
                if comp_des != prev_comp_des:
                    auto_counter += 1
                    prev_comp_des = comp_des
                row["cable_des"] = f"{cable_prefix}{auto_counter:03d}"
            else:
                row["cable_des"] = cable_des
                prev_comp_des = None

        self._columns = columns

    def _get(self, row: dict[str, str], key: str) -> str:
        """Return stripped value or empty string if column is absent."""
        return row.get(key, "").strip()

    # --- DataSourceProtocol methods ---

    def check_cable_existence(self, cable_des: str) -> bool:
        return any(row["cable_des"] == cable_des for row in self._rows)

    def load_net_table(self, cable_des_filter: str = "") -> list[NetRow]:
        rows = self._rows
        if cable_des_filter:
            rows = [r for r in rows if r["cable_des"] == cable_des_filter]
        return [
            NetRow(
                cable_des=r["cable_des"],
                comp_des_1=r["comp_des_1"],
                conn_des_1=r["conn_des_1"],
                pin_1=r["pin_1"],
                comp_des_2=r["comp_des_2"],
                conn_des_2=r["conn_des_2"],
                pin_2=r["pin_2"],
                net_name=r.get("net_name", ""),
            )
            for r in rows
        ]

    def load_designator_table(self) -> list[DesignatorRow]:
        seen: set[tuple[str, str, str]] = set()
        result: list[DesignatorRow] = []

        for row in self._rows:
            for suffix in ("1", "2"):
                comp_des = self._get(row, f"comp_des_{suffix}")
                conn_des = self._get(row, f"conn_des_{suffix}")
                conn_mpn = self._get(row, f"conn_mpn_{suffix}")
                if not conn_mpn:
                    continue
                key = (comp_des, conn_des, conn_mpn)
                if key not in seen:
                    seen.add(key)
                    result.append(DesignatorRow(comp_des=comp_des, conn_des=conn_des, conn_mpn=conn_mpn))

        return result

    def load_connector_table(self) -> list[ConnectorRow]:
        seen: dict[str, ConnectorRow] = {}

        for row in self._rows:
            for suffix in ("1", "2"):
                mpn = self._get(row, f"conn_mpn_{suffix}")
                if not mpn or mpn in seen:
                    continue

                pincount_str = self._get(row, "pincount")
                mate_mpn = self._get(row, "mate_mpn")
                pin_mpn = self._get(row, "pin_mpn")

                if not (pincount_str and mate_mpn and pin_mpn):
                    continue

                try:
                    pincount = int(pincount_str)
                except ValueError:
                    continue

                seen[mpn] = ConnectorRow(
                    mpn=mpn,
                    pincount=pincount,
                    mate_mpn=mate_mpn,
                    pin_mpn=pin_mpn,
                    description=self._get(row, "conn_description"),
                    manufacturer=self._get(row, "conn_manufacturer"),
                )

        return list(seen.values())

    def load_cable_table(self) -> list[CableRow]:
        seen: dict[str, CableRow] = {}

        for row in self._rows:
            cable_des = row["cable_des"]
            if cable_des in seen:
                continue

            gauge_str = self._get(row, "wire_gauge")
            length_str = self._get(row, "length")

            if not gauge_str:
                continue

            try:
                wire_gauge = float(gauge_str)
            except ValueError:
                continue

            try:
                length = float(length_str) if length_str else 0.0
            except ValueError:
                length = 0.0

            category = self._get(row, "category") or "bundle"
            colors = self._get(row, "colors")

            seen[cable_des] = CableRow(
                cable_des=cable_des,
                wire_gauge=wire_gauge,
                length=length,
                note=self._get(row, "cable_note"),
                category=category,
                colors=colors,
            )

        return list(seen.values())
