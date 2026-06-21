import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import warnings
warnings.filterwarnings('ignore')

# --- System Configuration ---
st.set_page_config(page_title="Anurag Forecast Engine", page_icon="☀️", layout="wide")

# Plant Parameters (Mainpuri / Kusmara Region)
LATITUDE = 27.2282 
LONGITUDE = 79.0250
CAPACITY_MW = 5.0

# --- Premium Dark CSS Theme ---
st.markdown('''
    <style>
        .stApp { background-color: #0e1117; color: #ffffff; font-family: 'Segoe UI', sans-serif;}
        [data-testid="stSidebar"] { background-color: #1a1e26; border-right: 1px solid #343a40; }
        .module-box { background-color: #1a1e26; padding: 2rem; border-radius: 12px; border: 1px solid #343a40; margin-bottom: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
        .metric-card { background-color: #232731; padding: 1.5rem; border-radius: 10px; text-align: center; border-left: 5px solid #ffbb00; }
        .metric-title { color: #adb5bd; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem; }
        .metric-value { font-size: 2.5rem; font-weight: bold; color: #ffffff; }
        .stButton>button { background-color: #ffaa00 !important; color: #000000 !important; font-weight: bold !important; border-radius: 25px !important; transition: 0.3s; width: 100%; border:none;}
        .stButton>button:hover { box-shadow: 0 0 15px rgba(255, 170, 0, 0.6); transform: scale(1.02); }
    </style>
''', unsafe_allow_html=True)

# --- Backend Engine ---
@st.cache_resource
def get_model():
    return RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42)

def fetch_live_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': LATITUDE, 'longitude': LONGITUDE,
        'minutely_15': 'shortwave_radiation,temperature_2m',
        'timezone': 'Asia/Kolkata', 'forecast_days': 2
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()['minutely_15']
        df = pd.DataFrame({
            'DateTime': pd.to_datetime(data['time']),
            'GHI': data['shortwave_radiation'],
            'Temp': data['temperature_2m']
        })
        df['Hour'] = df['DateTime'].dt.hour + df['DateTime'].dt.minute/60.0
        return df
    return pd.DataFrame()

# --- User Interface ---
st.markdown('<div style="border-bottom: 2px solid #ffbb00; margin-bottom: 20px; padding-bottom: 10px;"><h1>☀️ Anurag Forecast Engine (AFE)</h1><p style="color:#adb5bd; font-size:16px;">5 MWh Utility-Scale Forecasting Engine | Mainpuri, UP</p></div>', unsafe_allow_html=True)

col_ctrl, col_dash = st.columns([1.2, 2.8])

