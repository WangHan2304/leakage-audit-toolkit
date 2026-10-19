# -*- coding: utf-8 -*-
"""Leakage-audit toolkit --- material-agnostic data-integrity checks for
small-sample materials-ML regression corpora.

The five audits (A1--A5) and the three cheap screening statistics implemented
here are the same families used in the paper's three L-PBF case studies, but
they are written against a generic column contract so they run on any CSV of
process parameters + property labels + source (DOI) identifiers. No project-
specific module is imported; the only third-party requirements are numpy,
pandas and scikit-learn.

Public entry points
-------------------
audit_toolkit.checks   --- A1--A5 implementations
audit_toolkit.screens  --- three cheap pre-modeling screens
audit_toolkit.cli      --- command-line interface (python -m audit_toolkit)
"""
from . import checks, screens  # noqa: F401

__version__ = '0.1.0'
__all__ = ['checks', 'screens', '__version__']
