from __future__ import annotations

from lib.parser.seed_txt import parse_seed_urls_file
from lib.sources.discovery import iter_adapter_dirs, iter_source_library_seeds, sources_root


def test_sources_root_exists() -> None:
    assert (sources_root() / "my" / "parliament_my" / "seed_urls.txt").is_file()


def test_iter_adapter_dirs_includes_parliament() -> None:
    names = {d.name for d in iter_adapter_dirs()}
    assert "parliament_my" in names


def test_parliament_seed_urls_order() -> None:
    p = sources_root() / "my" / "parliament_my" / "seed_urls.txt"
    pairs = parse_seed_urls_file(p)
    assert len(pairs) == 4
    urls = [u for u, _ in pairs]
    assert urls[0].endswith("bills-dewan-rakyat.html")
    assert "uweb=dr" in urls[1] and "arkib" not in urls[1]
    assert "arkib=yes" in urls[2]
    assert "bills-dewan-negara.html" in urls[3]


def test_iter_source_library_seeds_parliament() -> None:
    rows = list(iter_source_library_seeds())
    parliament = [r for r in rows if r["adapter_id"] == "parliament_my"]
    assert len(parliament) == 4
    assert all("seed_urls.txt" in (r.get("notes") or "") for r in parliament)


def test_parse_seed_urls_ignores_comments_and_blank(tmp_path: Path) -> None:
    p = tmp_path / "seed_urls_sample.txt"
    p.write_text(
        "# c\n\nhttps://example.com/a\nhttps://example.com/b\tLabel B\n",
        encoding="utf-8",
    )
    pairs = parse_seed_urls_file(p)
    assert pairs == [("https://example.com/a", None), ("https://example.com/b", "Label B")]
