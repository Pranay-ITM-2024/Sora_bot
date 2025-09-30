"""
Shop system cog
"""

import discord
from discord.ext import commands
import random
import datetime
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import DataManager, CONSUMABLE_ITEMS, EQUIPABLE_ITEMS, CHEST_TYPES

class ShopCommands(commands.Cog):
    """Shop system commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='shop')
    async def shop(self, ctx):
        """Open interactive shop with categories"""
        embed = discord.Embed(
            title="🛒 SORA Shop",
            description="Welcome to the SORA Shop! Choose a category to browse:",
            color=0x00ff00
        )
        
        view = ShopView(ctx.author)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='buyitem')
    async def buyitem(self, ctx, item_name: str):
        """Buy an item from the shop"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Find item in consumables
        item_id = None
        item_data = None
        
        for item_key, item_info in CONSUMABLE_ITEMS.items():
            if item_info["name"].lower() == item_name.lower():
                item_id = item_key
                item_data = item_info
                break
        
        # Find item in equipables
        if not item_id:
            for item_key, item_info in EQUIPABLE_ITEMS.items():
                if item_info["name"].lower() == item_name.lower():
                    item_id = item_key
                    item_data = item_info
                    break
        
        # Find item in chests
        if not item_id:
            for chest_key, chest_info in CHEST_TYPES.items():
                if chest_info["name"].lower() == item_name.lower():
                    item_id = f"chest_{chest_key}"
                    item_data = {"name": chest_info["name"], "price": chest_info["price"], "type": "chest"}
                    break
        
        if not item_id or not item_data:
            await ctx.send("❌ Item not found in shop!")
            return
        
        # Check if user has enough coins
        price = item_data["price"]
        
        # Apply guild discount if user is in richest guild
        guild_discount = 0
        user_guild = None
        for guild_id, guild_data in data["guilds"].items():
            if user_id in guild_data.get("members", []):
                user_guild = guild_id
                break
        
        if user_guild:
            # Check if this guild is the richest
            guild_bank = data["guilds"][user_guild].get("bank", 0)
            is_richest = True
            for other_guild_id, other_guild_data in data["guilds"].items():
                if other_guild_id != user_guild and other_guild_data.get("bank", 0) > guild_bank:
                    is_richest = False
                    break
            
            if is_richest:
                guild_discount = 0.1  # 10% discount
        
        final_price = int(price * (1 - guild_discount))
        
        if data["coins"].get(user_id, 0) < final_price:
            await ctx.send(f"❌ You need {final_price:,} coins to buy this item!")
            return
        
        # Buy the item
        data["coins"][user_id] -= final_price
        
        if item_data["type"] == "chest":
            # For chests, add directly to inventory as a consumable
            if user_id not in data["inventories"]:
                data["inventories"][user_id] = {}
            data["inventories"][user_id][item_id] = data["inventories"][user_id].get(item_id, 0) + 1
        else:
            # For regular items, add to inventory
            if user_id not in data["inventories"]:
                data["inventories"][user_id] = {}
            data["inventories"][user_id][item_id] = data["inventories"][user_id].get(item_id, 0) + 1
        
        await DataManager.save_data(data)
        
        discount_text = f" (10% guild discount applied!)" if guild_discount > 0 else ""
        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"Bought **{item_data['name']}** for **{final_price:,} coins**{discount_text}",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

