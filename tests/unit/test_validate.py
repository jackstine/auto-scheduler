"""Unit tests for validation logic."""

from src.nodes.validate import validate_response


def test_valid_array():
    raw = '[{"name": "Test", "date": "2026-03-01", "time": "18:00"}]'
    result, error = validate_response(raw)
    assert error is None
    assert len(result) == 1
    assert result[0]["name"] == "Test"


def test_invalid_json():
    result, error = validate_response("not json at all")
    assert result is None
    assert "Invalid JSON" in error


def test_not_array():
    result, error = validate_response('{"name": "Test"}')
    assert result is None
    assert "Expected array" in error


def test_unknown_fields_rejected():
    raw = '[{"name": "Test", "date": "2026-03-01", "time": "18:00", "bogus": "bad"}]'
    result, error = validate_response(raw)
    assert error is None
    assert len(result) == 0


def test_missing_optional_fields_ok():
    raw = '[{"name": "Test", "date": "2026-03-01", "time": "18:00"}]'
    result, error = validate_response(raw)
    assert error is None
    assert len(result) == 1


def test_empty_array():
    result, error = validate_response("[]")
    assert error is None
    assert result == []


def test_strips_code_fences():
    raw = '```json\n[{"name": "Test", "date": "2026-03-01", "time": "18:00"}]\n```'
    result, error = validate_response(raw)
    assert error is None
    assert len(result) == 1


def test_mixed_valid_invalid_objects():
    raw = """[
        {"name": "Good", "date": "2026-03-01", "time": "18:00"},
        {"name": "Bad", "date": "2026-03-01", "time": "18:00", "unknown_field": "x"},
        {"name": "Also Good", "date": "2026-04-01", "time": "19:00", "venue": "Place", "address": "123 Main St"}
    ]"""
    result, error = validate_response(raw)
    assert error is None
    assert len(result) == 2
    assert result[0]["name"] == "Good"
    assert result[1]["name"] == "Also Good"


def test_non_dict_objects_skipped():
    raw = '[{"name": "Good", "date": "2026-03-01", "time": "18:00"}, "not an object", 42]'
    result, error = validate_response(raw)
    assert error is None
    assert len(result) == 1
