"""
Economy module: balance, daily, weekly, pay, request, rob, bank, profile
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import random
from .database import load_data, save_data

def deduct_debt(user_id, amount, server_data):
    """Deduct outstanding debt from earnings. Returns (remaining_amount, debt_paid)"""
    user_id = str(user_id)
    debt = server_data.get("debt", {}).get(user_id, 0)
    
    if debt <= 0:
        return amount, 0
    
    if amount >= debt:
        # Can pay off all debt
        remaining = amount - debt
        debt_paid = debt
        server_data.setdefault("debt", {})[user_id] = 0
    else:
        # Partial debt payment
        remaining = 0
        debt_paid = amount
        server_data.setdefault("debt", {})[user_id] = debt - amount
    
    return remaining, debt_paid

def auto_deduct_debt_from_balance(user_id, server_data):
    """
    Automatically deduct debt from user's wallet and bank balance.
    Called whenever checking balance or loading user data.
    Returns (debt_paid, message) tuple.
    """
    user_id = str(user_id)
    debt = server_data.get("debt", {}).get(user_id, 0)
    
    if debt <= 0:
        return 0, None
    
    wallet = server_data.get("coins", {}).get(user_id, 0)
    bank = server_data.get("bank", {}).get(user_id, 0)
    total_money = wallet + bank
    
    if total_money <= 0:
        return 0, None
    
    # Calculate how much debt we can pay
    debt_to_pay = min(debt, total_money)
    
    # Deduct from wallet first, then bank
    if wallet >= debt_to_pay:
        server_data.setdefault("coins", {})[user_id] = wallet - debt_to_pay
        remaining_wallet = wallet - debt_to_pay
        remaining_bank = bank
    else:
        # Take all from wallet, rest from bank
        remaining_from_bank = debt_to_pay - wallet
        server_data.setdefault("coins", {})[user_id] = 0
        server_data.setdefault("bank", {})[user_id] = bank - remaining_from_bank
        remaining_wallet = 0
        remaining_bank = bank - remaining_from_bank
    
    # Update debt
    new_debt = debt - debt_to_pay
    if new_debt > 0:
        server_data.setdefault("debt", {})[user_id] = new_debt
    else:
        server_data.setdefault("debt", {})[user_id] = 0
    
    # Create message
    message = (
        f"💳 **Debt Payment Auto-Deducted**\n"
        f"• Paid: {debt_to_pay:,} coins\n"
        f"• Remaining debt: {new_debt:,} coins\n"
        f"• New wallet: {remaining_wallet:,} coins\n"
        f"• New bank: {remaining_bank:,} coins"
    )
    
    return debt_to_pay, message

def deduct_combined_balance(user_id, amount, server_data):
    """
    Deduct from wallet first, then bank if wallet is insufficient.
    Returns (success: bool, message: str, from_wallet: int, from_bank: int)
    """
    user_id = str(user_id)
    wallet = server_data.get("coins", {}).get(user_id, 0)
    bank = server_data.get("bank", {}).get(user_id, 0)
    total = wallet + bank
    
    if total < amount:
        return False, f"❌ Insufficient funds! Need {amount:,} but have {total:,} total (💰 {wallet:,} + 🏦 {bank:,})", 0, 0
    
    # Deduct from wallet first
    if wallet >= amount:
        server_data.setdefault("coins", {})[user_id] = wallet - amount
        return True, f"💰 Paid {amount:,} from wallet", amount, 0
    else:
        # Take all from wallet, rest from bank
        remaining_needed = amount - wallet
        server_data.setdefault("coins", {})[user_id] = 0
        server_data.setdefault("bank", {})[user_id] = bank - remaining_needed
        return True, f"💰 Paid {wallet:,} from wallet + 🏦 {remaining_needed:,} from bank", wallet, remaining_needed

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
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, guild_id)
        
        # Auto-deduct debt from balance if they have money
        debt_paid, debt_message = auto_deduct_debt_from_balance(user_id, server_data)
        
        if debt_paid > 0:
            save_server_data(data, guild_id, server_data)
            await save_data(data)
        
        coins = server_data.get("coins", {}).get(user_id, 0)
        bank = server_data.get("bank", {}).get(user_id, 0)
        debt = server_data.get("debt", {}).get(user_id, 0)
        
        embed = discord.Embed(title=f"{interaction.user.display_name}'s Balance", color=0x00ff99)
        
        # Show debt payment notification if debt was paid
        if debt_paid > 0:
            embed.description = debt_message
            embed.color = 0xFFD700  # Gold color for debt payment
        
        embed.add_field(name="💰 Wallet", value=f"{coins:,} coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{bank:,} coins", inline=True)
        embed.add_field(name="💎 Total", value=f"{coins + bank:,} coins", inline=True)
        
        if debt > 0:
            embed.add_field(name="💳 Outstanding Debt", value=f"{debt:,} coins", inline=False)
            embed.set_footer(text="⚠️ Debt will be automatically deducted from your wallet and bank!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="daily", description="Claim your daily reward.")
    async def daily(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        now = datetime.utcnow()
        
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, guild_id)
        
        last_daily = server_data.get("last_daily", {}).get(user_id)
        daily_amount = server_data.get("_settings", {}).get("daily_reward", 150)
        
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
        equipped = server_data.get("equipment", {}).get(user_id, {})
        if equipped.get("accessory") == "piggy_bank":
            multiplier += 0.15
            bonuses.append("🐷 Piggy Bank: +15%")
        
        # Check consumable effects (wealth_potion gives +100%)
        consumable_effects = server_data.get("consumable_effects", {}).get(user_id, {})
        if "wealth_potion" in consumable_effects:
            multiplier += 1.0
            bonuses.append("💰 Wealth Potion: +100%")
            # Consume the potion
            consumable_effects.pop("wealth_potion")
            if not consumable_effects:
                server_data["consumable_effects"].pop(user_id, None)
        
        # Check xp_boost (+50% all earnings)
        if "xp_boost" in consumable_effects:
            multiplier += 0.5
            bonuses.append("⭐ XP Boost: +50%")
            # Consume the boost
            consumable_effects.pop("xp_boost")
            if not consumable_effects:
                server_data["consumable_effects"].pop(user_id, None)
        
        # Apply multiplier
        final_amount = int(daily_amount * multiplier)
        bonus_amount = final_amount - daily_amount
        
        # Deduct any outstanding debt
        remaining_amount, debt_paid = deduct_debt(user_id, final_amount, server_data)
        
        # Update balance
        coins = server_data.get("coins", {}).get(user_id, 0) + remaining_amount
        server_data.setdefault("coins", {})[user_id] = coins
        server_data.setdefault("last_daily", {})[user_id] = now.strftime("%Y-%m-%d")
        save_server_data(data, guild_id, server_data)
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
        
        if debt_paid > 0:
            embed.add_field(name="💳 Debt Paid", value=f"-{debt_paid:,} coins", inline=True)
            embed.add_field(name="Added to Wallet", value=f"+{remaining_amount:,} coins", inline=True)
            remaining_debt = data.get("debt", {}).get(user_id, 0)
            if remaining_debt > 0:
                embed.add_field(name="⚠️ Remaining Debt", value=f"{remaining_debt:,} coins", inline=True)
        
        embed.add_field(name="New Balance", value=f"💵 {coins:,} coins", inline=False)
        embed.set_footer(text="💡 Tip: Equip Piggy Bank or use Wealth Potion for bonuses!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="weekly", description="Claim your weekly reward.")
    async def weekly(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        now = datetime.utcnow()
        
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, guild_id)
        
        last_weekly = server_data.get("last_weekly", {}).get(user_id)
        weekly_amount = server_data.get("_settings", {}).get("weekly_reward", 1000)
        
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
        equipped = server_data.get("equipment", {}).get(user_id, {})
        if equipped.get("accessory") == "piggy_bank":
            multiplier += 0.15
            bonuses.append("🐷 Piggy Bank: +15%")
        
        # Check consumable effects (wealth_potion gives +100%)
        consumable_effects = server_data.get("consumable_effects", {}).get(user_id, {})
        if "wealth_potion" in consumable_effects:
            multiplier += 1.0
            bonuses.append("💰 Wealth Potion: +100%")
            # Consume the potion
            consumable_effects.pop("wealth_potion")
            if not consumable_effects:
                server_data["consumable_effects"].pop(user_id, None)
        
        # Check xp_boost (+50% all earnings)
        if "xp_boost" in consumable_effects:
            multiplier += 0.5
            bonuses.append("⭐ XP Boost: +50%")
            # Consume the boost
            consumable_effects.pop("xp_boost")
            if not consumable_effects:
                server_data["consumable_effects"].pop(user_id, None)
        
        # Apply multiplier
        final_amount = int(weekly_amount * multiplier)
        bonus_amount = final_amount - weekly_amount
        
        # Deduct any outstanding debt
        remaining_amount, debt_paid = deduct_debt(user_id, final_amount, server_data)
        
        # Update balance
        coins = server_data.get("coins", {}).get(user_id, 0) + remaining_amount
        server_data.setdefault("coins", {})[user_id] = coins
        server_data.setdefault("last_weekly", {})[user_id] = now.isoformat()
        
        save_server_data(data, guild_id, server_data)
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
        
        if debt_paid > 0:
            embed.add_field(name="💳 Debt Paid", value=f"-{debt_paid:,} coins", inline=True)
            embed.add_field(name="Added to Wallet", value=f"+{remaining_amount:,} coins", inline=True)
            remaining_debt = data.get("debt", {}).get(user_id, 0)
            if remaining_debt > 0:
                embed.add_field(name="⚠️ Remaining Debt", value=f"{remaining_debt:,} coins", inline=True)
        
        if debt_paid > 0:
            embed.add_field(name="💳 Debt Paid", value=f"-{debt_paid:,} coins", inline=True)
            embed.add_field(name="Added to Wallet", value=f"+{remaining_amount:,} coins", inline=True)
            remaining_debt = server_data.get("debt", {}).get(user_id, 0)
            if remaining_debt > 0:
                embed.add_field(name="⚠️ Remaining Debt", value=f"{remaining_debt:,} coins", inline=True)
        
        embed.add_field(name="New Balance", value=f"💵 {coins:,} coins", inline=False)
        embed.set_footer(text="💡 Tip: Equip Piggy Bank or use Wealth Potion for bonuses!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="bank", description="Access your bank account with deposit/withdraw options.")
    async def bank(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        data = await load_data()
        from .database import get_server_data
        server_data = get_server_data(data, guild_id)
        
        coins = server_data.get("coins", {}).get(user_id, 0)
        bank = server_data.get("bank", {}).get(user_id, 0)
        
        embed = discord.Embed(title="🏦 Bank Account", color=0x3498db)
        embed.add_field(name="💰 Wallet", value=f"{coins:,} coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{bank:,} coins", inline=True)
        embed.add_field(name="💎 Total", value=f"{coins + bank:,} coins", inline=True)
        embed.add_field(name="📈 Interest", value="0.5% per 24 hours", inline=True)
        embed.set_footer(text="Use the buttons below to deposit or withdraw coins")
        
        view = BankView(user_id, guild_id)
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
        guild_id = str(interaction.guild_id)
        
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, guild_id)
        
        sender_coins = server_data.get("coins", {}).get(sender_id, 0)
        
        if sender_coins < amount:
            await interaction.response.send_message(f"❌ Insufficient funds! You have {sender_coins:,} coins.", ephemeral=True)
            return
        
        # Transfer coins
        server_data.setdefault("coins", {})[sender_id] = sender_coins - amount
        server_data.setdefault("coins", {})[receiver_id] = server_data.get("coins", {}).get(receiver_id, 0) + amount
        
        save_server_data(data, guild_id, server_data)
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
        guild_id = str(interaction.guild_id)
        
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, guild_id)
        
        # Auto-deduct debt from balance if they have money
        debt_paid, debt_message = auto_deduct_debt_from_balance(user_id, server_data)
        
        if debt_paid > 0:
            save_server_data(data, guild_id, server_data)
            await save_data(data)
        
        coins = server_data.get("coins", {}).get(user_id, 0)
        bank = server_data.get("bank", {}).get(user_id, 0)
        total_wealth = coins + bank
        
        # Get equipped items
        equipped = server_data.get("equipped", {}).get(user_id, {})
        
        # Get guild info
        from .guild import get_user_guild
        guild_name = get_user_guild(user_id, server_data)
        if not guild_name:
            guild_name = "No Guild"
        
        # Get casino stats
        casino_stats = server_data.get("casino_stats", {}).get(user_id, {})
        games_played = casino_stats.get("games_played", 0)
        total_won = casino_stats.get("total_won", 0)
        total_lost = casino_stats.get("total_lost", 0)
        net_profit = total_won - total_lost
        
        # Get loan info
        loans = server_data.get("loans", {}).get(user_id, {})
        active_loan = loans.get("amount", 0) > 0
        
        embed = discord.Embed(title=f"👤 {interaction.user.display_name}'s Profile", color=0x9b59b6)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Show debt payment notification if debt was paid
        if debt_paid > 0:
            embed.description = f"✅ {debt_message}"
        
        embed.add_field(name="💰 Wallet", value=f"{coins:,} coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{bank:,} coins", inline=True)
        embed.add_field(name="💎 Total Wealth", value=f"{total_wealth:,} coins", inline=True)
        
        # Show debt/loan if exists
        user_debt = server_data.get("debt", {}).get(user_id, 0)
        if user_debt > 0:
            embed.add_field(name="⚠️ Debt", value=f"{user_debt:,} coins", inline=True)
        if active_loan:
            loan_amount = loans.get("amount", 0)
            embed.add_field(name="💳 Active Loan", value=f"{loan_amount:,} coins", inline=True)
        
        embed.add_field(name="�� Guild", value=guild_name, inline=True)
        
        # Casino stats
        if games_played > 0:
            profit_emoji = "📈" if net_profit >= 0 else "📉"
            embed.add_field(
                name="🎰 Casino Stats",
                value=f"Games: {games_played}\n{profit_emoji} Net: {net_profit:+,}",
                inline=True
            )
        
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
        guild_id = str(interaction.guild_id)
        
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, guild_id)
        
        # Check cooldown
        cooldowns = server_data.get("cooldowns", {})
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
        target_coins = server_data.get("coins", {}).get(target_id, 0)
        
        if target_coins < 100:
            await interaction.response.send_message(f"❌ {user.display_name} doesn't have enough coins to rob (minimum 100)!", ephemeral=True)
            return
        
        # Calculate success rate and stolen amount
        base_success_rate = data.get("config", {}).get("rob_success_rate", 0.3)
        max_steal_percent = data.get("config", {}).get("rob_max_steal_percent", 0.2)
        fine_percent = data.get("config", {}).get("rob_fine_percent", 0.1)
        
        # Check for equipped items that affect robbery
        equipped = server_data.get("equipment", {})
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
            server_data.setdefault("coins", {})[target_id] = target_coins - stolen_amount
            server_data.setdefault("coins", {})[robber_id] = server_data.get("coins", {}).get(robber_id, 0) + stolen_amount
            
            embed = discord.Embed(title="💰 Robbery Successful!", color=0x00ff00)
            embed.add_field(name="Target", value=user.mention, inline=True)
            embed.add_field(name="Stolen", value=f"{stolen_amount:,} coins", inline=True)
            embed.add_field(name="Success Rate", value=f"{success_rate*100:.1f}%", inline=True)
            if bonuses:
                embed.add_field(name="🎁 Active Bonuses", value="\n".join(bonuses), inline=False)
            
        else:
            # Failed!
            robber_coins = server_data.get("coins", {}).get(robber_id, 0)
            robber_bank = server_data.get("bank", {}).get(robber_id, 0)
            total_robber_money = robber_coins + robber_bank
            
            # Calculate fine (max 10% of target's coins)
            fine_amount = int(target_coins * fine_percent)
            
            # Take fine from wallet first, then bank if needed
            if total_robber_money >= fine_amount:
                if robber_coins >= fine_amount:
                    # Take from wallet only
                    server_data.setdefault("coins", {})[robber_id] = robber_coins - fine_amount
                    fine_from_wallet = fine_amount
                    fine_from_bank = 0
                else:
                    # Take all from wallet, rest from bank
                    fine_from_wallet = robber_coins
                    fine_from_bank = fine_amount - robber_coins
                    server_data.setdefault("coins", {})[robber_id] = 0
                    server_data.setdefault("bank", {})[robber_id] = robber_bank - fine_from_bank
                
                # Give fine to target's wallet
                server_data.setdefault("coins", {})[target_id] = target_coins + fine_amount
                
                embed = discord.Embed(title="🚔 Robbery Failed!", color=0xe74c3c)
                embed.add_field(name="Target", value=user.mention, inline=True)
                embed.add_field(name="Fine Paid", value=f"{fine_amount:,} coins", inline=True)
                if fine_from_bank > 0:
                    embed.add_field(name="💳 Taken From", value=f"Wallet: {fine_from_wallet:,}\nBank: {fine_from_bank:,}", inline=True)
            else:
                # Not enough money for full fine - take everything they have and add debt
                required_fine = int(target_coins * fine_percent)
                paid_amount = total_robber_money
                debt_amount = required_fine - paid_amount
                
                # Take all their money
                server_data.setdefault("coins", {})[robber_id] = 0
                server_data.setdefault("bank", {})[robber_id] = 0
                
                # Give what they can pay to target
                if paid_amount > 0:
                    server_data.setdefault("coins", {})[target_id] = target_coins + paid_amount
                
                # Add debt to robber
                server_data.setdefault("debt", {})[robber_id] = server_data.get("debt", {}).get(robber_id, 0) + debt_amount
                
                embed = discord.Embed(title="🚔 Robbery Failed!", color=0xe74c3c)
                embed.add_field(name="Target", value=user.mention, inline=True)
                embed.add_field(name="Fine Required", value=f"{required_fine:,} coins", inline=True)
                embed.add_field(name="Paid Now", value=f"{paid_amount:,} coins (all your money!)", inline=False)
                embed.add_field(name="💳 Outstanding Debt", value=f"{debt_amount:,} coins", inline=False)
                embed.set_footer(text="⚠️ Debt will be deducted from future earnings!")
            
            embed.add_field(name="Success Rate", value=f"{success_rate*100:.1f}%", inline=True)
            embed.description = "You were caught and had to pay a fine!"
        
        # Set cooldown
        server_data.setdefault("cooldowns", {}).setdefault("rob", {})[robber_id] = datetime.utcnow().isoformat()
        
        save_server_data(data, guild_id, server_data)
        await save_data(data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class BankView(discord.ui.View):
    def __init__(self, user_id, guild_id):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_id = guild_id

    @discord.ui.button(label="Deposit", style=discord.ButtonStyle.green, emoji="📥")
    async def deposit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your bank account!", ephemeral=True)
            return
        
        modal = BankModal("deposit", self.user_id, self.guild_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Withdraw", style=discord.ButtonStyle.red, emoji="📤")
    async def withdraw(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your bank account!", ephemeral=True)
            return
        
        modal = BankModal("withdraw", self.user_id, self.guild_id)
        await interaction.response.send_modal(modal)

class BankModal(discord.ui.Modal):
    def __init__(self, action, user_id, guild_id):
        super().__init__(title=f"{action.title()} Coins")
        self.action = action
        self.user_id = user_id
        self.guild_id = guild_id
        
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
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, self.guild_id)
        
        coins = server_data.get("coins", {}).get(self.user_id, 0)
        bank = server_data.get("bank", {}).get(self.user_id, 0)
        
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
        server_data.setdefault("coins", {})[self.user_id] = new_coins
        server_data.setdefault("bank", {})[self.user_id] = new_bank
        
        # Add transaction
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        tx = {"time": now, "type": "transfer", "amount": amount, "reason": f"Bank {self.action}"}
        server_data.setdefault("transactions", {}).setdefault(self.user_id, []).append(tx)
        
        save_server_data(data, self.guild_id, server_data)
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
