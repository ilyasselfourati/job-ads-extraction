# Sprint Log — v1.1: Classical ML Baseline

> One section per week. No deadlines — if a sprint spills into the next, that's information for the retro, not a failure. Fill in dates as you go; leave a sprint's review/retro blank until you actually close it out.

---

## Sprint 1 — Issue #25: Regenerate train/test split with joint stratification

**Dates:** 09/11/2026 to 15/11/2026

**Goal:** a `train.csv`/`test.csv` where both `seniority` and `home_office_policy` are proportionally represented in test.

**Planning notes:**
-

**Review** (run it, check what's actually done):
- [ ] `manager` merged into `confirme` before splitting
- [ ] New split stratified jointly on `seniority` × `home_office_policy`, 80/20, `random_state=42`
- [ ] Test set has a non-trivial number of `hybrid` examples
- [ ] Old split files overwritten, not left alongside

**Retro** (what slowed you down / what to change next sprint):
-

---

## Sprint 2 — Issue #26: Build the shared TF-IDF feature pipeline

**Dates:** _____ to _____

**Goal:** a tested `prepare_features` step; `max_features` chosen via CV independently per target, not assumed shared.

**Planning notes:**
-

**Review:**
- [ ] `prepare_features` fits vectorizer(s) on train only
- [ ] `max_features` chosen via CV, independently per target, "1 std below best" rule
- [ ] Shared vs. per-target vectorizer decided from CV results, not assumed
- [ ] Unit tests on fixture data, not sklearn internals

**Retro:**
-

---

## Sprint 3 — Issue #27: Train, evaluate, and persist the `seniority` baseline classifier

**Dates:** _____ to _____

**Goal:** a tuned `LogisticRegression` for `seniority`, beating (or not — that's data too) a `DummyClassifier` baseline, with results and artifacts saved.

**Planning notes:**
-

**Review:**
- [ ] `C`/`class_weight` tuned via CV on train only, same selection rule
- [ ] `DummyClassifier` baseline evaluated on the same test set
- [ ] Macro F1 + per-class F1 reported for both
- [ ] Vectorizer + classifier persisted to disk
- [ ] Unit tests on fixture data

**Retro:**
-

---

## Sprint 4 — Issue #28: Train, evaluate, and persist the `home_office_policy` baseline classifier

**Dates:** _____ to _____

**Goal:** same result as Sprint 3, for `home_office_policy` — reusing the training/evaluation code, not rebuilding it.

**Planning notes:**
-

**Review:**
- [ ] Reuses `train_classifier`/`evaluate` from #27, no duplicated logic
- [ ] `DummyClassifier` baseline + persistence, same as #27
- [ ] Unit tests on the `home_office_policy`-specific wiring

**Retro:**
-

---

## Sprint 5 — Issue #29: Write the v1.1 baseline metrics report

**Dates:** _____ to _____

**Goal:** one readable document someone could judge the baseline from, without opening the code.

**Planning notes:**
-

**Review:**
- [ ] Macro F1 + per-class F1 for both fields, model vs. dummy baseline, side by side
- [ ] States plainly that `stage`/`manager` and `remote` have no training examples
- [ ] States plainly why `contract_type` was excluded
- [ ] Readable standalone

**Retro:**
-

---

## v1.1 wrap-up

Once all 5 sprints are closed: a short look back at the whole slice — did the baseline beat the dummy classifiers? What would you do differently starting v1.2?

-
