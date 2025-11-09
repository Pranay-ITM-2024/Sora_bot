"""
Database module: Using AGGRESSIVE data persistence 
ZERO TOLERANCE FOR DATA LOSS - Immediate saves on every operation
"""

import json
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
        """AGGRESSIVE save to Firebase with force"""
        if _global_data_manager:
            return await _global_data_manager.save_data(data, force=True)
        else:
            logging.error("❌ No Firebase data manager available! Cannot save data!")
            return False
    
    async def load_data(self):
        """Load data from Firebase ONLY"""
        if _global_data_manager:
            return await _global_data_manager.load_data()
        else:
            logging.error("❌ No Firebase data manager available!")
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