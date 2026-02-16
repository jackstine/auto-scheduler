"""Validation logic for agent-produced event JSON."""

import json
import logging

logger = logging.getLogger(__name__)

ALLOWED_FIELDS = {"name", "date", "time", "time_zone", "venue", "address", "event_url", "source_url", "description"}


def validate_response(raw: str) -> tuple[list[dict] | None, str | None]:
    """Validate an agent response.

    Returns (valid_objects, error).
    If the response is not valid JSON or not an array, returns (None, error_msg) to trigger retry.
    If it is a valid array, returns (list_of_valid_objects, None). Invalid individual objects are discarded.
    """
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first and last fence lines
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"

    if not isinstance(data, list):
        return None, f"Expected array, got {type(data).__name__}"

    valid = []
    for i, obj in enumerate(data):
        if not isinstance(obj, dict):
            logger.warning(f"Object at index {i} is not a dict, skipping")
            continue
        unknown = set(obj.keys()) - ALLOWED_FIELDS
        if unknown:
            logger.warning(f"Object at index {i} has unknown fields {unknown}, skipping")
            continue
        valid.append(obj)

    logger.info(f"Validation: {len(valid)}/{len(data)} objects valid")
    return valid, None
