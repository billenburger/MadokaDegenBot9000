"""
Configuration Example for MEXC Trading Bot

Copy this file to config.py and fill in your actual values.
DO NOT commit config.py to version control - it contains sensitive information!
"""

CONFIG = {
    # MEXC API Configuration
    "mexc": {
        "api_key": "your_mexc_api_key_here",
        "secret_key": "your_mexc_secret_key_here"
    },
    
    # Discord Configuration
    "discord": {
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
    
    # Bot Settings
    "monitoring_interval": 10,  # Seconds between position checks
}

"""
Setup Instructions:

1. MEXC API Setup:
   - Go to MEXC Futures (https://contract.mexc.com/)
   - Create API keys with futures trading permissions
   - Copy your API Key and Secret Key

2. Discord Bot Setup:
   - Go to https://discord.com/developers/applications
   - Create a new application and bot
   - Copy the bot token
   - Invite the bot to your server with 'Send Messages' permission

3. Discord IDs:
   - Enable Developer Mode in Discord settings
   - Right-click on your channel → Copy ID
   - Right-click on your role → Copy ID

4. Configuration:
   - Copy this file to config.py
   - Fill in all your actual values
   - Never commit config.py to git!
"""
