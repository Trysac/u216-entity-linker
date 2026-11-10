# Testing

## Running

```sh
python -m pytest
```

## Policy

The tests are pytest functions in `tests/test_core.py` and `tests/test_cli.py`. They use temporary
paths for CLI input files and assert the observable results of the public API and CLI. No coverage
threshold or CI conformance setup is present in the provided code.

## Tiers

There is one local pytest tier: `tests/test_core.py` and `tests/test_cli.py`. No test markers or
external conformance downloads are defined in the provided tests.

## Layout

- `tests/test_core.py` covers context-term disambiguation, equal-score ambiguity, longest match
  (`New York City` over `New York`), and token alignment (`Limabean` produces no mention while
  `Lima.` and `(Lima)` each produce one).
- `tests/test_cli.py` covers CLI success with JSON output and return code `0`, a missing file
  returning `2`, an invalid catalog returning `2`, and a catalog file over 100 MB returning `2`.
