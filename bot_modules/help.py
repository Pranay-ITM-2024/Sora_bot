"""
Help/Utility module: helpme
"""
import discord
from discord import app_commands
from discord.ext import commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="helpme", description="Show all bot commands and features.")
    async def helpme(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 SORABOT Help", color=0x00bfff)
        embed.description = "A comprehensive economy bot with casino, guilds, stock market, shopping, and advanced inventory system!"
        
        embed.add_field(
            name="💰 Core Economy", 
            value="`/balance` - Check wallet & bank balance\n"
                  "`/daily` - Claim daily reward (150 coins)\n"
                  "`/weekly` - Claim weekly reward (1000 coins)\n"
                  "`/pay` - Send coins to another user\n"
                  "`/request` - Request coins from user\n"
                  "`/rob` - Attempt to rob user (1hr cooldown)\n"
                  "`/bank` - Deposit/withdraw from bank\n"
                  "`/profile` - View detailed user statistics", 
            inline=False
        )
        
        embed.add_field(
            name="🎰 Casino Games", 
            value="`/casino` - Interactive casino hub with:\n"
                  "• **Slots** - 3-reel slot machine (2x-50x payouts)\n"
                  "• **Coinflip** - 50/50 chance, double your bet\n"
                  "• **Blackjack** - Classic card game vs dealer\n"
                  "• **Rat Race** - 🏁 MULTIPLAYER live racing!\n"
                  "  → Random rat stats, live updates, 30s betting\n"
                  "  → Multiple players bet on same race\n"
                  "  → 5x/2x/1.5x payouts for top 3!\n"
                  "*Item effects boost your gambling luck!*", 
            inline=False
        )
        
        embed.add_field(
            name="🛒 Shop & Items", 
            value="`/shop` - Browse with dropdown menus (no typing!)\n"
                  "• Click category → Select from dropdown → Buy\n"
                  "`/inventory` - View your items\n"
                  "`/use <item>` - Use consumables\n"
                  "`/equip <item>` - Equip gear for bonuses\n"
                  "`/openchest <chest>` - Open chests for rewards", 
            inline=False
        )
        
        embed.add_field(
            name="🎒 Inventory & Equipment", 
            value="`/inventory` - View all owned items\n"
                  "`/equip` - Equip gear for bonuses\n"
                  "`/unequip` - Remove equipped items\n"
                  "`/use` - Consume items for effects\n"
                  "`/openchest` - Open loot chests\n"
                  "**Equipment Slots:** Accessory, Tool, Armor, Pet", 
            inline=False
        )
        
        embed.add_field(
            name="🏰 Guild System", 
            value="`/guild` - Complete guild management:\n"
                  "• Create/join/leave guilds\n"
                  "• Shared guild bank system\n"
                  "• Member roles & permissions\n"
                  "• Guild bonuses: shop discounts, bank interest\n"
                  "• Invite system with codes", 
            inline=False
        )
        
        embed.add_field(
            name="📈 Stock Market", 
            value="`/stocks` - Interactive stock trading:\n"
                  "• 8 unique stocks with live prices\n"
                  "• Buy/sell with trading interface\n"
                  "• Portfolio tracking & net worth\n"
                  "• Market volatility & price history\n"
                  "**Stocks:** SORACOIN, TECHNO, MEMES, CRYPTO, etc.", 
            inline=False
        )
        
        embed.add_field(
            name="🏆 Leaderboards", 
            value="`/leaderboard` - Multiple ranking categories:\n"
                  "• **Coins** - Wallet rankings\n"
                  "• **Bank** - Savings rankings\n"
                  "• **Net Worth** - Total wealth (coins+bank+stocks)\n"
                  "• **Guild Bank** - Guild wealth rankings\n"
                  "• **Slots Wins** - Casino success\n"
                  "• **Stock Value** - Portfolio rankings", 
            inline=False
        )
        
        embed.add_field(
            name="🛠️ Admin Tools", 
            value="`/admin` - Admin command hub:\n"
                  "• Give/take coins and items\n"
                  "• Economy freeze/unfreeze\n"
                  "• User data management\n"
                  "• Transaction monitoring\n"
                  "*(Admin permissions required)*", 
            inline=True
        )
        
        embed.add_field(
            name="💡 Pro Tips", 
            value="• Equip items for permanent bonuses\n"
                  "• Join a guild for shop discounts\n"
                  "• Use consumables before gambling\n"
                  "• Diversify your stock portfolio\n"
                  "• Check leaderboards for goals", 
            inline=True
        )
        
        embed.add_field(
            name="🎮 Features", 
            value="• **28 Unique Items** with special effects\n"
                  "• **Interactive UI** with buttons & dropdowns\n"
                  "• **Cross-system Integration** (items affect gambling)\n"
                  "• **Real-time Data** with atomic operations\n"
                  "• **Advanced Economy** with inflation protection", 
            inline=True
        )
        
        embed.set_footer(text="🚀 Use slash commands (/) to interact with SORABOT! All systems are fully integrated.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
