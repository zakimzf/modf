# Configuration settings will go here.
# For example, API keys, email settings, etc.

import os

# Binance WebSocket URL
BINANCE_WEBSOCKET_URL = "wss://stream.binance.com:9443/ws/!ticker@arr"

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Email Configuration (Optional)
FROM_EMAIL = os.getenv("FROM_EMAIL")
TO_EMAIL = os.getenv("TO_EMAIL")

# Telegram Configuration (Optional)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Alerting Thresholds
VOLATILITY_THRESHOLD = 3.0  # 3% change