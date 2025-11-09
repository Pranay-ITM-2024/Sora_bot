#!/usr/bin/env python3
"""
FIREBASE REALTIME DATABASE DATA MANAGER FOR SORABOT
Simple, reliable Firebase-only data persistence - NO LOCAL FILES
"""

import json
import logging
import datetime
import asyncio
from typing import Dict, Any, Optional

class FirebaseOnlyDataManager:
    """
    Firebase Realtime Database manager - Single source of truth
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
        
        logging.info("🔥 Firebase-Only Data Manager initialized")
    
    def _get_firebase_manager(self):
        """Get Firebase manager with lazy loading"""
        if self.firebase_manager is None:
            try:
                from firebase_manager import get_firebase_manager
                self.firebase_manager = get_firebase_manager()
                self.firebase_enabled = True
                self.firebase_ready = self.firebase_manager.is_available()
                
                if self.firebase_ready:
                    logging.info("🔥 Firebase Realtime Database integration active")
                else:
                    logging.error("❌ Firebase NOT available - bot will NOT work without Firebase!")
                    
            except Exception as e:
                logging.error(f"🔥 Firebase not available: {e}")
                self.firebase_enabled = False
                self.firebase_ready = False
        
        return self.firebase_manager
    
    def is_firebase_ready(self) -> bool:
        """Check if Firebase is ready"""
        if not self.firebase_ready:
            self._get_firebase_manager()
        return self.firebase_ready
    
    async def load_data(self) -> Dict[str, Any]:
        """Load data from Firebase Realtime Database ONLY"""
        try:
            # Try Firebase first
            if self.is_firebase_ready():
                firebase_data = self.firebase_manager.load_data()
                
                if firebase_data:
                    logging.info(f"🔥 Data loaded from Firebase Realtime Database - {len(firebase_data.get('coins', {}))} users")
                    self._data_cache = firebase_data.copy()
                    return firebase_data
                else:
                    logging.warning("🔥 No data in Firebase - creating fresh structure")
                    default_data = self.get_default_data()
                    await self.save_data(default_data, force=True)
                    return default_data
            else:
                logging.error("❌ Firebase is NOT available - bot cannot function!")
                logging.error("❌ Please check your Firebase credentials and configuration")
                return self.get_default_data()
                
        except Exception as e:
            logging.error(f"❌ Data load failed: {e}")
            return self.get_default_data()
    
    async def save_data(self, data: Dict[str, Any], force: bool = False) -> bool:
        """SAVE to Firebase Realtime Database ONLY - with retries"""
        if self._is_saving and not force:
            logging.debug("Save already in progress, forcing through...")
        
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
            data["_meta"]["version"] = "5.0_firebase_only"
            
            firebase_success = False
            
            # FIREBASE SAVE with retries
            if self.is_firebase_ready():
                for attempt in range(3):  # 3 attempts
                    try:
                        if self.firebase_manager.save_data(data):
                            firebase_success = True
                            logging.info(f"🔥 Firebase save successful (attempt {attempt + 1})")
                            break
                        else:
                            logging.warning(f"❌ Firebase save failed (attempt {attempt + 1})")
                            if attempt < 2:
                                await asyncio.sleep(0.5)
                    except Exception as e:
                        logging.error(f"🔥 Firebase save error (attempt {attempt + 1}): {e}")
                        if attempt < 2:
                            await asyncio.sleep(0.5)
                
                if not firebase_success:
                    logging.error("🚨 ALL Firebase save attempts FAILED! Data may be lost!")
                    return False
            else:
                logging.error("❌ Firebase not available - cannot save data!")
                return False
            
            # Update cache and metrics
            self._data_cache = data.copy()
            self.last_save_time = datetime.datetime.now(datetime.timezone.utc)
            
            user_count = len(data.get("coins", {}))
            total_coins = sum(data.get("coins", {}).values())
            
            logging.info(f"💾 COMMAND SAVE #{self.save_count} → Firebase Realtime DB ✅ - {user_count} users, {total_coins:,} coins")
            return True
            
        except Exception as e:
            logging.error(f"❌ Critical save error: {e}")
            return False
        finally:
            self._is_saving = False
    
    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate data structure - auto-fix missing keys"""
        if not isinstance(data, dict):
            return False
        
        # Auto-add missing required keys
        required_keys = ["coins", "bank", "config"]
        for key in required_keys:
            if key not in data:
                logging.info(f"🔧 Auto-adding missing key: {key}")
                if key == "config":
                    data[key] = {
                        "daily_amount": 150,
                        "weekly_amount": 1000,
                        "initial_coins": 100
                    }
                else:
                    data[key] = {}
            
            # Ensure it's a dict
            if not isinstance(data[key], dict):
                logging.warning(f"⚠️ Fixing invalid type for {key}, converting to dict")
                data[key] = {}
        
        return True
    
    def get_default_data(self) -> Dict[str, Any]:
        """Get default data structure"""
        return {
            "coins": {},
            "bank": {},
            "inventory": {},
            "cooldowns": {},
            "daily": {},
            "weekly": {},
            "guilds": {},
            "guild_members": {},
            "stock_prices": {},
            "stock_holdings": {},
            "shop_items": {},
            "achievements": {},
            "config": {
                "daily_amount": 150,
                "weekly_amount": 1000,
                "initial_coins": 100
            },
            "_meta": {
                "version": "5.0_firebase_only",
                "created": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "last_modified": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            return {
                "firebase_ready": self.is_firebase_ready(),
                "save_count": self.save_count,
                "last_save": self.last_save_time.isoformat() if self.last_save_time else None,
                "cache_available": self._data_cache is not None,
                "version": "5.0_firebase_only"
            }
        except Exception as e:
            logging.error(f"Stats error: {e}")
            return {}

# Global instance with lazy initialization
_firebase_manager = None

def get_firebase_manager():
    """Get Firebase manager instance (lazy initialization)"""
    global _firebase_manager
    if _firebase_manager is None:
        _firebase_manager = FirebaseOnlyDataManager()
    return _firebase_manager
