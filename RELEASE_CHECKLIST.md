# Release checklist — leakage-audit toolkit

Everything needed to publish `toolkit_release/` as a standalone, citable
open-source package is in place **except** the two actions only a human with
your GitHub/Zenodo account can perform: pushing the repository and minting the
archived DOI. This file is the runbook for those steps.

## What is already done (reviewer-runnable today, without the DOI)

- `pyproject.toml` — installable package, console script `audit-toolkit`,
  `pip install -e ".[test]"`.
- `audit_toolkit/` — A1–A5 (`checks.py`), three screens (`screens.py`),
  CLI (`cli.py`, `python -m audit_toolkit ...`) writing JSON + input `csv_sha256`.
- `tests/` — `pytest` suite (checks, screens, CLI end-to-end) using only the
  bundled `examples/example_corpus.csv` fixture.
- `.github/workflows/ci.yml` — runs `pytest` + a CLI smoke test on Python
  3.10/3.11/3.12 (becomes the standalone repo root `.github/` after the split).
- `LICENSE` (MIT), `README.md`, `requirements.txt`, `examples/`.

A reviewer can verify locally, right now:

```
cd toolkit_release
pip install -e ".[test]"
pytest -q
audit-toolkit all --csv examples/example_corpus.csv --out /tmp/audit.json
```

## Steps you perform to publish (owner/DOI fields)

1. **Split the folder into its own repo** (run from the project root):
   ```
   git subtree split -P toolkit_release -b audit-toolkit
   mkdir ../leakage-audit-toolkit && cd ../leakage-audit-toolkit
   git init && git pull ../<project> audit-toolkit
   ```
   (Alternatively: create an empty repo and push the split branch.)

2. **Create the GitHub repository** (e.g. `OWNER/leakage-audit-toolkit`) and
   push `main`. The `ci.yml` workflow starts running automatically.

3. **Fill the owner URL** in `CITATION.cff`
   (`repository-code: https://github.com/REPLACE_WITH_OWNER/...`) with the real
   `OWNER/repo`.

4. **Draft a release / tag** `v0.1.0` on GitHub.

5. **Mint the Zenodo DOI**: sign in with the same GitHub account, enable the
   repository on Zenodo, then "Release" the tag. Copy the assigned concept DOI.

6. **Backfill `CITATION.cff`**: set `date-released` to the release date and the
   `identifiers[0].value` to the Zenodo DOI (`10.5281/zenodo.NNNNNNN`); replace
   the `REPLACE_AT_RELEASE-ZENODO-DOI` placeholder. Also add the DOI badge +
   citation text to `README.md` ("Citing / Zenodo DOI").

7. Re-tag once so the archived snapshot carries the filled citation metadata.

## Fields still intentionally unresolved (need you)

- GitHub `OWNER/repo` string.
- Zenodo `date-released` and DOI (exist only after steps 4–5).

These are the only gaps between "standalone-repo-ready" and "published".
