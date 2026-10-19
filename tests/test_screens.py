# -*- coding: utf-8 -*-
"""Unit tests for the three cheap pre-modeling screens."""
import pandas as pd

from audit_toolkit import screens

PROC = ['laser_power_W', 'scan_speed_mm_s', 'layer_thickness_um',
        'hatch_spacing_um']


def _corpus():
    # two sources whose means differ -> non-zero between-source SS; one
    # within-source duplicate process vector -> duplicate census > 0; a clean
    # ED/UTS covariation -> non-zero correlation.
    rows = []
    for doi, base in [('10.1/a', 500.0), ('10.2/b', 700.0)]:
        for speed, uts in [(800.0, base), (800.0, base + 5),
                           (1000.0, base + 40), (1200.0, base + 80)]:
            rows.append({
                'laser_power_W': 180.0,
                'scan_speed_mm_s': speed,
                'layer_thickness_um': 30.0,
                'hatch_spacing_um': 90.0,
                'ultimate_tensile_strength_MPa': uts,
                'energy_density_J_mm3': 180.0 / (speed * 30.0 * 90.0) * 1e6,
                'doi': doi,
            })
    return pd.DataFrame(rows)


def test_between_source_ss_in_unit_interval():
    v = screens.between_source_ss(_corpus(), 'ultimate_tensile_strength_MPa')
    assert v is not None and 0.0 <= v <= 1.0


def test_duplicate_vector_census_finds_repeats():
    c = screens.duplicate_vector_census(_corpus(), PROC, group_col='doi')
    assert c['n_duplicate_groups'] >= 1
    assert c['rows_in_duplicate_groups'] >= 2
    assert 0.0 < c['duplicate_row_fraction'] <= 1.0


def test_corr_target_vs_feature_is_float():
    c = screens.corr_target_vs_feature(
        _corpus(), 'ultimate_tensile_strength_MPa')
    assert isinstance(c, float) and -1.0 <= c <= 1.0


def test_corr_target_vs_feature_none_when_too_few_rows():
    tiny = _corpus().head(2)
    assert screens.corr_target_vs_feature(
        tiny, 'ultimate_tensile_strength_MPa') is None


def test_run_all_returns_three_screens():
    out = screens.run_all(_corpus(), 'ultimate_tensile_strength_MPa', PROC)
    assert set(out) == {'target_col', 'between_source_SS_fraction',
                        'duplicate_vector_census', 'corr_target_vs_feature'}
    assert out['target_col'] == 'ultimate_tensile_strength_MPa'
