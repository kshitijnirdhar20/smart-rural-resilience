import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta

st.set_page_config(page_title="Smart Rural Resilience — Simulation", layout="wide")


def gen_soil_reading(seed=None):
    if seed is not None:
        np.random.seed(seed)
    soil = {
        "pH": round(np.random.uniform(5.0, 8.0), 2),
        "Moisture(%)": int(np.random.uniform(10, 85)),
        "Temperature(C)": int(np.random.uniform(15, 38)),
        "N(mg/kg)": int(np.random.uniform(30, 200)),
        "P(mg/kg)": int(np.random.uniform(10, 100)),
        "K(mg/kg)": int(np.random.uniform(30, 200)),
    }
    return soil

def recommend_crop(soil):
    ph = soil["pH"]
    moisture = soil["Moisture(%)"]
    N = soil["N(mg/kg)"]
   
    scores = {}
    
    scores['Rice'] = ((6.0 <= ph <= 7.5) * 1.0) + (moisture>50)*1.0
    scores['Maize'] = (5.5 <= ph <= 7.0)*1.0 + (moisture>35)*0.5
    scores['Millet'] = (ph < 6.5)*0.5 + (moisture<40)*1.0
    scores['Tomato'] = (6.0 <= ph <= 7.5)*0.8 + (N>100)*0.5
    
    top = sorted(scores.items(), key=lambda x: -x[1])[:3]
    return [t[0] for t in top]

def gen_history(days=7, noise_level=0.15):
    
    records = []
    base_date = datetime.now().date() - pd.Timedelta(days=days-1)
    for d in range(days):
        day = base_date + pd.Timedelta(days=d)
        
        sunny_factor = np.random.uniform(0.6, 1.0)
        for hour in range(24):
            
            solar = max(0, 100 * sunny_factor * (1 - abs(hour - 12)/12))
            solar = solar * (1 + np.random.normal(0, noise_level))
        
            load = 30 + 10*np.sin((hour/24)*2*np.pi + 1.5) + np.random.normal(0, 3)
            records.append({"date": day, "hour": hour, "solar": max(0, solar), "load": max(5, load)})
    return pd.DataFrame(records)

def forecast_next_day(history_df, window_days=3):
    
    history_df = history_df.sort_values('date')
    last_dates = history_df['date'].unique()[-window_days:]
    subset = history_df[history_df['date'].isin(last_dates)]
    forecast = subset.groupby('hour')['solar'].mean().reset_index()
    return forecast

def simulate_day(initial_batt_pct, forecast_df, demand_profile=None):
    
    batt = initial_batt_pct
    logs = []
    
    solar_by_hour = dict(zip(forecast_df['hour'], forecast_df['solar']))
    for hour in range(24):
        solar = solar_by_hour.get(hour, 0)
        
        if demand_profile is None:
            demand = 30 + 10*np.sin((hour/24)*2*np.pi + 1.5)
        else:
            demand = demand_profile.get(hour, 30)
     
        delta_pct = (solar - demand)/10.0  
        batt += delta_pct
        batt = max(0, min(100, batt))
        
        non_critical_on = True
        if batt < 20:
            non_critical_on = False
        logs.append({"hour": hour, "solar": round(solar,2), "demand": round(demand,2), "battery_pct": round(batt,2),
                     "non_critical_on": non_critical_on})
    return pd.DataFrame(logs)


st.title("🌾 Smart Rural Resilience — Simulation Dashboard")
st.sidebar.header("Controls")

st.header("1) Soil & Crop Advisor (Simulated)")
seed = st.sidebar.number_input("Soil seed (change to vary reading)", min_value=0, max_value=9999, value=42)
if st.sidebar.button("Generate new soil reading"):
    seed += 1
soil = gen_soil_reading(seed)
cols = st.columns([1,2,1])
with cols[0]:
    st.subheader("LCD (Mock)")
    st.markdown(f"""
    <div style="background:#013220;color:#b7ffce;padding:12px;border-radius:8px">
    <b>pH:</b> {soil['pH']} &nbsp;&nbsp; <b>Moisture:</b> {soil['Moisture(%)']}% <br>
    <b>Temp:</b> {soil['Temperature(C)']} °C <br>
    <b>NPK:</b> {soil['N(mg/kg)']}/{soil['P(mg/kg)']}/{soil['K(mg/kg)']}
    </div>
    """, unsafe_allow_html=True)
with cols[1]:
    st.subheader("Recommendations")
    crops = recommend_crop(soil)
    st.write("Top picks:", ", ".join([f"🌱 {c}" for c in crops]))
    st.write("- Fertilizer tip: Give balanced NPK; reduce N if soil N>150. (Demo rule)")
with cols[2]:
    
    st.subheader("Voice (demo)")
    st.info("Pre-recorded prompt plays in final hardware demo. (In simulation, text preview shown below.)")
    st.write(f"Voice text: 'Soil pH is {soil['pH']}. Recommended crop: {crops[0]}.'")

st.markdown("---")


st.header("2) Microgrid Controller (Simulated)")
history_days = st.sidebar.slider("Historic days for forecast", 1, 14, 7)
history_df = gen_history(days=history_days)
st.subheader("Historic solar (sample)")
sample_day = history_df['date'].unique()[-1]
day_df = history_df[history_df['date']==sample_day]
st.line_chart(day_df[['hour','solar']].set_index('hour'))


st.subheader("Day-ahead forecast (moving average)")
window_days = st.sidebar.slider("Window days for moving average", 1, min(7, history_days), 3)
forecast_df = forecast_next_day(history_df, window_days)

fig, ax = plt.subplots()
ax.plot(day_df['hour'], day_df['solar'], label="Actual sample day")
ax.plot(forecast_df['hour'], forecast_df['solar'], linestyle='--', label="Forecast next day")
ax.set_xlabel("Hour")
ax.set_ylabel("Solar (arbitrary units)")
ax.legend()
st.pyplot(fig)


st.subheader("Simulate next 24 hours with battery")
initial_batt = st.sidebar.slider("Initial battery %", 0, 100, 60)
if st.button("Run 24-hour microgrid simulation"):
    sim_log = simulate_day(initial_batt, forecast_df)
    st.dataframe(sim_log)
    st.line_chart(sim_log.set_index('hour')[['solar','demand','battery_pct']])
    
    shed_count = len(sim_log[sim_log['non_critical_on']==False])
    if shed_count>0:
        st.warning(f"Non-critical loads OFF for {shed_count} hour(s). Critical loads kept ON.")
    else:
        st.success("No load shedding required in simulation.")

    
    csv = sim_log.to_csv(index=False).encode('utf-8')
    st.download_button("Download simulation log (CSV)", data=csv, file_name="sim_log.csv", mime="text/csv")

st.markdown("---")


st.header("3) Road Highlighters (Demo)")
emergency = st.sidebar.checkbox("Trigger Emergency (road highlighters)")
if emergency:
    st.error("🚨 EMERGENCY: Road highlighters ACTIVATED! Follow the marked path to safety.")
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Map_pin_icon.svg/1200px-Map_pin_icon.svg.png", width=120)
    
    st.markdown("<h2 style='color:red'>→ SAFE ROUTE →</h2>", unsafe_allow_html=True)
else:
    st.success("Normal mode: highlighters OFF (demo)")