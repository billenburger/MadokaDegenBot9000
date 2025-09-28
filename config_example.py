"""
Configuration Example for Universal Trading Bot

Copy this file to config.py and fill in your actual values.
DO NOT commit config.py to version control - it contains sensitive information!

Supports ANY exchange that CCXT supports: Binance, OKX, Bybit, Kraken, Coinbase, etc.
"""

CONFIG = {
    # Exchange Configuration (CCXT)
    "exchange": {
        "id": "binance",  # CCXT exchange ID: binance, okx, bybit, kraken, etc.
        "name": "Binance",  # Display name
        "api_key": "your_api_key_here",
        "secret_key": "your_secret_key_here",
        "passphrase": "",  # Required for some exchanges like OKX
        "sandbox": False,  # Set to True for testnet/sandbox
    },
    
    # Discord Configuration (Optional)
    "discord": {
        "enabled": True,  # Set to False to disable Discord notifications
        "bot_token": "your_discord_bot_token_here",
        "servers": [
            {
                "name": "My Trading Server",
                "channel_id": "123456789012345678",  # Discord channel ID
                "role_id": "123456789012345678"      # Discord role ID to ping
            },
            # Add more servers as needed
            # {
            #     "name": "Another Server",
            #     "channel_id": "987654321098765432",
            #     "role_id": "987654321098765432"
            # }
        ]
    },
    
    # Telegram Configuration (Optional)
    "telegram": {
        "enabled": True,  # Set to False to disable Telegram notifications
        "bot_token": "your_telegram_bot_token_here",  # Get from @BotFather
        "chats": [
            {
                "name": "My Trading Chat",
                "chat_id": "-1001234567890"  # Group chat ID (negative for groups)
            },
            # Add more chats as needed
            # {
            #     "name": "Private Chat",
            #     "chat_id": "123456789"  # User ID (positive for private chats)
            # }
        ]
    },
    
    # Bot Settings
    "monitoring_interval": 10,  # Seconds between position checks
}

"""
Supported Exchanges (via CCXT):
- binance, binanceus, binancecoinm, binanceusdm
- okx (formerly okex)
- bybit
- kraken, krakenspot, krakenfutures
- coinbasepro, coinbaseadvanced
- mexc
- bitget
- kucoin, kucoinfutures
- huobi, huobipro
- gate, gateio
- bitfinex, bitfinex2
- bitmex
- deribit
- And 100+ more exchanges!

Setup Instructions:

1. Exchange API Setup:
   - Go to your exchange's API settings
   - Create API keys with futures/derivatives trading permissions (read-only is fine)
   - For some exchanges, enable "Read" permissions for positions and orders
   - Copy your API Key and Secret Key
   - For OKX: Also copy the Passphrase

2. Discord Bot Setup (Optional):
   - Go to https://discord.com/developers/applications
   - Create a new application and bot
   - Copy the bot token
   - Invite the bot to your server with 'Send Messages' permission
   - Get channel ID: Right-click channel → Copy ID
   - Get role ID: Right-click role → Copy ID

3. Telegram Bot Setup (Optional):
   - Message @BotFather on Telegram
   - Create a new bot with /newbot
   - Copy the bot token
   - Add the bot to your group/channel
   - Get chat ID: Forward a message from the chat to @userinfobot

4. Configuration:
   - Copy this file to config.py
   - Choose your exchange from the list above
   - Fill in all your actual values
   - Enable/disable Discord and Telegram as needed
   - Never commit config.py to git!

Example Exchange Configurations:

# Binance
"exchange": {
    "id": "binance",
    "name": "Binance",
    "api_key": "your_binance_api_key",
    "secret_key": "your_binance_secret_key",
    "sandbox": False,
},

# OKX
"exchange": {
    "id": "okx",
    "name": "OKX",
    "api_key": "your_okx_api_key",
    "secret_key": "your_okx_secret_key",
    "passphrase": "your_okx_passphrase",
    "sandbox": False,
},

# Bybit
"exchange": {
    "id": "bybit",
    "name": "Bybit",
    "api_key": "your_bybit_api_key",
    "secret_key": "your_bybit_secret_key",
    "sandbox": False,
},

# Your original MEXC
"exchange": {
    "id": "mexc",
    "name": "MEXC",
    "api_key": "your_mexc_api_key",
    "secret_key": "your_mexc_secret_key",
    "sandbox": False,
},
"""