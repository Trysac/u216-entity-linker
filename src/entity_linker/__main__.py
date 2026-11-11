from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from ._core import Catalog, Entity, LinkerError, link


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="entity-linker", description="Link mentions in text to a catalog."
    )
    parser.add_argument("--catalog", required=True, help="Path to JSON catalog file")
    parser.add_argument("text_file", help="Path to text file")
    args = parser.parse_args(argv)

    try:
        catalog_path = Path(args.catalog)
        if catalog_path.stat().st_size > 100 * 1024 * 1024:
            print("Error: catalog file exceeds 100MB limit", file=sys.stderr)
            return 2
        with open(catalog_path, encoding="utf-8") as f:
            catalog_data = json.load(f)
        entities = _parse_catalog(catalog_data)
        catalog = Catalog(entities)

        text_path = Path(args.text_file)
        with open(text_path, encoding="utf-8") as f:
            text = f.read()

        mentions = link(text, catalog)
        output = [asdict(mention) for mention in mentions]
        print(json.dumps(output, sort_keys=True))
        return 0
    except (FileNotFoundError, json.JSONDecodeError, LinkerError, ValueError, TypeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


def _parse_catalog(data: object) -> list[Entity]:
    if not isinstance(data, list):
        raise ValueError("catalog must be a JSON array")
    entities: list[Entity] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("each catalog entry must be an object")
        id_val = item.get("id")
        if not isinstance(id_val, str):
            raise ValueError("entity 'id' is required and must be a string")
        name = item.get("name")
        if not isinstance(name, str):
            raise ValueError("entity 'name' is required and must be a string")
        aliases = item.get("aliases", [])
        if not isinstance(aliases, list) or not all(isinstance(a, str) for a in aliases):
            raise ValueError("'aliases' must be a list of strings")
        context_terms = item.get("context_terms", [])
        if not isinstance(context_terms, list) or not all(
            isinstance(t, str) for t in context_terms
        ):
            raise ValueError("'context_terms' must be a list of strings")
        prior = item.get("prior", 0)
        if not isinstance(prior, int):
            raise ValueError("'prior' must be an integer")
        entities.append(Entity(id_val, name, tuple(aliases), tuple(context_terms), prior))
    return entities


if __name__ == "__main__":
    sys.exit(main())
