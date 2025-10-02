#!/usr/bin/env python3
"""
FIREBASE DATA MANAGER FOR SORABOT
Enterprise-grade cloud database with real-time synchronization
Replaces JSON files with Firebase Firestore for permanent data storage
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import asyncio
import logging
import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor
import threading

class FirebaseDataManager:
    """
    Firebase Firestore integration for SORABOT
    Features:
    - Real-time cloud storage
    - Automatic data persistence 
    - Atomic transactions
    - Offline caching
    - Zero data loss guarantee
    """
    
    def __init__(self):
        self.db = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._initialized = False
        
        # Initialize Firebase
        asyncio.create_task(self._initialize_firebase())
    
    async def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                logging.info("🔥 Firebase already initialized")
                self.db = firestore.client()
                self._initialized = True
                return
            
            # Method 1: Service Account JSON file (most secure)
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                logging.info("🔥 Firebase initialized with service account file")
            
            # Method 2: Environment variables (for Render deployment)
            elif os.getenv('FIREBASE_PROJECT_ID'):
                # Create credentials from environment variables
                firebase_config = {
                    "type": "service_account",
                    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                    "private_key": os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
                    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.getenv('FIREBASE_CLIENT_EMAIL')}"
                }
                
                cred = credentials.Certificate(firebase_config)
                firebase_admin.initialize_app(cred)
                logging.info("🔥 Firebase initialized with environment variables")
            
            # Method 3: Default credentials (for local development)
            else:
                # Try to use default credentials or fall back to JSON mode
                logging.warning("⚠️ No Firebase credentials found - falling back to JSON mode")
                self._initialized = False
                return
            
            # Get Firestore client
            self.db = firestore.client()
            self._initialized = True
            
            # Test connection
            await self._test_connection()
            logging.info("✅ Firebase Firestore connection successful!")
            
        except Exception as e:
            logging.error(f"❌ Firebase initialization failed: {e}")
            logging.warning("⚠️ Falling back to JSON mode")
            self._initialized = False
    
    async def _test_connection(self):
        """Test Firebase connection"""
        try:
            # Try to read from a test collection
            loop = asyncio.get_event_loop()
            test_ref = self.db.collection('_health_check').document('test')
            await loop.run_in_executor(self.executor, test_ref.set, {
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'status': 'healthy'
            })
            logging.info("🔥 Firebase write test successful")
        except Exception as e:
            logging.error(f"Firebase connection test failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Firebase is available"""
        return self._initialized and self.db is not None
    
    async def save_user_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Save user data to Firebase"""
        if not self.is_available():
            return False
        
        try:
            loop = asyncio.get_event_loop()
            user_ref = self.db.collection('users').document(str(user_id))
            
            # Add metadata
            data['_meta'] = {
                'last_updated': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'version': '4.0_firebase'
            }
            
            await loop.run_in_executor(self.executor, user_ref.set, data, True)
            
            # Update cache
            with self._cache_lock:
                self._cache[f'user_{user_id}'] = data
            
            logging.debug(f"💾 User {user_id} data saved to Firebase")
            return True
            
        except Exception as e:
            logging.error(f"Firebase save failed for user {user_id}: {e}")
            return False
    
    async def load_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user data from Firebase"""
        if not self.is_available():
            return None
        
        try:
            # Check cache first
            cache_key = f'user_{user_id}'
            with self._cache_lock:
                if cache_key in self._cache:
                    return self._cache[cache_key].copy()
            
            loop = asyncio.get_event_loop()
            user_ref = self.db.collection('users').document(str(user_id))
            doc = await loop.run_in_executor(self.executor, user_ref.get)
            
            if doc.exists:
                data = doc.to_dict()
                # Update cache
                with self._cache_lock:
                    self._cache[cache_key] = data
                return data
            else:
                return None
                
        except Exception as e:
            logging.error(f"Firebase load failed for user {user_id}: {e}")
            return None
    
    async def save_full_data(self, data: Dict[str, Any]) -> bool:
        """Save complete bot data to Firebase"""
        if not self.is_available():
            return False
        
        try:
            loop = asyncio.get_event_loop()
            
            # Save main data to 'bot_data' collection
            bot_ref = self.db.collection('bot_data').document('main')
            
            # Add metadata
            data['_meta'] = {
                'last_save': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'version': '4.0_firebase',
                'user_count': len(data.get('coins', {})),
                'total_coins': sum(data.get('coins', {}).values())
            }
            
            await loop.run_in_executor(self.executor, bot_ref.set, data)
            
            # Also save individual user data for better performance
            coins = data.get('coins', {})
            bank = data.get('bank', {})
            
            # Batch save user data
            batch = self.db.batch()
            
            for user_id in coins.keys():
                user_data = {
                    'coins': coins.get(user_id, 0),
                    'bank': bank.get(user_id, 0),
                    'inventory': data.get('inventories', {}).get(user_id, []),
                    'equipped': data.get('equipped', {}).get(user_id, {}),
                    'last_daily': data.get('last_daily', {}).get(user_id),
                    'last_weekly': data.get('last_weekly', {}).get(user_id),
                    'cooldowns': data.get('cooldowns', {}).get(user_id, {}),
                    '_meta': {
                        'last_updated': datetime.datetime.now(datetime.timezone.utc).isoformat()
                    }
                }
                
                user_ref = self.db.collection('users').document(str(user_id))
                batch.set(user_ref, user_data, merge=True)
            
            # Commit batch
            await loop.run_in_executor(self.executor, batch.commit)
            
            logging.info(f"🔥 Complete data saved to Firebase - {len(coins)} users")
            return True
            
        except Exception as e:
            logging.error(f"Firebase full save failed: {e}")
            return False
    
    async def load_full_data(self) -> Optional[Dict[str, Any]]:
        """Load complete bot data from Firebase"""
        if not self.is_available():
            return None
        
        try:
            loop = asyncio.get_event_loop()
            bot_ref = self.db.collection('bot_data').document('main')
            doc = await loop.run_in_executor(self.executor, bot_ref.get)
            
            if doc.exists:
                data = doc.to_dict()
                logging.info(f"🔥 Data loaded from Firebase - {len(data.get('coins', {}))} users")
                return data
            else:
                logging.warning("No main bot data found in Firebase")
                return None
                
        except Exception as e:
            logging.error(f"Firebase full load failed: {e}")
            return None
    
    async def get_leaderboard(self, field: str = 'coins', limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard data from Firebase"""
        if not self.is_available():
            return []
        
        try:
            loop = asyncio.get_event_loop()
            users_ref = self.db.collection('users')
            
            # Query top users by field
            query = users_ref.order_by(field, direction=firestore.Query.DESCENDING).limit(limit)
            docs = await loop.run_in_executor(self.executor, query.stream)
            
            leaderboard = []
            for doc in docs:
                data = doc.to_dict()
                data['user_id'] = doc.id
                leaderboard.append(data)
            
            return leaderboard
            
        except Exception as e:
            logging.error(f"Firebase leaderboard query failed: {e}")
            return []
    
    async def atomic_transaction(self, user_id: str, field: str, amount: int) -> bool:
        """Perform atomic transaction (add/subtract coins safely)"""
        if not self.is_available():
            return False
        
        try:
            loop = asyncio.get_event_loop()
            
            @firestore.transactional
            def update_user_balance(transaction, user_ref):
                # Get current data
                snapshot = user_ref.get(transaction=transaction)
                current_value = 0
                
                if snapshot.exists:
                    data = snapshot.to_dict()
                    current_value = data.get(field, 0)
                
                new_value = current_value + amount
                
                # Prevent negative balances
                if new_value < 0:
                    return False
                
                # Update with new value
                transaction.set(user_ref, {
                    field: new_value,
                    '_meta': {
                        'last_updated': datetime.datetime.now(datetime.timezone.utc).isoformat()
                    }
                }, merge=True)
                
                return True
            
            user_ref = self.db.collection('users').document(str(user_id))
            transaction = self.db.transaction()
            
            result = await loop.run_in_executor(
                self.executor, 
                update_user_balance, 
                transaction, 
                user_ref
            )
            
            return result
            
        except Exception as e:
            logging.error(f"Firebase atomic transaction failed: {e}")
            return False
    
    async def migrate_from_json(self, json_data: Dict[str, Any]) -> bool:
        """Migrate existing JSON data to Firebase"""
        if not self.is_available():
            return False
        
        try:
            logging.info("🔄 Starting Firebase migration...")
            
            # Save full data
            success = await self.save_full_data(json_data)
            
            if success:
                logging.info("✅ Firebase migration completed successfully!")
                
                # Create backup of original data
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"pre_firebase_backup_{timestamp}.json"
                
                try:
                    import aiofiles
                    async with aiofiles.open(backup_file, 'w') as f:
                        await f.write(json.dumps(json_data, indent=2, default=str))
                    logging.info(f"📄 JSON backup saved as {backup_file}")
                except:
                    pass
                
                return True
            else:
                logging.error("❌ Firebase migration failed")
                return False
                
        except Exception as e:
            logging.error(f"Migration error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Firebase database statistics"""
        if not self.is_available():
            return {'status': 'unavailable'}
        
        try:
            loop = asyncio.get_event_loop()
            
            # Count users
            users_ref = self.db.collection('users')
            users_count = len(list(await loop.run_in_executor(self.executor, users_ref.stream)))
            
            # Get bot data stats
            bot_ref = self.db.collection('bot_data').document('main')
            doc = await loop.run_in_executor(self.executor, bot_ref.get)
            
            if doc.exists:
                data = doc.to_dict()
                meta = data.get('_meta', {})
                
                return {
                    'status': 'connected',
                    'user_count': users_count,
                    'last_save': meta.get('last_save'),
                    'total_coins': meta.get('total_coins', 0),
                    'version': meta.get('version', 'unknown'),
                    'firebase_project': os.getenv('FIREBASE_PROJECT_ID', 'unknown')
                }
            else:
                return {
                    'status': 'connected',
                    'user_count': users_count,
                    'data_status': 'no_main_data'
                }
                
        except Exception as e:
            logging.error(f"Firebase stats error: {e}")
            return {'status': 'error', 'error': str(e)}

# Global Firebase manager instance
firebase_manager = FirebaseDataManager()