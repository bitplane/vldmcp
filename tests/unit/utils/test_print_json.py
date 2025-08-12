"""Tests for print_json utility."""

from vldmcp.util.print_json import pretty_print


def test_simple_dict():
    obj = {"a": "b, c"}
    result = pretty_print(obj)
    assert result == ["a: b, c"]


def test_nested_dict():
    obj = {"x": {"y": ["z", 1]}}
    result = pretty_print(obj)
    assert result == ["x.y: z, 1"]


def test_hex_value():
    obj = {"x.y": 0x123}
    result = pretty_print(obj)
    assert result == ["x.y: 291"]


def test_complex_example():
    obj = [{"x": {"y": ["z", 1]}}, {"a": "b, c"}, {"x.y": 0x123}]
    result = pretty_print(obj)
    assert result == ["x.y: z, 1", "a: b, c", "x.y: 291"]


def test_deeply_nested():
    obj = {"a": {"b": {"c": {"d": "e"}}}}
    result = pretty_print(obj)
    assert result == ["a.b.c.d: e"]


def test_multiple_keys():
    obj = {"a": 1, "b": 2, "c": 3}
    result = pretty_print(obj)
    assert set(result) == {"a: 1", "b: 2", "c: 3"}


def test_empty_dict():
    obj = {}
    result = pretty_print(obj)
    assert result == []


def test_empty_list():
    obj = []
    result = pretty_print(obj)
    assert result == []


def test_list_values():
    obj = {"items": [1, 2, 3, 4]}
    result = pretty_print(obj)
    assert result == ["items: 1, 2, 3, 4"]


def test_mixed_nesting():
    obj = [{"a": {"b": 1}}, {"c": [2, 3]}, {"d": {"e": {"f": [4, 5, 6]}}}]
    result = pretty_print(obj)
    assert result == ["a.b: 1", "c: 2, 3", "d.e.f: 4, 5, 6"]
