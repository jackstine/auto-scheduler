"""Aggregate node: combine all post-validation JSON files and inject source_url."""

import json
import logging
from pathlib import Path

from src.utils import filename_to_url

logger = logging.getLogger(__name__)


def aggregate(parsed_files: list[str]) -> list[dict]:
    """Read all post_validation JSON files and combine into a single list."""
    all_events = []
    for filepath in parsed_files:
        try:
            data = json.loads(Path(filepath).read_text())
            source_url = filename_to_url(Path(filepath).stem)
            for event in data:
                event["source_url"] = source_url
            all_events.extend(data)
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            continue

    logger.info(f"Aggregated {len(all_events)} total events")
    return all_events
