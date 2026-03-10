import requests

url = "http://localhost:8005/api/trading/order"
payload = {
    "symbol": "BTC-USD",
    "side": "buy",
    "type": "market",
    "size": 0.1,
    "price": 63000
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
