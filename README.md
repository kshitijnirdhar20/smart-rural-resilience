# 🌾 Smart Rural Resilience — Simulation Dashboard

A **Streamlit-based interactive simulation app** designed for rural resilience.  
This project demonstrates soil & crop advisory, microgrid energy forecasting, and road safety features in a single dashboard.  

> ⚠️ **Disclaimer:** The data used in this project is **not real**. It is fully simulated and created only for practicing **Streamlit**.

---

## 🚀 Features

### 1. Soil & Crop Advisor (Simulated)
- Generates soil readings (pH, moisture, temperature, NPK).
- Recommends suitable crops based on conditions.
- Provides fertilizer tips.
- Includes a mock LCD display and voice output preview.

### 2. Microgrid Controller (Simulated)
- Generates historic solar and demand data.
- Forecasts next day’s solar profile using moving average.
- Simulates battery charge/discharge for 24 hours.
- Shows when non-critical loads need to be shed.
- Exports simulation logs as CSV.

### 3. Road Highlighters (Demo)
- Trigger emergency mode to activate road highlighters.
- Displays safe route visualization.

---

## 🛠️ Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/smart-rural-resilience.git
   cd smart-rural-resilience
