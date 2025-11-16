===========================================
📚 SORA BOT DOCUMENTATION OVERVIEW
===========================================

Welcome to the Sora Bot documentation! This folder contains all guides, 
explanations, and examples for every system in the bot.

===========================================
📁 FOLDER STRUCTURE
===========================================

explain/
├── README.txt (this file)
├── firebase_setup/         → Firebase database configuration guides
├── setup_guides/           → Bot installation and deployment guides
├── heist_system/           → Multiplayer & solo heist mechanics
├── shop_system/            → Items, equipment, and shop mechanics
└── game_systems/           → Casino, rat race, and other games

===========================================
🚀 QUICK START
===========================================

1. **Setting Up the Bot**
   → Go to: setup_guides/LOCAL_SETUP_GUIDE.md

2. **Understanding Heists**
   → Go to: heist_system/HEIST_PLAYER_GUIDE.txt

3. **Shop & Items**
   → Go to: shop_system/SHOP_GUIDE.md

4. **Firebase Configuration**
   → Go to: firebase_setup/FIREBASE_SETUP.md

===========================================
📖 DOCUMENTATION BY FEATURE
===========================================

ECONOMY SYSTEM:
- Wallet & Bank system with interest
- Daily/Weekly rewards (configurable by admins)
- Loan system with EMI payments
- Profile tracking

GUILD SYSTEM:
- Create and manage guilds
- Guild bank with contribution tracking
- Transfer ownership
- Interest sharing based on contributions

HEIST SYSTEM:
- Solo heists with 3 approaches (Stealth, Fast, Tech)
- Multiplayer heists with 5 roles (Leader, Hacker, Muscle, Scout, Driver)
- Interactive minigames for each role
- Risk/reward mechanics with gear bonuses

SHOP SYSTEM:
- Consumable items (potions with effect bonuses)
- Equipment (heist gear, casino boosters)
- Loot chests (Common, Rare, Epic, Legendary)

CASINO GAMES:
- 5-reel slots with progressive jackpots
- Blackjack with strategy gameplay
- Coin flip for quick bets

MINIGAMES:
- Rat Race betting system
- Market trading (buy low, sell high)

ADMIN TOOLS:
- Set daily/weekly reward amounts
- Add/remove coins from users
- View server statistics

===========================================
🔧 SYSTEM INTERACTIONS
===========================================

1. EARN COINS:
   - /daily & /weekly commands
   - Casino games (slots, blackjack, coinflip)
   - Heists (solo or multiplayer)
   - Rat race betting
   - Market trading

2. SPEND COINS:
   - /shop to buy items & gear
   - /deposit to add to bank
   - /payloan to clear debt
   - /guild_deposit for guild contributions

3. GROW WEALTH:
   - Bank interest: 0.5% per 24 hours
   - Guild interest: Shared among contributors
   - Strategic heists with proper gear
   - Market speculation

===========================================
💡 TIPS FOR NEW PLAYERS
===========================================

1. Start with /daily and /weekly to get initial coins
2. Deposit excess coins in /bank for interest
3. Buy heist gear from /shop before attempting heists
4. Join or create a /guild for shared benefits
5. Practice casino games with small bets first
6. Use consumables strategically for big heists

===========================================
🛠️ FOR DEVELOPERS
===========================================

Bot Structure:
- bot.py              → Main bot file with core loops
- bot_modules/        → All command cogs (economy, heist, casino, etc.)
- firebase_*.py       → Firebase data management
- web_server.py       → Health check server for hosting

Key Files:
- requirements.txt    → Python dependencies
- render.yaml         → Deployment configuration
- .env               → Environment variables (not in repo)

===========================================

For detailed information on any system, navigate to the
corresponding folder and read the documentation files.

Happy gaming! 🎮
