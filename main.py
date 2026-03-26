import requests
from datetime import datetime, timedelta

# --- CONFIG ---
CAPACITY_KW = 5000 
LAT = 27.13 # sahasradhara energy pvt ltd
LON = 79.27
BOT_TOKEN = "8732527484:AAFxJVX2aFXsCMpyI2PJwTb74g2t0AnCABA"
CHAT_ID = "8545116146"

def run_solar_agent():
    try:
        # 1. Get India Time (UTC + 5:30)
        india_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        target_time = india_now + timedelta(hours=2)
        target_hour = target_time.hour
        
        # 2. Get Data
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=direct_radiation,diffuse_radiation&timezone=Asia%2FKolkata&forecast_days=2"
        data = requests.get(url, timeout=15).json()
        
        # 3. Calculate index (handles midnight rollover properly)
        # Using target_time logic to ensure we get the right hour index in the 48-hour list
        index = india_now.hour + 2
        
        total_rad = data['hourly']['direct_radiation'][index] + data['hourly']['diffuse_radiation'][index]
        prediction = (total_rad / 1000) * CAPACITY_KW * 0.75
        
        # 4. Construct Report
        report = (
            f"☀️ Anurag pls check, SOLAR SCHEDULING REPORT\n"
            f"📍 Sahasradhara energy pvt ltd\n"
            f"⏰ Forecast for: {target_hour}:00 IST\n"
            f"📊 Rad: {total_rad} W/m²\n"
            f"🔋 Predicted: {round(prediction, 2)} kW\n"
            f"---------------------------\n"
            f"{'✅ GOOD GEN: Proceed' if total_rad > 150 else '⚠️ LOW GEN: Delay load'}"
        )
        
        # 5. Send to Telegram
        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={report}"
        requests.get(send_url, timeout=10)
        print("Success")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_solar_agent()
