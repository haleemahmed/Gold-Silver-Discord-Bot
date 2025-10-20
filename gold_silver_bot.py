import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import os
import json

# === CONFIG ===
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RATES_FILE = "rates.json"

# --- Fetch Indian gold/silver rates ---
def fetch_rates():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # GoodReturns for gold
        res = requests.get("https://www.goodreturns.in/gold-rates/", headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()

        gold_24k = float(re.search(r"24[ ]?Carat.*?₹([\d,]+)", text).group(1).replace(",", ""))
        gold_22k = float(re.search(r"22[ ]?Carat.*?₹([\d,]+)", text).group(1).replace(",", ""))

        # LiveChennai for silver
        res2 = requests.get("https://www.livechennai.com/gold_silverrate.asp", headers=headers, timeout=15)
        soup2 = BeautifulSoup(res2.text, "html.parser")
        silver_match = re.search(r"Silver\s*1\s*Gm\s*</td>\s*<td[^>]*>([\d,\.]+)", str(soup2))
        silver_rate = float(silver_match.group(1).replace(",", "")) if silver_match else 190.0

        return {"gold_24k": gold_24k, "gold_22k": gold_22k, "silver": silver_rate}

    except Exception as e:
        print(f"❌ Error fetching rates: {e}")
        # fallback values
        return {"gold_24k": 13069.0, "gold_22k": 11980.0, "silver": 190.0}


# --- Load previous day rates ---
def load_previous_rates():
    if os.path.exists(RATES_FILE):
        with open(RATES_FILE, "r") as f:
            return json.load(f)
    return {}


# --- Save today's rates ---
def save_rates(rates):
    with open(RATES_FILE, "w") as f:
        json.dump(rates, f, indent=2)


# --- Compare rates for arrow and color ---
def format_difference(today, yesterday):
    diff = today - yesterday
    if diff > 0:
        return f"₹{abs(diff):,.0f} ▲", 0xFF0000  # red for decrease
    elif diff < 0:
        return f"- ₹{abs(diff):,.0f} ▼", 0x00FF00  # green for increase
    else:
        return "No change", 0x808080  # gray


# --- Send Discord embed ---
def send_to_discord(rates, prev):
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Compare
    diff_24k, color_24k = format_difference(rates["gold_24k"], prev.get("gold_24k", rates["gold_24k"]))
    diff_22k, color_22k = format_difference(rates["gold_22k"], prev.get("gold_22k", rates["gold_22k"]))
    diff_silver, color_silver = format_difference(rates["silver"], prev.get("silver", rates["silver"]))

    embed = {
        "title": f"🇮🇳 Indian Gold & Silver Rates (as of {today_str})",
        "color": 0xFFD700,
        "fields": [
            {
                "name": "🧈 Gold (24K - Pure Gold)",
                "value": f"• 1 gram → ₹{rates['gold_24k']:,.0f}  ({diff_24k})\n• 1 pavan (8 g) → ₹{rates['gold_24k']*8:,.0f}",
                "inline": False
            },
            {
                "name": "🧈 Gold (22K - Jewelry Gold)",
                "value": f"• 1 gram → ₹{rates['gold_22k']:,.0f}  ({diff_22k})\n• 1 pavan (8 g) → ₹{rates['gold_22k']*8:,.0f}",
                "inline": False
            },
            {
                "name": "🔘 Silver",
                "value": f"• 1 gram → ₹{rates['silver']:,.0f}  ({diff_silver})\n• 1 pavan (8 g) → ₹{rates['silver']*8:,.0f}",
                "inline": False
            }
        ],
        "footer": {"text": "📊 Rates from GoodReturns & LiveChennai | Updated daily at 10:00 AM IST (except Sunday)"}
    }

    payload = {"embeds": [embed]}
    requests.post(WEBHOOK_URL, json=payload)
    print("✅ Discord embed sent successfully!")


# --- Main ---
def main():
    if datetime.now().weekday() == 6:  # Skip Sunday
        print("⏭️ Sunday - no update")
        return
    today_rates = fetch_rates()
    prev_rates = load_previous_rates()
    send_to_discord(today_rates, prev_rates)
    save_rates(today_rates)


if __name__ == "__main__":
    main()

