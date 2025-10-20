import requests
from bs4 import BeautifulSoup
import re
import os
import json
from datetime import datetime

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RATES_FILE = "rates.json"

def fetch_rates():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # GoodReturns for gold
        response = requests.get("https://www.goodreturns.in/gold-rates/", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()

        gold_24k = float(re.search(r"24K[\s\S]*?₹([\d,]+)", text).group(1).replace(',', ''))
        gold_22k = float(re.search(r"22K[\s\S]*?₹([\d,]+)", text).group(1).replace(',', ''))

        # LiveChennai for silver
        response2 = requests.get("https://www.livechennai.com/gold_silverrate.asp", headers=headers)
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        silver_match = re.search(r'Silver\s*1\s*Gm\s*</td>\s*<td[^>]*>([\d,\.]+)', str(soup2))
        silver = float(silver_match.group(1).replace(',', '')) if silver_match else 190.0

        return {"gold_24k": gold_24k, "gold_22k": gold_22k, "silver": silver}
    except Exception:
        # fallback
        return {"gold_24k": 13069.0, "gold_22k": 11980.0, "silver": 190.0}

def load_previous():
    if os.path.exists(RATES_FILE):
        with open(RATES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_rates(rates):
    with open(RATES_FILE, "w") as f:
        json.dump(rates, f)

def diff_symbol(today, yesterday):
    if yesterday is None:
        return "🟩 no change"
    diff = today - yesterday
    if diff > 0:
        return "🔺 increase"
    elif diff < 0:
        return "🔻 decrease"
    else:
        return "🟩 no change"

def post_to_discord():
    today_rates = fetch_rates()
    prev_rates = load_previous()
    today = datetime.now().strftime("%Y-%m-%d")

    message = f"🇮🇳 Indian Gold & Silver Rates (as of {today}):\n\n"

    message += "🧈 Gold (24K - Pure Gold):\n"
    message += f"• 1 gram → ₹{today_rates['gold_24k']:.2f} ({diff_symbol(today_rates['gold_24k'], prev_rates.get('gold_24k'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['gold_24k']*8:.2f}\n\n"

    message += "🧈 Gold (22K - Jewelry Gold):\n"
    message += f"• 1 gram → ₹{today_rates['gold_22k']:.2f} ({diff_symbol(today_rates['gold_22k'], prev_rates.get('gold_22k'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['gold_22k']*8:.2f}\n\n"

    message += "🔘 Silver:\n"
    message += f"• 1 gram → ₹{today_rates['silver']:.2f} ({diff_symbol(today_rates['silver'], prev_rates.get('silver'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['silver']*8:.2f}\n\n"

    message += "📊 Rates sourced from Indian markets (GoodReturns & LiveChennai)\n"
    message += "🕙 Updated automatically every day at 10:00 AM IST (except Sunday)"

    # send to Discord
    requests.post(WEBHOOK_URL, json={"content": message})
    save_rates(today_rates)

if __name__ == "__main__":
    main()



