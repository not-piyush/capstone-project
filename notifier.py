import time
import requests
import database
import data_collection
from datetime import datetime

def send_discord_alert(webhook_url, message):
    if not webhook_url:
        return
    data = {"content": message}
    try:
        requests.post(webhook_url, json=data)
    except Exception as e:
        print(f"Failed to send webhook: {e}")

def run_notifier():
    print(f"[{datetime.now()}] Running notifier...")
    alerts = database.get_active_alerts()
    vid = database.add_vendor('Web Scraper', 'Online')
    for alert in alerts:
        a_id, p_id, p_name, target_price, u_id, tracking_url = alert
        if not tracking_url:
            continue
            
        # Get user settings
        user = database.get_user_by_id(u_id)
        webhook_url = user[3] if user else None
        
        # Check current price
        current_price = data_collection.scrape_url(tracking_url)
        if current_price is not None:
            database.add_price(p_id, vid, current_price)
            if current_price <= target_price:
                msg = f"🚨 Price Alert! **{p_name}** has dropped to Rs. {current_price}! (Target was Rs. {target_price})\nLink: {tracking_url}"
                print(msg)
                if webhook_url:
                    send_discord_alert(webhook_url, msg)
                # Deactivate alert once triggered
                database.deactivate_alert(a_id)

if __name__ == '__main__':
    print("Starting background Price Watcher daemon (checks every 60 mins)...")
    while True:
        run_notifier()
        # Sleep for an hour
        time.sleep(3600)

def run_notifier_loop():
    print("Starting background Price Watcher thread...")
    while True:
        run_notifier()
        time.sleep(3600)
