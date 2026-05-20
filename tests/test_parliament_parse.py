from __future__ import annotations

from pathlib import Path

from lib.sources.my.parliament_my import parse

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "html"
INDEX_URL = "https://www.parlimen.gov.my/bills-dewan-rakyat.html"


def test_parse_minimal_fixture_link_count() -> None:
    """Fixture is tiny nav-only HTML: EN + Hansard links — no ``.pdf`` / billindex strings."""
    html = (FIXTURES / "parliament_index_minimal.html").read_text(encoding="utf-8")
    out = parse.parse_fetched_index(html, source_url=INDEX_URL)
    assert out["source_id"] == "parliament_my"
    assert out["index_url"] == INDEX_URL
    assert out["link_count"] == 2
    urls = {L["url"] for L in out["links"]}
    assert "https://www.parlimen.gov.my/bills-dewan-rakyat.html?&lang=en" in urls
    assert "https://www.parlimen.gov.my/hansard-dewan-rakyat.html?uweb=dr" in urls
    assert out.get("pdf_urls_on_page") == []
    assert out.get("bill_table_rows") == []


def test_extract_listing_pagination_same_path() -> None:
    base = "https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr"
    html = """
    <a href="bills-dewan-rakyat.html?uweb=dr&amp;page=2">2</a>
    <a href="/bills-dewan-rakyat.html?uweb=dr&amp;page=3">3</a>
    <a href="https://www.parlimen.gov.my/hansard-dewan-rakyat.html">other path</a>
    """
    found = parse.extract_listing_pagination_urls(html, base)
    assert len(found) == 2
    assert all("page=" in u for u in found)


def test_extract_dr_bill_ids() -> None:
    html = "Bill D.R. 12/2026 and dr3/2025 mentioned."
    ids = parse.extract_dr_bill_ids(html)
    assert len(ids) >= 1
