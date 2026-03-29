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
BASE_SYSTEM_LOSSES = 0.70  
INVERTER_EFFICIENCY = 0.982 
TILT = 45
AZIMUTH = 180 

def get_solar_data(target_time):
    target_time_str = target_time.strftime("%Y-%m-%dT%H:00")
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LAT}&longitude={LON}&"
        f"hourly=global_tilted_irradiance,temperature_2m&"
        f"timezone=Asia%2FKolkata&forecast_days=2&"
        f"tilt={TILT}&azimuth={AZIMUTH}"
    )
    response = requests.get(url, timeout=15)
    data = response.json()
    index = data['hourly']['time'].index(target_time_str)
    rad = data['hourly']['global_tilted_irradiance'][index]
    temp = data['hourly']['temperature_2m'][index]
    
    predicted_kw = 0.0
    if rad > 0:
        temp_cell = temp + (rad / 40)
        loss = min(1.0, max(0.0, 1 + (TEMP_COEFF * (temp_cell - 25))))
        raw_ac = (rad / 1000) * DC_CAPACITY_KW * BASE_SYSTEM_LOSSES * loss * INVERTER_EFFICIENCY
        predicted_kw = round(min(raw_ac, TOTAL_INVERTER_MAX_KW), 2)
    return rad, temp, predicted_kw

def run_solar_agent():
    try:
        india_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        if india_now.hour < 7 or india_now.hour > 18: return

        # 1. Current Status (अभी का)
        rad_now, temp_now, kw_now = get_solar_data(india_now)
        
        # 2. Next Hour Forecast (1 घंटे बाद)
        next_hour = india_now + timedelta(hours=1)
        rad_next, temp_next, kw_next = get_solar_data(next_hour)

        # आज का टोटल (CSV से)
        today_str = india_now.strftime("%Y-%m-%d")
        running_total = 0.0
        if os.path.isfile('hourly_generation.csv'):
            with open('hourly_generation.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Date_Time'].startswith(today_str):
                        running_total += float(row['Predicted_AC_kW'])
        
        running_total = round(running_total + kw_now, 2)

        report = (
            f"📊 *SOLAR LIVE REPORT - {india_now.strftime('%H:%00')}*\n"
            f"📍 Sahasradhara energy pvt ltd\n\n"
            f"🔴 *CURRENT STATUS (NOW):*\n"
            f"✨ Power: {kw_now} kW\n"
            f"📈 Today's Total: {running_total} kWh\n\n"
            f"🔵 *FORECAST ({next_hour.strftime('%H:00')}):*\n"
            f"✨ Exp. Power: {kw_next} kW\n"
            f"☀️ Rad: {rad_next} W/m² | 🌡️ {temp_next}°C\n"
            f"---------------------------"
        )

        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.get(send_url, params={'chat_id': CHAT_ID, 'text': report, 'parse_mode': 'Markdown'}, timeout=10)

        # CSV Update
        file_exists = os.path.isfile('hourly_generation.csv')
        with open('hourly_generation.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists: writer.writerow(['Date_Time', 'Rad', 'Temp', 'Predicted_AC_kW'])
            writer.writerow([india_now.strftime("%Y-%m-%dT%H:00"), rad_now, temp_now, kw_now])

    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    run_solar_agent()
    
