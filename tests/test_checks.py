# -*- coding: utf-8 -*-
"""Unit tests for the A1--A5 leakage-audit checks.

Every test builds a small synthetic DataFrame against the generic column
contract; no project data and no `data/collected/` file is read.
"""
import pandas as pd

from audit_toolkit import checks

VERDICTS = {'PASS', 'PASS_WITH_DISCLOSURE', 'REVIEW'}


def _corpus():
    # 3 sources x 4 rows, all measured (few decimals), no DOI overlap beyond gt.
    return pd.DataFrame({
        'laser_power_W': [180.0] * 12,
        'scan_speed_mm_s': [800.0, 800.0, 900.0, 950.0] * 3,
        'layer_thickness_um': [30.0] * 12,
        'hatch_spacing_um': [90.0] * 12,
        'ultimate_tensile_strength_MPa': [612.5, 605.0, 640.0, 598.0] * 3,
        'doi': ['10.1/a'] * 4 + ['10.2/b'] * 4 + ['10.3/c'] * 4,
        'provenance_type': ['primary_paper'] * 12,
        'publisher': ['A', 'A', 'B', 'C'] * 3,
    })


def test_a1_is_source_disjoint_by_construction():
    res = checks.a1_source_disjoint_contract(_corpus(), doi_col='doi')
    assert res['verdict'] in VERDICTS
    assert res['n_sources'] == 3
    assert res['all_folds_source_disjoint'] is True
    assert res['example_violations'] == []


def test_a2_flags_generated_decimal_labels():
    df = _corpus()
    # one suspected generated label: 12 float decimals
    df.loc[0, 'ultimate_tensile_strength_MPa'] = 612.123456789012
    res = checks.a2_label_provenance_decimals(
        df, ['ultimate_tensile_strength_MPa'])
    assert res['verdict'] == 'REVIEW'
    assert 'ultimate_tensile_strength_MPa' in res['flagged_targets']


def test_a2_passes_clean_measured_labels():
    res = checks.a2_label_provenance_decimals(
        _corpus(), ['ultimate_tensile_strength_MPa'])
    assert res['verdict'] == 'PASS'
    assert res['flagged_targets'] == []


def test_a3_detects_augmentation_gt_doi_overlap():
    df = _corpus()
    df.loc[0:1, 'provenance_type'] = 'synthetic_augmentation'  # shares gt DOIs
    res = checks.a3_doi_overlap(df)
    assert res['verdict'] == 'PASS_WITH_DISCLOSURE'
    assert res['tiers_with_gt_overlap']


def test_a3_no_overlap_when_tiers_are_disjoint():
    df = _corpus()
    df['provenance_type'] = 'primary_paper'
    res = checks.a3_doi_overlap(df)
    assert res['verdict'] == 'PASS'
    assert res['tiers_with_gt_overlap'] == []


def test_a4_counts_near_duplicate_rows():
    res = checks.a4_near_duplicate_params(_corpus(), [
        'laser_power_W', 'scan_speed_mm_s', 'layer_thickness_um',
        'hatch_spacing_um'], tol=0.05)
    assert res['verdict'] == 'PASS'
    # first two rows of each source share the full 4-tuple -> duplicates exist
    assert res['n_rows_with_a_near_duplicate'] >= 1
    assert 0.0 < res['duplicate_row_fraction'] <= 1.0


def test_a5_reports_concentration():
    res = checks.a5_source_concentration(_corpus())
    assert res['verdict'] in VERDICTS
    assert res['n_sources'] == 3
    assert 0.0 < res['largest_source_share'] <= 1.0
    assert 'largest_publisher' in res


def test_a1_raises_when_only_one_source():
    """A1 must fail loudly on a single-source corpus (the BAM-style
    degenerate case), not silently return PASS. GroupKFold requires
    n_splits >= 2; a corpus collapsed to one DOI drives ``n`` to 1 and
    sklearn raises ValueError. This test is the intentional-leak toy
    example that prevents a future refactor from turning A1 permissive.
    """
    import pytest
    df = _corpus()
    df['doi'] = '10.0/only'  # collapse every row to a single source
    with pytest.raises(ValueError):
        checks.a1_source_disjoint_contract(df, doi_col='doi')


def test_all_registry_lists_five_audits():
    assert set(checks.ALL) == {'a1', 'a2', 'a3', 'a4', 'a5'}
