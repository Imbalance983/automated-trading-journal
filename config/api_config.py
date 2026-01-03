# config/api_config.py
import os
from dotenv import load_dotenv


class BybitConfig:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Get API keys from .env file
        self.key = os.getenv("BYBIT_TESTNET_KEY")
        self.secret = os.getenv("BYBIT_TESTNET_SECRET")

        # Check if keys exist
        if not self.key or not self.secret:
            print("❌ ERROR: API keys not found in .env file")
            print("Make sure your .env file has:")
            print("BYBIT_TESTNET_KEY=your_key_here")
            print("BYBIT_TESTNET_SECRET=your_secret_here")
            raise ValueError("Missing API credentials")

        print("✅ API Configuration loaded successfully")
        print(f"   Key: {self.key[:10]}...{self.key[-4:]}")
        print(f"   Environment: TESTNET (Fake Money Only)")