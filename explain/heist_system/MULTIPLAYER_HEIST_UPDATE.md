# Multiplayer Heist & Saturday Contribution System - Update Summary

## 🎯 Major Features Added

### 1. **Multiplayer Role-Based Heist System**
- **Team Size:** 2-5 players from the same guild
- **Roles Available:**
  - 👔 **Leader** - Coordinates team, makes critical decisions
  - 💻 **Hacker** - Disables security systems and cameras
  - 💪 **Muscle** - Breaks into vault, handles obstacles
  - 🚗 **Driver** - Manages escape and getaway
  - 👁️ **Scout** - Monitors surroundings, detects threats

#### Heist Flow:
1. Leader initiates `/heist` command
2. Choose between Solo or Multiplayer mode
3. **Multiplayer Mode:**
   - 2-minute recruitment phase (guild members click "Join Heist")
   - Leader assigns roles to each member
   - All members confirm roles
   - **3 Phases:** Entry → Vault Breach → Escape
   - Each player clicks "Complete Task" for their role
   - Success chance based on role bonuses and gear
   - **Critical Rule:** If ANY player fails their task, ENTIRE heist fails!

4. **Solo Mode:**
   - Traditional 3-button gameplay (Stealth/Fast/Tech)
   - Single player controls all aspects
   - Simpler mechanics, lower rewards

#### Rewards & Penalties:
- **Success (Multiplayer):**
  - Stolen amount goes to attacker's guild bank
  - 10% of stolen amount split equally among all team members as personal reward
  
- **Failure (Multiplayer):**
  - 30% penalty split equally among all team members
  - Each member pays from wallet/bank (debt if insufficient)
  - All penalties paid to target guild bank

### 2. **Saturday Automatic Guild Contribution**
- **Every Saturday:** Bot automatically runs contribution task
- **Contribution:** 75% of each guild member's total worth (wallet + bank)
- **Process:**
  - Takes from bank first, then wallet
  - Adds directly to guild bank
  - Tracks individual contributions per member
  - Locks guild bank withdrawals

#### Withdrawal Lock System:
- **Locked:** Saturday contribution until unlock conditions met
- **Unlock Conditions:**
  1. Sunday 8 PM UTC (automatic unlock task)
  2. OR when guild bank is targeted by heist attempt
- **Benefits:** Protects Saturday contributions, encourages heist defense

### 3. **Guild Join Approval System**
- **Old System:** Members could instantly join any guild
- **New System:**
  1. Player selects guild from dropdown
  2. Bot sends DM to guild owner with approval request
  3. Owner has 24 hours to Approve ✅ or Deny ❌
  4. Applicant receives DM notification of decision
  5. No typing required - all button-based

#### Features:
- Prevents guild spam/trolling
- Gives owners control over membership
- Automatic timeout after 24 hours
- Both parties notified via DM

## 🔧 Technical Implementation

### New Files Modified:
1. **bot_modules/heist.py** - Complete rewrite
   - `HeistRecruitView` - Recruitment interface
   - `HeistRoleSelectView` - Role assignment system
   - `MultiplayerHeistView` - Team-based gameplay
   - `SoloHeistView` - Single-player gameplay
   - 5 role definitions with unique tasks per phase

2. **bot.py** - Added background tasks
   - `saturday_contribution_task()` - Runs hourly, checks for Saturday
   - `sunday_unlock_task()` - Runs hourly, unlocks at Sunday 8 PM
   - Both tasks added to `on_ready()` startup

3. **bot_modules/guild.py** - Join approval system
   - `GuildJoinApprovalView` - Owner approval interface
   - Updated `GuildJoinSelect` to send DM requests
   - Updated `WithdrawModal` to check withdrawal locks
   - Added bot instance passing for DM functionality

4. **bot_modules/help.py** - Documentation updated
   - Multiplayer heist roles documented
   - Saturday contribution explained
   - Withdrawal lock mechanics
   - Guild approval system

