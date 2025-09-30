"""
Robust Multi-Layer Backup System
Replacing complex SQLite with reliable JSON-based backups
"""

import json
import asyncio
import aiofiles
import aiohttp
import os
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configuration
DATA_PATH = Path(__file__).parent.parent / "data.json"
BACKUP_DIR = Path(__file__).parent.parent / "backups"
MAX_BACKUPS = 20  # Keep last 20 backups
COMPRESSION_ENABLED = True

class BackupManager:
    """Advanced backup system with multiple layers of protection"""
    
    def __init__(self):
        self._lock = asyncio.Lock()
        self.backup_webhook = os.getenv("BACKUP_WEBHOOK")
        self.save_count = 0
        
        # Ensure backup directory exists
        BACKUP_DIR.mkdir(exist_ok=True)
        
    async def save_data(self, data: dict):
        """Save data with comprehensive backup strategy"""
        async with self._lock:
            try:
                self.save_count += 1
                success_layers = []
                
                # Layer 1: Main JSON file (atomic write)
                try:
                    await self._atomic_json_save(data, DATA_PATH)
                    success_layers.append("main_json")
                except Exception as e:
                    logging.error(f"Main JSON save failed: {e}")
                
                # Layer 2: Timestamped backup
                try:
                    await self._create_timestamped_backup(data)
                    success_layers.append("timestamped")
                except Exception as e:
                    logging.error(f"Timestamped backup failed: {e}")
                
                # Layer 3: Compressed backup (every 5 saves)
                if self.save_count % 5 == 0:
                    try:
                        await self._create_compressed_backup(data)
                        success_layers.append("compressed")
                    except Exception as e:
                        logging.error(f"Compressed backup failed: {e}")
                
                # Layer 4: Emergency backup if main failed
                if "main_json" not in success_layers:
                    try:
                        emergency_path = DATA_PATH.with_suffix('.emergency.json')
                        await self._atomic_json_save(data, emergency_path)
                        success_layers.append("emergency")
                    except Exception as e:
                        logging.error(f"Emergency backup failed: {e}")
                
                # Layer 5: Remote notification (every 10 saves)
                if self.save_count % 10 == 0 and self.backup_webhook:
                    try:
                        await self._send_backup_notification(data, success_layers)
                        success_layers.append("remote_notification")
                    except Exception as e:
                        logging.error(f"Remote notification failed: {e}")
                
                # Cleanup old backups
                await self._cleanup_old_backups()
                
                # Log results
                if success_layers:
                    logging.info(f"Backup successful - Layers: {', '.join(success_layers)} (Save #{self.save_count})")
                else:
                    logging.error(f"ALL BACKUP LAYERS FAILED! Save #{self.save_count}")
                    
                return len(success_layers) > 0
                
            except Exception as e:
                logging.error(f"Critical backup system error: {e}")
                return False
    
    async def load_data(self) -> dict:
        """Load data with intelligent fallback system"""
        try:
            # Try main data file first
            if DATA_PATH.exists():
                try:
                    async with aiofiles.open(DATA_PATH, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        if self._validate_data(data):
                            logging.info("Data loaded from main file")
                            return data
                except Exception as e:
                    logging.warning(f"Main file corrupted: {e}")
            
            # Try emergency backup
            emergency_path = DATA_PATH.with_suffix('.emergency.json')
            if emergency_path.exists():
                try:
                    async with aiofiles.open(emergency_path, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        if self._validate_data(data):
                            logging.info("Data loaded from emergency backup")
                            # Restore main file
                            await self._atomic_json_save(data, DATA_PATH)
                            return data
                except Exception as e:
                    logging.warning(f"Emergency backup corrupted: {e}")
            
            # Try latest timestamped backup
            latest_backup = await self._find_latest_backup()
            if latest_backup:
                try:
                    async with aiofiles.open(latest_backup, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        if self._validate_data(data):
                            logging.info(f"Data loaded from backup: {latest_backup.name}")
                            # Restore main file
                            await self._atomic_json_save(data, DATA_PATH)
                            return data
                except Exception as e:
                    logging.warning(f"Backup file corrupted: {e}")
            
            # Try compressed backups
            compressed_backup = await self._find_latest_compressed_backup()
            if compressed_backup:
                try:
                    data = await self._load_compressed_backup(compressed_backup)
                    if self._validate_data(data):
                        logging.info(f"Data loaded from compressed backup: {compressed_backup.name}")
                        # Restore main file
                        await self._atomic_json_save(data, DATA_PATH)
                        return data
                except Exception as e:
                    logging.warning(f"Compressed backup corrupted: {e}")
            
            # Last resort: create fresh data
            logging.warning("All backups failed, creating fresh data structure")
            return self._get_default_data()
            
        except Exception as e:
            logging.error(f"Critical data loading error: {e}")
            return self._get_default_data()
    
    async def _atomic_json_save(self, data: dict, file_path: Path):
        """Atomic JSON save to prevent corruption"""
        temp_path = file_path.with_suffix('.tmp')
        try:
            # Write to temporary file first
            async with aiofiles.open(temp_path, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
            
            # Atomic move (rename) to final location
            temp_path.replace(file_path)
            
        except Exception as e:
            # Cleanup temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise e
    
    async def _create_timestamped_backup(self, data: dict):
        """Create timestamped backup file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"backup_{timestamp}.json"
        
        await self._atomic_json_save(data, backup_path)
        logging.info(f"Timestamped backup created: {backup_path.name}")
    
    async def _create_compressed_backup(self, data: dict):
        """Create compressed backup for space efficiency"""
        if not COMPRESSION_ENABLED:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"backup_compressed_{timestamp}.json.gz"
        
        # Create compressed backup
        json_data = json.dumps(data, indent=2, default=str)
        
        async with aiofiles.open(backup_path, 'wb') as f:
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            await f.write(compressed_data)
        
        logging.info(f"Compressed backup created: {backup_path.name}")
    
    async def _find_latest_backup(self) -> Path:
        """Find the most recent timestamped backup"""
        backup_files = list(BACKUP_DIR.glob("backup_*.json"))
        if not backup_files:
            return None
        
        # Sort by modification time, newest first
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return backup_files[0]
    
    async def _find_latest_compressed_backup(self) -> Path:
        """Find the most recent compressed backup"""
        backup_files = list(BACKUP_DIR.glob("backup_compressed_*.json.gz"))
        if not backup_files:
            return None
        
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return backup_files[0]
    
    async def _load_compressed_backup(self, backup_path: Path) -> dict:
        """Load data from compressed backup"""
        async with aiofiles.open(backup_path, 'rb') as f:
            compressed_data = await f.read()
            json_data = gzip.decompress(compressed_data).decode('utf-8')
            return json.loads(json_data)
    
    async def _cleanup_old_backups(self):
        """Clean up old backup files to save disk space"""
        try:
            # Get all backup files
            backup_files = list(BACKUP_DIR.glob("backup_*.json"))
            compressed_files = list(BACKUP_DIR.glob("backup_compressed_*.json.gz"))
            
            # Sort by modification time, newest first
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            compressed_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the most recent backups
            for old_file in backup_files[MAX_BACKUPS:]:
                old_file.unlink()
            
            for old_file in compressed_files[MAX_BACKUPS//2:]:  # Keep fewer compressed backups
                old_file.unlink()
                
        except Exception as e:
            logging.error(f"Backup cleanup failed: {e}")
    
    async def _send_backup_notification(self, data: dict, success_layers: list):
        """Send backup status to Discord webhook"""
        if not self.backup_webhook:
            return
        
        try:
            data_size = len(json.dumps(data))
            embed = {
                "title": "🔄 Backup Status Report",
                "color": 0x00ff00,
                "fields": [
                    {"name": "📊 Data Size", "value": f"{data_size:,} characters", "inline": True},
                    {"name": "✅ Successful Layers", "value": ", ".join(success_layers), "inline": True},
                    {"name": "📅 Timestamp", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True},
                    {"name": "💾 Save Count", "value": f"#{self.save_count}", "inline": True}
                ],
                "footer": {"text": "SORA Bot Backup System"}
            }
            
            payload = {"embeds": [embed]}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.backup_webhook, json=payload) as response:
                    if response.status == 204:
                        logging.info("Backup notification sent successfully")
                    else:
                        logging.warning(f"Backup notification failed: {response.status}")
                        
        except Exception as e:
            logging.error(f"Failed to send backup notification: {e}")
    
    def _validate_data(self, data: dict) -> bool:
        """Validate data structure integrity"""
        if not isinstance(data, dict):
            return False
        
        # Check for essential keys
        required_keys = ['coins', 'bank', 'inventories', 'guilds']
        for key in required_keys:
            if key not in data:
                logging.warning(f"Missing required key: {key}")
                return False
        
        # Basic type checking
        if not isinstance(data.get('coins', {}), dict):
            return False
        if not isinstance(data.get('bank', {}), dict):
            return False
        
        return True
    
    def _get_default_data(self) -> dict:
        """Create default data structure"""
        return {
            'coins': {},
            'bank': {},
            'last_daily': {},
            'last_weekly': {},
            'transactions': [],
            'active_games': {},
            'companies': {},
            'items': {},
            'inventories': {},
            'equipped': {},
            'equipment': {},
            'guilds': {},
            'guild_members': {},
            'guild_invites': {},
            'stock_holdings': {},
            'stock_portfolios': {},
            'stock_market': {},
            'stock_prices': {
                'TECH': 150, 'BANK': 80, 'MINE': 45, 'FOOD': 60,
                'ENERGY': 90, 'HEALTH': 120, 'AUTO': 70, 'RETAIL': 35
            },
            'consumable_effects': {},
            'loot_tables': {},
            'shop_items': {},
            'config': {},
            'bans': {},
            'cooldowns': {},
            'leaderboard_channel': None,
            'leaderboard_message': None,
            '_meta': {
                'created': datetime.now().isoformat(),
                'version': '3.0',
                'backup_system': 'advanced_json'
            }
        }

# Global backup manager instance
backup_manager = BackupManager()

# Helper functions for backward compatibility
async def load_data():
    """Load data using the backup manager"""
    return await backup_manager.load_data()

async def save_data(data):
    """Save data using the backup manager"""
    return await backup_manager.save_data(data)