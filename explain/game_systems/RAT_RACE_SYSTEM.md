# 🏁 RAT RACE - Multiplayer Live Racing System

## Overview
The Rat Race is a **multiplayer gambling game** where multiple users can bet on the same race in real-time with live visual updates.

## Features

### ✨ Core Mechanics
- **6 Rats per Race** - Each with unique randomized stats
- **Multiplayer Betting** - Multiple users bet on the same race
- **Live Updates** - Race updates every 2 seconds with visual track
- **30 Second Betting Phase** - Time to analyze stats and place bets
- **Random Movement** - Rats move 0-2 spaces per turn based on stats
- **Random Forfeit** - One rat may forfeit during race (20% chance)
- **20 Space Track** - First to finish wins

### 🐭 Rat Stats (Randomized Each Race)
Each rat has three stats that affect performance:

1. **Speed (40-100)** 
   - Affects movement probability
   - Higher speed = more likely to move 2 spaces

2. **Stamina (40-100)**
   - Affects consistency
   - Higher stamina = less likely to stand still

3. **Luck (40-100)**
   - Affects random events
   - Higher luck = better chances overall

**Visual Stat Bars:**
```
Speed:   ████████░░ 80
Stamina: ██████░░░░ 60
Luck:    ██████████ 100
```

### 💰 Payout System
- 🥇 **1st Place:** 5x your bet
- 🥈 **2nd Place:** 2x your bet
- 🥉 **3rd Place:** 1.5x your bet
- ❌ **4th-6th:** Lose bet

### 🎮 How to Play

#### Step 1: Start a Race
```
/ratrace
```
Click **"Start New Race"** button

#### Step 2: Analyze Rats (30 seconds)
The lobby shows:
- All 6 rats with their randomized stats
- Speed, Stamina, and Luck bars for each rat
- Current bets from other players

#### Step 3: Place Your Bet
1. Select your rat from dropdown menu
2. Enter bet amount in modal (minimum 10 coins)
3. Wait for other players to join

#### Step 4: Watch the Race!
- Race starts automatically after 30 seconds
- Live updates every 2 seconds
- Visual track shows rat positions
- See which rats are forfeiting
- Real-time finish notifications

#### Step 5: Collect Winnings
- Final results show all placements
- Payouts distributed automatically
- Your new balance updated immediately

## Race Mechanics

### Movement System
Each turn, every rat can:
- **Stand Still (0 spaces)** - 20% chance (affected by stamina)
- **Move 1 Space** - 30-50% chance (affected by speed)
- **Move 2 Spaces** - 30-50% chance (affected by speed)

Formula:
```python
roll = random(0, 1)
if roll < 0.2 * (stamina/100):
    move 0 spaces
elif roll < 0.5 + 0.3 * (speed/100):
    move 1 space
else:
    move 2 spaces
```

### Forfeit System
- **20% chance** one rat will forfeit during the race
- Only **1 rat maximum** can forfeit per race
- Forfeited rats cannot win or place
- Bets on forfeited rats automatically lose

### Race End Conditions
Race ends when:
1. **Top 3 rats cross finish line**, OR
2. **All rats finish or forfeit**

## Visual Features

### 🎨 Live Race Track
```
▓▓▓▓▓▓🐭░░░░░░░░░░░░ Speedy 💰2
▓▓▓▓▓▓▓▓🐀░░░░░░░░░░ Whiskers
▓▓▓▓🐁░░░░░░░░░░░░░░ Nibbles 💰1
🐭 ❌ FORFEITED - Flash
▓▓▓▓▓▓▓▓▓▓🐀░░░░░░░░ Chomper
▓▓▓▓▓▓▓🐁░░░░░░░░░░░ Dash
```

**Legend:**
- `▓` = Track completed
- `░` = Track remaining
- `🐭🐀🐁` = Rat position
- `💰2` = Number of bettors on this rat
- `❌ FORFEITED` = Rat gave up

### 📊 Betting Phase Display
Shows:
- Race ID (last 8 characters)
- Host username
- All 6 rats with full stats
- Current bets from all players
- 30-second countdown

### 🏆 Results Display
Shows:
- Final track positions
- Podium (1st, 2nd, 3rd with multipliers)
- All player payouts with profit/loss
- Each player's chosen rat

## Strategy Tips

### 💡 Betting Strategy

1. **High Speed Rats**
   - More likely to move 2 spaces
   - Better for quick wins
   - Higher risk (may tire out)

2. **Balanced Stats**
   - Consistent performance
   - Lower risk of forfeiting
   - Safe bet for placement

3. **High Stamina**
   - Won't stand still as often
   - Steady progress
   - Good for avoiding forfeits

4. **Watch Other Bets**
   - See what others are betting
   - Avoid overly popular rats (no advantage)
   - Find undervalued rats

5. **Forfeit Risk**
   - 20% chance of 1 forfeit per race
   - No way to predict which rat
   - Spread risk if playing multiple races

### 📈 Probability Analysis

**Expected Win Rate (Single Bet):**
- 1st Place: ~16.67% (1 in 6)
- 2nd Place: ~16.67% (1 in 6)
- 3rd Place: ~16.67% (1 in 6)
- Total Placement: ~50%

