# 🛒 SORABOT SHOP GUIDE

## How to Use the Shop

### 📖 Quick Start
1. Use `/shop` to open the shop menu
2. Click on a category button (Potions, Chests, or Equipment)
3. Use `/buy <item_name>` to purchase any item
4. Check `/inventory` to see what you own

### 💰 Available Items

#### 🧪 Potions (Temporary Boosts)
- **Luck Potion** (`luck_potion`) - 500 coins
  - Increases casino winnings by 20% for 1 hour
  - Use with `/use luck_potion`

- **Wealth Potion** (`wealth_potion`) - 1,000 coins
  - Get 2x coins from daily/weekly rewards for 24 hours
  - Use with `/use wealth_potion`

- **XP Boost** (`xp_boost`) - 750 coins
  - Earn 50% more coins from all activities for 2 hours
  - Use with `/use xp_boost`

#### 🎁 Chests (Random Rewards)
- **Small Chest** (`small_chest`) - 250 coins
  - Contains 100-500 random coins
  - Open with `/openchest small_chest`

- **Medium Chest** (`medium_chest`) - 750 coins
  - Contains 500-2,000 coins or a random item
  - Open with `/openchest medium_chest`

- **Large Chest** (`large_chest`) - 2,000 coins
  - Contains 2,000-10,000 coins or a rare item
  - Open with `/openchest large_chest`

#### ⚔️ Equipment (Permanent Bonuses)
- **Lucky Charm** (`lucky_charm`) - 3,000 coins
  - Permanent +10% casino winnings
  - Equip with `/equip lucky_charm`

- **Piggy Bank** (`piggy_bank`) - 2,500 coins
  - Permanent +15% daily/weekly rewards
  - Equip with `/equip piggy_bank`

- **Golden Horseshoe** (`golden_horseshoe`) - 5,000 coins
  - Permanent +25% rob success rate
  - Equip with `/equip golden_horseshoe`

### 📋 Essential Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/shop` | Open the shop menu | `/shop` |
| `/buy <item>` | Purchase an item | `/buy luck_potion` |
| `/inventory` | View your items | `/inventory` |
| `/use <item>` | Use a consumable | `/use luck_potion` |
| `/equip <item>` | Equip equipment | `/equip lucky_charm` |
| `/unequip <slot>` | Remove equipment | `/unequip slot1` |
| `/openchest <chest>` | Open a chest | `/openchest small_chest` |

### 💡 Tips

1. **Item Names**: Use the exact name (e.g., `luck_potion`, not "Luck Potion")
2. **Check Your Balance**: Your coin balance is shown in the shop
3. **Equipment Must Be Equipped**: Buy equipment and then use `/equip` to activate it
4. **Potions Are Temporary**: Use potions before doing activities for maximum benefit
5. **Chests Are Random**: Each chest has different reward ranges

### ❓ Troubleshooting

**"Item Not Found"**: Make sure you're using the exact item name (shown in parentheses above)

**"Not Enough Coins"**: Earn more coins with `/daily`, `/weekly`, `/work`, or casino games

**Can't see item effects?**: Equipment must be equipped with `/equip`, potions must be used with `/use`

### 🎮 Example Workflow

```
1. /shop                    # Browse available items
2. /buy luck_potion         # Purchase a luck potion (500 coins)
3. /inventory               # Confirm it's in your inventory
4. /use luck_potion         # Activate the 20% casino boost
5. /slots 100               # Play casino games with the boost active!
```

---

**Need more help?** Use `/help` to see all available commands!
