# utils/pricing.py
from __future__ import annotations
import math
import numpy as np
from typing import List
from .types import ProductInputs, MarketInputs

# ---------- Schedules ----------
def observations_per_year(freq: str) -> int:
    return {"annual": 1, "semi-annual": 2, "quarterly": 4, "monthly": 12}[freq]

def build_obs_steps(maturity_years: float, steps_per_year: int, freq: str) -> List[int]:
    obs_per_y = observations_per_year(freq)
    obs_steps = []
    for y in range(1, int(math.ceil(maturity_years * obs_per_y)) + 1):
        t_years = y / obs_per_y
        step_index = int(round(t_years * steps_per_year))
        obs_steps.append(step_index)
    # Clamp to the grid end
    max_step = int(round(maturity_years * steps_per_year))
    obs_steps = [min(s, max_step) for s in obs_steps]
    return obs_steps

# ---------- Core MC ----------
def price_autocall_mc(
    prod: ProductInputs,
    mkt: MarketInputs,
    n_paths: int = 10000,
    steps_per_year: int = 252,
    seed: int | None = None,
):
    """
    Autocall MC pricer with:
      - Autocall at observation j if S >= autocall barrier
      - Coupons:
          * memory_feature=True: coupons sum over obs where S >= coupon barrier (and while alive)
          * memory_feature=False: if called at obs j -> pays j periods of coupon; if to maturity -> pays 1 coupon if S_T >= coupon barrier else 0
      - DIP:
          * American: if path crosses DIP barrier anytime, final payoff may be reduced
          * European: only S_T compared to DIP strike
      - Loss leg at maturity (if dipped): min(100, 100 * S_T / DIP_STRIKE)
    """
    # Unpack
    T = float(prod.maturity_years)
    obs_freq = prod.obs_frequency
    obs_per_y = observations_per_year(obs_freq)

    s0 = float(mkt.stock_price)
    r  = float(mkt.interest_rate)
    q  = float(mkt.dividend_yield)
    vol = float(mkt.volatility)

    ac_bar   = prod.autocall_barrier_pct / 100.0 * s0
    coup_bar = prod.coupon_barrier_pct / 100.0 * s0
    dip_bar  = prod.dip_barrier_pct / 100.0 * s0
    dip_strk = prod.dip_strike_pct / 100.0 * s0
    coupon   = prod.annual_coupon_pct / 100.0

    # Grid
    n_steps = int(round(T * steps_per_year))
    dt = T / max(1, n_steps)
    t_grid = np.linspace(0.0, T, n_steps + 1)

    # RNG
    rng = np.random.default_rng(seed)

    # Simulate GBM paths (log-Euler with exact variance)
    z = rng.standard_normal(size=(n_paths, n_steps))
    drift = (r - q - 0.5 * vol * vol) * dt
    diff  = vol * math.sqrt(dt)

    x0 = math.log(max(1e-12, s0))
    x = np.full((n_paths, n_steps + 1), x0, dtype=float)
    for i in range(1, n_steps + 1):
        x[:, i] = x[:, i-1] + drift + diff * z[:, i-1]
    paths = np.exp(x)

    # DIP monitoring
    if prod.dip_style.lower().startswith("amer"):
        min_along = np.min(paths, axis=1)
        dipped = (min_along < dip_bar)
    else:  # European
        dipped = (paths[:, -1] < dip_bar)

    # Observation steps
    obs_steps = build_obs_steps(T, steps_per_year, obs_freq)

    # Autocall / coupons (memory per path)
    payoffs = np.zeros(n_paths, dtype=float)
    pay_times = np.zeros(n_paths, dtype=float)
    call_obs_index = np.full(n_paths, -1, dtype=int)
    coupon_paid_flags = np.zeros((n_paths, len(obs_steps)), dtype=int)

    for j, step in enumerate(obs_steps, start=1):
        s = paths[:, step]

        # --- FIX: coupon probability conditional on survival (alive_before) ---
        alive_before = (call_obs_index < 0)
        eligible_coupon = ((s >= coup_bar) & alive_before).astype(int)
        coupon_paid_flags[:, j - 1] = eligible_coupon

        # Autocall check (only if still alive)
        call_mask = (s >= ac_bar) & (call_obs_index < 0)
        if not np.any(call_mask):
            continue

        call_obs_index[call_mask] = j
        years_elapsed = j / obs_per_y

        # Payoff when called
        if prod.memory_feature:
            coupons_to_pay = coupon_paid_flags[call_mask, :j].sum(axis=1).astype(float)
        else:
            coupons_to_pay = np.full(call_mask.sum(), years_elapsed, dtype=float)

        payoffs[call_mask] = 100.0 + 100.0 * coupon * coupons_to_pay
        pay_times[call_mask] = years_elapsed

    # Not called: payoff at maturity with DIP
    not_called = (call_obs_index < 0)
    if np.any(not_called):
        sT = paths[not_called, -1]
        if prod.memory_feature:
            coupons_to_pay = coupon_paid_flags[not_called, :].sum(axis=1)
        else:
            coupons_to_pay = (sT >= coup_bar).astype(int)

        payoff_no_dip = 100.0 + 100.0 * coupon * coupons_to_pay

        # Loss leg at maturity if dipped
        loss_leg = np.where(sT < dip_strk, 100.0 * (sT / dip_strk), 100.0)
        payoff_final = np.where(dipped[not_called], np.minimum(100.0, loss_leg), 100.0)

        payoffs[not_called] = np.minimum(payoff_no_dip, payoff_final)
        pay_times[not_called] = T

    # Discounting
    discounts = np.exp(-r * pay_times)
    pv_contrib = payoffs * discounts
    pv = float(pv_contrib.mean())

    # Diagnostics
    call_probs = [float(np.mean(call_obs_index == j)) for j in range(1, len(obs_steps) + 1)]
    coupon_prob_per_obs = list(np.mean(coupon_paid_flags, axis=0)) if len(obs_steps) > 0 else []
    prob_maturity = float(np.mean(call_obs_index < 0))
    prob_capital_loss = float(np.mean(payoffs < 100.0))
    eem = float(pay_times.mean())
    std = float(pv_contrib.std(ddof=1))
    ci95 = 1.96 * std / math.sqrt(n_paths)
    forward_at_maturity = s0 * math.exp((r - q) * T)
    zcb_equiv = 100.0 * math.exp(-r * eem)

    diagnostics = {
        "call_prob_per_obs": call_probs,
        "coupon_prob_per_obs": coupon_prob_per_obs,  # now conditional on survival
        "prob_maturity": prob_maturity,
        "prob_capital_loss": prob_capital_loss,
        "expected_duration_years": eem,
        "pv_contrib_samples": pv_contrib,
        "payoff_samples": payoffs,
        "ci95_low": pv - ci95,
        "ci95_high": pv + ci95,
        "forward_at_maturity": forward_at_maturity,
        "equivalent_zcb": zcb_equiv,
    }
    return pv, diagnostics



