# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `JobPosting` Pydantic schema (`src/jobscope/schema.py`): `Seniority`, `ContractType`, `HomeOfficePolicy` enums, `SalaryRange`, and `skills` field.
- Test fixtures (`tests/fixtures/`) and schema validation tests (`tests/test_schema.py`).
- Project tooling: `mypy` (strict mode) and `ruff`, configured in `pyproject.toml`.
- CI workflow (`.github/workflows/ci.yml`) running `mypy` and `pytest` on push to `main` and on pull requests.
- Data source decision (`docs/data-sources.md`): France Travail's "Offres d'emploi" API selected after evaluating France Travail, Indeed, and Welcome to the Jungle against ToS, `robots.txt`, and API availability.