class ShopView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user
    
    @discord.ui.select(
        placeholder="Choose a category...",
        options=[
            discord.SelectOption(label="Consumables", description="Single-use items with temporary effects", value="consumables"),
            discord.SelectOption(label="Equipable Items", description="Items with passive effects", value="equipable"),
            discord.SelectOption(label="Loot Chests", description="Mystery boxes with random rewards", value="chests")
        ]
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This is not your shop!", ephemeral=True)
            return
        
        category = select.values[0]
        
        if category == "consumables":
            await self.show_consumables(interaction)
        elif category == "equipable":
            await self.show_equipables(interaction)
        elif category == "chests":
            await self.show_chests(interaction)
    
    async def show_consumables(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🧪 Consumables Shop",
            description="Single-use items with temporary effects:",
            color=0x00ff00
        )
        
        for item_id, item_data in CONSUMABLE_ITEMS.items():
            effect_desc = self.get_consumable_effect_description(item_data)
            embed.add_field(
                name=f"{item_data['name']} - {item_data['price']:,} coins",
                value=f"**Effect:** {effect_desc}\n**Rarity:** {item_data['rarity']}",
                inline=True
            )
        
        embed.add_field(
            name="How to Buy",
            value="Use `/buyitem <item_name>` to purchase an item!",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def show_equipables(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚔️ Equipable Items Shop",
            description="Items with passive effects:",
            color=0x0099ff
        )
        
        # Group by slot
        slots = {}
        for item_id, item_data in EQUIPABLE_ITEMS.items():
            slot = item_data["slot"]
            if slot not in slots:
                slots[slot] = []
            slots[slot].append((item_id, item_data))
        
        for slot, items in slots.items():
            slot_text = ""
            for item_id, item_data in items:
                effect_desc = self.get_equipable_effect_description(item_data)
                slot_text += f"• **{item_data['name']}** - {item_data['price']:,} coins\n  {effect_desc} ({item_data['rarity']})\n"
            
            embed.add_field(
                name=f"{slot.title()} Slot",
                value=slot_text,
                inline=False
            )
        
        embed.add_field(
            name="How to Buy",
            value="Use `/buyitem <item_name>` to purchase an item!",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    async def show_chests(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎁 Loot Chests Shop",
            description="Mystery boxes with random rewards:",
            color=0xffd700
        )
        
        for chest_type, chest_data in CHEST_TYPES.items():
            embed.add_field(
                name=f"{chest_data['name']} - {chest_data['price']:,} coins",
                value=f"**Coin Chance:** {chest_data['coin_chance']*100:.0f}%\n"
                      f"**Item Chance:** {chest_data['item_chance']*100:.0f}%\n"
                      f"**Mimic Chance:** {chest_data['mimic_chance']*100:.0f}%",
                inline=True
            )
        
        embed.add_field(
            name="How to Buy & Use",
            value="Use `/buyitem <chest_name>` to purchase, then `/openchest <type>` to open!",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    def get_consumable_effect_description(self, item_data):
        """Get description of consumable effect"""
        effect = item_data["effect"]
        value = item_data["value"]
        
        if effect == "gambling_boost":
            return f"+{value*100:.0f}% chance to win next casino game"
        elif effect == "payout_boost":
            return f"+{value*100:.0f}% payout on next slots spin"
        elif effect == "rob_boost":
            return f"+{value*100:.0f}% success on next robbery"
        elif effect == "insurance":
            return f"Refunds {value*100:.0f}% of next lost bet"
        elif effect == "mimic_protection":
            return f"Avoid one mimic event when opening chest"
        else:
            return "Unknown effect"
    
    def get_equipable_effect_description(self, item_data):
        """Get description of equipable effect"""
        effect = item_data["effect"]
        value = item_data["value"]
        
        if effect == "gambling_boost":
            return f"+{value*100:.0f}% gambling win chance"
        elif effect == "slots_boost":
            return f"+{value*100:.0f}% slots payout"
        elif effect == "rob_protection":
            return f"Blocks {int(value)} robbery attempt"
        elif effect == "bank_interest":
            return f"+{value*100:.2f}% bank interest"
        elif effect == "rob_boost":
            return f"+{value*100:.0f}% rob success chance"
        elif effect == "rat_race_boost":
            return f"+{value*100:.0f}% rat race winnings"
        elif effect == "stealth":
            return f"-{value*100:.0f}% chance of being targeted"
        else:
            return "Unknown effect"

async def setup(bot):
    await bot.add_cog(ShopCommands(bot))
