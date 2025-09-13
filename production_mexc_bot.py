"""
MEXC Trading Bot - Discord Position Tracker
Monitors MEXC futures positions and sends formatted notifications to Discord channels.
"""

import asyncio
import discord
import hashlib
import hmac
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mexc_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MEXCTradingBot:
    """
    MEXC Trading Bot for Discord notifications
    
    Features:
    - Real-time position monitoring
    - Beautiful Discord message formatting  
    - Multiple server support with role tagging
    - Position tracking with PnL calculations
    - Performance metrics (max profit/drawdown)
    - Graceful shutdown and restart functionality
    """
    
    def __init__(self, config: Dict):
        """Initialize the bot with configuration"""
        self.config = config
        self.mexc_api_key = config['mexc']['api_key']
        self.mexc_secret_key = config['mexc']['secret_key']
        self.discord_token = config['discord']['bot_token']
        self.servers = config['discord']['servers']
        self.monitoring_interval = config.get('monitoring_interval', 10)
        self.base_url = "https://contract.mexc.com"
        
        # Initialize tracking dictionaries
        self.current_positions: Dict[str, dict] = {}
        self.position_extremes: Dict[str, tuple] = {}
        self.position_start_times: Dict[str, int] = {}
        
        # Control flags
        self.should_restart = False
        self.should_stop = False
        
        # Discord client setup
        intents = discord.Intents.default()
        intents.presences = False
        intents.members = False
        intents.message_content = False
        self.client = discord.Client(intents=intents)
        
        logger.info("Bot initialized successfully")
    
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
                        print(f"Monitoring interval: {self.monitoring_interval}s")
                        print(f"Configured servers: {len(self.servers)}")
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
            
            # Close Discord client
            if not self.client.is_closed():
                await self.client.close()
                
            # Final cleanup delay
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def generate_signature(self, api_key: str, secret_key: str, req_time: str, param_string: str = "") -> str:
        """Generate MEXC futures API signature"""
        sign_string = api_key + req_time + param_string
        signature = hmac.new(
            secret_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def mexc_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to MEXC Futures API"""
        if params is None:
            params = {}
        
        req_time = str(int(time.time() * 1000))
        
        # Build parameter string
        if params:
            sorted_params = sorted(params.items())
            param_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        else:
            param_string = ""
        
        # Generate signature
        signature = self.generate_signature(
            self.mexc_api_key, 
            self.mexc_secret_key, 
            req_time, 
            param_string
        )
        
        # Prepare headers
        headers = {
            'ApiKey': self.mexc_api_key,
            'Request-Time': req_time,
            'Signature': signature,
            'Content-Type': 'application/json'
        }
        
        # Build URL
        url = f"{self.base_url}{endpoint}"
        if param_string:
            url += f"?{param_string}"
        
        # Make request with proper session cleanup
        session = None
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            session = aiohttp.ClientSession(timeout=timeout)
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"MEXC API call successful: {endpoint}")
                    return data
                else:
                    response_text = await response.text()
                    logger.error(f"MEXC API error: {response.status} - {response_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Request error for {endpoint}: {e}")
            return None
        finally:
            if session:
                await session.close()
    
    async def get_positions(self) -> Optional[Dict]:
        """Get current futures positions"""
        return await self.mexc_request("/api/v1/private/position/open_positions")
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        session = None
        try:
            url = f"https://contract.mexc.com/api/v1/contract/ticker"
            params = {'symbol': symbol}
            
            timeout = aiohttp.ClientTimeout(total=10)
            session = aiohttp.ClientSession(timeout=timeout)
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success') and data.get('data'):
                        return float(data['data'].get('lastPrice', 0))
            
            logger.warning(f"Could not get price for {symbol}")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0
        finally:
            if session:
                await session.close()
    
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
    
    def calculate_pnl_percentage(self, position: Dict, current_price: float = None) -> float:
        """Calculate PnL percentage using entry price vs current price"""
        try:
            entry_price = float(position.get('holdAvgPrice', 0))
            position_type = position.get('positionType', 1)
            leverage = float(position.get('leverage', 1))
            
            if entry_price == 0 or current_price is None or current_price == 0:
                return 0.0
            
            # Calculate price change percentage
            if position_type == 1:  # LONG position
                price_change_pct = ((current_price - entry_price) / entry_price) * 100
            else:  # SHORT position
                price_change_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Apply leverage
            pnl_percentage = price_change_pct * leverage
            return pnl_percentage
                
        except Exception as e:
            logger.error(f"Error calculating PnL: {e}")
            return 0.0
    
    def format_trade_message(self, position: Dict, current_price: float, trade_type: str, role_id: str) -> str:
        """Format trade information for Discord with modern styling"""
        try:
            symbol = position.get('symbol', 'UNKNOWN')
            position_type = position.get('positionType', 1)
            side = "LONG" if position_type == 1 else "SHORT"
            
            entry_price = float(position.get('holdAvgPrice', 0))
            leverage = int(float(position.get('leverage', 1)))
            pnl_pct = self.calculate_pnl_percentage(position, current_price)
            
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
            logger.error(f"Error formatting trade message: {e}")
            return f"❌ Error formatting trade data for {position.get('symbol', 'UNKNOWN')}"
    
    async def send_to_all_servers(self, message: str) -> None:
        """Send message to all configured Discord servers"""
        for server in self.servers:
            try:
                channel = self.client.get_channel(int(server['channel_id']))
                if channel:
                    await channel.send(message)
                    logger.info(f"Message sent to {server.get('name', 'Unknown server')}")
                else:
                    logger.error(f"Channel not found for server: {server.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error sending to server {server.get('name', 'Unknown')}: {e}")
    
    async def send_server_specific_message(
        self, 
        message_template: str, 
        position: Optional[Dict] = None, 
        current_price: Optional[float] = None, 
        trade_type: str = ""
    ) -> None:
        """Send customized message to each server with their role"""
        for server in self.servers:
            try:
                if position and current_price:
                    # For trade messages, format with server's role
                    message = self.format_trade_message(position, current_price, trade_type, server['role_id'])
                else:
                    # For close messages, substitute role placeholder
                    message = message_template.replace("ROLE_PLACEHOLDER", server['role_id'])
                
                channel = self.client.get_channel(int(server['channel_id']))
                if channel:
                    await channel.send(message)
                    logger.info(f"Message sent to {server.get('name', 'Unknown server')}")
                else:
                    logger.error(f"Channel not found for server: {server.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error sending to server {server.get('name', 'Unknown')}: {e}")
    
    async def check_positions(self) -> None:
        """Check for position changes and send Discord notifications"""
        try:
            positions_data = await self.get_positions()
            
            if not positions_data or 'data' not in positions_data:
                logger.warning("No position data received from MEXC")
                return
            
            current_positions = {}
            
            # Process active positions
            for position in positions_data['data']:
                symbol = position.get('symbol')
                hold_vol = float(position.get('holdVol', 0))
                
                # Skip positions with zero volume
                if hold_vol == 0:
                    continue
                
                current_price = await self.get_current_price(symbol)
                current_pnl = self.calculate_pnl_percentage(position, current_price)
                
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
                    await self.send_server_specific_message("", position, current_price, "NEW POSITION")
                    logger.info(f"New position detected: {symbol}")
                
                # Check for position updates
                elif self.current_positions[symbol] != position:
                    old_vol = float(self.current_positions[symbol].get('holdVol', 0))
                    new_vol = float(position.get('holdVol', 0))
                    
                    if abs(new_vol) > abs(old_vol):
                        trade_type = "POSITION INCREASED (DCA)"
                    elif abs(new_vol) < abs(old_vol):
                        trade_type = "POSITION REDUCED"
                    else:
                        trade_type = "POSITION UPDATED"
                    
                    await self.send_server_specific_message("", position, current_price, trade_type)
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
            
            # Get final price for PnL calculation
            final_price = await self.get_current_price(symbol)
            final_pnl_pct = self.calculate_pnl_percentage(last_position, final_price)
            
            max_profit, max_drawdown = self.position_extremes.get(symbol, (final_pnl_pct, final_pnl_pct))
            
            # Check if bot was offline during position opening
            offline_note = ""
            if symbol not in self.position_start_times:
                offline_note = "\n⚠️ *Bot was offline during close*"
            
            # Format close message
            status_emoji = "🎉" if final_pnl_pct > 0 else "💔" if final_pnl_pct < 0 else "😐"
            result_emoji = "🟢" if final_pnl_pct > 0 else "🔴" if final_pnl_pct < 0 else "🟡"
            
            message_template = f"<@&ROLE_PLACEHOLDER>\n\n"
            message_template += f"## 🔒 **POSITION CLOSED** {status_emoji}\n\n"
            message_template += f"{result_emoji} **{symbol}** • Final Result: **{final_pnl_pct:+.2f}%**\n\n"
            message_template += f"**📊 Performance Summary:**\n"
            message_template += f"• **Max Profit:** `{max_profit:+.2f}%`\n"
            message_template += f"• **Max Drawdown:** `{max_drawdown:+.2f}%`\n"
            message_template += f"• **Duration:** `{duration}`\n\n"
            message_template += f"⏰ Closed at {datetime.now().strftime('%H:%M:%S')}"
            message_template += offline_note
            
            await self.send_server_specific_message(message_template)
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
        """Start the Discord bot"""
        @self.client.event
        async def on_ready():
            logger.info(f'Discord bot logged in as {self.client.user}')
            
            # Start command listener
            loop = asyncio.get_event_loop()
            self.start_command_listener(loop)
            
            # Send startup notification
            if self.servers:
                startup_time = datetime.now().strftime('%H:%M:%S')
                startup_msg = "## 🤖 **MEXC TRADING BOT ONLINE**\n\n"
                startup_msg += "✅ **Connected & Ready**\n\n"
                startup_msg += "• **API:** Connected to MEXC\n"
                startup_msg += "• **Discord:** Notifications active\n" 
                startup_msg += "• **Status:** Monitoring positions\n"
                startup_msg += f"• **Started:** {startup_time}\n\n"
                startup_msg += "🚀 **Ready to track your trades!**"
                await self.send_to_all_servers(startup_msg)
            else:
                logger.warning("No servers configured - bot will not post messages")
                
            # Start position monitoring
            asyncio.create_task(self.monitoring_loop())
        
        @self.client.event
        async def on_error(event, *args, **kwargs):
            logger.error(f'Discord error in {event}: {args}')
        
        try:
            await self.client.start(self.discord_token)
        except Exception as e:
            logger.error(f"Discord connection error: {e}")


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
    required_keys = ['mexc', 'discord']
    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required configuration section: {key}")
            sys.exit(1)
    
    while True:  # Restart loop
        bot = MEXCTradingBot(config)
        
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
        print("=" * 50)
        print("MEXC Trading Bot - Discord Position Tracker")
        print("Commands: 'restart', 'stop', 'status'")
        print("=" * 50)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
    finally:
        print("Bot shut down.")
