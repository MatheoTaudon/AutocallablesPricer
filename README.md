# AutocallablesPricer

> **Live demo :** [autocallablespricer.streamlit.app](https://autocallablespricer.streamlit.app/)

Streamlit application for pricing, backtesting and generating term sheets for **Autocallable structured products**.

---

## Features

- **Monte Carlo Pricing** — Simulates thousands of price paths to compute the fair value of an Autocallable with configurable parameters (barrier levels, coupon rate, memory feature, DIP type...)
- **Historical Backtesting** — Retrieves historical data from Yahoo Finance and replays the product on real market data
- **Term Sheet Generation** — Automatically produces a professional Word document (.docx) summarising product terms, performance history and scenario illustrations

---

## Installation

```bash
# Clone the repository
git clone https://github.com/MatheoTaudon/AutocallablesPricer.git
cd AutocallablesPricer

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

> The app will open at `http://localhost:8501`

---

## Usage

| Tab | Description |
|-----|-------------|
| **Pricer** | Configure product parameters (barrier, coupon, maturity, obs. frequency) and run Monte Carlo simulation |
| **Backtest** | Select an underlying (e.g. S&P 500, EuroStoxx 50), set product terms and replay on historical data |
| **Term Sheet** | Generate and download a Word term sheet based on your inputs |

---

## Project Structure

```
AutocallablesPricer/
├── app.py                  # Streamlit entry point
├── requirements.txt        # Python dependencies
├── packages.txt            # System packages (for Streamlit Cloud)
├── modules/
│   ├── accueil.py          # Landing page
│   └── profile.py          # Profile page
└── utils/
    ├── pricing.py          # Monte Carlo engine
    ├── backtest.py         # Historical backtesting logic
    ├── termsheet.py        # Word document generation
    ├── yahoo.py            # Yahoo Finance data retrieval
    ├── plots.py            # Plotly visualisations
    ├── tables.py           # Data tables
    ├── formatting.py       # Number / date formatting helpers
    ├── validation.py       # Input validation
    ├── constants.py        # App-wide constants
    └── types.py            # Typed dataclasses (ProductInputs, MarketInputs)
```

---

## Dependencies

| Package | Role |
|---------|------|
| `streamlit` | Web app framework |
| `numpy` | Numerical computations (Monte Carlo paths) |
| `pandas` | Data manipulation |
| `plotly` | Interactive charts |
| `matplotlib` | Static charts |
| `python-docx` / `docxtpl` | Word document generation |
| `openpyxl` | Excel support |
| `requests` | HTTP requests |

---

## License

MIT
