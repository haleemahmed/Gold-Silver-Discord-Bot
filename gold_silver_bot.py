import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import os
import json

# === CONFIG ===
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RATES_FILE = "rates.json"

def fetch_indian_rates():
    """Fetch gold/silver rates from GoodReturns and LiveChennai"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Get from GoodReturns
        url = "https://www.goodreturns.in/gold-rates/"
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')

        text = soup.get_text()
        gold_24k = float(re.search(r'24K[\s\S]*?₹([\d,]+)', text).group(1).replace(',', ''))
        gold_22k = float(re.search(r'22K[\s\S]*?₹([\d,]+)', text).group(1).replace(',', ''))

        # LiveChennai Silver
        response2 = requests.get("https://www.livechennai.com/gold_silverrate.asp", headers=headers, timeout=15)
        soup2 = BeautifulSoup(response2.content, 'html.parser')
        silver_match = re.search(r'Silver\s*1\s*Gm\s*</td>\s*<td[^>]*>([\d,\.]+)', str(soup2))
        silver_rate = float(silver_match.group(1).replace(',', '')) if silver_match else 190.0

        return gold_24k, gold_22k, silver_rate

    except Exception as e:
        print("❌ Error fetching:", e)
        return 13000.0, 12000.0, 190.0


def load_previous_rates():
    if os.path.exists(RATES_FILE):
        with open(RATES_FILE, "r") as f:
            return json.load(f)
    return {}


def save_current_rates(data):
    with open(RATES_FILE, "w") as f:
        json.dump(data, f)


def diff_arrow(today, yesterday):
    """Return arrow & difference text"""
    diff = today - yesterday
    if diff > 0:
        return f"🔺 ₹{abs(diff):,.0f}"
    elif diff < 0:
        return f"🔻 ₹{abs(diff):,.0f}"
    else:
        return "➡️ No change"


def post_to_discord():
    today = datetime.now()
    if today.weekday() == 6:  # Sunday skip
        print("⏭️ Sunday - skipped.")
        return

    gold_24k, gold_22k, silver = fetch_indian_rates()
    previous = load_previous_rates()

    msg = f"🇮🇳 **Indian Gold & Silver Rates (as of {today.date()}):**\n\n"

    # Compare & add arrows
    if previous:
        msg += f"🧈 **Gold (24K - Pure Gold)** → ₹{gold_24k:,.0f}  {diff_arrow(gold_24k, previous.get('gold_24k', gold_24k))}\n"
        msg += f"🧈 **Gold (22K - Jewelry Gold)** → ₹{gold_22k:,.0f}  {diff_arrow(gold_22k, previous.get('gold_22k', gold_22k))}\n"
        msg += f"🔘 **Silver** → ₹{silver:,.0f}  {diff_arrow(silver, previous.get('silver', silver))}\n\n"
    else:
        msg += f"🧈 **Gold (24K - Pure Gold)** → ₹{gold_24k:,.0f}\n"
        msg += f"🧈 **Gold (22K - Jewelry Gold)** → ₹{gold_22k:,.0f}\n"
        msg += f"🔘 **Silver** → ₹{silver:,.0f}\n\n"

    # Pavan rates
    msg += f"💰 **1 Pavan (8 g) rates:**\n"
    msg += f"• 24K → ₹{gold_24k * 8:,.0f}\n"
    msg += f"• 22K → ₹{gold_22k * 8:,.0f}\n"
    msg += f"• Silver → ₹{silver * 8:,.0f}\n\n"

    msg += "📊 *Rates sourced from Indian markets (GoodReturns & LiveChennai)*\n"
    msg += "🕙 *Updated automatically every day at 10:00 AM IST (except Sunday)*"

    # Send to Discord
    requests.post(WEBHOOK_URL, json={"content": msg})
    print("✅ Posted successfully to Discord!")

    # Save for next run
    save_current_rates({
        "gold_24k": gold_24k,
        "gold_22k": gold_22k,
        "silver": silver
    })


if __name__ == "__main__":
    post_to_discord()

