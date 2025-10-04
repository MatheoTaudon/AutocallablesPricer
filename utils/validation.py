# utils/validation.py
from .types import ProductInputs, MarketInputs

def validate_inputs(prod: ProductInputs, mkt: MarketInputs) -> list[str]:
    errors: list[str] = []
    if mkt.stock_price <= 0:
        errors.append("Stock price must be > 0")
    if not (0.0 <= mkt.volatility <= 1.5):
        errors.append("Volatility must be in [0%, 150%]")
    if not (-0.10 <= mkt.interest_rate <= 0.20):
        errors.append("Interest rate must be in [-10%, 20%]")
    if not (0.0 <= mkt.dividend_yield <= 0.20):
        errors.append("Dividend yield must be in [0%, 20%]")

    if prod.maturity_years <= 0:
        errors.append("Maturity must be > 0")
    for name, val, lo, hi in [
        ("DIP Strike", prod.dip_strike_pct, 1, 300),
        ("DIP Barrier", prod.dip_barrier_pct, 1, 300),
        ("Autocallable Barrier", prod.autocall_barrier_pct, 1, 300),
        ("Coupon Barrier", prod.coupon_barrier_pct, 1, 300),
        ("Annualized coupon", prod.annual_coupon_pct, 0, 100),
    ]:
        if not (lo <= val <= hi):
            errors.append(f"{name} must be in [{lo}%, {hi}%]")

    if prod.dip_barrier_pct >= prod.autocall_barrier_pct:
        errors.append("DIP Barrier should be < Autocallable Barrier for a coherent payoff")

    if prod.dip_style not in ("American", "European"):
        errors.append("DIP style must be American or European")

    if prod.obs_frequency not in ("annual", "semi-annual", "quarterly", "monthly"):
        errors.append("Observation frequency invalid")

    return errors

