# Install required libraries before running: pip install requests schedule

import requests
import datetime
import time
import schedule

# --- Configuration ---
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'
SOLCAST_API_KEY = 'YOUR_SOLCAST_API_KEY'

# Plant Parameters
PLANT_CAPACITY_KW = 5000.0  
PERFORMANCE_RATIO = 0.75
TEMP_COEFFICIENT = -0.004

# Coordinates
LATITUDE = 27.131397
LONGITUDE = 79.2762589

def job():
    # 1. Fetch Solcast Data (Forecast Endpoint)
    url = f"https://api.solcast.com.au/data/forecast/radiation_and_weather?latitude={LATITUDE}&longitude={LONGITUDE}&api_key={SOLCAST_API_KEY}&format=json"
    
    try:
        response = requests.get(url).json()
        ghi = response['forecasts'][0]['ghi']
        temp = response['forecasts'][0]['air_temp']
    except Exception as e:
        print(f"API Error: {e}")
        return

    # 2. Calculate Power
    if ghi <= 0:
        predicted_kw = 0.0
    else:
        temp_loss_factor = 1 + (TEMP_COEFFICIENT * (temp - 25))
        predicted_kw = PLANT_CAPACITY_KW * (ghi / 1000.0) * PERFORMANCE_RATIO * temp_loss_factor
        predicted_kw = max(0, predicted_kw)

    # 3. Fetch Actual Total (Replace placeholder with DB fetch logic)
    actual_today_total_kwh = 17160.0 

    # 4. Send Telegram Alert
    now = datetime.datetime.now()
    time_str = now.strftime("%H:00 IST")
    
    message = (
        f"☀️ Anurag pls check, SOLAR SCHEDULING REPORT\n"
        f"📍 Sahasradhara energy pvt ltd\n"
        f"⏰ Forecast for: {time_str}\n"
        f"📊 GHI: {ghi} W/m² | 🌡️ Temp: {temp}°C\n"
        f"🔋 Predicted AC: {predicted_kw:.2f} kW\n"
        f"📈 Today's Total: {actual_today_total_kwh:.2f} kWh\n"
        f"------------------------\n"
        f"✅ GOOD GEN: Proceed"
    )
    
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    requests.post(telegram_url, data=payload)

# 10 Scheduled calls to stay within Solcast free tier limits (8 AM to 5 PM)
run_times = [
    "08:00", "09:00", "10:00", "11:00", "12:00", 
    "13:00", "14:00", "15:00", "16:00", "17:00"
]

for t in run_times:
    schedule.every().day.at(t).do(job)

if __name__ == "__main__":
    print("Solar Bot Started. Waiting for scheduled times (8 AM to 5 PM)...")
    while True:
        schedule.run_pending()
        time.sleep(60)
            
        print(f"Success! Predicted {predicted_ac_kw} kW. Running Total: {round(running_total, 2)} kWh")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_solar_agent()
        
