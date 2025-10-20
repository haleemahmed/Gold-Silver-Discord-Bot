import requests
from datetime import datetime
from bs4 import BeautifulSoup
import json
import os
import re

# Your Discord webhook URL (keep it secret!)
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# File to store previous day's rates
RATES_FILE = "rates.json"

# Function to fetch gold and silver rates
def fetch_rates():
    url = "https://www.goodreturns.in/gold-rates/chennai.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract gold and silver rates
    text = soup.get_text()
    gold_24k = re.search(r"24 Carat.*?₹\s?([\d,]+)", text)
    gold_22k = re.search(r"22 Carat.*?₹\s?([\d,]+)", text)
    silver = re.search(r"Silver.*?₹\s?([\d,]+)", text)

    return {
        "gold_24k": int(gold_24k.group(1).replace(",", "")) if gold_24k else None,
        "gold_22k": int(gold_22k.group(1).replace(",", "")) if gold_22k else None,
        "silver": int(silver.group(1).replace(",", "")) if silver else None,
    }

# Function to load previous rates
def load_previous_rates():
    if not os.path.exists(RATES_FILE):
        return {}
    with open(RATES_FILE, "r") as f:
        return json.load(f)

# Function to save current rates
def save_current_rates(rates):
    with open(RATES_FILE, "w") as f:
        json.dump(rates, f, indent=4)

# Function to compare and show difference
def format_difference(today, yesterday):
    if yesterday is None:
        return "(new)"
    diff = today - yesterday
    if diff > 0:
        return f"+₹{diff:,} ▲"
    elif diff < 0:
        return f"-₹{abs(diff):,} ▼"
    else:
        return "No change"

# Main process
def main():
    today_rates = fetch_rates()
    old_rates = load_previous_rates()

    message = f"🇮🇳 **Indian Gold & Silver Rates (as of {datetime.now().strftime('%Y-%m-%d')})**\n\n"
    message += "🧈 **Gold (24K - Pure Gold)** →:\n"
    message += f"• 1 gram → ₹{today_rates['gold_24k']:,} ({format_difference(today_rates['gold_24k'], old_rates.get('gold_24k'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['gold_24k'] * 8:,}\n\n"

    message += "🧈 **Gold (22K - Jewellery Gold)** →:\n"
    message += f"• 1 gram → ₹{today_rates['gold_22k']:,} ({format_difference(today_rates['gold_22k'], old_rates.get('gold_22k'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['gold_22k'] * 8:,}\n\n"

    message += "🔘 **Silver** →:\n"
    message += f"• 1 gram → ₹{today_rates['silver']:,} ({format_difference(today_rates['silver'], old_rates.get('silver'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['silver'] * 8:,}\n\n"

    message += "📊 Rates sourced from Indian markets (GoodReturns)\n"
    message += "🕙 Updated automatically every day at 10:00 AM IST"

    # Send to Discord
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)

    # Save today’s rates for tomorrow’s comparison
    save_current_rates(today_rates)

if __name__ == "__main__":
    main()

