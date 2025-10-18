# utils/tables.py
from __future__ import annotations

import pandas as pd
from .formatting import fmt_pct


def _as_series_pct(values: list[float] | tuple[float, ...]) -> pd.Series:
    """Convert list of probabilities (0..1) into formatted percentage strings."""
    return pd.Series(values).apply(lambda x: fmt_pct(x))


def table_observations(
    call_prob_per_obs: list[float] | tuple[float, ...],
    coupon_prob_per_obs: list[float] | tuple[float, ...],
) -> pd.DataFrame:
    """
    Build a clean observations table with NO index column displayed.
    """
    n = max(len(call_prob_per_obs), len(coupon_prob_per_obs))
    df = pd.DataFrame({
        "Observation": range(1, n + 1),
        "P(Autocall)": _as_series_pct(call_prob_per_obs),
        "P(Coupon)": _as_series_pct(coupon_prob_per_obs),
    })
    return df.reset_index(drop=True)


def table_information(
    expected_duration_years: float,
    equivalent_zcb: float,
    forward_at_maturity: float,
    prob_capital_loss: float,
    prob_full_100: float,
) -> pd.DataFrame:
    """
    Information table with original labels; 'Forward at maturity' NOT in %.
    """
    rows = [
        ("Expected duration (years)", f"{expected_duration_years:.2f}"),
        ("Equivalent ZCB (per 100)", f"{equivalent_zcb:.2f}"),
        ("Forward at maturity", f"{forward_at_maturity:.2f}"),
        ("Prob. of capital loss", fmt_pct(prob_capital_loss)),
        ("Prob. of full redemption last year", fmt_pct(prob_full_100)),
    ]
    df = pd.DataFrame(rows, columns=["Metric", "Value"])
    return df.reset_index(drop=True)
