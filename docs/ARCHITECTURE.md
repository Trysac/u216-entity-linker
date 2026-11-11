# Architecture

`trysac-entity-linker` performs deterministic entity mention detection by combining three ideas:

1. **Normalization without losing offsets**: Each character is casefolded, decomposed with NFD,
   and all non‑spacing marks (Unicode category `Mn`) are removed. A parallel mapping keeps, for
   every folded character, the index of the original character that produced it. This allows exact
   offset reporting even when folding expands a character (e.g., `ß` → `ss`) or removes marks.

2. **Token-aligned longest match via trie**: After folding, the text is tokenized into maximal runs
   of alphanumeric characters. All entity names and aliases are tokenized and inserted into a trie.
   Scanning the token stream left to right, the longest sequence present in the trie is selected at
   each position. This guarantees that `New York City` wins over `New York`, and that partial-word
   matches like `Limabean` are not produced.

3. **Context-term disambiguation**: For each candidate entity sharing a surface, a score is
   computed as the number of distinct folded context terms that appear as token sequences within a
   configurable character window before or after the mention. Highest score wins; ties are broken by
   higher prior, then lower id. An `ambiguous` flag is set when the top two candidates have equal
   scores.

Limits are enforced during catalog construction: at most 100,000 entities, 1,000,000 names plus
 aliases, each with at most 10 tokens, and entity ids of 1–128 characters. The `link` function
 enforces an input length limit (default 1,000,000 characters).

All errors are raised as `LinkerError` with a stable machine-readable `code` (`duplicate_id`,
`invalid_alias`, `invalid_entity`, `input_too_large`). The library uses a module-level logger with a
 `NullHandler`, and never logs user text.
