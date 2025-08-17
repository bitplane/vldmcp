import click
from vldmcp.util.pprint import pprint_dict


def test_output_nested_dict(capsys):
    """Test the pprint_dict function with tab-separated output."""
    d = {"a": 1, "b": {"c": 2, "d": {"e": 3}}, "f": 0, "g": "0B", "h": None}
    pprint_dict(d, output_func=click.echo, tab_separated=True, filter_empty=True)
    captured = capsys.readouterr()
    assert captured.out == "a	1\nb.c	2\nb.d.e	3\n"
