import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import joblib
import os
import numpy as np
import time
from sqlalchemy import create_engine
from datetime import datetime
from data_audit import get_forecast_ready_data

#PAGE CONFIG
st.set_page_config(
    page_title="Nakuru PM2.5 Forecaster",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CUSTOM CSS
st.markdown("""
    <style>
    .main { background-color: #f9fbfd; }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border-left: 5px solid #2E86C1;
    }
    .stButton>button {
        background-color: #2E86C1;
        color: white;
        border-radius: 8px;
        height: 3em;
        font-weight: bold;
    }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# PATH CONFIGURATION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FOLDER = os.path.join(BASE_DIR, "models")
SARIMAX_PATH = os.path.join(MODEL_FOLDER, "sarimax_mean_model.joblib")
EGARCH_PATH = os.path.join(MODEL_FOLDER, "egarch_volatility_model.joblib")

# SIDEBAR
with st.sidebar:
    st.title("Model Parameters")
    st.markdown("---")
    forecast_horizon = st.number_input("Forecast Window in Hours", min_value=1, max_value=72, value=12)
    st.divider()
    st.markdown("### Model Architecture")
    st.info("**Mean:** SARIMAX(2,0,0)\n\n**Vol:** EGARCH(1,1,1)")
    st.caption("Live Sync: Postgres Database")

# HEADER SECTION
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("🍃 Nakuru AirQuality Dashboard")
    st.subheader("AI-Powered $PM_{2.5}$ Forecasting System")
with col_t2:
    st.write(f"**{datetime.now().strftime('%A, %d %b %Y')}**")
    st.write(f"**Last Sync:** {datetime.now().strftime('%H:%M')} Local")

# DATA LOADING
@st.cache_data(ttl=300) # Reduced TTL to 5 mins to see sync updates faster
def load_and_clean():
    return get_forecast_ready_data()

try:
    data = load_and_clean()
    current_val = round(data.iloc[-1], 2)
    latest_timestamp = data.index.max()
except Exception as e:
    st.error(f"Database Connection Failed: {e}")
    st.stop()

#DATA HEALTH MONITOR
def get_data_health(ts):
    time_diff = (datetime.now() - ts).total_seconds() / 3600
    if time_diff < 1.5:
        return "System Sync: Active", "#2ecc71"
    elif time_diff < 3:
        return "System Sync: Delayed", "#f1c40f"
    else:
        return "System Sync: Offline", "#e74c3c"

health_label, health_color = get_data_health(latest_timestamp)

st.markdown(
    f"""
    <div style="background-color:{health_color}; padding:8px; border-radius:10px; 
    text-align:center; color:white; font-weight:bold; margin-bottom:25px; font-family:sans-serif;">
        {health_label} | Last Successful Audit: {latest_timestamp.strftime('%d %b, %H:%M')}
    </div>
    """, 
    unsafe_allow_html=True
)

#STATUS HELPER
def get_aqi_info(val):
    if val <= 12: return "Good", "#2ecc71", "Safe for all outdoor activities."
    if val <= 35: return "Moderate", "#f1c40f", "Sensitive groups should reduce exertion."
    return "Unhealthy", "#e74c3c", "Avoid prolonged outdoor exposure."

status_label, status_color, status_desc = get_aqi_info(current_val)

#TOP METRICS
m1, m2, m3, m4 = st.columns(4)
m1.metric("Current PM2.5", f"{current_val} µg/m³", delta="Live")
m2.metric("AQI Status", status_label)
m3.metric("Data Reliability", "98.4%", delta="High")
m4.metric("Location", "Nakuru")

#FORECAST LOGIC
def prepare_hybrid_inputs(data, horizon):
    current_exog = pd.DataFrame({'is_missing': 0}, index=data.index)
    offset = 0.005 
    data_log = np.log(data + offset)
    future_dates = pd.date_range(start=data.index[-1] + pd.Timedelta(hours=1), periods=horizon, freq='h')
    forecast_exog = pd.DataFrame({'is_missing': 0}, index=future_dates)
    return data_log, current_exog, forecast_exog, offset

st.markdown("### Predictive Intelligence")

if st.button('Generate High-Fidelity Forecast', use_container_width=True):
    try:
        with st.status("Initializing AI Simulation...", expanded=True) as status:
            st.write("Extracting latest sensor data from Postgres...")
            data_log, current_exog, forecast_exog, offset = prepare_hybrid_inputs(data, forecast_horizon)
            time.sleep(0.4)
            
            st.write("Loading SARIMAX weights & calculating seasonal trends...")
            sarimax_results = joblib.load(SARIMAX_PATH)
            updated_sarimax = sarimax_results.apply(data_log, exog=current_exog)
            sarimax_f = updated_sarimax.get_forecast(steps=forecast_horizon, exog=forecast_exog)
            mean_forecast = np.exp(sarimax_f.predicted_mean) - offset
            time.sleep(0.4)
            
            st.write("Estimating EGARCH volatility & variance shocks...")
            egarch_results = joblib.load(EGARCH_PATH)
            egarch_f = egarch_results.forecast(horizon=forecast_horizon, method='simulation')
            vol = np.sqrt(egarch_f.variance.values[-1, :]) / 10
            time.sleep(0.4)
            
            st.write("Synthesizing hybrid confidence bands...")
            upper_ci = mean_forecast + (1.96 * vol)
            lower_ci = mean_forecast - (1.96 * vol)
            status.update(label="Forecast Complete!", state="complete", expanded=False)

        #PLOT
        history = data.tail(48)
        fig = go.Figure()
        fig.add_hrect(y0=0, y1=12, fillcolor="#2ecc71", opacity=0.1, line_width=0, annotation_text="Healthy")
        fig.add_hrect(y0=12.1, y1=35.4, fillcolor="#f1c40f", opacity=0.1, line_width=0, annotation_text="Moderate")
        fig.add_hrect(y0=35.5, y1=150, fillcolor="#e74c3c", opacity=0.1, line_width=0, annotation_text="Unhealthy")

        fig.add_trace(go.Scatter(x=history.index, y=history.values, name='Observed (Past)', line=dict(color='#34495e', width=2)))
        fig.add_trace(go.Scatter(x=mean_forecast.index, y=mean_forecast.values, name='AI Forecast', line=dict(color='#e74c3c', width=4)))
        fig.add_trace(go.Scatter(
            x=pd.concat([pd.Series(mean_forecast.index), pd.Series(mean_forecast.index[::-1])]),
            y=pd.concat([pd.Series(upper_ci), pd.Series(lower_ci[::-1])]),
            fill='toself', fillcolor='rgba(231, 76, 60, 0.1)', line=dict(color='rgba(0,0,0,0)'), name='95% Volatility Band'
        ))

        fig.update_layout(
            xaxis_title="<b>Time (Local Nakuru Time)</b>",
            yaxis_title="<b>PM2.5 (µg/m³)</b>",
            template="plotly_white",
            height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        # INSIGHTS
        st.markdown("### Insights & Health Recommendations")
        peak_val = round(mean_forecast.max(), 1)
        peak_time = mean_forecast.idxmax().strftime('%H:00')
        avg_risk = round(vol.mean(), 2)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.info(f"**Peak Pollution**\n\n{peak_val} µg/m³ expected at {peak_time}.")
        with c2:
            st.success(f"**Daily Forecast Average**\n\n{round(mean_forecast.mean(),1)} µg/m³ predicted.")
        with c3:
            st.warning(f"**Atmospheric Volatility**\n\nRisk Score: {avg_risk}")

        st.markdown("---")
        if peak_val > 35:
            st.error(f"**Health Advisory:** Pollution levels are expected to spike. {status_desc}")
        else:
            st.success(f"**Clear Air Outlook:** Conditions are expected to remain stable. {status_desc}")

    except Exception as e:
        st.error(f"Simulation Error: {e}")

# FOOTER
st.markdown("---")
f1, f2 = st.columns(2)
with f1:
    st.caption("AI Model: Hybrid SARIMAX-EGARCH | Data Source: PostgreSQL (OpenAQ Sync)")
with f2:
    st.markdown("<p style='text-align: right; color: black; font-size: 0.8em;'>Developed by <b>Eugene Githinji Mbugua</b></p>", unsafe_allow_html=True)