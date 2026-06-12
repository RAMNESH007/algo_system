from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from alerts.telegram import send_alert

send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, "✅ Telegram working!")