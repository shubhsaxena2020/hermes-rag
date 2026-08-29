"""PHASE C item #5 — multi-turn session persistence (regression lock).

The embeddable widget sends a stable session_id with every turn (app/static/widget.html),
and the backend rewrites follow-ups against prior context + stores turns
(app/main.py query + query/stream -> rewrite_query / get_session_store). This suite proves
the SERVER contract the widget relies on: two queries sharing a session_id are treated as
one conversation (the 2nd is rewritten to include the 1st's context), whereas two queries
with different/no session_id are independent. Without this, every widget message would be a
fresh conversation.

Note: the JS widget itself can't be unit-tested without a browser; this locks the backend
behavior the widget depends on.
"""
import pytest

V = "/api/v1"
ADMIN = {"Admin-Key": "test-admin-key-for-tests"}


def _auth(key):
    return {"Authorization": f"Bearer {key}"}


def _make_tenant(client, name="mt"):
    r = client.post(f"{V}/tenants", json={"name": name, "plan": "standard"}, headers=ADMIN)
    assert r.status_code == 201, r.text
    return r.json()


def test_multiturn_session_rewrites_followup(client):
    """A follow-up referencing the prior turn is rewritten to include its context."""
    t = _make_tenant(client)
    auth = _auth(t["api_key"])
    sid = "sess-multiturn-1"
    # Seed a doc so retrieval has something to anchor context to.
    client.post(
        f"{V}/{t['tenant_id']}/documents", headers=auth,
        json={"title": "Atlas", "content": "Project Atlas deadline is March 14 and Priya owns it.",
              "doc_id": "atlas"},
    )

    # Turn 1: establishes context.
    q1 = client.post(
        f"{V}/{t['tenant_id']}/query", headers=auth,
        json={"question": "What is Project Atlas?", "generate": False, "session_id": sid},
    )
    assert q1.status_code == 200, q1.text

    # Turn 2: weak-reference follow-up ("it" / "who owns it") must be rewritten with context.
    q2 = client.post(
        f"{V}/{t['tenant_id']}/query", headers=auth,
        json={"question": "who owns it?", "generate": False, "session_id": sid},
    )
    assert q2.status_code == 200, q2.text
    body = q2.json()
    # Multi-turn: the backend rewrote the follow-up to carry the prior topic.
    assert body.get("rewritten_query"), "expected a rewritten_query for the follow-up"
    assert body["rewritten_query"] != "who owns it?", body
    # The prior anchor ("Atlas"/"Project Atlas") should now be present in the clarified query.
    assert "atlas" in body["rewritten_query"].lower(), body["rewritten_query"]


def test_different_session_ids_are_independent(client):
    """Two different session_ids are NOT merged into one conversation."""
    t = _make_tenant(client)
    auth = _auth(t["api_key"])
    client.post(
        f"{V}/{t['tenant_id']}/documents", headers=auth,
        json={"title": "Atlas", "content": "Project Atlas deadline is March 14 and Priya owns it.",
              "doc_id": "atlas"},
    )

    q1 = client.post(
        f"{V}/{t['tenant_id']}/query", headers=auth,
        json={"question": "What is Project Atlas?", "generate": False, "session_id": "sess-A"},
    )
    assert q1.status_code == 200, q1.text
    q2 = client.post(
        f"{V}/{t['tenant_id']}/query", headers=auth,
        json={"question": "who owns it?", "generate": False, "session_id": "sess-B"},
    )
    assert q2.status_code == 200, q2.text
    # Different session -> no conversational rewrite applied (no prior context to lean on).
    assert q2.json().get("rewritten_query") in (None, "who owns it?"), q2.json()


def test_stream_endpoint_also_accepts_session_id(client):
    """The SSE /query/stream path the widget actually uses stores turns under session_id
    (proven by a 200 stream that carries a rewritten event for a follow-up)."""
    t = _make_tenant(client)
    auth = _auth(t["api_key"])
    sid = "sess-stream-1"
    client.post(
        f"{V}/{t['tenant_id']}/documents", headers=auth,
        json={"title": "Atlas", "content": "Project Atlas deadline is March 14 and Priya owns it.",
              "doc_id": "atlas"},
    )
    q1 = client.post(
        f"{V}/{t['tenant_id']}/query/stream", headers=auth,
        json={"question": "What is Project Atlas?", "generate": False, "session_id": sid},
    )
    assert q1.status_code == 200, q1.text
    q2 = client.post(
        f"{V}/{t['tenant_id']}/query/stream", headers=auth,
        json={"question": "who owns it?", "generate": False, "session_id": sid},
    )
    assert q2.status_code == 200, q2.text
    # The stream must emit a `rewritten` event for the follow-up (multi-turn active).
    assert "event: rewritten" in q2.text, q2.text[:400]
