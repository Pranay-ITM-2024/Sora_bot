===========================================
⚙️ SETUP & DEPLOYMENT GUIDES
===========================================

Complete guides for setting up, deploying,
and maintaining your Sora Bot instance.

===========================================
📄 FILES IN THIS FOLDER
===========================================

1. LOCAL_SETUP_GUIDE.md
   → Setting up bot on local machine
   → Development environment
   → Testing and debugging

2. MULTI_SERVER_CONVERSION_COMPLETE.md
   → Multi-server architecture explanation
   → Data separation per Discord server
   → Migration from single to multi-server

===========================================
🚀 QUICK START (LOCAL SETUP)
===========================================

PREREQUISITES:
- Python 3.8+ installed
- Discord bot token
- Firebase project (see firebase_setup/)
- Git (optional, for cloning)

STEP 1: Clone/Download Repository
git clone https://github.com/yourusername/sora-bot.git
cd sora-bot

STEP 2: Install Dependencies
pip install -r requirements.txt

Required packages:
- discord.py (Discord API)
- firebase-admin (Database)
- python-dotenv (Environment variables)
- aiohttp (Async HTTP)

STEP 3: Configure Environment
Create .env file in root directory:

DISCORD_TOKEN=your_discord_bot_token_here
FIREBASE_CREDENTIALS_PATH=firebase_credentials.json

Get Discord token:
1. Go to https://discord.com/developers
2. Create application
3. Go to Bot section
4. Copy token

STEP 4: Setup Firebase
Follow guides in explain/firebase_setup/
- Create Firebase project
- Download credentials JSON
- Place in root as firebase_credentials.json
- NEVER commit this file!

STEP 5: Run Bot
python bot.py

Bot should come online in your Discord server!

===========================================
🌐 DEPLOYMENT (RENDER.COM)
===========================================

OVERVIEW:
Render.com offers free hosting for Discord bots
with automatic deployments from GitHub.

STEP 1: Prepare Repository
Ensure you have:
- requirements.txt (dependencies)
- render.yaml (deployment config)
- .gitignore (excludes .env, credentials)

STEP 2: Create Render Account
1. Go to https://render.com
2. Sign up (free tier available)
3. Connect GitHub account

STEP 3: Create Web Service
1. Click "New +"
2. Select "Web Service"
3. Connect your GitHub repo
4. Choose branch (main/master)

STEP 4: Configure Service
Name: sora-bot
Environment: Python
Build Command: pip install -r requirements.txt
Start Command: python bot.py

STEP 5: Add Environment Variables
In Render dashboard:
- Add DISCORD_TOKEN
- Add FIREBASE_CREDENTIALS_PATH
- Upload firebase_credentials.json as file

STEP 6: Deploy
- Click "Create Web Service"
- Wait for deployment (2-5 minutes)
- Check logs for errors
- Bot should be online!

AUTO-DEPLOY:
- Push to GitHub
- Render auto-deploys
- Zero downtime updates

===========================================
🏗️ BOT ARCHITECTURE
===========================================

FILE STRUCTURE:
sora-bot/
├── bot.py                 → Main bot file
├── web_server.py          → Health check server
├── firebase_manager.py    → Firebase connection
├── firebase_data_manager.py → Data operations
├── requirements.txt       → Python packages
├── render.yaml           → Deployment config
├── .env                  → Environment variables (local)
├── bot_modules/          → Command modules (cogs)
│   ├── economy.py        → Wallet, bank, rewards
│   ├── casino.py         → Slots, blackjack, coinflip
│   ├── heist.py          → Solo & multiplayer heists
│   ├── guild.py          → Guild system
│   ├── shop.py           → Shop & items
│   ├── inventory.py      → Item management
│   ├── loan.py           → Loan system
│   ├── leaderboard.py    → Rankings
│   ├── market.py         → Trading system
│   ├── admin.py          → Admin commands
│   └── help.py           → Help command
└── explain/              → Documentation (this folder)

===========================================
🔧 MULTI-SERVER ARCHITECTURE
===========================================

OVERVIEW:
Sora Bot supports multiple Discord servers
with completely isolated data per server.

DATA STRUCTURE:
{
  "servers": {
    "SERVER_ID_1": {
      "coins": {...},
      "bank": {...},
      "guilds": {...},
      ...
    },
    "SERVER_ID_2": {
      "coins": {...},
      "bank": {...},
      "guilds": {...},
      ...
    }
  }
}

KEY FEATURES:
- Each server has independent economy
- Separate guild systems per server
- Server-specific settings (daily/weekly rewards)
- No data leakage between servers
- Admins control their server only

MIGRATION:
If you're converting from single-server:
See MULTI_SERVER_CONVERSION_COMPLETE.md

===========================================
🔐 SECURITY BEST PRACTICES
===========================================

