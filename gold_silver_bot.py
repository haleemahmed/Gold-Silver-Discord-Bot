import requests
from bs4 import BeautifulSoup
import re
import os
import json
from datetime import datetime, timedelta

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RATES_FILE = "rates.json"

# ----------------- FETCH TODAY'S RATES -----------------
def fetch_rates():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get("https://www.goodreturns.in/gold-rates/", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        text = soup.get_text()

        # Try to extract rates using regex
        match_24k = re.findall(r'24 Carat Gold Rate(?:.*?)₹\s*([\d,]+)', text)
        match_22k = re.findall(r'22 Carat Gold Rate(?:.*?)₹\s*([\d,]+)', text)
        match_18k = re.findall(r'18 Carat Gold Rate(?:.*?)₹\s*([\d,]+)', text)
        match_silver = re.findall(r'Silver Rate(?:.*?)₹\s*([\d,]+)', text)

        if not (match_24k and match_22k and match_silver):
            raise ValueError("Failed to parse one or more rates")

        rates = {
            "gold_24k": float(match_24k[0].replace(",", "")),
            "gold_22k": float(match_22k[0].replace(",", "")),
            "gold_18k": float(match_18k[0].replace(",", "")) if match_18k else round(float(match_24k[0].replace(",", "")) * 0.75, 2),
            "silver": float(match_silver[0].replace(",", ""))
        }

        return rates
    except Exception as e:
        print(f"Error fetching rates: {e}")
        return None

# ----------------- LOAD & SAVE JSON -----------------
def load_all_rates():
    if os.path.exists(RATES_FILE):
        with open(RATES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_all_rates(all_rates):
    with open(RATES_FILE, "w") as f:
        json.dump(all_rates, f, indent=4)

# ----------------- COMPARE -----------------
def compare_rates(today, yesterday):
    comparison = {}
    for key in today:
        if key in yesterday:
            if today[key] > yesterday[key]:
                comparison[key] = "🔺 increase"
            elif today[key] < yesterday[key]:
                comparison[key] = "🔻 decrease"
            else:
                comparison[key] = "➖ no change"
        else:
            comparison[key] = "❓ no data"
    return comparison

# ----------------- FORMAT MESSAGE -----------------
def format_message(today_rates, comparison):
    date_str = datetime.now().strftime("%Y-%m-%d")

    msg = f"🇮🇳 **Indian Gold & Silver Rates (as of {date_str})**\n\n"

    msg += f"🧈 **Gold (24K - Pure Gold):**\n"
    msg += f"• 1 gram → ₹{today_rates['gold_24k']:,.2f} ({comparison['gold_24k']})\n"
    msg += f"• 1 pavan (8 g) → ₹{today_rates['gold_24k']*8:,.2f}\n\n"

    msg += f"🧈 **Gold (22K - Jewelry Gold):**\n"
    msg += f"• 1 gram → ₹{today_rates['gold_22k']:,.2f} ({comparison['gold_22k']})\n"
    msg += f"• 1 pavan (8 g) → ₹{today_rates['gold_22k']*8:,.2f}\n\n"

    msg += f"🧈 **Gold (18K - Hallmark/Ornamental Gold):**\n"
    msg += f"• 1 gram → ₹{today_rates['gold_18k']:,.2f} ({comparison['gold_18k']})\n"
    msg += f"• 1 pavan (8 g) → ₹{today_rates['gold_18k']*8:,.2f}\n\n"

    msg += f"🥈 **Silver:**\n"
    msg += f"• 1 gram → ₹{today_rates['silver']:,.2f} ({comparison['silver']})\n"

    return msg

# ----------------- SEND TO DISCORD -----------------
def send_to_discord(message):
    if not WEBHOOK_URL:
        print("⚠️ Missing Discord Webhook URL")
        return
    payload = {"content": message}
    try:
        r = requests.post(WEBHOOK_URL, json=payload)
        if r.status_code == 204:
            print("✅ Sent successfully to Discord")
        else:
            print(f"⚠️ Failed: {r.status_code}, {r.text}")
    except Exception as e:
        print(f"Error sending message: {e}")

# ----------------- MAIN -----------------
def main():
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    all_rates = load_all_rates()
    today_rates = fetch_rates()
    if not today_rates:
        print("❌ Could not fetch today's rates.")
        return

    # Add today’s data to JSON
    all_rates[today] = today_rates

    # Keep only last 7 days to avoid file growth
    last_7_days = sorted(all_rates.keys())[-7:]
    all_rates = {k: all_rates[k] for k in last_7_days}

    save_all_rates(all_rates)

    # Compare with yesterday if available
    if yesterday in all_rates:
        comparison = compare_rates(today_rates, all_rates[yesterday])
    else:
        comparison = {k: "❓ no data" for k in today_rates}

    message = format_message(today_rates, comparison)
    send_to_discord(message)

if __name__ == "__main__":
    main()
