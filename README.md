# JobScope

**Structured information extraction from job postings — comparing classical ML, prompted LLMs, and fine-tuned LLMs on the same task.**

> ⚠️ **Status: in progress.** This README describes the intended scope. Results sections are placeholders until the corresponding milestone is complete. See the [roadmap](#roadmap) for what is actually done.

---

## The problem

A job posting is unstructured prose. Turning it into structured data — seniority, contract type, remote policy, required skills, salary range — is a deceptively hard extraction task: the vocabulary is inconsistent, key facts are often implied rather than stated, and the same concept appears in a dozen phrasings.

It is also a task where the "obvious" 2026 answer (throw an LLM at it) may well be the wrong engineering decision. That is what this project sets out to measure.

## The question

**When is a large language model actually worth it for structured extraction, and when is a linear model on TF-IDF features the better call?**

Three approaches are built against the same dataset, the same schema, and the same evaluation harness:

| Approach | Method | Annotation cost | Expected trade-off |
|---|---|---|---|
| **A. Classical ML** | TF-IDF + linear classifiers, one model per field; CRF for skill spans | High — every field needs labels | Fast and free at inference, blind to unseen vocabulary |
| **B. Prompted LLM** | Schema-constrained generation, validated with Pydantic | None | Zero setup, but latency and per-call cost |
| **C. Fine-tuned LLM** | LoRA adapter on a small open-weights model | Medium — reuses A's labels | The interesting middle ground |

The deliverable is not a demo. It is **a defensible comparison**, including the cases where the LLM loses.

## Evaluation

Accuracy alone would make this project useless. Every approach is scored on four axes:

- **Quality** — per-field F1, with a separate score for skill extraction (set-level precision/recall)
- **Latency** — p50 and p95 per posting
- **Cost** — euros per 1,000 postings, including amortized training
- **Data hunger** — quality as a function of the number of annotated examples

**Human ceiling.** Before any model is trained, 20 postings are re-annotated one week apart to measure annotator self-agreement. No model can meaningfully exceed this ceiling, and reporting a score without it is reporting a number without a scale. That figure will be published here.

## Data

- **Source:** publicly listed job postings, collected with rate limiting and `robots.txt` compliance
- **Volume:** ~500 postings, of which ~150 are hand-annotated
- **Language:** French
- **Schema:** defined as a Pydantic model in `src/schema.py`, with allowed values documented per field
- **Annotation guide:** `docs/annotation-guide.md` — decision rules plus adjudicated ambiguous cases

Raw postings are not redistributed. The repository ships the annotation layer and the collection scripts.

## Architecture

```
scraping → raw JSONL → annotation → train/val/test split
                                          │
                        ┌─────────────────┼─────────────────┐
                        ▼                 ▼                 ▼
                  classical ML      prompted LLM     fine-tuned LLM
                        └─────────────────┼─────────────────┘
                                          ▼
                              evaluation harness
                                          ▼
                         FastAPI service → Docker → CI/CD
                                          ▼
                            drift monitoring + MCP server
```

## Stack

**Modeling** — scikit-learn, sentence-transformers, PEFT/LoRA, Pydantic
**Serving** — FastAPI, Docker
**Ops** — MLflow, GitHub Actions, Evidently
**Integration** — MCP server exposing the corpus as callable tools

## Roadmap

| # | Milestone | Status |
|---|---|---|
| 1 | Dataset — schema, scraping, annotation guide, human ceiling | 🔨 In progress |
| 2 | Classical ML baseline | ⬜ Not started |
| 3 | Prompted LLM + evaluation harness | ⬜ Not started |
| 4 | LoRA fine-tuning | ⬜ Not started |
| 5 | FastAPI service, Docker, CI/CD | ⬜ Not started |
| 6 | Drift monitoring | ⬜ Not started |
| 7 | MCP server | ⬜ Not started |

Progress is tracked on the [project board](../../projects). Each milestone ships independently.

## Results

_Populated as milestones complete. Placeholder table below shows the intended reporting format._

| Approach | Macro F1 | Skills F1 | p95 latency | € / 1k postings |
|---|---|---|---|---|
| Human ceiling | — | — | — | — |
| A. Classical ML | — | — | — | — |
| B. Prompted LLM | — | — | — | — |
| C. Fine-tuned LLM | — | — | — | — |

## Getting started

```bash
git clone https://github.com/<user>/jobscope.git
cd jobscope
uv sync            # or: pip install -e ".[dev]"
pytest
```

Full usage documented once the API milestone lands.

## Repository layout

```
src/
  schema.py            # Pydantic extraction schema — the contract
  scraping/            # collection scripts
  models/              # A, B, C implementations behind a shared interface
  evaluation/          # metrics, harness, report generation
  api/                 # FastAPI service
  mcp/                 # MCP server
data/
  annotations/         # committed
  raw/                 # gitignored
docs/
  annotation-guide.md
notebooks/             # exploration only — nothing load-bearing
tests/
```

## Contributing

Conventions are documented in [CONTRIBUTING.md](CONTRIBUTING.md). Issues and discussion are welcome.

## License

MIT — see [LICENSE](LICENSE).
