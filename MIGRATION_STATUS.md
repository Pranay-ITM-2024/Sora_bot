"""
IMPORTANT: Multi-Server Migration in Progress

STATUS: PARTIALLY COMPLETE (~20% done)

COMPLETED:
✅ bot_modules/database.py - Added get_server_data() and save_server_data()
✅ bot_modules/economy.py - MOSTLY DONE
   - balance ✅
   - daily ✅  
   - weekly ✅
   - bank ✅
   - pay ✅
   - profile ✅
   - rob ✅
   - BankView ✅
   - BankModal ✅

REMAINING WORK:
❌ economy.py - Helper functions need guild_id parameter:
   - get_user_effects(user_id) - add guild_id
   - use_consumable_effect(user_id, effect_type, value) - add guild_id
   - consume_effect(user_id, effect_type) - add guild_id
   - get_balance(user_id) - add guild_id
   - update_balance(user_id, coins, bank) - add guild_id
   - PaymentRequestView - needs guild_id handling

❌ bot_modules/shop.py (~13 issues)
❌ bot_modules/casino.py (~36 issues) 
❌ bot_modules/market.py (~37 issues)
❌ bot_modules/guild.py (~42 issues)
❌ bot_modules/heist.py (~61 issues)
❌ bot_modules/leaderboard.py (~24 issues)
❌ bot_modules/admin.py (~22 issues)
❌ bot.py - Background tasks (interest, contributions, unlocks)

PATTERN TO FOLLOW:
Every command needs these changes:

1. Add at top of command:
   guild_id = str(interaction.guild_id)

2. After load_data():
   from .database import get_server_data, save_server_data
   server_data = get_server_data(data, guild_id)

3. Replace all data.get() with server_data.get()

4. Replace all data.setdefault() with server_data.setdefault()

5. Before save_data():
   save_server_data(data, guild_id, server_data)

ESTIMATED TIME TO COMPLETE: 
- 6-8 more hours of systematic conversion work
- ~250 more data access patterns need updating
- ~30 more commands need guild_id extraction

⚠️ WARNING: Bot currently has mixed global/per-server data!
Only economy commands are using per-server data. All other modules
still use global data. DO NOT deploy until migration is complete!

NEXT STEPS:
1. Complete economy.py helper functions
2. Convert shop.py (smallest remaining - 13 issues)
3. Convert casino.py (high priority - 36 issues)
4. Convert remaining modules
5. Test with multiple Discord servers
6. Create data migration script

For questions or to continue work, see:
- MULTI_SERVER_MIGRATION_GUIDE.md
- MULTI_SERVER_TODO.md
- analyze_migration.py
