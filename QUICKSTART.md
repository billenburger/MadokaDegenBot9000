# Quick Start Guide 🚀

## 1. Install Dependencies
```bash
pip install -r requirements.txt
```

Or use the helper:
```bash
python setup_helper.py --install
```

## 2. Interactive Setup
```bash
python setup_helper.py --setup
```

This will guide you through:
- ✅ Exchange selection and API setup
- ✅ Discord bot configuration (optional)
- ✅ Telegram bot configuration (optional)
- ✅ Bot settings configuration

## 3. Test Configuration
```bash
python setup_helper.py --test
```

## 4. Run the Bot
```bash
python trading_bot.py
```

## 🔧 Manual Configuration

If you prefer manual setup, copy the config template:
```bash
cp config_universal_example.py config.py
```

Then edit `config.py` with your settings.

## 📚 Need Help?

- **List exchanges**: `python exchange_info.py --list`
- **Test exchange**: `python exchange_info.py --test binance`
- **Exchange details**: `python exchange_info.py --info binance`

## 🏃‍♂️ Super Quick Start (Existing MEXC Users)

If you're migrating from the original MEXC bot:

```bash
# 1. Install new dependencies
pip install ccxt python-telegram-bot

# 2. Quick config for MEXC
python setup_helper.py --setup

# 3. Choose MEXC as exchange, enter your existing API keys

# 4. Run new bot
python trading_bot.py
```

Done! Your MEXC bot now works with the universal system and supports Telegram too! 🎉