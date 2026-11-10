# trysac-entity-linker

Deterministic, catalog-driven entity mention detection for Python. Link mentions in text to a
catalog of entities by name and alias with token-aligned longest match, case and accent
insensitivity, context-term disambiguation, and exact character offsets.

[![PyPI version](https://img.shields.io/pypi/v/trysac-entity-linker.svg)](https://pypi.org/project/trysac-entity-linker/)
![Python versions](https://img.shields.io/pypi/pyversions/trysac-entity-linker.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Why this library?

Applications that tag documents with known products, places or people need more than a simple
string search: aliases vary, accents and capitalisation differ, longer names must win over shorter
ones, and the same name can refer to two entities. Hand-rolled matching produces partial-word hits
and wrong offsets once text is normalized. This library links mentions to a catalog
deterministically, disambiguates by nearby context terms, and reports offsets into the original
text.

## Why not NER models

NER models discover entities and require learned model data. This library links mentions to a
catalog that you supply, is deterministic, reports offsets into the original input, and uses only
the Python standard library. It does not handle fuzzy or misspelled mentions, coreference or
pronouns, learned models, or nested mentions.

## Installation

```bash
pip install trysac-entity-linker
```

Requires Python 3.10+. There are no runtime dependencies.

## Quick start

```python
from entity_linker import Catalog, Entity, link

catalog = Catalog(
    [
        Entity("Q1", "Lima", context_terms=("peru", "capital")),
        Entity("Q2", "Lima", context_terms=("ohio",)),
    ]
)
mentions = link("I flew to Lima, the capital of Peru.", catalog)
print(mentions[0])
```

The first mention has `start=10`, `end=14`, `surface='Lima'`, `entity_id='Q1'`,
`candidates=('Q1', 'Q2')`, `score=2`, and `ambiguous=False`.

## Features

- **Token-aligned longest match**: Matches are whole folded token sequences; longer names win;
  matches do not overlap.
- **Case and accent insensitive**: Each character is casefolded, decomposed with NFD, and
  combining marks in Unicode category `Mn` are removed.
- **Exact offsets**: Offsets refer to the original input string, including when folding expands a
  character such as the German sharp s.
- **Context-term disambiguation**: Candidate entities are scored by distinct catalog context terms
  found within `window` characters before or after the mention; ties are broken by higher prior,
  then lower entity id.
- **Limits enforced**: At most 100,000 entities, 1,000,000 names plus aliases, 10 tokens per name
  or alias, entity ids of 1-128 characters, and an input length cap of 1,000,000 characters by
  default.
- **Typed errors**: `LinkerError` carries a machine-readable `code`.

## API

### `Entity`

```python
@dataclass(frozen=True)
class Entity:
    id: str
    name: str
    aliases: tuple[str, ...] = ()
    context_terms: tuple[str, ...] = ()
    prior: int = 0
```

### `Catalog`

```python
catalog = Catalog(entities)  # entities: Sequence[Entity]
```

Builds the token trie, candidate map, entity map, and folded context sequences once. Raises
`LinkerError` with code `'duplicate_id'` for duplicate ids, `'invalid_alias'` for invalid aliases,
and `'invalid_entity'` for invalid entity data or exceeded catalog limits.

### `link`

```python
mentions = link(text, catalog, *, window=50, max_chars=1_000_000)
```

Returns a tuple of `Mention` objects in order of appearance. Raises `LinkerError` with code
`'input_too_large'` when `len(text) > max_chars`. The `window` option sets the maximum character
distance for context terms before or after a mention.

### `Mention`

```python
@dataclass(frozen=True)
class Mention:
    start: int
    end: int
    surface: str
    entity_id: str
    candidates: tuple[str, ...]
    score: int
    ambiguous: bool
```

`candidates` lists every entity id for the matched surface in id order. `surface` is
`text[start:end]`. `ambiguous` is true when the top two candidates have equal score.

## Command-line interface

```bash
python -m entity_linker --catalog catalog.json text.txt
```

- `catalog.json`: JSON array of entity objects with keys `id`, `name`, optional `aliases`,
  `context_terms`, and `prior`. Catalog files over 100 MB are rejected.
- `text.txt`: Text to process. The `link` input length limit applies.
- Output: JSON array of mentions with sorted keys.
- Exit codes: `0` success; `2` for usage, IO, invalid catalog, or other handled errors.

## Development

Run the tests with `python -m pytest`.

## License

MIT

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model and reporting policy.
