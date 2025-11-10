"""
Economy module: balance, daily, weekly, pay, request, rob, bank, profile
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import random
from .database import load_data, save_data

def get_rarity_color(rarity):
    """Get color for item rarity"""
    colors = {
        "Common": 0x9e9e9e,
        "Rare": 0x3f51b5,
        "Epic": 0x9c27b0,
        "Legendary": 0xff9800
    }
    return colors.get(rarity, 0x9e9e9e)

async def get_user_effects(user_id):
    """Get all active effects for a user (consumables + equipped items)"""
    data = await load_data()
    user_id = str(user_id)
    
    effects = {}
    
    # Get consumable effects
    consumable_effects = data.get("consumable_effects", {}).get(user_id, {})
    for effect_type, value in consumable_effects.items():
        effects[effect_type] = effects.get(effect_type, 0) + value
    
    # Get equipped item effects
    equipped = data.get("equipped", {}).get(user_id, {})
    shop_items = data.get("shop_items", {})
    
    for slot, item_key in equipped.items():
        # Find item in shop_items
        for category, items in shop_items.get("equipables", {}).items():
            if item_key in items:
                item_data = items[item_key]
                effect_type = item_data.get("effect")
                value = item_data.get("value", 0)
                if effect_type:
                    effects[effect_type] = effects.get(effect_type, 0) + value
                break
    
    return effects

async def use_consumable_effect(user_id, effect_type, value):
    """Add a temporary consumable effect for a user"""
    data = await load_data()
    user_id = str(user_id)
    
    data.setdefault("consumable_effects", {}).setdefault(user_id, {})[effect_type] = value
    await save_data(data)

async def consume_effect(user_id, effect_type):
    """Remove a consumable effect after use"""
    data = await load_data()
    user_id = str(user_id)
    
    if user_id in data.get("consumable_effects", {}):
        data["consumable_effects"][user_id].pop(effect_type, None)
        if not data["consumable_effects"][user_id]:
            del data["consumable_effects"][user_id]
    
    await save_data(data)

def get_default_data():
    """Get default data structure"""
    return {
        "coins": {},
        "bank": {},
        "last_daily": {},
        "last_weekly": {},
        "transactions": {},
        "active_games": {},
        "companies": {},
        "items": {},
        "inventories": {},
        "equipped": {},
        "guilds": {},
        "guild_members": {},
        "stock_holdings": {},
        "stock_prices": {
            "SORACOIN": 100.0,
            "LUCKYST": 50.0,
            "GUILDCO": 75.0,
            "MINING": 200.0
        },
        "consumable_effects": {},
        "loot_tables": {
            "common": {"coin_chance": 0.7, "item_chance": 0.25, "mimic_chance": 0.05},
            "rare": {"coin_chance": 0.5, "item_chance": 0.4, "mimic_chance": 0.1},
            "epic": {"coin_chance": 0.3, "item_chance": 0.6, "mimic_chance": 0.15},
            "legendary": {"coin_chance": 0.1, "item_chance": 0.8, "mimic_chance": 0.2}
        },
        "shop_items": {
            "consumables": {
                "lucky_potion": {"name": "Lucky Potion", "effect": "gambling_boost", "value": 0.2, "price": 150, "rarity": "Common"},
                "mega_lucky_potion": {"name": "Mega Lucky Potion", "effect": "gambling_boost", "value": 0.5, "price": 400, "rarity": "Rare"},
                "jackpot_booster": {"name": "Jackpot Booster", "effect": "payout_boost", "value": 0.1, "price": 200, "rarity": "Rare"},
                "robbers_mask": {"name": "Robber's Mask", "effect": "rob_boost", "value": 0.15, "price": 250, "rarity": "Rare"},
                "insurance_scroll": {"name": "Insurance Scroll", "effect": "insurance", "value": 0.5, "price": 300, "rarity": "Epic"},
                "mimic_repellent": {"name": "Mimic Repellent", "effect": "mimic_protection", "value": 1.0, "price": 500, "rarity": "Epic"}
            },
            "equipables": {
                "gamblers_charm": {"name": "Gambler's Charm", "slot": "trinket", "effect": "gambling_boost", "value": 0.05, "price": 400, "rarity": "Rare"},
                "golden_dice": {"name": "Golden Dice", "slot": "trinket", "effect": "slots_boost", "value": 0.1, "price": 600, "rarity": "Epic"},
                "security_dog": {"name": "Security Dog", "slot": "armor", "effect": "rob_protection", "value": 1, "price": 700, "rarity": "Epic"},
                "vault_key": {"name": "Vault Key", "slot": "bank_mod", "effect": "bank_interest", "value": 0.0025, "price": 800, "rarity": "Legendary"},
                "master_lockpick": {"name": "Master Lockpick", "slot": "weapon", "effect": "rob_boost", "value": 0.1, "price": 750, "rarity": "Epic"},
                "lucky_coin": {"name": "Lucky Coin", "slot": "trinket", "effect": "rat_race_boost", "value": 0.05, "price": 300, "rarity": "Rare"},
                "shadow_cloak": {"name": "Shadow Cloak", "slot": "armor", "effect": "stealth", "value": 0.15, "price": 600, "rarity": "Epic"}
            },
            "chests": {
                "common_chest": {"name": "Common Chest", "price": 100, "rarity": "Common"},
                "rare_chest": {"name": "Rare Chest", "price": 300, "rarity": "Rare"},
                "epic_chest": {"name": "Epic Chest", "price": 600, "rarity": "Epic"},
                "legendary_chest": {"name": "Legendary Chest", "price": 1200, "rarity": "Legendary"}
            }
        },
        "consumable_effects": {},
        "loot_tables": {},
        "config": {
            "min_bet": 10,
            "max_bet": 1000000,
            "daily_amount": 150,
            "weekly_amount": 1000,
            "interest_rate": 0.001,
            "interest_tick_minutes": 10,
            "market_tick_minutes": 10,
            "economy_frozen": False,
            "rob_cooldown_hours": 1,
            "rob_success_rate": 0.3,
            "rob_max_steal_percent": 0.2,
            "rob_fine_percent": 0.1
        },
        "bans": {},
        "cooldowns": {},
        "leaderboard_channel": None,
        "leaderboard_message": None,
        "_meta": {
            "last_interest_ts": None,
            "last_market_ts": None
        }
    }

async def get_balance(user_id):
    data = await load_data()
    coins = data.get("coins", {}).get(str(user_id), 0)
    bank = data.get("bank", {}).get(str(user_id), 0)
    return coins, bank

async def update_balance(user_id, coins=None, bank=None):
    data = await load_data()
    if coins is not None:
        data.setdefault("coins", {})[str(user_id)] = coins
    if bank is not None:
        data.setdefault("bank", {})[str(user_id)] = bank
    await save_data(data)

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Check your wallet and bank balance.")
    async def balance(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        coins, bank = await get_balance(user_id)
        embed = discord.Embed(title=f"{interaction.user.display_name}'s Balance", color=0x00ff99)
        embed.add_field(name="💰 Wallet", value=f"{coins:,} coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{bank:,} coins", inline=True)
        embed.add_field(name="💎 Total", value=f"{coins + bank:,} coins", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="daily", description="Claim your daily reward.")
    async def daily(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        now = datetime.utcnow()
        data = await load_data()
        
        last_daily = data.get("last_daily", {}).get(user_id)
        daily_amount = data.get("config", {}).get("daily_amount", 150)
        
        if last_daily:
            last_time = datetime.strptime(last_daily, "%Y-%m-%d")
            if last_time.date() == now.date():
                next_daily = (last_time + timedelta(days=1)).replace(hour=0, minute=0, second=0)
                time_left = next_daily - now
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                await interaction.response.send_message(
                    f"⏰ You have already claimed your daily reward today!\n"
                    f"Next daily available in: {time_left.days}d {hours}h {minutes}m", 
                    ephemeral=True
                )
                return
        
        # Check for item bonuses
        bonuses = []
        multiplier = 1.0
        
        # Check equipped items (piggy_bank gives +15%)
        equipped = data.get("equipment", {}).get(user_id, {})
        if equipped.get("accessory") == "piggy_bank":
            multiplier += 0.15
            bonuses.append("🐷 Piggy Bank: +15%")
        
        # Check consumable effects (wealth_potion gives +100%)
        consumable_effects = data.get("consumable_effects", {}).get(user_id, {})
        if "wealth_potion" in consumable_effects:
            multiplier += 1.0
            bonuses.append("💰 Wealth Potion: +100%")
            # Consume the potion
            consumable_effects.pop("wealth_potion")
            if not consumable_effects:
                data["consumable_effects"].pop(user_id, None)
        
        # Check xp_boost (+50% all earnings)
        if "xp_boost" in consumable_effects:
            multiplier += 0.5
            bonuses.append("⭐ XP Boost: +50%")
            # Consume the boost
            consumable_effects.pop("xp_boost")
            if not consumable_effects:
                data["consumable_effects"].pop(user_id, None)
        
        # Apply multiplier
        final_amount = int(daily_amount * multiplier)
        bonus_amount = final_amount - daily_amount
        
        # Update balance
        coins = data.get("coins", {}).get(user_id, 0) + final_amount
        data.setdefault("coins", {})[user_id] = coins
        data.setdefault("last_daily", {})[user_id] = now.strftime("%Y-%m-%d")
        
        # Add transaction
        tx = {
            "time": now.strftime("%Y-%m-%d %H:%M:%S UTC"), 
            "type": "credit", 
            "amount": final_amount, 
            "reason": "Daily claim" + (f" (+{bonus_amount} bonus)" if bonus_amount > 0 else "")
        }
        data.setdefault("transactions", {}).setdefault(user_id, []).append(tx)
        
        await save_data(data, force=True)
        
        embed = discord.Embed(title="💰 Daily Reward Claimed!", color=0x00ff99)
        embed.add_field(name="Base Amount", value=f"{daily_amount:,} coins", inline=True)
        if bonus_amount > 0:
            embed.add_field(name="Bonus", value=f"+{bonus_amount:,} coins", inline=True)
            embed.add_field(name="Total Received", value=f"**{final_amount:,} coins**", inline=True)
            if bonuses:
                embed.add_field(name="🎁 Active Bonuses", value="\n".join(bonuses), inline=False)
        else:
            embed.add_field(name="Total Received", value=f"{final_amount:,} coins", inline=True)
        embed.add_field(name="New Balance", value=f"💵 {coins:,} coins", inline=False)
        embed.set_footer(text="💡 Tip: Equip Piggy Bank or use Wealth Potion for bonuses!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="weekly", description="Claim your weekly reward.")
    async def weekly(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        now = datetime.utcnow()
        data = await load_data()
        
        last_weekly = data.get("last_weekly", {}).get(user_id)
        weekly_amount = data.get("config", {}).get("weekly_amount", 1000)
        
        if last_weekly:
            last_time = datetime.strptime(last_weekly, "%Y-%m-%dT%H:%M:%S.%f")
            if now - last_time < timedelta(days=7):
                next_time = last_time + timedelta(days=7)
                wait = next_time - now
                days = wait.days
                hours, remainder = divmod(wait.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                await interaction.response.send_message(
                    f"⏰ You can claim your next weekly reward in: {days}d {hours}h {minutes}m", 
                    ephemeral=True
                )
                return
        
        # Check for item bonuses
        bonuses = []
        multiplier = 1.0
        
        # Check equipped items (piggy_bank gives +15%)
        equipped = data.get("equipment", {}).get(user_id, {})
        if equipped.get("accessory") == "piggy_bank":
            multiplier += 0.15
            bonuses.append("🐷 Piggy Bank: +15%")
        
        # Check consumable effects (wealth_potion gives +100%)
        consumable_effects = data.get("consumable_effects", {}).get(user_id, {})
        if "wealth_potion" in consumable_effects:
            multiplier += 1.0
            bonuses.append("💰 Wealth Potion: +100%")
            # Consume the potion
            consumable_effects.pop("wealth_potion")
            if not consumable_effects:
                data["consumable_effects"].pop(user_id, None)
        
        # Check xp_boost (+50% all earnings)
        if "xp_boost" in consumable_effects:
            multiplier += 0.5
            bonuses.append("⭐ XP Boost: +50%")
            # Consume the boost
            consumable_effects.pop("xp_boost")
            if not consumable_effects:
                data["consumable_effects"].pop(user_id, None)
        
        # Apply multiplier
        final_amount = int(weekly_amount * multiplier)
        bonus_amount = final_amount - weekly_amount
        
        # Update balance
        coins = data.get("coins", {}).get(user_id, 0) + final_amount
        data.setdefault("coins", {})[user_id] = coins
        data.setdefault("last_weekly", {})[user_id] = now.isoformat()
        
        # Add transaction
        tx = {
            "time": now.strftime("%Y-%m-%d %H:%M:%S UTC"), 
            "type": "credit", 
            "amount": final_amount, 
            "reason": "Weekly claim" + (f" (+{bonus_amount} bonus)" if bonus_amount > 0 else "")
        }
        data.setdefault("transactions", {}).setdefault(user_id, []).append(tx)
        
        await save_data(data, force=True)
        
        embed = discord.Embed(title="🎁 Weekly Reward Claimed!", color=0x9d4edd)
        embed.add_field(name="Base Amount", value=f"{weekly_amount:,} coins", inline=True)
        if bonus_amount > 0:
            embed.add_field(name="Bonus", value=f"+{bonus_amount:,} coins", inline=True)
            embed.add_field(name="Total Received", value=f"**{final_amount:,} coins**", inline=True)
            if bonuses:
                embed.add_field(name="🎁 Active Bonuses", value="\n".join(bonuses), inline=False)
        else:
            embed.add_field(name="Total Received", value=f"{final_amount:,} coins", inline=True)
        embed.add_field(name="New Balance", value=f"💵 {coins:,} coins", inline=False)
        embed.set_footer(text="💡 Tip: Equip Piggy Bank or use Wealth Potion for bonuses!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="bank", description="Access your bank account with deposit/withdraw options.")
    async def bank(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        coins, bank = await get_balance(int(user_id))
        
        embed = discord.Embed(title="🏦 Bank Account", color=0x3498db)
        embed.add_field(name="💰 Wallet", value=f"{coins:,} coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{bank:,} coins", inline=True)
        embed.add_field(name="💎 Total", value=f"{coins + bank:,} coins", inline=True)
        embed.add_field(name="📈 Interest", value="0.1% per 10 minutes", inline=True)
        embed.set_footer(text="Use the buttons below to deposit or withdraw coins")
        
        view = BankView(user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="pay", description="Send coins to another user.")
    @app_commands.describe(user="User to send coins to", amount="Amount of coins to send")
    async def pay(self, interaction: discord.Interaction, user: discord.User, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return
        
        if user.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't pay yourself!", ephemeral=True)
            return
        
        sender_id = str(interaction.user.id)
        receiver_id = str(user.id)
        
        data = await load_data()
        sender_coins = data.get("coins", {}).get(sender_id, 0)
        
        if sender_coins < amount:
            await interaction.response.send_message(f"❌ Insufficient funds! You have {sender_coins:,} coins.", ephemeral=True)
            return
        
        # Transfer coins
        data.setdefault("coins", {})[sender_id] = sender_coins - amount
        data.setdefault("coins", {})[receiver_id] = data.get("coins", {}).get(receiver_id, 0) + amount
        
        # Add transactions
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        sender_tx = {"time": now, "type": "debit", "amount": amount, "reason": f"Payment to {user.display_name}"}
        receiver_tx = {"time": now, "type": "credit", "amount": amount, "reason": f"Payment from {interaction.user.display_name}"}
        
        data.setdefault("transactions", {}).setdefault(sender_id, []).append(sender_tx)
        data.setdefault("transactions", {}).setdefault(receiver_id, []).append(receiver_tx)
        
        await save_data(data)
        
        embed = discord.Embed(title="💸 Payment Sent", color=0x00ff00)
        embed.add_field(name="To", value=user.mention, inline=True)
        embed.add_field(name="Amount", value=f"{amount:,} coins", inline=True)
        embed.add_field(name="Your New Balance", value=f"{sender_coins - amount:,} coins", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="request", description="Request coins from another user.")
    @app_commands.describe(user="User to request coins from", amount="Amount of coins to request")
    async def request(self, interaction: discord.Interaction, user: discord.User, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return
        
        if user.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't request from yourself!", ephemeral=True)
            return
        
        embed = discord.Embed(title="💰 Payment Request", color=0xf39c12)
        embed.add_field(name="From", value=interaction.user.mention, inline=True)
        embed.add_field(name="To", value=user.mention, inline=True)
        embed.add_field(name="Amount", value=f"{amount:,} coins", inline=True)
        embed.description = f"{user.mention}, {interaction.user.display_name} is requesting {amount:,} coins from you."
        
        view = PaymentRequestView(interaction.user.id, user.id, amount)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="profile", description="View your stats, guild, and equipped items.")
    async def profile(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        coins = data.get("coins", {}).get(user_id, 0)
        bank = data.get("bank", {}).get(user_id, 0)
        total_wealth = coins + bank
        
        # Get transaction count
        transactions = data.get("transactions", {}).get(user_id, [])
        transaction_count = len(transactions)
        
        # Get equipped items
        equipped = data.get("equipped", {}).get(user_id, {})
        
        # Get guild info (placeholder)
        guild_name = "No Guild"
        
        embed = discord.Embed(title=f"👤 {interaction.user.display_name}'s Profile", color=0x9b59b6)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        embed.add_field(name="💰 Wealth", value=f"{total_wealth:,} coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{bank:,} coins", inline=True)
        embed.add_field(name="📊 Transactions", value=f"{transaction_count:,}", inline=True)
        
        embed.add_field(name="🏰 Guild", value=guild_name, inline=True)
        embed.add_field(name="🎲 Games Played", value="Coming Soon", inline=True)
        embed.add_field(name="🏆 Rank", value="#??? (TBD)", inline=True)
        
        if equipped:
            equipped_text = []
            for slot, item in equipped.items():
                equipped_text.append(f"**{slot.title()}**: {item}")
            embed.add_field(name="⚔️ Equipped Items", value="\n".join(equipped_text[:5]), inline=False)
        else:
            embed.add_field(name="⚔️ Equipped Items", value="No items equipped", inline=False)
        
        embed.set_footer(text="Use /inventory to manage your items")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="rob", description="Attempt to rob another user.")
    @app_commands.describe(user="User to attempt to rob")
    async def rob(self, interaction: discord.Interaction, user: discord.User):
        if user.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't rob yourself!", ephemeral=True)
            return
        
        if user.bot:
            await interaction.response.send_message("❌ You can't rob bots!", ephemeral=True)
            return
        
        robber_id = str(interaction.user.id)
        target_id = str(user.id)
        
        data = await load_data()
        
        # Check cooldown
        cooldowns = data.get("cooldowns", {})
        rob_cooldowns = cooldowns.get("rob", {})
        last_rob = rob_cooldowns.get(robber_id)
        
        if last_rob:
            last_time = datetime.fromisoformat(last_rob)
            cooldown_hours = data.get("config", {}).get("rob_cooldown_hours", 1)
            if datetime.utcnow() - last_time < timedelta(hours=cooldown_hours):
                time_left = last_time + timedelta(hours=cooldown_hours) - datetime.utcnow()
                minutes = int(time_left.total_seconds() / 60)
                await interaction.response.send_message(f"⏰ Rob cooldown! Try again in {minutes} minutes.", ephemeral=True)
                return
        
        # Get target's wallet
        target_coins = data.get("coins", {}).get(target_id, 0)
        
        if target_coins < 100:
            await interaction.response.send_message(f"❌ {user.display_name} doesn't have enough coins to rob (minimum 100)!", ephemeral=True)
            return
        
        # Calculate success rate and stolen amount
        base_success_rate = data.get("config", {}).get("rob_success_rate", 0.3)
        max_steal_percent = data.get("config", {}).get("rob_max_steal_percent", 0.2)
        fine_percent = data.get("config", {}).get("rob_fine_percent", 0.1)
        
        # Check for equipped items that affect robbery
        equipped = data.get("equipment", {})
        robber_equipped = equipped.get(robber_id, {})
        target_equipped = equipped.get(target_id, {})
        
        success_rate = base_success_rate
        bonuses = []
        
        # Robber bonuses
        if robber_equipped.get("accessory") == "golden_horseshoe":
            success_rate += 0.25  # +25% rob success rate
            bonuses.append("🌟 Golden Horseshoe: +25%")
        
        if "weapon" in robber_equipped and "lockpick" in robber_equipped["weapon"].lower():
            success_rate += 0.1
            bonuses.append("🔓 Lockpick: +10%")
        
        # Target protection
        if "armor" in target_equipped and "security" in target_equipped["armor"].lower():
            success_rate -= 0.5  # Security dog blocks robbery
        
        if "armor" in target_equipped and "cloak" in target_equipped["armor"].lower():
            success_rate -= 0.15  # Shadow cloak reduces targeting
        
        success_rate = max(0.05, min(0.95, success_rate))  # Clamp between 5% and 95%
        
        # Attempt robbery
        if random.random() < success_rate:
            # Success!
            max_steal = int(target_coins * max_steal_percent)
            stolen_amount = random.randint(50, max_steal)
            
            # Transfer coins
            data.setdefault("coins", {})[target_id] = target_coins - stolen_amount
            data.setdefault("coins", {})[robber_id] = data.get("coins", {}).get(robber_id, 0) + stolen_amount
            
            embed = discord.Embed(title="💰 Robbery Successful!", color=0x00ff00)
            embed.add_field(name="Target", value=user.mention, inline=True)
            embed.add_field(name="Stolen", value=f"{stolen_amount:,} coins", inline=True)
            embed.add_field(name="Success Rate", value=f"{success_rate*100:.1f}%", inline=True)
            if bonuses:
                embed.add_field(name="🎁 Active Bonuses", value="\n".join(bonuses), inline=False)
            
            # Add transactions
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            robber_tx = {"time": now, "type": "credit", "amount": stolen_amount, "reason": f"Robbed {user.display_name}"}
            target_tx = {"time": now, "type": "debit", "amount": stolen_amount, "reason": f"Robbed by {interaction.user.display_name}"}
            
            data.setdefault("transactions", {}).setdefault(robber_id, []).append(robber_tx)
            data.setdefault("transactions", {}).setdefault(target_id, []).append(target_tx)
            
        else:
            # Failed!
            robber_coins = data.get("coins", {}).get(robber_id, 0)
            fine_amount = min(robber_coins, int(target_coins * fine_percent))
            
            if fine_amount > 0:
                # Pay fine to target
                data.setdefault("coins", {})[robber_id] = robber_coins - fine_amount
                data.setdefault("coins", {})[target_id] = target_coins + fine_amount
            
            embed = discord.Embed(title="🚔 Robbery Failed!", color=0xe74c3c)
            embed.add_field(name="Target", value=user.mention, inline=True)
            embed.add_field(name="Fine Paid", value=f"{fine_amount:,} coins", inline=True)
            embed.add_field(name="Success Rate", value=f"{success_rate*100:.1f}%", inline=True)
            embed.description = "You were caught and had to pay a fine!"
            
            # Add transactions
            if fine_amount > 0:
                now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                robber_tx = {"time": now, "type": "debit", "amount": fine_amount, "reason": f"Failed robbery fine to {user.display_name}"}
                target_tx = {"time": now, "type": "credit", "amount": fine_amount, "reason": f"Robbery protection from {interaction.user.display_name}"}
                
                data.setdefault("transactions", {}).setdefault(robber_id, []).append(robber_tx)
                data.setdefault("transactions", {}).setdefault(target_id, []).append(target_tx)
        
        # Set cooldown
        data.setdefault("cooldowns", {}).setdefault("rob", {})[robber_id] = datetime.utcnow().isoformat()
        
        await save_data(data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class BankView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.button(label="Deposit", style=discord.ButtonStyle.green, emoji="📥")
    async def deposit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your bank account!", ephemeral=True)
            return
        
        modal = BankModal("deposit", self.user_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Withdraw", style=discord.ButtonStyle.red, emoji="📤")
    async def withdraw(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your bank account!", ephemeral=True)
            return
        
        modal = BankModal("withdraw", self.user_id)
        await interaction.response.send_modal(modal)

class BankModal(discord.ui.Modal):
    def __init__(self, action, user_id):
        super().__init__(title=f"{action.title()} Coins")
        self.action = action
        self.user_id = user_id
        
        self.amount = discord.ui.TextInput(
            label=f"Amount to {action}",
            placeholder="Enter amount of coins...",
            required=True,
            max_length=10
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount.value)
            if amount <= 0:
                await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
            return
        
        data = await load_data()
        coins = data.get("coins", {}).get(self.user_id, 0)
        bank = data.get("bank", {}).get(self.user_id, 0)
        
        if self.action == "deposit":
            if coins < amount:
                await interaction.response.send_message(f"❌ Insufficient wallet funds! You have {coins:,} coins.", ephemeral=True)
                return
            
            new_coins = coins - amount
            new_bank = bank + amount
            
            embed = discord.Embed(title="📥 Deposit Successful", color=0x00ff00)
            embed.add_field(name="Amount Deposited", value=f"{amount:,} coins", inline=True)
            embed.add_field(name="New Wallet", value=f"{new_coins:,} coins", inline=True)
            embed.add_field(name="New Bank", value=f"{new_bank:,} coins", inline=True)
            
        else:  # withdraw
            if bank < amount:
                await interaction.response.send_message(f"❌ Insufficient bank funds! You have {bank:,} coins in bank.", ephemeral=True)
                return
            
            new_coins = coins + amount
            new_bank = bank - amount
            
            embed = discord.Embed(title="📤 Withdrawal Successful", color=0xe74c3c)
            embed.add_field(name="Amount Withdrawn", value=f"{amount:,} coins", inline=True)
            embed.add_field(name="New Wallet", value=f"{new_coins:,} coins", inline=True)
            embed.add_field(name="New Bank", value=f"{new_bank:,} coins", inline=True)
        
        # Update data
        data.setdefault("coins", {})[self.user_id] = new_coins
        data.setdefault("bank", {})[self.user_id] = new_bank
        
        # Add transaction
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        tx = {"time": now, "type": "transfer", "amount": amount, "reason": f"Bank {self.action}"}
        data.setdefault("transactions", {}).setdefault(self.user_id, []).append(tx)
        
        await save_data(data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class PaymentRequestView(discord.ui.View):
    def __init__(self, requester_id, target_id, amount):
        super().__init__(timeout=300)
        self.requester_id = requester_id
        self.target_id = target_id
        self.amount = amount

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_id:
            await interaction.response.send_message("❌ This request is not for you!", ephemeral=True)
            return
        
        data = await load_data()
        payer_coins = data.get("coins", {}).get(str(self.target_id), 0)
        
        if payer_coins < self.amount:
            await interaction.response.send_message(f"❌ Insufficient funds! You have {payer_coins:,} coins.", ephemeral=True)
            return
        
        # Transfer coins
        data.setdefault("coins", {})[str(self.target_id)] = payer_coins - self.amount
        data.setdefault("coins", {})[str(self.requester_id)] = data.get("coins", {}).get(str(self.requester_id), 0) + self.amount
        
        # Add transactions
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        payer_tx = {"time": now, "type": "debit", "amount": self.amount, "reason": f"Payment request to user {self.requester_id}"}
        receiver_tx = {"time": now, "type": "credit", "amount": self.amount, "reason": f"Payment request from user {self.target_id}"}
        
        data.setdefault("transactions", {}).setdefault(str(self.target_id), []).append(payer_tx)
        data.setdefault("transactions", {}).setdefault(str(self.requester_id), []).append(receiver_tx)
        
        await save_data(data)
        
        embed = discord.Embed(title="✅ Payment Request Accepted", color=0x00ff00)
        embed.description = f"Successfully sent {self.amount:,} coins!"
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, emoji="❌")
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_id:
            await interaction.response.send_message("❌ This request is not for you!", ephemeral=True)
            return
        
        embed = discord.Embed(title="❌ Payment Request Declined", color=0xe74c3c)
        embed.description = "The payment request was declined."
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(Economy(bot))
