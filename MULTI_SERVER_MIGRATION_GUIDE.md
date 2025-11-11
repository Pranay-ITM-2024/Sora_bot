# Multi-Server Data Separation - Migration Guide

## Overview

This bot now supports running on **multiple Discord servers** with completely isolated data per server.

## Data Structure Change

### Before (Global):
```json
{
  "coins": {
    "user123": 1000,
    "user456": 2000
  },
  "bank": {
    "user123": 5000
  }
}
```

### After (Per-Server):
```json
{
  "servers": {
    "guild_id_111": {
      "coins": {
        "user123": 1000
      },
      "bank": {
        "user123": 5000
      }
    },
    "guild_id_222": {
      "coins": {
        "user456": 2000
      },
      "bank": {}
    }
  }
}
```

## Implementation Strategy

### Phase 1: Add Helper Functions ✅
- Added `get_server_data(data, guild_id)` 
- Added `save_server_data(data, guild_id, server_data)`
- These functions handle server data isolation

### Phase 2: Update All Commands (TODO)
Every command needs to:
1. Get `guild_id` from `interaction.guild_id` or `interaction.guild.id`
2. Load server-specific data using `get_server_data()`
3. Work with server data instead of global data
4. Save back to global data structure

### Phase 3: Migration Script (TODO)
Create script to migrate existing data:
- Move current global data to first server
- Preserve all existing user data
- No data loss

## Example Command Update

### Before:
```python
async def balance(self, interaction):
    user_id = str(interaction.user.id)
    data = await load_data()
    coins = data.get("coins", {}).get(user_id, 0)
    bank = data.get("bank", {}).get(user_id, 0)
```

### After:
```python
async def balance(self, interaction):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild_id)
    
    data = await load_data()
    server_data = get_server_data(data, guild_id)
    
    coins = server_data.get("coins", {}).get(user_id, 0)
    bank = server_data.get("bank", {}).get(user_id, 0)
```

## Benefits

✅ **Complete Data Isolation**
- Server A's economy is separate from Server B
- Users can have different balances on different servers
- Server admins have full control over their server's economy

✅ **No Cross-Contamination**
- Guilds (in-game) are server-specific
- Leaderboards are server-specific
- Shop and items are server-specific

✅ **Scalability**
- Add unlimited Discord servers
- Each server's data is independent
- No conflicts or overwrites

## Status

- [ ] Helper functions created
- [ ] Economy commands updated
- [ ] Casino commands updated
- [ ] Shop commands updated
- [ ] Guild commands updated
- [ ] Heist commands updated
- [ ] Leaderboard commands updated
- [ ] Admin commands updated
- [ ] Migration script created
- [ ] Testing completed

## Next Steps

1. Update all command modules to use `get_server_data()`
2. Test on development server
3. Create migration script
4. Deploy to production
5. Monitor for issues

---

**Important**: This is a breaking change that requires careful migration of existing data!
