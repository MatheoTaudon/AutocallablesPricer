# utils/yahoo.py

from __future__ import annotations
import datetime as dt
from typing import Literal, Tuple
import pandas as pd
import requests_cache

try:
    import yfinance as yf
except Exception as e:
    raise ImportError(
        "Le module 'yfinance' est requis. Installe-le avec: pip install yfinance"
    ) from e


IndexName = Literal["S&P 500", "EuroStoxx 50"]

INDEX_MAP: dict[IndexName, str] = {
    "S&P 500": "^GSPC",
    "EuroStoxx 50": "^SX5E",  # Yahoo symbol corrigé pour compatibilité Cloud
}


# --- Session HTTP persistante et fiable ---
_session = requests_cache.CachedSession("yfinance.cache")
_session.headers["User-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def fetch_index_history(
    name: IndexName,
    years: int,
    end: dt.date | None = None,
    interval: str = "1d",
) -> pd.Series:
    if name not in INDEX_MAP:
        raise ValueError(f"Indice inconnu: {name}. Choisis parmi: {list(INDEX_MAP)}")

    end = end or dt.date.today()
    start = end - dt.timedelta(days=int(years * 365.25))
    ticker = INDEX_MAP[name]

    # --- Tentatives de téléchargement robustes ---
    df = pd.DataFrame()
    max_tries = 3
    for i in range(max_tries):
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False,  # important pour Streamlit Cloud
                session=_session,
            )
            if not df.empty:
                break
        except Exception as e:
            print(f"Tentative {i+1}/{max_tries} échouée pour {ticker}: {e}")

    if df.empty:
        raise RuntimeError(f"Aucune donnée Yahoo pour {name} ({ticker}).")

    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    s = df[col]

    if isinstance(s, pd.DataFrame):
        s = s.iloc[:, 0]

    s = s.copy()
    s.index = pd.to_datetime(s.index, utc=True)
    s.name = name
    return s


def get_performances(name: IndexName) -> Tuple[float, float, float]:
    """
    Retourne les performances annualisées de l’indice sur 1 an, 5 ans et 10 ans.
    Résultats en pourcentage (%).
    """
    today = dt.date.today()
    perf_values = []

    for years in [1, 5, 10]:
        try:
            s = fetch_index_history(name, years, end=today)
            if len(s) < 2:
                raise RuntimeError("Pas assez de données")
            start_price, end_price = float(s.iloc[0]), float(s.iloc[-1])
            perf = (end_price / start_price - 1) * 100
        except Exception:
            perf = None
        perf_values.append(perf)

    perf_1y, perf_5y, perf_10y = perf_values
    return perf_1y, perf_5y, perf_10y

