# reframe-apolo

ReFrame test suite and performance-reproducibility research platform for the
**Apolo Scientific Computing Center** at Universidad EAFIT, covering the
**Apolo2** and **Apolo3** clusters.

The repository serves two missions from one codebase:

1. **Operational testing** — smoke checks, microbenchmarks and application
   sanity tests that run on a schedule, compare against learned thresholds, and
   alert when the clusters regress.
2. **Reproducibility research** — a campaign-driven experimental platform that
   runs HPL, HPCG and MLPerf across a controlled factorial space
   (compiler, flags, binding, BLAS/MPI, batch size) with repetition, captures
   per-run environment metadata, and produces statistical reports (mean, σ,
   coefficient of variation, confidence intervals, ANOVA) attributing
   performance variability to concrete factors.

The two share the tests and the site configurations; they do not share a driver.
Nightly runs must never block on a missing node, and a campaign must never
silently proceed with an unbalanced design — collapsing them would give one of
the two the wrong behavior.

> **Status:** scaffold. Directories are in place; implementation has not started.

---

## Repository structure

```
reframe-apolo/
├── pyproject.toml                 # installable package + `apolo-rfm` CLI + pinned deps
├── README.md
├── CITATION.cff                   # this is a research artifact; make it citable
│
├── src/apoloreframe/              # the "turn-key" layer ReFrame does not provide
│   ├── cli.py                     # apolo-rfm {plan,run,export,stats,report,refresh-refs}
│   ├── campaign/
│   │   ├── manifest.py            # parse + validate campaigns/*.yaml
│   │   └── driver.py              # expand factors → ReFrame invocations, run order, resume
│   ├── metadata/
│   │   ├── probe.sh               # runs ON THE ALLOCATED NODE, emits JSON
│   │   ├── collect.py             # normalize probe output
│   │   └── schema.py              # versioned run-record schema
│   ├── export/
│   │   ├── from_reframe.py        # sqlite / JSON reports → tidy long-format rows
│   │   └── writers.py             # json / csv
│   ├── stats/
│   │   ├── descriptive.py         # mean, sd, CV, t-CI, bootstrap-CI
│   │   ├── anova.py               # factor attribution
│   │   └── outliers.py            # flag anomalous runs before they poison a mean
│   ├── report/
│   │   ├── render.py
│   │   └── templates/
│   └── references/
│       ├── loader.py              # feed learned thresholds into tests at runtime
│       └── refresh.py             # recompute thresholds from stored results
│
├── rfm/                           # everything ReFrame reads
│   ├── settings/
│   │   ├── common.py              # shared environments, logging, sqlite storage
│   │   ├── apolo2.py              # partitions / environs / access for Apolo2
│   │   └── apolo3.py              # …for Apolo3
│   ├── lib/
│   │   ├── factors.py             # canonical factor vocabulary (single source of truth)
│   │   ├── mixins.py              # MetadataMixin, BindingMixin, RepeatMixin
│   │   └── bootstrap.py           # single import shim for tests
│   ├── tests/
│   │   ├── smoke/                 # partition reachability, ping — operational
│   │   ├── microbenchmarks/
│   │   │   ├── hpl/
│   │   │   ├── hpcg/
│   │   │   ├── stream/
│   │   │   └── osu/
│   │   ├── ml/
│   │   │   └── mlperf/            # the AI/ML benchmark (MLPerf)
│   │   └── apps/                  # center-specific application sanity tests
│   └── suites/
│       ├── lib.sh                 # shared Lmod/conda bootstrap
│       ├── nightly.sh
│       └── weekly.sh
│
├── campaigns/                     # experiments as versioned, reviewable artifacts
│   ├── 2026-07-pilot.yaml
│   ├── 2026-08-hpl-hpcg-main.yaml
│   └── 2026-09-ml-main.yaml
│
├── data/
│   ├── raw/<campaign-id>/         # immutable export, never edited
│   ├── processed/<campaign-id>/   # derived tables
│   └── README.md                  # schema + provenance
│
├── reports/<campaign-id>/         # generated; regenerable from data/raw + CLI
├── notebooks/                     # exploration only — nothing published from here
├── tests/                         # pytest for src/ (the statistics get real tests)
├── docs/
│   ├── install.md · settings.md · usage.md · adding-tests.md
│   ├── methodology.md             # experimental design — the paper's backbone
│   ├── data-schema.md
│   └── decisions/                 # short ADRs: why this factor, why this N
└── .github/workflows/
```

---

## Directory definitions

### `src/apoloreframe/` — the analysis and orchestration package

An installable Python package exposing the `apolo-rfm` CLI. ReFrame runs jobs;
this package is what turns those runs into an experiment. Every number that
reaches a report comes from here, so that reports are regenerable end-to-end
from `data/raw/` without manual steps.

