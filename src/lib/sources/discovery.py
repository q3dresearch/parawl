"""
Discover adapters under ``lib/sources/<region>/<adapter>/`` that ship ``seed_urls.txt``.

Use this to seed ``source_library`` without a central ``sites.yaml``.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Iterator

from lib.parser.seed_txt import parse_seed_urls_file

_SOURCES_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _SOURCES_ROOT.parent.parent.parent  # .../stateconscious (lib/sources -> lib -> src -> repo)


def sources_root() -> Path:
    return _SOURCES_ROOT


def iter_adapter_dirs() -> Iterator[Path]:
    """Directories containing ``seed_urls.txt`` (e.g. ``.../my/parliament_my``)."""
    for region in sorted(_SOURCES_ROOT.iterdir()):
        if not region.is_dir() or region.name.startswith("_"):
            continue
        if region.name == "__pycache__":
            continue
        for adapter_dir in sorted(region.iterdir()):
            if not adapter_dir.is_dir() or adapter_dir.name.startswith("_"):
                continue
            if (adapter_dir / "seed_urls.txt").is_file():
                yield adapter_dir


def _config_module(adapter_dir: Path):
    rel = adapter_dir.relative_to(_SOURCES_ROOT)
    mod_name = "lib.sources." + ".".join(rel.parts) + ".config"
    return importlib.import_module(mod_name)


def iter_source_library_seeds() -> Iterator[dict[str, Any]]:
    """Yield ``upsert_source_library`` kwargs for every URL in every adapter's ``seed_urls.txt``."""
    for adapter_dir in iter_adapter_dirs():
        cfg = _config_module(adapter_dir)
        source_id = cfg.SOURCE_ID
        resource_kind = str(getattr(cfg, "RESOURCE_KIND", "index"))
        crawl_notes = getattr(cfg, "CRAWL_NOTES", None)
        seed_path = adapter_dir / "seed_urls.txt"
        try:
            rel_display = seed_path.resolve().relative_to(_REPO_ROOT.resolve())
        except ValueError:
            rel_display = Path("src") / "lib" / "sources" / adapter_dir.relative_to(_SOURCES_ROOT) / "seed_urls.txt"
        pairs = parse_seed_urls_file(seed_path)
        for url, label in pairs:
            if not label:
                label = url[:500]
            notes_parts = [f"Seeded from {rel_display.as_posix()}"]
            if crawl_notes:
                notes_parts.append(str(crawl_notes).strip())
            yield {
                "url": url,
                "adapter_id": str(source_id),
                "label": str(label)[:500],
                "resource_kind": resource_kind,
                "notes": " — ".join(notes_parts),
            }
