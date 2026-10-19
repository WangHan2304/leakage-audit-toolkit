# -*- coding: utf-8 -*-
"""Three cheap pre-modeling screens.

These are computed from a curated table alone (no model training) and predict
whether a process-parameter-only surrogate is worth building for a new alloy:

  screen 1  between_source_SS_fraction --- share of the target sum of squares
            that lies BETWEEN literature sources (high => the target is mostly
            a cross-study offset, not a process response).
  screen 2  duplicate-vector census --- fraction of rows that repeat a process
            vector already seen in the same source (the within-source noise
            floor).
  screen 3  corr_target_vs_ED --- Pearson correlation of the target with an
            energy-density feature; its sign and magnitude test whether the
            expected process->property physics is even present.

All three are recomputable from the released CSV by one script run each.
"""
import numpy as np
import pandas as pd


def between_source_ss(df, target_col, group_col='doi'):
    d = df.dropna(subset=[target_col, group_col])
    y = d[target_col].values.astype(float)
    gm = float(y.mean())
    sst = float(((y - gm) ** 2).sum())
    ssb = 0.0
    for _, g in d.groupby(group_col):
        v = g[target_col].values.astype(float)
        ssb += len(v) * (float(v.mean()) - gm) ** 2
    return round(ssb / sst, 4) if sst > 0 else None


def duplicate_vector_census(df, proc_cols, target_col=None,
                            group_col='doi'):
    cols = list(proc_cols) + ([target_col] if target_col else [])
    d = df.dropna(subset=cols + [group_col])
    grp = d.groupby(proc_cols)
    n_rep, n_grp = 0, 0
    for _, g in grp:
        if len(g) > 1:
            n_rep += len(g)
            n_grp += 1
    return {'rows_in_duplicate_groups': int(n_rep),
            'n_duplicate_groups': int(n_grp),
            'duplicate_row_fraction': round(n_rep / len(d), 4)
            if len(d) else None, 'n_rows': int(len(d))}


def corr_target_vs_feature(df, target_col, feature_col='energy_density_J_mm3'):
    d = df.dropna(subset=[target_col, feature_col])
    if len(d) < 3:
        return None
    return round(float(np.corrcoef(d[feature_col].values.astype(float),
                                   d[target_col].values.astype(float))[0, 1]), 4)


def run_all(df, target_col, proc_cols, group_col='doi',
            feature_col='energy_density_J_mm3'):
    return {
        'target_col': target_col,
        'between_source_SS_fraction': between_source_ss(df, target_col,
                                                        group_col),
        'duplicate_vector_census': duplicate_vector_census(
            df, proc_cols, target_col=target_col, group_col=group_col),
        'corr_target_vs_feature': corr_target_vs_feature(
            df, target_col, feature_col),
    }