| Subpackage | Purpose |
|---|---|
| `campaign/` | Parses and validates campaign manifests, expands the factorial cross-product, applies seeded run-order randomization, submits, and tracks progress so an interrupted campaign can resume. |
| `metadata/` | Captures the execution environment **on the allocated compute node** — CPU model, NUMA topology, kernel, compiler/MPI/BLAS versions, GPU driver/runtime, relevant environment variables — and normalizes it against a versioned schema. Login-node metadata would describe the wrong machine. |
| `export/` | Reads ReFrame's sqlite store and JSON reports and materializes tidy long-format JSON/CSV under `data/`. Single write path: ReFrame's store is the source of truth, everything else is derived. |
| `stats/` | Descriptive statistics (mean, σ, CV, confidence intervals) and factor attribution (ANOVA), plus outlier detection. Unit-tested against known inputs — CV and CI values that nobody has verified are not evidence. |
| `report/` | Renders comparative reports per campaign from the processed data. |
| `references/` | Learned performance thresholds for the operational side. `refresh.py` recomputes a ±kσ band per test/partition/metric from stored history; `loader.py` feeds it back into tests at `@run_before('performance')`, falling back to a hardcoded reference when no history exists. |

### `rfm/` — everything ReFrame reads

Named `rfm/`, not `reframe/`, deliberately. Python treats a directory without
`__init__.py` as a namespace package, so a top-level `reframe/` directory can
shadow the ReFrame framework itself whenever the repository root lands on
`sys.path` — which pytest, IDEs, and running scripts from the root all do.

| Subdirectory | Purpose |
|---|---|
| `settings/` | One ReFrame site configuration per cluster, sharing environments, logging and storage configuration through `common.py`. |
| `lib/` | Helpers imported by tests. `factors.py` is the single source of truth for what each factor level means and how it materializes into environment variables and `srun` flags — if `binding=close` means different things in HPL and HPCG, the ANOVA is meaningless. `mixins.py` holds the reusable test behaviors (metadata capture, binding, repetition). |
| `tests/` | ReFrame tests, split by intent: `smoke/` for reachability, `microbenchmarks/` for HPL/HPCG/STREAM/OSU, `ml/` for MLPerf, `apps/` for center-specific application sanity. Research factors are declared as native ReFrame `parameter()` builtins so ReFrame owns the cross-product and encodes it in `display_name` as `%binding=close %flags=O3`, which the statistics grouping keys on. |
| `suites/` | Shell runners for the operational mission — cron-driven nightly and weekly runs, parameterized by system so one script serves both clusters. |

### `campaigns/` — experiments as versioned artifacts

A campaign manifest is the unit of scientific work: a written, reviewed, frozen
statement of what will be measured and how, authored **before** the data exists.
It records the question and hypothesis, the factor space, the repetition
structure, and the run policy.

The manifest is read by the driver (to expand and submit), by the exporter (to
know which columns are factors, which are observed covariates, and which are
responses), and by the analysis (to get its model structure handed to it rather
than guessed from column names).

Repetition is declared in two distinct dimensions, because they measure
different variance components:

- `repeats.within_job` — repeats inside one allocation on the same nodes,
  capturing run-to-run noise (DVFS, turbo, interference).
- `repeats.across_jobs` — repeats in fresh allocations, capturing node-to-node
  and scheduler-placement variance.

Campaigns are immutable once they have produced data. A revised design is a new
manifest with `derived_from:` and a `changes:` note recording why the design
moved.

### `data/` — measurements

`raw/<campaign-id>/` holds the immutable export for one campaign: the frozen
`manifest.lock.yaml` (the manifest plus what the system actually resolved to at
submit time — module versions, repository SHA, ReFrame version), the ledger of
every attempted measurement and its outcome, and the measurements themselves.
Never edited after the fact.

`processed/<campaign-id>/` holds derived tables produced by the CLI from
`raw/`. Anything here can be deleted and regenerated.

The ledger matters as much as the measurements: if one factor level failed
disproportionately the design is unbalanced, and an unbalanced design silently
biases a naive ANOVA. Recording completion counts per configuration makes that
visible as a fact instead of a mean quietly computed over survivors.

### `reports/` — generated output

One directory per campaign, produced by `apolo-rfm report`. Generated, not
hand-written, so that the chain

```
campaigns/<id>.yaml → data/raw/<id>/ → data/processed/<id>/ → reports/<id>/
```

answers "which runs produced this figure?" by lookup rather than reconstruction.

### `notebooks/` — exploration only

Jupyter notebooks for exploratory analysis. Nothing published originates here.
Findings that survive exploration get reimplemented in `src/apoloreframe/stats/`
so they are tested and regenerable.

### `tests/` — pytest suite for the package

Unit tests for `src/apoloreframe/`, distinct from the ReFrame tests under
`rfm/tests/`. The statistics functions are the priority: a reproducibility
project cannot publish uncertainty estimates from unverified code.

### `docs/` — documentation

Operational guides (install, settings, usage, adding tests) alongside the
research documentation. `methodology.md` is the experimental design writeup and
the backbone of the final report; `data-schema.md` documents the run-record
schema so the dataset is usable by someone who did not build it;
`decisions/` holds short architecture decision records — why a factor was
included, why a given N was chosen.

### `.github/workflows/` — CI

Linting and the `tests/` pytest suite on pull requests. CI cannot run ReFrame
tests (no cluster), so it validates the package and the campaign manifests.
