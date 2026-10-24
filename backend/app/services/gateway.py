"""Bound concurrency; timed-out workers retain their slot until they finish."""
import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import BoundedSemaphore

from ..domain import pipeline
from .errors import ServiceError

_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="storescout-domain")
_slots = BoundedSemaphore(2)
logger = logging.getLogger(__name__)


def invoke(name, *args):
    function = getattr(pipeline, name, None)
    if not callable(function):
        raise ServiceError(503, "ENGINE_UNAVAILABLE", f"{name} is not connected to the analytical engine.")
    try:
        timeout = float(os.getenv("STORESCOUT_COMPUTE_TIMEOUT_SECONDS", "15"))
        if not 0 < timeout <= 120:
            raise ValueError("Invalid timeout")
    except ValueError as exc:
        raise ServiceError(503, "CONFIGURATION_ERROR", "Compute timeout must be greater than zero and at most 120 seconds.") from exc
    if not _slots.acquire(blocking=False):
        raise ServiceError(503, "ENGINE_BUSY", "Analytical workers are busy; retry after the active calculation finishes.")
    try:
        future = _pool.submit(function, *args)
    except Exception:
        _slots.release()
        raise
    future.add_done_callback(lambda _: _slots.release())
    try:
        return future.result(timeout=timeout)
    except NotImplementedError as exc:
        raise ServiceError(503, "ENGINE_UNAVAILABLE", f"{name} awaits the ML/logic implementation; no result was saved.") from exc
    except TimeoutError as exc:
        raise ServiceError(503, "ENGINE_TIMEOUT", "Calculation exceeded its time limit; no result was saved.") from exc
    except ServiceError:
        raise
    except Exception as exc:
        logger.exception("Domain calculation failed: %s", name)
        raise ServiceError(503, "COMPUTATION_FAILED", "The analytical calculation failed; no result was saved.") from exc
