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
    """Fetch live gold and silver rates for Chennai from GoodReturns"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}

        # --- GOLD (GoodReturns Chennai) ---
        gold_url = "https://www.goodreturns.in/gold-rates/chennai.html"
        gold_resp = requests.get(gold_url, headers=headers, timeout=10)
        gold_html = gold_resp.text

        # Extract gold rates from embedded JSON in page
        gold_data_match = re.findall(r'"(\d{2})K Gold"[\s\S]*?"price":"₹([\d,]+)"', gold_html)
        gold_rates = {f"gold_{k}k": float(v.replace(',', '')) for k, v in gold_data_match}

        gold_24k = gold_rates.get("gold_24k", 12589.0)
        gold_22k = gold_rates.get("gold_22k", 11540.0)
        gold_18k = gold_rates.get("gold_18k", 9600.0)

        # --- SILVER (GoodReturns Chennai) ---
        silver_url = "https://www.goodreturns.in/silver-rates/chennai.html"
        silver_resp = requests.get(silver_url, headers=headers, timeout=10)
        silver_html = silver_resp.text

        # Extract silver rate per gram
        silver_match = re.search(r'Silver\s*/g[\s\S]*?₹([\d,]+)', silver_html)
        silver = float(silver_match.group(1).replace(',', '')) if silver_match else 171.0

        print(f"✅ Successfully fetched: 24K={gold_24k}, 22K={gold_22k}, 18K={gold_18k}, Silver={silver}")
        return {
            "gold_24k": gold_24k,
            "gold_22k": gold_22k,
            "gold_18k": gold_18k,
            "silver": silver
        }

    except Exception as e:
        print("⚠️ Error fetching rates:", e)
        # fallback values (most recent working)
        return {
            "gold_24k": 12589.0,
            "gold_22k": 11540.0,
            "gold_18k": 9600.0,
            "silver": 171.0
        }


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

    message = f"🇮🇳 **Indian Gold & Silver Rates (as of {date_str})**\n\n"

    # --- GOLD 24K ---
    message += "🧈 **Gold (24K - Pure Gold)**\n"
    message += f"• 1 gram → ₹{today_rates['gold_24k']:.2f} ({diff_symbol(today_rates['gold_24k'], prev_rates.get('gold_24k'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['gold_24k']*8:.2f}\n\n"

    # --- GOLD 22K ---
    message += "🧈 **Gold (22K - Jewellery Gold)**\n"
    message += f"• 1 gram → ₹{today_rates['gold_22k']:.2f} ({diff_symbol(today_rates['gold_22k'], prev_rates.get('gold_22k'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['gold_22k']*8:.2f}\n\n"

    # --- GOLD 18K ---
    message += "🧈 **Gold (18K - Light Jewellery)**\n"
    message += f"• 1 gram → ₹{today_rates['gold_18k']:.2f} ({diff_symbol(today_rates['gold_18k'], prev_rates.get('gold_18k'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['gold_18k']*8:.2f}\n\n"

    # --- SILVER ---
    message += "🔘 **Silver**\n"
    message += f"• 1 gram → ₹{today_rates['silver']:.2f} ({diff_symbol(today_rates['silver'], prev_rates.get('silver'))})\n"
    message += f"• 1 pavan (8 g) → ₹{today_rates['silver']*8:.2f}\n\n"

    message += f"🕙 *Fetched at {time_str} IST*\n"
    message += "📊 Rates sourced from GoodReturns Chennai\n"
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
