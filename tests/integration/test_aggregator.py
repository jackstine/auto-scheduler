"""Integration test: crawl + aggregate (no LLM)."""

import json
from pathlib import Path

from src.nodes.aggregate import aggregate


def test_aggregate_from_crawled_output(tmp_path):
    """Create mock post_validation files and verify aggregation."""
    f1 = tmp_path / "aimug.org_events.json"
    f2 = tmp_path / "www.meetup.com_aittg-austin.json"

    f1.write_text(json.dumps([
        {"name": "AIMUG Mixer", "date": "2026-03-04", "time": "18:00", "venue": "ACC RGC 3000"},
    ]))
    f2.write_text(json.dumps([
        {"name": "AI Meetup", "date": "2026-02-04", "time": "17:30", "venue": "Capital Factory"},
        {"name": "AI Governance", "date": "2026-02-24", "time": "17:30", "venue": "Coder Austin"},
    ]))

    result = aggregate([str(f1), str(f2)])
    assert len(result) == 3
    # source_url injected
    assert all("source_url" in e for e in result)
