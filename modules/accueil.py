import streamlit as st
import numpy as np

from utils.constants import ORANGE, APP_TITLE, OBS_FREQS
from utils.types import ProductInputs, MarketInputs
from utils.validation import validate_inputs
from utils.pricing import price_autocall_mc
from utils.tables import table_observations, table_information


def render():
    # ====== Styles globaux ======
    st.markdown(
        f"""
        <style>
          .title {{
            font-size: 40px;
            font-weight: bold;
            text-align: center;
            color: {ORANGE};
            margin-top: 20px;
            margin-bottom: 20px;
          }}
          .thin-hr {{
            border: 0; border-top: 2px solid {ORANGE};
            margin: 10px 0 14px 0;
          }}
          .red-btn button {{
            background-color:#DC2626 !important; color:white !important;
            padding: 10px 14px !important; border:none; border-radius:8px;
          }}
          .center-title {{
            text-align: center !important;
            display: block;
            width: 100%;
          }}
          .block-container {{
            background-color: var(--background-color);  
            border-radius: 10px;
            padding: 2rem;
          }}
        </style>
        <div class="title">{APP_TITLE}</div>
        <hr class="thin-hr"/>
        """,
        unsafe_allow_html=True,
    )

    # ====== Inputs Market / Contract / Barriers ======
    c1, c2, c3, c4, c5 = st.columns(5, gap="large")

    with c2:
        st.markdown("<h3 class='center-title'>Market</h3>", unsafe_allow_html=True)
        stock_price = st.number_input("Stock price (base 100)", min_value=0.0, value=100.0, step=0.1, format="%.4f")
        dividend_yield = st.number_input("Dividend yield (%)", value=0.00, step=0.05, format="%.2f")
        interest_rate = st.number_input("Interest rate (%)", value=2.00, step=0.05, format="%.2f")
        volatility = st.number_input("Volatility (%)", value=20.00, step=0.25, format="%.2f")

    with c3:
        st.markdown("<h3 class='center-title'>Contract</h3>", unsafe_allow_html=True)
        annual_coupon_pct = st.number_input("Coupon (%)", value=7.0, step=0.1, format="%.2f")
        obs_frequency = st.selectbox("Observations frequency", OBS_FREQS, index=0)
        memory_feature = st.radio("Memory feature", ["Yes", "No"], horizontal=True)
        maturity_years = st.number_input("Maturity (years)", min_value=0.25, value=5.0, step=0.25, format="%.2f")

    with c4:
        st.markdown("<h3 class='center-title'>Barriers</h3>", unsafe_allow_html=True)
        dip_barrier_pct = st.number_input("DIP barrier (% of S0)", value=70.0, step=0.5, format="%.2f")
        dip_style = st.radio("DIP style", ["American", "European"], horizontal=True)
        autocall_barrier_pct = st.number_input("Autocallable barrier (% of S0)", value=110.0, step=0.5, format="%.2f")
        coupon_barrier_pct = st.number_input("Coupon barrier (% of S0)", value=100.0, step=0.5, format="%.2f")
        dip_strike_pct = 100.0

    with c1: st.write("")
    with c5: st.write("")

    # ====== Bouton Price ======
    c_btn_left, c_btn_mid, c_btn_right = st.columns([2, 1, 2])
    with c_btn_mid:
        st.markdown('<div class="red-btn">', unsafe_allow_html=True)
        price_btn = st.button("Price", key="price_button", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ====== Construire inputs ======
    prod = ProductInputs(
        maturity_years=float(maturity_years),
        dip_style=dip_style,
        dip_strike_pct=float(dip_strike_pct),
        dip_barrier_pct=float(dip_barrier_pct),
        autocall_barrier_pct=float(autocall_barrier_pct),
        coupon_barrier_pct=float(coupon_barrier_pct),
        annual_coupon_pct=float(annual_coupon_pct),
        memory_feature=bool(memory_feature),
        obs_frequency=obs_frequency,
        underlying=None,
    )
    mkt = MarketInputs(
        stock_price=float(stock_price),
        dividend_yield=float(dividend_yield) / 100.0,
        interest_rate=float(interest_rate) / 100.0,
        volatility=float(volatility) / 100.0,
        currency=None,
    )

    # ====== Validation ======
    errors = validate_inputs(prod, mkt)
    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    # ====== Pricing + Memo ======
    if price_btn:
        with st.spinner("Monte Carlo pricing..."):
            pv, diag = price_autocall_mc(prod, mkt, n_paths=30000, steps_per_year=252, seed=42)
        st.session_state["pv"] = pv
        st.session_state["diag"] = diag
        
    st.markdown('<hr class="thin-hr"/>', unsafe_allow_html=True)

    if "diag" not in st.session_state:
        return

    pv = st.session_state["pv"]
    diag = st.session_state["diag"]

    # ====== Résultats ======
    r1, r2, r3 = st.columns(3, gap="large")

    with r1:
        st.markdown("<h3 class='center-title'>Price</h3>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style='text-align:center;'>
              <div style='font-size:2rem; font-weight:600;'>{pv:.2f}</div>
              <div style='font-size:0.9rem; opacity:0.8;'>CI95: {diag['ci95_low']:.2f} – {diag['ci95_high']:.2f}</div>
              <div style='font-size:0.9rem; margin-top:4px;'>per 100</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r2:
        st.markdown("<h3 class='center-title'>Observations</h3>", unsafe_allow_html=True)
        obs_df = table_observations(
            diag["call_prob_per_obs"],
            diag["coupon_prob_per_obs"],
        )
        st.dataframe(obs_df, hide_index=True, use_container_width=True)

    with r3:
        st.markdown("<h3 class='center-title'>Informations</h3>", unsafe_allow_html=True)
    
        # Prob(full 100) = prob d'aller à maturité - prob de perte en capital
        prob_full_100 = max(0.0, min(1.0, diag["prob_maturity"] - diag["prob_capital_loss"]))
    
        info_df = table_information(
            diag["expected_duration_years"],
            diag["equivalent_zcb"],
            diag["forward_at_maturity"],
            diag["prob_capital_loss"],
            prob_full_100,
        )
        st.dataframe(info_df, hide_index=True, use_container_width=True)

    st.markdown('<hr class="thin-hr"/>', unsafe_allow_html=True)
    
    # ====== BACKTEST UI ======
    from utils.yahoo import fetch_index_history
    from utils.backtest import ProductSpec, run_backtest, fig_duration, fig_total_return, summary_table
    from utils.termsheet import INDEX_MAP_API
    
    # Ligne 1 : 3 colonnes
    left_spacer, c1, c2, c3, right_spacer = st.columns([0.5, 1.5, 1, 1.5, 0.5], gap="large")
    
    with c1:
        st.markdown("<br><br>", unsafe_allow_html=True)  # décale les selects
        under_choice = st.selectbox("Underlying", ["EURO STOXX 50", "S&P 500",], index=0)
        back_years = st.selectbox("Backtest window (years)", [5, 10, 15, 20], index=3)
        launch_freq_ui = st.selectbox("Launch frequency", ["Weekly", "Monthly", "Quarterly", "Yearly"], index=0)
        st.markdown('<div class="red-btn">', unsafe_allow_html=True)
        run_bt = st.button("Backtest", key="backtest_button", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with c2:
        st.markdown("<h3 class='center-title'>Backtest</h3>", unsafe_allow_html=True)
    
    with c3:
        st.markdown("<br><br>", unsafe_allow_html=True)  # décale le tableau
        summary_placeholder = st.empty()
    
    if run_bt:
        prod_spec = ProductSpec(
            maturity_years=float(maturity_years),
            obs_frequency=obs_frequency,
            autocall_barrier=float(autocall_barrier_pct) / 100.0,
            coupon_barrier=float(coupon_barrier_pct) / 100.0,
            dip_barrier=float(dip_barrier_pct) / 100.0,
            annual_coupon=float(annual_coupon_pct) / 100.0,
            memory_feature=(memory_feature == "Yes"),
        )
        extra_years = int(np.ceil(prod_spec.maturity_years))
        
        
    
        try:
            
            under_choice_api = INDEX_MAP_API.get(under_choice.strip(), under_choice)
            with st.spinner("Téléchargement des données historiques..."):
                hist = fetch_index_history(under_choice_api, years=int(back_years + extra_years))
            with st.spinner("Backtest en cours..."):
                bt = run_backtest(hist, int(back_years), launch_freq_ui, prod_spec)
    
            if bt.empty:
                st.warning("Aucun backtest possible sur la période choisie (historique insuffisant).")
            else:
                with c3:
                    st.dataframe(summary_table(bt), hide_index=True, use_container_width=True)
    
                g1, g2 = st.columns(2, gap="large")
                with g1:
                    st.plotly_chart(fig_duration(bt), use_container_width=True, config={"displaylogo": False})
                with g2:
                    st.plotly_chart(fig_total_return(bt), use_container_width=True, config={"displaylogo": False})
                    
                # ====== BOUTON TERM SHEET ======
                from utils.yahoo import fetch_index_history
                
                # Conversion display -> API
                under_choice_api = INDEX_MAP_API.get(under_choice.strip(), under_choice)
                
                # Historique 10 ans pour la Term Sheet (toujours une Series)
                hist_series = fetch_index_history(under_choice_api, 10)
                
                st.markdown("<br>", unsafe_allow_html=True)  
                btn_left, btn_center, btn_right = st.columns([2, 1, 2])
                
                with btn_center:
                    from utils.termsheet import generate_termsheet
                
                    # Générer le fichier Word
                    docx_file = generate_termsheet(
                        prod=prod,
                        mkt=mkt,
                        under_choice=under_choice,   # nom affichage
                        back_years=back_years,
                        launch_freq_ui=launch_freq_ui,
                        bt=bt,
                        hist=hist_series,            # ✅ une vraie Series
                        diag=st.session_state["diag"],  
                    )
                
                    st.download_button(
                        label="Download Term Sheet (Word)",
                        data=docx_file,
                        file_name="term_sheet.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )




                    
        except Exception as e:
            st.error(f"Backtest impossible: {e}")


# === Point d'entrée ===
def main():
    render()


if __name__ == "__main__":
    main()
             
                        
     

   

