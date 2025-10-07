import os
import datetime as dt
import pandas as pd
from typing import Tuple


DATA_DIR = "download"

# Fichiers CSV à utiliser pour les indices
CSV_MAP = {
    "^GSPC": "SP500.csv",
    "^STOXX50E": "SX5E.csv",
}

# Alias d'indices (compatibles avec ton projet)
INDEX_TICKERS = {
    "SP500": "^GSPC",
    "S&P 500": "^GSPC",
    "S&P500": "^GSPC",
    "US500": "^GSPC",
    "SP 500": "^GSPC",
    "SX5E": "^STOXX50E",
    "EUROSTOXX50": "^STOXX50E",
    "EuroStoxx 50": "^STOXX50E",
    "Eurostoxx 50": "^STOXX50E",
    "Euro Stoxx 50": "^STOXX50E",
}


# ==============================================================
# Fonctions utilitaires
# ==============================================================

def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Aplati les colonnes MultiIndex et nettoie les espaces."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join([str(c) for c in col if c]).strip() for col in df.columns.values]
    else:
        df.columns = [str(c).strip() for c in df.columns]
    return df


def _read_csv_data(ticker: str) -> pd.DataFrame:
    """Lit les données d’un fichier CSV local pour un ticker donné."""
    filename = CSV_MAP.get(ticker)
    if not filename:
        raise ValueError(f"Aucun fichier CSV défini pour le ticker {ticker}")

    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"⚠️ Fichier {path} introuvable. "
            f"Assure-toi que {filename} est bien placé dans le dossier /{DATA_DIR}/."
        )

    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df = _flatten_columns(df)
    df.columns = [c.lower() for c in df.columns]

    try:
        df.index = pd.to_datetime(df.index)
    except Exception:
        # Si l'index n'est pas une date, tenter la colonne 'date'
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        else:
            raise RuntimeError(f"Impossible de convertir l'index en date pour {ticker}")
    return df


# ==============================================================
# Fonctions principales (mêmes signatures qu'avant)
# ==============================================================

def download_price(ticker: str, start=None, end=None) -> pd.DataFrame:
    """
    Version CSV uniquement : lit les données depuis le fichier local.
    """
    df = _read_csv_data(ticker)

    # Filtrage optionnel par dates
    if start:
        df = df[df.index >= pd.to_datetime(start)]
    if end:
        df = df[df.index <= pd.to_datetime(end)]

    return df


def get_data(tickers, start=None, end=None):
    """
    Compatibilité avec l'ancien code :
    - Accepte un ticker unique ou une liste.
    - Retourne un DataFrame ou un dict de DataFrames.
    """
    if isinstance(tickers, str):
        return download_price(tickers, start, end)

    all_data = {}
    for t in tickers:
        all_data[t] = download_price(t, start, end)
    return all_data


def fetch_index_history(name: str, years: int, end: dt.date = None) -> pd.Series:
    """
    Retourne la série historique de clôture ajustée pour un indice donné.
    Fonctionne uniquement à partir des CSV locaux.
    """
    end = end or dt.date.today()
    start = end - dt.timedelta(days=years * 365)
    ticker = INDEX_TICKERS.get(name)

    if not ticker:
        raise ValueError(f"Indice inconnu : {name}")

    df = download_price(ticker, start=start, end=end)

    # Recherche automatique de la bonne colonne de prix
    possible_cols = ["adj close", "close", "price", "last", "value"]
    found = None
    for col in possible_cols:
        if col in df.columns:
            found = col
            break

    if not found:
        raise RuntimeError(f"Aucune colonne de clôture trouvée pour {name}. Colonnes disponibles : {list(df.columns)}")

    s = df[found].dropna()
    if not isinstance(s, pd.Series):
        s = pd.Series(s.squeeze())

    s.name = name
    return s


def get_performances(name: str) -> Tuple[float, float, float]:
    """
    Retourne les performances annualisées de l’indice sur 1, 5 et 10 ans (%).
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





