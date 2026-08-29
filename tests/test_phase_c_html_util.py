"""Unit test for the dependency-free HTML->text extraction used by URL ingestion.

Ensures chunk text (and thus citation snippets) is readable, not raw tag soup.
"""
from app.ingestion.html_util import html_to_text


def test_strips_tags_and_decodes_entities():
    html = "<html><body><h1>Hello &amp; welcome</h1><p>Price: $9</p></body></html>"
    out = html_to_text(html)
    assert "<" not in out, out
    assert "Hello & welcome" in out, out
    assert "Price: $9" in out, out


def test_removes_script_and_style():
    html = "<div>keep</div><script>var x=1;</script><style>.a{color:red}</style><p>body</p>"
    out = html_to_text(html)
    assert "var x=1" not in out, out
    assert "color:red" not in out, out
    assert "keep" in out and "body" in out, out


def test_block_elements_become_breaks():
    html = "<p>one</p><p>two</p>"
    out = html_to_text(html)
    assert "one" in out and "two" in out
    # paragraph separation preserved (at least one newline between)
    assert "one\n" in out or "one\n\ntwo" in out, out
