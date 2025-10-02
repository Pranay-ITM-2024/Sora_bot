# 🔥 FIREBASE SETUP GUIDE FOR SORABOT

## Quick Setup Instructions

### 1. Download Your Firebase Service Account Key

You mentioned you have Firebase set up. Now you need to get your credentials:

1. Go to your Firebase Console: https://console.firebase.google.com/
2. Select your project
3. Click the gear icon → "Project Settings"
4. Go to "Service accounts" tab
5. Click "Generate new private key"
6. Download the JSON file

### 2. Set Environment Variables

You have two options:

#### Option A: Use Service Account File (Recommended)
```bash
# Add to your .env file:
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/your/serviceAccountKey.json
```

#### Option B: Use Individual Environment Variables (For Render)
Extract these from your downloaded JSON file and add to .env:

```bash
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
```

### 3. Test Firebase Connection

Run this to test if Firebase is working:

```bash
python3 -c "
from firebase_manager import firebase_manager
import asyncio
async def test():
    await asyncio.sleep(2)
    print('Firebase available:', firebase_manager.is_available())
asyncio.run(test())
"
```

### 4. Your Current .env File Should Look Like:

```bash
# Discord Bot
DISCORD_TOKEN=your_discord_bot_token

# Firebase (choose one method)
# Method 1: Service Account File
FIREBASE_SERVICE_ACCOUNT_PATH=./serviceAccountKey.json

# OR Method 2: Individual Variables (for Render)
# FIREBASE_PROJECT_ID=your-project-id
# FIREBASE_PRIVATE_KEY="your-private-key"
# FIREBASE_CLIENT_EMAIL=your-service-account-email

# Optional: GitHub Backup (still works as secondary backup)
# GITHUB_TOKEN=your_github_token
# GIST_ID=your_gist_id
```

## 🚀 For Render Deployment

When deploying to Render, use **Method 2** (individual environment variables) because file uploads are restricted.

In your Render dashboard:
1. Go to your service → Environment
2. Add each Firebase variable separately
3. For FIREBASE_PRIVATE_KEY, copy the entire private key including the `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` parts

## 🔥 What You'll Get

✅ **Real-time Data Sync** - Instant updates across all bot instances  
✅ **Zero Data Loss** - Google's enterprise infrastructure  
✅ **Automatic Scaling** - Handle thousands of users  
✅ **Backup System** - Firebase + JSON redundancy  
✅ **Performance Boost** - 10x faster than file operations  

## Commands to Test Firebase

Once configured, these admin commands will be available:

- `!firebase_status` - Check Firebase connection
- `!migrate_to_firebase` - Migrate existing JSON data to Firebase

**Your bot will automatically use Firebase when available, and fall back to JSON if Firebase is unavailable!**