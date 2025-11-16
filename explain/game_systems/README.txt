===========================================
🎮 GAME SYSTEMS OVERVIEW
===========================================

Complete guide to all mini-games and game
systems in Sora Bot beyond heists.

===========================================
📄 FILES IN THIS FOLDER
===========================================

1. RAT_RACE_SYSTEM.md
   → Rat race betting mechanics
   → How races work
   → Betting strategies

===========================================
🎰 CASINO GAMES
===========================================

1. SLOTS (/slots <bet>)
   - 5-reel slot machine
   - Progressive jackpot system
   - Various winning combinations
   - Multipliers: 2x, 5x, 10x, 20x, JACKPOT

2. BLACKJACK (/blackjack <bet>)
   - Classic card game vs dealer
   - Hit, Stand, Double Down
   - Dealer stands on 17
   - Blackjack pays 3:2

3. COINFLIP (/coinflip <bet> <heads/tails>)
   - Simple 50/50 bet
   - Double your money or lose it
   - Quick gambling option

===========================================
🎰 SLOTS SYSTEM DETAILS
===========================================

MECHANICS:
- 5 reels spin independently
- Match symbols across payline
- Progressive jackpot grows with each spin
- Jackpot announced and auto-deleted after 5min

SYMBOLS & PAYOUTS:
🍒 Cherry: 2x (Most common)
🍋 Lemon: 5x (Common)
🍊 Orange: 10x (Uncommon)
💎 Diamond: 20x (Rare)
🎰 777: JACKPOT! (Very rare)

JACKPOT SYSTEM:
- Starts at 10,000 coins
- Grows by 5% of each bet
- Resets to 10,000 after win
- Server-wide (all players contribute)

BALANCE CHECK:
- Uses wallet + bank combined
- Wins go to wallet
- Can play with banked money

GEAR BONUSES:
- Slot Magnet: +8% payout
- Lucky Charm: +5% win chance
- Coin Doubler: 2x winnings (if equipped)

===========================================
🃏 BLACKJACK SYSTEM DETAILS
===========================================

MECHANICS:
- You vs dealer
- Goal: Get closer to 21 than dealer
- Dealer hits on 16, stands on 17
- Ace counts as 1 or 11

ACTIONS:
- HIT: Take another card
- STAND: Keep current hand
- DOUBLE DOWN: Double bet, get 1 card, end turn

PAYOUTS:
- Win: Get bet back + equal amount
- Blackjack (A + 10-value): 3:2 payout
- Push (tie): Get bet back
- Lose: Lose bet

