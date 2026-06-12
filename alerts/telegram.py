# alerts/telegram.py
import requests

def send_alert(token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=payload)
        print(f"📨 Alert sent: {message}")
        return response
    except Exception as e:
        print(f"❌ Alert failed: {e}")