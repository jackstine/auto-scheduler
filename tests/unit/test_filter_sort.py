"""Unit tests for filter and sort logic."""

import json
from datetime import date, timedelta

from src.nodes.filter_sort import filter_sort


def _today():
    return date.today().isoformat()


def _yesterday():
    return (date.today() - timedelta(days=1)).isoformat()


def _tomorrow():
    return (date.today() + timedelta(days=1)).isoformat()


def test_removes_past_events(tmp_path):
    events = [
        {"name": "Past", "date": _yesterday(), "time": "18:00"},
        {"name": "Future", "date": _tomorrow(), "time": "18:00"},
    ]
    count = filter_sort(events, str(tmp_path))
    output = json.loads((tmp_path / "raw_output.json").read_text())
    assert count == 1
    assert output[0]["name"] == "Future"


def test_keeps_today(tmp_path):
    events = [{"name": "Today", "date": _today(), "time": "18:00"}]
    count = filter_sort(events, str(tmp_path))
    assert count == 1


def test_sorts_by_date_then_time(tmp_path):
    events = [
        {"name": "Late", "date": "2026-06-01", "time": "20:00"},
        {"name": "Early", "date": "2026-05-01", "time": "10:00"},
        {"name": "Same Day Later", "date": "2026-05-01", "time": "18:00"},
    ]
    filter_sort(events, str(tmp_path))
    output = json.loads((tmp_path / "raw_output.json").read_text())
    assert output[0]["name"] == "Early"
    assert output[1]["name"] == "Same Day Later"
    assert output[2]["name"] == "Late"


def test_handles_missing_fields(tmp_path):
    events = [
        {"name": "No time", "date": _tomorrow()},
        {"name": "Has time", "date": _tomorrow(), "time": "10:00"},
    ]
    count = filter_sort(events, str(tmp_path))
    assert count == 2


def test_empty_input(tmp_path):
    count = filter_sort([], str(tmp_path))
    assert count == 0
    output = json.loads((tmp_path / "raw_output.json").read_text())
    assert output == []
