# utils/types.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductInputs:
    maturity_years: float
    dip_style: str                  # 'American' | 'European'
    dip_strike_pct: float
    dip_barrier_pct: float
    autocall_barrier_pct: float
    coupon_barrier_pct: float
    annual_coupon_pct: float
    memory_feature: bool
    obs_frequency: str              # 'annual' | 'semi-annual' | 'quarterly' | 'monthly'
    underlying: Optional[str] = None
    
@dataclass
class MarketInputs:
    stock_price: float
    dividend_yield: float           # decimal (0.02 = 2%)
    interest_rate: float            # decimal
    volatility: float               # decimal
    currency: str | None = None     # rempli via Yahoo si dispo
