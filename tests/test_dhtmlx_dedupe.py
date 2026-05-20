from __future__ import annotations

from lib.sources.my.parliament_my.dhtmlx_arkib import (
    arkib_page_url_with_lang_en,
    dedupe_bill_records,
)
from lib.sources.my.parliament_my import parse


def _row(**kwargs: str) -> dict[str, str]:
    base = {
        "year": "",
        "bill_item_id": "",
        "summary": "",
        "dr_label": "",
        "pdf_filename": "",
        "pdf_url": "",
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
    base.update(kwargs)
    return base


def test_arkib_page_url_forces_lang_en() -> None:
    base = "https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&arkib=yes"
    assert "lang=en" in arkib_page_url_with_lang_en(base)
    bm = "https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&lang=bm&arkib=yes"
    out = arkib_page_url_with_lang_en(bm)
    assert "lang=en" in out
    assert "lang=bm" not in out


def test_dedupe_prefers_year_node_over_root() -> None:
    rows = [
        _row(
            year="1990",
            dr_label="D.R.02/1990",
            pdf_filename="DR021990.pdf",
            pdf_url="https://www.parlimen.gov.my/files/billindex/pdf/1990/DR021990.pdf",
            source_tree_node_id="0",
        ),
        _row(
            year="1990",
            dr_label="D.R.02/1990",
            pdf_filename="DR021990E.pdf",
            pdf_url="https://www.parlimen.gov.my/files/billindex/pdf/1990/DR021990E.pdf",
            source_tree_node_id="0_1990",
        ),
    ]
    out = dedupe_bill_records(rows)
    assert len(out) == 1
    assert out[0]["source_tree_node_id"] == "0_1990"
    assert "E.pdf" in out[0]["pdf_url"]


def test_merge_rank_prefers_bi_over_bm_at_same_tier() -> None:
    bm = _row(
        year="2024",
        dr_label="D.R.17/2024",
        pdf_url="https://www.parlimen.gov.my/files/billindex/pdf/2024/DR%2017%20BM.pdf",
        source_tree_node_id="0_2024",
    )
    bi = _row(
        year="2024",
        dr_label="D.R.17/2024",
        pdf_url="https://www.parlimen.gov.my/files/billindex/pdf/2024/DR%2017%20BI.pdf",
        source_tree_node_id="0_2024",
    )
    assert parse.bill_record_merge_rank(bi) < parse.bill_record_merge_rank(bm)


def test_dedupe_prefers_bi_when_merging() -> None:
    rows = [
        _row(
            year="2024",
            dr_label="D.R.17/2024",
            pdf_url="https://www.parlimen.gov.my/files/billindex/pdf/2024/DR%2017%20BM.pdf",
            source_tree_node_id="0_2024",
        ),
        _row(
            year="2024",
            dr_label="D.R.17/2024",
            pdf_url="https://www.parlimen.gov.my/files/billindex/pdf/2024/DR%2017%20BI.pdf",
            source_tree_node_id="0_2024",
        ),
    ]
    out = dedupe_bill_records(rows)
    assert len(out) == 1
    assert "BI.pdf" in out[0]["pdf_url"]


def test_dedupe_same_pdf_keeps_one() -> None:
    a = _row(
        year="1990",
        dr_label="D.R.01/1990",
        pdf_url="https://x/files/billindex/pdf/1990/DR011990E.pdf",
        source_tree_node_id="0",
    )
    b = a.copy()
    b["source_tree_node_id"] = "0_1990"
    out = dedupe_bill_records([a, b])
    assert len(out) == 1
    assert out[0]["source_tree_node_id"] == "0_1990"