**Expected Value:**
- 1st: 5x * 0.167 = 0.835
- 2nd: 2x * 0.167 = 0.334
- 3rd: 1.5x * 0.167 = 0.251
- **Total EV:** ~142% (profitable!)

*Note: Stats affect these probabilities. Higher stats = better odds.*

## Technical Details

### Race Lifecycle
1. **Creation** - User starts race, lobby created
2. **Betting** - 30 second window, multiple users can join
3. **Validation** - Bets deducted from wallets
4. **Race Start** - 3...2...1...GO!
5. **Turn Loop** - Rats move every 2 seconds
6. **Forfeit Check** - Random forfeit may occur
7. **Finish Check** - Monitor for winners
8. **Payout** - Winners credited automatically
9. **Cleanup** - Lobby removed from memory

### Data Persistence
- ✅ Bets deducted immediately at race start
- ✅ Winnings added at race end
- ✅ All transactions logged
- ✅ Force save to Firebase
- ✅ Balance updates in real-time

### Race Limits
- **Minimum Bet:** 10 coins
- **Maximum Bettors:** Unlimited
- **Race Duration:** 2-3 minutes typical
- **Betting Window:** 30 seconds
- **Cooldown:** None (start new race anytime)

### One Bet Per Race
- Users can only bet **once per race**
- Cannot change bet after placing
- Can participate in multiple races simultaneously
- Each race is independent

## Example Race Flow

```
User A: /ratrace
→ Clicks "Start New Race"
→ Lobby opens with 6 rats (stats shown)

User B: Joins, bets 100 on Rat #3 (High speed: 95)
User A: Bets 200 on Rat #1 (Balanced: 75/80/70)
User C: Bets 50 on Rat #5 (High stamina: 90)

30 seconds pass...

Race starts!
Turn 1: Rat #3 moves 2, Rat #1 moves 1, Rat #5 moves 0
Turn 2: Rat #3 moves 2, Rat #1 moves 2, Rat #5 moves 1
Turn 3: Rat #4 FORFEITS! ❌
Turn 4: Rat #3 moves 2, Rat #1 moves 1, Rat #5 moves 2
...
Turn 8: Rat #3 FINISHES! 🥇
Turn 9: Rat #5 FINISHES! 🥈
Turn 10: Rat #1 FINISHES! 🥉

Results:
🥇 User B wins 500 (100 * 5x)
🥈 User C wins 100 (50 * 2x)
🥉 User A wins 300 (200 * 1.5x)

Everyone profits! 🎉
```

## Commands Reference

### Main Command
```
/ratrace
```
Opens the rat race interface with "Start New Race" button

### Betting Flow
1. Click "Start New Race" (Host only)
2. Select rat from dropdown
3. Enter bet amount in modal
4. Wait for race to start
5. Watch live race updates
6. Collect automatic payout

## Troubleshooting

### "Race Cancelled - No Bets"
- Happens if no one bets within 30 seconds
- Race lobby automatically closes
- No coins lost

### "You already placed a bet"
- Can only bet once per race
- Wait for race to finish
- Start a new race to bet again

### "Not enough coins"
- Check your balance with `/balance`
- Minimum bet is 10 coins
- Withdraw from bank if needed

### "This is not your trading interface"
- Each betting menu is user-specific
- Start your own race to bet
- Or join the current race's dropdown

## Advanced Features

### 🎯 Multiple Races
- Multiple races can run simultaneously
- Each race is independent
- Join multiple races at once
- Manage your risk across races

### 📊 Smart Betting
- Analyze rat stats before betting
- Look for high speed + high stamina combos
- Avoid rats with all low stats
- Watch for popular choices

### 🎰 Item Bonuses (Future)
- Lucky items may boost your rat
- Equipment could improve odds
- Special rat-specific items

## Code Architecture

### Classes
1. **RatStats** - Individual rat with randomized stats
2. **RatRaceLobby** - Manages single race instance
3. **RatRaceStartView** - Initial start button
4. **RatRaceBettingView** - Dropdown rat selection
5. **BetAmountModal** - Bet input modal

### Key Functions
- `_generate_rats()` - Creates 6 random rats
- `move_rats()` - Turn-based movement logic
- `forfeit_random_rat()` - Random forfeit system
- `get_track_visual()` - ASCII race track
- `calculate_payouts()` - Winner payouts
- `_start_race_sequence()` - Live race loop

## Balance & Economy

### Profitability
The rat race has a **positive expected value** (~142%) which makes it profitable for players on average. This is intentional to:
1. Encourage multiplayer participation
2. Reward strategic betting
3. Create excitement and engagement
4. Balance with other casino games

### Economy Impact
- Players gain more coins over time
- Encourages social betting
- Creates player interaction
- Drives economy circulation

---

## Quick Start Guide

**Want to race right now?**

1. Type `/ratrace`
2. Click "Start New Race"
3. Pick a rat with good stats
4. Bet 50-100 coins to start
5. Watch the magic happen! 🏁

**Pro Tip:** Look for rats with 80+ in all stats for best odds!

---

*Have fun racing! May the best rat win! 🐭🏆*
