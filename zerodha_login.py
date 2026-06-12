# zerodha_login.py
from kiteconnect import KiteConnect
from config import ZERODHA_API_KEY, ZERODHA_SECRET
import json

kite = KiteConnect(api_key=ZERODHA_API_KEY)
login_url = kite.login_url()

print(f"\n{'═'*50}")
print(f"  ZERODHA DAILY LOGIN")
print(f"{'═'*50}")
print(f"\n1. Open this URL in browser:")
print(f"\n{login_url}\n")
print(f"2. Login with Zerodha credentials")
print(f"3. Copy redirect URL after login")
print(f"{'═'*50}\n")

redirect_url = input("Paste redirect URL here: ")
request_token = redirect_url.split("request_token=")[1].split("&")[0]
print(f"\n✅ Request token: {request_token}")

data = kite.generate_session(request_token, api_secret=ZERODHA_SECRET)
access_token = data["access_token"]

token_data = {
    "access_token": access_token,
    "date": str(__import__('datetime').date.today())
}
with open('zerodha_token.json', 'w') as f:
    json.dump(token_data, f)

print(f"✅ Token saved!")
print(f"✅ Ready to trade Indian markets!")
print(f"{'═'*50}\n")