# 🎰 SORABOT - Discord Economy Bot

A comprehensive Discord economy bot with casino games, guild system, stock market, loot system, and much more!

## 🌟 Features

### 💰 Core Economy
- **Daily & Weekly Rewards** - Claim coins every day/week
- **Bank System** - Earn interest on your deposits
- **Player Transactions** - Send money to other users
- **Request System** - Request money with interactive buttons
- **Robbery System** - Risk vs reward robbery mechanics
- **Transaction History** - Track all your financial activities

### 🎰 Casino & Games
- **Casino Hub** - Interactive casino with all games
- **Roulette** - Bet on numbers, colors, sections with multiple payout types
- **Slot Machines** - Spin for jackpots with different symbol combinations
- **Blackjack** - Beat the dealer to 21
- **Rat Racing** - Bet on racing rats with 5:1 payouts

### 🎁 Loot & Inventory System
- **Loot Chests** - 4 types with different rewards and mimic chances
- **Item Inventory** - Manage your consumable and equipable items
- **Item Effects** - Use consumables for temporary boosts
- **Equipment System** - Equip items for permanent passive effects

### 🛒 Shop System
- **Interactive Shop** - Browse items by category with dropdowns
- **Consumable Items** - Lucky potions, boosters, insurance scrolls
- **Equipable Items** - Gambler's charms, security dogs, vault keys
- **Guild Discounts** - Richest guild gets 10% shop discount

### 🏰 Guild System
- **Guild Creation** - Create and manage your own guild
- **Guild Banks** - Shared guild treasury
- **Guild Bonuses** - Extra interest rates for guild members
- **Guild Leaderboards** - Compete with other guilds

### 📈 Stock Market
- **4 Companies** - Invest in different stocks with varying volatility
- **Real-time Prices** - Prices update every 10 minutes
- **Market Pressure** - Your trades affect stock prices
- **Portfolio Tracking** - Monitor your investments

### 🏆 Leaderboards
- **Player Rankings** - See the richest players
- **Guild Rankings** - Top guilds by bank balance
- **Auto-updating** - Rankings update in real-time

