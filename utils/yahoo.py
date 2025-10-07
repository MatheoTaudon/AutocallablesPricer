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

# Fichiers CSV pour Streamlit Cloud
CSV_MAP = {
    "^GSPC": "SP500.csv",
    "^STOXX50E": "SX5E.csv",
}

# Alias possibles pour les indices (compatibilité totale avec ton projet)
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
# Téléchargement hybride : API ou CSV local
# ==============================================================

def download_price(ticker: str, start=None, end=None) -> pd.DataFrame:
    """
    Télécharge les données d’un ticker via yfinance.
    Si l’appel échoue (ex: Streamlit Cloud), lit le CSV local correspondant.
    """
    # 1️⃣ Tentative via Yahoo Finance
    try:
        df = yf.download(ticker, start=start, end=end)
        if df is not None and not df.empty:
            print(f"[INFO] Données Yahoo Finance chargées pour {ticker}")
            return df
        else:
            print(f"[INFO] Données vides pour {ticker}, fallback CSV local...")
    except Exception as e:
        print(f"[WARN] Échec du téléchargement {ticker}: {e}")
        print(f"[INFO] Lecture du CSV local...")

    # 2️⃣ Fallback CSV local
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

    # Normalisation des colonnes (maj/min)
    df.columns = [c.strip().title() for c in df.columns]

    if start:
        df = df[df.index >= pd.to_datetime(start)]
    if end:
        df = df[df.index <= pd.to_datetime(end)]

    print(f"[INFO] Données lues depuis le CSV local : {path}")
    return df


def get_data(tickers, start=None, end=None):
    """
    Compatibilité complète avec l’ancien code :
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
# Fonctions de séries historiques et performances
# ==============================================================

def fetch_index_history(name: str, years: int, end: dt.date = None) -> pd.Series:
    """
    Retourne la série historique de clôture ajustée pour un indice donné
    sur la période demandée (en années).
    Toujours retourne une pd.Series (corrige l’erreur "hist doit être une Series").
    """
    end = end or dt.date.today()
    start = end - dt.timedelta(days=years * 365)
    ticker = INDEX_TICKERS.get(name)

    if not ticker:
        raise ValueError(f"Indice inconnu : {name}")

    df = download_price(ticker, start=start, end=end)

    # Normalise les noms de colonnes
    df.columns = [c.strip().lower() for c in df.columns]

    # Choisit automatiquement la colonne la plus pertinente
    if "adj close" in df.columns:
        s = df["adj close"].dropna()
    elif "close" in df.columns:
        s = df["close"].dropna()
    else:
        raise RuntimeError(f"Aucune colonne 'close' ou 'adj close' trouvée pour {name}")

    # Force le type Series
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

    perf_1y, perf_5y, perf_10y = perf_values
    return perf_1y, perf_5y, perf_10y


