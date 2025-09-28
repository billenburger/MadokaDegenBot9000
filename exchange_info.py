#!/usr/bin/env python3
"""
Exchange Information Tool
Shows available exchanges and their capabilities for the Universal Trading Bot
"""

import ccxt
import asyncio
import sys

def list_exchanges():
    """List all available CCXT exchanges"""
    exchanges = ccxt.exchanges
    
    print("=" * 60)
    print("AVAILABLE EXCHANGES FOR UNIVERSAL TRADING BOT")
    print("=" * 60)
    print(f"Total exchanges supported: {len(exchanges)}")
    print()
    
    # Popular exchanges first
    popular = [
        'binance', 'okx', 'bybit', 'kraken', 'coinbasepro', 
        'mexc', 'bitget', 'kucoin', 'huobi', 'gate'
    ]
    
    print("POPULAR EXCHANGES:")
    print("-" * 30)
    for exchange_id in popular:
        if exchange_id in exchanges:
            print(f"• {exchange_id}")
    
    print(f"\nALL EXCHANGES ({len(exchanges)} total):")
    print("-" * 30)
    
    # Group by first letter
    grouped = {}
    for exchange_id in sorted(exchanges):
        first_letter = exchange_id[0].upper()
        if first_letter not in grouped:
            grouped[first_letter] = []
        grouped[first_letter].append(exchange_id)
    
    for letter in sorted(grouped.keys()):
        print(f"\n{letter}:")
        for exchange_id in grouped[letter]:
            print(f"  {exchange_id}")

async def test_exchange_connection(exchange_id: str, api_key: str = None, secret: str = None):
    """Test connection to a specific exchange"""
    try:
        if not hasattr(ccxt, exchange_id):
            print(f"❌ Exchange '{exchange_id}' not found in CCXT")
            return False
        
        exchange_class = getattr(ccxt, exchange_id)
        
        # Create exchange instance
        config = {'enableRateLimit': True}
        if api_key and secret:
            config.update({
                'apiKey': api_key,
                'secret': secret,
            })
        
        exchange = exchange_class(config)
        
        print(f"Testing {exchange_id}...")
        
        # Test public endpoints
        try:
            markets = await exchange.load_markets()
            print(f"✅ Markets loaded: {len(markets)} trading pairs")
        except Exception as e:
            print(f"⚠️  Market loading failed: {e}")
        
        # Test authenticated endpoints if credentials provided
        if api_key and secret:
            try:
                balance = await exchange.fetch_balance()
                print("✅ Authentication successful")
                
                # Test futures positions if supported
                try:
                    positions = await exchange.fetch_positions()
                    print(f"✅ Positions endpoint working: {len(positions)} positions")
                except Exception:
                    print("⚠️  Positions endpoint not available or not accessible")
                
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
        else:
            print("ℹ️  Skipping authentication tests (no credentials provided)")
        
        await exchange.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def show_exchange_info(exchange_id: str):
    """Show detailed information about a specific exchange"""
    try:
        if not hasattr(ccxt, exchange_id):
            print(f"❌ Exchange '{exchange_id}' not found")
            return
        
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class()
        
        print(f"\nEXCHANGE INFORMATION: {exchange_id}")
        print("=" * 50)
        print(f"Name: {exchange.name}")
        print(f"Countries: {', '.join(exchange.countries)}")
        print(f"Website: {exchange.urls.get('www', 'N/A')}")
        print(f"API Documentation: {exchange.urls.get('doc', 'N/A')}")
        
        print(f"\nSupported Features:")
        print(f"• Futures Trading: {'✅' if exchange.has.get('fetchPositions') else '❌'}")
        print(f"• Margin Trading: {'✅' if exchange.has.get('fetchBorrowRate') else '❌'}")
        print(f"• Options Trading: {'✅' if exchange.has.get('fetchOption') else '❌'}")
        print(f"• WebSocket: {'✅' if exchange.has.get('ws') else '❌'}")
        
        print(f"\nAPI Capabilities:")
        for capability in ['fetchTicker', 'fetchBalance', 'fetchPositions', 'fetchOrders']:
            status = "✅" if exchange.has.get(capability) else "❌"
            print(f"• {capability}: {status}")
        
        if exchange.requiredCredentials:
            print(f"\nRequired Credentials:")
            for cred, required in exchange.requiredCredentials.items():
                if required:
                    print(f"• {cred}: Required")
        
        exchange.close()
        
    except Exception as e:
        print(f"❌ Error getting exchange info: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal Trading Bot - Exchange Information Tool')
    parser.add_argument('--list', action='store_true', help='List all available exchanges')
    parser.add_argument('--info', type=str, help='Show detailed info for specific exchange')
    parser.add_argument('--test', type=str, help='Test connection to specific exchange')
    parser.add_argument('--api-key', type=str, help='API key for testing (optional)')
    parser.add_argument('--secret', type=str, help='Secret key for testing (optional)')
    
    args = parser.parse_args()
    
    if args.list:
        list_exchanges()
    elif args.info:
        show_exchange_info(args.info)
    elif args.test:
        asyncio.run(test_exchange_connection(args.test, args.api_key, args.secret))
    else:
        print("Universal Trading Bot - Exchange Information Tool")
        print()
        print("Usage:")
        print("  python exchange_info.py --list                    # List all exchanges")
        print("  python exchange_info.py --info binance           # Show exchange details")
        print("  python exchange_info.py --test binance           # Test connection")
        print("  python exchange_info.py --test binance --api-key YOUR_KEY --secret YOUR_SECRET")
        print()
        print("Popular exchanges: binance, okx, bybit, kraken, mexc, bitget")

if __name__ == "__main__":
    main()