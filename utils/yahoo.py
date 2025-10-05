# utils/yahoo.py

from __future__ import annotations
import datetime as dt
from typing import Literal, Tuple
import pandas as pd
import os
import requests
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
    "EuroStoxx 50": "^SX5E",  # symbole compatible Yahoo
}


# --- Configuration de session fiable pour Yahoo ---
_session = requests_cache.CachedSession("yfinance.cache")
_session.headers["User-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


# --- Clé Alpha Vantage intégrée ---
ALPHAVANTAGE_API_KEY = "Q2DPMRMQCB1513GY"


def _fetch_from_yahoo(ticker: str, start: dt.date, end: dt.date, interval: str) -> pd.DataFrame:
    """Essaye de récupérer les données depuis Yahoo Finance."""
    try:
        df = yf.download(
            ticker,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
            session=_session,
        )
        return df
    except Exception as e:
        print(f"⚠️ Erreur Yahoo pour {ticker}: {e}")
        return pd.DataFrame()


def _fetch_from_alphavantage(ticker: str) -> pd.DataFrame:
    """Fallback via Alpha Vantage si Yahoo échoue."""
    api_key = ALPHAVANTAGE_API_KEY
    if not api_key:
        print("⚠️ Aucune clé API Alpha Vantage trouvée.")
        return pd.DataFrame()

    # Conversion symboles Yahoo -> Alpha Vantage
    symbol_map = {
        "^GSPC": "SPX",
        "^SX5E": "SX5E",
    }
    symbol = symbol_map.get(ticker, ticker)

    url = (
        f"https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_DAILY_ADJUSTED"
        f"&symbol={symbol}"
        f"&outputsize=full"
        f"&apikey={api_key}"
    )

    try:
        r = requests.get(url)
        data = r.json()
        if "Time Series (Daily)" not in data:
            print(f"⚠️ Alpha Vantage n’a pas retourné de données valides pour {symbol}.")
            return pd.DataFrame()

        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index", dtype=float)
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        df.rename(columns={"5. adjusted close": "Adj Close", "4. close": "Close"}, inplace=True)
        return df
    except Exception as e:
        print(f"⚠️ Erreur Alpha Vantage pour {symbol}: {e}")
        return pd.DataFrame()


def fetch_index_history(
    name: IndexName,
    years: int,
    end: dt.date | None = None,
    interval: str = "1d",
) -> pd.Series:
    """Télécharge l'historique d'un indice depuis Yahoo, puis fallback Alpha Vantage si nécessaire."""
    if name not in INDEX_MAP:
        raise ValueError(f"Indice inconnu: {name}. Choisis parmi: {list(INDEX_MAP)}")

    end = end or dt.date.today()
    start = end - dt.timedelta(days=int(years * 365.25))
    ticker = INDEX_MAP[name]

    # --- 1. Tentative Yahoo ---
    df = _fetch_from_yahoo(ticker, start, end, interval)

    # --- 2. Fallback Alpha Vantage ---
    if df.empty:
        print(f"🔁 Fallback vers Alpha Vantage pour {ticker}")
        df = _fetch_from_alphavantage(ticker)

    if df.empty:
        raise RuntimeError(f"Aucune donnée trouvée pour {name} ({ticker}).")

    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    s = df[col]
    if isinstance(s, pd.DataFrame):
        s = s.iloc[:, 0]
    s = s.copy()
    s.index = pd.to_datetime(s.index, utc=True)
    s.name = name
    return s


def get_performances(name: IndexName) -> Tuple[float, float, float]:
    """Retourne les performances annualisées de l’indice sur 1 an, 5 ans et 10 ans (%)."""
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

