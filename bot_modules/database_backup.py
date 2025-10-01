"""
Database module: Using AGGRESSIVE data persistence 
ZERO TOLERANCE FOR DATA LOSS - Immediate saves on every operation
"""

import json
import aiofiles
import logging
from pathlib import Path

# Global variables for data persistence
DATA_FILE = 'data.json'
EMERGENCY_BACKUP = 'emergency_data.json'

# AGGRESSIVE data manager instance - will be set by main bot
_global_data_manager = None

def set_data_manager(manager):
    """Set the global data manager from main bot"""
    global _global_data_manager
    _global_data_manager = manager
    logging.info("🔗 Database module linked to AGGRESSIVE data manager")

class DataManager:
    """AGGRESSIVE data manager wrapper for bot modules"""
    
    async def init_database(self):
        """Initialize - no more SQLite issues!"""
        try:
            if _global_data_manager:
                test_data = await _global_data_manager.load_data()
                logging.info("✅ AGGRESSIVE data system verified")
                return True
            else:
                # Fallback to local loading
                test_data = await self.load_data()
                logging.info("✅ Local data system initialized")
                return True
        except Exception as e:
            logging.error(f"Data system initialization failed: {e}")
            return False
    
    async def save_data(self, data):
        """AGGRESSIVE save with force"""
        if _global_data_manager:
            return await _global_data_manager.save_data(data, force=True)
        else:
            # Fallback save
            return await self._fallback_save(data)
    
    async def load_data(self):
        """Load data with AGGRESSIVE recovery"""
        if _global_data_manager:
            return await _global_data_manager.load_data()
        else:
            # Fallback load
            return await self._fallback_load()
    
    async def _fallback_save(self, data):
        """Fallback save method"""
        try:
            async with aiofiles.open(DATA_FILE, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
            # Also save emergency backup
            async with aiofiles.open(EMERGENCY_BACKUP, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
            logging.info("💾 Fallback save completed")
            return True
        except Exception as e:
            logging.error(f"Fallback save failed: {e}")
            return False
    
    async def _fallback_load(self):
        """Fallback load method"""
        try:
            # Try primary file
            if Path(DATA_FILE).exists():
                async with aiofiles.open(DATA_FILE, 'r') as f:
                    return json.loads(await f.read())
            
            # Try emergency backup
            if Path(EMERGENCY_BACKUP).exists():
                async with aiofiles.open(EMERGENCY_BACKUP, 'r') as f:
                    return json.loads(await f.read())
            
            # Return default data
            return self._get_default_data()
            
        except Exception as e:
            logging.error(f"Fallback load failed: {e}")
            return self._get_default_data()
    
    def _get_default_data(self):
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
            "stock_prices": {},
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
                "economy_frozen": False
            },
            "bans": {},
            "cooldowns": {},
            "leaderboard_channel": None,
            "leaderboard_message": None,
            "_meta": {}
        }

# Global data manager instance
data_manager = DataManager()

# Helper functions with AGGRESSIVE saving
async def load_data():
    """Load data using the AGGRESSIVE system"""
    return await data_manager.load_data()

async def save_data(data):
    """Save data using the AGGRESSIVE system with FORCE"""
    return await data_manager.save_data(data)

import json
import aiofiles
import logging
from pathlib import Path

# Global variables for data persistence
DATA_FILE = 'data.json'
EMERGENCY_BACKUP = 'emergency_data.json'

# AGGRESSIVE data manager instance - will be set by main bot
_global_data_manager = None

def set_data_manager(manager):
    """Set the global data manager from main bot"""
    global _global_data_manager
    _global_data_manager = manager
    logging.info("🔗 Database module linked to AGGRESSIVE data manager")