### ⚙️ Admin & Mod Commands
- **Item Management** - Give items and coins to users
- **Economy Control** - Freeze/unfreeze economy
- **User Management** - Ban/unban users from economy
- **Data Management** - Reset economy data
- **Economy Status** - Monitor system health

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SORABOT
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Discord Bot**
   - Create a bot on [Discord Developer Portal](https://discord.com/developers/applications)
   - Copy the bot token
   - Invite bot to your server with necessary permissions

4. **Set environment variable**
   ```bash
   export DISCORD_TOKEN='your_bot_token_here'
   ```

5. **Run the bot**
   ```bash
   python start.py
   ```

## 📋 Requirements

- Python 3.8+
- discord.py 2.7.3+
- aiofiles for async file operations

## 🎮 Commands

### Core Economy
- `/balance` - Check wallet & bank balance
- `/daily` - Claim daily reward (150 coins)
- `/weekly` - Claim weekly reward (1000 coins)
- `/pay <user> <amount>` - Send coins to another user
- `/request <user> <amount>` - Request money (with buttons)
- `/rob <user>` - Attempt to rob another user
- `/bank` - View bank and manage deposits/withdrawals
- `/profile` - Show user stats, guild, inventory, and equipped items

### Casino & Games
- `/casino` - Opens the casino hub
- `/roulette <amount> <bet_type> [value]` - Play roulette
- `/slots <amount>` - Spin slot machine
- `/blackjack <amount>` - Play blackjack
- `/rat_race <amount> <rat_number>` - Bet on racing rats

### Loot & Inventory
- `/openchest <chest_type>` - Open loot chests (common, rare, epic, legendary)
- `/inventory` - View owned items and equipped items
- `/useitem <item_name>` - Use a consumable item
- `/equip <item_name>` - Equip an item (passive effects)
- `/unequip <slot>` - Unequip an item back to inventory

### Shop System
- `/shop` - Open interactive shop with categories
- `/buyitem <item_name>` - Buy an item from the shop

### Guild System
- `/guild create <name>` - Create a guild
- `/guild join <name>` - Join a guild
- `/guild leave` - Leave a guild
- `/guild bank` - Manage guild bank (deposit/withdraw)
- `/guild members` - View guild members
- `/guild top` - Show leaderboard of richest guilds

### Stock Market
- `/market` - View stock market prices with trend lines
- `/buy <stock> <amount>` - Buy stock shares
- `/sell <stock> <amount>` - Sell stock shares
- `/portfolio` - View your stock portfolio

### Leaderboards
- `/leaderboard` - Show richest players
- `/guild top` - Show richest guilds

### Admin Commands
- `/giveitem <user> <item> [qty]` - Give items to a user
- `/givecoins <user> <amount>` - Give coins to a user
- `/set_loot_table` - Configure chest probabilities
- `/resetdata` - Reset bot economy data (owner only)
- `/freeze_economy <true/false>` - Freeze/unfreeze economy
- `/ban_user <user>` - Ban a user from economy
- `/unban_user <user>` - Unban a user from economy
- `/economy_status` - Show economy system status

### Utility
- `/helpme` - Show explanation of all commands & features

## 🎁 Item System

### Consumable Items (Single-use)
| Item Name | Effect | Price | Rarity |
|-----------|--------|-------|--------|
| Lucky Potion | +20% gambling win chance | 150 | Common |
| Mega Lucky Potion | +50% gambling win chance | 400 | Rare |
| Jackpot Booster | +10% slots payout | 200 | Rare |
| Robber's Mask | +15% rob success | 250 | Rare |
| Insurance Scroll | 50% refund on lost bet | 300 | Epic |
| Mimic Repellent | Avoid one mimic | 500 | Epic |

### Equipable Items (Passive effects)
| Item Name | Slot | Effect | Price | Rarity |
|-----------|------|--------|-------|--------|
| Gambler's Charm | Trinket | +5% gambling win chance | 400 | Rare |
| Golden Dice | Trinket | +10% slots payout | 600 | Epic |
| Security Dog | Armor | Blocks 1 robbery attempt | 700 | Epic |
| Vault Key | Bank Mod | +0.25% bank interest | 800 | Legendary |
| Master Lockpick | Weapon | +10% rob success | 750 | Epic |
| Lucky Coin | Trinket | +5% rat race winnings | 300 | Rare |
| Shadow Cloak | Armor | -15% chance of being targeted | 600 | Epic |

### Loot Chests
| Chest Name | Coin Chance | Item Chance | Mimic Chance | Price |
|------------|-------------|-------------|--------------|-------|
| Common Chest | 70% | 25% | 5% | 100 |
| Rare Chest | 50% | 40% | 10% | 300 |
| Epic Chest | 30% | 60% | 15% | 750 |
| Legendary Chest | 10% | 80% | 20% | 2000 |

## 🏰 Guild Bonuses

- **Normal guild accounts** → +5% interest
- **Richest guild** → +10% interest and 10% shop discount

## 📈 Stock Market

| Stock | Company | Base Price | Volatility |
|-------|---------|------------|------------|
| SORACOIN | SORA Corporation | 100 | 10% |
| LUCKYST | Lucky Stars Casino | 50 | 15% |
| GUILDCO | Guild Commerce | 75 | 8% |
| MINING | Digital Mining Co | 200 | 20% |

## 🔧 Configuration

The bot automatically creates a `data.json` file with default settings. You can modify:

- Interest rates and tick intervals
- Daily/weekly reward amounts
- Game odds and payouts
- Robbery success rates and penalties
- Market volatility and update intervals

## 🛡️ Security Features

- **Anti-spam protection** with cooldowns
- **Economy freeze** capability for maintenance
- **User banning** system
- **Data validation** and error handling
- **Transaction logging** for audit trails

## 🤖 Bot Permissions

The bot needs the following Discord permissions:
- Send Messages
- Use Slash Commands
- Embed Links
- Add Reactions
- Read Message History

## 📝 License

MIT License - Feel free to modify and distribute!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## 📞 Support

For support, please open an issue on GitHub or contact the bot developer.

---

**Happy gaming! 🎮💰**