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
    # 1. Fetch Solcast Data
    url = f"https://api.solcast.com.au/data/forecast/radiation_and_weather?latitude={LATITUDE}&longitude={LONGITUDE}&api_key={SOLCAST_API_KEY}&format=json"
    
    try:
        response = requests.get(url).json()
        ghi = response['forecasts'][0]['
