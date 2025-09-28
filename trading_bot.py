"""
Universal Trading Bot - Multi-Exchange Position Tracker
Monitors futures positions on any CCXT-supported exchange and sends notifications to Discord and/or Telegram.
"""

import asyncio
import discord
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Optional, Union
import aiohttp
import logging
import ccxt.async_support as ccxt
from telegram import Bot
from telegram.error import TelegramError

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UniversalTradingBot:
    """
    Universal Trading Bot for Discord and Telegram notifications
    
    Features:
    - CCXT integration for multiple exchanges
    - Real-time position monitoring
    - Beautiful Discord and Telegram message formatting  
    - Multiple server/channel support with role tagging
    - Position tracking with PnL calculations
    - Performance metrics (max profit/drawdown)
    - Graceful shutdown and restart functionality
    """
    
    def __init__(self, config: Dict):
        """Initialize the bot with configuration"""
        self.config = config
        self.exchange_config = config['exchange']
        self.discord_config = config.get('discord', {})
        self.telegram_config = config.get('telegram', {})
        self.monitoring_interval = config.get('monitoring_interval', 10)
        
        # Initialize tracking dictionaries
        self.current_positions: Dict[str, dict] = {}
        self.position_extremes: Dict[str, tuple] = {}
        self.position_start_times: Dict[str, int] = {}
        
        # Control flags
        self.should_restart = False
        self.should_stop = False
        
        # Initialize exchange
        self.exchange = None
        self.init_exchange()
        
        # Initialize Discord client if configured
        self.discord_client = None
        if self.discord_config.get('enabled', False):
            self.init_discord()
        
        # Initialize Telegram bot if configured
        self.telegram_bot = None
        if self.telegram_config.get('enabled', False):
            self.init_telegram()
        
        logger.info(f"Bot initialized successfully for {self.exchange_config['name']} exchange")
    
    def init_exchange(self):
        """Initialize CCXT exchange connection"""
        try:
            exchange_id = self.exchange_config['id']
            
            # Get the exchange class
            if not hasattr(ccxt, exchange_id):
                raise ValueError(f"Exchange '{exchange_id}' not supported by CCXT")
            
            exchange_class = getattr(ccxt, exchange_id)
            
            # Initialize exchange with credentials
            self.exchange = exchange_class({
                'apiKey': self.exchange_config['api_key'],
                'secret': self.exchange_config['secret_key'],
                'password': self.exchange_config.get('passphrase', ''),  # For some exchanges like OKX
                'sandbox': self.exchange_config.get('sandbox', False),
                'enableRateLimit': True,
            })
            
            # Set to futures/derivatives market if available
            if hasattr(self.exchange, 'set_sandbox_mode'):
                self.exchange.set_sandbox_mode(self.exchange_config.get('sandbox', False))
            
            logger.info(f"Exchange {exchange_id} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            sys.exit(1)
    
    def init_discord(self):
        """Initialize Discord client"""
        try:
            intents = discord.Intents.default()
            intents.presences = False
            intents.members = False
            intents.message_content = False
            self.discord_client = discord.Client(intents=intents)
            logger.info("Discord client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Discord: {e}")
    
    def init_telegram(self):
        """Initialize Telegram bot"""
        try:
            self.telegram_bot = Bot(token=self.telegram_config['bot_token'])
            logger.info("Telegram bot initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram: {e}")
    
    def start_command_listener(self, loop: asyncio.AbstractEventLoop) -> None:
        """Start terminal command listener in separate thread"""
        import threading
        
        def command_listener():
            """Listen for terminal commands"""
            print("Bot is running. Commands: 'restart', 'stop', 'status'")
            while not self.should_stop:
                try:
                    command = input().strip().lower()
                    
                    if command == 'restart':
                        print("Restarting bot...")
                        self.should_restart = True
                        self.should_stop = True
                        asyncio.run_coroutine_threadsafe(self.graceful_shutdown(), loop)
                        break
                    elif command == 'stop':
                        print("Stopping bot...")
                        self.should_stop = True
                        asyncio.run_coroutine_threadsafe(self.graceful_shutdown(), loop)
                        break
                    elif command == 'status':
                        print(f"Active positions: {len(self.current_positions)}")
                        print(f"Bot status: Running")
                        print(f"Exchange: {self.exchange_config['name']}")
                        print(f"Monitoring interval: {self.monitoring_interval}s")
                        if self.discord_config.get('enabled'):
                            print(f"Discord servers: {len(self.discord_config.get('servers', []))}")
                        if self.telegram_config.get('enabled'):
                            print(f"Telegram chats: {len(self.telegram_config.get('chats', []))}")
                    else:
                        print("Unknown command. Available: restart, stop, status")
                        
                except (EOFError, KeyboardInterrupt):
                    self.should_stop = True
                    asyncio.run_coroutine_threadsafe(self.graceful_shutdown(), loop)
                    break
                except Exception as e:
                    logger.error(f"Command error: {e}")
        
        # Start command listener in daemon thread
        command_thread = threading.Thread(target=command_listener, daemon=True)
        command_thread.start()
    
    async def graceful_shutdown(self) -> None:
        """Gracefully shutdown the bot with proper cleanup"""
        try:
            logger.info("Starting graceful shutdown...")
            
            # Allow pending operations to complete
            await asyncio.sleep(0.5)
            
            # Close exchange connection
            if self.exchange:
                await self.exchange.close()
            
            # Close Discord client
            if self.discord_client and not self.discord_client.is_closed():
                await self.discord_client.close()
                
            # Final cleanup delay
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def get_positions(self) -> Optional[List[Dict]]:
        """Get current futures positions from exchange"""
        try:
            # Load markets if not already loaded
            if not self.exchange.markets:
                await self.exchange.load_markets()
            
            # Set exchange to derivatives/futures mode if supported
            if hasattr(self.exchange, 'options'):
                self.exchange.options['defaultType'] = 'swap'  # or 'future' for some exchanges
            
            # Fetch positions (method varies by exchange)
            positions = await self.exchange.fetch_positions()
            
            # Filter out closed positions (size = 0)
            active_positions = []
            for position in positions:
                # Check different size fields that might be used
                size = position.get('size', 0) or position.get('contracts', 0)
                if size != 0 and position.get('side') is not None:  # Position size not zero and has side
                    active_positions.append(position)
            
            return active_positions
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return None
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return float(ticker['last'] or ticker['close'] or 0)
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0
    
    @staticmethod
    def format_duration(start_time: int, end_time: int) -> str:
        """Format duration between two timestamps"""
        try:
            duration_seconds = (end_time - start_time) / 1000
            
            if duration_seconds < 60:
                return f"{int(duration_seconds)}s"
            elif duration_seconds < 3600:
                minutes = int(duration_seconds / 60)
                seconds = int(duration_seconds % 60)
                return f"{minutes}m {seconds}s"
            else:
                hours = int(duration_seconds / 3600)
                minutes = int((duration_seconds % 3600) / 60)
                return f"{hours}h {minutes}m"
        except Exception:
            return "Unknown"
    
    def calculate_pnl_percentage(self, position: Dict) -> float:
        """Calculate PnL percentage from CCXT position data"""
        try:
            # Try the unified percentage field first
            if 'percentage' in position and position['percentage'] is not None:
                return float(position['percentage'])
            
            # Fallback: calculate from unrealizedPnl and notional
            if 'unrealizedPnl' in position and 'notional' in position:
                pnl = float(position['unrealizedPnl'] or 0)
                notional = float(position['notional'] or 0)
                if notional > 0:
                    return (pnl / notional) * 100
            
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating PnL: {e}")
            return 0.0
    
    def _position_size_changed(self, old_position: Dict, new_position: Dict) -> bool:
        """Check if position size has changed"""
        try:
            old_size = old_position.get('size', 0) or old_position.get('contracts', 0)
            new_size = new_position.get('size', 0) or new_position.get('contracts', 0)
            return abs(float(old_size or 0)) != abs(float(new_size or 0))
        except Exception:
            return False
    
    def format_discord_message(self, position: Dict, trade_type: str, role_id: str) -> str:
        """Format trade information for Discord with modern styling"""
        try:
            symbol = position.get('symbol', 'UNKNOWN')
            side = position.get('side', 'unknown').upper()
            
            entry_price = float(position.get('entryPrice') or position.get('avgPrice', 0))
            current_price = float(position.get('markPrice') or position.get('lastPrice', 0))
            
            # Get leverage - try different possible fields
            leverage = 1
            if 'leverage' in position and position['leverage']:
                leverage = float(position['leverage'])
            elif 'initialMarginPercentage' in position and position['initialMarginPercentage']:
                leverage = round(100 / float(position['initialMarginPercentage']))
            
            pnl_pct = self.calculate_pnl_percentage(position)
            
            # Dynamic emojis based on trade type
            if "NEW" in trade_type.upper():
                header_emoji = "🚀"
                accent_color = "🟢" if side == "LONG" else "🔴"
            elif "DCA" in trade_type.upper() or "INCREASED" in trade_type.upper():
                header_emoji = "📈"
                accent_color = "🔵"
            elif "REDUCED" in trade_type.upper():
                header_emoji = "📉"
                accent_color = "🟡"
            else:
                header_emoji = "📋"
                accent_color = "⚪"
            
            pnl_emoji = "🟢" if pnl_pct > 0 else "🔴" if pnl_pct < 0 else "🟡"
            
            # Build message with modern Discord formatting
            message = f"<@&{role_id}>\n\n"
            message += f"## {header_emoji} **{trade_type}**\n\n"
            message += f"{accent_color} **{symbol}** • **{side}** ({leverage}x)\n\n"
            message += f"**💰 Entry Price:** `${entry_price:.4f}`\n"
            message += f"**📈 Current Price:** `${current_price:.4f}`\n"
            message += f"**{pnl_emoji} PnL:** `{pnl_pct:+.2f}%`\n\n"
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting Discord message: {e}")
            return f"❌ Error formatting trade data for {position.get('symbol', 'UNKNOWN')}"
    
    def format_telegram_message(self, position: Dict, trade_type: str) -> str:
        """Format trade information for Telegram"""
        try:
            symbol = position.get('symbol', 'UNKNOWN')
            side = position.get('side', 'unknown').upper()
            
            entry_price = float(position.get('entryPrice') or position.get('avgPrice', 0))
            current_price = float(position.get('markPrice') or position.get('lastPrice', 0))
            
            # Get leverage - try different possible fields
            leverage = 1
            if 'leverage' in position and position['leverage']:
                leverage = float(position['leverage'])
            elif 'initialMarginPercentage' in position and position['initialMarginPercentage']:
                leverage = round(100 / float(position['initialMarginPercentage']))
                
            pnl_pct = self.calculate_pnl_percentage(position)
            
            # Emojis for Telegram
            if "NEW" in trade_type.upper():
                header_emoji = "🚀"
            elif "DCA" in trade_type.upper() or "INCREASED" in trade_type.upper():
                header_emoji = "📈"
            elif "REDUCED" in trade_type.upper():
                header_emoji = "📉"
            else:
                header_emoji = "📋"
            
            pnl_emoji = "🟢" if pnl_pct > 0 else "🔴" if pnl_pct < 0 else "🟡"
            
            # Build Telegram message
            message = f"{header_emoji} <b>{trade_type}</b>\n\n"
            message += f"<b>{symbol}</b> • <b>{side}</b> ({leverage}x)\n\n"
            message += f"💰 Entry: <code>${entry_price:.4f}</code>\n"
            message += f"📈 Current: <code>${current_price:.4f}</code>\n"
            message += f"{pnl_emoji} PnL: <code>{pnl_pct:+.2f}%</code>\n\n"
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting Telegram message: {e}")
            return f"❌ Error formatting trade data for {position.get('symbol', 'UNKNOWN')}"
    
    async def send_discord_notifications(self, message_template: str, position: Optional[Dict] = None, trade_type: str = "") -> None:
        """Send notifications to all configured Discord servers"""
        if not self.discord_client or not self.discord_config.get('enabled'):
            return
        
        for server in self.discord_config.get('servers', []):
            try:
                if position:
                    # For trade messages, format with server's role
                    message = self.format_discord_message(position, trade_type, server['role_id'])
                else:
                    # For close messages, substitute role placeholder
                    message = message_template.replace("ROLE_PLACEHOLDER", server['role_id'])
                
                channel = self.discord_client.get_channel(int(server['channel_id']))
                if channel:
                    await channel.send(message)
                    logger.info(f"Discord message sent to {server.get('name', 'Unknown server')}")
                else:
                    logger.error(f"Discord channel not found for server: {server.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error sending Discord message to server {server.get('name', 'Unknown')}: {e}")
    
    async def send_telegram_notifications(self, message_template: str, position: Optional[Dict] = None, trade_type: str = "") -> None:
        """Send notifications to all configured Telegram chats"""
        if not self.telegram_bot or not self.telegram_config.get('enabled'):
            return
        
        for chat in self.telegram_config.get('chats', []):
            try:
                if position:
                    message = self.format_telegram_message(position, trade_type)
                else:
                    message = message_template
                
                await self.telegram_bot.send_message(
                    chat_id=chat['chat_id'], 
                    text=message, 
                    parse_mode='HTML'
                )
                logger.info(f"Telegram message sent to {chat.get('name', 'Unknown chat')}")
            except TelegramError as e:
                logger.error(f"Telegram error for chat {chat.get('name', 'Unknown')}: {e}")
            except Exception as e:
                logger.error(f"Error sending Telegram message to chat {chat.get('name', 'Unknown')}: {e}")
    
    async def send_notifications(self, message_template: str = "", position: Optional[Dict] = None, trade_type: str = "") -> None:
        """Send notifications to all configured platforms"""
        # Send to Discord
        await self.send_discord_notifications(message_template, position, trade_type)
        
        # Send to Telegram  
        await self.send_telegram_notifications(message_template, position, trade_type)
    
    async def check_positions(self) -> None:
        """Check for position changes and send notifications"""
        try:
            positions = await self.get_positions()
            
            if positions is None:
                logger.warning("No position data received from exchange")
                return
            
            current_positions = {}
            
            # Process active positions
            for position in positions:
                symbol = position.get('symbol')
                
                current_pnl = self.calculate_pnl_percentage(position)
                current_positions[symbol] = position
                
                # Track PnL extremes
                if symbol not in self.position_extremes:
                    self.position_extremes[symbol] = (current_pnl, current_pnl)
                else:
                    max_profit, max_drawdown = self.position_extremes[symbol]
                    new_max_profit = max(max_profit, current_pnl)
                    new_max_drawdown = min(max_drawdown, current_pnl)
                    self.position_extremes[symbol] = (new_max_profit, new_max_drawdown)
                
                # Check for new positions
                if symbol not in self.current_positions:
                    self.position_start_times[symbol] = int(time.time() * 1000)
                    await self.send_notifications("", position, "NEW POSITION")
                    logger.info(f"New position detected: {symbol}")
                
                # Check for position updates (size changes)
                elif self._position_size_changed(self.current_positions[symbol], position):
                    old_size = abs(float(self.current_positions[symbol].get('size', 0) or self.current_positions[symbol].get('contracts', 0)))
                    new_size = abs(float(position.get('size', 0) or position.get('contracts', 0)))
                    
                    if new_size > old_size:
                        trade_type = "POSITION INCREASED (DCA)"
                    elif new_size < old_size:
                        trade_type = "POSITION REDUCED"
                    else:
                        trade_type = "POSITION UPDATED"
                    
                    await self.send_notifications("", position, trade_type)
                    logger.info(f"Position updated: {symbol} - {trade_type}")
            
            # Check for closed positions
            for symbol in list(self.current_positions.keys()):
                if symbol not in current_positions:
                    await self._handle_position_closure(symbol)
            
            self.current_positions = current_positions
            
        except Exception as e:
            logger.error(f"Error checking positions: {e}")
    
    async def _handle_position_closure(self, symbol: str) -> None:
        """Handle position closure and send notification"""
        try:
            last_position = self.current_positions[symbol]
            
            # Calculate trade duration
            start_time = self.position_start_times.get(symbol, int(time.time() * 1000))
            end_time = int(time.time() * 1000)
            duration = self.format_duration(start_time, end_time)
            
            # Get final PnL
            final_pnl_pct = self.calculate_pnl_percentage(last_position)
            max_profit, max_drawdown = self.position_extremes.get(symbol, (final_pnl_pct, final_pnl_pct))
            
            # Check if bot was offline during position opening
            offline_note = ""
            if symbol not in self.position_start_times:
                offline_note = "\n⚠️ *Bot was offline during close*"
            
            # Format close message for Discord
            status_emoji = "🎉" if final_pnl_pct > 0 else "💔" if final_pnl_pct < 0 else "😐"
            result_emoji = "🟢" if final_pnl_pct > 0 else "🔴" if final_pnl_pct < 0 else "🟡"
            
            discord_message = f"<@&ROLE_PLACEHOLDER>\n\n"
            discord_message += f"## 🔒 **POSITION CLOSED** {status_emoji}\n\n"
            discord_message += f"{result_emoji} **{symbol}** • Final Result: **{final_pnl_pct:+.2f}%**\n\n"
            discord_message += f"**📊 Performance Summary:**\n"
            discord_message += f"• **Max Profit:** `{max_profit:+.2f}%`\n"
            discord_message += f"• **Max Drawdown:** `{max_drawdown:+.2f}%`\n"
            discord_message += f"• **Duration:** `{duration}`\n\n"
            discord_message += f"⏰ Closed at {datetime.now().strftime('%H:%M:%S')}"
            discord_message += offline_note
            
            # Format close message for Telegram
            telegram_message = f"🔒 <b>POSITION CLOSED</b> {status_emoji}\n\n"
            telegram_message += f"{result_emoji} <b>{symbol}</b> • Final: <b>{final_pnl_pct:+.2f}%</b>\n\n"
            telegram_message += f"📊 <b>Performance:</b>\n"
            telegram_message += f"• Max Profit: <code>{max_profit:+.2f}%</code>\n"
            telegram_message += f"• Max Drawdown: <code>{max_drawdown:+.2f}%</code>\n"
            telegram_message += f"• Duration: <code>{duration}</code>\n\n"
            telegram_message += f"⏰ Closed at {datetime.now().strftime('%H:%M:%S')}"
            telegram_message += offline_note.replace("*", "<i>").replace("*", "</i>") if offline_note else ""
            
            # Send Discord notification
            await self.send_discord_notifications(discord_message)
            
            # Send Telegram notification
            await self.send_telegram_notifications(telegram_message)
            
            logger.info(f"Position closed: {symbol} - Duration: {duration}, Final PnL: {final_pnl_pct:+.2f}%")
            
            # Clean up tracking data
            self.position_extremes.pop(symbol, None)
            self.position_start_times.pop(symbol, None)
            
        except Exception as e:
            logger.error(f"Error handling position closure for {symbol}: {e}")
    
    async def monitoring_loop(self) -> None:
        """Main monitoring loop"""
        logger.info("Starting position monitoring...")
        
        while not self.should_stop:
            try:
                await self.check_positions()
                await asyncio.sleep(self.monitoring_interval)
                
                if self.should_stop:
                    logger.info("Monitoring loop stopping...")
                    break
                    
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Wait longer on errors
    
    async def start_bot(self) -> None:
        """Start the bot"""
        # Set up Discord event handlers if Discord is enabled
        if self.discord_client and self.discord_config.get('enabled'):
            @self.discord_client.event
            async def on_ready():
                logger.info(f'Discord bot logged in as {self.discord_client.user}')
        
        # Start command listener
        loop = asyncio.get_event_loop()
        self.start_command_listener(loop)
        
        # Send startup notification
        startup_time = datetime.now().strftime('%H:%M:%S')
        
        # Discord startup message
        discord_startup = "## 🤖 **UNIVERSAL TRADING BOT ONLINE**\n\n"
        discord_startup += "✅ **Connected & Ready**\n\n"
        discord_startup += f"• **Exchange:** {self.exchange_config['name']}\n"
        discord_startup += "• **Discord:** Notifications active\n" if self.discord_config.get('enabled') else ""
        discord_startup += "• **Telegram:** Notifications active\n" if self.telegram_config.get('enabled') else ""
        discord_startup += "• **Status:** Monitoring positions\n"
        discord_startup += f"• **Started:** {startup_time}\n\n"
        discord_startup += "🚀 **Ready to track your trades!**"
        
        # Telegram startup message
        telegram_startup = f"🤖 <b>UNIVERSAL TRADING BOT ONLINE</b>\n\n"
        telegram_startup += f"✅ <b>Connected & Ready</b>\n\n"
        telegram_startup += f"• <b>Exchange:</b> {self.exchange_config['name']}\n"
        telegram_startup += f"• <b>Status:</b> Monitoring positions\n"
        telegram_startup += f"• <b>Started:</b> {startup_time}\n\n"
        telegram_startup += f"🚀 <b>Ready to track your trades!</b>"
        
        # Send startup notifications
        await self.send_discord_notifications(discord_startup)
        await self.send_telegram_notifications(telegram_startup)
        
        # Start Discord client if enabled
        if self.discord_client and self.discord_config.get('enabled'):
            # Start Discord in background
            asyncio.create_task(self.discord_client.start(self.discord_config['bot_token']))
        
        # Start position monitoring
        await self.monitoring_loop()


def load_config() -> Dict:
    """Load configuration from config.py"""
    try:
        from config import CONFIG
        logger.info("Configuration loaded from config.py")
        return CONFIG
    except ImportError:
        logger.error("config.py not found! Please create config.py with your settings.")
        logger.error("See config_example.py for the required format.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)


async def main():
    """Main application entry point"""
    config = load_config()
    
    # Validate configuration
    required_keys = ['exchange']
    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required configuration section: {key}")
            sys.exit(1)
    
    while True:  # Restart loop
        bot = UniversalTradingBot(config)
        
        try:
            await bot.start_bot()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user (Ctrl+C)")
            break
        except Exception as e:
            logger.error(f"Bot error: {e}")
        
        # Handle restart requests
        if bot.should_restart:
            logger.info("Restarting bot in 2 seconds...")
            await asyncio.sleep(2)
            continue
        else:
            logger.info("Bot stopped")
            break


if __name__ == "__main__":
    try:
        print("=" * 60)
        print("Universal Trading Bot - Multi-Exchange Position Tracker")
        print("Commands: 'restart', 'stop', 'status'")
        print("=" * 60)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
    finally:
        print("Bot shut down.")