# -*- coding: utf-8 -*-
"""Command-line interface for the leakage-audit toolkit.

Examples
--------
Run every audit on a corpus and dump JSON:

    python -m audit_toolkit all \
        --csv lpbf_316l_benchmark.csv \
        --targets ultimate_tensile_strength_MPa yield_strength_MPa \
        --proc laser_power_W scan_speed_mm_s layer_thickness_um hatch_spacing_um \
        --out audit_316l.json

Run a single audit, or the three cheap screens for one target:

    python -m audit_toolkit a4 --csv corpus.csv --proc P v t h --tol 0.05
    python -m audit_toolkit screens --csv corpus.csv \
        --target ultimate_tensile_strength_MPa --proc P v t h

Column names are all configurable; defaults match the paper's three corpora.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import checks, screens, __version__

DEFAULT_PROC = ['laser_power_W', 'scan_speed_mm_s', 'layer_thickness_um',
                'hatch_spacing_um']


def _ensure_ed(df, feature_col, proc_cols):
    """Derive an energy-density feature if absent and P/v/t/h are present."""
    if feature_col in df.columns:
        return df
    need = {'laser_power_W', 'scan_speed_mm_s', 'layer_thickness_um',
            'hatch_spacing_um'}
    if need.issubset(set(df.columns)):
        df = df.copy()
        df[feature_col] = (df['laser_power_W'] /
                           (df['scan_speed_mm_s'] * df['layer_thickness_um'] *
                            df['hatch_spacing_um']) * 1e6)
    return df


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_parser():
    p = argparse.ArgumentParser(prog='audit_toolkit', description=__doc__)
    p.add_argument('command',
                   choices=['a1', 'a2', 'a3', 'a4', 'a5', 'all', 'screens'])
    p.add_argument('--csv', required=True, help='input corpus CSV')
    p.add_argument('--targets', nargs='*',
                   default=['ultimate_tensile_strength_MPa',
                            'yield_strength_MPa', 'elongation_percent'])
    p.add_argument('--target', default=None,
                   help='single target column (screens command)')
    p.add_argument('--proc', nargs='*', default=DEFAULT_PROC)
    p.add_argument('--doi-col', default='doi')
    p.add_argument('--tier-col', default='provenance_type')
    p.add_argument('--gt-tier', default='primary_paper')
    p.add_argument('--publisher-col', default='publisher')
    p.add_argument('--tol', type=float, default=0.05)
    p.add_argument('--feature-col', default='energy_density_J_mm3')
    p.add_argument('--out', default=None, help='write JSON here (default: '
                                               'stdout)')
    p.add_argument('--version', action='version',
                   version='audit_toolkit ' + __version__)
    return p


def run(args):
    df = pd.read_csv(args.csv)
    df = _ensure_ed(df, args.feature_col, args.proc)
    result = {'toolkit_version': __version__,
              'generated_utc': datetime.now(timezone.utc).isoformat(
                  timespec='seconds'),
              'csv': str(args.csv), 'csv_sha256': _sha256(args.csv),
              'command': args.command}
    if args.command == 'screens':
        tgt = args.target or args.targets[0]
        result['screens'] = screens.run_all(
            df, tgt, args.proc, group_col=args.doi_col,
            feature_col=args.feature_col)
    else:
        audit_ids = list(checks.ALL) if args.command == 'all' else [
            args.command]
        res = {}
        for aid in audit_ids:
            if aid == 'a1':
                res['a1'] = checks.a1_source_disjoint_contract(
                    df, doi_col=args.doi_col)
            elif aid == 'a2':
                res['a2'] = checks.a2_label_provenance_decimals(
                    df, args.targets)
            elif aid == 'a3':
                res['a3'] = checks.a3_doi_overlap(
                    df, doi_col=args.doi_col, tier_col=args.tier_col,
                    gt_tier=args.gt_tier)
            elif aid == 'a4':
                res['a4'] = checks.a4_near_duplicate_params(
                    df, args.proc, tol=args.tol)
            elif aid == 'a5':
                res['a5'] = checks.a5_source_concentration(
                    df, doi_col=args.doi_col, publisher_col=args.publisher_col)
        result['audits'] = res
    return result


def main(argv=None):
    args = build_parser().parse_args(argv)
    result = run(args)
    text = json.dumps(result, ensure_ascii=False, indent=2,
                      default=_json_default)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
        print('wrote %s' % args.out, file=sys.stderr)
    else:
        print(text)
    return 0


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError('unserialisable %r' % type(o))


if __name__ == '__main__':
    raise SystemExit(main())
