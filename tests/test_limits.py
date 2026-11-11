import pytest

from entity_linker import Catalog, Entity, LinkerError


def test_max_entities():
    entities = [Entity(f"id{i}", "Name") for i in range(100_001)]
    with pytest.raises(LinkerError) as exc_info:
        Catalog(entities)
    assert exc_info.value.code == "invalid_entity"


def test_max_total_names():
    # Create 100_000 entities each with 10 aliases => 1_100_000 names+aliases
    # But total limit is 1_000_000, so exceed
    entities = []
    for i in range(100_000):
        e = Entity(f"id{i}", "Name", aliases=tuple(f"alias{j}" for j in range(10)))
        entities.append(e)
    with pytest.raises(LinkerError) as exc_info:
        Catalog(entities)
    assert exc_info.value.code == "invalid_entity"


def test_name_too_many_tokens():
    name = " ".join(["token"] * 11)
    with pytest.raises(LinkerError) as exc_info:
        Catalog([Entity("Q", name)])
    assert exc_info.value.code == "invalid_entity"


def test_alias_too_many_tokens():
    alias = " ".join(["token"] * 11)
    with pytest.raises(LinkerError) as exc_info:
        Catalog([Entity("Q", "ValidName", aliases=(alias,))])
    assert exc_info.value.code == "invalid_alias"


def test_entity_id_too_long():
    with pytest.raises(LinkerError) as exc_info:
        Catalog([Entity("A" * 129, "Name")])
    assert exc_info.value.code == "invalid_entity"


def test_entity_id_too_short():
    with pytest.raises(LinkerError) as exc_info:
        Catalog([Entity("", "Name")])
    assert exc_info.value.code == "invalid_entity"
