===========================================
🔥 FIREBASE SETUP GUIDE
===========================================

This folder contains guides for setting up Firebase 
with your Sora Bot instance.

===========================================
📄 FILES IN THIS FOLDER
===========================================

1. FIREBASE_SETUP.md
   → Initial Firebase project setup
   → Creating service account credentials
   → Connecting bot to Firebase

2. FIREBASE_REALTIME_SETUP.md
   → Firebase Realtime Database configuration
   → Security rules setup
   → Data structure explanation

===========================================
🚀 QUICK SETUP STEPS
===========================================

STEP 1: Create Firebase Project
- Go to https://console.firebase.google.com
- Click "Add Project"
- Name it (e.g., "sora-bot-data")
- Disable Google Analytics (optional)

STEP 2: Enable Realtime Database
- In Firebase Console, go to "Realtime Database"
- Click "Create Database"
- Choose location (us-central1 recommended)
- Start in LOCKED MODE (we'll add rules later)

STEP 3: Generate Service Account Key
- Go to Project Settings → Service Accounts
- Click "Generate New Private Key"
- Download JSON file
- Rename to: firebase_credentials.json
- Place in bot root directory
- Add to .gitignore (NEVER commit this file!)

STEP 4: Set Environment Variable
In your .env file:
FIREBASE_CREDENTIALS_PATH=firebase_credentials.json

STEP 5: Configure Security Rules
Go to Realtime Database → Rules tab
Use the rules from FIREBASE_REALTIME_SETUP.md

STEP 6: Test Connection
Run the bot and use /daily command
Check Firebase Console to see if data appears

===========================================
📊 DATA STRUCTURE
===========================================

Firebase stores all bot data in JSON format:

{
  "servers": {
    "SERVER_ID_1": {
      "coins": { "USER_ID": 1000 },
      "bank": { "USER_ID": 5000 },
      "inventories": { "USER_ID": {...} },
      "guilds": {...},
      "loans": {...},
      "casino_stats": {...},
      "_settings": {
        "daily_reward": 100,
        "weekly_reward": 500
      }
    },
    "SERVER_ID_2": {...}
  }
}

===========================================
🔒 SECURITY BEST PRACTICES
===========================================

1. ✅ NEVER commit firebase_credentials.json
2. ✅ Use proper Firebase security rules
3. ✅ Limit database access to service account only
4. ✅ Use environment variables for credentials path
5. ✅ Enable audit logging in Firebase Console
6. ✅ Regularly backup your database

===========================================
🛠️ TROUBLESHOOTING
===========================================

ISSUE: "Failed to load data from Firebase"
FIX: Check credentials path in .env file

ISSUE: "Permission denied"
FIX: Update Firebase security rules (see FIREBASE_REALTIME_SETUP.md)

ISSUE: "Database not found"
FIX: Ensure Realtime Database is enabled in console

ISSUE: "Data not saving"
FIX: Check Firebase Console logs for errors

===========================================
📚 ADDITIONAL RESOURCES
===========================================

Firebase Documentation:
https://firebase.google.com/docs/database

Python Admin SDK:
https://firebase.google.com/docs/admin/setup

Security Rules Guide:
https://firebase.google.com/docs/database/security

===========================================

For detailed setup instructions, read:
- FIREBASE_SETUP.md (initial setup)
- FIREBASE_REALTIME_SETUP.md (database config)
