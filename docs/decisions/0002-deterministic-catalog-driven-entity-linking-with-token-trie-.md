# Deterministic catalog-driven entity linking with token trie and folding

Status: accepted (generated, pending human review)

## Context

The utility must link mentions to known entities. Requirements include longest match, accent/case insensitivity, exact offsets, disambiguation by context terms, and bounded resource usage.

## Decision

Normalize by casefold+NFD+remove marks with offset mapping, tokenize into alphanumeric runs, build a trie over token sequences, and scan left-to-right for longest matches. Disambiguation scores candidates by context term presence within a window.

## Consequences

Implementation is deterministic, testable, and has clear complexity bounds. Users must provide a catalog; the library does not discover new entities. Performance is linear in input length for matching, with trie construction O(total tokens).
