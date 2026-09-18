# Annotation guide

Decision rules for labeling job postings against the `JobPosting` schema (`src/jobscope/schema.py`), plus a running log of adjudicated ambiguous cases. This guide is the ground truth that both classical ML and LLM approaches are measured against — every rule here directly caps the "human ceiling" reported in the README, so precision matters more than speed.

> **Status:** rules locked (2026-09-18) — the three open decisions below are resolved. Two of them need a small follow-up in code before annotation starts; see [Follow-ups](#follow-ups-before-annotating).

## What the annotator sees

One JSON object per line, from `data/interim/france_travail_offers_clean.jsonl` (output of `jobscope.cleaning`). Cleaning only normalizes `intitule` and `description` (HTML stripped, whitespace collapsed) and drops exact-duplicate descriptions — every other field France Travail returns is passed through untouched, so each record mixes free text with structured metadata, e.g.:

```json
{
  "id": "...",
  "intitule": "Développeur Full stack .NET/ Angular Confirmé (H/F)",
  "description": "...",
  "typeContrat": "CDI",
  "typeContratLibelle": "Contrat à durée indéterminée",
  "experience": "2",
  "experienceLibelle": "Expérience exigée de 2 An(s)",
  "experienceExige": "E",
  "salaire": { "libelle": "Annuel de 40000,00 Euros à 45000,00 Euros" },
  "dureeTravailLibelle": "35H Horaires normaux",
  "lieuTravail": { "libelle": "75 - PARIS 8" }
}
```

## Ground rule: text first, structured fields second

**Label from `intitule` + `description`.** That's the only input any of the three extraction approaches (A/B/C) actually gets at inference time — the whole point of the project is extraction from prose, not from an API that has already done the work. Using France Travail's own structured fields (`typeContrat`, `experienceLibelle`, `salaire`, ...) as the gold label would silently make `contract_type` and part of `seniority` a solved problem before any model runs, and the comparison would stop meaning anything for those fields.

So:

1. Read `intitule` + `description` and label as if the structured fields did not exist.
2. If the text is genuinely silent on a field, you may use the matching structured field as a fallback (rules below say exactly when).
3. If the text and the structured field **disagree**, the text wins — but log it (see [Adjudication log](#adjudication-log)). A disagreement is a signal that the raw data may be wrong, or that a rule below needs revisiting, not something to average away.

## Field-by-field rules

### `seniority`

Values: `stage`, `junior`, `confirme`, `senior`, `lead`, `manager`.

Priority order — stop at the first that applies:

1. **Explicit title cue.** "Confirmé", "Senior", "Junior", "Lead", "Stagiaire" in `intitule` (as in the example above) wins outright.
2. **Explicit years in the description.** Map years to bucket: 0 → `junior` (unless the contract itself is `stage`, see rule 4), 1–2 → `junior`, 3–5 → `confirme`, 6–8 → `senior`, 9+ → `lead`.
3. **Management language**, regardless of years: the description names people-management duties (hiring, 1:1s, managing a team, "manager une équipe de N personnes") → `manager`. This overrides the years bucket — a manager with 3 years total experience is still `manager`, not `confirme`.
4. **Contract-type default.** `contract_type = stage` → `seniority = stage`. `contract_type = alternance` → `seniority = junior`, unless the text states otherwise.
5. **Fallback to `experienceLibelle`/`experienceExige`** only if 1–4 all come up empty. `experienceExige: "D"` (débutant) → `junior`; use the `experience` duration code (`0`/`1`/`2`/`3` years) against the same bucket table as rule 2.
6. **Still nothing:** default to `confirme` and flag the posting in the adjudication log — don't guess silently.

**Range wording ("profil junior à confirmé", "2 à 5 ans d'expérience"):** label the **lower bound**. The schema takes one value, and the lower bound is the actual minimum bar a candidate must clear to be a valid match — the safer of the two errors is under- rather than over-estimating seniority.

### `contract_type`

Values: `cdi`, `cdd`, `freelance`, `stage`, `alternance`.

1. Look for the explicit French term in the text: CDI, CDD, stage/stagiaire, alternance/apprentissage, freelance/indépendant/portage.
2. If absent from the text, fall back to `typeContratLibelle`, mapped as: "Contrat à durée indéterminée" → `cdi`, "Contrat à durée déterminée" → `cdd`, "Contrat d'apprentissage"/"Contrat de professionnalisation" → `alternance`.

**Unsupported contract types — decided: exclude.** France Travail's `typeContrat` referential includes codes with no home in this schema — `MIS` (intérim/mission), `SAI` (saisonnier), `LIB` (profession libérale), among others. Do not force these onto the nearest enum value (e.g. mapping intérim to `cdd`) — that would corrupt the label, not fill a gap. **These postings are dropped from the corpus entirely**, not just from the annotation sheet: `jobscope.cleaning` should filter them out during the clean/dedup pass and log a count of how many were excluded and why (see [Follow-ups](#follow-ups-before-annotating)). Until that filter exists, mark such postings `EXCLUDE — unsupported contract type` by hand and skip them.

### `home_office_policy`

Values: `on_site`, `hybrid`, `remote`.

1. "100% télétravail", "full remote", "télétravail total" → `remote`.
2. Any partial mention — "N jours de télétravail/semaine", "télétravail possible", "hybride" → `hybrid`.
3. No mention of télétravail/remote anywhere in the text → `on_site` **by default**.

**Decided: keep the default, verify later.** Rule 3 is an assumption, not an observation — silence most likely means on-site in this market, but that's not verified against the actual corpus. Rather than block annotation on it, apply it as-is now, and re-check it as a checkpoint once ~50 postings are annotated: pull the same kind of counts as `corpus_statistics.ipynb` on the annotated subset and confirm `on_site`-by-default isn't systematically wrong. If it is, this rule (and the postings already annotated under it) gets revisited then — not before.

### `salary_range`

`{min_salary, max_salary, salary_period}` — `salary_period` is `"annual"` or `"daily"`, `min_salary`/`max_salary` are whole euros in that period, and the whole object is `null` if the posting states no figure at all. Do not estimate a market-rate salary when it isn't given.

> **Schema change needed:** this assumes `SalaryRange` gains a `salary_period: Literal["annual", "daily"] | None` field — see [Follow-ups](#follow-ups-before-annotating). Until the schema is updated, record the period in the `notes` column of the annotation sheet instead of a real field.

1. Take the range from the description if it states one explicitly.
2. If the description is silent but `salaire.libelle` has a parseable range, use it as fallback — this field is often genuinely free text ("Annuel de 40000,00 Euros à 45000,00 Euros", but also "Selon profil" or "A négocier", which are not usable and stay `null`).
3. **For `cdi`/`cdd`/`stage`/`alternance` postings:** normalize to annual gross EUR, `salary_period = "annual"`. A monthly figure ×12; an hourly figure needs the `dureeTravailLibelle` weekly-hours figure to annualize — if that's missing, leave the whole `salary_range` `null` rather than guessing a full-time assumption.
4. **For `freelance` postings:** the figure is a daily rate (TJM), not annual. Record it as-is with `salary_period = "daily"` — do **not** multiply it into a fake annual figure. This resolves the earlier ambiguity where a freelance `min_salary: 400` was indistinguishable from a CDI's 400.

### `skills`

Free-form list of strings, e.g. `["python", "fastapi", "docker", "kubernetes"]`.

1. Lowercase, canonical spelling (`"Kubernetes"` → `kubernetes`, `"Python3"` → `python`).
2. Include: programming languages, frameworks/libraries, tools/platforms, and named methodologies (`scrum`, `ci/cd`) when the posting names them explicitly as a requirement or a plus.
3. Exclude: soft skills ("esprit d'équipe", "autonomie") and generic non-technical requirements ("permis B", "anglais courant") — those aren't part of this schema.
4. One canonical entry per skill, no duplicates, no versions unless the posting specifically requires one (`python 3.11` only if the text calls out that version as a hard requirement, otherwise just `python`).
5. Order: as they appear in the text, not alphabetized — preserves which ones were emphasized first, which is a genuinely observed signal, not a stylistic choice.

## General principles

- **One annotator per posting for the first pass.** Escalation only when a case doesn't fit any rule above — don't quietly resolve it your own way and move on.
- **Never infer past what the text (or, per the fallback rules, the structured metadata) actually supports.** No modeling of "postings like this one usually pay X."
- **Every rule exception gets a row in the adjudication log below**, including the ones you're sure about — the log is what makes the guide reproducible for issue #8's human-ceiling measurement (20 postings re-annotated a week apart need to hit the same calls, not just the same instincts).

## Adjudication log

Format: `[date] posting id — field — question — decision — rationale`. Two illustrative entries to show the format (replace with real cases as annotation starts):

| Date | Posting | Field | Question | Decision | Rationale |
|---|---|---|---|---|---|
| _(example)_ | fixture: `job_posting_full` | `seniority` | Title says "Confirmé", no years stated | `confirme` | Rule 1 (title cue) — no need to reach for rule 2 |
| _(example)_ | fixture: `job_posting_partial_salary` | `salary_range` | `freelance`, single figure `400`, no currency/period stated | `{min: 400, max: null, salary_period: "daily"}` | Freelance rule (§ `salary_range`, rule 4) — TJM, not annualized |
