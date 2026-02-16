"""Filter and sort node: remove past events and sort by date/time."""

import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)


def filter_sort(events: list[dict], output_dir: str) -> int:
    """Filter out past events, sort by date then time, write to raw_output.json."""
    today = date.today().isoformat()

    # Filter: keep events with date >= today, or missing date
    future = [e for e in events if e.get("date", "") >= today]
    logger.info(f"Filtered: {len(future)} future events (removed {len(events) - len(future)} past)")

    # Sort by date, then time
    future.sort(key=lambda e: (e.get("date", ""), e.get("time", "")))

    # Write output
    output_path = Path(output_dir) / "raw_output.json"
    output_path.write_text(json.dumps(future, indent=2))
    logger.info(f"Wrote {len(future)} events to {output_path}")

    return len(future)
