import pytest

from entity_linker import Catalog, Entity, LinkerError, link


def _cat(*entities: Entity) -> Catalog:
    return Catalog(entities)


def test_acceptance_context_disambiguation():
    catalog = _cat(
        Entity("Q1", "Lima", context_terms=("peru", "capital")),
        Entity("Q2", "Lima", context_terms=("ohio",)),
    )
    mentions = link("I flew to Lima, the capital of Peru.", catalog)
    assert len(mentions) == 1
    m = mentions[0]
    assert m.start == 10
    assert m.end == 14
    assert m.surface == "Lima"
    assert m.entity_id == "Q1"
    assert m.candidates == ("Q1", "Q2")
    assert m.score == 2
    assert m.ambiguous is False


def test_acceptance_ambiguous_same_score():
    catalog = _cat(
        Entity("Q1", "Lima", context_terms=("peru", "capital")),
        Entity("Q2", "Lima", context_terms=("ohio",)),
    )
    mentions = link("Lima is nice.", catalog)
    assert len(mentions) == 1
    m = mentions[0]
    assert m.entity_id == "Q1"
    assert m.score == 0
    assert m.ambiguous is True


def test_acceptance_longest_match():
    catalog = _cat(
        Entity("Q3", "New York City"),
        Entity("Q4", "New York"),
    )
    mentions = link("Visit New York City now", catalog)
    assert len(mentions) == 1
    m = mentions[0]
    assert m.entity_id == "Q3"
    assert m.start == 6
    assert m.end == 19


def test_acceptance_token_alignment():
    catalog = _cat(Entity("Q1", "Lima"))
    assert link("Limabean", catalog) == ()
    m1 = link("Lima.", catalog)
    assert len(m1) == 1
    assert m1[0].start == 0
    assert m1[0].end == 4
    m2 = link("(Lima)", catalog)
    assert len(m2) == 1
    assert m2[0].start == 1
    assert m2[0].end == 5


def test_acceptance_accent_insensitive():
    catalog = _cat(Entity("Q5", "S\u00e3o Paulo", aliases=("SP",)))
    text = "Flights to sao paulo today"
    m1 = link(text, catalog)
    assert len(m1) == 1
    assert m1[0].start == 11
    assert m1[0].end == 20
    assert m1[0].surface == "sao paulo"
    text2 = "S\u00c3O PAULO"
    m2 = link(text2, catalog)
    assert len(m2) == 1
    assert m2[0].surface == text2
    text3 = "I live in SP city"
    m3 = link(text3, catalog)
    assert len(m3) == 1
    assert m3[0].surface == "SP"


def test_acceptance_duplicate_id_error():
    with pytest.raises(LinkerError) as exc_info:
        Catalog([Entity("Q1", "First"), Entity("Q1", "Second")])
    assert exc_info.value.code == "duplicate_id"


def test_acceptance_invalid_alias_error():
    with pytest.raises(LinkerError) as exc_info:
        Catalog([Entity("Q1", "Name", aliases=("!!!",))])
    assert exc_info.value.code == "invalid_alias"


def test_acceptance_input_too_large():
    catalog = _cat(Entity("Q1", "Name"))
    with pytest.raises(LinkerError) as exc_info:
        link("a" * 1_000_001, catalog)
    assert exc_info.value.code == "input_too_large"
    # 1_000_000 chars accepted
    assert link("a" * 1_000_000, catalog) == ()


def test_context_window_limits():
    catalog = _cat(
        Entity("A", "Target", context_terms=("near",)),
        Entity("B", "Target", context_terms=("far",)),
    )
    # "near" ends 55 characters before the mention, so it is outside the 50-character window:
    # both candidates score 0 and the tie goes to the lowest id.
    text = "near" + " " * 55 + "Target"
    m = link(text, catalog, window=50)
    assert len(m) == 1
    assert m[0].entity_id == "A"
    assert m[0].score == 0
    # Now within window
    text2 = "near" + " " * 30 + "Target"
    m2 = link(text2, catalog, window=50)
    assert len(m2) == 1
    assert m2[0].entity_id == "A"


def test_mention_at_start_and_end():
    catalog = _cat(Entity("Q", "hello"))
    m = link("hello world hello", catalog)
    assert len(m) == 2
    assert m[0].start == 0
    assert m[0].end == 5
    assert m[1].start == 12
    assert m[1].end == 17


def test_adjacent_mentions():
    catalog = _cat(Entity("A", "foo"), Entity("B", "bar"))
    m = link("foobar", catalog)
    assert len(m) == 0  # 'foobar' is one token, no match
    m = link("foo bar", catalog)
    assert len(m) == 2
    assert m[0].entity_id == "A"
    assert m[1].entity_id == "B"


def test_three_entities_same_name():
    catalog = _cat(
        Entity("1", "Common"),
        Entity("2", "Common"),
        Entity("3", "Common"),
    )
    m = link("Common", catalog)
    assert len(m) == 1
    assert m[0].candidates == ("1", "2", "3")
    assert m[0].entity_id == "1"  # all score 0, lowest id
    assert m[0].ambiguous is True


def test_alias_equals_other_name():
    catalog = _cat(
        Entity("A", "NameX"),
        Entity("B", "Other", aliases=("NameX",)),
    )
    m = link("NameX", catalog)
    assert len(m) == 1
    assert m[0].candidates == ("A", "B")
    assert m[0].entity_id == "A"  # tie, lowest id


def test_context_multitoken():
    catalog = _cat(
        Entity("A", "Target", context_terms=("new york",)),
        Entity("B", "Target", context_terms=("los angeles",)),
    )
    text = "new york" + " " * 10 + "Target"
    m = link(text, catalog)
    assert len(m) == 1
    assert m[0].entity_id == "A"


def test_context_term_counted_once_on_both_sides():
    catalog = _cat(
        Entity("A", "Target", context_terms=("near",)),
        Entity("B", "Target", context_terms=("other",)),
    )
    m = link("near Target near", catalog)
    assert len(m) == 1
    assert m[0].score == 1  # 'near' occurs before and after, but counts once
    assert m[0].entity_id == "A"
    assert m[0].ambiguous is False


def test_folding_expands_sharp_s():
    catalog = _cat(Entity("S", "stra\u00dfe"))  # 'straße'
    text = "STRASSE"  # 'STRASSE' capital SS
    m = link(text, catalog)
    assert len(m) == 1
    assert m[0].surface == text
    assert m[0].entity_id == "S"
