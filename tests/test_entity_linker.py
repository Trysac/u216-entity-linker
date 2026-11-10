"""Behavior tests for the public API of entity_linker."""

from __future__ import annotations

import entity_linker


def test_public_api_exports_the_documented_names() -> None:
    expected = {"Catalog", "Entity", "LinkerError", "LinkerErrorCode", "Mention", "link"}
    assert expected <= set(entity_linker.__all__)


def test_version_is_semver() -> None:
    parts = entity_linker.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_package_level_link_returns_mentions() -> None:
    catalog = entity_linker.Catalog([entity_linker.Entity("Q1", "Lima")])
    mentions = entity_linker.link("Lima", catalog)
    assert mentions == (
        entity_linker.Mention(
            start=0,
            end=4,
            surface="Lima",
            entity_id="Q1",
            candidates=("Q1",),
            score=0,
            ambiguous=False,
        ),
    )
