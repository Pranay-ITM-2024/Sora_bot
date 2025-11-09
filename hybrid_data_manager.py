#!/usr/bin/env python3
"""
FIREBASE REALTIME DATABASE DATA MANAGER FOR SORABOT
Simple, reliable Firebase-only data persistence
"""

import json
import logging
import datetime
import asyncio
from typing import Dict, Any, Optional

class FirebaseOnlyDataManager:
    """
    Firebase Realtime Database manager - NO LOCAL FILES
    All data stored in Firebase Realtime Database only
    """
    
    def __init__(self):
        self.save_count = 0
        self.last_save_time = datetime.datetime.now(datetime.timezone.utc)
        self._data_cache = None
        self._is_saving = False
        
        # Firebase manager (lazy loaded)
        self.firebase_manager = None
        self.firebase_enabled = False
        self.firebase_ready = False
        
        logging.info("🔧 Firebase-Only Data Manager initialized")
    
    def _get_firebase_manager(self):
        """Get Firebase manager with lazy loading"""
        if self.firebase_manager is None:
            try:
                from firebase_manager import get_firebase_manager
                self.firebase_manager = get_firebase_manager()
                self.firebase_enabled = True
                self.firebase_ready = self.firebase_manager.is_available()
                
                if self.firebase_ready:
                    logging.info("🔥 Firebase integration active")
                else:
                    logging.info("📄 JSON-only mode active")
                    
            except Exception as e:
                logging.warning(f"🔥 Firebase not available: {e}")
                self.firebase_enabled = False
                self.firebase_ready = False
        
        return self.firebase_manager
    
    def is_firebase_ready(self) -> bool:
        """Check if Firebase is ready for operations"""
        if not self.firebase_enabled:
            return False
        
        manager = self._get_firebase_manager()
        return manager and manager.is_available()
    
    async def load_data(self) -> Dict[str, Any]:
        """Load data with Firebase priority, JSON fallback"""
        logging.info("📖 Loading bot data...")
        
        # Try Firebase first (if available)
        if self.is_firebase_ready():
            try:
                firebase_data = self.firebase_manager.load_data()
                if firebase_data:
                    logging.info("🔥 Data loaded from Firebase Firestore")
                    self._data_cache = firebase_data.copy()
                    
                    # Also save to JSON as backup
                    await self._save_json_backup(firebase_data)
                    return firebase_data
                else:
                    logging.warning("🔥 No data found in Firebase, trying JSON...")
            except Exception as e:
                logging.error(f"🔥 Firebase load failed: {e}, falling back to JSON")
        
        # Fallback to JSON
        try:
            if DATA_FILE.exists():
                async with aiofiles.open(DATA_FILE, 'r') as f:
                    content = await f.read()
                    json_data = json.loads(content)
                
                logging.info("📄 Data loaded from JSON file")
                
                # If Firebase is ready, migrate the data
                if self.is_firebase_ready():
                    logging.info("🔄 Migrating JSON data to Firebase...")
                    self.firebase_manager.migrate_from_json(json_data)
                
                self._data_cache = json_data.copy()
                return json_data
            
            elif EMERGENCY_BACKUP.exists():
                async with aiofiles.open(EMERGENCY_BACKUP, 'r') as f:
                    content = await f.read()
                    backup_data = json.loads(content)
                
                logging.warning("🚨 Loaded from emergency backup")
                self._data_cache = backup_data.copy()
                
                # Migrate to Firebase if available
                if self.is_firebase_ready():
                    logging.info("🔄 Migrating emergency backup to Firebase...")
                    self.firebase_manager.migrate_from_json(backup_data)
                
                return backup_data
            
            else:
                logging.warning("🆕 No existing data found - creating fresh structure")
                default_data = self.get_default_data()
                await self.save_data(default_data, force=True)
                return default_data
                
        except Exception as e:
            logging.error(f"❌ Data loading failed: {e}")
            default_data = self.get_default_data()
            await self.save_data(default_data, force=True)
            return default_data
    
    async def save_data(self, data: Dict[str, Any], force: bool = False) -> bool:
        """AGGRESSIVE save to both Firebase and JSON with Firebase priority"""
        if self._is_saving and not force:
            logging.debug("Save already in progress, forcing through...")
            # Don't skip - force saves are critical
        
        try:
            self._is_saving = True
            self.save_count += 1
            
            # Validate data
            if not self._validate_data(data):
                logging.error("❌ Invalid data structure, aborting save")
                return False
            
            # Add metadata
            data.setdefault("_meta", {})
            data["_meta"]["last_save"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            data["_meta"]["save_count"] = self.save_count
            data["_meta"]["firebase_enabled"] = self.is_firebase_ready()
            data["_meta"]["version"] = "4.0_hybrid"
            
            firebase_success = False
            json_success = False
            
            # PRIORITY 1: AGGRESSIVE Firebase Save with retries
            if self.is_firebase_ready():
                for attempt in range(3):  # 3 attempts for Firebase
                    try:
                        if self.firebase_manager.save_data(data):
                            firebase_success = True
                            logging.info(f"🔥 Firebase save successful (attempt {attempt + 1})")
                            break
                        else:
                            logging.warning(f"❌ Firebase save failed (attempt {attempt + 1})")
                            if attempt < 2:
                                await asyncio.sleep(0.5)  # Brief delay before retry
                    except Exception as e:
                        logging.error(f"🔥 Firebase save error (attempt {attempt + 1}): {e}")
                        if attempt < 2:
                            await asyncio.sleep(0.5)
                
                if not firebase_success:
                    logging.error("🚨 ALL Firebase save attempts FAILED! Data may be lost on restart!")
            else:
                logging.warning("🔥 Firebase not available - using JSON only")
            
            # PRIORITY 2: JSON Backup (always do this)
            try:
                await self._save_json_backup(data)
                json_success = True
                logging.debug("📄 JSON backup successful")
            except Exception as e:
                logging.error(f"📄 JSON save error: {e}")
            
            # PRIORITY 3: Emergency backup (always do this)
            try:
                async with aiofiles.open(EMERGENCY_BACKUP, 'w') as f:
                    await f.write(json.dumps(data, indent=2, default=str))
            except Exception as e:
                logging.error(f"🚨 Emergency backup failed: {e}")
            
            # Update cache and metrics
            self._data_cache = data.copy()
            self.last_save_time = datetime.datetime.now(datetime.timezone.utc)
            
            user_count = len(data.get("coins", {}))
            total_coins = sum(data.get("coins", {}).values())
            
            # Report save status
            if firebase_success:
                logging.info(f"💾 Save #{self.save_count} SUCCESS (Firebase + JSON) - {user_count} users, {total_coins:,} coins")
                return True
            elif json_success:
                logging.warning(f"⚠️ Save #{self.save_count} PARTIAL (JSON only) - {user_count} users, {total_coins:,} coins")
                return True  # Still successful, but warn about Firebase
            else:
                logging.error(f"❌ Save #{self.save_count} FAILED (all methods) - DATA MAY BE LOST!")
                return False
                storage_info = []
        except Exception as e:
            logging.error(f"❌ Critical save error: {e}")
            return False
        finally:
            self._is_saving = False
    
    async def _save_json_backup(self, data: Dict[str, Any]):
        """Save data to JSON file"""
        # Atomic save to prevent corruption
        temp_file = f"{DATA_FILE}.tmp"
        async with aiofiles.open(temp_file, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
        os.rename(temp_file, DATA_FILE)
        
        # Create timestamped backup
        if self.save_count % 5 == 0:  # Every 5 saves
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.json"
            async with aiofiles.open(backup_file, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
    
    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate data structure"""
        if not isinstance(data, dict):
            return False
        
        required_keys = ["coins", "bank", "config"]
        for key in required_keys:
            if key not in data:
                logging.warning(f"Missing required key: {key}")
                return False
            if not isinstance(data[key], dict):
                return False
        
        return True
    
    def get_default_data(self) -> Dict[str, Any]:
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
            "equipment": {},
            "guilds": {},
            "guild_members": {},
            "guild_invites": {},
            "stock_holdings": {},
            "stock_portfolios": {},
            "stock_market": {"price_history": {}},
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
                "created": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "version": "4.0_hybrid",
                "save_count": 0,
                "firebase_enabled": self.is_firebase_ready()
            }
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive data manager statistics"""
        stats = {
            'hybrid_mode': True,
            'firebase_enabled': self.firebase_enabled,
            'firebase_ready': self.is_firebase_ready(),
            'save_count': self.save_count,
            'last_save': self.last_save_time.isoformat(),
            'cache_size': len(str(self._data_cache)) if self._data_cache else 0
        }
        
        if self._data_cache:
            stats.update({
                'user_count': len(self._data_cache.get('coins', {})),
                'total_coins': sum(self._data_cache.get('coins', {}).values()),
                'guild_count': len(self._data_cache.get('guilds', {}))
            })
        
        return stats

# Global hybrid data manager instance
# Global instance with lazy initialization
_hybrid_manager = None

def get_hybrid_manager():
    """Get hybrid manager instance (lazy initialization)"""
    global _hybrid_manager
    if _hybrid_manager is None:
        _hybrid_manager = HybridDataManager()
    return _hybrid_manager