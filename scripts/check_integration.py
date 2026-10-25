"""Supported application acceptance suite; historical training audits are separate."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
MODULES = ('tests.unit.test_finance', 'tests.unit.test_decision_engine',
           'tests.unit.test_rescue_handoff', 'tests.contract.test_integration',
           'tests.contract.test_scaffold', 'tests.contract.test_auth')
if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromNames(MODULES))
    raise SystemExit(0 if result.wasSuccessful() else 1)
