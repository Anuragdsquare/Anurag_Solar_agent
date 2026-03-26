import requests
from datetime import datetime

# --- CONFIG ---
CAPACITY_KW = 5000 
LAT = 27.13 # sahasradhara energy pvt ltd
LON = 79.27
BOT_TOKEN = "8732527484:AAFxJVX2aFXsCMpyI2PJwTb74g2t0AnCABA"
CHAT_ID = "8545116146"

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    requests.get(url)

def run_solar_agent():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=direct_radiation,diffuse_radiation&forecast_days=1"
    
    try:
        data = requests.get(url).json()
        india_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
        target_hour = (india_time.hour + 1) % 24
        total_rad = data['hourly']['direct_radiation'][target_hour] + data['hourly']['diffuse_radiation'][target_hour]
        prediction = (total_rad / 1000) * CAPACITY_KW * 0.75
        
        report = (
            f"☀️Anurag pls check,  SOLAR SCHEDULING REPORT\n"
            f"📍 Location: Sahasradhara energy pvt ltd\n"
            f"⏰ Forecast for: {target_hour}:00\n"
            f"📊 Rad: {total_rad} W/m²\n"
            f"🔋 Predicted: {round(prediction, 2)} kW\n\n"
            f"{'⚠️ LOW GEN: Delay heavy loads' if total_rad < 150 else '✅ GOOD GEN: Proceed with scheduling'}"
        )
        
        # Send to Telegram
        send_to_telegram(report)
        print("Success! Check your Telegram.")
            
    except Exception as e:
        print(f"Error: {e}")

run_solar_agent()