class DataManager:
    """AGGRESSIVE data manager wrapper for bot modules"""
    
    async def init_database(self):
        """Initialize - no more SQLite issues!"""
        try:
            if _global_data_manager:
                test_data = await _global_data_manager.load_data()
                logging.info("✅ AGGRESSIVE data system verified")
                return True
            else:
                # Fallback to local loading
                test_data = await self.load_data()
                logging.info("✅ Local data system initialized")
                return True
        except Exception as e:
            logging.error(f"Data system initialization failed: {e}")
            return False
    
    async def save_data(self, data):
        """AGGRESSIVE save with force"""
        if _global_data_manager:
            return await _global_data_manager.save_data(data, force=True)
        else:
            # Fallback save
            return await self._fallback_save(data)
    
    async def load_data(self):
        """Load data with AGGRESSIVE recovery"""
        if _global_data_manager:
            return await _global_data_manager.load_data()
        else:
            # Fallback load
            return await self._fallback_load()
    
    async def _fallback_save(self, data):
        """Fallback save method"""
        try:
            async with aiofiles.open(DATA_FILE, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
            # Also save emergency backup
            async with aiofiles.open(EMERGENCY_BACKUP, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
            logging.info("💾 Fallback save completed")
            return True
        except Exception as e:
            logging.error(f"Fallback save failed: {e}")
            return False
    
    async def _fallback_load(self):
        """Fallback load method"""
        try:
            # Try primary file
            if Path(DATA_FILE).exists():
                async with aiofiles.open(DATA_FILE, 'r') as f:
                    return json.loads(await f.read())
            
            # Try emergency backup
            if Path(EMERGENCY_BACKUP).exists():
                async with aiofiles.open(EMERGENCY_BACKUP, 'r') as f:
                    return json.loads(await f.read())
            
            # Return default data
            return self._get_default_data()
            
        except Exception as e:
            logging.error(f"Fallback load failed: {e}")
            return self._get_default_data()
    
    def _get_default_data(self):
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
            "stock_prices": {},
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
                "economy_frozen": False
            },
            "bans": {},
            "cooldowns": {},
            "leaderboard_channel": None,
            "leaderboard_message": None,
            "_meta": {}
        }

# Global data manager instance
data_manager = DataManager()

# Helper functions with AGGRESSIVE saving
async def load_data():
    """Load data using the AGGRESSIVE system"""
    return await data_manager.load_data()

async def save_data(data):
    """Save data using the AGGRESSIVE system with FORCE"""
    return await data_manager.save_data(data)

# For backward compatibility, expose the same interface
class DataManager:
    """Compatibility wrapper for the new backup system"""
    
    def __init__(self):
        self.backup_manager = backup_manager
        
    async def init_database(self):
        """Initialize the backup system (no more SQLite issues!)"""
        try:
            # Test the backup system
            test_data = await self.backup_manager.load_data()
            logging.info("✅ Advanced backup system initialized successfully")
            return True
        except Exception as e:
            logging.error(f"Backup system initialization failed: {e}")
            return False
    
    async def save_data(self, data):
        """Save data using the new backup system"""
        return await self.backup_manager.save_data(data)
    
    async def load_data(self):
        """Load data using the new backup system"""
        return await self.backup_manager.load_data()

# Global data manager instance (maintains compatibility)
data_manager = DataManager()

# Helper functions for backward compatibility
async def load_data():
    """Load data using the backup system"""
    return await backup_load_data()

