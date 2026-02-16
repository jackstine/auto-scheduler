"""Utility functions for filename encoding/decoding."""

import re


def url_to_filename(url: str) -> str:
    """Convert a URL to a safe filename."""
    name = re.sub(r"https?://", "", url)
    name = re.sub(r"[/:]", "_", name)
    name = name.rstrip("_")
    return name


def filename_to_url(filename: str) -> str:
    """Best-effort reverse of url_to_filename. Assumes https."""
    name = filename.removesuffix(".md").removesuffix(".json")
    # First underscore group after domain is the path separator
    # This is approximate — replace first _ with :// and rest with /
    parts = name.split("_", 1)
    if len(parts) == 2:
        return f"https://{parts[0]}/{parts[1].replace('_', '/')}"
    return f"https://{name}"
