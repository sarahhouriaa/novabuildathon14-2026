"""Convert parser output into compact, chart-ready dashboard data."""

from __future__ import annotations

from collections import Counter
from typing import Any


def build_dashboard(parsed: dict[str, Any]) -> dict[str, Any]:
    files = parsed["files"]
    return {
        "summary": {
            "file_count": parsed["file_count"],
            "parsed_count": sum(item["status"] == "parsed" for item in files),
            "binary_count": sum(item["status"] == "binary" for item in files),
            "error_count": sum(item["status"] == "error" for item in files),
        },
        "behavioral_sessions": [
            session for item in files if (session := _behavioral_session(item)) is not None
        ],
        "trigger_sessions": [
            session for item in files if (session := _trigger_session(item)) is not None
        ],
        "files": [
            {
                "path": item["path"],
                "extension": item["extension"] or "—",
                "size": _human_size(item["size_bytes"]),
                "status": item["status"],
            }
            for item in files
        ],
    }


def _behavioral_session(item: dict[str, Any]) -> dict[str, Any] | None:
    if item["status"] != "parsed" or item["extension"] != ".csv":
        return None
    rows = item["data"]["rows"]
    trials = []
    for index, row in enumerate(rows, start=1):
        response = _first_value(row, "trials.make_or_miss.keys", "make_or_miss.keys")
        reaction_time = _as_float(_first_value(row, "trials.make_or_miss.rt", "make_or_miss.rt"))
        trials.append(
            {
                "trial": _as_int(row.get("thisN"), index - 1) + 1,
                "reaction_time": reaction_time,
                "made": str(response).strip().lower() == "y",
            }
        )
    makes = sum(trial["made"] for trial in trials)
    reaction_times = [trial["reaction_time"] for trial in trials if trial["reaction_time"] is not None]
    return {
        "name": item["name"],
        "trials": trials,
        "trial_count": len(trials),
        "makes": makes,
        "misses": len(trials) - makes,
        "average_reaction_time": round(sum(reaction_times) / len(reaction_times), 3) if reaction_times else None,
    }


def _trigger_session(item: dict[str, Any]) -> dict[str, Any] | None:
    if item["status"] != "parsed" or item["extension"] != ".trg":
        return None
    events = [event for event in item["data"]["events"] if event["code"] is not None]
    counts = Counter(str(event["code"]) for event in events)
    return {
        "name": item["name"],
        "events": [{"time": event["time_seconds"], "code": str(event["code"])} for event in events],
        "event_count": len(events),
        "duration": round(max((event["time_seconds"] for event in events), default=0), 2),
        "code_counts": dict(sorted(counts.items())),
    }


def _first_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, "", "None"):
            return value
    return None


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"
