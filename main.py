import requests
from datetime import datetime, timedelta
import csv
import os

# --- CONFIG ---
DC_CAPACITY_KW = 5000  
TOTAL_INVERTER_MAX_KW = 4800  
LAT = 27.131399 
LON = 79.276257
BOT_TOKEN = "8732527484:AAFxJVX2aFXsCMpyI2PJwTb74g2t0AnCABA"
CHAT_ID = "8545116146"

# --- SYSTEM CONSTANTS ---
TEMP_COEFF = -0.004  
BASE_SYSTEM_LOSSES = 0.85  
INVERTER_EFFICIENCY = 0.982 
TILT = 20
AZIMUTH = 180 

def get_solar_data(target_time):
    """Fetches radiation and temperature, then calculates predicted AC power."""
    target_time_str = target_time.strftime("%Y-%m-%dT%H:00")
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LAT}&longitude={LON}&"
        f"hourly=global_tilted_irradiance,temperature_2m&"
        f"timezone=Asia%2FKolkata&forecast_days=2&"
        f"tilt={TILT}&azimuth={AZIMUTH}"
    )
    
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        
        # Find the correct hour index
        if target_time_str not in data['hourly']['time']:
            return 0, 0, 0
            
        index = data['hourly']['time'].index(target_time_str)
        rad = data['hourly']['global_tilted_irradiance'][index]
        temp = data['hourly']['temperature_2m'][index]
        
        predicted_kw = 0.0
        if rad > 0:
            # Cell Temp Calculation
            temp_cell = temp + (rad / 40)
            # Temperature Loss Factor
            loss_factor = min(1.0, max(0.0, 1 + (TEMP_COEFF * (temp_cell - 25))))
            # AC Power Calculation
            raw_ac = (rad / 1000) * DC_CAPACITY_KW * BASE_SYSTEM_LOSSES * loss_factor * INVERTER_EFFICIENCY
            predicted_kw = round(min(raw_ac, TOTAL_INVERTER_MAX_KW), 2)
            
        return rad, temp, predicted_kw
    except Exception:
        return 0, 0, 0

def run_solar_agent():
    try:
        # IST Time Calculation
        india_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        
        # Only run during daylight hours (7 AM to 6 PM)
        if india_now.hour < 7 or india_now.hour > 18: 
            print("Outside operating hours.")
            return

        # 1. Get Current and Forecast Data
        rad_now, temp_now, kw_now = get_solar_data(india_now)
        next_hour = india_now + timedelta(hours=1)
        rad_next, temp_next, kw_next = get_solar_data(next_hour)

        # 2. SAVE CURRENT DATA TO CSV (Update first!)
        file_name = 'hourly_generation.csv'
        file_exists = os.path.isfile(file_name)
        
        with open(file_name, 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_
