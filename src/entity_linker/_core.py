from __future__ import annotations

import bisect
import logging
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger(__name__)

LinkerErrorCode = Literal["duplicate_id", "invalid_alias", "invalid_entity", "input_too_large"]


class LinkerError(ValueError):
    def __init__(self, code: LinkerErrorCode, message: str = ""):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class Entity:
    id: str
    name: str
    aliases: tuple[str, ...] = ()
    context_terms: tuple[str, ...] = ()
    prior: int = 0


@dataclass(frozen=True)
class Mention:
    start: int
    end: int
    surface: str
    entity_id: str
    candidates: tuple[str, ...]
    score: int
    ambiguous: bool


def _fold_text(text: str) -> tuple[list[str], list[int]]:
    """Fold text for matching: casefold, NFD, remove Mn marks.

    Returns parallel lists of folded characters and original indices for each.
    """
    folded_chars: list[str] = []
    index_map: list[int] = []
    for i, ch in enumerate(text):
        folded = ch.casefold()
        decomposed = unicodedata.normalize("NFD", folded)
        for dch in decomposed:
            if unicodedata.category(dch) != "Mn":
                folded_chars.append(dch)
                index_map.append(i)
    return folded_chars, index_map


def _tokenize(text: str) -> list[tuple[int, int, str]]:
    """Tokenize folded text into maximal runs of alphanumeric characters.

    Returns list of (start, end, token) where start/end are original offsets.
    """
    folded_chars, index_map = _fold_text(text)
    tokens: list[tuple[int, int, str]] = []
    i = 0
    n = len(folded_chars)
    while i < n:
        if folded_chars[i].isalnum():
            start_folded = i
            start_orig = index_map[i]
            while i < n and folded_chars[i].isalnum():
                i += 1
            end_folded = i
            end_orig = index_map[i - 1] + 1  # last char original index + 1
            token_str = "".join(folded_chars[start_folded:end_folded])
            tokens.append((start_orig, end_orig, token_str))
        else:
            i += 1
    return tokens


class _TrieNode:
    __slots__ = ("children", "entities")

    def __init__(self) -> None:
        self.children: dict[str, _TrieNode] = {}
        self.entities: set[str] = set()


class Catalog:
    """Catalog of entities with prebuilt token trie for efficient matching."""

    _MAX_ENTITIES = 100_000
    _MAX_TOTAL_NAMES = 1_000_000
    _MAX_TOKENS_PER_NAME = 10

    def __init__(self, entities: Sequence[Entity]):
        self._entities = tuple(entities)
        self._validate()
        self._build_trie()
        self._build_candidates()
        self._build_entity_map()
        self._build_context_seqs()

    def _validate(self) -> None:
        if len(self._entities) > self._MAX_ENTITIES:
            raise LinkerError("invalid_entity", "too many entities")
        total_names = sum(1 + len(e.aliases) for e in self._entities)
        if total_names > self._MAX_TOTAL_NAMES:
            raise LinkerError("invalid_entity", "too many names and aliases")
        seen_ids: set[str] = set()
        for entity in self._entities:
            if not isinstance(entity.id, str) or not (1 <= len(entity.id) <= 128):
                raise LinkerError("invalid_entity", "entity id must be 1-128 characters")
            if entity.id in seen_ids:
                raise LinkerError("duplicate_id", f"duplicate entity id: {entity.id[:128]}")
            seen_ids.add(entity.id)
            name_tokens = _tokenize(entity.name)
            if not name_tokens:
                raise LinkerError(
                    "invalid_entity", "entity name must contain letters or digits after folding"
                )
            if len(name_tokens) > self._MAX_TOKENS_PER_NAME:
                raise LinkerError("invalid_entity", "entity name has too many tokens")
            for alias in entity.aliases:
                if not isinstance(alias, str):
                    raise LinkerError("invalid_alias", "alias must be a string")
                alias_tokens = _tokenize(alias)
                if not alias_tokens:
                    raise LinkerError(
                        "invalid_alias", "alias must contain letters or digits after folding"
                    )
                if len(alias_tokens) > self._MAX_TOKENS_PER_NAME:
                    raise LinkerError("invalid_alias", "alias has too many tokens")

    def _build_trie(self) -> None:
        self._root = _TrieNode()
        for entity in self._entities:
            name_tokens = [tok[2] for tok in _tokenize(entity.name)]
            self._insert_sequence(self._root, name_tokens, entity.id)
            for alias in entity.aliases:
                alias_tokens = [tok[2] for tok in _tokenize(alias)]
                self._insert_sequence(self._root, alias_tokens, entity.id)

    def _insert_sequence(self, root: _TrieNode, tokens: list[str], entity_id: str) -> None:
        node = root
        for token in tokens:
            if token not in node.children:
                node.children[token] = _TrieNode()
            node = node.children[token]
        node.entities.add(entity_id)

    def _build_candidates(self) -> None:
        self._surface_map: dict[tuple[str, ...], tuple[str, ...]] = {}

        def dfs(node: _TrieNode, prefix: tuple[str, ...]) -> None:
            if node.entities:
                self._surface_map[prefix] = tuple(sorted(node.entities))
            for token, child in node.children.items():
                dfs(child, (*prefix, token))

        dfs(self._root, ())

    def _build_entity_map(self) -> None:
        self._entity_by_id = {e.id: e for e in self._entities}

    def _build_context_seqs(self) -> None:
        """Fold and tokenize every entity's context terms exactly once."""
        self._context_seqs: dict[str, tuple[tuple[str, ...], ...]] = {}
        for entity in self._entities:
            seqs: set[tuple[str, ...]] = set()
            for term in entity.context_terms:
                term_tokens = tuple(tok[2] for tok in _tokenize(term))
                if term_tokens:
                    seqs.add(term_tokens)
            self._context_seqs[entity.id] = tuple(seqs)

    def get_entity(self, entity_id: str) -> Entity | None:
        return self._entity_by_id.get(entity_id)

    def _get_candidates(self, token_seq: tuple[str, ...]) -> tuple[str, ...]:
        return self._surface_map.get(token_seq, ())


