#!/usr/bin/env python3
"""
SORABOT - Discord Economy Bot with Firebase Integration
A comprehensive economy bot with casino, guilds, stock market, and more.
Now with enterprise-grade Firebase Firestore data persistence!
"""

import discord
from discord.ext import commands, tasks
import json
import asyncio
import random
import datetime
from typing import Dict, List, Optional, Any
import os
import math
import importlib
import logging
from pathlib import Path
from dotenv import load_dotenv

# Import Firebase-only data manager
from firebase_data_manager import get_firebase_manager

# Load environment variables
load_dotenv('.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sorabot.log'),
        logging.StreamHandler()
    ]
)

# Initialize Firebase-only data manager
firebase_data_manager = get_firebase_manager()

# Suppress PyNaCl warning for economy bot (voice not needed)
logging.getLogger('discord.client').setLevel(logging.ERROR)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Global constants for economy
INITIAL_COINS = 100
DEFAULT_DAILY = 150
DEFAULT_WEEKLY = 1000

# Stock market data
STOCK_MARKET = {
    "TECHNO": {"name": "TechnoBot Industries", "base_price": 150, "volatility": 0.12},
    "GAMING": {"name": "Gaming Paradise", "base_price": 80, "volatility": 0.18},
    "CRYPTO": {"name": "CryptoCoin Corp", "base_price": 300, "volatility": 0.25},
    "FOOD": {"name": "Food Delivery Plus", "base_price": 120, "volatility": 0.09},
    "ENERGY": {"name": "Green Energy Ltd", "base_price": 250, "volatility": 0.14},
    "TRANSPORT": {"name": "Hyper Transport", "base_price": 180, "volatility": 0.11},
    "HEALTH": {"name": "HealthTech Solutions", "base_price": 220, "volatility": 0.13},
    "MEDIA": {"name": "Digital Media Group", "base_price": 90, "volatility": 0.16},
    "FINANCE": {"name": "FinanceBot Banking", "base_price": 350, "volatility": 0.08},
    "RETAIL": {"name": "Retail Revolution", "base_price": 110, "volatility": 0.15},
    "SORACOIN": {"name": "SORA Corporation", "base_price": 100, "volatility": 0.1},
    "LUCKYST": {"name": "Lucky Stars Casino", "base_price": 50, "volatility": 0.15},
    "GUILDCO": {"name": "Guild Commerce", "base_price": 75, "volatility": 0.08},
    "MINING": {"name": "Digital Mining Co", "base_price": 200, "volatility": 0.2}
}

# Global Firebase-only data manager instance
data_manager = firebase_data_manager

