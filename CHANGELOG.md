# Changelog

All notable changes to the leakage-audit toolkit are documented here.
The format follows Keep a Changelog; this project uses SemVer-ish tags.

## [0.1.0]

Initial standalone release, extracted from the paper's three L-PBF case
studies and rewritten against a generic column contract so the checks run on
any CSV of process parameters + property labels + source (DOI) identifiers.

### Added
- `audit_toolkit/checks.py` --- five leakage audits A1--A5:
  - A1 source-disjoint grouped-CV contract (GroupKFold holds out whole sources)
  - A2 label-provenance decimal profile (generated-label float artefacts)
  - A3 DOI overlap matrix (augmentation tier sharing a study with ground truth)
  - A4 near-duplicate process-parameter census (relative tolerance)
  - A5 source / publisher concentration summary
- `audit_toolkit/screens.py` --- three cheap pre-modeling screens:
  between-source sum-of-squares fraction, duplicate-vector census,
  target--energy-density correlation.
- `audit_toolkit/cli.py` --- `python -m audit_toolkit {a1..a5,all,screens}`
  with a configurable column contract; every run records the input CSV SHA-256
  and a UTC timestamp.
- `examples/` --- a worked example corpus and its JSON output.

### Notes
- Repository URL and Zenodo DOI are placeholders to be filled at publication.
- The check code is MIT; the paper's data corpora are NOT redistributed here.
