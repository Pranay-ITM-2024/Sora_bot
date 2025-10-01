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
import logging
import shutil
import gzip
from pathlib import Path
from dotenv import load_dotenv

# Import render persistence for cloud backup
from render_persistence import render_persistence

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

# Suppress PyNaCl warning for economy bot (voice not needed)
logging.getLogger('discord.client').setLevel(logging.ERROR)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Data persistence configuration - AGGRESSIVE MODE
DATA_FILE = 'data.json'
BACKUP_DIR = Path('backups')
EMERGENCY_BACKUP = 'emergency_data.json'
AUTO_SAVE_INTERVAL = 15  # AGGRESSIVE: 15 seconds instead of 30

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

class AdvancedDataManager:
    """
    AGGRESSIVE DATA PERSISTENCE SYSTEM - ZERO TOLERANCE FOR DATA LOSS
    Features:
    - IMMEDIATE cloud backup on every change
    - Multiple local redundancy layers
    - Forced save on every critical operation
    - Startup data verification and recovery
    - RENDER-READY: Bulletproof cloud persistence
    """
    
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(exist_ok=True)
        self.save_count = 0
        self.last_save_time = datetime.datetime.utcnow()
        self._data_cache = None
        self._is_saving = False
        self.last_cloud_sync = datetime.datetime.utcnow()
        
        # Detect if running on Render (ephemeral environment)
        self.is_render = os.getenv('RENDER') == 'true' or os.getenv('RENDER_SERVICE_ID') is not None
        
        # AGGRESSIVE MODE: Always treat as production environment
        self.aggressive_mode = True
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(exist_ok=True)
        
        if self.is_render:
            logging.info("🌥️ RENDER DETECTED: AGGRESSIVE cloud persistence initialized")
        else:
            logging.info("🛡️ AGGRESSIVE Data Manager initialized - ZERO TOLERANCE FOR DATA LOSS")
    
    async def load_data(self):
        """AGGRESSIVE data loading with comprehensive fallback protection"""
        try:
            loaded_data = None
            
            # PRIORITY 1: Try cloud sources first if configured
            if render_persistence.github_token or self.is_render:
                try:
                    cloud_data = await render_persistence.load_from_cloud()
                    if cloud_data and self._validate_data(cloud_data):
                        logging.info("☁️ PRIORITY RECOVERY: Data loaded from cloud backup")
                        loaded_data = cloud_data
                        # Immediately save to all local backups
                        await self._save_local_redundant(cloud_data)
                except Exception as e:
                    logging.error(f"Cloud recovery failed: {e}")
            
            # PRIORITY 2: Try primary data file
            if not loaded_data and os.path.exists(DATA_FILE):
                try:
                    async with aiofiles.open(DATA_FILE, 'r') as f:
                        data = json.loads(await f.read())
                        if self._validate_data(data):
                            logging.info("✅ Data loaded from primary file")
                            loaded_data = data
                        else:
                            logging.warning("⚠️ Primary data corrupted, trying backup...")
                except Exception as e:
                    logging.warning(f"Primary file error: {e}, trying backup...")
            
            # PRIORITY 3: Emergency backup
            if not loaded_data and os.path.exists(EMERGENCY_BACKUP):
                try:
                    async with aiofiles.open(EMERGENCY_BACKUP, 'r') as f:
                        data = json.loads(await f.read())
                        if self._validate_data(data):
                            logging.info("✅ Restored from emergency backup")
                            loaded_data = data
                except Exception as e:
                    logging.warning(f"Emergency backup error: {e}")
            
            # PRIORITY 4: Latest timestamped backup
            if not loaded_data:
                backup_files = sorted(self.backup_dir.glob('backup_*.json'), 
                                    key=lambda x: x.stat().st_mtime, reverse=True)
                for backup_file in backup_files[:10]:  # Try last 10 backups
                    try:
                        async with aiofiles.open(backup_file, 'r') as f:
                            data = json.loads(await f.read())
                            if self._validate_data(data):
                                logging.info(f"✅ Restored from backup: {backup_file.name}")
                                loaded_data = data
                                break
                    except Exception as e:
                        logging.warning(f"Backup {backup_file.name} error: {e}")
                        continue
            
            # PRIORITY 5: Compressed backups
            if not loaded_data:
                compressed_files = sorted(self.backup_dir.glob('backup_compressed_*.json.gz'), 
                                        key=lambda x: x.stat().st_mtime, reverse=True)
                for compressed_file in compressed_files[:5]:
                    try:
                        with gzip.open(compressed_file, 'rt', encoding='utf-8') as f:
                            data = json.loads(f.read())
                            if self._validate_data(data):
                                logging.info(f"✅ Restored from compressed backup: {compressed_file.name}")
                                loaded_data = data
                                break
                    except Exception as e:
                        logging.warning(f"Compressed backup {compressed_file.name} error: {e}")
                        continue
            
            # LAST RESORT: Fresh data
            if not loaded_data:
                logging.warning("🆕 ALL BACKUPS FAILED - Creating fresh data structure")
                loaded_data = self.get_default_data()
            
            # AGGRESSIVE SAVE: Immediately save to all locations
            self._data_cache = loaded_data.copy()
            await self.save_data(loaded_data, force=True)
            
            return loaded_data
            
        except Exception as e:
            logging.error(f"❌ CRITICAL data loading error: {e}")
            data = self.get_default_data()
            await self.save_data(data, force=True)
            return data
    
    async def save_data(self, data, force=False):
        """AGGRESSIVE save with immediate cloud sync and multiple redundancy"""
        if self._is_saving and not force:
            logging.debug("Save already in progress, skipping...")
            return True
        
        try:
            self._is_saving = True
            self.save_count += 1
            
            # Validate data before saving
            if not self._validate_data(data):
                logging.error("❌ Invalid data structure, aborting save")
                return False
            
            # Add metadata
            data.setdefault("_meta", {})
            data["_meta"]["last_save"] = datetime.datetime.utcnow().isoformat()
            data["_meta"]["save_count"] = self.save_count
            data["_meta"]["version"] = "3.0_aggressive_persistence"
            data["_meta"]["render_mode"] = self.is_render
            data["_meta"]["hostname"] = os.getenv('HOSTNAME', 'unknown')
            
            # AGGRESSIVE SAVE: Multiple redundant saves
            await self._save_local_redundant(data)
            
            # IMMEDIATE CLOUD SYNC: Always sync on aggressive mode
            if self.aggressive_mode:
                try:
                    cloud_success = await render_persistence.save_to_cloud(data)
                    if cloud_success:
                        self.last_cloud_sync = datetime.datetime.utcnow()
                        logging.info("☁️ IMMEDIATE cloud sync successful")
                    else:
                        logging.warning("⚠️ IMMEDIATE cloud sync failed - retrying...")
                        # Retry once
                        await asyncio.sleep(1)
                        if await render_persistence.save_to_cloud(data):
                            logging.info("☁️ Cloud sync retry successful")
                        else:
                            logging.error("❌ Cloud sync retry failed")
                except Exception as e:
                    logging.error(f"Cloud sync error: {e}")
            
            # Traditional backup layers (always create local redundancy)
            try:
                # Emergency backup
                shutil.copy2(DATA_FILE, EMERGENCY_BACKUP)
                
                # Force timestamped backup on every save in aggressive mode
                if self.aggressive_mode or self.save_count % 2 == 0 or force:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_file = self.backup_dir / f"backup_{timestamp}.json"
                    shutil.copy2(DATA_FILE, backup_file)
                    logging.debug(f"Created timestamped backup: {backup_file.name}")
                
                # Compressed backup (every 5 saves in aggressive mode)
                if self.save_count % 5 == 0:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    compressed_file = self.backup_dir / f"backup_compressed_{timestamp}.json.gz"
                    with open(DATA_FILE, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    logging.info(f"Created compressed backup: {compressed_file.name}")
                
                # Cleanup old backups
                if self.save_count % 50 == 0:
                    await self._cleanup_old_backups()
                    
            except Exception as e:
                logging.warning(f"Local backup error: {e}")
            
            # Update cache and log success
            self._data_cache = data.copy()
            self.last_save_time = datetime.datetime.utcnow()
            
            user_count = len(data.get("coins", {}))
            total_coins = sum(data.get("coins", {}).values())
            
            if self.is_render:
                logging.info(f"☁️ AGGRESSIVE SAVE #{self.save_count} - {user_count} users, {total_coins:,} coins [RENDER MODE]")
            else:
                logging.info(f"�️ AGGRESSIVE SAVE #{self.save_count} - {user_count} users, {total_coins:,} coins")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ CRITICAL save error: {e}")
            # Emergency save to alternative location
            try:
                emergency_file = f"CRITICAL_BACKUP_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                async with aiofiles.open(emergency_file, 'w') as f:
                    await f.write(json.dumps(data, indent=2, default=str))
                logging.error(f"🚨 Emergency backup saved to {emergency_file}")
                
                # Try to save to cloud as last resort
                if self.is_render or self.aggressive_mode:
                    await render_persistence.save_to_cloud(data)
                    
            except Exception as e2:
                logging.critical(f"💥 COMPLETE SAVE FAILURE: {e2}")
            return False
        finally:
            self._is_saving = False
    
    async def _save_local_redundant(self, data):
        """Save data to multiple local locations with redundancy"""
        # Primary atomic save
        temp_file = f"{DATA_FILE}.tmp"
        async with aiofiles.open(temp_file, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
        os.rename(temp_file, DATA_FILE)
        
        # Immediate secondary save
        secondary_file = f"{DATA_FILE}.backup"
        async with aiofiles.open(secondary_file, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
        
        # Immediate tertiary save
        tertiary_file = f"{DATA_FILE}.redundant"
        async with aiofiles.open(tertiary_file, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
    
    async def auto_save_if_needed(self, data):
        """AGGRESSIVE auto-save - much more frequent saves"""
        now = datetime.datetime.utcnow()
        time_since_save = (now - self.last_save_time).total_seconds()
        
        # AGGRESSIVE: Save every 15 seconds instead of 30
        if time_since_save >= 15 or self.aggressive_mode:
            await self.save_data(data, force=True)
    
    def _validate_data(self, data):
        """Validate data structure integrity"""
        if not isinstance(data, dict):
            return False
        
        # Check for essential keys
        required_keys = ["coins", "bank", "config"]
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            logging.warning(f"Missing required keys: {missing_keys}")
            return False
        
        # Basic type checking
        if not isinstance(data.get("coins", {}), dict):
            return False
        if not isinstance(data.get("bank", {}), dict):
            return False
        if not isinstance(data.get("config", {}), dict):
            return False
        
        return True
    
    async def _cleanup_old_backups(self):
        """Clean up old backup files to save space"""
        try:
            # Keep last 20 timestamped backups
            backup_files = sorted(self.backup_dir.glob('backup_*.json'), 
                                key=lambda x: x.stat().st_mtime, reverse=True)
            for old_backup in backup_files[20:]:
                old_backup.unlink()
                logging.debug(f"Cleaned up old backup: {old_backup.name}")
            
            # Keep last 10 compressed backups
            compressed_files = sorted(self.backup_dir.glob('backup_compressed_*.json.gz'), 
                                    key=lambda x: x.stat().st_mtime, reverse=True)
            for old_compressed in compressed_files[10:]:
                old_compressed.unlink()
                logging.debug(f"Cleaned up old compressed backup: {old_compressed.name}")
                
        except Exception as e:
            logging.warning(f"Backup cleanup error: {e}")
    
    async def create_manual_backup(self, reason="manual"):
        """Create a manual backup with custom reason"""
        try:
            if self._data_cache:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"backup_{reason}_{timestamp}.json"
                
                async with aiofiles.open(backup_file, 'w') as f:
                    await f.write(json.dumps(self._data_cache, indent=2, default=str))
                
                logging.info(f"Manual backup created: {backup_file.name}")
                return backup_file
        except Exception as e:
            logging.error(f"Manual backup failed: {e}")
            return None
    
    def get_default_data(self):
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
            "guild_invites": {},
            "stock_holdings": {},
            "stock_portfolios": {},
            "stock_market": {},
            "stock_prices": {stock: data["base_price"] for stock, data in STOCK_MARKET.items()},
            "consumable_effects": {},
            "loot_tables": {},
            "shop_items": {},
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
                "last_market_ts": None,
                "created": datetime.datetime.utcnow().isoformat(),
                "version": "3.0_bulletproof",
                "save_count": 0
            }
        }

# Global data manager instance - NO SQLite, pure JSON with bulletproof protection
data_manager = AdvancedDataManager()

# Bot initialization

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
    
    # Initialize advanced data protection system
    try:
        # Test load data to ensure system is working
        test_data = await data_manager.load_data()
        logging.info(f'✅ AGGRESSIVE data system initialized - {len(test_data.get("coins", {}))} users loaded')
        
        # Link the data manager to bot modules for aggressive saving
        try:
            from bot_modules.database import set_data_manager
            set_data_manager(data_manager)
        except Exception as e:
            logging.warning(f"Could not link data manager to modules: {e}")
            
    except Exception as e:
        logging.error(f'❌ Data system initialization failed: {e}')
    
    # Load all bot_modules
    modules = ["economy", "casino", "inventory", "shop", "guild", "market", "leaderboard", "admin", "help"]
    
    for module_name in modules:
        try:
            module = importlib.import_module(f"bot_modules.{module_name}")
            if hasattr(module, "setup"):
                await module.setup(bot)
                print(f'✅ Loaded {module_name} module')
        except Exception as e:
            print(f'❌ Failed to load {module_name} module: {e}')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    
    # Start background tasks for economic system and AGGRESSIVE data protection
    if not interest_ticker.is_running():
        interest_ticker.start()
        logging.info("💰 Interest ticker started")
    
    if not market_ticker.is_running():
        market_ticker.start()
        logging.info("📈 Market ticker started")
    
    if not data_protection_ticker.is_running():
        data_protection_ticker.start()
        logging.info("🛡️ AGGRESSIVE data protection ticker started")
    
    # Start cloud health monitoring on Render
    if data_manager.is_render and not cloud_health_check.is_running():
        cloud_health_check.start()
        logging.info("☁️ Cloud health monitoring started")
    
    # Start data verification task
    if not data_verification_ticker.is_running():
        data_verification_ticker.start()
        logging.info("🔍 Data verification ticker started")
    
    # Update web server status
    try:
        from web_server import update_bot_status
        update_bot_status("online")
    except:
        pass
    
    print('🚀 SORABOT is fully operational with data protection and uptime monitoring!')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(f"❌ Error: {str(error)}")

# Graceful shutdown handling for data protection
import signal

async def graceful_shutdown():
    """Ensure data is saved before shutdown"""
    try:
        logging.info("🛑 Graceful shutdown initiated...")
        
        # Create final backup before shutdown
        await data_manager.create_manual_backup("shutdown")
        
        # Force save current data
        data = await data_manager.load_data()
        await data_manager.save_data(data, force=True)
        
        logging.info("✅ Final backup completed successfully")
    except Exception as e:
        logging.error(f"❌ Shutdown backup failed: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, initiating graceful shutdown...")
    asyncio.create_task(graceful_shutdown())
    
# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Background tasks with bulletproof data protection
@tasks.loop(minutes=10)
async def interest_ticker():
    """Apply bank interest every 10 minutes with advanced data protection"""
    try:
        data = await data_manager.load_data()
        now = datetime.datetime.utcnow()
        
        # Check if enough time has passed for interest
        last_interest = data.get("_meta", {}).get("last_interest_ts")
        if last_interest:
            last_time = datetime.datetime.fromisoformat(last_interest)
            time_diff = (now - last_time).total_seconds() / 60
            
            if time_diff < data["config"]["interest_tick_minutes"]:
                return  # Too early for next interest payment
        
        interest_applied = 0
        users_paid = 0
        
        for user_id, amount in data["bank"].items():
            if amount > 0:
                interest = int(amount * data["config"]["interest_rate"])
                if interest > 0:
                    data["bank"][user_id] += interest
                    interest_applied += interest
                    users_paid += 1
        
        # Update timestamp
        data["_meta"]["last_interest_ts"] = now.isoformat()
        
        # Save with advanced protection
        await data_manager.save_data(data)
        
        if interest_applied > 0:
            logging.info(f"💰 Applied {interest_applied:,} interest to {users_paid} bank accounts")
    except Exception as e:
        logging.error(f"Interest ticker error: {e}")

@tasks.loop(minutes=10)
async def market_ticker():
    """Update stock market prices every 10 minutes with advanced data protection"""
    try:
        data = await data_manager.load_data()
        now = datetime.datetime.utcnow()
        
        # Check if enough time has passed for market update
        last_market = data.get("_meta", {}).get("last_market_ts")
        if last_market:
            last_time = datetime.datetime.fromisoformat(last_market)
            time_diff = (now - last_time).total_seconds() / 60
            
            if time_diff < data["config"]["market_tick_minutes"]:
                return  # Too early for next market update
        
        price_changes = {}
        for stock_symbol in STOCK_MARKET.keys():
            current_price = data["stock_prices"].get(stock_symbol, STOCK_MARKET[stock_symbol]["base_price"])
            volatility = STOCK_MARKET[stock_symbol]["volatility"]
            
            # Random price change based on volatility
            change = random.uniform(-volatility, volatility)
            new_price = max(1, round(current_price * (1 + change), 2))
            
            if new_price != current_price:
                data["stock_prices"][stock_symbol] = new_price
                price_changes[stock_symbol] = {
                    "old": current_price,
                    "new": new_price,
                    "change": ((new_price - current_price) / current_price) * 100
                }
        
        # Update timestamp
        data["_meta"]["last_market_ts"] = now.isoformat()
        
        # Save with advanced protection
        await data_manager.save_data(data)
        
        if price_changes:
            logging.info(f"📈 Updated {len(price_changes)} stock prices")
    except Exception as e:
        logging.error(f"Market ticker error: {e}")

@tasks.loop(minutes=2)
async def data_protection_ticker():
    """AGGRESSIVE data protection - every 2 minutes instead of 5"""
    try:
        # Load current data
        data = await data_manager.load_data()
        
        # AGGRESSIVE auto-save check
        await data_manager.auto_save_if_needed(data)
        
        # Create frequent backups
        now = datetime.datetime.utcnow()
        if now.minute % 10 == 0 and not data_manager.is_render:  # Every 10 minutes
            await data_manager.create_manual_backup("scheduled")
        
        # RENDER: Force cloud sync every 5 minutes
        if data_manager.is_render and now.minute % 5 == 0:
            try:
                await render_persistence.save_to_cloud(data)
                logging.info("☁️ AGGRESSIVE cloud sync completed")
            except Exception as e:
                logging.error(f"AGGRESSIVE cloud sync failed: {e}")
        
    except Exception as e:
        logging.error(f"Data protection ticker error: {e}")

@tasks.loop(minutes=10)
async def cloud_health_check():
    """Monitor cloud backup health and connectivity - more frequent"""
    if not data_manager.is_render:
        return  # Only run on Render
    
    try:
        # Test cloud connectivity with real data
        data = await data_manager.load_data()
        success = await render_persistence.save_to_cloud(data)
        
        if success:
            logging.info("☁️ Cloud backup health check: HEALTHY")
        else:
            logging.warning("⚠️ Cloud backup health check: DEGRADED - ATTEMPTING RECOVERY")
            # Try to recover cloud connectivity
            await asyncio.sleep(5)
            retry_success = await render_persistence.save_to_cloud(data)
            if retry_success:
                logging.info("☁️ Cloud backup recovery: SUCCESS")
            else:
                logging.error("❌ Cloud backup recovery: FAILED")
            
    except Exception as e:
        logging.error(f"Cloud health check failed: {e}")

# NEW: Data verification task
@tasks.loop(minutes=15)
async def data_verification_ticker():
    """Verify data integrity and force save if needed"""
    try:
        data = await data_manager.load_data()
        
        # Verify data structure
        if not data_manager._validate_data(data):
            logging.error("❌ Data integrity check FAILED - attempting recovery")
            # Try to recover from backups
            backup_files = sorted(data_manager.backup_dir.glob('backup_*.json'), 
                                key=lambda x: x.stat().st_mtime, reverse=True)
            for backup_file in backup_files[:3]:
                try:
                    async with aiofiles.open(backup_file, 'r') as f:
                        backup_data = json.loads(await f.read())
                        if data_manager._validate_data(backup_data):
                            logging.info(f"✅ Data recovered from {backup_file.name}")
                            await data_manager.save_data(backup_data, force=True)
                            break
                except Exception as e:
                    continue
        else:
            logging.debug("✅ Data integrity check passed")
            # Force save to ensure cloud sync
            await data_manager.save_data(data, force=True)
        
    except Exception as e:
        logging.error(f"Data verification error: {e}")

if __name__ == "__main__":
    # Load bot token from environment variable
    token = os.getenv('DISCORD_TOKEN') or os.getenv('BOT_TOKEN')
    if not token:
        print("❌ Please set DISCORD_TOKEN or BOT_TOKEN environment variable")
        exit(1)
    
    print("🚀 Starting SORABOT with advanced data protection...")
    bot.run(token)
