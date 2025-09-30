"""
Admin and mod commands cog
"""

import discord
from discord.ext import commands
import random
import datetime
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import DataManager, CONSUMABLE_ITEMS, EQUIPABLE_ITEMS

class AdminCommands(commands.Cog):
    """Admin and mod commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def is_owner_or_admin(self, ctx):
        """Check if user is bot owner or has admin permissions"""
        return ctx.author.id == ctx.bot.owner_id or ctx.author.guild_permissions.administrator
    
    @commands.command(name='giveitem')
    async def giveitem(self, ctx, user: discord.Member, item_name: str, quantity: int = 1):
        """Give items to a user (Admin only)"""
        if not self.is_owner_or_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions!")
            return
        
        if quantity <= 0:
            await ctx.send("❌ Quantity must be positive!")
            return
        
        data = await DataManager.load_data()
        user_id = str(user.id)
        
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
        
        if not item_id or not item_data:
            await ctx.send("❌ Item not found!")
            return
        
        # Give the item
        if user_id not in data["inventories"]:
            data["inventories"][user_id] = {}
        
        data["inventories"][user_id][item_id] = data["inventories"][user_id].get(item_id, 0) + quantity
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="✅ Item Given!",
            description=f"**{ctx.author.display_name}** gave **{quantity}x {item_data['name']}** to **{user.display_name}**!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='set_loot_table')
    async def set_loot_table(self, ctx, chest_type: str, coin_chance: float, item_chance: float, mimic_chance: float):
        """Configure chest probabilities (Admin only)"""
        if not self.is_owner_or_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions!")
            return
        
        if not (0 <= coin_chance <= 1 and 0 <= item_chance <= 1 and 0 <= mimic_chance <= 1):
            await ctx.send("❌ All probabilities must be between 0 and 1!")
            return
        
        if abs(coin_chance + item_chance + mimic_chance - 1.0) > 0.01:
            await ctx.send("❌ Probabilities must sum to 1.0!")
            return
        
        data = await DataManager.load_data()
        
        if chest_type.lower() not in data.get("loot_tables", {}):
            data["loot_tables"][chest_type.lower()] = {}
        
        data["loot_tables"][chest_type.lower()] = {
            "coin_chance": coin_chance,
            "item_chance": item_chance,
            "mimic_chance": mimic_chance
        }
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="⚙️ Loot Table Updated!",
            description=f"Updated **{chest_type}** chest probabilities:\n"
                       f"• Coins: {coin_chance*100:.1f}%\n"
                       f"• Items: {item_chance*100:.1f}%\n"
                       f"• Mimics: {mimic_chance*100:.1f}%",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='resetdata')
    async def resetdata(self, ctx):
        """Reset bot economy data (Owner only)"""
        if ctx.author.id != ctx.bot.owner_id:
            await ctx.send("❌ This command is owner-only!")
            return
        
        # Confirmation required
        embed = discord.Embed(
            title="⚠️ DANGER: Reset Economy Data",
            description="This will **PERMANENTLY DELETE** all economy data including:\n"
                       "• All user balances and bank accounts\n"
                       "• All items and inventories\n"
                       "• All guilds and stock holdings\n"
                       "• All transaction history\n\n"
                       "**This action cannot be undone!**\n\n"
                       "React with ✅ to confirm or ❌ to cancel.",
            color=0xff0000
        )
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                # Reset data to default
                data = DataManager.get_default_data()
                await DataManager.save_data(data)
                
                embed = discord.Embed(
                    title="🗑️ Data Reset Complete",
                    description="All economy data has been reset to default values.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Data reset cancelled.")
                
        except asyncio.TimeoutError:
            await ctx.send("⏰ Reset confirmation timed out.")
    
    @commands.command(name='givecoins')
    async def givecoins(self, ctx, user: discord.Member, amount: int):
        """Give coins to a user (Admin only)"""
        if not self.is_owner_or_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions!")
            return
        
        if amount <= 0:
            await ctx.send("❌ Amount must be positive!")
            return
        
        data = await DataManager.load_data()
        user_id = str(user.id)
        
        # Give coins
        data["coins"][user_id] = data["coins"].get(user_id, 0) + amount
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="💰 Coins Given!",
            description=f"**{ctx.author.display_name}** gave **{amount:,} coins** to **{user.display_name}**!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='economy_status')
    async def economy_status(self, ctx):
        """Show economy system status (Admin only)"""
        if not self.is_owner_or_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions!")
            return
        
        data = await DataManager.load_data()
        
        # Calculate statistics
        total_users = len(set(data["coins"].keys()) | set(data["bank"].keys()))
        total_coins = sum(data["coins"].values())
        total_bank = sum(data["bank"].values())
        total_guilds = len(data["guilds"])
        total_stock_value = 0
        
        for stock_symbol, holdings in data.get("stock_holdings", {}).items():
            for user_id, shares in holdings.items():
                current_price = data["stock_prices"].get(stock_symbol, 100)
                total_stock_value += current_price * shares
        
        embed = discord.Embed(
            title="📊 Economy Status",
            color=0x0099ff
        )
        
        embed.add_field(name="👥 Total Users", value=f"{total_users:,}", inline=True)
        embed.add_field(name="💰 Total Wallet Coins", value=f"{total_coins:,}", inline=True)
        embed.add_field(name="🏦 Total Bank Coins", value=f"{total_bank:,}", inline=True)
        embed.add_field(name="🏰 Total Guilds", value=f"{total_guilds:,}", inline=True)
        embed.add_field(name="📈 Total Stock Value", value=f"{total_stock_value:,}", inline=True)
        embed.add_field(name="💎 Total Economy Value", value=f"{total_coins + total_bank + total_stock_value:,}", inline=True)
        
        embed.add_field(
            name="⚙️ System Status",
            value=f"**Economy Frozen:** {'Yes' if data['config']['economy_frozen'] else 'No'}\n"
                  f"**Interest Rate:** {data['config']['interest_rate']*100:.3f}%\n"
                  f"**Last Interest Tick:** {data['_meta'].get('last_interest_ts', 'Never')}\n"
                  f"**Last Market Tick:** {data['_meta'].get('last_market_ts', 'Never')}",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='freeze_economy')
    async def freeze_economy(self, ctx, freeze: bool):
        """Freeze/unfreeze the economy (Admin only)"""
        if not self.is_owner_or_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions!")
            return
        
        data = await DataManager.load_data()
        data["config"]["economy_frozen"] = freeze
        
        await DataManager.save_data(data)
        
        status = "frozen" if freeze else "unfrozen"
        embed = discord.Embed(
            title="🧊 Economy Status Changed",
            description=f"The economy has been **{status}**!",
            color=0xff0000 if freeze else 0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='ban_user')
    async def ban_user(self, ctx, user: discord.Member):
        """Ban a user from the economy (Admin only)"""
        if not self.is_owner_or_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions!")
            return
        
        data = await DataManager.load_data()
        user_id = str(user.id)
        
        if user_id in data.get("bans", {}):
            await ctx.send(f"❌ **{user.display_name}** is already banned!")
            return
        
        data["bans"][user_id] = {
            "banned_by": str(ctx.author.id),
            "banned_at": datetime.datetime.utcnow().isoformat(),
            "reason": "Admin ban"
        }
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="🚫 User Banned",
            description=f"**{user.display_name}** has been banned from the economy!",
            color=0xff0000
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='unban_user')
    async def unban_user(self, ctx, user: discord.Member):
        """Unban a user from the economy (Admin only)"""
        if not self.is_owner_or_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions!")
            return
        
        data = await DataManager.load_data()
        user_id = str(user.id)
        
        if user_id not in data.get("bans", {}):
            await ctx.send(f"❌ **{user.display_name}** is not banned!")
            return
        
        del data["bans"][user_id]
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="✅ User Unbanned",
            description=f"**{user.display_name}** has been unbanned from the economy!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
