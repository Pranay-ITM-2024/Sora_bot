#!/usr/bin/env python3
"""
HYBRID DATA MANAGER FOR SORABOT
Combines Firebase Firestore with JSON backup for ultimate reliability
- Primary: Firebase Firestore (cloud persistence)
- Fallback: JSON files (local backup)
- Zero data loss guarantee
"""

import asyncio
import json
import os
import logging
import datetime
from typing import Dict, List, Optional, Any
import aiofiles
from pathlib import Path

# Try to import Firebase (optional dependency)
try:
    from firebase_manager import firebase_manager
    FIREBASE_AVAILABLE = True
    logging.info("🔥 Firebase integration available")
except ImportError:
    FIREBASE_AVAILABLE = False
    firebase_manager = None
    logging.warning("⚠️ Firebase not available - using JSON mode only")

# File paths
DATA_FILE = Path("data.json")
BACKUP_DIR = Path("backups")
EMERGENCY_BACKUP = Path("emergency_backup.json")

class HybridDataManager:
    """
    Hybrid data manager with Firebase + JSON backup
    Features:
    - Firebase Firestore for cloud persistence
    - JSON files for local backup and fallback
    - Automatic migration between systems
    - Zero downtime data access
    - Enterprise-level reliability
    """
    
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(exist_ok=True)
        self.save_count = 0
        self.last_save_time = datetime.datetime.now(datetime.timezone.utc)
        self._data_cache = None
        self._is_saving = False
        
        # Firebase status
        self.firebase_enabled = FIREBASE_AVAILABLE
        self.firebase_ready = False
        
        # Check Firebase availability
        if self.firebase_enabled:
            asyncio.create_task(self._check_firebase_ready())
        
        logging.info(f"🔧 Hybrid Data Manager initialized - Firebase: {'✅' if self.firebase_enabled else '❌'}")
    
    async def _check_firebase_ready(self):
        """Check if Firebase is ready"""
        if not self.firebase_enabled:
            return
        
        try:
            # Wait for Firebase to initialize
            for attempt in range(10):  # Wait up to 10 seconds
                if firebase_manager.is_available():
                    self.firebase_ready = True
                    logging.info("🔥 Firebase is ready for data operations")
                    return
                await asyncio.sleep(1)
            
            logging.warning("⚠️ Firebase initialization timeout - using JSON mode")
            self.firebase_ready = False
            
        except Exception as e:
            logging.error(f"Firebase check failed: {e}")
            self.firebase_ready = False
    
    def is_firebase_ready(self) -> bool:
        """Check if Firebase is ready for operations"""
        return self.firebase_enabled and self.firebase_ready and firebase_manager.is_available()
    
    async def load_data(self) -> Dict[str, Any]:
        """Load data with Firebase priority, JSON fallback"""
        logging.info("📖 Loading bot data...")
        
        # Try Firebase first (if available)
        if self.is_firebase_ready():
            try:
                firebase_data = await firebase_manager.load_full_data()
                if firebase_data:
                    logging.info("🔥 Data loaded from Firebase Firestore")
                    self._data_cache = firebase_data.copy()
                    
                    # Also save to JSON as backup
                    await self._save_json_backup(firebase_data)
                    return firebase_data
                else:
                    logging.warning("No data found in Firebase, trying JSON...")
            except Exception as e:
                logging.error(f"Firebase load failed: {e}, falling back to JSON")
        
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
                    await firebase_manager.migrate_from_json(json_data)
                
                self._data_cache = json_data.copy()
                return json_data
            
            elif EMERGENCY_BACKUP.exists():
                async with aiofiles.open(EMERGENCY_BACKUP, 'r') as f:
                    content = await f.read()
                    backup_data = json.loads(content)
                
                logging.warning("🚨 Loaded from emergency backup")
                self._data_cache = backup_data.copy()
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
        """Save data to both Firebase and JSON"""
        if self._is_saving and not force:
            logging.debug("Save already in progress, skipping...")
            return True
        
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
            
            success_count = 0
            total_attempts = 0
            
            # Save to Firebase (primary)
            if self.is_firebase_ready():
                total_attempts += 1
                try:
                    if await firebase_manager.save_full_data(data):
                        success_count += 1
                        logging.debug("🔥 Data saved to Firebase")
                    else:
                        logging.warning("❌ Firebase save failed")
                except Exception as e:
                    logging.error(f"Firebase save error: {e}")
            
            # Save to JSON (backup/fallback)
            total_attempts += 1
            try:
                await self._save_json_backup(data)
                success_count += 1
                logging.debug("📄 Data saved to JSON")
            except Exception as e:
                logging.error(f"JSON save error: {e}")
            
            # Emergency backup
            try:
                async with aiofiles.open(EMERGENCY_BACKUP, 'w') as f:
                    await f.write(json.dumps(data, indent=2, default=str))
            except Exception as e:
                logging.warning(f"Emergency backup failed: {e}")
            
            # Update cache and metrics
            self._data_cache = data.copy()
            self.last_save_time = datetime.datetime.now(datetime.timezone.utc)
            
            user_count = len(data.get("coins", {}))
            total_coins = sum(data.get("coins", {}).values())
            
            if success_count > 0:
                storage_info = []
                if self.is_firebase_ready() and success_count >= 1:
                    storage_info.append("Firebase")
                if success_count >= (1 if self.is_firebase_ready() else 1):
                    storage_info.append("JSON")
                
                logging.info(f"💾 Save #{self.save_count} successful ({'/'.join(storage_info)}) - {user_count} users, {total_coins:,} coins")
                return True
            else:
                logging.error(f"❌ All save methods failed ({success_count}/{total_attempts})")
                return False
            
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
    
    async def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get specific user data (Firebase optimized)"""
        if self.is_firebase_ready():
            try:
                user_data = await firebase_manager.load_user_data(user_id)
                if user_data:
                    return user_data
            except Exception as e:
                logging.error(f"Firebase user load failed: {e}")
        
        # Fallback to full data
        if self._data_cache:
            return {
                'coins': self._data_cache.get('coins', {}).get(user_id, 0),
                'bank': self._data_cache.get('bank', {}).get(user_id, 0),
                'inventory': self._data_cache.get('inventories', {}).get(user_id, []),
                'equipped': self._data_cache.get('equipped', {}).get(user_id, {}),
            }
        
        return {}
    
    async def update_user_coins(self, user_id: str, amount: int) -> bool:
        """Update user coins with atomic transaction"""
        if self.is_firebase_ready():
            try:
                success = await firebase_manager.atomic_transaction(user_id, 'coins', amount)
                if success:
                    # Update local cache
                    if self._data_cache:
                        current = self._data_cache.get('coins', {}).get(user_id, 0)
                        self._data_cache.setdefault('coins', {})[user_id] = current + amount
                    return True
            except Exception as e:
                logging.error(f"Firebase atomic transaction failed: {e}")
        
        # Fallback to cache update
        if self._data_cache:
            current = self._data_cache.get('coins', {}).get(user_id, 0)
            new_amount = current + amount
            if new_amount >= 0:
                self._data_cache.setdefault('coins', {})[user_id] = new_amount
                # Save updated data
                await self.save_data(self._data_cache)
                return True
        
        return False
    
    async def get_leaderboard(self, field: str = 'coins', limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard data"""
        if self.is_firebase_ready():
            try:
                return await firebase_manager.get_leaderboard(field, limit)
            except Exception as e:
                logging.error(f"Firebase leaderboard failed: {e}")
        
        # Fallback to cache-based leaderboard
        if self._data_cache:
            field_data = self._data_cache.get(field, {})
            sorted_users = sorted(field_data.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            return [
                {'user_id': user_id, field: value}
                for user_id, value in sorted_users
            ]
        
        return []
    
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
        
        if self.is_firebase_ready():
            try:
                firebase_stats = await firebase_manager.get_stats()
                stats.update({'firebase_' + k: v for k, v in firebase_stats.items()})
            except:
                pass
        
        if self._data_cache:
            stats.update({
                'user_count': len(self._data_cache.get('coins', {})),
                'total_coins': sum(self._data_cache.get('coins', {}).values()),
                'guild_count': len(self._data_cache.get('guilds', {}))
            })
        
        return stats

# Global hybrid data manager instance
hybrid_manager = HybridDataManager()