from __future__ import annotations
import datetime as dt
from dataclasses import dataclass
from typing import Literal, List
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ------------------ Types ------------------
FreqLaunch = Literal["Weekly", "Monthly", "Quarterly", "Yearly"]
ObsFreq = Literal["annual", "semi-annual", "quarterly", "monthly"]

# ------------------ Spec produit ------------------
@dataclass
class ProductSpec:
    maturity_years: float
    obs_frequency: ObsFreq
    autocall_barrier: float
    coupon_barrier: float
    dip_barrier: float
    annual_coupon: float
    memory_feature: bool

# ------------------ Utils ------------------
def _obs_per_year(freq: ObsFreq) -> int:
    return {"annual": 1, "semi-annual": 2, "quarterly": 4, "monthly": 12}[freq]

def _gen_launch_dates(prices: pd.Series, years: int, freq: FreqLaunch, maturity_years: float) -> List[pd.Timestamp]:
    end = prices.index[-1].normalize()
    start = end - pd.DateOffset(years=years)
    px = prices.loc[start:end].dropna()
    if freq == "Weekly":
        anchors = px.resample("W-FRI").last().index
    elif freq == "Monthly":
        anchors = px.resample("M").last().index
    elif freq == "Quarterly":
        anchors = px.resample("Q").last().index
    else:
        anchors = px.resample("Y").last().index
    good = []
    for d in anchors:
        maturity_date = d + pd.DateOffset(years=maturity_years)
        if maturity_date <= prices.index[-1]:
            if d in prices.index:
                good.append(d)
            else:
                nxt = prices.index[prices.index.searchsorted(d)]
                if nxt + pd.DateOffset(years=maturity_years) <= prices.index[-1]:
                    good.append(nxt)
    return good

def _build_observation_dates(launch: pd.Timestamp, freq: ObsFreq, maturity_years: float, prices_index: pd.DatetimeIndex) -> List[pd.Timestamp]:
    n_per_year = _obs_per_year(freq)
    n_obs = int(round(maturity_years * n_per_year))
    obs = []
    for k in range(1, n_obs + 1):
        target = launch + pd.DateOffset(months=int(12 * k / n_per_year))
        if target in prices_index:
            obs.append(target)
        else:
            pos = prices_index.searchsorted(target)
            if pos >= len(prices_index):
                obs.append(prices_index[-1])
            else:
                obs.append(prices_index[pos])
    return obs

# ------------------ Evaluation ------------------
def _evaluate_autocall_path(prices: pd.Series, launch: pd.Timestamp, spec: ProductSpec) -> dict:
    s0 = float(prices.loc[launch])
    obs_dates = _build_observation_dates(launch, spec.obs_frequency, spec.maturity_years, prices.index)
    px = prices.loc[launch: obs_dates[-1]].copy()
    ss = (px / s0).reindex(px.index).ffill()

    coupon_paid, coupons_count, memory_accrual = 0.0, 0, 0
    called, call_date = False, None
    n_per_year = _obs_per_year(spec.obs_frequency)

    for idx, d in enumerate(obs_dates, start=1):
        lvl = float(ss.loc[:d].iloc[-1])
        if lvl >= spec.coupon_barrier:
            c = (memory_accrual + 1) * (spec.annual_coupon / n_per_year)
            coupon_paid += c
            coupons_count += (memory_accrual + 1)
            memory_accrual = 0
        else:
            if spec.memory_feature:
                memory_accrual += 1
        if lvl >= spec.autocall_barrier:
            called, call_date = True, d
            break

    if called:
        maturity, principal, outcome_type = call_date, 1.0, "Autocall"
    else:
        maturity = obs_dates[-1]
        last_lvl = float(ss.loc[:maturity].iloc[-1])
        if last_lvl >= spec.dip_barrier:
            principal, outcome_type = 1.0, "Capital Redemption"
        else:
            principal, outcome_type = last_lvl / spec.dip_barrier, "Capital Loss"

    days = max(1, (maturity - launch).days)
    total_return = principal - 1.0 + coupon_paid
    irr = total_return * (365.25 / days)

    return {
        "launch": launch,
        "end": maturity,
        "called": called,
        "coupons": coupons_count,
        "coupon_paid": coupon_paid,
        "principal": principal,
        "total_return": total_return,
        "irr_simple": irr,
        "duration_days": days,
        "outcome_type": outcome_type,
        "obs_count": len(obs_dates),
        "obs_reached": idx if called else len(obs_dates),
    }

