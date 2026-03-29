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

def run_solar_agent():
    try:
        india_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        target_time = india_now + timedelta(hours=2)
        target_hour = target_time.hour
        target_time_str = target_time.strftime("%Y-%m-%dT%H:00")
        today_str = target_time.strftime("%Y-%m-%d")
        
        if target_hour < 7 or target_hour > 18:
            return
            
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={LAT}&longitude={LON}&"
            f"hourly=global_tilted_irradiance,temperature_2m&"
            f"timezone=Asia%2FKolkata&forecast_days=2&"
            f"tilt={TILT}&azimuth={AZIMUTH}"
        )
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        index = data['hourly']['time'].index(target_time_str)
        tilted_rad = data['hourly']['global_tilted_irradiance'][index] 
        temp_air = data['hourly']['temperature_2m'][index]
        
        if tilted_rad > 0:
            temp_cell = temp_air + (tilted_rad / 40)
            temp_loss_factor = 1 + (TEMP_COEFF * (temp_cell - 25))
            temp_loss_factor = min(1.0, max(0.0, temp_loss_factor)) 
            
            dc_power = (tilted_rad / 1000) * DC_CAPACITY_KW * BASE_SYSTEM_LOSSES * temp_loss_factor
            ac_power_raw = dc_power * INVERTER_EFFICIENCY
            predicted_ac_kw = min(ac_power_raw, TOTAL_INVERTER_MAX_KW)
        else:
            predicted_ac_kw = 0.0
            
        predicted_ac_kw = round(predicted_ac_kw, 2)
        
        running_total = 0.0
        if os.path.isfile('hourly_generation.csv'):
            with open('hourly_generation.csv', mode='r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Date_Time'].startswith(today_str):
                        running_total += float(row['Predicted_AC_kW'])
                        
        running_total += predicted_ac_kw
            
        status = "✅ GOOD GEN: Proceed" if predicted_ac_kw > (DC_CAPACITY_KW * 0.1) else "⚠️ LOW GEN: Delay load"
        
        report = (
            f"☀️ Anurag pls check, SOLAR SCHEDULING REPORT\n"
            f"📍 Sahasradhara energy pvt ltd\n"
            f"⏰ Forecast for: {target_time.strftime('%H:00')} IST\n"
            f"📊 Rad (45°): {tilted_rad} W/m² | 🌡️ Temp: {temp_air}°C\n"
            f"🔋 Predicted AC: {predicted_ac_kw} kW\n"
            f"📈 Today's Total: {round(running_total, 2)} kWh\n"
            f"---------------------------\n"
            f"{status}"
        )
        
        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {'chat_id': CHAT_ID, 'text': report}
        requests.get(send_url, params=payload, timeout=10)
        
        file_exists = os.path.isfile('hourly_generation.csv')
        with open('hourly_generation.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Date_Time', 'Rad_45', 'Temp_C', 'Predicted_AC_kW'])
            writer.writerow([target_time_str, tilted_rad, temp_air, predicted_ac_kw])
            
        if target_hour == 18:
            summary_msg = (
                f"🌅 *END OF DAY SUMMARY*\n"
                f"📅 Date: {today_str}\n"
                f"⚡ Total Final Generation: {round(running_total, 2)} kWh\n"
                f"---------------------------"
            )
            requests.get(send_url, params={'chat_id': CHAT_ID, 'text': summary_msg}, timeout=10)
            
            with open('hourly_generation.csv', 'rb') as doc:
                doc_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
                requests.post(doc_url, data={'chat_id': CHAT_ID}, files={'document': doc}, timeout=20)
            print("Daily summary sent!")
            
        print(f"Success! Predicted {predicted_ac_kw} kW.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_solar_agent()
    
