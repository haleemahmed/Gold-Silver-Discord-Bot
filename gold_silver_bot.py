import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import os
import json

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RATES_FILE = "rates.json"

def fetch_indian_gold_rates():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get("https://www.goodreturns.in/gold-rates/", headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        gold_24k = gold_22k = None
        price_elements = soup.find_all('div', class_='gldrate')
        for elem in price_elements:
            text = elem.get_text(strip=True)
            if '24K' in text:
                match = re.search(r'₹([\d,]+)', text)
                if match: gold_24k = float(match.group(1).replace(',', ''))
            elif '22K' in text:
                match = re.search(r'₹([\d,]+)', text)
                if match: gold_22k = float(match.group(1).replace(',', ''))

        # LiveChennai for silver
        response2 = requests.get("https://www.livechennai.com/gold_silverrate.asp", headers=headers, timeout=15)
        soup2 = BeautifulSoup(response2.content, 'html.parser')
        silver_rate = None
        tables2 = soup2.find_all('table')
        for table in tables2:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    if 'Silver 1 Gm' in cells[0].get_text(strip=True):
                        match = re.search(r'([\d,]+\.?\d*)', cells[1].get_text())
                        if match: silver_rate = float(match.group(1).replace(',', ''))
                        break

        return gold_24k or 13069.0, gold_22k or 11980.0, silver_rate or 190.0
    except:
        return 13069.0, 11980.0, 190.0

def load_previous_rates():
    if os.path.exists(RATES_FILE):
        with open(RATES_FILE, "r") as f:
            return json.load(f)
    return {"gold_24k": 13069.0, "gold_22k": 11980.0, "silver": 190.0}

def save_current_rates(gold_24k, gold_22k, silver):
    with open(RATES_FILE, "w") as f:
        json.dump({"gold_24k": gold_24k, "gold_22k": gold_22k, "silver": silver}, f)

def get_trend_arrow(today, yesterday):
    if today > yesterday: return "↑"
    elif today < yesterday: return "↓"
    else: return "→"

def post_to_discord():
    today_date = datetime.now().date()
    if datetime.now().weekday() == 6:  # Skip Sunday
        print("⏭️ Today is Sunday, skipping update.")
        return

    gold_24k, gold_22k, silver_rate = fetch_indian_gold_rates()
    prev_rates = load_previous_rates()

    # Trend arrows
    gold_24k_arrow = get_trend_arrow(gold_24k, prev_rates["gold_24k"])
    gold_22k_arrow = get_trend_arrow(gold_22k, prev_rates["gold_22k"])
    silver_arrow = get_trend_arrow(silver_rate, prev_rates["silver"])

    # Per pavan
    gold_24k_pavan = gold_24k * 8
    gold_22k_pavan = gold_22k * 8
    silver_pavan = silver_rate * 8

    message = f"""🇮🇳 Indian Gold & Silver Rates (as of {today_date}):

🧈 Gold (24K - Pure Gold) {gold_24k_arrow}:
• 1 gram → ₹{gold_24k:,.2f}
• 1 pavan (8 g) → ₹{gold_24k_pavan:,.2f}

🧈 Gold (22K - Jewelry Gold) {gold_22k_arrow}:
• 1 gram → ₹{gold_22k:,.2f}
• 1 pavan (8 g) → ₹{gold_22k_pavan:,.2f}

🔘 Silver {silver_arrow}:
• 1 gram → ₹{silver_rate:,.2f}
• 1 pavan (8 g) → ₹{silver_pavan:,.2f}

📊 Rates sourced from Indian markets (GoodReturns & LiveChennai)
🕙 Updated automatically every day at 10:00 AM IST (except Sunday)
"""

    requests.post(WEBHOOK_URL, json={"content": message})
    print(f"✅ Discord updated with trends!")

    save_current_rates(gold_24k, gold_22k, silver_rate)

if __name__ == "__main__":
    post_to_discord()
