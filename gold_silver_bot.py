import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import os
import json

# Your Discord webhook URL (from GitHub secrets)
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RATES_FILE = "rates.json"

# --- Step 1: Scrape gold & silver prices ---
def fetch_rates():
    url = "https://www.goodreturns.in/gold-rates/"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(res.text, "html.parser")

    def extract_price(text):
        price = re.sub(r"[^\d.]", "", text)
        return float(price) if price else 0.0

    all_spans = soup.find_all("span")
    rates = {}
    for i, span in enumerate(all_spans):
        if "24 Carat Gold" in span.text:
            rates["gold_24k"] = extract_price(all_spans[i+1].text)
        elif "22 Carat Gold" in span.text:
            rates["gold_22k"] = extract_price(all_spans[i+1].text)
        elif "Silver" in span.text:
            rates["silver"] = extract_price(all_spans[i+1].text)
    return rates

# --- Step 2: Load yesterday’s rates ---
def load_previous_rates():
    if os.path.exists(RATES_FILE):
        with open(RATES_FILE, "r") as f:
            return json.load(f)
    return {}

# --- Step 3: Save today’s rates ---
def save_rates(rates):
    with open(RATES_FILE, "w") as f:
        json.dump(rates, f, indent=2)

# --- Step 4: Compare rates ---
def format_difference(today, yesterday):
    diff = today - yesterday
    if diff > 0:
        return f"₹{abs(diff):,.0f} ▲", 0xFF0000  # red for decrease
    elif diff < 0:
        return f"- ₹{abs(diff):,.0f} ▼", 0x00FF00  # green for increase
    else:
        return "No Change", 0x808080  # grey

# --- Step 5: Create and send embed ---
def send_to_discord(rates, prev):
    now = datetime.now().strftime("%Y-%m-%d")

    # Compare differences
    diff_24k, color_24k = format_difference(rates["gold_24k"], prev.get("gold_24k", rates["gold_24k"]))
    diff_22k, color_22k = format_difference(rates["gold_22k"], prev.get("gold_22k", rates["gold_22k"]))
    diff_silver, color_silver = format_difference(rates["silver"], prev.get("silver", rates["silver"]))

    embed = {
        "title": f"🇮🇳 Indian Gold & Silver Rates (as of {now})",
        "color": 0xFFD700,  # gold color
        "fields": [
            {
                "name": "🧈 Gold (24K - Pure Gold)",
                "value": f"₹{rates['gold_24k']:,.0f} /g  •  {diff_24k}",
                "inline": False
            },
            {
                "name": "🧈 Gold (22K - Jewelry Gold)",
                "value": f"₹{rates['gold_22k']:,.0f} /g  •  {diff_22k}",
                "inline": False
            },
            {
                "name": "🔘 Silver",
                "value": f"₹{rates['silver']:,.0f} /g  •  {diff_silver}",
                "inline": False
            }
        ],
        "footer": {
            "text": "📊 Source: GoodReturns | Updated daily at 10:00 AM IST (except Sunday)"
        }
    }

    data = {"embeds": [embed]}
    requests.post(WEBHOOK_URL, json=data)

# --- Step 6: Main logic ---
def main():
    today_rates = fetch_rates()
    prev_rates = load_previous_rates()
    send_to_discord(today_rates, prev_rates)
    save_rates(today_rates)

if __name__ == "__main__":
    main()
