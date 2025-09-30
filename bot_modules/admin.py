"""
Admin & Mod module: giveitem, set_loot_table, resetdata
"""
import discord
from discord import app_commands
from discord.ext import commands
import json
import aiofiles
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data.json"

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveitem", description="Give an item to a user (admin only).")
    @app_commands.describe(user="User to give item to", item="Item name", qty="Quantity to give")
    async def giveitem(self, interaction: discord.Interaction, user: discord.User, item: str, qty: int = 1):
        # Check if user is bot owner or has admin permissions
        if interaction.user.id != interaction.guild.owner_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        if qty <= 0:
            await interaction.response.send_message("❌ Quantity must be positive!", ephemeral=True)
            return
        
        embed = discord.Embed(title="🎁 Item Given", color=0x00ff00)
        embed.add_field(name="Recipient", value=user.mention, inline=True)
        embed.add_field(name="Item", value=item.title(), inline=True)
        embed.add_field(name="Quantity", value=str(qty), inline=True)
        embed.description = f"Successfully gave {qty}x {item} to {user.display_name}! (Placeholder - needs inventory integration)"
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="resetdata", description="Reset bot economy data (owner only).")
    async def resetdata(self, interaction: discord.Interaction):
        # Check if user is bot owner
        app_info = await self.bot.application_info()
        if interaction.user.id != app_info.owner.id:
            await interaction.response.send_message("❌ Only the bot owner can use this command!", ephemeral=True)
            return
        
        # Confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.confirmed = False
            
            @discord.ui.button(label="Confirm Reset", style=discord.ButtonStyle.danger, emoji="⚠️")
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.confirmed = True
                embed = discord.Embed(title="🔄 Data Reset", color=0xff0000)
                embed.description = "Economy data has been reset! (Placeholder - actual reset needs implementation)"
                await interaction.response.edit_message(embed=embed, view=None)
            
            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                embed = discord.Embed(title="❌ Reset Cancelled", color=0x95a5a6)
                embed.description = "Data reset was cancelled."
                await interaction.response.edit_message(embed=embed, view=None)
        
        embed = discord.Embed(title="⚠️ DANGER: Reset All Data", color=0xe74c3c)
        embed.description = "This will permanently delete ALL economy data including:\n" \
                           "• User balances\n• Inventories\n• Guilds\n• Transaction history\n• Stock holdings\n\n" \
                           "**This action cannot be undone!**"
        embed.set_footer(text="Are you absolutely sure?")
        
        view = ConfirmView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="set_loot_table", description="Configure chest loot probabilities (admin only).")
    @app_commands.describe(chest_type="Chest type (common, rare, epic, legendary)")
    async def set_loot_table(self, interaction: discord.Interaction, chest_type: str):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        valid_types = ["common", "rare", "epic", "legendary"]
        if chest_type.lower() not in valid_types:
            await interaction.response.send_message(f"❌ Invalid chest type! Choose from: {', '.join(valid_types)}", ephemeral=True)
            return
        
        embed = discord.Embed(title="⚙️ Loot Table Configuration", color=0x3498db)
        embed.add_field(name="Chest Type", value=chest_type.title(), inline=True)
        embed.description = f"Loot table configuration for {chest_type} chests (Placeholder - needs implementation)"
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="economy_status", description="Show economy system status (admin only).")
    async def economy_status(self, interaction: discord.Interaction):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        try:
            async with aiofiles.open(DATA_PATH, 'r') as f:
                data = json.loads(await f.read())
        except:
            data = {}
        
        # Calculate some basic stats
        total_users = len(set(list(data.get("coins", {}).keys()) + list(data.get("bank", {}).keys())))
        total_coins = sum(data.get("coins", {}).values()) + sum(data.get("bank", {}).values())
        total_transactions = sum(len(txs) for txs in data.get("transactions", {}).values())
        
        embed = discord.Embed(title="📊 Economy Status", color=0x2ecc71)
        embed.add_field(name="👥 Total Users", value=f"{total_users:,}", inline=True)
        embed.add_field(name="💰 Total Coins", value=f"{total_coins:,}", inline=True)
        embed.add_field(name="📋 Transactions", value=f"{total_transactions:,}", inline=True)
        embed.add_field(name="🏦 Bank Interest", value="Active", inline=True)
        embed.add_field(name="📈 Stock Market", value="Active", inline=True)
        embed.add_field(name="🎮 Games", value="Active", inline=True)
        
        embed.set_footer(text="Economy system operational")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
