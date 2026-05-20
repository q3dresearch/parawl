"""
Parliament of Malaysia — Dewan Rakyat / Dewan Negara bill listing adapters.

Official listing pages (human-facing):
  - https://www.parlimen.gov.my/bills-dewan-rakyat.html
  - https://www.parlimen.gov.my/bills-dewan-negara.html

Many requests from cloud/datacenter IPs receive HTTP 403; run fetches from a
normal browser network when needed, or paste saved HTML into ``parse`` tests.
"""

from . import config, fetch, parse

__all__ = ["config", "fetch", "parse"]
