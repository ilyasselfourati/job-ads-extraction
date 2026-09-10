from pathlib import Path

from jobscope.scraping.france_travail import append_offers, load_existing_ids


def test_load_existing_ids_empty_when_file_missing(tmp_path: Path) -> None:
    output_path = tmp_path / "offers.jsonl"

    assert load_existing_ids(output_path) == set()


def test_load_existing_ids_reads_ids_from_existing_file(tmp_path: Path) -> None:
    output_path = tmp_path / "offers.jsonl"
    output_path.write_text('{"id": "A1"}\n{"id": "A2"}\n', encoding="utf-8")

    assert load_existing_ids(output_path) == {"A1", "A2"}


def test_append_offers_skips_duplicates(tmp_path: Path) -> None:
    output_path = tmp_path / "offers.jsonl"
    seen_ids: set[str] = {"A1"}

    new_count = append_offers(
        output_path,
        offers=[{"id": "A1", "intitule": "already seen"}, {"id": "A2", "intitule": "new"}],
        seen_ids=seen_ids,
    )

    assert new_count == 1
    assert seen_ids == {"A1", "A2"}
    assert load_existing_ids(output_path) == {"A2"}


def test_append_offers_is_idempotent_across_calls(tmp_path: Path) -> None:
    output_path = tmp_path / "offers.jsonl"
    seen_ids: set[str] = set()

    first_run = append_offers(output_path, offers=[{"id": "A1"}, {"id": "A2"}], seen_ids=seen_ids)
    second_run = append_offers(output_path, offers=[{"id": "A1"}, {"id": "A2"}], seen_ids=seen_ids)

    assert first_run == 2
    assert second_run == 0
    assert load_existing_ids(output_path) == {"A1", "A2"}
