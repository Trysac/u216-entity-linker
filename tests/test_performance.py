"""Performance regression tests: linking must stay linear in the input length."""

from __future__ import annotations

import time

from entity_linker import Catalog, Entity, link


def test_large_text_with_many_mentions_completes_quickly() -> None:
    catalog = Catalog([Entity("Q1", "Lima")])
    text = "Lima " * 200_000
    assert len(text) == 1_000_000

    started = time.perf_counter()
    mentions = link(text, catalog)
    elapsed = time.perf_counter() - started

    assert len(mentions) == 200_000
    assert mentions[0].start == 0
    assert mentions[0].end == 4
    assert mentions[-1].start == 999_995
    assert mentions[-1].end == 999_999
    assert elapsed < 30.0