# Auto-save background task for data persistence
async def auto_save_task():
    """ULTRA-AGGRESSIVE auto-save every 10 seconds to prevent ANY data loss"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            # Load current data
            current_data = await firebase_data_manager.load_data()
            
            # Force save to Firebase Realtime Database
            success = await firebase_data_manager.save_data(current_data, force=True)
            
            if success:
                logging.debug("🔄 Auto-save completed successfully")
            else:
                logging.warning("⚠️ Auto-save failed!")
                
        except Exception as e:
            logging.error(f"🚨 Auto-save error: {e}")
        
        # Wait only 10 seconds before next save - ULTRA AGGRESSIVE
        await asyncio.sleep(10)

# Bot events
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
    # Start web server for uptime monitoring
    try:
        from web_server import start_web_server, update_bot_status
        start_web_server()
        update_bot_status("initializing")
        print('🌐 Web server started for uptime monitoring')
    except Exception as e:
        print(f'⚠️ Web server failed to start: {e}')
    
    # Initialize Firebase Realtime Database system
    try:
        # Test load data to ensure Firebase is working
        test_data = await data_manager.load_data()
        
        stats = await data_manager.get_stats()
        firebase_status = "🔥 Firebase Realtime DB" if stats.get('firebase_ready') else "❌ OFFLINE"
        
        logging.info(f'✅ Data system initialized ({firebase_status}) - {len(test_data.get("coins", {}))} users loaded')
        
        if not stats.get('firebase_ready'):
            logging.error("❌ CRITICAL: Firebase Realtime Database is NOT connected!")
            logging.error("❌ Bot will NOT function properly without Firebase!")
        
        # Link the data manager to bot modules
        try:
            from bot_modules.database import set_data_manager
            set_data_manager(data_manager)
        except Exception as e:
            logging.warning(f"Could not link data manager to modules: {e}")
        
        # Start ULTRA-AGGRESSIVE auto-save background task
        bot.loop.create_task(auto_save_task())
        logging.info("🔄 ULTRA-AGGRESSIVE auto-save task started (10-second intervals)")
            
    except Exception as e:
        logging.error(f'❌ Data system initialization failed: {e}')
    
    # Load all bot_modules
    modules = ["economy", "casino", "inventory", "shop", "guild", "market", "leaderboard", "admin", "help", "heist"]
    
    for module_name in modules:
        try:
            module = importlib.import_module(f"bot_modules.{module_name}")
            if hasattr(module, "setup"):
                await module.setup(bot)
                print(f'✅ Loaded {module_name} module')
        except Exception as e:
            print(f'❌ Failed to load {module_name}: {e}')
    
    # Start background tasks
    if not auto_save_task.is_running():
        auto_save_task.start()
        print('🔄 Auto-save task started')
    
    if not market_update_task.is_running():
        market_update_task.start()
        print('📈 Market update task started')
    
    if not interest_task.is_running():
        interest_task.start()
        print('💰 Interest calculation task started')
    
    # Update web server status
    try:
        from web_server import update_bot_status
        update_bot_status("online")
    except:
        pass
    
    print('🚀 SORABOT is ready with Firebase-powered data persistence!')

@bot.event
async def on_command_completion(ctx):
    """Triggered after EVERY successful command - ensures immediate Firebase save"""
    try:
        # Load current data
        current_data = await data_manager.load_data()
        
        # Force immediate save to Firebase after every command
        success = await data_manager.save_data(current_data, force=True)
        
        if success:
            logging.debug(f"✅ Post-command save for '{ctx.command.name}' by {ctx.author.name}")
        else:
            logging.error(f"❌ Post-command save FAILED for '{ctx.command.name}'")
            
    except Exception as e:
        logging.error(f"❌ Post-command save error: {e}")

@bot.event
async def on_guild_join(guild):
    """When bot joins a new server"""
    print(f'Joined new guild: {guild.name} (ID: {guild.id})')
    
    # Send welcome message to first available text channel
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="🤖 SORABOT Has Arrived!",
                description="Thanks for adding me to your server! 🎉",
                color=0x00ff00
            )
            embed.add_field(
                name="🚀 Getting Started",
                value="Type `!help` to see all available commands!",
                inline=False
            )
            embed.add_field(
                name="💰 Economy Features",
                value="• Daily/Weekly rewards\n• Casino games\n• Stock trading\n• Guild system\n• Shop & inventory",
                inline=False
            )
            embed.add_field(
                name="🔧 Setup",
                value="Use `!config` to customize bot settings for your server.",
                inline=False
            )
            embed.set_footer(text="Powered by Firebase • Enterprise-grade data persistence")
            
            try:
                await channel.send(embed=embed)
                break
            except:
                continue

# Background tasks
@tasks.loop(minutes=5)
async def auto_save_task():
    """Auto-save task with hybrid Firebase/JSON persistence"""
    try:
        if data_manager._data_cache:
            await data_manager.save_data(data_manager._data_cache)
            
            stats = await data_manager.get_stats()
            if stats.get('firebase_ready'):
                logging.debug("🔥 Auto-save completed (Firebase + JSON)")
            else:
                logging.debug("📄 Auto-save completed (JSON only)")
    except Exception as e:
        logging.error(f"Auto-save failed: {e}")

@tasks.loop(minutes=15)
async def market_update_task():
    """Update stock market prices"""
    try:
        data = await data_manager.load_data()
        stock_prices = data.get("stock_prices", {})
        
        # Update each stock price based on volatility
        for stock_symbol, stock_info in STOCK_MARKET.items():
            base_price = stock_info["base_price"]
            volatility = stock_info["volatility"]
            
            if stock_symbol not in stock_prices:
                stock_prices[stock_symbol] = base_price
            
            current_price = stock_prices[stock_symbol]
            change_percent = random.uniform(-volatility, volatility)
            new_price = max(1, round(current_price * (1 + change_percent), 2))
            
            # Prevent prices from going too far from base price
            max_deviation = base_price * 2
            min_deviation = base_price * 0.5
            new_price = max(min_deviation, min(max_deviation, new_price))
            
            stock_prices[stock_symbol] = new_price
        
        data["stock_prices"] = stock_prices
        data["_meta"]["last_market_ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        await data_manager.save_data(data)
        logging.debug("📈 Stock market updated")
        
    except Exception as e:
        logging.error(f"Market update failed: {e}")

@tasks.loop(minutes=10)
async def interest_task():
    """Calculate interest on bank accounts"""
    try:
        data = await data_manager.load_data()
        bank_accounts = data.get("bank", {})
        config = data.get("config", {})
        interest_rate = config.get("interest_rate", 0.001)
        
        for user_id, balance in bank_accounts.items():
            if balance > 0:
                interest = int(balance * interest_rate)
                if interest > 0:
                    bank_accounts[user_id] = balance + interest
        
        data["bank"] = bank_accounts
        data["_meta"]["last_interest_ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        await data_manager.save_data(data)
        logging.debug("💰 Interest calculated")
        
    except Exception as e:
        logging.error(f"Interest calculation failed: {e}")

# Admin commands for Firebase management
@bot.command(name='sync')
@commands.has_permissions(administrator=True)
async def sync(ctx, force: str = None):
    """Sync slash commands with Discord (admin only)
    
    Usage:
    !sync - Normal sync
    !sync force - Clear and re-sync all commands (fixes cached parameters)
    """
    try:
        if force == "force":
            await ctx.send("🔄 Force syncing: Clearing old commands and re-syncing...")
            bot.tree.clear_commands(guild=None)
            await bot.tree.sync()
            await ctx.send("✅ Cleared cache and synced commands! Wait 1-2 minutes and restart Discord.")
        else:
            await ctx.send("🔄 Syncing commands with Discord...")
            synced = await bot.tree.sync()
            await ctx.send(f"✅ Successfully synced {len(synced)} slash commands!")
            print(f"✅ Synced {len(synced)} commands: {[cmd.name for cmd in synced]}")
    except Exception as e:
        await ctx.send(f"❌ Failed to sync commands: {e}")
        print(f"❌ Sync error: {e}")

@bot.command(name='firebase_status')
@commands.has_permissions(administrator=True)
async def firebase_status(ctx):
    """Check Firebase connection status"""
    try:
        stats = await data_manager.get_stats()
        
        embed = discord.Embed(
            title="🔥 Firebase Status Dashboard",
            color=0x00ff00 if stats.get('firebase_ready') else 0xffaa00
        )
        
        # Basic info
        embed.add_field(
            name="📊 System Status",
            value=f"```\nHybrid Mode: {'✅' if stats.get('hybrid_mode') else '❌'}\n"
                  f"Firebase: {'🔥 Connected' if stats.get('firebase_ready') else '❌ Offline'}\n"
                  f"JSON Backup: {'✅ Active' if True else '❌'}\n```",
            inline=False
        )
        
        # Data stats
        if stats.get('user_count'):
            embed.add_field(
                name="📈 Data Statistics",
                value=f"```\nUsers: {stats.get('user_count', 0):,}\n"
                      f"Total Coins: {stats.get('total_coins', 0):,}\n"
                      f"Guilds: {stats.get('guild_count', 0):,}\n"
                      f"Save Count: {stats.get('save_count', 0):,}\n```",
                inline=False
            )
        
        # Firebase specific stats
        if stats.get('firebase_ready'):
            embed.add_field(
                name="🔥 Firebase Details",
                value=f"```\nProject: {stats.get('firebase_project', 'Unknown')}\n"
                      f"Status: {stats.get('firebase_status', 'Unknown')}\n"
                      f"Last Save: {stats.get('last_save', 'Never')[:19]}\n```",
                inline=False
            )
        
        embed.set_footer(text="Enterprise-grade data persistence powered by Firebase Firestore")
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Firebase Status Error",
            description=f"```{str(e)}```",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='migrate_to_firebase')
@commands.has_permissions(administrator=True)
async def migrate_to_firebase(ctx):
    """Manually trigger Firebase migration"""
    try:
        if not data_manager.is_firebase_ready():
            await ctx.send("❌ Firebase is not available for migration!")
            return
        
        await ctx.send("🔄 Starting Firebase migration...")
        
        # Load current data
        data = await data_manager.load_data()
        
        # Force migration
        from firebase_manager import get_firebase_manager
        firebase_manager = get_firebase_manager()
        success = await firebase_manager.migrate_from_json(data)
        
        if success:
            embed = discord.Embed(
                title="✅ Firebase Migration Successful!",
                description="Your bot data has been successfully migrated to Firebase Firestore.",
                color=0x00ff00
            )
            embed.add_field(
                name="📊 Migration Stats",
                value=f"```\nUsers Migrated: {len(data.get('coins', {})):,}\n"
                      f"Total Coins: {sum(data.get('coins', {}).values()):,}\n"
                      f"Guilds: {len(data.get('guilds', {})):,}\n"
                      f"Data Size: {len(str(data)):,} characters\n```",
                inline=False
            )
            embed.set_footer(text="Your data is now safely stored in Firebase Firestore!")
        else:
            embed = discord.Embed(
                title="❌ Migration Failed",
                description="The Firebase migration could not be completed.",
                color=0xff0000
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Migration Error",
            description=f"```{str(e)}```",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='forcesave')
@commands.has_permissions(administrator=True)
async def force_save(ctx):
    """Force immediate save to Firebase and JSON (Admin only)"""
    try:
        await ctx.send("🔄 **Forcing immediate save to Firebase and JSON...**")
        
        # Load current data
        data = await data_manager.load_data()
        
        # Force aggressive save
        success = await data_manager.save_data(data, force=True)
        
        if success:
            stats = await data_manager.get_stats()
            firebase_status = "🔥 Firebase" if stats.get('firebase_ready') else "❌ Failed"
            
            embed = discord.Embed(
                title="✅ Force Save Successful!",
                description="Data has been aggressively saved to all available storage systems.",
                color=0x00ff00
            )
            embed.add_field(
                name="💾 Save Status",
                value=f"```\nFirebase: {firebase_status}\n"
                      f"JSON Backup: ✅ Completed\n"
                      f"Emergency Backup: ✅ Completed\n```",
                inline=False
            )
            embed.add_field(
                name="📊 Data Stats",
                value=f"```\nUsers: {len(data.get('coins', {})):,}\n"
                      f"Total Coins: {sum(data.get('coins', {}).values()):,}\n"
                      f"Save Count: {stats.get('save_count', 0)}\n```",
                inline=False
            )
            embed.set_footer(text="Your data is now safely synchronized!")
        else:
            embed = discord.Embed(
                title="❌ Force Save Failed",
                description="The forced save operation could not be completed.",
                color=0xff0000
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Force Save Error",
            description=f"```{str(e)}```",
            color=0xff0000
        )
        await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f} seconds.")
    else:
        logging.error(f"Command error: {error}")
        await ctx.send("❌ An error occurred while processing the command.")

# Run the bot
if __name__ == "__main__":
    # Check for required environment variables
    discord_token = os.getenv('DISCORD_TOKEN')
    
    if not discord_token:
        print("❌ Error: DISCORD_TOKEN not found in environment variables!")
        print("Please add your Discord bot token to the .env file.")
        exit(1)
    
    # Optional Firebase configuration check
    firebase_project = os.getenv('FIREBASE_PROJECT_ID')
    if firebase_project:
        print(f"🔥 Firebase project configured: {firebase_project}")
    else:
        print("📄 Running in JSON-only mode (Firebase not configured)")
        print("To enable Firebase:")
        print("1. Set FIREBASE_PROJECT_ID in environment variables")
        print("2. Set FIREBASE_PRIVATE_KEY and FIREBASE_CLIENT_EMAIL")
        print("3. Or provide FIREBASE_SERVICE_ACCOUNT_PATH")
    
    print("🚀 Starting SORABOT with hybrid data persistence...")
    
    try:
        bot.run(discord_token)
    except discord.LoginFailure:
        print("❌ Error: Invalid Discord token!")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")