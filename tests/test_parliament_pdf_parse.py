from __future__ import annotations

import csv
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from lib.sources.my.parliament_my.dhtmlx_arkib import write_arkib_bills_csv_by_year
from lib.sources.my.parliament_my.parse import (
    absolute_billindex_pdf_url,
    alternates_parliament_bill_pdf_url,
    billindex_url_for_dhtmlx_path,
    billindex_pdf_url_is_bm,
    extract_billindex_pdf_urls_from_html,
    legacy_e_suffix_billindex_path,
    extract_pdf_links,
    extract_pdf_urls_from_dhtmlx_tree_xml,
    extract_pdf_urls_from_html,
    extract_pdf_urls_from_onclick,
    extract_pdf_urls_with_xpath,
    parse_dhtmlx_bill_records_from_xml,
    parse_dr_label_bill_year,
    is_dr_bills_follow_candidate,
    is_html_follow_candidate,
    is_pdf_href,
    normalize_listing_url_for_dedupe,
    pdf_filename_from_url,
)


def test_legacy_e_suffix_billindex_path() -> None:
    assert legacy_e_suffix_billindex_path("/files/billindex/pdf/1990/DR021990.pdf") == (
        "/files/billindex/pdf/1990/DR021990E.pdf"
    )
    assert legacy_e_suffix_billindex_path("/files/billindex/pdf/1990/DR021990E.pdf") is None


def test_parse_dr_label_bill_year() -> None:
    assert parse_dr_label_bill_year("D.R.17/2024") == (17, 2024)
    assert parse_dr_label_bill_year("D.R.01/1990") == (1, 1990)
    assert parse_dr_label_bill_year("") is None


def test_synthetic_billindex_paths_match_known_patterns() -> None:
    from urllib.parse import unquote, urlparse

    from lib.sources.my.parliament_my.dhtmlx_arkib import (
        BILLINDEX_WORKING_LEGACY_E_PDF,
        BILLINDEX_WORKING_SPACED_BI_PDF,
        synthetic_billindex_pdf_rel_paths,
    )

    p1990 = synthetic_billindex_pdf_rel_paths(1, 1990)
    assert p1990[0] == unquote(urlparse(BILLINDEX_WORKING_LEGACY_E_PDF).path)
    p2024 = synthetic_billindex_pdf_rel_paths(17, 2024)
    assert unquote(urlparse(BILLINDEX_WORKING_SPACED_BI_PDF).path) in p2024


def test_alternates_parliament_bill_pdf_url_orders_e_and_bi() -> None:
    bm = "https://www.parlimen.gov.my/files/billindex/pdf/2024/DR%2017%20BM.pdf"
    alts = alternates_parliament_bill_pdf_url(bm)
    assert alts[0].endswith("DR%2017%20BI.pdf")
    assert not any(billindex_pdf_url_is_bm(u) for u in alts)
    compact = "https://www.parlimen.gov.my/files/billindex/pdf/1990/DR021990.pdf"
    alts2 = alternates_parliament_bill_pdf_url(compact)
    assert "DR021990E.pdf" in alts2[0]
    assert not any(billindex_pdf_url_is_bm(u) for u in alts2)


def test_alternates_parliament_bill_pdf_url_empty_returns_empty() -> None:
    assert alternates_parliament_bill_pdf_url("") == []


def test_drop_bm_billindex_urls() -> None:
    from lib.sources.my.parliament_my.dhtmlx_arkib import drop_bm_billindex_urls

    rows: list[dict[str, str]] = [
        {
            "pdf_url": "https://www.parlimen.gov.my/files/billindex/pdf/2024/DR%2017%20BM.pdf",
            "pdf_filename": "DR 17 BM.pdf",
        },
        {
            "pdf_url": "https://www.parlimen.gov.my/files/billindex/pdf/2024/DR%2017%20BI.pdf",
            "pdf_filename": "DR 17 BI.pdf",
        },
    ]
    drop_bm_billindex_urls(rows)
    assert rows[0]["pdf_url"] == ""
    assert rows[0]["pdf_filename"] == ""
    assert "BI.pdf" in rows[1]["pdf_url"]


def test_billindex_url_for_dhtmlx_path_never_bm() -> None:
    bi = billindex_url_for_dhtmlx_path("/files/billindex/pdf/2024/DR 17 BI.pdf")
    assert bi and "BI" in bi
    assert not billindex_pdf_url_is_bm(bi)
    from_bm = billindex_url_for_dhtmlx_path("/files/billindex/pdf/2024/DR 17 BM.pdf")
    assert from_bm and "BI.pdf" in from_bm
    assert not billindex_pdf_url_is_bm(from_bm)


def test_billindex_pdf_url_is_bm() -> None:
    assert billindex_pdf_url_is_bm("https://x/files/billindex/pdf/2024/DR%2017%20BM.pdf")
    assert not billindex_pdf_url_is_bm("https://x/files/billindex/pdf/2024/DR%2017%20BI.pdf")
    # NBSP between number and BM (site sometimes uses unicode space; broke alternates + drop_bm)
    assert billindex_pdf_url_is_bm(
        "https://x/files/billindex/pdf/2024/DR%2017\u00a0BM.pdf",
    )


