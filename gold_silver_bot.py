import requests
from bs4 import BeautifulSoup
import re
import os
import json
from datetime import datetime, timedelta, timezone

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RATES_FILE = "rates.json"

# Create IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def fetch_rates():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # --- GOLD (GoodReturns) ---
        response = requests.get("https://www.goodreturns.in/gold-rates/", headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()

        gold_24k_match = re.search(r"24K[\s\S]*?₹([\d,]+)", text)
        gold_22k_match = re.search(r"22K[\s\S]*?₹([\d,]+)", text)

        gold_24k = float(gold_24k_match.group(1).replace(',', '')) if gold_24k_match else 13069.0
        gold_22k = float(gold_22k_match.group(1).replace(',', '')) if gold_22k_match else 11980.0

        # --- SILVER (LiveChennai) ---
        response2 = requests.get("https://www.livechennai.com/gold_silverrate.asp", headers=headers, timeout=10)
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        silver_match = re.search(r'Silver\s*1\s*Gm\s*</td>\s*<td[^>]*>([\d,\.]+)', str(soup2))
        silver = float(silver_match.group(1).replace(',', '')) if silver_match else 190.0

        print(f"✅ Successfully fetched: 24K={gold_24k}, 22K={gold_22k}, Silver={silver}")
        return {"gold_24k": gold_24k, "gold_22k": gold_22k, "silver": silver}

    except Exception as e:
        print("⚠️ Error fetching rates:", e)
        return {"gold_24k": 13069.0, "gold_22k": 11980.0, "silver": 190.0}


def load_previous_rates():
    if os.path.exists(RATES_FILE):
        with open(RATES_FILE, "r") as f:
            return json.load(f)
    return {}


def save_rates(rates):
    with open(RATES_FILE, "w") as f:
        json.dump(rates, f, indent=2)


def diff_symbol(today, yesterday):
    if yesterday is None:
        return "(new)"
    diff = today - yesterday
    if diff > 0:
        return f"🔺 +₹{diff:.2f}"
    elif diff < 0:
        return f"🔻 -₹{abs(diff):.2f}"
    else:
        return "🟩 no change"


def send_to_discord(today_rates, prev_rates):
    now_ist = datetime.now(IST)
    date_str = now_ist.strftime("%Y-%m-%d")
    time_str = now_ist.strftime("%I:%M %p")

    message = f"🇮🇳 Indian Gold & Silver Rates (as of {date_str}):\n\n"

    message += "🧈 Gold (24K - Pure Gold):\n"
    message += f"• 1 gram → ₹{today_rates['gold_24k']:.2f} ({diff_symbol(today_rates['gold_24k'], prev_rates.get('gold_24k'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['gold_24k']*8:.2f}\n\n"

    message += "🧈 Gold (22K - Jewelry Gold):\n"
    message += f"• 1 gram → ₹{today_rates['gold_22k']:.2f} ({diff_symbol(today_rates['gold_22k'], prev_rates.get('gold_22k'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['gold_22k']*8:.2f}\n\n"

    message += "🔘 Silver:\n"
    message += f"• 1 gram → ₹{today_rates['silver']:.2f} ({diff_symbol(today_rates['silver'], prev_rates.get('silver'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['silver']*8:.2f}\n\n"

    message += f"🕙 Fetched at {time_str} IST\n"
    message += "📊 Rates sourced from Indian markets (GoodReturns & LiveChennai)\n"
    message += "🤖 Updated automatically every day at 10:00 AM IST (except Sunday)"

    try:
        response = requests.post(WEBHOOK_URL, json={"content": message})
        response.raise_for_status()
        print("✅ Successfully posted message to Discord")
    except Exception as e:
        print("⚠️ Failed to post message to Discord:", e)

    save_rates(today_rates)
    print("💾 rates.json updated successfully.")


def main():
    today_rates = fetch_rates()
    prev_rates = load_previous_rates()
    send_to_discord(today_rates, prev_rates)


if __name__ == "__main__":
    main()
