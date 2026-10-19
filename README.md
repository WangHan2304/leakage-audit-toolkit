# Leakage-Audit Toolkit

Material-agnostic data-integrity checks for small-sample materials-ML
regression corpora. These are the five leakage audits (A1--A5) and the three
cheap pre-modeling screens used in the paper's three L-PBF case studies
(Ti-6Al-4V, 316L, Inconel 718), rewritten against a **generic column contract**
so they run on any CSV of process parameters + property labels + source (DOI)
identifiers. No project module is imported.

> Scope note. This tool is offered as a template that can be run on any
> small-sample materials ML task; its evidence base in the paper is three
> L-PBF, process-parameter-only corpora with n < 100 ground-truth rows.

## Install

No build step. The only requirements are numpy, pandas and scikit-learn:

```
pip install -r requirements.txt
```

Or install it as a package (editable) so the `audit-toolkit` console script and
the `audit_toolkit` import are on your path:

```
pip install -e .
```

Then run from this directory, or copy the `audit_toolkit/` package onto your
`PYTHONPATH`.

## Quick start

Run every audit on a corpus and write JSON:

```
python -m audit_toolkit all \
    --csv examples/example_corpus.csv \
    --targets ultimate_tensile_strength_MPa yield_strength_MPa elongation_percent \
    --proc laser_power_W scan_speed_mm_s layer_thickness_um hatch_spacing_um \
    --out audit_out.json
```

Run one audit, or the three screens for a single target:

```
python -m audit_toolkit a4 --csv corpus.csv --tol 0.05
python -m audit_toolkit screens --csv corpus.csv \
    --target ultimate_tensile_strength_MPa
```

An end-to-end example output is in `examples/example_audit_output.json`
(from `examples/example_corpus.csv`, a 12-row fixture that deliberately trips
A2 and A3). `examples/example_realrun_316l_all.json` is the `all` audit run
unchanged against the paper's real 316L corpus, kept as a worked reference.

## The checks

| id | name | what it catches |
|----|------|-----------------|
| A1 | source-disjoint grouped-CV contract | a grouped split that leaks a study across train/test |
| A2 | label-provenance decimal profile | generated labels (10--13 float decimals) written as if measured |
| A3 | DOI overlap matrix | augmentation rows sharing a study DOI with ground truth |
| A4 | near-duplicate process params | replicate measurements at (nearly) identical settings (noise floor) |
| A5 | source / publisher concentration | a corpus that looks diverse but is one dominant study |
| screens | between-source SS / duplicate census / target-ED correlation | whether a process-only surrogate is worth building at all |

Each returns a JSON object with a `verdict` in
`{PASS, PASS_WITH_DISCLOSURE, REVIEW}`.

## Column contract (CLI flags)

| flag | default | meaning |
|------|---------|---------|
| `--doi-col` | `doi` | per-row literature source id |
| `--tier-col` | `provenance_type` | row provenance tier (A3) |
| `--gt-tier` | `primary_paper` | which tier is ground truth (A3) |
| `--publisher-col` | `publisher` | publisher label (A5) |
| `--proc` | `laser_power_W scan_speed_mm_s layer_thickness_um hatch_spacing_um` | process columns (A4, screens) |
| `--targets` | the three tensile properties | label columns (A2, screens) |
| `--feature-col` | `energy_density_J_mm3` | ED feature (derived if absent and P/v/t/h present) |
| `--tol` | `0.05` | relative near-duplicate tolerance (A4) |

## Output

Every run records the input CSV `csv_sha256` and a UTC timestamp so results are
tied to an exact input. `screens` and `all` are pure functions of the CSV plus
the flags above, so two runs on the same bytes are identical.

## Running the tests

The suite needs only `pytest` and the bundled fixture (no project data):

```
pip install -e ".[test]"
pytest -q
```

It covers A1--A5 and the three screens against synthetic frames, plus an
end-to-end CLI run on `examples/example_corpus.csv`. `.github/workflows/ci.yml`
runs the same suite (plus a CLI smoke test) on Python 3.10/3.11/3.12.

## License

MIT (see `LICENSE`). The check code is MIT; the paper's data corpora are under
their own licenses and are not redistributed here.

## Citation

See `CITATION.cff`. The package is standalone-repo-ready; the GitHub push and
the Zenodo archive DOI are assigned at release --- follow `RELEASE_CHECKLIST.md`
(subtree-split this folder -> create the repo -> tag `v0.1.0` -> Zenodo DOI ->
backfill the DOI/owner fields in `CITATION.cff`). Until then the DOI/owner
values are clearly marked `REPLACE_AT_RELEASE`.
