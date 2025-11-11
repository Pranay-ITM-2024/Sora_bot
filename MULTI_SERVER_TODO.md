# Multi-Server Migration TODO List

## ✅ Phase 1: Infrastructure (COMPLETED)
- [x] Add helper functions to database.py
  - [x] `get_server_data(data, guild_id)`
  - [x] `save_server_data(data, guild_id, server_data)`
- [x] Create migration guide documentation
- [x] Update `balance` command in economy.py
- [x] Update `daily` command in economy.py

## 🔄 Phase 2: Economy Module Commands (IN PROGRESS)
File: `bot_modules/economy.py` (928 lines)

- [x] `balance` - DONE
- [x] `daily` - DONE
- [ ] `weekly`
- [ ] `pay`
- [ ] `rob`
- [ ] `bank` (deposit, withdraw)
- [ ] `profile`
- [ ] Helper functions that need server_data parameter:
  - [ ] `get_user_effects(user_id)` - add guild_id parameter
  - [ ] `use_consumable_effect(user_id, effect_type, value)` - add guild_id
  - [ ] `consume_effect(user_id, effect_type)` - add guild_id
  - [ ] `get_balance(user_id)` - add guild_id
  - [ ] `update_balance(user_id, coins, bank)` - add guild_id

## 📋 Phase 3: Casino Module (HIGH PRIORITY)
File: `bot_modules/casino.py` (~1264 lines)

Commands to update:
- [ ] `slots`
- [ ] `coinflip`
- [ ] `blackjack` (including BlackjackView class)
- [ ] `roulette`
- [ ] `ratrace`
- [ ] `track_casino_game()` function - needs server_data parameter

## 🛒 Phase 4: Shop Module
File: `bot_modules/shop.py` (~445 lines)

Commands to update:
- [ ] `shop` (view)
- [ ] `buy` (with BuyConfirmView)
- [ ] `inventory`
- [ ] `equip`
- [ ] `unequip`
- [ ] `use`
- [ ] `openchest`

## 🏰 Phase 5: Guild Module
File: `bot_modules/guild.py`

Commands to update:
- [ ] `guild` (view)
- [ ] `create_guild`
- [ ] `join_guild`
- [ ] `leave_guild`
- [ ] `guild_deposit`
- [ ] `guild_withdraw`
- [ ] `guild_upgrade`
- [ ] `guild_stats`

## 💰 Phase 6: Market Module
File: `bot_modules/market.py`

Commands to update:
- [ ] `stocks` (view)
- [ ] `buy_stock`
- [ ] `sell_stock`
- [ ] `portfolio`

## 🏆 Phase 7: Leaderboard Module
File: `bot_modules/leaderboard.py` (~517 lines)

Commands to update:
- [ ] `leaderboard wealth`
- [ ] `leaderboard casino`
- [ ] `leaderboard stocks`
- [ ] `leaderboard guilds`

## 👮 Phase 8: Admin Module
File: `bot_modules/admin.py`

Commands to update:
- [ ] `givecoin`
- [ ] `takecoin`
- [ ] Other admin commands if any

## 🎯 Phase 9: Heist Module
File: `bot_modules/heist.py`

Commands to update:
- [ ] All heist-related commands
- [ ] Heist state management per-server

## ⏰ Phase 10: Background Tasks
File: `bot.py`

Tasks to update:
- [ ] `interest_task` - Apply interest per-server
- [ ] `saturday_contributions_task` - Per-server guild contributions
- [ ] `sunday_unlock_task` - Per-server vault unlocks
- [ ] Any other scheduled tasks

## 🧪 Phase 11: Testing & Migration
- [ ] Create data migration script
  - [ ] Move existing global data to first server
  - [ ] Test with multiple guild_ids
- [ ] Test all commands on multiple Discord servers
- [ ] Verify data isolation between servers
- [ ] Test leaderboards are server-specific
- [ ] Test guild system is server-specific
- [ ] Check for any data leaks between servers

## 📝 Phase 12: Documentation
- [ ] Update README.md
- [ ] Document multi-server setup
- [ ] Add deployment guide for multiple servers
- [ ] Update command documentation

---

## Current Status: Phase 2 (2/7 commands done)

### Pattern for Updates

Every command needs:

```python
# OLD:
async def command(self, interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    data = await load_data()
    coins = data.get("coins", {}).get(user_id, 0)
    # ... rest of command ...
    await save_data(data)

# NEW:
async def command(self, interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild_id)  # ADD THIS
    
    data = await load_data()
    from .database import get_server_data, save_server_data  # ADD THIS
    server_data = get_server_data(data, guild_id)  # ADD THIS
    
    coins = server_data.get("coins", {}).get(user_id, 0)  # USE server_data
    # ... rest of command ...
    
    save_server_data(data, guild_id, server_data)  # ADD THIS
    await save_data(data)
```

### Helper Functions Pattern

```python
# OLD:
async def get_balance(user_id):
    data = await load_data()
    coins = data.get("coins", {}).get(str(user_id), 0)
    return coins

# NEW:
async def get_balance(user_id, guild_id):
    data = await load_data()
    from .database import get_server_data
    server_data = get_server_data(data, guild_id)
    coins = server_data.get("coins", {}).get(str(user_id), 0)
    return coins
```

---

## Estimated Progress: 5% Complete

- Infrastructure: ✅ 100%
- Economy module: 🔄 29% (2/7 main commands)
- Other modules: ⏳ 0%

**Next Action**: Continue updating economy.py commands (weekly, pay, rob, bank, profile)
