"""Pure finance building block; monetary inputs and outputs use INR."""

from dataclasses import dataclass
from math import isfinite
from typing import Sequence


@dataclass(frozen=True)
class FinanceResult:
    npv_inr: float
    horizon_roi: float | None
    payback_years: float | None


def evaluate_cashflows(
    capex_inr: float,
    annual_network_cashflows_inr: Sequence[float],
    discount_rate: float,
) -> FinanceResult:
    """Value end-of-year cash flows with time-zero CAPEX.

    ROI is a decimal fraction. Simple payback interpolates the first cumulative
    recovery, without discounting; null means no recovery within the horizon.
    Rent, COGS and displacement must already be counted exactly once upstream.
    """
    if not isfinite(capex_inr) or capex_inr < 0:
        raise ValueError("CAPEX must be finite and nonnegative")
    if not isfinite(discount_rate) or discount_rate <= -1:
        raise ValueError("Discount rate must be finite and greater than -1")
    flows = tuple(annual_network_cashflows_inr)
    if not flows or any(not isfinite(value) for value in flows):
        raise ValueError("At least one finite annual cash flow is required")

    npv = -capex_inr + sum(
        flow / (1 + discount_rate) ** year
        for year, flow in enumerate(flows, start=1)
    )
    roi = (sum(flows) - capex_inr) / capex_inr if capex_inr else None
    payback: float | None = 0.0 if capex_inr == 0 else None
    cumulative = 0.0
    for year, flow in enumerate(flows, start=1):
        previous = cumulative
        cumulative += flow
        if payback is None and previous < capex_inr <= cumulative and flow > 0:
            payback = (year - 1) + (capex_inr - previous) / flow
    return FinanceResult(npv_inr=npv, horizon_roi=roi, payback_years=payback)
