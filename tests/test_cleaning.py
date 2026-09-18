import json
from pathlib import Path

from jobscope.cleaning import (
    clean_corpus,
    clean_text,
    is_supported_contract,
    normalize_whitespace,
    strip_html,
)


def test_strip_html_removes_tags_and_unescapes_entities() -> None:
    raw = "<p>D&eacute;veloppeur <b>Python</b></p>"

    assert strip_html(raw) == "Développeur Python"


def test_normalize_whitespace_collapses_runs_and_strips() -> None:
    raw = "  Bonjour   le \n\n\n monde \t !  "

    assert normalize_whitespace(raw) == "Bonjour le monde !"


def test_clean_text_combines_both() -> None:
    raw = "<p>Bonjour   le   monde</p>\n\n"

    assert clean_text(raw) == "Bonjour le monde"


def test_is_supported_contract_accepts_cdi_and_cdd_codes() -> None:
    assert is_supported_contract({"typeContrat": "CDI"})
    assert is_supported_contract({"typeContrat": "CDD"})


def test_is_supported_contract_accepts_alternance_and_stage_by_libelle() -> None:
    assert is_supported_contract({"typeContrat": "FRA", "typeContratLibelle": "Contrat d'apprentissage"})
    assert is_supported_contract({"typeContrat": "FRA", "typeContratLibelle": "Convention de stage"})
    assert is_supported_contract({"typeContrat": "FRA", "typeContratLibelle": "Contrat d'alternance"})
    assert is_supported_contract({"typeContrat": "FRA", "typeContratLibelle": "Contrat d'alternant"})


def test_is_supported_contract_rejects_unsupported_codes() -> None:
    assert not is_supported_contract({"typeContrat": "LIB", "typeContratLibelle": "Profession liberale"})
    assert not is_supported_contract({"typeContrat": "MIS", "typeContratLibelle": "Interim - 3 Mois"})
    assert not is_supported_contract({"typeContrat": "SAI"})


def test_clean_corpus_deduplicates_identical_descriptions(tmp_path: Path) -> None:
    input_path = tmp_path / "raw.jsonl"
    output_path = tmp_path / "clean.jsonl"
    input_path.write_text(
        '{"id": "A1", "typeContrat": "CDI", "intitule": "Dev", "description": "Meme   annonce"}\n'
        '{"id": "A2", "typeContrat": "CDI", "intitule": "Dev", "description": "Meme annonce"}\n'
        '{"id": "A3", "typeContrat": "CDI", "intitule": "Dev", "description": "Annonce differente"}\n',
        encoding="utf-8",
    )

    total_read, total_kept, dropped = clean_corpus(input_path, output_path)

    assert total_read == 3
    assert total_kept == 2
    assert dropped == {}
    kept_ids = [json.loads(line)["id"] for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert kept_ids == ["A1", "A3"]


def test_clean_corpus_drops_unsupported_contract_types(tmp_path: Path) -> None:
    input_path = tmp_path / "raw.jsonl"
    output_path = tmp_path / "clean.jsonl"
    input_path.write_text(
        '{"id": "A1", "typeContrat": "CDI", "intitule": "Dev", "description": "Une annonce"}\n'
        '{"id": "A2", "typeContrat": "LIB", "intitule": "Consultant", "description": "Autre annonce"}\n',
        encoding="utf-8",
    )

    total_read, total_kept, dropped = clean_corpus(input_path, output_path)

    assert total_read == 2
    assert total_kept == 1
    assert dropped == {"LIB": 1}
