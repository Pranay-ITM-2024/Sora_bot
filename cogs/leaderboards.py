"""
Leaderboards and utility commands cog
"""

import discord
from discord.ext import commands
import random
import datetime
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import DataManager

class LeaderboardCommands(commands.Cog):
    """Leaderboard and utility commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='leaderboard')
    async def leaderboard(self, ctx):
        """Show richest players leaderboard"""
        data = await DataManager.load_data()
        
        # Calculate total wealth for each user
        user_wealth = []
        for user_id in set(data["coins"].keys()) | set(data["bank"].keys()):
            wallet = data["coins"].get(user_id, 0)
            bank = data["bank"].get(user_id, 0)
            total = wallet + bank
            
            # Add stock portfolio value
            holdings = data["stock_holdings"].get(user_id, {})
            stock_value = 0
            for stock_symbol, shares in holdings.items():
                current_price = data["stock_prices"].get(stock_symbol, 100)  # Default price
                stock_value += current_price * shares
            
            total += stock_value
            user_wealth.append((user_id, total))
        
        # Sort by total wealth
        user_wealth.sort(key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title="🏆 Richest Players",
            color=0xffd700
        )
        
        for i, (user_id, wealth) in enumerate(user_wealth[:15]):
            position = i + 1
            try:
                user = await self.bot.fetch_user(int(user_id))
                username = user.display_name
            except:
                username = f"Unknown User ({user_id})"
            
            medal = "🥇" if position == 1 else "🥈" if position == 2 else "🥉" if position == 3 else f"{position}."
            embed.add_field(
                name=f"{medal} {username}",
                value=f"{wealth:,} coins",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='helpme')
    async def helpme(self, ctx):
        """Show explanation of all commands & features"""
        embed = discord.Embed(
            title="🤖 SORABOT Help",
            description="A comprehensive Discord economy bot with casino, guilds, stock market, and more!",
            color=0x0099ff
        )
        
        # Core Economy
        economy_commands = """
        `/balance` - Check wallet & bank balance
        `/daily` - Claim daily reward (150 coins)
        `/weekly` - Claim weekly reward (1000 coins)
        `/pay <user> <amount>` - Send coins to another user
        `/request <user> <amount>` - Request money (with buttons)
        `/rob <user>` - Attempt to rob another user
        `/bank` - View bank and manage deposits/withdrawals
        `/profile` - Show user stats, guild, inventory, and equipped items
        """
        
        # Casino & Games
        casino_commands = """
        `/casino` - Opens the casino hub
        `/roulette <amount> <bet_type> [value]` - Play roulette
        `/slots <amount>` - Spin slot machine
        `/blackjack <amount>` - Play blackjack
        `/rat_race <amount> <rat_number>` - Bet on racing rats
        """
        
        # Loot & Inventory
        loot_commands = """
        `/openchest <chest_type>` - Open loot chests (common, rare, epic, legendary)
        `/inventory` - View owned items and equipped items
        `/useitem <item_name>` - Use a consumable item
        `/equip <item_name>` - Equip an item (passive effects)
        `/unequip <slot>` - Unequip an item back to inventory
        """
        
        # Shop System
        shop_commands = """
        `/shop` - Open interactive shop with categories
        `/buyitem <item_name>` - Buy an item from the shop
        """
        
        # Guild System
        guild_commands = """
        `/guild create <name>` - Create a guild
        `/guild join <name>` - Join a guild
        `/guild leave` - Leave a guild
        `/guild bank` - Manage guild bank (deposit/withdraw)
        `/guild members` - View guild members
        `/guild top` - Show leaderboard of richest guilds
        """
        
        # Stock Market
        market_commands = """
        `/market` - View stock market prices with trend lines
        `/buy <stock> <amount>` - Buy stock shares
        `/sell <stock> <amount>` - Sell stock shares
        `/portfolio` - View your stock portfolio
        """
        
        # Leaderboards
        leaderboard_commands = """
        `/leaderboard` - Show richest players
        `/guild top` - Show richest guilds
        """
        
        embed.add_field(name="💰 Core Economy", value=economy_commands, inline=False)
        embed.add_field(name="🎰 Casino & Games", value=casino_commands, inline=False)
        embed.add_field(name="🎁 Loot & Inventory", value=loot_commands, inline=False)
        embed.add_field(name="🛒 Shop System", value=shop_commands, inline=False)
        embed.add_field(name="🏰 Guild System", value=guild_commands, inline=False)
        embed.add_field(name="📈 Stock Market", value=market_commands, inline=False)
        embed.add_field(name="🏆 Leaderboards", value=leaderboard_commands, inline=False)
        
        embed.add_field(
            name="💡 Tips",
            value="• Use `/shop` to buy items that boost your chances\n"
                  "• Join a guild for bonus interest rates\n"
                  "• Check `/market` regularly for stock opportunities\n"
                  "• Open chests for random rewards and items\n"
                  "• Equip items for permanent passive effects",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LeaderboardCommands(bot))
