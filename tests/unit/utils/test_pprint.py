"""Tests for pprint utility."""

from vldmcp.util.pprint import _format_dict


def test_simple_dict():
    obj = {"a": "b, c"}
    result = _format_dict(obj)
    assert result == ["a: b, c"]


def test_nested_dict():
    obj = {"x": {"y": ["z", 1]}}
    result = _format_dict(obj)
    assert result == ["x.y: z, 1"]


def test_hex_value():
    obj = {"x.y": 0x123}
    result = _format_dict(obj)
    assert result == ["x.y: 291"]


def test_complex_example():
    obj = [{"x": {"y": ["z", 1]}}, {"a": "b, c"}, {"x.y": 0x123}]
    result = _format_dict(obj)
    assert result == ["x.y: z, 1", "a: b, c", "x.y: 291"]


def test_deeply_nested():
    obj = {"a": {"b": {"c": {"d": "e"}}}}
    result = _format_dict(obj)
    assert result == ["a.b.c.d: e"]


def test_multiple_keys():
    obj = {"a": 1, "b": 2, "c": 3}
    result = _format_dict(obj)
    assert set(result) == {"a: 1", "b: 2", "c: 3"}


def test_empty_dict():
    obj = {}
    result = _format_dict(obj)
    assert result == []


def test_empty_list():
    obj = []
    result = _format_dict(obj)
    assert result == []


def test_list_values():
    obj = {"items": [1, 2, 3, 4]}
    result = _format_dict(obj)
    assert result == ["items: 1, 2, 3, 4"]


def test_mixed_nesting():
    obj = [{"a": {"b": 1}}, {"c": [2, 3]}, {"d": {"e": {"f": [4, 5, 6]}}}]
    result = _format_dict(obj)
    assert result == ["a.b: 1", "c: 2, 3", "d.e.f: 4, 5, 6"]
