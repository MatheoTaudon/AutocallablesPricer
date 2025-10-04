# utils/constants.py
"""
Constantes de l'app Autocallables Pricer.
- Couleur orange "classique"
- Libellés d'UI (titre)
- Univers de sous-jacents
- Fréquences d'observation
- Mapping API Yahoo Finance
"""

# Orange 
ORANGE = "#FFA500"

# Titre affiché en tête de page
APP_TITLE = "Autocallables Pricer"

# Sous-jacents proposés dans la selectbox
UNDERLYINGS = [

    "Euro Stoxx 50",
    "S&P 500",
]

# Fréquences d'observation
OBS_FREQS = ["annual", "semi-annual", "quarterly", "monthly"]

# (Pour usage futur) Tickers Yahoo correspondants
YAHOO_TICKERS = {

    "Euro Stoxx 50": "^STOXX50E",
    "S&P 500": "^GSPC",
}