def test_alternates_nbsp_bm_yields_bi_only() -> None:
    u = "https://www.parlimen.gov.my/files/billindex/pdf/2024/DR%2017\u00a0BM.pdf"
    alts = alternates_parliament_bill_pdf_url(u)
    assert alts
    assert any("BI" in x.upper() for x in alts)
    assert not any(billindex_pdf_url_is_bm(x) for x in alts)


def test_resolve_arkib_never_keeps_bm_even_if_probe_succeeds(monkeypatch) -> None:
    from lib.sources.my.parliament_my.dhtmlx_arkib import resolve_arkib_bill_pdf_urls

    def probe(url: str, **kwargs: object) -> bool:
        return "BM" in url.upper()

    monkeypatch.setattr(
        "lib.sources.my.parliament_my.dhtmlx_arkib.fetch.probe_pdf_magic",
        probe,
    )
    row = {
        "year": "2024",
        "bill_item_id": "0_0",
        "summary": "",
        "dr_label": "D.R.17/2024",
        "pdf_filename": "DR 17 BM.pdf",
        "pdf_url": "https://www.parlimen.gov.my/files/billindex/pdf/2024/DR%2017%20BM.pdf",
        "pdf_url_embedded": "",
        "pdf_resolve_status": "",
        "first_reading": "",
        "second_reading": "",
        "presented_by": "",
        "passed_at": "",
        "source_tree_node_id": "0_0",
        "ajax_url": "",
        "seed_url": "https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&arkib=yes",
    }
    resolve_arkib_bill_pdf_urls([row], verify_tls=True)
    assert row["pdf_resolve_status"] == "failed"
    assert row["pdf_url"] == ""


def test_absolute_billindex_pdf_url_encodes_spaces() -> None:
    u = absolute_billindex_pdf_url("/files/billindex/pdf/2024/DR 17 BI.pdf")
    assert "DR%2017%20BI.pdf" in u
    assert " " not in urlparse(u).path


def test_parse_dhtmlx_bill_records_from_xml_2024() -> None:
    xml = (Path(__file__).resolve().parent / "fixtures" / "xml" / "dhtmlx_bills_2024_sample.xml").read_text(
        encoding="utf-8",
    )
    rows = parse_dhtmlx_bill_records_from_xml(
        xml,
        source_tree_node_id="0_2024",
        ajax_url="https://example.invalid/ajax",
        seed_url="https://example.invalid/seed",
    )
    assert len(rows) == 2
    assert rows[0]["year"] == "2024"
    assert "Drug Dependants" in rows[0]["summary"]
    assert rows[0]["dr_label"] == "D.R.17/2024"
    assert rows[0]["pdf_filename"] == "DR 17 BI.pdf"
    assert "/files/billindex/pdf/2024/" in rows[0]["pdf_url"]
    assert "DR%2017%20BI.pdf" in rows[0]["pdf_url"]
    assert rows[0]["first_reading"] == "02/07/2024"
    assert rows[0]["second_reading"] == "03/07/2024"
    assert "Shamsul Anuar" in rows[0]["presented_by"]
    assert "Saifuddin" in rows[0]["presented_by"]
    assert rows[0]["passed_at"] == "18/07/2024"
    assert rows[1]["dr_label"] == "D.R.18/2024"
    assert rows[1]["pdf_filename"] == "DR 18 BI.pdf"


def test_parse_dhtmlx_bill_records_rewrites_bm_embed_to_bi() -> None:
    xml = """<tree id="0_2024"><item id="x" child="1" text="Summary">
<item text="D.R.17/2024"><userdata name="myurl">javascript:loadResult('/files/billindex/pdf/2024/DR 17 BM.pdf','DR 17 BM.pdf')</userdata></item>
</item></tree>"""
    rows = parse_dhtmlx_bill_records_from_xml(
        xml,
        source_tree_node_id="0_0",
        seed_url="https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&arkib=yes",
    )
    assert len(rows) == 1
    assert rows[0]["pdf_filename"] == "DR 17 BI.pdf"
    assert rows[0]["pdf_url"]
    assert not billindex_pdf_url_is_bm(rows[0]["pdf_url"])
    assert "BI.pdf" in rows[0]["pdf_url"]


