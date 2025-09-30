#!/usr/bin/env python3
"""
SORABOT - Discord Economy Bot
A comprehensive economy bot with casino, guilds, stock market, and more.
"""

import discord
from discord.ext import commands, tasks
import json
import asyncio
import random
import datetime
from typing import Dict, List, Optional, Any
import aiofiles
import os
import math
import importlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Data file path
DATA_FILE = 'data.json'

# Item definitions
CONSUMABLE_ITEMS = {
    "lucky_potion": {"name": "Lucky Potion", "effect": "gambling_boost", "value": 0.2, "price": 150, "rarity": "Common"},
    "mega_lucky_potion": {"name": "Mega Lucky Potion", "effect": "gambling_boost", "value": 0.5, "price": 400, "rarity": "Rare"},
    "jackpot_booster": {"name": "Jackpot Booster", "effect": "payout_boost", "value": 0.1, "price": 200, "rarity": "Rare"},
    "robbers_mask": {"name": "Robber's Mask", "effect": "rob_boost", "value": 0.15, "price": 250, "rarity": "Rare"},
    "insurance_scroll": {"name": "Insurance Scroll", "effect": "insurance", "value": 0.5, "price": 300, "rarity": "Epic"},
    "mimic_repellent": {"name": "Mimic Repellent", "effect": "mimic_protection", "value": 1.0, "price": 500, "rarity": "Epic"}
}

EQUIPABLE_ITEMS = {
    "gamblers_charm": {"name": "Gambler's Charm", "slot": "trinket", "effect": "gambling_boost", "value": 0.05, "price": 400, "rarity": "Rare"},
    "golden_dice": {"name": "Golden Dice", "slot": "trinket", "effect": "slots_boost", "value": 0.1, "price": 600, "rarity": "Epic"},
    "security_dog": {"name": "Security Dog", "slot": "armor", "effect": "rob_protection", "value": 1, "price": 700, "rarity": "Epic"},
    "vault_key": {"name": "Vault Key", "slot": "bank_mod", "effect": "bank_interest", "value": 0.0025, "price": 800, "rarity": "Legendary"},
    "master_lockpick": {"name": "Master Lockpick", "slot": "weapon", "effect": "rob_boost", "value": 0.1, "price": 750, "rarity": "Epic"},
    "lucky_coin": {"name": "Lucky Coin", "slot": "trinket", "effect": "rat_race_boost", "value": 0.05, "price": 300, "rarity": "Rare"},
    "shadow_cloak": {"name": "Shadow Cloak", "slot": "armor", "effect": "stealth", "value": 0.15, "price": 600, "rarity": "Epic"}
}

CHEST_TYPES = {
    "common": {"name": "Common Chest", "coin_chance": 0.7, "item_chance": 0.25, "mimic_chance": 0.05, "price": 100},
    "rare": {"name": "Rare Chest", "coin_chance": 0.5, "item_chance": 0.4, "mimic_chance": 0.1, "price": 300},
    "epic": {"name": "Epic Chest", "coin_chance": 0.3, "item_chance": 0.6, "mimic_chance": 0.15, "price": 750},
    "legendary": {"name": "Legendary Chest", "coin_chance": 0.1, "item_chance": 0.8, "mimic_chance": 0.2, "price": 2000}
}

STOCK_MARKET = {
    "SORACOIN": {"name": "SORA Corporation", "base_price": 100, "volatility": 0.1},
    "LUCKYST": {"name": "Lucky Stars Casino", "base_price": 50, "volatility": 0.15},
    "GUILDCO": {"name": "Guild Commerce", "base_price": 75, "volatility": 0.08},
    "MINING": {"name": "Digital Mining Co", "base_price": 200, "volatility": 0.2}
}

class DataManager:
    """Handles all data persistence operations"""
    
    @staticmethod
    async def load_data():
        """Load data from JSON file"""
        try:
            async with aiofiles.open(DATA_FILE, 'r') as f:
                return json.loads(await f.read())
        except FileNotFoundError:
            return DataManager.get_default_data()
        except Exception as e:
            print(f"Error loading data: {e}")
            return DataManager.get_default_data()
    
    @staticmethod
    async def save_data(data):
        """Save data to JSON file"""
        try:
            async with aiofiles.open(DATA_FILE, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"Error saving data: {e}")
    
    @staticmethod
    def get_default_data():
        """Get default data structure"""
        return {
            "coins": {},
            "bank": {},
            "last_daily": {},
            "last_weekly": {},
            "transactions": {},
            "active_games": {},
            "companies": {},
            "items": {},
            "inventories": {},
            "equipped": {},
            "guilds": {},
            "guild_members": {},
            "stock_holdings": {},
            "stock_prices": {stock: data["base_price"] for stock, data in STOCK_MARKET.items()},
            "consumable_effects": {},
            "loot_tables": {},
            "config": {
                "min_bet": 10,
                "max_bet": 1000000,
                "daily_amount": 150,
                "weekly_amount": 1000,
                "interest_rate": 0.001,
                "interest_tick_minutes": 10,
                "market_tick_minutes": 10,
                "economy_frozen": False,
                "rob_cooldown_hours": 1,
                "rob_success_rate": 0.3,
                "rob_max_steal_percent": 0.2,
                "rob_fine_percent": 0.1
            },
            "bans": {},
            "cooldowns": {},
            "leaderboard_channel": None,
            "leaderboard_message": None,
            "_meta": {
                "last_interest_ts": None,
                "last_market_ts": None
            }
        }

# Bot initialization

# Bot events
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
    # Load all bot_modules
    modules = ["economy", "casino", "inventory", "shop", "guild", "market", "leaderboard", "admin", "help"]
    
    for module_name in modules:
        try:
            module = importlib.import_module(f"bot_modules.{module_name}")
            if hasattr(module, "setup"):
                await module.setup(bot)
                print(f'Loaded {module_name} module')
        except Exception as e:
            print(f'Failed to load {module_name} module: {e}')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    
    # Start background tasks
    if not interest_ticker.is_running():
        interest_ticker.start()
    if not market_ticker.is_running():
        market_ticker.start()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"❌ Error: {str(error)}")

# Background tasks
@tasks.loop(minutes=10)
async def interest_ticker():
    """Apply bank interest every 10 minutes"""
    data = await DataManager.load_data()
    now = datetime.datetime.utcnow()
    
    for user_id, amount in data["bank"].items():
        if amount > 0:
            interest = int(amount * data["config"]["interest_rate"])
            data["bank"][user_id] += interest
    
    data["_meta"]["last_interest_ts"] = now.isoformat()
    await DataManager.save_data(data)

@tasks.loop(minutes=10)
async def market_ticker():
    """Update stock market prices every 10 minutes"""
    data = await DataManager.load_data()
    now = datetime.datetime.utcnow()
    
    for stock, current_price in data["stock_prices"].items():
        if stock in STOCK_MARKET:
            volatility = STOCK_MARKET[stock]["volatility"]
            change = random.uniform(-volatility, volatility)
            new_price = max(1, current_price * (1 + change))
            data["stock_prices"][stock] = round(new_price, 2)
    
    data["_meta"]["last_market_ts"] = now.isoformat()
    await DataManager.save_data(data)

if __name__ == "__main__":
    # Load bot token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Please set DISCORD_TOKEN environment variable")
        exit(1)
    
    bot.run(token)