# ------------------ Backtest ------------------
def run_backtest(prices: pd.Series, years: int, launch_freq: FreqLaunch, spec: ProductSpec) -> pd.DataFrame:
    launches = _gen_launch_dates(prices, years=years, freq=launch_freq, maturity_years=spec.maturity_years)
    return pd.DataFrame.from_records([_evaluate_autocall_path(prices, d, spec) for d in launches]).sort_values("launch").reset_index(drop=True)

# ------------------ Graphs ------------------
def fig_duration(bt: pd.DataFrame) -> go.Figure:
    if bt.empty:
        return go.Figure()

    obs_labels = [f"A{i}" for i in range(1, int(bt["obs_count"].max()) + 1)]
    bt["obs_label"] = bt["obs_reached"].apply(lambda x: f"A{x}")
    counts = bt.groupby("obs_label").size().reindex(obs_labels, fill_value=0)

    fig = go.Figure()
    total_all = len(bt)

    # Toutes sauf la dernière observation
    for lab in obs_labels[:-1]:
        c = counts.get(lab, 0)
        if c > 0:
            text = f"{c/total_all:.1%}"
            fig.add_trace(go.Bar(
                x=[lab], y=[c],
                name="Autocall",
                marker_color="#1f77b4",
                text=text, textposition="inside",
                insidetextanchor="middle",
                showlegend=(lab == obs_labels[0])  # Autocall une seule fois
            ))

    # Dernière observation → breakdown
    last_label = obs_labels[-1]
    subset_last = bt[bt["obs_label"] == last_label]
    total_last = len(subset_last)
    if total_last > 0:
        for outcome, color in [
            ("Autocall", "#1f77b4"),
            ("Capital Redemption", "#2ca02c"),
            ("Capital Loss", "#d62728")
        ]:
            c = (subset_last["outcome_type"] == outcome).sum()
            if c > 0:
                text = f"{c/total_all:.1%}"
                fig.add_trace(go.Bar(
                    x=[last_label], y=[c],
                    name=outcome,
                    marker_color=color,
                    text=text, textposition="inside", insidetextanchor="middle",
                    showlegend=(outcome != "Autocall")
                ))

    fig.update_layout(
        barmode="stack",
        title="Duration to outcome",
        xaxis_title="Observations",
        yaxis_title="Count",
        bargap=0.25,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(255,255,255,0.92)")
    )
    return fig


def fig_total_return(bt: pd.DataFrame) -> go.Figure:
    if bt.empty:
        return go.Figure()

    f = px.histogram(
        bt, x=bt["total_return"] * 100.0,
        nbins=25, opacity=0.85,
        color_discrete_sequence=["#1f77b4"]
    )

    f.update_layout(
        bargap=0.2,
        title="Distribution of Total Return (per 100)",
        xaxis_title="Total return (%)",
        yaxis_title="Count",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="rgba(255,255,255,0.92)")
    )
    return f

# ------------------ Summary ------------------
def summary_table(bt: pd.DataFrame) -> pd.DataFrame:
    if bt.empty:
        return pd.DataFrame({"Metric": [], "Value": []})

    n = len(bt)
    autocalled = bt["called"].mean() * 100

    # Produits arrivés à maturité (dernier A uniquement)
    max_obs = bt["obs_count"].max()
    matured = bt[bt["obs_reached"] == max_obs]

    pct_full_redemption = 100 * (bt["outcome_type"] == "Capital Redemption").sum() / n
    pct_loss = 100 * (bt["outcome_type"] == "Capital Loss").sum() / n

    avg_coupons = bt["coupons"].mean()
    avg_total_return = 100 * bt["total_return"].mean()
    avg_irr = 100 * bt["irr_simple"].mean()
    avg_duration = bt["duration_days"].mean() / 365.25

    return pd.DataFrame([
        ("Backtest Count", f"{n}"),
        ("% Autocalled", f"{autocalled:.1f}%"),
        ("% Full Redemption at maturity", f"{pct_full_redemption:.1f}%"),
        ("% Capital Loss", f"{pct_loss:.1f}%"),
        ("Avg Coupons Count", f"{avg_coupons:.2f}"),
        ("Avg Total Return", f"{avg_total_return:.2f}%"),
        ("Avg IRR %", f"{avg_irr:.2f}%"),
        ("Avg duration", f"{avg_duration:.2f}")
    ], columns=["Metric", "Value"])




