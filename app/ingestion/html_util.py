"""Minimal, dependency-free HTML -> readable text extraction for URL ingestion.

We deliberately avoid a heavy external dep (trafilatura/pdfminer) here so the hermetic test
suite stays network/dep-free; the goal is to strip markup and decode entities so that:
  * retrieved chunk text (and therefore citation snippets) are human-readable, not raw HTML, and
  * retrieval quality isn't polluted by tag soup.
For production-quality extraction a tenant can pre-clean; this is the safe default.
"""
from __future__ import annotations

import html as _html
import re

# Block elements we treat as paragraph breaks.
_BLOCK_RE = re.compile(r"(?i)</(p|div|br|li|h[1-6]|tr|section|article|blockquote)>")
_TAG_RE = re.compile(r"(?i)<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_MULTI_NL_RE = re.compile(r"\n{3,}")


def html_to_text(html: str) -> str:
    if not html:
        return ""
    # Drop script/style content entirely.
    cleaned = re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1>", " ", html)
    # Convert common block-closers into newlines so structure survives.
    cleaned = _BLOCK_RE.sub("\n", cleaned)
    # Strip remaining tags.
    cleaned = _TAG_RE.sub(" ", cleaned)
    # Decode HTML entities (&amp; -> &, &#39; -> ').
    cleaned = _html.unescape(cleaned)
    # Normalize whitespace: collapse runs of spaces/tabs, keep paragraph newlines.
    cleaned = _WS_RE.sub(" ", cleaned)
    cleaned = re.sub(r" ?\n ?", "\n", cleaned)
    cleaned = _MULTI_NL_RE.sub("\n\n", cleaned)
    return cleaned.strip()