### Data Structure Changes:
```python
# New data fields added:
data = {
    "saturday_contributions": {
        "guild_name": {
            "user_id": {
                "amount": 10000,
                "timestamp": "2025-11-11T12:00:00"
            }
        }
    },
    "withdrawal_locks": {
        "guild_name": {
            "locked": True,
            "locked_since": "2025-11-09T00:00:00",
            "heist_attempted": False,
            "unlocked_at": null
        }
    },
    "_meta": {
        "last_saturday_contribution": "2025-11-09T00:00:00"
    }
}
```

## 🎮 How to Use (Player Guide)

### Starting a Multiplayer Heist:
1. Wait for Sunday
2. Use `/heist target_guild:GuildName amount:50000`
3. Click "Multiplayer Heist (2-5 players)"
4. Wait for teammates to click "Join Heist"
5. When ready, click "Start Heist"
6. Assign roles to each member
7. Click "Confirm Roles & Start"
8. **Each player must complete their task** by clicking "Complete Task" button
9. Watch progress bars and noise level
10. Complete all 3 phases without anyone failing!

### Saturday Contributions:
- **Automatic** - no action needed
- Bot takes 75% of your wealth Saturday morning
- Goes directly to your guild bank
- Cannot withdraw until Sunday night or heist
- Check `/guild_bank` to see locked status

### Joining Guilds (New):
1. Use `/guild_join`
2. Select guild from dropdown
3. Wait for owner approval (you'll get DM)
4. Owner receives DM with your request
5. They click Approve or Deny
6. You're notified of decision via DM

## ⚙️ Admin Notes

### Background Tasks:
- `saturday_contribution_task` - Runs every hour, only executes on Saturday
- `sunday_unlock_task` - Runs every hour, only executes Sunday 8+ PM UTC
- Both tasks have safety checks to prevent duplicate runs
- All changes force-saved to Firebase

### Discord Permissions Required:
- Bot needs permission to send DMs to users
- If DMs fail, guild join system won't work properly
- Users should be reminded to enable DMs from server members

### Testing Recommendations:
1. Test multiplayer heist with 2-5 players
2. Verify role assignment works
3. Test task failure (one player fails = all fail)
4. Verify Saturday contributions (may need to adjust time for testing)
5. Test withdrawal locks
6. Test guild join approval with DMs
7. Test heist attempt unlocking guild bank

## 🐛 Known Issues & Considerations

1. **DM Failures:** If user has DMs disabled, guild join approval won't work
   - Bot will notify with error message
   - Owner won't receive request
   
2. **Saturday Timing:** Uses UTC timezone
   - Contributions may happen at different local times
   - Can be adjusted in `bot.py` if needed

3. **Multiplayer Coordination:** Requires team communication
   - No built-in voice/chat
   - Teams should use Discord voice channels

4. **Timeout Handling:** 
   - Multiplayer heist: 5 minutes total
   - Guild join approval: 24 hours
   - Both will auto-cancel if timeout

## 📊 Statistics & Tracking

### New Trackable Metrics:
- Total Saturday contributions per guild
- Individual contribution amounts
- Heist success/fail rates (multiplayer vs solo)
- Role performance statistics
- Withdrawal lock duration
- Guild join approval/denial rates

### Future Enhancement Ideas:
- Heist leaderboard (most successful heists)
- Role-specific achievements
- Saturday contribution leaderboard
- Guild defense statistics
- Auto-recruit system for heists
- Heist replay/highlights

---

## 🚀 Deployment Checklist

- [x] All code tested for syntax errors
- [x] Background tasks added to startup
- [x] Help command updated
- [x] Data structures implemented
- [x] Error handling added
- [x] DM permissions handled
- [ ] Test on live server
- [ ] Monitor first Saturday contribution
- [ ] Monitor first Sunday unlock
- [ ] Test multiplayer heist with real users

---

**Version:** 2.0.0  
**Date:** November 2025  
**Author:** SORABOT Development Team
