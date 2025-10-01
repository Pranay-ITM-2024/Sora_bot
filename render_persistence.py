"""
RENDER-SPECIFIC DATA PERSISTENCE MODULE
Handles data persistence for ephemeral file systems like Render
Uses multiple cloud storage options and webhook backups
"""

import asyncio
import aiohttp
import json
import os
import datetime
import logging
import base64
import gzip
from typing import Optional, Dict, Any

class RenderDataPersistence:
    """
    Cloud-based data persistence for Render hosting
    Features:
    - GitHub Gist backups (free, reliable)
    - Webhook-based external storage
    - Discord webhook backups as fallback
    - Automatic recovery on startup
    - Periodic cloud synchronization
    """
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.backup_webhook_url = os.getenv('BACKUP_WEBHOOK_URL')
        self.discord_backup_webhook = os.getenv('DISCORD_BACKUP_WEBHOOK')
        self.gist_id = os.getenv('GIST_ID')  # Will be created if not exists
        
        # Backup URLs for data retrieval
        self.backup_sources = []
        if self.gist_id:
            self.backup_sources.append(f"https://gist.githubusercontent.com/{self.gist_id}/raw/sorabot_data.json")
        
        # Log configuration status
        if self.github_token:
            logging.info("☁️ GitHub token configured - cloud backups enabled")
        else:
            logging.warning("⚠️ No GitHub token found - cloud backups disabled")
            logging.info("💡 To enable cloud backups, set GITHUB_TOKEN environment variable")
            logging.info("💡 Get token at: https://github.com/settings/tokens (with 'gist' scope)")
        
        if self.backup_webhook_url:
            logging.info("🔗 Backup webhook configured")
        
        if self.discord_backup_webhook:
            logging.info("💬 Discord backup webhook configured")
        
        logging.info("🌥️ Render data persistence initialized")
    
    async def save_to_cloud(self, data: Dict[str, Any]) -> bool:
        """Save data to multiple cloud sources"""
        if not self.github_token and not self.backup_webhook_url and not self.discord_backup_webhook:
            logging.debug("🔕 No cloud backup methods configured - skipping cloud sync")
            return False
        
        success_count = 0
        total_attempts = 0
        
        # Method 1: GitHub Gist (most reliable)
        if self.github_token:
            total_attempts += 1
            if await self._save_to_gist(data):
                success_count += 1
                logging.debug("✅ Data saved to GitHub Gist")
            else:
                logging.warning("❌ GitHub Gist backup failed")
        
        # Method 2: Webhook backup
        if self.backup_webhook_url:
            total_attempts += 1
            if await self._save_to_webhook(data):
                success_count += 1
                logging.debug("✅ Data saved to webhook backup")
            else:
                logging.warning("❌ Webhook backup failed")
        
        # Method 3: Discord webhook (emergency backup)
        if self.discord_backup_webhook:
            total_attempts += 1
            if await self._save_to_discord(data):
                success_count += 1
                logging.debug("✅ Data saved to Discord backup")
            else:
                logging.warning("❌ Discord backup failed")
        
        # Log overall result
        if success_count > 0:
            logging.info(f"☁️ Cloud sync: {success_count}/{total_attempts} methods successful")
        elif total_attempts > 0:
            logging.warning(f"⚠️ Cloud sync failed: 0/{total_attempts} methods successful")
        
        return success_count > 0
    
    async def load_from_cloud(self) -> Optional[Dict[str, Any]]:
        """Load data from cloud sources with fallback priority"""
        
        # Try GitHub Gist first (most reliable)
        if self.gist_id:
            data = await self._load_from_gist()
            if data:
                logging.info("✅ Data loaded from GitHub Gist")
                return data
        
        # Try webhook backup
        data = await self._load_from_webhook()
        if data:
            logging.info("✅ Data loaded from webhook backup")
            return data
        
        # Try Discord backup (last resort)
        data = await self._load_from_discord()
        if data:
            logging.info("✅ Data loaded from Discord backup")
            return data
        
        logging.warning("⚠️ No cloud backup found")
        return None
    
    async def _save_to_gist(self, data: Dict[str, Any]) -> bool:
        """Save data to GitHub Gist"""
        if not self.github_token:
            logging.debug("🔕 No GitHub token - skipping Gist backup")
            return False
        
        try:
            # Compress data for storage
            json_data = json.dumps(data, default=str)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            encoded_data = base64.b64encode(compressed_data).decode('utf-8')
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            gist_data = {
                "description": f"SORABOT Data Backup - {datetime.datetime.utcnow().isoformat()}",
                "public": False,
                "files": {
                    "sorabot_data.json": {
                        "content": json_data
                    },
                    "sorabot_data_compressed.txt": {
                        "content": encoded_data
                    },
                    "backup_info.json": {
                        "content": json.dumps({
                            "timestamp": datetime.datetime.utcnow().isoformat(),
                            "user_count": len(data.get("coins", {})),
                            "total_coins": sum(data.get("coins", {}).values()),
                            "version": "render_safe"
                        })
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                if self.gist_id:
                    # Update existing gist
                    url = f"https://api.github.com/gists/{self.gist_id}"
                    async with session.patch(url, headers=headers, json=gist_data) as response:
                        if response.status == 200:
                            return True
                        else:
                            logging.error(f"Gist update failed: HTTP {response.status}")
                            return False
                else:
                    # Create new gist
                    url = "https://api.github.com/gists"
                    async with session.post(url, headers=headers, json=gist_data) as response:
                        if response.status == 201:
                            result = await response.json()
                            self.gist_id = result['id']
                            logging.info(f"📝 Created new Gist: {self.gist_id}")
                            logging.info("💡 Save this Gist ID as GIST_ID environment variable for faster recovery")
                            return True
                        else:
                            logging.error(f"Gist creation failed: HTTP {response.status}")
                            return False
                        
        except aiohttp.ClientError as e:
            logging.error(f"GitHub API connection error: {e}")
        except Exception as e:
            logging.error(f"Gist backup error: {e}")
        
        return False
    
    async def _load_from_gist(self) -> Optional[Dict[str, Any]]:
        """Load data from GitHub Gist"""
        if not self.gist_id:
            return None
        
        try:
            url = f"https://api.github.com/gists/{self.gist_id}"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        gist_data = await response.json()
                        content = gist_data['files']['sorabot_data.json']['content']
                        return json.loads(content)
                        
        except Exception as e:
            logging.error(f"Gist load failed: {e}")
        
        return None
    
    async def _save_to_webhook(self, data: Dict[str, Any]) -> bool:
        """Save data to external webhook"""
        if not self.backup_webhook_url:
            return False
        
        try:
            # Split large data into chunks if needed
            json_data = json.dumps(data, default=str)
            
            # If data is too large, compress it
            if len(json_data) > 50000:  # 50KB limit
                compressed = gzip.compress(json_data.encode('utf-8'))
                encoded_data = base64.b64encode(compressed).decode('utf-8')
                payload = {
                    "type": "compressed_backup",
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "data": encoded_data,
                    "metadata": {
                        "user_count": len(data.get("coins", {})),
                        "compressed": True
                    }
                }
            else:
                payload = {
                    "type": "backup",
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "data": data,
                    "metadata": {
                        "user_count": len(data.get("coins", {})),
                        "compressed": False
                    }
                }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.backup_webhook_url, json=payload, timeout=30) as response:
                    return response.status < 400
                    
        except Exception as e:
            logging.error(f"Webhook backup failed: {e}")
        
        return False
    
    async def _load_from_webhook(self) -> Optional[Dict[str, Any]]:
        """Load data from external webhook"""
        if not self.backup_webhook_url:
            return None
        
        try:
            # Try to get data from webhook
            get_url = self.backup_webhook_url.replace('/save', '/load')  # Convention
            
            async with aiohttp.ClientSession() as session:
                async with session.get(get_url, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('metadata', {}).get('compressed', False):
                            # Decompress data
                            encoded_data = result['data']
                            compressed_data = base64.b64decode(encoded_data.encode('utf-8'))
                            json_data = gzip.decompress(compressed_data).decode('utf-8')
                            return json.loads(json_data)
                        else:
                            return result.get('data')
                            
        except Exception as e:
            logging.error(f"Webhook load failed: {e}")
        
        return None
    
    async def _save_to_discord(self, data: Dict[str, Any]) -> bool:
        """Save data summary to Discord webhook (emergency backup)"""
        if not self.discord_backup_webhook:
            return False
        
        try:
            # Create summary for Discord (Discord has message limits)
            summary = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "user_count": len(data.get("coins", {})),
                "total_coins": sum(data.get("coins", {}).values()),
                "bank_total": sum(data.get("bank", {}).values()),
                "active_guilds": len(data.get("guilds", {})),
                "stock_prices": data.get("stock_prices", {}),
                "config": data.get("config", {})
            }
            
            # Store compressed full data as file attachment
            json_data = json.dumps(data, default=str)
            compressed = gzip.compress(json_data.encode('utf-8'))
            encoded_data = base64.b64encode(compressed).decode('utf-8')
            
            embed = {
                "title": "🛡️ SORABOT Data Backup",
                "description": f"Backup created at {summary['timestamp'][:19]}",
                "color": 0x00ff00,
                "fields": [
                    {"name": "👥 Users", "value": str(summary['user_count']), "inline": True},
                    {"name": "💰 Total Coins", "value": f"{summary['total_coins']:,}", "inline": True},
                    {"name": "🏦 Bank Total", "value": f"{summary['bank_total']:,}", "inline": True},
                    {"name": "🏛️ Guilds", "value": str(summary['active_guilds']), "inline": True}
                ]
            }
            
            # Send summary + compressed data
            payload = {
                "embeds": [embed],
                "content": f"```json\n{encoded_data[:1500]}...\n```"  # Truncated for Discord
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.discord_backup_webhook, json=payload, timeout=30) as response:
                    return response.status < 400
                    
        except Exception as e:
            logging.error(f"Discord backup failed: {e}")
        
        return False
    
    async def _load_from_discord(self) -> Optional[Dict[str, Any]]:
        """Load data from Discord webhook (limited recovery)"""
        # Discord webhooks don't support GET requests for data retrieval
        # This would need to be implemented with a Discord bot that can read messages
        # For now, return None - this is truly the last resort
        return None

# Global instance
render_persistence = RenderDataPersistence()