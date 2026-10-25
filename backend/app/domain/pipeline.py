"""Stable backend seams for the pure deterministic analytical engine.

Loading, public schema validation, identities and atomic persistence remain
backend responsibilities. Persist prepare_evaluation()['context'] with results.
"""
from .engine import (run_evaluation, run_portfolio, prepare_evaluation,
                     calculate_rescue)

__all__ = ['run_evaluation', 'run_portfolio', 'prepare_evaluation', 'calculate_rescue']
