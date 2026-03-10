import os
import secrets
try:
    from eth_account import Account
except ImportError:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "eth_account"])
    from eth_account import Account

def generate_testnet_wallet():
    priv = secrets.token_hex(32)
    private_key = "0x" + priv
    acct = Account.from_key(private_key)
    print(f"==========================================")
    print(f"🟢 Generated New Testnet Wallet")
    print(f"Wallet Address : {acct.address}")
    print(f"Private Key    : {private_key}")
    print(f"==========================================")
    
    env_file = ".env"
    if not os.path.exists(env_file):
        print(f"File {env_file} not found. Cannot update automatically.")
        return

    with open(env_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(env_file, "w", encoding="utf-8") as f:
        for line in lines:
            if line.startswith("HYPERLIQUID_API_KEY="):
                f.write(f"HYPERLIQUID_API_KEY={acct.address}\n")
            elif line.startswith("HYPERLIQUID_API_SECRET="):
                f.write(f"HYPERLIQUID_API_SECRET={private_key}\n")
            elif line.startswith("HYPERLIQUID_WALLET_ADDRESS="):
                f.write(f"HYPERLIQUID_WALLET_ADDRESS={acct.address}\n")
            elif line.startswith("TRADING_MODE="):
                f.write("TRADING_MODE=paper\n")
            elif line.startswith("DEMO_MODE="):
                f.write("DEMO_MODE=false\n")
            else:
                f.write(line)

    print("✅ System configured for PAPER TRADING mode.")
    print("✅ Disabled DEMO_MODE.")
    print("✅ Please go to app.hyperliquid-testnet.xyz and fund this wallet with Test USDC before restarting the system.")

if __name__ == "__main__":
    generate_testnet_wallet()
