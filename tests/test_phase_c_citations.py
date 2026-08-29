"""PHASE C item #6 — clickable source citations with REAL links (regression lock).

The widget renders each retrieved source as a clickable <a href=src.url> (app/static/widget.html,
addMsg -> builds an anchor with target=_blank rel=noopener). The link is only as good as the
data the server ships. This suite proves the SERVER contract: the SSE `sources` event and the
non-stream `results` both carry a real `url` (metadata.source_url) for URL-ingested content, so
the widget's citations are genuine links — not a plain "N sources" label. It also locks the
client rendering code so a regression can't silently drop the anchors.

Note: JS widget can't run in-browser here; we lock the server payload (drives the links) and
assert the shipped widget.html still emits the anchor markup.
"""
import pytest

V = "/api/v1"
ADMIN = {"Admin-Key": "test-admin-key-for-tests"}


def _auth(key):
    return {"Authorization": f"Bearer {key}"}


def _make_tenant(client, name="cite"):
    r = client.post(f"{V}/tenants", json={"name": name, "plan": "standard"}, headers=ADMIN)
    assert r.status_code == 201, r.text
    return r.json()


def _parse_sse(text):
    """Return list of (event, data_dict) from an SSE byte/text stream."""
    events = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        ev = None
        data = None
        for line in block.split("\n"):
            if line.startswith("event:"):
                ev = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data = line[len("data:"):].strip()
        if ev is not None and data is not None:
            import json
            events.append((ev, json.loads(data)))
    return events


def test_stream_sources_carry_real_url_for_url_ingested_doc(client, monkeypatch):
    """A URL-ingested doc yields clickable citations: the `sources` event includes a real url."""
    t = _make_tenant(client)
    tid, key = t["tenant_id"], t["api_key"]
    url = "https://example.com/pricing"
    html = "<html><body><h1>Pricing starts at $9/mo for the starter plan.</h1></body></html>"

    import app.ingestion as ing
    monkeypatch.setattr(ing, "fetch_url", lambda u, timeout=20.0: html)

    r = client.post(f"{V}/{tid}/ingest/url", headers=_auth(key), json={"url": url})
    assert r.status_code == 201, r.text

    resp = client.post(
        f"{V}/{tid}/query/stream", headers=_auth(key),
        json={"question": "how much does it cost?", "generate": False, "session_id": "cite-1"},
    )
    assert resp.status_code == 200, resp.text
    events = _parse_sse(resp.text)
    src_events = [d for (ev, d) in events if ev == "sources"]
    assert src_events, "expected a `sources` SSE event"
    sources = src_events[0]
    assert any(s.get("url") == url for s in sources), f"citation must carry real url {url}; got {sources}"
    # Title should also be present so the link has meaningful label text.
    assert any(s.get("title") for s in sources), sources


def test_nonstream_results_metadata_carries_source_url(client, monkeypatch):
    """Non-stream /query results also expose source_url so any client can build links."""
    t = _make_tenant(client)
    tid, key = t["tenant_id"], t["api_key"]
    url = "https://example.com/about"
    html = "<html><body><h1>About us: we ship on-prem RAG for regulated teams.</h1></body></html>"

    import app.ingestion as ing
    monkeypatch.setattr(ing, "fetch_url", lambda u, timeout=20.0: html)

    r = client.post(f"{V}/{tid}/ingest/url", headers=_auth(key), json={"url": url})
    assert r.status_code == 201, r.text

    resp = client.post(
        f"{V}/{tid}/query", headers=_auth(key),
        json={"question": "what do you ship?", "generate": False, "session_id": "cite-2"},
    )
    assert resp.status_code == 200, resp.text
    results = resp.json()["results"]
    assert results, "expected retrieved chunks"
    assert any((r.get("metadata") or {}).get("source_url") == url for r in results), \
        f"result metadata must carry source_url {url}; got {[ (x.get('metadata') or {}).get('source_url') for x in results ]}"


def test_text_ingested_doc_has_no_url_honest_no_link(client):
    """A text upload has no source URL -> citation url is None (widget shows title, no link).
    This proves we don't fabricate links; only real URLs become clickable."""
    t = _make_tenant(client)
    tid, key = t["tenant_id"], t["api_key"]
    r = client.post(
        f"{V}/{tid}/documents", headers=_auth(key),
        json={"title": "Internal note", "content": "Internal note without a public URL.",
              "doc_id": "note1"},
    )
    assert r.status_code == 201, r.text
    resp = client.post(
        f"{V}/{tid}/query/stream", headers=_auth(key),
        json={"question": "internal note?", "generate": False, "session_id": "cite-3"},
    )
    assert resp.status_code == 200, resp.text
    events = _parse_sse(resp.text)
    sources = [d for (ev, d) in events if ev == "sources"]
    if sources:
        # When a source lacks a url, the widget must NOT invent one (None stays None).
        for s in sources[0]:
            assert s.get("url") in (None, ""), f"must not fabricate url; got {s}"


def test_widget_html_renders_clickable_anchors():
    """Lock the client: shipped widget.html builds <a href=src.url target=_blank rel=noopener>
    for each source (the clickable-citation markup), so a refactor can't regress it silently."""
    from pathlib import Path
    html = (Path(__file__).parent.parent / "app" / "static" / "widget.html").read_text(encoding="utf-8")
    assert 'a.href = src.url' in html, "widget must set anchor href from source url"
    assert 'target = "_blank"' in html, "citation links must open in a new tab"
    assert 'rel = "noopener noreferrer"' in html, "citation links must be opener-safe"
