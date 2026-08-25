"""Parsers for the files stored in the project's dataset directory.

The public output is deliberately made only of JSON-serializable Python types so
that it can later be returned by a Django view without another conversion layer.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Callable


class DatasetParserError(ValueError):
    """Raised when the dataset path is invalid or a known file is malformed."""


Parser = Callable[[Path], Any]


class DatasetParser:
    """Read every file beneath a dataset directory.

    Text-based formats are decoded into structured values. Proprietary binary
    formats are represented by metadata, so callers can still discover and pair
    them without loading many megabytes into memory.
    """

    _BINARY_FORMATS = {".cnt", ".evt", ".psydat", ".xlsx", ".docx"}

    def __init__(self, dataset_path: str | Path):
        self.dataset_path = Path(dataset_path).expanduser().resolve()

    def parse(self) -> dict[str, Any]:
        """Return a manifest and parsed contents for the configured directory."""
        if not self.dataset_path.exists():
            raise DatasetParserError(f"Dataset path does not exist: {self.dataset_path}")
        if not self.dataset_path.is_dir():
            raise DatasetParserError(f"Dataset path is not a directory: {self.dataset_path}")

        files = [
            self._parse_file(path)
            for path in sorted(self.dataset_path.rglob("*"))
            if path.is_file() and not any(part.startswith(".") for part in path.relative_to(self.dataset_path).parts)
        ]
        return {
            "root": str(self.dataset_path),
            "file_count": len(files),
            "files": files,
        }

    def _parse_file(self, path: Path) -> dict[str, Any]:
        extension = path.suffix.lower()
        parsers: dict[str, Parser] = {
            ".csv": self._parse_csv,
            ".trg": self._parse_trigger,
            ".seg": self._parse_segment,
            ".log": self._parse_log,
            ".json": self._parse_json,
            ".bst": self._parse_json,
        }

        result: dict[str, Any] = {
            "path": path.relative_to(self.dataset_path).as_posix(),
            "name": path.name,
            "extension": extension,
            "size_bytes": path.stat().st_size,
        }
        parser = parsers.get(extension)
        if parser is not None:
            try:
                result.update(status="parsed", data=parser(path))
            except (csv.Error, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
                result.update(status="error", error=str(exc))
        elif extension in self._BINARY_FORMATS:
            result.update(status="binary", data=self._binary_metadata(path))
        else:
            result.update(status="unsupported", data=None)
        return result

    @staticmethod
    def _parse_csv(path: Path) -> dict[str, Any]:
        # utf-8-sig removes the BOM emitted by PsychoPy on the first heading.
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError("CSV file has no header")
            rows = [dict(row) for row in reader]
        return {"columns": reader.fieldnames, "row_count": len(rows), "rows": rows}

    @staticmethod
    def _parse_trigger(path: Path) -> dict[str, Any]:
        events = []
        with path.open("r", encoding="ascii") as handle:
            for line_number, line in enumerate(handle, start=1):
                parts = line.split(maxsplit=3)
                if not parts:
                    continue
                if len(parts) < 2:
                    raise ValueError(f"Invalid trigger on line {line_number}")
                events.append(
                    {
                        "time_seconds": float(parts[0]),
                        "sample": int(parts[1]),
                        "code": parts[2] if len(parts) >= 3 else None,
                        "label": parts[3].strip() if len(parts) == 4 else None,
                    }
                )
        return {"event_count": len(events), "events": events}

    @staticmethod
    def _parse_segment(path: Path) -> dict[str, Any]:
        lines = [line.strip() for line in path.read_text(encoding="ascii").splitlines() if line.strip()]
        if not lines or "=" not in lines[0]:
            raise ValueError("Segment file has no NumberSegments header")
        key, value = lines[0].split("=", maxsplit=1)
        if key.strip() != "NumberSegments":
            raise ValueError("Unexpected segment header")
        segments = []
        for line_number, line in enumerate(lines[1:], start=2):
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"Invalid segment on line {line_number}")
            segments.append({"position": float(parts[0]), "duration": float(parts[1]), "sample": int(parts[2])})
        return {"declared_count": int(value), "segment_count": len(segments), "segments": segments}

    @staticmethod
    def _parse_log(path: Path) -> dict[str, Any]:
        entries = []
        for line in path.read_text(encoding="utf-8").splitlines():
            parts = line.split(maxsplit=2)
            if not parts:
                continue
            entry: dict[str, Any] = {"message": line}
            if len(parts) == 3:
                try:
                    entry = {"time_seconds": float(parts[0]), "level": parts[1], "message": parts[2]}
                except ValueError:
                    pass
            entries.append(entry)
        return {"entry_count": len(entries), "entries": entries}

    @staticmethod
    def _parse_json(path: Path) -> Any:
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)

    @staticmethod
    def _binary_metadata(path: Path) -> dict[str, Any]:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return {"sha256": digest.hexdigest()}


def parse_dataset(dataset_path: str | Path) -> dict[str, Any]:
    """Convenience function for parsing a dataset directory."""
    return DatasetParser(dataset_path).parse()
