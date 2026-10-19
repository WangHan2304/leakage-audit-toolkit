# -*- coding: utf-8 -*-
"""A1--A5 leakage-audit checks, written against a generic column contract.

Column contract (all configurable from the CLI)
-----------------------------------------------
doi_col      : per-row literature source identifier (str). Defaults 'doi'.
tier_col     : per-row provenance tier label (str) separating ground-truth
               rows from augmentation tiers. Defaults 'provenance_type'.
target_cols  : one or more property label columns to audit.
proc_cols    : the numeric process-parameter columns used for near-duplicate
               detection.

Each function returns a plain dict of JSON-serialisable scalars/lists plus a
'verdict' string in {PASS, PASS_WITH_DISCLOSURE, REVIEW}.
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold


# --------------------------------------------------------------- A1
def a1_source_disjoint_contract(df, doi_col='doi', n_splits=5):
    """Grouped-CV source-disjointness contract.

    A leakage-safe source-grouped evaluation must hold out whole sources: for
    every fold the set of sources in the test partition must be disjoint from
    the training partition. This is the fold-level guarantee behind the paper's
    strict-subset contract; here it is verified without needing a fitted
    regenerator so it runs on any corpus.
    """
    d = df.dropna(subset=[doi_col])
    groups = d[doi_col].astype(str).values
    n = min(int(n_splits), len(set(groups)))
    X = np.zeros((len(d), 1))
    ok = True
    violations = []
    for tr, te in GroupKFold(n_splits=n).split(X, groups=groups):
        inter = set(groups[tr]) & set(groups[te])
        if inter:
            ok = False
            violations.append(sorted(inter)[:5])
    return {
        'n_rows': int(len(d)), 'n_sources': int(len(set(groups))),
        'n_splits_used': int(n),
        'all_folds_source_disjoint': bool(ok),
        'example_violations': violations,
        'verdict': 'PASS' if ok else 'REVIEW',
    }


# --------------------------------------------------------------- A2
def _decimals(text):
    if '.' not in text:
        return 0
    frac = text.split('.')[-1]
    return len(frac.rstrip('')) if frac.isdigit() or frac == '' else len(frac)


def a2_label_provenance_decimals(df, target_cols, suspicious_ge=6):
    """Decimal-place profiling of label columns.

    A model fitted globally on all rows and used to (re)generate labels leaves
    float artefacts of ~10--13 significant decimals in the written CSV, whereas
    literature-measured values carry at most a couple. Any label with
    >= suspicious_ge decimals is flagged as a suspected generated value.
    """
    per = {}
    flagged = []
    for col in target_cols:
        s = pd.Series(df[col]).dropna().astype(str)
        decs = np.array([_decimals(t) for t in s]) if len(s) else np.array([])
        prof = {}
        for k in sorted(set(decs.tolist())):
            prof[int(k)] = int((decs == k).sum())
        susp = int((decs >= suspicious_ge).sum()) if decs.size else 0
        per[col] = {'n_labels': int(len(s)), 'decimal_profile': prof,
                    'n_ge_threshold': susp, 'threshold': suspicious_ge}
        if susp:
            flagged.append(col)
    return {
        'per_target': per, 'flagged_targets': flagged,
        'verdict': 'PASS' if not flagged else 'REVIEW',
    }


# --------------------------------------------------------------- A3
def a3_doi_overlap(df, doi_col='doi', tier_col='provenance_type',
                   gt_tier='primary_paper'):
    """DOI overlap matrix between the ground-truth tier and every other tier.

    A synthetic/augmentation row sharing a DOI with a ground-truth row is a
    potential same-study leakage path (the generator may have seen that study).
    """
    d = df.dropna(subset=[doi_col, tier_col])
    gt = set(d.loc[d[tier_col] == gt_tier, doi_col].astype(str))
    matrix = {}
    any_overlap = []
    for tier, sub in d.groupby(tier_col):
        s = set(sub[doi_col].astype(str))
        inter = sorted(gt & s) if tier != gt_tier else []
        matrix[str(tier)] = {'n_dois': len(s), 'overlap_with_gt': inter}
        if inter:
            any_overlap.append((str(tier), inter[:5]))
    return {
        'gt_tier': gt_tier, 'n_gt_dois': len(gt), 'tiers': matrix,
        'tiers_with_gt_overlap': any_overlap,
        'verdict': 'PASS' if not any_overlap else 'PASS_WITH_DISCLOSURE',
    }


# --------------------------------------------------------------- A4
def a4_near_duplicate_params(df, proc_cols, tol=0.05):
    """Near-duplicate process-vector census (symmetric relative tolerance).

    Two rows are near-duplicates if every process dimension is within `tol`
    relative. Within-source duplicates expose replicate measurements at (nearly)
    the same settings --- the noise floor a process-only model cannot beat.
    """
    d = df.dropna(subset=proc_cols)
    M = d[proc_cols].values.astype(float)
    n = len(M)
    rel = np.abs(M[:, None, :] - M[None, :, :]) / np.maximum(
        np.maximum(np.abs(M[:, None, :]), np.abs(M[None, :, :])), 1e-9)
    close = np.all(rel <= tol, axis=2)
    np.fill_diagonal(close, False)
    dup_rows = close.any(axis=1)
    return {
        'n_rows': int(n), 'tolerance': float(tol),
        'proc_cols': list(proc_cols),
        'n_rows_with_a_near_duplicate': int(dup_rows.sum()),
        'duplicate_row_fraction': round(float(dup_rows.mean()), 4)
        if n else None,
        'verdict': 'PASS',
    }


# --------------------------------------------------------------- A5
def a5_source_concentration(df, doi_col='doi', publisher_col='publisher'):
    """Source / publisher concentration summary.

    Reports the largest single-source share and the largest publisher share so
    that a corpus that only looks diverse at the publisher level but is actually
    one dominant study is visible.
    """
    d = df.dropna(subset=[doi_col])
    vc = d[doi_col].astype(str).value_counts()
    out = {
        'n_rows': int(len(d)), 'n_sources': int(len(vc)),
        'largest_source_doi': str(vc.index[0]) if len(vc) else None,
        'largest_source_share': round(float(vc.iloc[0] / len(d)), 4)
        if len(d) else None,
    }
    if publisher_col and publisher_col in d.columns:
        pv = d[publisher_col].dropna().astype(str).value_counts()
        out['n_publishers'] = int(len(pv))
        out['largest_publisher'] = str(pv.index[0]) if len(pv) else None
        out['largest_publisher_share'] = round(float(pv.iloc[0] / len(d)), 4)
    out['verdict'] = 'PASS' if (out['largest_source_share'] or 0) < 0.5 \
        else 'PASS_WITH_DISCLOSURE'
    return out


ALL = {
    'a1': ('source-disjoint grouped-CV contract', a1_source_disjoint_contract),
    'a2': ('label-provenance decimal profile', a2_label_provenance_decimals),
    'a3': ('DOI overlap matrix', a3_doi_overlap),
    'a4': ('near-duplicate process params', a4_near_duplicate_params),
    'a5': ('source/publisher concentration', a5_source_concentration),
}
