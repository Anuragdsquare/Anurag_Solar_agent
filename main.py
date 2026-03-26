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
    # 1. CALCULATE CORRECT INDIA TIME (UTC + 5:30)
    # GitHub servers use UTC, so we must add 5.5 hours to see IST
    now_utc = datetime.utcnow()
    india_now = now_utc + timedelta(hours=5, minutes=30)
    
    # 2. CALCULATE TARGET HOUR (Looking 2 hours ahead in IST)
    target_time_ist = india_now + timedelta(hours=2)
    target_hour = target_time_ist.hour
    
    print(f"Current India Time: {india_now.strftime('%H:%M')} IST")
    print(f"Fetching forecast for: {target_hour}:00 IST")

    # 3. FETCH SATELLITE DATA (Open-Meteo)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=direct_radiation,diffuse_radiation&forecast_days=1"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Get radiation values for the specific target hour
        direct = data['hourly']['direct_radiation'][target_hour]
        diffuse = data['hourly']['diffuse_radiation'][target_hour]
        total_rad = direct + diffuse
        
        # Power Prediction: (Rad/1000) * Capacity * Efficiency (0.75)
        prediction = (total_rad / 1000) * CAPACITY_KW * 0.75
        
        # 4. CONSTRUCT THE REPORT
        report = (
            f"☀️ Anurag pls check, SOLAR SCHEDULING REPORT\n"
            f"📍 Location: Sahasradhara energy pvt ltd\n"
            f"⏰ Forecast for: {target_hour}:00 IST\n"
            f"📊 Rad: {total_rad} W/m²\n"
            f"🔋 Predicted: {round(prediction, 2)} kW\n"
            f"---------------------------\n"
            f"{'⚠️ LOW GEN: Delay heavy loads' if total_rad < 150 else '✅ GOOD GEN: Proceed with scheduling'}"
        )
        
        send_to_telegram(report)
        print("Success! Report sent to Telegram.")
            
    except Exception as e:
        print(f"Data Error: {e}")

if __name__ == "__main__":
    run_solar_agent()
