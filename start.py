#!/usr/bin/env python3
"""
SORABOT Startup Script
Run this to start the Discord economy bot
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from config.env file
load_dotenv('config.env')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the bot
from bot import bot

if __name__ == "__main__":
    # Check for Discord token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ Error: DISCORD_TOKEN environment variable not set!")
        print("Please set your Discord bot token:")
        print("export DISCORD_TOKEN='your_bot_token_here'")
        sys.exit(1)
    
    try:
        print("🚀 Starting SORABOT...")
        bot.run(token)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        sys.exit(1)
