import streamlit as st
import importlib
from streamlit_option_menu import option_menu

st.set_page_config(page_title="Option Pricer", layout="wide", page_icon="📈")

# --- Style global ---
st.markdown("""
    <style>
        /* Sidebar (volet gauche) */
        [data-testid="stSidebar"] {
            background-color: background-color: #2e2e2e; /* ✅ contraste avec le contenu */
            color: var(--text-color);
        }

        /* Conteneur principal */
        .block-container {
            background-color: var(--background-color); /* ✅ fond principal */
            padding: 2rem;
            border-radius: 10px;
        }

        /* Titres */
        h1, h2, h3, .title {
            color: var(--text-color);
        }

        /* Dataframes, sélecteurs et boutons */
        .stDataFrame, .stSelectbox, .stButton>button, .stRadio, .stTextInput, .stNumberInput {
            border-radius: 8px;
        }

        /* Bouton actif dans menu latéral */
        .nav-link-selected {
            background-color: var(--primary-color) !important;
            color: white !important;
            border-radius: 6px;
        }

        /* Liens */
        a {
            color: var(--primary-color);
            text-decoration: none;
        }
        a:hover {
            opacity: 0.8;
        }
    </style>
""", unsafe_allow_html=True)

# --- Menu latéral ---
with st.sidebar:
    selected_section = option_menu(
        menu_title=None,
        options=["Pricer", "Profile"],
        icons=["graph-up", "person"],
        menu_icon=None,
        default_index=0,
        styles={
            "container": {
                "padding": "0!important",
                "background-color": "var(--secondary-background-color)",  # ✅ fond auto
            },
            "icon": {
                "color": "var(--text-color)",  # ✅ icônes auto
                "font-size": "18px",
            },
            "nav-link": {
                "font-size": "18px",
                "text-align": "left",
                "padding": "12px",
                "margin": "5px 0",
                "border-radius": "5px",
                "color": "var(--text-color)",
                "--hover-color": "var(--background-color)",  # ✅ hover discret
            },
            "nav-link-selected": {
                "background-color": "var(--primary-color)",  # ✅ accent du thème
                "color": "white",
                "border-radius": "6px",
            },
        }
    )

# --- Routing vers les pages ---
pages = {
    "Pricer": "modules.accueil",   # ton pricer = accueil.py
    "Profile": "modules.profile"
}

if selected_section in pages:
    module = importlib.import_module(pages[selected_section])
    module.main()