async def save_data(data):
    """Save data using the backup system"""
    return await backup_save_data(data)
        
    async def init_database(self):
        """Initialize SQLite database with proper schema"""
        try:
            # Ensure database directory exists
            db_path = Path(DATABASE_PATH)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiosqlite.connect(DATABASE_PATH) as db:
                # Main data table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS bot_data (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Individual user data for faster access
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS user_data (
                        user_id TEXT PRIMARY KEY,
                        coins INTEGER DEFAULT 0,
                        bank INTEGER DEFAULT 0,
                        inventory TEXT DEFAULT '{}',
                        equipment TEXT DEFAULT '{}',
                        stats TEXT DEFAULT '{}',
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Guild data
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS guild_data (
                        guild_id TEXT PRIMARY KEY,
                        name TEXT,
                        owner_id TEXT,
                        bank INTEGER DEFAULT 0,
                        members TEXT DEFAULT '[]',
                        settings TEXT DEFAULT '{}',
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Stock market data
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS stock_data (
                        symbol TEXT PRIMARY KEY,
                        price REAL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Transaction history
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        amount INTEGER,
                        type TEXT,
                        reason TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Backup history table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS backup_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        backup_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data_size INTEGER,
                        backup_type TEXT,
                        success BOOLEAN DEFAULT TRUE
                    )
                """)
                
                await db.commit()
                logging.info("Database initialized successfully")
                
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            # Create data.json as fallback
            default_data = self._get_default_data()
            await self._save_to_json(default_data)
            logging.info("Created JSON fallback due to database initialization failure")

    async def save_data(self, data):
        """Save data with multi-layer protection"""
        async with self._lock:
            try:
                self.save_count += 1
                
                # 1. Try to save to SQLite database (primary storage)
                database_success = False
                try:
                    await self._save_to_database(data)
                    database_success = True
                except Exception as e:
                    logging.warning(f"SQLite save failed: {e}, using JSON backup")
                
                # 2. Save to JSON file (backup)
                await self._save_to_json(data)
                
                # 3. Create timestamped backup every 5 saves
                if self.save_count % 5 == 0:
                    await self._create_timestamped_backup(data)
                
                # 4. Create remote backup every 20 saves
                if self.save_count % 20 == 0:
                    await self._create_remote_backup(data)
                
                # 5. Log successful save
                await self._log_backup("auto_save", len(json.dumps(data)), True)
                
                logging.info(f"Data saved successfully (save #{self.save_count})")
                
            except Exception as e:
                logging.error(f"Error saving data: {e}")
                # Try to save to emergency backup
                await self._emergency_backup(data)
                await self._log_backup("emergency", len(json.dumps(data)), False)

    async def load_data(self):
        """Load data with fallback options"""
        try:
            # Try SQLite first (primary)
            data = await self._load_from_database()
            if data and self._validate_data(data):
                logging.info("Data loaded from SQLite database")
                return data
                
            # Fallback to JSON file
            logging.warning("SQLite failed, trying JSON backup")
            data = await self._load_from_json()
            if data and self._validate_data(data):
                # Restore to database
                await self._save_to_database(data)
                logging.info("Data loaded from JSON backup and restored to database")
                return data
                
            # Try timestamped backups
            logging.warning("JSON failed, trying timestamped backups")
            data = await self._load_latest_backup()
            if data and self._validate_data(data):
                await self._save_to_database(data)
                await self._save_to_json(data)
                logging.info("Data loaded from timestamped backup")
                return data
                
            # Last resort - empty data structure
            logging.warning("All backups failed, starting fresh")
            return self._get_default_data()
            
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            return self._get_default_data()

    async def _save_to_database(self, data):
        """Save to SQLite database with normalized structure"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                # Save complete data as JSON blob
                data_json = json.dumps(data, indent=2)
                await db.execute(
                    "INSERT OR REPLACE INTO bot_data (key, value, last_updated) VALUES (?, ?, ?)",
                    ("main_data", data_json, datetime.now().isoformat())
                )
            
            # Save individual user data for faster queries
            for user_id, coins in data.get("coins", {}).items():
                bank = data.get("bank", {}).get(user_id, 0)
                inventory = json.dumps(data.get("inventories", {}).get(user_id, {}))
                equipment = json.dumps(data.get("equipment", {}).get(user_id, {}))
                
                await db.execute("""
                    INSERT OR REPLACE INTO user_data 
                    (user_id, coins, bank, inventory, equipment, last_updated) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, coins, bank, inventory, equipment, datetime.now().isoformat()))
            
            # Save guild data
            for guild_name, guild_data in data.get("guilds", {}).items():
                members = json.dumps(data.get("guild_members", {}).get(guild_name, []))
                await db.execute("""
                    INSERT OR REPLACE INTO guild_data 
                    (guild_id, name, owner_id, bank, members, last_updated) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (guild_name, guild_name, guild_data.get("owner"), 
                     guild_data.get("bank", 0), members, datetime.now().isoformat()))
            
            # Save stock prices
            for symbol, price in data.get("stock_prices", {}).items():
                await db.execute("""
                    INSERT OR REPLACE INTO stock_data (symbol, price, last_updated) 
                    VALUES (?, ?, ?)
                """, (symbol, price, datetime.now().isoformat()))
            
            await db.commit()
                
        except Exception as e:
            logging.error(f"Error saving to database: {e}")
            raise  # Re-raise so save_data can handle fallback

    async def _load_from_database(self):
        """Load from SQLite database"""
        try:
            # Check if database file exists
            if not Path(DATABASE_PATH).exists():
                logging.warning(f"Database file {DATABASE_PATH} does not exist")
                return None
                
            async with aiosqlite.connect(DATABASE_PATH) as db:
                cursor = await db.execute(
                    "SELECT value FROM bot_data WHERE key = ?",
                    ("main_data",)
                )
                row = await cursor.fetchone()
                if row and row[0]:
                    return json.loads(row[0])
                else:
                    logging.warning("No main_data found in database")
                    return None
                    
        except Exception as e:
            logging.error(f"Error loading from database: {e}")
            return None

    async def _save_to_json(self, data):
        """Save to JSON file backup"""
        try:
            async with aiofiles.open(DATA_PATH, 'w') as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logging.error(f"Failed to save JSON backup: {e}")

    async def _load_from_json(self):
        """Load from JSON file backup"""
        try:
            async with aiofiles.open(DATA_PATH, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except:
            return None

    async def _create_timestamped_backup(self, data):
        """Create timestamped backup file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = Path(__file__).parent.parent / f"backup_{timestamp}.json"
            
            async with aiofiles.open(backup_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))
                
            # Keep only last 10 backup files
            await self._cleanup_old_backups()
            
            logging.info(f"Timestamped backup created: {backup_file}")
            
        except Exception as e:
            logging.error(f"Timestamped backup failed: {e}")

    async def _load_latest_backup(self):
        """Load the most recent timestamped backup"""
        try:
            backup_dir = Path(__file__).parent.parent
            backup_files = list(backup_dir.glob("backup_*.json"))
            
            if not backup_files:
                return None
                
            # Sort by timestamp (newest first)
            backup_files.sort(reverse=True)
            
            for backup_file in backup_files:
                try:
                    async with aiofiles.open(backup_file, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        if self._validate_data(data):
                            logging.info(f"Loaded backup from {backup_file}")
                            return data
                except:
                    continue
                    
            return None
            
        except Exception as e:
            logging.error(f"Failed to load backup: {e}")
            return None

    async def _cleanup_old_backups(self):
        """Keep only the 10 most recent backup files"""
        try:
            backup_dir = Path(__file__).parent.parent
            backup_files = list(backup_dir.glob("backup_*.json"))
            
            if len(backup_files) > 10:
                # Sort by timestamp (oldest first) and remove excess
                backup_files.sort()
                for old_file in backup_files[:-10]:
                    old_file.unlink()
                    
        except Exception as e:
            logging.error(f"Backup cleanup failed: {e}")

    async def _create_remote_backup(self, data):
        """Create remote backup via Discord webhook"""
        if not self.backup_webhook:
            return
            
        try:
            # Create backup summary
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "user_count": len(data.get("coins", {})),
                "total_coins": sum(data.get("coins", {}).values()),
                "total_bank": sum(data.get("bank", {}).values()),
                "guild_count": len(data.get("guilds", {})),
                "data_size": len(json.dumps(data))
            }
            
            async with aiohttp.ClientSession() as session:
                webhook_data = {
                    "embeds": [{
                        "title": "🔄 SORABOT Data Backup",
                        "description": f"Automatic backup #{self.save_count} created",
                        "fields": [
                            {"name": "👥 Users", "value": str(backup_data["user_count"]), "inline": True},
                            {"name": "💰 Total Coins", "value": f"{backup_data['total_coins']:,}", "inline": True},
                            {"name": "🏦 Total Bank", "value": f"{backup_data['total_bank']:,}", "inline": True},
                            {"name": "🏰 Guilds", "value": str(backup_data["guild_count"]), "inline": True},
                            {"name": "📊 Data Size", "value": f"{backup_data['data_size']:,} bytes", "inline": True},
                            {"name": "⏰ Backup Time", "value": backup_data["timestamp"], "inline": True}
                        ],
                        "timestamp": backup_data["timestamp"],
                        "color": 0x00ff00,
                        "footer": {"text": "SORABOT Auto-Backup System"}
                    }]
                }
                
                # Send backup notification
                await session.post(self.backup_webhook, json=webhook_data)
                
            # Log backup
            await self._log_backup("remote_webhook", backup_data["data_size"], True)
                
            logging.info("Remote backup notification sent successfully")
            
        except Exception as e:
            logging.error(f"Remote backup failed: {e}")

    async def _emergency_backup(self, data):
        """Emergency backup to timestamped file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            emergency_file = Path(__file__).parent.parent / f"EMERGENCY_backup_{timestamp}.json"
            
            async with aiofiles.open(emergency_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))
                
            logging.critical(f"EMERGENCY backup saved to {emergency_file}")
            
        except Exception as e:
            logging.critical(f"EMERGENCY backup failed: {e}")

    async def _log_backup(self, backup_type, data_size, success):
        """Log backup to database"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute(
                    "INSERT INTO backup_history (data_size, backup_type, success) VALUES (?, ?, ?)",
                    (data_size, backup_type, success)
                )
                await db.commit()
        except:
            pass

    def _validate_data(self, data):
        """Validate data structure"""
        if not isinstance(data, dict):
            return False
            
        # Check for required keys
        required_keys = ["coins", "bank"]
        for key in required_keys:
            if key not in data:
                return False
                
        return True

    def _get_default_data(self):
        """Default data structure"""
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
            "equipment": {},
            "guilds": {},
            "guild_members": {},
            "guild_invites": {},
            "stock_holdings": {},
            "stock_portfolios": {},
            "stock_market": {
                "price_history": {}
            },
            "stock_prices": {
                "SORACOIN": 108.87,
                "LUCKYST": 57.78,
                "GUILDCO": 79.89,
                "MINING": 187.37,
                "TECHNO": 150.0,
                "BANKCO": 80.0,
                "MINERS": 45.0,
                "FOODIE": 60.0
            },
            "consumable_effects": {},
            "loot_tables": {
                "common": {
                    "coins": {"weight": 70, "min": 50, "max": 200},
                    "items": {"weight": 25, "pool": ["lucky_potion", "jackpot_booster", "robbers_mask"]},
                    "special": {"weight": 5, "pool": ["gamblers_charm", "lucky_coin"]}
                },
                "rare": {
                    "coins": {"weight": 50, "min": 150, "max": 500},
                    "items": {"weight": 40, "pool": ["mega_lucky_potion", "insurance_scroll", "master_lockpick", "shadow_cloak"]},
                    "special": {"weight": 10, "pool": ["golden_dice", "security_dog"]}
                },
                "epic": {
                    "coins": {"weight": 30, "min": 300, "max": 1000},
                    "items": {"weight": 60, "pool": ["mimic_repellent", "vault_key", "golden_dice", "security_dog"]},
                    "special": {"weight": 10, "pool": ["rare_chest", "epic_chest"]}
                },
                "legendary": {
                    "coins": {"weight": 10, "min": 800, "max": 2500},
                    "items": {"weight": 80, "pool": ["vault_key", "security_dog", "mimic_repellent", "mega_lucky_potion"]},
                    "special": {"weight": 10, "pool": ["epic_chest", "legendary_chest"]}
                }
            },
            "shop_items": {
                "consumables": {
                    "lucky_potion": {
                        "name": "Lucky Potion", "price": 150, "rarity": "Common",
                        "effect": "gambling_bonus", "value": 0.2,
                        "description": "Increases casino win chance by 20% for next game",
                        "emoji": "🍀"
                    },
                    "mega_lucky_potion": {
                        "name": "Mega Lucky Potion", "price": 400, "rarity": "Rare",
                        "effect": "gambling_bonus", "value": 0.5,
                        "description": "Increases casino win chance by 50% for next game",
                        "emoji": "🔮"
                    },
                    "jackpot_booster": {
                        "name": "Jackpot Booster", "price": 200, "rarity": "Common",
                        "effect": "payout_bonus", "value": 0.1,
                        "description": "Increases casino payouts by 10% for next game",
                        "emoji": "💰"
                    },
                    "robbers_mask": {
                        "name": "Robber's Mask", "price": 250, "rarity": "Common",
                        "effect": "rob_success", "value": 0.15,
                        "description": "Increases robbery success chance by 15%",
                        "emoji": "🎭"
                    },
                    "insurance_scroll": {
                        "name": "Insurance Scroll", "price": 300, "rarity": "Rare",
                        "effect": "loss_protection", "value": 0.5,
                        "description": "Refunds 50% of lost bets in casino games",
                        "emoji": "🛡️"
                    },
                    "mimic_repellent": {
                        "name": "Mimic Repellent", "price": 500, "rarity": "Epic",
                        "effect": "mimic_protection", "value": 1.0,
                        "description": "Completely blocks mimic attacks from chests",
                        "emoji": "💊"
                    }
                },
                "equipables": {
                    "gamblers_charm": {
                        "name": "Gambler's Charm", "price": 400, "rarity": "Common",
                        "slot": "accessory", "effect": "gambling_bonus", "value": 0.05,
                        "description": "Permanently increases gambling win chance by 5%",
                        "emoji": "🎲"
                    },
                    "golden_dice": {
                        "name": "Golden Dice", "price": 600, "rarity": "Rare",
                        "slot": "accessory", "effect": "payout_bonus", "value": 0.1,
                        "description": "Permanently increases slots payouts by 10%",
                        "emoji": "🎯"
                    },
                    "security_dog": {
                        "name": "Security Dog", "price": 700, "rarity": "Rare",
                        "slot": "pet", "effect": "rob_protection", "value": 1.0,
                        "description": "Completely blocks robbery attempts against you",
                        "emoji": "🐕"
                    },
                    "vault_key": {
                        "name": "Vault Key", "price": 800, "rarity": "Epic",
                        "slot": "accessory", "effect": "bank_interest", "value": 0.0025,
                        "description": "Increases bank interest rate by 0.25%",
                        "emoji": "🗝️"
                    },
                    "master_lockpick": {
                        "name": "Master Lockpick", "price": 750, "rarity": "Rare",
                        "slot": "tool", "effect": "rob_success", "value": 0.1,
                        "description": "Permanently increases robbery success by 10%",
                        "emoji": "🔓"
                    },
                    "lucky_coin": {
                        "name": "Lucky Coin", "price": 300, "rarity": "Common",
                        "slot": "accessory", "effect": "ratrace_bonus", "value": 0.05,
                        "description": "Increases rat race winnings by 5%",
                        "emoji": "🪙"
                    },
                    "shadow_cloak": {
                        "name": "Shadow Cloak", "price": 600, "rarity": "Rare",
                        "slot": "armor", "effect": "rob_stealth", "value": 0.15,
                        "description": "Reduces chance of being robbed by 15%",
                        "emoji": "🥷"
                    }
                },
                "chests": {
                    "common_chest": {
                        "name": "Common Chest", "price": 100, "rarity": "Common",
                        "description": "Contains random rewards with 5% mimic chance",
                        "emoji": "📦", "loot_table": "common", "mimic_chance": 0.05
                    },
                    "rare_chest": {
                        "name": "Rare Chest", "price": 300, "rarity": "Rare",
                        "description": "Contains better rewards with 10% mimic chance",
                        "emoji": "🎁", "loot_table": "rare", "mimic_chance": 0.10
                    },
                    "epic_chest": {
                        "name": "Epic Chest", "price": 600, "rarity": "Epic",
                        "description": "Contains excellent rewards with 15% mimic chance",
                        "emoji": "💎", "loot_table": "epic", "mimic_chance": 0.15
                    },
                    "legendary_chest": {
                        "name": "Legendary Chest", "price": 1200, "rarity": "Legendary",
                        "description": "Contains amazing rewards with 20% mimic chance",
                        "emoji": "👑", "loot_table": "legendary", "mimic_chance": 0.20
                    }
                }
            },
            "config": {
                "min_bet": 10, "max_bet": 1000000,
                "daily_amount": 150, "weekly_amount": 1000,
                "interest_rate": 0.001, "interest_tick_minutes": 10,
                "market_tick_minutes": 10, "economy_frozen": False,
                "rob_cooldown_hours": 1, "rob_success_rate": 0.3,
                "rob_max_steal_percent": 0.2, "rob_fine_percent": 0.1
            },
            "bans": {}, "cooldowns": {},
            "leaderboard_channel": None, "leaderboard_message": None,
            "_meta": {
                "last_interest_ts": "2025-09-30T18:53:05.318089",
                "last_market_ts": "2025-09-19T11:22:09.890710"
            }
        }

# Global data manager instance
data_manager = DataManager()

# Helper functions for backward compatibility
async def load_data():
    """Load data using the data manager"""
    return await data_manager.load_data()

async def save_data(data):
    """Save data using the data manager"""
    await data_manager.save_data(data)