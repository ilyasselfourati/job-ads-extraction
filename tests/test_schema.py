from pathlib import Path

import pytest

from jobscope.schema import JobPosting

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE_FILES = sorted(FIXTURES_DIR.glob("*.json"))


@pytest.mark.parametrize("fixture_path", FIXTURE_FILES, ids=lambda p: p.stem)
def test_fixture_parses_as_job_posting(fixture_path: Path) -> None:
    raw_json = fixture_path.read_text(encoding="utf-8")

    posting = JobPosting.model_validate_json(raw_json)

    assert posting.seniority is not None
    assert posting.contract_type is not None
    assert posting.home_office_policy is not None


def test_minimal_fixture_uses_defaults() -> None:
    raw_json = (FIXTURES_DIR / "job_posting_minimal.json").read_text(encoding="utf-8")

    posting = JobPosting.model_validate_json(raw_json)

    assert posting.salary_range is None
    assert posting.skills == []


def test_freelance_fixture_uses_daily_salary_period() -> None:
    raw_json = (FIXTURES_DIR / "job_posting_partial_salary.json").read_text(encoding="utf-8")

    posting = JobPosting.model_validate_json(raw_json)

    assert posting.salary_range is not None
    assert posting.salary_range.salary_period == "daily"
    assert posting.salary_range.max_salary is None
