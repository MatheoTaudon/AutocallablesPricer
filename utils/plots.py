import plotly.io as pio
import plotly.graph_objects as go
from docxtpl import InlineImage
from docx.shared import Inches
from io import BytesIO
from utils.backtest import fig_duration
import pandas as pd
import datetime as dt



# ======================
# Durée avant maturité
# ======================
def make_duration_plot_inline(bt, template, width=4.5):
    fig = fig_duration(bt)

    # Nettoyage des légendes (une seule occurrence par type)
    seen = set()
    for trace in fig.data:
        if trace.name in seen:
            trace.showlegend = False
        else:
            trace.showlegend = True
            seen.add(trace.name)

    # Ajustements spécifiques pour l'export Word
    fig.update_layout(
        title="Durée avant maturité",
        xaxis_title="Observations",
        yaxis_title="Nombre de cas",
        width=800,
        height=350,
        font=dict(color="gray"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(
            title="Résultats",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )

    # Export en mémoire
    img_bytes = fig.to_image(format="png", scale=2, width=600, height=350)
    stream = BytesIO(img_bytes)

    return InlineImage(template, stream, width=Inches(width))


# ======================
# Historique indice 10 ans (base 100)
# ======================


def make_index_history_plot_inline(hist: pd.Series, under_choice: str, template, width=5.5):
    from docxtpl import InlineImage
    from docx.shared import Inches
    from io import BytesIO
    import plotly.graph_objects as go

    if not isinstance(hist, pd.Series):
        raise ValueError("hist doit être une Series issue de fetch_index_history.")

    s = hist.dropna().sort_index()
    if s.empty:
        raise ValueError(f"Aucune donnée disponible pour {under_choice}")

    # Fenêtre des 10 dernières années
    end_date = s.index.max()
    start_date = end_date - pd.DateOffset(years=10)
    s = s[s.index >= start_date]

    if s.empty:
        raise ValueError(f"Pas de données disponibles sur les 10 dernières années pour {under_choice}")

    start_str = s.index.min().strftime("%d/%m/%Y")

    # Graphique en points (valeurs brutes)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=s.index,
        y=s.values,
        mode="lines",
        name=under_choice,
        line=dict(color="steelblue", width=2)
    ))

    fig.update_layout(
        title=f"Performance de l’indice {under_choice} depuis le {start_str}",
        xaxis_title="Années",
        yaxis_title="Points",
        width=800,
        height=365,
        font=dict(color="gray"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5
        ),
        xaxis=dict(
            type="date",
            tickformat="%Y"
        )
    )

    # Export en mémoire
    img_bytes = fig.to_image(format="png", scale=2, width=700, height=400)
    stream = BytesIO(img_bytes)

    return InlineImage(template, stream, width=Inches(width))

def make_autocall_scenario_plot_inline(template, prod, scenario: str, width=5.0):
    import numpy as np
    from docxtpl import InlineImage
    from docx.shared import Inches
    from io import BytesIO
    import plotly.graph_objects as go

    n_obs = 5  # A0 à A5
    x = [f"A{i}" for i in range(n_obs+1)]

    # === Trajectoires stylisées ===
    if scenario == "defavorable":
        # Descente progressive sous la protection
        y = [100, 95, 90, 85, 80, prod.dip_barrier_pct - 10]
        final_text = f"{-(100-100 - int(y[-1]))}% du Capital"

    elif scenario == "median":
        # Descend puis remonte légèrement, finit < 100
        y = [100, 95, prod.autocall_barrier_pct - 5, 80, 95, 90]
        final_text = " 100% du capital"

    elif scenario == "favorable":
        # Courbe qui franchit la barrière d’autocall et s’arrête pile à ce moment
        y = [100, prod.autocall_barrier_pct -4, prod.autocall_barrier_pct + 3] + [None]*(n_obs-2)
        final_text = " 100% du capital"
        
    else:
        raise ValueError("Scénario inconnu")

    # === Figure ===
    fig = go.Figure()

    # Courbe principale (spline)
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines",
        line=dict(color="blue", width=2, shape="spline"),
        showlegend=False,
        connectgaps=False  # 🔑 coupe la courbe à l’autocall
    ))

    # === Barrières ===
    fig.add_hline(y=prod.autocall_barrier_pct, line=dict(color="green", dash="dot"), annotation_text="Autocall")
    fig.add_hline(y=prod.coupon_barrier_pct, line=dict(color="orange", dash="dot"), annotation_text="Coupon")
    fig.add_hline(y=prod.dip_barrier_pct, line=dict(color="red", dash="dot"), annotation_text="Protection")

    # === Annotations "Coupon" pour scénario médian ===
    for i, val in enumerate(y):
            if val is not None and val >= prod.coupon_barrier_pct and i > 0:
                fig.add_annotation(
                    x=x[i],
                    y=val,
                    text="Coupon",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.2,
                    ax=0,
                    ay=-50,  # 🔑 décalé pour lisibilité
                    font=dict(color="darkorange", size=11)
                )

    # === Annotation finale ===
    if scenario == "favorable":
        # arrêt pile au moment de l’autocall
        ann_x, ann_y = x[2], y[2]
    else:
        ann_x, ann_y = x[-1], y[-1]

    fig.add_annotation(
        x=ann_x,
        y=ann_y,
        text=f"<b>{final_text}</b>",
        showarrow=False,
        font=dict(color="blue", size=12),
        xanchor="left",
        yanchor="bottom"
    )

    # === Mise en forme ===
    fig.update_layout(
        xaxis_title="Observations",
        yaxis_title="Niveau de l'indice (% du S0)",
        width=720,
        height=300,
        font=dict(color="black", size=11),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=50, r=50, t=30, b=40),
        xaxis=dict(
            showline=True, linecolor="black", mirror=True,
            range=[-0.2, n_obs+1.2]  # espace après A5
        ),
        yaxis=dict(
            showline=True, linecolor="black", mirror=True,
            title_standoff=20,
            range=[prod.dip_barrier_pct - 15, prod.autocall_barrier_pct + 23]
        )
    )

    # Export image
    img_bytes = fig.to_image(format="png", scale=2, width=720, height=300)
    stream = BytesIO(img_bytes)

    return InlineImage(template, stream, width=Inches(width))



