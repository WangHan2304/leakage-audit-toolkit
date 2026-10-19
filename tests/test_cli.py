# -*- coding: utf-8 -*-
"""End-to-end tests for the ``audit_toolkit`` command-line interface.

Uses only the repository-bundled ``examples/example_corpus.csv`` fixture; no
project data is read.
"""
import json
from pathlib import Path

from audit_toolkit import cli

EXAMPLE_CSV = str(Path(__file__).resolve().parents[1] / 'examples' /
                  'example_corpus.csv')


def _read(tmp_path, args):
    out = tmp_path / 'result.json'
    code = cli.main(args + ['--csv', EXAMPLE_CSV, '--out', str(out)])
    assert code == 0
    return json.loads(out.read_text(encoding='utf-8'))


def test_all_command_emits_five_audit_blocks(tmp_path):
    res = _read(tmp_path, ['all'])
    assert res['command'] == 'all'
    assert set(res['audits']) == {'a1', 'a2', 'a3', 'a4', 'a5'}
    assert res['csv_sha256'] and len(res['csv_sha256']) == 64
    assert 'toolkit_version' in res and 'generated_utc' in res


def test_single_audit_command(tmp_path):
    res = _read(tmp_path, ['a4'])
    assert set(res['audits']) == {'a4'}
    assert res['audits']['a4']['verdict'] == 'PASS'


def test_screens_command(tmp_path):
    res = _read(tmp_path, ['screens', '--target',
                           'ultimate_tensile_strength_MPa'])
    assert 'screens' in res
    assert 'between_source_SS_fraction' in res['screens']


def test_parser_defaults_and_choices():
    p = cli.build_parser()
    ns = p.parse_args(['all', '--csv', EXAMPLE_CSV])
    assert ns.command == 'all'
    assert ns.proc == cli.DEFAULT_PROC
    assert ns.tol == 0.05
