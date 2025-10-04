from docxtpl import DocxTemplate, InlineImage
from io import BytesIO
import os

from docx.shared import Inches
from utils.yahoo import get_performances, fetch_index_history
from utils.plots import make_duration_plot_inline, make_index_history_plot_inline, make_autocall_scenario_plot_inline


# === Helpers ===
def fmt_number(x):
    """Affiche sans .0 si entier, sinon 2 décimales."""
    if x is None:
        return "N/A"
    if float(x).is_integer():
        return str(int(x))
    return f"{x:.2f}"


# Ce qu'on envoie à Yahoo
INDEX_MAP_API = {
    "S&P 500": "S&P 500",
    "EURO STOXX 50": "EuroStoxx 50",  
}

# Ce qu'on affiche dans le Word
INDEX_MAP_DISPLAY = {
    "S&P 500": "S&P 500",
    "EURO STOXX 50": "EURO STOXX 50",
}

# Traductions des fréquences
FREQ_MAP_UI = {
    "Weekly": "Hebdomadaire",
    "Monthly": "Mensuel",
    "Quarterly": "Trimestriel",
    "Yearly": "Annuel",
}

FREQ_MAP_OBS = {
    "annual": "Annuel",
    "semi-annual": "Semestriel",
    "quarterly": "Trimestriel",
    "monthly": "Mensuel",
}


def generate_termsheet(prod, mkt, under_choice, back_years, launch_freq_ui, bt, hist, diag=None):
    """
    Génère le Term Sheet Word rempli avec les inputs utilisateur et résultats calculés.
    """
    # === Mapping des noms ===
    under_choice_api = INDEX_MAP_API.get(under_choice.strip(), under_choice)
    under_choice_display = INDEX_MAP_DISPLAY.get(under_choice.strip(), under_choice)
    # Corriger esperluette pour Word
    under_choice_display = under_choice_display.replace("&", "&amp;")

    launch_freq_display = FREQ_MAP_UI.get(launch_freq_ui, launch_freq_ui)
    obs_freq_display = FREQ_MAP_OBS.get(prod.obs_frequency, prod.obs_frequency)

    # === Choix du template ===
    base_path = os.path.join(os.getcwd(), "Termsheet")
    fname = "termsheet_sp500.docx" if "500" in under_choice_api else "termsheet_eurostoxx.docx"
    template_path = os.path.join(base_path, fname)

    template = DocxTemplate(template_path)

    # === Champs calculés ===
    coupon_times_maturity = prod.annual_coupon_pct * prod.maturity_years

    # Performances Yahoo (1y, 5y, 10y)
    perf_1y, perf_5y, perf_10y = get_performances(under_choice_api)

    # Résultats backtest
    backtest_count = len(bt) if bt is not None else 0
    autocall_pct = f"{bt['called'].mean()*100:.2f}%" if (bt is not None and not bt.empty) else "N/A"
    capital_loss_pct = f"{(bt['outcome_type'].eq('Capital Loss').mean()*100):.2f}%" if (bt is not None and not bt.empty) else "N/A"
    total_return_avg = f"{bt['total_return'].mean()*100:.2f}%" if (bt is not None and not bt.empty) else "N/A"
    tri_annual_avg = f"{bt['irr_simple'].mean()*100:.2f}%" if (bt is not None and not bt.empty) else "N/A"
    average_duration = f"{(bt['duration_days'].mean()/365.25):.2f}" if (bt is not None and not bt.empty) else "N/A"

    # Forward issu du pricing (diagnostics)
    forward = diag.get("forward_at_maturity") if diag else None

    # === Graphiques ===
    duration_plot = None
    index_history_plot = None
    scenario_defav = None
    scenario_med = None
    scenario_fav = None

    if bt is not None and not bt.empty:
        duration_plot = make_duration_plot_inline(bt, template, width=4.5)

    # ⚡️ check générique qui marche pour Series & DataFrame
    if hist is not None and len(hist) > 0:
        index_history_plot = make_index_history_plot_inline(hist, under_choice, template, width=5.5)

    # Scénarios marketing cohérents avec les barrières choisies
    scenario_defav = make_autocall_scenario_plot_inline(template, prod, "defavorable")
    scenario_med = make_autocall_scenario_plot_inline(template, prod, "median")
    scenario_fav = make_autocall_scenario_plot_inline(template, prod, "favorable")

    # ⚡️ check générique qui marche pour Series & DataFrame
    if hist is not None and len(hist) > 0:
        index_history_plot = make_index_history_plot_inline(hist, under_choice, template, width=5.5)


    # === Contexte pour {{ }} ===
    context = {
        "maturity_years": fmt_number(prod.maturity_years),
        "under_choice": under_choice_display,
        "dip_barrier_pct": fmt_number(prod.dip_barrier_pct),
        "autocall_barrier_pct": fmt_number(prod.autocall_barrier_pct),
        "coupon_barrier_pct": fmt_number(prod.coupon_barrier_pct),
        "annual_coupon_pct": fmt_number(prod.annual_coupon_pct),
        "obs_frequency": obs_freq_display,
        "launch_freq_ui": launch_freq_display,
        "back_years": fmt_number(back_years),
        "coupon_times_maturity": fmt_number(coupon_times_maturity) + "%",
        # Résultats backtest
        "backtest_count": backtest_count,
        "autocall_pct": autocall_pct,
        "capital_loss_pct": capital_loss_pct,
        "total_return_avg": total_return_avg,
        "tri_annual_avg": tri_annual_avg,
        "average_duration": average_duration,
        # Performances Yahoo
        "perf_1y": f"{perf_1y:.2f}%" if perf_1y is not None else "N/A",
        "perf_5y": f"{perf_5y:.2f}%" if perf_5y is not None else "N/A",
        "perf_10y": f"{perf_10y:.2f}%" if perf_10y is not None else "N/A",
        # Forward
        "forward": fmt_number(forward),
        # Graphiques
        "duration_plot": duration_plot,
        "index_history_plot": index_history_plot,
        "scenario_defav": scenario_defav,
        "scenario_med": scenario_med,
        "scenario_fav": scenario_fav,
    }

    # === Rendu du document ===
    template.render(context)

    # Sauvegarde dans buffer mémoire
    buffer = BytesIO()
    template.save(buffer)
    buffer.seek(0)

    return buffer


