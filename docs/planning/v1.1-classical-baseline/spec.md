# Spec — v1.1: Classical ML Baseline

> Synthesized from the planning discussion on 2026-11-06/07. This is a local reference document, not published to the issue tracker — user stories and tickets are written separately, by hand (see `user-stories.md` in this folder, and the GitHub issue tracker for tickets).

## Problem Statement

The original JobScope plan asked one small, hand-annotated dataset (100 labeled postings) to support five extraction fields — three classification fields, one nested extraction field (`salary_range`), and one open-vocabulary span-extraction field (`skills`) — compared across three separate modeling approaches. That's too much complexity and not enough data for a first version of a personal learning project: most effort would go into fighting noisy metrics and annotation edge cases rather than learning ML and deployment.

Digging into the actual label distribution also surfaced a second, independent problem: one of the three classification fields, `contract_type`, has almost no signal to learn from (99 of 100 examples are `cdi`).

## Solution

Ship a deliberately small first version, and grow it in clearly named steps rather than building everything at once:

- **v1.1** (this spec): a classical ML baseline — TF-IDF features + a `LogisticRegression` classifier — for the two fields that actually have class diversity: `seniority` and `home_office_policy`. `contract_type` is dropped. `salary_range` and `skills` are deferred.
- **v1.2**: v1.1 + MLflow run tracking.
- **v1.x**: v1.2 + a FastAPI/Docker deployment (exact version number TBD).
- **v2**: `salary_range` extraction, `skills` CRF extraction, a human-ceiling re-annotation study, and revisiting `contract_type` if the dataset gains more contract-type diversity.
- Later, separate milestones (not yet scoped): a prompted-LLM approach and a fine-tuned-LLM approach, compared against this baseline.

## User Stories

See `user-stories.md` in this folder — written separately as a deliberate practice exercise.

## Implementation Decisions

- **Scope**: v1.1 targets exactly two fields — `seniority` (4 practical classes after merging) and `home_office_policy` (2 practical classes). `contract_type` is excluded, with the reason (99/100 `cdi`) documented so it doesn't read as an oversight later.
- **Data**: reuse the existing 100 annotated postings (`data/interim/annotated_data.csv`). No new scraping or annotation for v1.1.
- **Train/test split**: regenerate `train.csv`/`test.csv` with a **joint stratification key** combining `seniority` and `home_office_policy` — the current split only stratifies on `seniority`, which was fine when it was the only confirmed target but leaves `home_office_policy`'s minority class (`hybrid`) under-controlled in a 20-row test set. Before building the joint key, replace the single `manager` value with the majority `seniority` class (same merge rule already implemented in `split_train_test.ipynb`, via `replace_column_with_less_than_1_occurrence`), since a class with one member breaks stratification. Keep the existing 80/20 ratio and `random_state=42` convention.
- **Known, accepted dataset limitations** (documented, not fixed in v1.1): `seniority` has zero `stage` examples and only one `manager` example (merged away); `home_office_policy` has zero `remote` examples. The baseline report should state this explicitly so it doesn't read as a bug.
- **Feature pipeline**: TF-IDF vectorization on `intitule` and `description` — the only usable text columns (the cleaned data has no other categorical/engineered features). Fit on train only. Whether both target fields share one vectorizer or each gets its own `max_features` is **not assumed** — run the same cross-validation sweep independently per target and compare; only share the vectorizer if the sweep actually agrees.
- **Model**: `LogisticRegression`, one instance per target field. No comparison against other algorithms in v1.1 (that's a later exercise, not this one).
- **Hyperparameter tuning**: `C` and `class_weight` (including `'balanced'` as a candidate, given how skewed both targets are) tuned via the same method already validated for `max_features` — `StratifiedKFold` cross-validation on train only (no separate validation split, per the existing "too little data for a val set" reasoning), selected using the "best mean CV score minus one standard deviation" rule rather than raw argmax.
- **Baseline comparator**: a `DummyClassifier` (majority-class strategy) evaluated on the same test set, for each field, so the real classifier's metrics have a reference point.
- **Metrics**: macro F1 as the headline metric per field (so minority classes aren't masked by the dominant class), with per-class F1 reported alongside for detail — for both the real classifier and the dummy baseline.
- **Artifacts**: persist the fitted vectorizer(s) and both trained classifiers (e.g. via `joblib`), so v1.2 (MLflow) and v1.x (deployment) have something to load instead of retraining from scratch. Exact storage path is an implementation detail left for the ticket that builds this.
- **Code location**: training/evaluation logic lives as an importable module under `src/jobscope` (not only in a notebook) — following the existing pattern of `cleaning.py` / `annotation.py`. The exploratory notebook (`tf_idf_vectorizer.ipynb`) stays as-is, as the documented record of how `max_features` was first investigated — it is not the deliverable.
- **Proposed seam** (pending confirmation before implementation): one module exposing three public functions — `prepare_features(train_df, test_df)`, `train_classifier(X_train, y_train, target)`, `evaluate(model, X_test, y_test)` — reused for both the real classifier and the dummy baseline. One seam, not one per concern.

## Testing Decisions

- A good test here exercises the module's **public functions** with small, deterministic fixture data (a handful of rows covering both a majority and a minority class) and asserts on the shape/keys/values of the output (e.g. the metrics dict has the expected keys, macro F1 is a valid float in `[0, 1]`) — it does not assert on sklearn's internal computations.
- **Prior art in this repo**: `tests/test_cleaning.py` and `tests/test_schema.py` already follow this pattern — testing public function behavior against fixture inputs, not implementation internals. New tests for this module should follow the same shape.
- New fixtures will likely be needed (small synthetic labeled rows), since `tests/fixtures/job_posting_*.json` are schema-validation fixtures, not labeled training data.
- **Out of scope for automated tests**: whether the trained model is actually *good* (i.e. the macro F1 value itself). That's measured and reported, not asserted in a test — tests verify the pipeline runs correctly and returns well-formed output, not that the model has learned something useful.

## Out of Scope

- `contract_type` modeling — no real signal in the current data (deferred to v2, contingent on more diverse data).
- `salary_range` extraction and `skills` CRF extraction (both v2).
- Human-ceiling re-annotation study (v2).
- MLflow experiment tracking (v1.2).
- FastAPI/Docker deployment (v1.x).
- Comparing multiple algorithms (e.g. `LinearSVC`) or multiple modeling approaches (prompted LLM, fine-tuned LLM) — later, separate milestones.
- Publishing this spec, user stories, or tickets to the GitHub issue tracker — intentionally left to be written by hand, as a project-planning exercise.

## Further Notes

- `/setup-matt-pocock-skills` has not been run on this repo, so there is no configured issue-tracker/triage-label setup; this document was written as a local file for that reason, not published as a GitHub issue.
- Versioning convention adopted for the project going forward: `v1.1` → `v1.2` → `v1.x` → `v2`, each one a strictly incremental, independently shippable slice of the original 3-approach, full-schema vision.
