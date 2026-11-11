# Tickets — v1.1: Classical ML Baseline

> Tracer-bullet breakdown of `spec.md`, in dependency order (blockers first). Local reference only — not published to the issue tracker; copy these into GitHub issues by hand when you start each one.

---

## 01: Regenerate train/test split with joint stratification

**What to build:** A regenerated `train.csv`/`test.csv` where both `seniority` and `home_office_policy` are proportionally represented in the test set — not just `seniority`, as the current split does.

**Blocked by:** None (can start immediately)

- [ ] The single `manager` value in `seniority` is merged into `confirme` before splitting (reuse the existing `replace_column_with_less_than_1_occurrence` logic from `split_train_test.ipynb`)
- [ ] `train.csv`/`test.csv` are regenerated with an 80/20 split stratified on a combined `seniority` × `home_office_policy` key, `random_state=42`
- [ ] The new test set contains a non-trivial number of `hybrid` examples (previous split left only 2)
- [ ] Old `train.csv`/`test.csv` are overwritten/superseded, not left alongside the new ones

---

## 02: Build the shared TF-IDF feature pipeline

**What to build:** A reusable, tested feature-preparation step that turns `intitule` + `description` text into TF-IDF features for both target fields, without assuming one `max_features` choice fits both.

**Blocked by:** 01

- [ ] A `prepare_features` function fits TF-IDF vectorizer(s) on train only (`intitule`, `description`)
- [ ] `max_features` is chosen via `StratifiedKFold` cross-validation, independently for `seniority` and `home_office_policy`, using the "best mean CV score minus 1 std" rule already validated in `tf_idf_vectorizer.ipynb`
- [ ] If both targets land on the same effective `max_features`, one shared vectorizer is used; otherwise each target gets its own — decided from the CV results, not assumed upfront
- [ ] Unit tests exercise `prepare_features` against small fixture data, asserting on output shape/type — not on sklearn's internal computations

---

## 03: Train, evaluate, and persist the `seniority` baseline classifier

**What to build:** A tuned, evaluated, saved `LogisticRegression` model for `seniority`, compared against a trivial baseline so its metrics mean something.

**Blocked by:** 02

- [ ] `train_classifier` tunes `C` and `class_weight` (including `'balanced'`) via CV on train only, same selection rule as ticket 02
- [ ] A `DummyClassifier` (most-frequent strategy) is evaluated on the same test set, for comparison
- [ ] `evaluate` reports macro F1 and per-class F1 for both the real classifier and the dummy baseline
- [ ] The fitted vectorizer and trained classifier are persisted to disk (e.g. via `joblib`)
- [ ] Unit tests cover `train_classifier`/`evaluate` against fixture data, following the pattern in `tests/test_cleaning.py`

---

## 04: Train, evaluate, and persist the `home_office_policy` baseline classifier

**What to build:** The same end-to-end result as ticket 03, for `home_office_policy` — reusing the training/evaluation code rather than re-deriving it.

**Blocked by:** 02, 03 (reuses the `train_classifier`/`evaluate` functions ticket 03 introduces)

- [ ] Reuses `train_classifier`/`evaluate` from ticket 03, applied to `home_office_policy` — no duplicated logic
- [ ] Same `DummyClassifier` comparison and artifact persistence as ticket 03
- [ ] Unit tests cover the `home_office_policy`-specific wiring (fixture data, expected output shape)

---

## 05: Write the v1.1 baseline metrics report

**What to build:** A single readable document presenting both fields' results, so someone who only read `spec.md` can judge whether the baseline is worth anything — without reading the code.

**Blocked by:** 03, 04

- [ ] Presents macro F1 + per-class F1 for both fields, model vs. dummy baseline, side by side
- [ ] States explicitly that `stage`/`manager` (`seniority`) and `remote` (`home_office_policy`) have no training examples and cannot realistically be predicted
- [ ] States explicitly that `contract_type` was excluded from v1.1, and why (99/100 examples are `cdi`)
- [ ] Readable on its own — no need to open the training code to understand the result