STRATEGY:
- Hit on 11 or less (can't bust)
- Stand on 17+ (dealer likely worse)
- Double on 10 or 11 (good odds)
- Watch dealer's shown card

GEAR BONUSES:
- Card Counter: Shows hint of dealer's next card
- Lucky Charm: +5% better hands
- Casino boosters stack

===========================================
🪙 COINFLIP SYSTEM DETAILS
===========================================

MECHANICS:
- Choose heads or tails
- Flip the coin
- 50/50 chance

PAYOUTS:
- Correct guess: 2x your bet
- Wrong guess: Lose bet

STRATEGY:
- Pure luck, no skill involved
- Good for quick gambling
- Lower house edge than slots

GEAR BONUSES:
- Coin Doubler: 2x winnings (4x total!)
- Lucky Charm: Slight edge (55/45 odds)

===========================================
🐀 RAT RACE SYSTEM
===========================================

OVERVIEW:
- Betting event with 5 racing rats
- Each rat has unique stats
- Race simulated in real-time
- Winners get payouts based on odds

HOW TO PARTICIPATE:
1. Wait for /ratrace announcement
2. Use /bet <rat_number> <amount>
3. Watch the race progress
4. Winners announced automatically

RAT STATS:
- Each rat has: Speed, Stamina, Luck
- Stats affect win probability
- Better stats = lower odds (less payout)
- Weaker stats = higher odds (more payout)

BETTING ODDS:
Rat 1 (Strong): 2:1 odds
Rat 2 (Good): 3:1 odds
Rat 3 (Average): 4:1 odds
Rat 4 (Weak): 6:1 odds
Rat 5 (Longshot): 10:1 odds

EXAMPLE:
- Bet 1,000 on Rat 5
- Rat 5 wins!
- Payout: 1,000 × 10 = 10,000 coins

STRATEGY:
- Bet on favorites for safer wins
- Bet on underdogs for big payouts
- Diversify bets across multiple rats
- Check rat stats before betting

TIMING:
- Races announced by admins
- 2-minute betting window
- 30-second race duration
- Instant payout after race

===========================================
📈 MARKET SYSTEM
===========================================

OVERVIEW:
- Buy items when prices are low
- Sell when prices are high
- Prices fluctuate randomly
- Profit from speculation

MECHANICS:
- /market to view current prices
- Items have buy/sell prices
- Prices change every 10-30 minutes
- Hold items for better prices

ITEMS TRADED:
- Bread: 50-150 coins
- Fish: 100-300 coins
- Gold Bar: 500-1500 coins
- Diamond: 1000-3000 coins
- Rare Gem: 2000-5000 coins

STRATEGY:
- Buy during market dips
- Sell during market peaks
- Hold valuable items longer
- Don't be greedy (prices crash)

EXAMPLE:
1. Gold Bar price: 500 (LOW)
2. Buy 10 bars: -5,000 coins
3. Wait for price increase
4. Gold Bar price: 1,400 (HIGH)
5. Sell 10 bars: +14,000 coins
6. Profit: 9,000 coins!

===========================================
💰 ECONOMY SYSTEM
===========================================

WALLET:
- Holds active coins
- Used for purchases, bets, heists
- No interest earned
- Visible to others

BANK:
- Stores coins safely
- Earns 0.5% interest per 24 hours
- Protected from some penalties
- Use /deposit and /withdraw

DAILY REWARDS:
- /daily command (once per 24h)
- Amount configurable by admins
- Default: 100 coins
- Free money for activity

WEEKLY REWARDS:
- /weekly command (once per 7 days)
- Amount configurable by admins
- Default: 500 coins
- Bigger bonus for consistency

LOANS:
- /takeloan to borrow money
- Pay back with /payloan
- EMI system with interest
- Missed payments = penalties
- Can't overpay (refunds excess)

===========================================
🏛️ GUILD SYSTEM
===========================================

OVERVIEW:
- Create or join guilds with /guild
- Share a guild bank
- Earn interest together
- Track contributions

GUILD COMMANDS:
- /guild create <name>: Make a guild
- /guild join <name>: Join existing guild
- /guild leave: Leave guild
- /guild info: View guild stats
- /guild_deposit <amount>: Add to guild bank
- /guild_withdraw <amount>: Take from guild bank
- /guild_transfer <member>: Transfer ownership
- /gshare: View contribution shares

GUILD BANK:
- Shared by all members
- Earns 0.5% interest per 24 hours
- Interest distributed by contribution %
- Leader can manage

CONTRIBUTION TRACKING:
- Every deposit tracked per member
- Withdrawals reduce contribution
- Interest split proportionally
- Use /gshare to see shares

EXAMPLE:
Guild Bank: 100,000 coins
- Leader contributed 60,000 (60%)
- Member1 contributed 30,000 (30%)
- Member2 contributed 10,000 (10%)

Interest: 500 coins earned
- Leader gets 300 (60%)
- Member1 gets 150 (30%)
- Member2 gets 50 (10%)

===========================================
📊 PROFILE SYSTEM
===========================================

COMMAND: /profile [@user]
View your or another's stats:

DISPLAYED INFO:
- 💰 Wallet balance
- 🏦 Bank balance
- 🏛️ Guild membership
- 💳 Active loans
- 🎰 Casino stats (wins/losses)
- 🎯 Heist success rate
- 📅 Join date
- 🏆 Total earnings

===========================================
💡 EARNING STRATEGIES
===========================================

CONSERVATIVE (Low Risk):
1. /daily and /weekly religiously
2. Deposit everything in bank
3. Let interest compound
4. Occasional safe bets
5. Join guild for shared growth

BALANCED (Medium Risk):
1. Daily/weekly rewards
2. 50% in bank, 50% active
3. Small casino bets
4. Solo stealth heists
5. Rat race on favorites

AGGRESSIVE (High Risk):
1. All money in circulation
2. Big casino bets
3. Fast approach heists
4. Rat race underdogs
5. Market speculation

===========================================
🎯 GAME TIPS BY EXPERIENCE
===========================================

BEGINNER (0-50k):
- Focus on /daily and /weekly
- Small casino bets to learn
- Save for first heist gear
- Join a guild early
- Avoid loans

INTERMEDIATE (50k-500k):
- Mix of gambling and heisting
- Buy key equipment
- Take calculated risks
- Build casino win streak
- Small loans OK for gear

ADVANCED (500k+):
- Optimize every system
- Full gear loadout
- Big heists with team
- Smart market trading
- Guild leadership

===========================================
⚠️ COMMON MISTAKES
===========================================

❌ Keeping all money in wallet
   ✅ Deposit in bank for interest

❌ Betting entire balance at once
   ✅ Bet 10-20% max per game

❌ Ignoring daily/weekly rewards
   ✅ Claim every cooldown

❌ Heisting without gear
   ✅ Buy equipment first

❌ Taking huge loans early
   ✅ Only borrow what you can repay

❌ Opening legendary chests too early
   ✅ Build up funds first

❌ Solo heisting on fast approach
   ✅ Use stealth for better odds

===========================================
📚 COMMAND QUICK REFERENCE
===========================================

ECONOMY:
/balance, /daily, /weekly, /profile
/deposit, /withdraw, /pay

CASINO:
/slots <bet>
/blackjack <bet>
/coinflip <bet> <heads/tails>

GUILD:
/guild, /guild_deposit, /guild_withdraw
/gshare, /guild_transfer

HEIST:
/soloheist, /heist, /useitem, /inventory

MARKET:
/market, /buy, /sell

LOANS:
/takeloan, /payloan, /loaninfo

ADMIN:
/setdaily, /setweekly, /addcoins

===========================================

For detailed information on specific systems,
check the other folders in explain/

Good luck and have fun! 🎮💰
