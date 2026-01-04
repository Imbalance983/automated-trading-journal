# utils/bybit_client.py
from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv


class BybitClient:
    def __init__(self):
        print("🔐 Connecting to Bybit Testnet...")

        # Load environment variables
        load_dotenv()

        # Try multiple variable names
        api_key = (
                os.getenv('BYBIT_API_KEY') or
                os.getenv('BYBIT_TESTNET_KEY')
        )

        api_secret = (
                os.getenv('BYBIT_API_SECRET') or
                os.getenv('BYBIT_TESTNET_SECRET')
        )

        if not api_key or not api_secret:
            print("❌ ERROR: API keys not found in .env file")
            raise ValueError("API keys missing")

        try:
            # Connect to TESTNET
            self.client = HTTP(
                testnet=True,
                api_key=api_key,
                api_secret=api_secret
            )
            print(f"✅ Connected to Bybit Testnet successfully!")

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            raise