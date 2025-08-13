from vldmcp.util import output


def test_output_nested_dict(capsys):
    """Test the output_nested_dict function."""
    d = {"a": 1, "b": {"c": 2, "d": {"e": 3}}, "f": 0, "g": "0B", "h": None}
    output.output_nested_dict(d)
    captured = capsys.readouterr()
    assert captured.out == "a	1\nb.c	2\nb.d.e	3\n"