with col_ctrl:
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.header("⚙️ Control Panel")
    
    is_trained = st.session_state.get('is_trained', False)
    if is_trained:
        st.markdown(f'<div style="background-color:#2e7d32; padding:10px; border-radius:5px; text-align:center; font-weight:bold;">✅ AI Model Active | Accuracy: {st.session_state.get("r2", 0)}%</div><br>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background-color:#c62828; padding:10px; border-radius:5px; text-align:center; font-weight:bold;">⚠️ AI Model Inactive. Please Train Model.</div><br>', unsafe_allow_html=True)
        
    st.subheader("1. System Training")
    uploaded_file = st.file_uploader("Upload SCADA Data (CSV/Excel)", type=["csv", "xlsx"])
    if st.button("🔥 Initialize AI Core") and uploaded_file:
        with st.spinner("Compiling mathematical correlations from plant data..."):
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_hist = pd.read_csv(uploaded_file, low_memory=False)
                else:
                    df_hist = pd.read_excel(uploaded_file)
                
                # Dynamic column mapping
                df_hist.columns = [str(c).upper().strip() for c in df_hist.columns]
                
                time_c = next((c for c in df_hist.columns if 'TIME' in c), df_hist.columns[0])
                ghi_c = next((c for c in df_hist.columns if 'GHI' in c), None)
                temp_c = next((c for c in df_hist.columns if 'A.T' in c.replace(' ','') or 'M.T' in c or 'TEMP' in c), None)
                gen_c = next((c for c in df_hist.columns if 'GENERATION' in c), None)
                
                if ghi_c and temp_c and gen_c:
                    df_clean = df_hist[[time_c, ghi_c, temp_c, gen_c]].dropna().copy()
                    df_clean.columns = ['Time', 'GHI', 'Temp', 'Generation']
                    df_clean['GHI'] = pd.to_numeric(df_clean['GHI'], errors='coerce')
                    df_clean['Temp'] = pd.to_numeric(df_clean['Temp'], errors='coerce')
                    df_clean['Generation'] = pd.to_numeric(df_clean['Generation'], errors='coerce')
                    df_clean = df_clean.dropna()
                    
                    df_clean['Generation_MW'] = df_clean['Generation'] / 1000.0
                    
                    def extract_hour(t_str):
                        import re
                        try:
                            match = re.search(r'(\d{1,2}):(\d{2})', str(t_str))
                            if match: return int(match.group(1)) + int(match.group(2))/60.0
                            return np.nan
                        except: return np.nan
                    
                    df_clean['Hour'] = df_clean['Time'].apply(extract_hour)
                    df_clean = df_clean.dropna(subset=['Hour'])
                    df_clean = df_clean[(df_clean['Hour'] >= 5) & (df_clean['Hour'] <= 19)]
                    
                    X = df_clean[['Hour', 'GHI', 'Temp']]
                    y = df_clean['Generation_MW']
                    
                    model = get_model()
                    model.fit(X, y)
                    st.session_state['is_trained'] = True
                    st.session_state['model'] = model
                    st.session_state['r2'] = round(r2_score(y, model.predict(X)) * 100, 2)
                    st.rerun()
                else:
                    st.error("Invalid File Format. Columns missing.")
            except Exception as e:
                st.error(f"Error during training: {e}")

    st.markdown("---")
    st.subheader("2. Grid Scheduling Action")
    gen_btn = st.button("📊 GENERATE 15-MIN FORECAST")
    st.markdown('</div>', unsafe_allow_html=True)

with col_dash:
    if gen_btn:
        if not is_trained:
            st.warning("⚠️ Action Denied. Train the model first.")
        else:
            with st.spinner("Fetching Satellite Weather & Computing Generation Matrix..."):
                forecast_df = fetch_live_weather()
                if not forecast_df.empty:
                    X_future = forecast_df[['Hour', 'GHI', 'Temp']]
                    forecast_df['Est_Gen (MW)'] = st.session_state['model'].predict(X_future)
                    
                    forecast_df.loc[forecast_df['GHI'] <= 0, 'Est_Gen (MW)'] = 0.0
                    forecast_df['Est_Gen (MW)'] = forecast_df['Est_Gen (MW)'].clip(0, CAPACITY_MW).round(3)
                    
                    peak_mw = forecast_df.head(96)['Est_Gen (MW)'].max()
                    total_mwh = forecast_df.head(96)['Est_Gen (MW)'].sum() * 0.25
                    
                    st.markdown("<h2 style='color:#ffffff;'>📊 Live Analytics Board</h2>", unsafe_allow_html=True)
                    
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.markdown(f'<div class="metric-card"><div class="metric-title">Peak Prediction</div><div class="metric-value">{peak_mw} MW</div></div>', unsafe_allow_html=True)
                    mc2.markdown(f'<div class="metric-card"><div class="metric-title">Total MWh (24h)</div><div class="metric-value">{total_mwh:.2f} MWh</div></div>', unsafe_allow_html=True)
                    mc3.markdown(f'<div class="metric-card"><div class="metric-title">Plant Rating</div><div class="metric-value">{CAPACITY_MW} MW</div></div>', unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    fig = px.area(forecast_df.head(96), x='DateTime', y='Est_Gen (MW)', title="High-Precision Generation Curve", color_discrete_sequence=['#ffaa00'])
                    fig.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="Time (15 Min Blocks)", yaxis_title="Power (MW)")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown('<div class="module-box" style="text-align:center;">', unsafe_allow_html=True)
                    st.subheader("📥 Export for Grid Authority")
                    csv = forecast_df[['DateTime', 'GHI', 'Temp', 'Est_Gen (MW)']].to_csv(index=False).encode('utf-8')
                    st.download_button("DOWNLOAD SCHEDULE REPORT (.CSV)", data=csv, file_name=f"AFE_Schedule_{datetime.now().strftime('%d%m%Y')}.csv", mime='text/csv')
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("System Standby. Awaiting Operator Instruction...")