ENVIRONMENT VARIABLES:
✅ Use .env for sensitive data
✅ Never commit tokens/credentials
✅ Add .env to .gitignore
✅ Use different tokens for dev/prod

FIREBASE:
✅ Proper security rules
✅ Service account only access
✅ Regular backups
✅ Monitor for unusual activity

DISCORD:
✅ Bot permissions: minimum required
✅ Enable 2FA on Discord account
✅ Regenerate token if compromised
✅ Use role-based command restrictions

CODE:
✅ Validate all user inputs
✅ Use ephemeral messages for sensitive info
✅ Implement rate limiting
✅ Error handling on all commands

===========================================
🐛 DEBUGGING & TROUBLESHOOTING
===========================================

BOT WON'T START:
- Check Discord token is correct
- Verify Firebase credentials exist
- Check Python version (3.8+)
- Install all requirements

COMMANDS NOT WORKING:
- Ensure bot has proper permissions
- Check if slash commands synced
- Wait 1 hour for command registration
- Check bot role hierarchy

DATA NOT SAVING:
- Verify Firebase connection
- Check Firebase security rules
- Look for errors in console
- Test with /daily command

FIREBASE ERRORS:
- Credentials path correct?
- Database exists in console?
- Security rules allow access?
- Check Firebase Console logs

===========================================
📊 MONITORING & MAINTENANCE
===========================================

HEALTH CHECKS:
- web_server.py runs health endpoint
- Render pings every 5 minutes
- Prevents dyno sleep on free tier

LOGGING:
- Bot prints to console
- Render captures all logs
- Check for errors regularly

BACKUPS:
- Firebase auto-backs up data
- Manual export in console
- Keep local backup periodically

UPDATES:
1. Make changes locally
2. Test thoroughly
3. Commit to GitHub
4. Push to main branch
5. Render auto-deploys
6. Monitor logs for errors

===========================================
🔄 UPDATING THE BOT
===========================================

ADD NEW COMMAND:
1. Edit appropriate cog in bot_modules/
2. Add command function
3. Test locally
4. Update help.py documentation
5. Deploy to production

ADD NEW FEATURE:
1. Plan data structure changes
2. Update Firebase security rules if needed
3. Implement feature in cog
4. Add tests
5. Update documentation
6. Deploy gradually

MODIFY EXISTING:
1. Check all usages with grep/search
2. Test changes thoroughly
3. Consider backward compatibility
4. Update affected commands
5. Deploy and monitor

===========================================
📈 PERFORMANCE OPTIMIZATION
===========================================

REDUCE LATENCY:
- Use async/await properly
- Batch database operations
- Cache frequently accessed data
- Use defer() for slow commands

REDUCE COSTS:
- Minimize Firebase reads/writes
- Implement data caching
- Use efficient queries
- Delete old/unused data

IMPROVE UX:
- Fast command responses
- Clear error messages
- Helpful command hints
- Intuitive interfaces

===========================================
👥 MULTI-BOT SETUP
===========================================

DEVELOPMENT BOT:
- Separate Discord application
- Different Firebase project
- Test all changes here first
- Invite to test server only

PRODUCTION BOT:
- Main Discord application
- Production Firebase database
- Only deploy tested changes
- Invite to all real servers

BENEFITS:
- Safe testing environment
- No risk to real users
- Debug without pressure
- Easy rollback if needed

===========================================
🔧 ADMIN TOOLS
===========================================

/setdaily <amount>
- Configure daily reward for server
- Affects all server members

/setweekly <amount>
- Configure weekly reward for server
- Per-server customization

/addcoins <user> <amount>
- Add coins to user's wallet
- For events, competitions, corrections

/removecoins <user> <amount>
- Remove coins from user
- For penalties, exploits

ADMIN REQUIREMENTS:
- Must have Administrator permission
- Or have designated admin role
- Per-server admin control

===========================================
❓ COMMON QUESTIONS
===========================================

Q: How do I invite bot to my server?
A: Discord Developer Portal → OAuth2 → URL Generator
   Select scopes: bot, applications.commands
   Select permissions needed
   Copy URL and open in browser

Q: Can I run multiple instances?
A: No, one bot token = one instance
   Use different tokens for dev/prod

Q: How much does hosting cost?
A: Render free tier works fine
   Firebase free tier: 1GB storage
   Upgrade if needed

Q: Can I modify the code?
A: Yes! It's your bot instance
   Keep documentation updated

Q: How do I backup data?
A: Firebase Console → Database → Export
   Save JSON file locally

===========================================
📚 ADDITIONAL RESOURCES
===========================================

Discord.py Documentation:
https://discordpy.readthedocs.io/

Firebase Admin SDK:
https://firebase.google.com/docs/admin/setup

Render Deployment:
https://render.com/docs

Python Best Practices:
https://docs.python-guide.org/

===========================================

For system-specific setup information,
check the other folders in explain/

Good luck with your bot! 🤖✨
