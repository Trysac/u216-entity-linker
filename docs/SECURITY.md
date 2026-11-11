# Security

## Threat model

Defended:

- **Input size limits**: `link` rejects text longer than `max_chars` (default 1,000,000) with
  `LinkerError('input_too_large')`.
- **Catalog size limits**: `Catalog` rejects more than 100,000 entities, more than 1,000,000 names
  plus aliases, names or aliases with more than 10 tokens, and entity ids outside 1-128
  characters.
- **CLI catalog file size**: `python -m entity_linker` rejects a catalog file whose size is over
  100 MB before parsing it.
- **No code execution from catalogs**: The CLI reads catalog data with `json.load`; entries must be
  JSON objects and fields are type-checked.
- **No user text in library errors**: `LinkerError` uses static messages. A duplicate-id error
  includes the entity id truncated to 128 characters; it does not include input text.
- **No network access in the library**: The library performs no I/O and calls no external
  services. The CLI reads only the paths it is given.

Not defended:

- Resource exhaustion within the allowed limits.
- Untrusted filesystem paths, file permissions, or other filesystem behavior in the CLI.
- Escaping or sanitizing mention output for downstream consumers.
- Semantic correctness of catalog content beyond the documented validation.

## Reporting

Please report vulnerabilities privately via the repository's security advisory page. Do not open a
public issue.
