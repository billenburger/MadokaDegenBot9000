# Universal Trading Bot 🚀

A powerful, multi-exchange trading bot that monitors your futures positions and sends real-time notifications to Discord and/or Telegram. Built with CCXT for maximum exchange compatibility.

## ✨ Features

- **🏢 Multi-Exchange Support**: Works with 100+ exchanges via CCXT (Binance, OKX, Bybit, Kraken, MEXC, etc.)
- **📱 Dual Platform Notifications**: Send alerts to Discord AND/OR Telegram
- **📊 Real-time Position Tracking**: Monitor position changes, PnL, and performance metrics
- **📈 Advanced Analytics**: Track max profit, max drawdown, and trade duration
- **🔄 Smart Position Detection**: Detects new positions, DCA entries, and position closures
- **⚡ High Performance**: Async/await architecture for optimal performance
- **🛡️ Robust Error Handling**: Graceful handling of network issues and API errors
- **🔧 Easy Configuration**: Simple config file setup for any exchange

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Choose Your Exchange

Use the exchange info tool to see supported exchanges:

```bash
python exchange_info.py --list
```

Test your exchange connection:

```bash
python exchange_info.py --test binance --api-key YOUR_KEY --secret YOUR_SECRET
```

### 3. Configure the Bot

Copy the configuration template:

```bash
cp config_example.py config.py
```

Edit `config.py` with your settings:

```python
CONFIG = {
    # Exchange Configuration
    "exchange": {
        "id": "binance",  # Your exchange ID
        "name": "Binance",
        "api_key": "your_api_key",
        "secret_key": "your_secret_key",
        "sandbox": False,
    },
    
    # Discord (Optional)
    "discord": {
        "enabled": True,
        "bot_token": "your_discord_bot_token",
        "servers": [
            {
                "name": "My Server",
                "channel_id": "123456789",
                "role_id": "987654321"
            }
        ]
    },
    
    # Telegram (Optional)
    "telegram": {
        "enabled": True,
        "bot_token": "your_telegram_bot_token",
        "chats": [
            {
                "name": "My Chat",
                "chat_id": "-1001234567890"
            }
        ]
    },
    
    "monitoring_interval": 10,
}
```

### 4. Run the Bot

```bash
python trading_bot.py
```

## 🏢 Supported Exchanges

The bot supports **100+ exchanges** through CCXT. Popular ones include:

| Exchange | Futures | Spot | API Required |
|----------|---------|------|--------------|
| Binance | ✅ | ✅ | API Key + Secret |
| OKX | ✅ | ✅ | API Key + Secret + Passphrase |
| Bybit | ✅ | ✅ | API Key + Secret |
| Kraken | ✅ | ✅ | API Key + Secret |
| MEXC | ✅ | ✅ | API Key + Secret |
| Bitget | ✅ | ✅ | API Key + Secret |
| KuCoin | ✅ | ✅ | API Key + Secret + Passphrase |

[See full list with `python exchange_info.py --list`]

## 📱 Platform Setup

### Discord Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Copy the bot token
4. Invite bot to your server with "Send Messages" permission
5. Get Channel ID: Right-click channel → Copy ID
6. Get Role ID: Right-click role → Copy ID

### Telegram Setup

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token
4. Add bot to your group/channel
5. Get Chat ID: Forward a message to [@userinfobot](https://t.me/userinfobot)

## 🔧 Configuration Options

### Exchange Configuration

```python
"exchange": {
    "id": "binance",          # CCXT exchange identifier
    "name": "Binance",        # Display name
    "api_key": "...",         # Your API key
    "secret_key": "...",      # Your secret key
    "passphrase": "...",      # Required for OKX, KuCoin, etc.
    "sandbox": False,         # Set True for testnet
}
```

## 🎮 Bot Commands

While the bot is running, you can use these terminal commands:

- `status` - Show bot status and active positions
- `restart` - Restart the bot gracefully
- `stop` - Stop the bot

## 📁 File Structure

```
MadokaDegenBot9000/
├── trading_bot.py           # Main bot file
├── config_example.py        # Configuration template
├── exchange_info.py         # Exchange information tool
├── setup_helper.py          # Interactive setup helper
├── requirements.txt         # Dependencies
├── QUICKSTART.md           # Quick start guide
└── README.md               # This file
```

## ⚠️ Important Notes

### Security
- **Never commit `config.py`** - it contains sensitive credentials
- Use **read-only API keys** when possible
- Enable **IP restrictions** on your exchange API keys

### API Permissions Required
Most exchanges need these permissions:
- ✅ **Read** - View account info, positions, balances
- ❌ **Trade** - Not needed (we only monitor)
- ❌ **Withdraw** - Never enable this

## 📈 Performance Tips

1. **Optimize Monitoring Interval**: 
   - Active trading: 5-10 seconds
   - Swing trading: 30-60 seconds

2. **Use Multiple Platforms**: Enable both Discord and Telegram for redundancy

3. **Monitor Resources**: The bot uses minimal CPU and memory

## 🐛 Troubleshooting

### Common Issues

**❌ "Exchange not found"**
- Check exchange ID with `python exchange_info.py --list`
- Ensure CCXT supports your exchange

**❌ "Authentication failed"** 
- Verify API credentials in config.py
- Check API permissions on exchange
- Test with `python exchange_info.py --test EXCHANGE`

**❌ "No positions found"**
- Ensure you have active futures positions
- Check if exchange requires special position endpoint access

## 📄 License

This project is licensed under the MIT License - see the [license_mit.txt](license_mit.txt) file for details.

## 🙏 Acknowledgments

- [CCXT](https://github.com/ccxt/ccxt) - Cryptocurrency exchange library
- [Discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API

---

**⚠️ Disclaimer**: This bot is for monitoring purposes only. Always verify trades independently. The authors are not responsible for any trading losses.

## 🆕 What's New in v2

- **🔄 Universal Exchange Support**: Upgraded from MEXC-only to 100+ exchanges via CCXT
- **📱 Telegram Integration**: Added Telegram notifications alongside Discord
- **🛠️ Enhanced Tools**: Interactive setup helper and exchange explorer
- **📊 Better Position Tracking**: Improved field mapping for all exchange types
- **⚡ Modern Architecture**: Async/await with robust error handling