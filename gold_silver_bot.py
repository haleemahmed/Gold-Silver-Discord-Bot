import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import os
import json

# Discord webhook URL (from GitHub secrets)
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RATES_FILE = "rates.json"

# Fetch rates from GoodReturns & LiveChennai
def fetch_rates():
    headers = {'User-Agent': 'Mozilla/5.0'}
    rates = {}

    # Gold 24K & 22K from GoodReturns
    try:
        response = requests.get("https://www.goodreturns.in/gold-rates/", headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()

        rates["gold_24k"] = float(re.search(r"24K.*?₹([\d,]+)", text).group(1).replace(",", ""))
        rates["gold_22k"] = float(re.search(r"22K.*?₹([\d,]+)", text).group(1).replace(",", ""))
    except:
        rates["gold_24k"] = 13069
        rates["gold_22k"] = 11980

    # Silver from LiveChennai
    try:
        response2 = requests.get("https://www.livechennai.com/gold_silverrate.asp", headers=headers)
        soup2 = BeautifulSoup(response2.text, "html.parser")
        match = re.search(r'Silver.*?1 Gm.*?>([\d,\.]+)', str(soup2))
        rates["silver"] = float(match.group(1).replace(",", "")) if match else 190
    except:
        rates["silver"] = 190

    return rates

# Load previous rates
def load_previous_rates():
    if os.path.exists(RATES_FILE):
        with open(RATES_FILE, "r") as f:
            return json.load(f)
    return {}

# Save today rates
def save_rates(rates):
    with open(RATES_FILE, "w") as f:
        json.dump(rates, f, indent=2)

# Format price difference with arrow and color
def format_diff(today, yesterday):
    diff = today - yesterday
    if diff > 0:
        return f"₹{diff:,.0f} ▲", 0xFF0000  # red for increase
    elif diff < 0:
        return f"- ₹{abs(diff):,.0f} ▼", 0x00FF00  # green for decrease
    else:
        return "No Change", 0x808080

# Send Discord embed
def send_to_discord(rates, prev):
    now = datetime.now().strftime("%Y-%m-%d")

    diff_24k, color_24k = format_diff(rates["gold_24k"], prev.get("gold_24k", rates["gold_24k"]))
    diff_22k, color_22k = format_diff(rates["gold_22k"], prev.get("gold_22k", rates["gold_22k"]))
    diff_silver, color_silver = format_diff(rates["silver"], prev.get("silver", rates["silver"]))

    embed = {
        "title": f"🇮🇳 Indian Gold & Silver Rates (as of {now})",
        "color": 0xFFD700,
        "fields": [
            {"name": "🧈 Gold (24K - Pure Gold)", "value": f"₹{rates['gold_24k']:,.0f} /g  •  {diff_24k}", "inline": False},
            {"name": "🧈 Gold (22K - Jewelry Gold)", "value": f"₹{rates['gold_22k']:,.0f} /g  •  {diff_22k}", "inline": False},
            {"name": "🔘 Silver", "value": f"₹{rates['silver']:,.0f} /g  •  {diff_silver}", "inline": False},
            {"name": "💰 1 Pavan (8g) Rates",
             "value": f"24K: ₹{rates['gold_24k']*8:,.0f}\n22K: ₹{rates['gold_22k']*8:,.0f}\nSilver: ₹{rates['silver']*8:,.0f}",
             "inline": False}
        ],
        "footer": {"text": "📊 Source: GoodReturns & LiveChennai | Updated daily at 10:00 AM IST (except Sunday)"}
    }

    requests.post(WEBHOOK_URL, json={"embeds": [embed]})

# Main function
def main():
    today_rates = fetch_rates()
    prev_rates = load_previous_rates()
    send_to_discord(today_rates, prev_rates)
    save_rates(today_rates)

if __name__ == "__main__":
    main()