def link(
    text: str,
    catalog: Catalog,
    *,
    window: int = 50,
    max_chars: int = 1_000_000,
) -> tuple[Mention, ...]:
    """Link mentions in text to entities in catalog.

    Args:
        text: Input text.
        catalog: Prebuilt catalog.
        window: Maximum character distance for context terms (before/after mention).
        max_chars: Maximum allowed input length.

    Returns:
        Tuple of Mention objects in order of appearance.

    Raises:
        LinkerError: If input exceeds max_chars or other errors.
    """
    if len(text) > max_chars:
        raise LinkerError("input_too_large", "text exceeds maximum allowed characters")
    tokens = _tokenize(text)
    if not tokens:
        return ()
    token_starts = [token[0] for token in tokens]
    token_ends = [token[1] for token in tokens]
    mentions: list[Mention] = []
    token_count = len(tokens)
    i = 0
    while i < token_count:
        node = catalog._root
        last_match_j = -1
        j = i
        while j < token_count:
            token = tokens[j][2]
            if token not in node.children:
                break
            node = node.children[token]
            j += 1
            if node.entities:
                last_match_j = j - 1  # index of last token of match
        if last_match_j >= i:
            start = tokens[i][0]
            end = tokens[last_match_j][1]
            surface = text[start:end]
            token_seq = tuple(tokens[k][2] for k in range(i, last_match_j + 1))
            candidates = catalog._get_candidates(token_seq)
            best_entity_id, best_score, ambiguous = _disambiguate(
                tokens, token_starts, token_ends, start, end, candidates, catalog, window
            )
            mentions.append(
                Mention(start, end, surface, best_entity_id, candidates, best_score, ambiguous)
            )
            i = last_match_j + 1
        else:
            i += 1
    return tuple(mentions)


def _disambiguate(
    tokens: list[tuple[int, int, str]],
    token_starts: list[int],
    token_ends: list[int],
    mention_start: int,
    mention_end: int,
    candidate_ids: tuple[str, ...],
    catalog: Catalog,
    window: int,
) -> tuple[str, int, bool]:
    before_lo = bisect.bisect_left(token_ends, mention_start - window)
    before_hi = bisect.bisect_right(token_ends, mention_start)
    before_tokens = [tokens[k][2] for k in range(before_lo, before_hi)]
    after_lo = bisect.bisect_left(token_starts, mention_end)
    after_hi = bisect.bisect_right(token_starts, mention_end + window)
    after_tokens = [tokens[k][2] for k in range(after_lo, after_hi)]
    candidate_scores: dict[str, int] = {}
    for entity_id in candidate_ids:
        context_seqs = catalog._context_seqs.get(entity_id, ())
        # Each distinct context term counts at most once, even when it occurs
        # both before and after the mention.
        score = sum(
            1
            for seq in context_seqs
            if _contains(before_tokens, seq) or _contains(after_tokens, seq)
        )
        candidate_scores[entity_id] = score

    def sort_key(entity_id: str) -> tuple[int, int, str]:
        entity = catalog.get_entity(entity_id)
        prior = entity.prior if entity else 0
        return (-candidate_scores[entity_id], -prior, entity_id)

    sorted_ids = sorted(candidate_ids, key=sort_key)
    winner = sorted_ids[0]
    winner_score = candidate_scores[winner]
    ambiguous = False
    if len(sorted_ids) > 1:
        second = sorted_ids[1]
        if candidate_scores[second] == winner_score:
            ambiguous = True
    return winner, winner_score, ambiguous


def _contains(tokens: list[str], seq: tuple[str, ...]) -> bool:
    """Return True if ``seq`` occurs as a contiguous token subsequence of ``tokens``."""
    n = len(tokens)
    seq_len = len(seq)
    if seq_len == 0 or seq_len > n:
        return False
    first = seq[0]
    for i in range(n - seq_len + 1):
        if tokens[i] == first and tuple(tokens[i : i + seq_len]) == seq:
            return True
    return False
