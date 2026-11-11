# Project record

## Objective

Link mentions in text to a catalog of entities by name and alias: token-aligned longest match,
case and accent insensitive, context-term disambiguation, and exact character offsets.

## Scope

In scope:

- The public API `Catalog`, `Entity`, `Mention`, `LinkerError`, and `link` in package
  `entity_linker`.
- Token-aligned longest matching against catalog names and aliases.
- Case folding, NFD normalization, removal of Unicode category `Mn` marks, and original-input
  offsets.
- Context-term disambiguation using `window`, `prior`, and entity id ordering.
- Typed validation and input-size errors.
- The `python -m entity_linker` CLI for JSON catalogs and text files.

Out of scope: fuzzy or misspelled mentions, coreference and pronouns, learned models, and nested
mentions.

## Timeline

No dated milestones are recorded in the code or specification.

## Effort metrics

The factory fills these values; unmeasured values stay pending measurement.

| Metric | Value |
|---|---|
| Tokens (input / output) | 871256 / 62940 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.0961 |

## Factory run u216 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | generation | deepseek-v4-pro | yes | 1336 | 21616 | 0 | 3328 | 0.0438 |
| 2026-11-10 | fix-1 | deepseek-flash | no | 28684 | 5093 | 0 | 226816 | 0.0080 |
| 2026-11-10 | audit | deepseek-flash | no | 20652 | 23076 | 0 | 350208 | 0.0180 |
| 2026-11-10 | fix-2 | deepseek-flash | no | 10425 | 5986 | 0 | 119296 | 0.0055 |
| 2026-11-10 | docs | deepseek-flash | no | 110255 | 7169 | 0 | 256 | 0.0208 |

Total: $0.0961. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
