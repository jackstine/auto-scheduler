"""Unit tests for aggregation logic."""

import json

from src.nodes.aggregate import aggregate


def test_combines_files(tmp_path):
    f1 = tmp_path / "site_a.json"
    f2 = tmp_path / "site_b.json"
    f1.write_text(json.dumps([{"name": "Event A", "date": "2026-03-01", "time": "18:00"}]))
    f2.write_text(json.dumps([{"name": "Event B", "date": "2026-04-01", "time": "19:00"}]))

    result = aggregate([str(f1), str(f2)])
    assert len(result) == 2
    names = {e["name"] for e in result}
    assert names == {"Event A", "Event B"}


def test_injects_source_url(tmp_path):
    f = tmp_path / "aimug.org_events.json"
    f.write_text(json.dumps([{"name": "Test", "date": "2026-03-01", "time": "18:00"}]))

    result = aggregate([str(f)])
    assert result[0]["source_url"] == "https://aimug.org/events"


def test_skips_bad_files(tmp_path):
    f1 = tmp_path / "good.json"
    f2 = tmp_path / "bad.json"
    f1.write_text(json.dumps([{"name": "Good", "date": "2026-03-01", "time": "18:00"}]))
    f2.write_text("not json")

    result = aggregate([str(f1), str(f2)])
    assert len(result) == 1


def test_empty_files(tmp_path):
    f = tmp_path / "empty.json"
    f.write_text("[]")

    result = aggregate([str(f)])
    assert result == []
