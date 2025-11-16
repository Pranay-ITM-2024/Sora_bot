# Guild Leader-Controlled Heist System - Update Summary

## 🎯 Key Changes

### 1. **Guild Leader Restriction**
- **ONLY guild leaders** can initiate heists using `/heist` command
- Non-leaders attempting to use `/heist` receive error message showing who their guild leader is
- This prevents unauthorized heist attempts and gives leaders full control

### 2. **Guild-Based Cooldown (Not Per-Player)**
- **OLD:** Each player could heist once per Sunday
- **NEW:** Each GUILD can heist once per Sunday (regardless of who participated)
- Cooldown tracked at guild level: `data["cooldowns"]["guild_heist"][guild_name]`
- Prevents multiple heist attempts by same guild using different members

### 3. **Leader Selects Team Members**
- **OLD:** Open recruitment - any guild member could click "Join Heist"
- **NEW:** Guild leader manually selects which members participate
- Leader uses dropdown menu to choose 1-4 additional members (2-5 total including leader)
- Selected members cannot opt-out - they're chosen by the leader

## 📋 Updated Heist Flow

### For Guild Leaders:

1. **Initiate Heist** (Sunday only)
   ```
   /heist target_guild:EnemyGuild amount:50000
   ```

2. **Choose Mode**
   - **Solo Heist** - Leader goes alone
   - **Multiplayer Heist** - Leader selects 1-4 team members

3. **Select Team** (Multiplayer only)
   - Dropdown shows all guild members
   - Leader selects 1-4 additional members
   - Leader is automatically included in team
   - Click "Confirm Team & Proceed"

4. **Assign Roles**
   - Leader assigns a role to each selected member
   - Roles: Leader, Hacker, Muscle, Driver, Scout
   - Each role has unique tasks

5. **Execute Heist**
   - 3 phases: Entry → Vault → Escape
   - Each member must complete their role-specific task
   - If ANY member fails, ENTIRE team fails

### For Regular Members:

- **Cannot initiate heists** - must wait for leader
- **Cannot volunteer** - must be selected by leader
- If selected by leader, **must participate** (no opt-out)
- Contribute by completing assigned role tasks

## 🔧 Technical Changes

### File: `bot_modules/heist.py`

#### Changed: Heist Command
```python
# Now checks for guild leader
guild_owner = guild_data.get("owner")
if str(guild_owner) != user_id:
    # Error: Only leaders can initiate
```

#### Changed: Cooldown System
```python
# OLD: Per-user cooldown
data["cooldowns"]["heist"][user_id] = timestamp

# NEW: Per-guild cooldown  
data["cooldowns"]["guild_heist"][guild_name] = timestamp
```

#### New Class: `HeistMemberSelectView`
- Replaces open recruitment system
- Dropdown for leader to select team members
- Shows all guild members (max 24)
- Leader selects 1-4 additional members
- "Confirm Team & Proceed" button

#### Removed Class: `HeistRecruitView`
- Old system where members clicked "Join Heist"
- No longer needed with leader selection

#### Updated Class: `HeistConfirmView`
- Now shows "Select team members" for multiplayer
- Leader controls all aspects

### File: `bot_modules/help.py`

Updated heist documentation to reflect:
- Guild leaders only
- One heist per guild (not per player)
- Leader selects team members
- No open recruitment

## 📊 Data Structure Changes

### Cooldown Tracking
```python
# NEW structure
data = {
    "cooldowns": {
        "guild_heist": {
            "GuildName": "2025-11-10T15:30:00",  # Guild-level cooldown
            "AnotherGuild": "2025-11-10T14:20:00"
        }
    }
}

# OLD structure (deprecated for heists)
data = {
    "cooldowns": {
        "heist": {
            "user_id": "timestamp"  # No longer used for heists
        }
    }
}
```

## 🎮 Use Cases & Examples

### Example 1: Leader Initiates Solo Heist
1. Leader uses `/heist target_guild:Rivals amount:100000`
2. Leader clicks "Solo Heist"
3. Guild cooldown set - no other heists this Sunday
4. Leader completes heist alone

### Example 2: Leader Initiates Multiplayer Heist
1. Leader uses `/heist target_guild:Rivals amount:100000`
2. Leader clicks "Multiplayer Heist (2-5 players)"
3. Dropdown appears with guild members
4. Leader selects: @Member1, @Member2, @Member3
5. Leader clicks "Confirm Team & Proceed"
6. Leader assigns roles: Leader (self), Hacker (M1), Muscle (M2), Driver (M3)
7. All 4 members must complete tasks
8. Guild cooldown prevents any more heists this Sunday

### Example 3: Non-Leader Attempts Heist
1. Regular member uses `/heist target_guild:Rivals amount:50000`
2. Receives error: "❌ Only the guild leader can initiate heists! Your guild leader is @LeaderName"
3. Must wait for leader to initiate

### Example 4: Second Heist Attempt
1. Guild already completed heist this Sunday
2. Leader tries `/heist` again
3. Receives error: "⏰ Your guild **GuildName** has already done a heist today! One heist per Sunday per guild."
4. Must wait until next Sunday

## ⚠️ Important Notes

### Guild Leader Requirements:
- Only the guild owner (creator) can initiate heists
- Officers/co-leaders CANNOT initiate heists
- Leader must be in the guild (obviously)

### Team Selection:
- Leader chooses members - members don't volunteer
- Selected members receive no notification until roles are assigned
- No confirmation/acceptance required from selected members
- If a selected member is offline, heist may fail (they can't complete task)

### Cooldown Management:
- Cooldown applied at guild level when:
  - Solo heist starts
  - Multiplayer roles confirmed and heist starts
- Cooldown resets on Monday (new week)
- Affects ENTIRE guild - no member can bypass

### Strategy Implications:
- Leaders should coordinate with members before selecting them
- Check member availability before starting heist
- Consider member gear/bonuses when forming team
- Solo heists have lower rewards but simpler coordination

## 🐛 Potential Issues & Solutions

### Issue: Selected Member is AFK
**Problem:** Leader selects member who's offline, they can't complete task  
**Solution:** Leader should verify member availability first  
**Future Enhancement:** Add member online status check

### Issue: Member Refuses to Participate
**Problem:** Selected member doesn't want to participate  
**Solution:** Currently no opt-out - leader must choose wisely  
**Future Enhancement:** Could add decline button with penalty

### Issue: Leader Abuse
**Problem:** Leader repeatedly selects same members  
**Solution:** No current solution - guild governance issue  
**Future Enhancement:** Could add member heist participation limits

## 📈 Statistics & Tracking

### Trackable Metrics:
- Heists initiated per guild per week
- Solo vs multiplayer heist success rates
- Leader performance (as initiator)
- Guild heist frequency
- Cooldown compliance

### Leaderboard Ideas:
- Most successful guild leaders
- Most active heist guilds
- Best heist teams
- Highest single-heist earnings

---

## 🚀 Testing Checklist

- [x] Non-leader cannot use `/heist` command
- [x] Guild leader can use `/heist` command
- [x] Leader can select team members for multiplayer
- [x] Team members appear in role selection
- [x] Guild cooldown prevents second heist
- [x] Solo heist sets guild cooldown
- [x] Multiplayer heist sets guild cooldown
- [x] Error messages show correct guild leader
- [ ] Test with actual Discord users (live testing needed)

---

**Version:** 2.1.0 (Leader-Controlled Heists)  
**Date:** November 2025  
**Changes:** Guild leader restrictions, guild-based cooldown, leader team selection
