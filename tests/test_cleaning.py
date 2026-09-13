import json
from pathlib import Path

from jobscope.cleaning import clean_corpus, clean_text, normalize_whitespace, strip_html


def test_strip_html_removes_tags_and_unescapes_entities() -> None:
    raw = "<p>D&eacute;veloppeur <b>Python</b></p>"

    assert strip_html(raw) == "Développeur Python"


def test_normalize_whitespace_collapses_runs_and_strips() -> None:
    raw = "  Bonjour   le \n\n\n monde \t !  "

    assert normalize_whitespace(raw) == "Bonjour le monde !"


def test_clean_text_combines_both() -> None:
    raw = "<p>Bonjour   le   monde</p>\n\n"

    assert clean_text(raw) == "Bonjour le monde"


def test_clean_corpus_deduplicates_identical_descriptions(tmp_path: Path) -> None:
    input_path = tmp_path / "raw.jsonl"
    output_path = tmp_path / "clean.jsonl"
    input_path.write_text(
        '{"id": "A1", "intitule": "Dev", "description": "Meme   annonce"}\n'
        '{"id": "A2", "intitule": "Dev", "description": "Meme annonce"}\n'
        '{"id": "A3", "intitule": "Dev", "description": "Annonce differente"}\n',
        encoding="utf-8",
    )

    total_read, total_kept = clean_corpus(input_path, output_path)

    assert total_read == 3
    assert total_kept == 2
    kept_ids = [json.loads(line)["id"] for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert kept_ids == ["A1", "A3"]
