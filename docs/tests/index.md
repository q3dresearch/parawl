---
title: Tests
description: Test coverage for parawl crawlers, parsers, and pipeline stages.
tags: [testing, pytest, parliament]
---

# Tests

All tests live under `tests/` and run with `pytest`.

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests are grouped by the module they cover. Each test uses fixtures or synthetic inputs — no live network calls.

---

## `test_parliament_parse.py` — HTML index parser

Tests for `lib.sources.my.parliament_my.parse` — the parser that reads the live bill index HTML page.

| Test | What it checks |
|------|---------------|
| `test_parse_minimal_fixture_link_count` | A nav-only HTML fixture (no bills) returns zero PDF URLs and zero bill table rows, but correctly identifies the two navigation links |
| `test_extract_listing_pagination_same_path` | Pagination links (`?page=2`, `?page=3`) on the same path are kept; links to other pages (e.g. Hansard) are excluded |

**Fixture:** `tests/fixtures/html/parliament_index_minimal.html`

---

## `test_parliament_pdf_parse.py` — dhtmlx XML and PDF URL resolution

Tests for the archive (1990–2024) crawl path: XML tree parsing, PDF URL construction, and language preference logic.

| Test | What it checks |
|------|---------------|
| `test_parse_dr_label_bill_year` | `D.R.21/2024` → year `2024`, id `21` |
| `test_legacy_e_suffix_billindex_path` | Legacy `/e` suffix paths are correctly recognised |
| `test_synthetic_billindex_paths_match_known_patterns` | A batch of known real URL patterns all resolve correctly |
| `test_alternates_parliament_bill_pdf_url_orders_e_and_bi` | English (`/e`) URL is preferred over Bahasa Malaysia (`/bi`) when both exist |
| `test_drop_bm_billindex_urls` | Bahasa Malaysia URLs are dropped when an English equivalent is available |
| `test_billindex_url_for_dhtmlx_path_never_bm` | dhtmlx path resolution never produces a BM URL as output |
| `test_billindex_pdf_url_is_bm` | BM URL classifier returns correct true/false for known patterns |
| `test_resolve_arkib_never_keeps_bm_even_if_probe_succeeds` | Even if a BM PDF URL responds HTTP 200, the resolver still discards it in favour of English |
| `test_absolute_billindex_pdf_url_encodes_spaces` | Spaces in PDF filenames are percent-encoded before the URL is returned |
| `test_parse_dhtmlx_bill_records_from_xml_2024` | Parses the 2024 dhtmlx XML fixture and produces the expected bill rows |
| `test_parse_dhtmlx_bill_records_rewrites_bm_embed_to_bi` | Embedded BM PDF URLs in the XML tree are rewritten to English (`/bi`) variants |
| `test_write_arkib_bills_csv_by_year_splits_files` | Bills are split into per-year CSV files with the correct filenames |
| `test_extract_pdf_urls_from_dhtmlx_tree_xml` | PDF URLs are extracted from a dhtmlx tree XML fixture |
| `test_normalize_listing_url_dedupes_lang_and_order` | Query parameter order and `lang=` variations are normalised before deduplication |
| `test_extract_pdf_urls_with_xpath_nested` | Nested XML structures with PDF links are correctly traversed |
| `test_extract_pdf_from_onclick` | `onclick="..."` JavaScript handlers are parsed to extract embedded PDF URLs |
| `test_is_pdf_href` | Correctly classifies `.pdf` hrefs vs non-PDF hrefs |
| `test_pdf_filename_from_url` | Extracts the filename from a PDF URL, including percent-encoded names |

**Fixtures:** `tests/fixtures/xml/dhtmlx_bills_2024_sample.xml`, `tests/fixtures/xml/dhtmlx_tree_sample.xml`

---

## `test_dhtmlx_dedupe.py` — bill record deduplication

Tests for `dhtmlx_arkib.dedupe_bill_records` — the logic that merges duplicate bill entries produced by the XML tree walk.

The dhtmlx archive tree can yield the same bill from multiple nodes (root node, year node, session node). The deduplicator merges them, preferring the most specific node and the English PDF URL.

| Test | What it checks |
|------|---------------|
| `test_arkib_page_url_forces_lang_en` | The archive URL always has `lang=en` appended, regardless of input |
| `test_dedupe_prefers_year_node_over_root` | When the same bill appears under a year node and the root node, the year-node record wins |
| `test_merge_rank_prefers_bi_over_bm_at_same_tier` | At equal specificity, a bilingual (`/bi`) PDF is preferred over a Bahasa Malaysia one |
| `test_dedupe_prefers_bi_when_merging` | After merging two records, the bilingual PDF URL is carried forward |
| `test_dedupe_same_pdf_keeps_one` | Two records with identical PDF URLs collapse to a single record |

---

## `test_dhtmlx_hansard.py` — Hansard XML parser and date parsing

Tests for the Hansard crawl path: dhtmlx tree parsing, Malay date parsing, and CSV output.

| Test | What it checks |
|------|---------------|
| `test_parse_bm_date_text_standard` | `"19 Julai 1982"` → `"1982-07-19"` |
| `test_parse_bm_date_text_case_insensitive` | Month names are matched case-insensitively |
| `test_parse_date_from_hindex_filename_dr` | `"DR-19072024.pdf"` → `"2024-07-19"` |
| `test_parse_date_from_hindex_filename_dn` | `"DN-01012023.pdf"` → `"2023-01-01"` |
| `test_parse_hansard_records_from_xml_basic` | Leaf nodes from a synthetic Hansard XML yield correct `sitting_date`, `house`, `pdf_url` |
| `test_parse_dhtmlx_xml_handles_duplicate_trees` | Repeated `<tree>` elements (malformed Hansard response) are parsed without error |
| `test_parliaments_for_year_2024` | `parliaments_for_year(2024)` returns `[15]` |
| `test_parliaments_for_year_1982` | `parliaments_for_year(1982)` returns the correct parliament(s) covering 1982 |
| `test_write_hansard_csv_by_year_splits_files` | Records are split into per-house per-year CSV files with the correct filenames |

---

## `test_discovery.py` — source adapter discovery

Tests for `lib.sources.discovery` — the module that reads `seed_urls.txt` files across all adapters.

| Test | What it checks |
|------|---------------|
| `test_sources_root_exists` | `src/lib/sources/my/parliament_my/seed_urls.txt` is present on disk |
| `test_iter_adapter_dirs_includes_parliament` | `parliament_my` appears in the list of discovered adapters |
| `test_parliament_seed_urls_order` | The 8 seed URLs are in the expected order: bills (EN/BM/archive) then hansard (DR/DN live+archive) |
| `test_iter_source_library_seeds_parliament` | `parliament_my` contributes exactly 8 seed rows to the source library |

---

## Running a single test file

```bash
pytest tests/test_dhtmlx_dedupe.py -v
pytest tests/test_dhtmlx_hansard.py -v
pytest tests/test_parliament_pdf_parse.py -v -k "bm"   # filter by name
```
