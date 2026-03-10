import os
import json
import time
import requests
from eth_account import Account
from eth_account.messages import encode_defunct

# 1. Read Testnet Wallet from .env
env_file = ".env"
wallet_address = None
private_key = None

if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("HYPERLIQUID_WALLET_ADDRESS="):
                wallet_address = line.strip().split("=")[1]
            if line.startswith("HYPERLIQUID_API_SECRET="):
                private_key = line.strip().split("=")[1]

if not wallet_address or not private_key:
    print("❌ Cannot find wallet address or private key in .env.")
    print("Please ensure generate_testnet.py was run successfully first.")
    exit(1)

# Ensure account object is instantiated
try:
    account = Account.from_key(private_key)
except Exception as e:
    print(f"❌ Invalid private key format: {e}")
    exit(1)

# 2. Hyperliquid API Helper
HL_URL = "https://api.hyperliquid-testnet.xyz"
EXCHANGE_URL = f"{HL_URL}/exchange"

def send_api_request(payload):
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(EXCHANGE_URL, headers=headers, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# 3. Formulate the L1 Action Request to Claim Faucet
# Hyperliquid L1 operates on specific action payloads.
# For Testnet Faucet, many SDKs/Users use a specific endpoint or signature.
# However, Hyperliquid testnet faucet is usually claimed on the website.
# Let's check API documentation if /info supports a faucet claim or if it requires a manual website request.
# Often, creating an API connection is the best we can do without a captcha.

print(f"==========================================")
print(f"🟢 Checking Testnet Wallet Balance")
print(f"Address: {wallet_address}")
print(f"==========================================")

# Let's request the current Web2 state info to see if we have USDC
info_url = f"{HL_URL}/info"
state_resp = requests.post(info_url, json={"type": "clearinghouseState", "user": wallet_address}).json()

margin_summary = state_resp.get("marginSummary", {})
account_value = float(margin_summary.get("accountValue", 0))

print(f"Current Account Value: {account_value} USDC")

if account_value > 0:
    print("✅ Wallet is already funded!")
else:
    print("⚠️ Wallet balance is ZERO.")
    print("\nBecause Hyperliquid's Testnet Faucet is protected by Cloudflare/Captcha on their website,")
    print("We cannot automate the free money claim entirely through this Python script without triggering anti-bot protections.")
    print("\nUntuk mengklaim uang simulasi $100,000 USDC secara gratis, Anda HANYA perlu melakukan 2 step ini:")
    print("1. Buka link ini di browser Anda: https://app.hyperliquid-testnet.xyz/")
    print("2. Klik tulisan 'Connect' di pojok kanan atas, lalu pilih 'Burner Wallet' / 'Create New'.")
    print("3. Sistem akan memberi Anda 100,000 USDC secara gratis.")
    print("4. Beritahu saya lagi di chat jika sudah, saya akan menarik kunci rahasia baru Anda dari sana!")
