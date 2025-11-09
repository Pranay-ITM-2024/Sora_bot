#!/usr/bin/env python3
"""
FIREBASE REALTIME DATABASE MANAGER FOR SORABOT
Simple, reliable Firebase Realtime Database integration
"""

import json
import os
import logging
import datetime
from typing import Dict, List, Optional, Any

# Try to import Firebase (optional dependency)
try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    firebase_admin = None
    db = None

class FirebaseDataManager:
    """Simple Firebase Realtime Database integration"""
    
    def __init__(self):
        self.db_ref = None
        self.firebase_available = False
        self._initialized = False
    
    def initialize_firebase(self):
        """Initialize Firebase Realtime Database connection"""
        if self._initialized:
            return self.firebase_available
            
        if not FIREBASE_AVAILABLE:
            logging.warning("🔥 Firebase SDK not available - install with: pip install firebase-admin")
            self._initialized = True
            return False
        
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Firebase configuration
                firebase_config = {
                    "apiKey": "AIzaSyBgVbPpOenpLAW--9L0nv6PU-3u1z1uTu8",
                    "authDomain": "sorabotthenew.firebaseapp.com",
                    "projectId": "sorabotthenew",
                    "storageBucket": "sorabotthenew.firebasestorage.app",
                    "messagingSenderId": "860618153543",
                    "appId": "1:860618153543:web:8a2f4f44b27323a7511b62",
                    "measurementId": "G-NJJRYBSWBX",
                    "databaseURL": "https://sorabotthenew-default-rtdb.firebaseio.com"
                }
                
                # Initialize with minimal credentials for Realtime Database
                cred = credentials.Certificate({
                    "type": "service_account",
                    "project_id": "sorabotthenew",
                    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID', 'dummy'),
                    "private_key": os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n') if os.getenv('FIREBASE_PRIVATE_KEY') else None,
                    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL', 'firebase-adminsdk@sorabotthenew.iam.gserviceaccount.com'),
                    "client_id": os.getenv('FIREBASE_CLIENT_ID', ''),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                })
                
                firebase_admin.initialize_app(cred, {
                    'databaseURL': firebase_config['databaseURL']
                })
                logging.info("🔥 Firebase Realtime Database initialized successfully")
            
            # Get database reference
            self.db_ref = db.reference('/')
            self.firebase_available = True
            logging.info("🔥 Firebase Realtime Database connected successfully")
            
            # Test connection
            test_data = {
                'test': True,
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'status': 'connected'
            }
            db.reference('/meta/connection_test').set(test_data)
            logging.info("🔥 Firebase connection test successful")
            
        except Exception as e:
            logging.error(f"🔥 Firebase initialization failed: {e}")
            logging.warning("🔥 Falling back to JSON data storage")
            self.firebase_available = False
        
        self._initialized = True
        return self.firebase_available
    
    def is_available(self) -> bool:
        """Check if Firebase is available"""
        return self.firebase_available and self.db_ref is not None
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """Save data to Firebase Realtime Database"""
        if not self.is_available():
            return False
        
        try:
            # Convert datetime objects to strings for JSON serialization
            serializable_data = json.loads(json.dumps(data, default=str))
            
            # Save to /bot_data path in Realtime Database
            db.reference('/bot_data').set(serializable_data)
            
            logging.debug("🔥 Data saved to Firebase Realtime Database")
            return True
            
        except Exception as e:
            logging.error(f"🔥 Firebase save failed: {e}")
            return False
    
    def load_data(self) -> Optional[Dict[str, Any]]:
        """Load data from Firebase Realtime Database"""
        if not self.is_available():
            return None
        
        try:
            # Load from /bot_data path
            data = db.reference('/bot_data').get()
            
            if data:
                logging.debug("🔥 Data loaded from Firebase Realtime Database")
                return data
            else:
                logging.warning("🔥 No data found in Firebase")
                return None
                
        except Exception as e:
            logging.error(f"🔥 Firebase load failed: {e}")
            return None
    
    def migrate_from_json(self, json_data: Dict[str, Any]) -> bool:
        """Migrate JSON data to Firebase Realtime Database"""
        if not self.is_available():
            return False
        
        try:
            logging.info("🔄 Starting Firebase migration...")
            
            # Add migration metadata
            json_data['_meta'] = json_data.get('_meta', {})
            json_data['_meta']['migrated_to_firebase'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            json_data['_meta']['migration_source'] = 'json_backup'
            
            # Save to Firebase
            success = self.save_data(json_data)
            
            if success:
                user_count = len(json_data.get('coins', {}))
                stock_count = len(json_data.get('stock_prices', {}))
                logging.info(f"✅ Firebase migration completed! Migrated {user_count} users, {stock_count} stocks")
                return True
            else:
                logging.error("❌ Firebase migration failed")
                return False
                
        except Exception as e:
            logging.error(f"🔥 Migration error: {e}")
            return False

# Global instance with lazy initialization
_firebase_manager = None

def get_firebase_manager():
    """Get Firebase manager instance (lazy initialization)"""
    global _firebase_manager
    if _firebase_manager is None:
        _firebase_manager = FirebaseDataManager()
        _firebase_manager.initialize_firebase()
    return _firebase_manager