def test_write_arkib_bills_csv_by_year_splits_files() -> None:
    empty = {
        "pdf_url_embedded": "",
        "pdf_resolve_status": "",
        "first_reading": "",
        "second_reading": "",
        "presented_by": "",
        "passed_at": "",
        "source_tree_node_id": "",
        "ajax_url": "",
        "seed_url": "",
    }
    rows = [
        {"year": "2024", "bill_item_id": "a", "summary": "s1", "dr_label": "", "pdf_filename": "", "pdf_url": "", **empty},
        {"year": "1993", "bill_item_id": "b", "summary": "s2", "dr_label": "", "pdf_filename": "", "pdf_url": "", **empty},
    ]
    with tempfile.TemporaryDirectory() as td:
        paths = write_arkib_bills_csv_by_year(rows, Path(td))
        assert len(paths) == 2
        names = {p.name for p in paths}
        assert names == {"bills_1993.csv", "bills_2024.csv"}
        with (Path(td) / "bills_2024.csv").open(encoding="utf-8-sig", newline="") as f:
            r = list(csv.DictReader(f))
            assert len(r) == 1 and r[0]["summary"] == "s1"


def test_extract_pdf_urls_from_dhtmlx_tree_xml() -> None:
    xml = (Path(__file__).resolve().parent / "fixtures" / "xml" / "dhtmlx_tree_sample.xml").read_text(
        encoding="utf-8",
    )
    urls = extract_pdf_urls_from_dhtmlx_tree_xml(xml)
    assert len(urls) == 2
    assert any("DR011993E.pdf" in u for u in urls)
    assert any("DR021993E.pdf" in u for u in urls)


def test_normalize_listing_url_dedupes_lang_and_order() -> None:
    a = "https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&lang=en&arkib=yes"
    b = "https://www.parlimen.gov.my/bills-dewan-rakyat.html?arkib=yes&uweb=dr&lang=bm"
    c = "https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&arkib=yes"
    assert normalize_listing_url_for_dedupe(a) == normalize_listing_url_for_dedupe(b)
    assert normalize_listing_url_for_dedupe(a) == normalize_listing_url_for_dedupe(c)


def test_extract_pdf_urls_with_xpath_nested() -> None:
    html = """<html><body><table><tr>
 <td>1</td><td><span><a href="/files/billindex/pdf/2025/DR/z.pdf">x</a></span></td>
    </tr></table></body></html>"""
    base = "https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&arkib=yes"
    xp = "//table//tr/td[2]/span"
    urls = extract_pdf_urls_with_xpath(html, base, xp)
    assert len(urls) == 1
    assert urls[0].endswith(".pdf")


def test_extract_pdf_from_onclick() -> None:
    html = (
        '<span onclick="window.open(\'/files/billindex/pdf/2025/DR/X~1.PDF\')">x</span>'
    )
    base = "https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&arkib=yes"
    urls = extract_pdf_urls_from_onclick(html, base)
    assert len(urls) == 1
    assert "billindex/pdf/2025/DR" in urls[0]


def test_is_pdf_href() -> None:
    assert is_pdf_href("https://www.parlimen.gov.my/x/Akta%20237%20BM.pdf")
    assert not is_pdf_href("https://www.parlimen.gov.my/bills.html")


def test_pdf_filename_from_url() -> None:
    assert pdf_filename_from_url(
        "https://www.parlimen.gov.my/images/webuser/akta/Akta%20237%20BM.pdf",
    ).endswith(".pdf")


def test_extract_pdf_links() -> None:
    html = '<a href="/images/webuser/akta/Akta%20237%20BM.pdf">Act</a>'
    base = "https://www.parlimen.gov.my/bills-dewan-rakyat.html"
    urls = extract_pdf_links(html, base)
    assert len(urls) == 1
    assert "Akta" in urls[0] or "akta" in urls[0].lower()


def test_html_follow_candidate() -> None:
    assert is_html_follow_candidate("https://www.parlimen.gov.my/bills-dewan-rakyat.html?x=1")
    assert is_html_follow_candidate("https://www.parlimen.gov.my/hansard-dewan-rakyat.html?uweb=dr")
    assert not is_html_follow_candidate("https://www.parlimen.gov.my/doc.pdf")
    assert not is_html_follow_candidate("https://www.parlimen.gov.my/i.png")


def test_dr_bills_follow_skips_sidebar_noise() -> None:
    assert is_dr_bills_follow_candidate(
        "https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&arkib=yes",
    )
    assert not is_dr_bills_follow_candidate(
        "https://www.parlimen.gov.my/hansard-dewan-rakyat.html?uweb=dr",
    )
    assert not is_dr_bills_follow_candidate(
        "https://www.parlimen.gov.my/bills-dewan-negara.html?uweb=dn",
    )
    assert not is_dr_bills_follow_candidate(
        "https://www.parlimen.gov.my/ahli-dewan.html?uweb=dr",
    )


def test_extract_billindex_from_embedded_string() -> None:
    html = (
        'var u="/files/billindex/pdf/2026/DR/Supplementary%20Supply%20(2025)%20'
        'Bill%202026.pdf";'
    )
    base = "https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&arkib=yes"
    urls = extract_billindex_pdf_urls_from_html(html, base)
    assert len(urls) == 1
    assert urls[0].endswith(".pdf")
    assert "/files/billindex/pdf/2026/DR/" in urls[0]

    merged = extract_pdf_urls_from_html(
        html + '<a href="/files/billindex/pdf/other.pdf">x</a>',
        base,
    )
    assert len(merged) == 2
