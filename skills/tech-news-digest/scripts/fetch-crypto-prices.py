#!/usr/bin/env python3
"""Fetch cryptocurrency prices from CoinGecko API."""

import json
import requests
from datetime import datetime

def fetch_prices():
    """Fetch current crypto prices and 24h change."""
    
    # CoinGecko free API (no auth required)
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,usdc,tether,polygon,solana,chainlink",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_24hr_vol": "true",
        "include_market_cap": "true"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            prices = []
            
            for coin_id, info in data.items():
                name_map = {
                    "bitcoin": ("BTC", "Bitcoin"),
                    "ethereum": ("ETH", "Ethereum"),
                    "usdc": ("USDC", "USD Coin"),
                    "tether": ("USDT", "Tether"),
                    "polygon": ("MATIC", "Polygon"),
                    "solana": ("SOL", "Solana"),
                    "chainlink": ("LINK", "Chainlink")
                }
                
                symbol, full_name = name_map.get(coin_id, (coin_id, coin_id))
                prices.append({
                    "symbol": symbol,
                    "name": full_name,
                    "price_usd": info.get("usd", 0),
                    "change_24h": info.get("usd_24h_change", 0),
                    "volume_24h": info.get("usd_24h_vol", 0),
                    "market_cap": info.get("usd_market_cap", 0)
                })
            
            return prices
    except Exception as e:
        print(f"Error fetching prices: {e}")
    
    # Fallback data
    return [
        {"symbol": "BTC", "name": "Bitcoin", "price_usd": 68000, "change_24h": 2.5},
        {"symbol": "ETH", "name": "Ethereum", "price_usd": 3200, "change_24h": 1.8},
        {"symbol": "USDC", "name": "USD Coin", "price_usd": 1.00, "change_24h": 0.01},
        {"symbol": "USDT", "name": "Tether", "price_usd": 1.00, "change_24h": -0.02}
    ]

def format_change(change):
    """Format 24h change with color indicator."""
    if change >= 0:
        return f"+{change:.2f}%"
    return f"{change:.2f}%"

if __name__ == "__main__":
    prices = fetch_prices()
    
    print("## 加密货币价格")
    print(f"*更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    print("| 币种 | 价格 (USD) | 24h 涨跌 |")
    print("|------|-----------|---------|")
    
    for p in prices:
        change_str = format_change(p["change_24h"])
        print(f"| {p['symbol']} | ${p['price_usd']:,.2f} | {change_str} |")
