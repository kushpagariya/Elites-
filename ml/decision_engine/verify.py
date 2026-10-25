"""Current-stage gate; retains historical experiment tests/reports unchanged."""
import io
import json
from pathlib import Path
import tempfile
from time import perf_counter
import unittest
import warnings

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'ml/evaluation/decision_engine_v1'


def main():
    parent=(ROOT/'.runtime/decision-engine-tests').resolve()
    if not parent.is_relative_to(ROOT): raise ValueError('Unsafe test temporary directory')
    parent.mkdir(parents=True,exist_ok=True)
    tempfile.tempdir=str(parent)
    modules=['tests.unit.test_decision_engine','tests.unit.test_finance']
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in modules)
    output=io.StringIO();start=perf_counter()
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        result=unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
    record=dict(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
                seconds=perf_counter()-start,success=result.wasSuccessful(),output=output.getvalue(),
                warnings=sorted(set(str(w.message) for w in captured)),command='python -m ml.decision_engine.verify',
                modules=modules, historical_suite_status='Not rerun: historical B/B1/B2 preservation assertions bind their stage HEAD and pipeline stubs. These historical tests/reports remain unchanged; this is the current-stage gate.',
                api_contract_attempt='Additional unchanged tests.contract.test_scaffold run stalled and was interrupted; not counted as passed. No API/transport code was edited. HTTP integration remains a separate backend gate.',
                earlier_correction='Initial 33-check run exposed cumulative monotonicity diagnostic; corrected to detect total declines above INR1, then expanded independent full-network, model-boundary and artifact-restore checks.')
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'test_results.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print(output.getvalue())
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    raise SystemExit(main())
