# entity-linker

[![PyPI version](https://img.shields.io/pypi/v/trysac-entity-linker)](https://pypi.org/project/trysac-entity-linker/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-entity-linker)](LICENSE)
[![CI](https://github.com/Trysac/u216-entity-linker/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u216-entity-linker/actions/workflows/ci.yml)

Link mentions in text to a catalog of entities by name and alias: token-aligned longest match, case and accent insensitive, context-term disambiguation and exact character offsets

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-entity-linker
# or
uv add trysac-entity-linker
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import entity_linker

# normalize() trims surrounding whitespace and lower-cases the text.
print(entity_linker.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    entity_linker.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
