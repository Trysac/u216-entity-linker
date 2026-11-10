import json
from pathlib import Path

from entity_linker.__main__ import main


def test_cli_success(tmp_path: Path):
    catalog_data = [
        {
            "id": "Q1",
            "name": "Lima",
            "context_terms": ["peru", "capital"],
        }
    ]
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(catalog_data), encoding="utf-8")
    text_path = tmp_path / "text.txt"
    text_path.write_text("I flew to Lima, the capital of Peru.", encoding="utf-8")

    argv = ["--catalog", str(catalog_path), str(text_path)]
    # Capture stdout
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        ret = main(argv)
    assert ret == 0
    output = json.loads(f.getvalue())
    assert len(output) == 1
    assert output[0]["entity_id"] == "Q1"


def test_cli_missing_file(tmp_path: Path):
    argv = ["--catalog", str(tmp_path / "nonexistent.json"), str(tmp_path / "text.txt")]
    assert main(argv) == 2


def test_cli_invalid_catalog(tmp_path: Path):
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text("not json", encoding="utf-8")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello", encoding="utf-8")
    argv = ["--catalog", str(catalog_path), str(text_path)]
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        ret = main(argv)
    assert ret == 2


def test_cli_catalog_too_large(tmp_path: Path):
    catalog_path = tmp_path / "catalog.json"
    # Create file larger than 100MB (sparse or dummy)
    with open(catalog_path, "wb") as f:
        f.seek(100 * 1024 * 1024)
        f.write(b"\0")
    text_path = tmp_path / "text.txt"
    text_path.write_text("hello", encoding="utf-8")
    argv = ["--catalog", str(catalog_path), str(text_path)]
    import io
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        ret = main(argv)
    assert ret == 2
