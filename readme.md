# MEXC Trading Bot - Discord Position Tracker

A Python bot that monitors your MEXC futures positions and sends beautiful, real-time notifications to Discord channels with role pinging support.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-2.3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- **Real-time Position Monitoring** - Tracks your MEXC futures positions every 10 seconds
- **Beautiful Discord Notifications** - Modern formatted messages with emojis and styling
- **Multiple Server Support** - Send notifications to multiple Discord servers
- **Role Pinging** - Tag specific roles when positions open/close
- **Performance Tracking** - Monitors max profit, max drawdown, and trade duration
- **PnL Calculations** - Real-time profit/loss calculations with leverage
- **Graceful Shutdown** - Clean restart and stop functionality
- **Comprehensive Logging** - File and console logging for debugging

## Message Examples

### New Position
```
@TradingRole

## 🚀 **NEW POSITION**

🟢 **BTC_USDT** • **LONG** (10x)

**💰 Entry Price:** `$45234.5678`
**📈 Current Price:** `$46123.4567`
**🟢 PnL:** `+4.92%`

⏰ 14:35:22
```

### Position Closed
```
@TradingRole

## 🔒 **POSITION CLOSED** 🎉

🟢 **BTC_USDT** • Final Result: **+12.45%**

**📊 Performance Summary:**
• **Max Profit:** `+15.67%`
• **Max Drawdown:** `-2.34%`
• **Duration:** `2h 34m`

⏰ Closed at 16:45:33
```

## Requirements

- Python 3.8+
- MEXC Futures account with API access
- Discord bot with channel permissions

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mexc-trading-bot.git
   cd mexc-trading-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration**
   ```bash
   cp config_example.py config.py
   ```
   Edit `config.py` with your API keys and Discord settings.

## Configuration

### MEXC API Setup
1. Go to [MEXC Futures](https://contract.mexc.com/)
2. Navigate to API Management
3. Create new API keys with futures trading permissions
4. Copy your API Key and Secret Key

### Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Copy the bot token
4. Invite the bot to your server with "Send Messages" permission
5. Enable Developer Mode in Discord to get channel and role IDs

### Configuration File
Edit `config.py`:

```python
CONFIG = {
    "mexc": {
        "api_key": "your_mexc_api_key",
        "secret_key": "your_mexc_secret_key"
    },
    "discord": {
        "bot_token": "your_discord_bot_token",
        "servers": [
            {
                "name": "My Trading Server",
                "channel_id": "123456789012345678",
                "role_id": "