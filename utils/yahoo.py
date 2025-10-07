# utils/yahoo.py

import os
import datetime as dt
import pandas as pd
import yfinance as yf
from typing import Tuple

# ==============================================================
# Yahoo Finance (hybride API + fallback CSV local)
# ==============================================================

DATA_DIR = "download"

# Fichiers CSV locaux
CSV_MAP = {
    "^GSPC": "SP500.csv",
    "^STOXX50E": "SX5E.csv",
}

# Alias possibles pour les indices (compatibilité totale)
INDEX_TICKERS = {
    # S&P 500
    "SP500": "^GSPC",
    "S&P 500": "^GSPC",
    "S&P500": "^GSPC",
    "US500": "^GSPC",
    "SP 500": "^GSPC",

    # Euro Stoxx 50
    "SX5E": "^STOXX50E",
    "EUROSTOXX50": "^STOXX50E",
    "EuroStoxx 50": "^STOXX50E",
    "Eurostoxx 50": "^STOXX50E",
    "Euro Stoxx 50": "^STOXX50E",
}

# ==============================================================
# Utilitaires internes
# ==============================================================

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Aplati les colonnes MultiIndex issues de yfinance ou CSV."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [' '.join([str(c) for c in col if c]).strip() for col in df.columns.values]
    else:
        df.columns = [str(c).strip() for c in df.columns]
    return df

# ==============================================================
# Téléchargement hybride (yfinance + fallback CSV)
# ==============================================================

def download_price(ticker: str, start=None, end=None) -> pd.DataFrame:
    """
    Télécharge les données d’un ticker via yfinance.
    Si échec (Streamlit Cloud), lit le CSV local correspondant.
    """
    try:
        df = yf.download(ticker, start=start, end=end)
        if df is not None and not df.empty:
            df = _flatten_columns(df)
            df.columns = [c.lower() for c in df.columns]
            print(f"[INFO] Données Yahoo Finance chargées pour {ticker}")
            return df
        else:
            print(f"[INFO] Données vides pour {ticker}, fallback CSV local...")
    except Exception as e:
        print(f"[WARN] Échec du téléchargement {ticker}: {e}")
        print(f"[INFO] Lecture du CSV local...")

    # --- Fallback CSV local ---
    filename = CSV_MAP.get(ticker)
    if not filename:
        raise ValueError(f"Aucun fichier CSV défini pour le ticker {ticker}")

    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Le fichier {path} est introuvable.\n"
            f"Ajoute {filename} dans le dossier /{DATA_DIR}/"
        )

    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df = _flatten_columns(df)
    df.columns = [c.lower() for c in df.columns]

    if start:
        df = df[df.index >= pd.to_datetime(start)]
    if end:
        df = df[df.index <= pd.to_datetime(end)]

    print(f"[INFO] Données lues depuis le CSV local : {path}")
    return df


def get_data(tickers, start=None, end=None):
    """
    Compatibilité complète :
    - Accepte un ticker ou une liste de tickers.
    - Retourne un DataFrame ou un dict de DataFrames.
    """
    if isinstance(tickers, str):
        return download_price(tickers, start, end)

    all_data = {}
    for t in tickers:
        all_data[t] = download_price(t, start, end)
    return all_data

# ==============================================================
# Historique d'indice et performances
# ==============================================================

def fetch_index_history(name: str, years: int, end: dt.date = None) -> pd.Series:
    """
    Retourne la série historique de clôture ajustée pour un indice donné
    sur la période demandée (en années).
    Toujours retourne une pd.Series propre.
    """
    end = end or dt.date.today()
    start = end - dt.timedelta(days=years * 365)
    ticker = INDEX_TICKERS.get(name)

    if not ticker:
        raise ValueError(f"Indice inconnu : {name}")

    df = download_price(ticker, start=start, end=end)
    df = _flatten_columns(df)
    df.columns = [c.lower() for c in df.columns]

    # Choix de la colonne de prix la plus pertinente
    if "adj close" in df.columns:
        s = df["adj close"].dropna()
    elif "close" in df.columns:
        s = df["close"].dropna()
    else:
        raise RuntimeError(f"Aucune colonne 'close' ou 'adj close' trouvée pour {name}")

    # Assure qu'on retourne bien une Series
    if not isinstance(s, pd.Series):
        s = pd.Series(s.squeeze())

    s.name = name
    return s


def get_performances(name: str) -> Tuple[float, float, float]:
    """
    Retourne les performances annualisées de l’indice sur 1 an, 5 ans et 10 ans (%).
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

    return tuple(perf_values)




