#!/usr/bin/env python3
"""
FIREBASE DATA MANAGER FOR SORABOT
Simple, reliable Firebase Firestore integration
"""

import json
import os
import logging
import datetime
from typing import Dict, List, Optional, Any

# Try to import Firebase (optional dependency)
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    firebase_admin = None
    firestore = None

class FirebaseDataManager:
    """Simple Firebase Firestore integration"""
    
    def __init__(self):
        self.db = None
        self.firebase_available = False
        self._initialized = False
    
    def initialize_firebase(self):
        """Initialize Firebase connection synchronously"""
        if self._initialized:
            return self.firebase_available
            
        if not FIREBASE_AVAILABLE:
            logging.warning("🔥 Firebase SDK not available - install with: pip install firebase-admin")
            self._initialized = True
            return False
        
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Get Firebase credentials from environment
                project_id = os.getenv('FIREBASE_PROJECT_ID')
                private_key = os.getenv('FIREBASE_PRIVATE_KEY')
                client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
                
                if not all([project_id, private_key, client_email]):
                    logging.warning("🔥 Firebase credentials not found - using JSON fallback")
                    self._initialized = True
                    return False
                
                # Create credentials object
                cred_dict = {
                    "type": "service_account",
                    "project_id": project_id,
                    "private_key": private_key.replace('\\n', '\n'),
                    "client_email": client_email,
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                }
                
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                logging.info("🔥 Firebase Admin SDK initialized successfully")
            
            # Get Firestore client
            self.db = firestore.client()
            self.firebase_available = True
            logging.info("🔥 Firebase Firestore connected successfully")
            
            # Test connection
            test_ref = self.db.collection('meta').document('connection_test')
            test_ref.set({
                'test': True,
                'timestamp': datetime.datetime.now(datetime.timezone.utc),
                'status': 'connected'
            })
            logging.info("🔥 Firebase connection test successful")
            
        except Exception as e:
            logging.error(f"🔥 Firebase initialization failed: {e}")
            logging.warning("🔥 Falling back to JSON data storage")
            self.firebase_available = False
        
        self._initialized = True
        return self.firebase_available
    
    def is_available(self) -> bool:
        """Check if Firebase is available"""
        return self.firebase_available and self.db is not None
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """Save data to Firebase"""
        if not self.is_available():
            return False
        
        try:
            # Save main bot data
            bot_ref = self.db.collection('bot_data').document('main')
            bot_ref.set(data)
            
            logging.debug("🔥 Data saved to Firebase")
            return True
            
        except Exception as e:
            logging.error(f"🔥 Firebase save failed: {e}")
            return False
    
    def load_data(self) -> Optional[Dict[str, Any]]:
        """Load data from Firebase"""
        if not self.is_available():
            return None
        
        try:
            bot_ref = self.db.collection('bot_data').document('main')
            doc = bot_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                logging.debug("🔥 Data loaded from Firebase")
                return data
            else:
                logging.warning("🔥 No data found in Firebase")
                return None
                
        except Exception as e:
            logging.error(f"🔥 Firebase load failed: {e}")
            return None
    
    def migrate_from_json(self, json_data: Dict[str, Any]) -> bool:
        """Migrate JSON data to Firebase"""
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

# Create global instance but don't initialize yet
firebase_manager = None

def get_firebase_manager():
    """Get Firebase manager instance (lazy initialization)"""
    global firebase_manager
    if firebase_manager is None:
        firebase_manager = FirebaseDataManager()
        firebase_manager.initialize_firebase()
    return firebase_manager