"""
Admin & Mod module: giveitem, set_loot_table, resetdata
"""
import discord
from discord import app_commands
from discord.ext import commands
import json
from pathlib import Path
from .database import load_data, save_data

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

    @app_commands.command(name="givecoin", description="Give coins to a user (admin only).")
    @app_commands.describe(user="User to give coins to", amount="Amount of coins to give", location="Where to add coins (wallet/bank)")
    async def givecoin(self, interaction: discord.Interaction, user: discord.User, amount: int, location: str = "wallet"):
        # Check if user is bot owner or has admin permissions
        if interaction.user.id != interaction.guild.owner_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return
        
        location = location.lower()
        if location not in ["wallet", "bank"]:
            await interaction.response.send_message("❌ Location must be either 'wallet' or 'bank'!", ephemeral=True)
            return
        
        guild_id = str(interaction.guild_id)
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, guild_id)
        
        user_id = str(user.id)
        
        # Add coins to the specified location
        if location == "wallet":
            current = server_data.get("coins", {}).get(user_id, 0)
            server_data.setdefault("coins", {})[user_id] = current + amount
        else:  # bank
            current = server_data.get("bank", {}).get(user_id, 0)
            server_data.setdefault("bank", {})[user_id] = current + amount
        
        save_server_data(data, guild_id, server_data)
        await save_data(data)
        
        embed = discord.Embed(title="💰 Coins Given", color=0x00ff00)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Recipient", value=user.mention, inline=True)
        embed.add_field(name="Amount", value=f"{amount:,} coins", inline=True)
        embed.add_field(name="Location", value=location.title(), inline=True)
        
        new_amount = server_data.get("coins" if location == "wallet" else "bank", {}).get(user_id, 0)
        embed.add_field(name=f"New {location.title()} Balance", value=f"{new_amount:,} coins", inline=False)
        embed.set_footer(text=f"Admin: {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="takecoin", description="Take coins from a user (admin only).")
    @app_commands.describe(user="User to take coins from", amount="Amount of coins to take", location="Where to take coins from (wallet/bank/both)")
    async def takecoin(self, interaction: discord.Interaction, user: discord.User, amount: int, location: str = "wallet"):
        # Check if user is bot owner or has admin permissions
        if interaction.user.id != interaction.guild.owner_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
            return
        
        location = location.lower()
        if location not in ["wallet", "bank", "both"]:
            await interaction.response.send_message("❌ Location must be 'wallet', 'bank', or 'both'!", ephemeral=True)
            return
        
        guild_id = str(interaction.guild_id)
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, guild_id)
        
        user_id = str(user.id)
        
        wallet = server_data.get("coins", {}).get(user_id, 0)
        bank = server_data.get("bank", {}).get(user_id, 0)
        
        taken_from = []
        total_taken = 0
        
        if location == "wallet":
            taken = min(amount, wallet)
            server_data.setdefault("coins", {})[user_id] = wallet - taken
            total_taken = taken
            taken_from.append(f"💰 Wallet: {taken:,}")
        elif location == "bank":
            taken = min(amount, bank)
            server_data.setdefault("bank", {})[user_id] = bank - taken
            total_taken = taken
            taken_from.append(f"🏦 Bank: {taken:,}")
        else:  # both
            # Take from wallet first, then bank
            if wallet >= amount:
                server_data.setdefault("coins", {})[user_id] = wallet - amount
                total_taken = amount
                taken_from.append(f"💰 Wallet: {amount:,}")
            else:
                # Take all from wallet, rest from bank
                remaining = amount - wallet
                taken_from_bank = min(remaining, bank)
                server_data.setdefault("coins", {})[user_id] = 0
                server_data.setdefault("bank", {})[user_id] = bank - taken_from_bank
                total_taken = wallet + taken_from_bank
                if wallet > 0:
                    taken_from.append(f"💰 Wallet: {wallet:,}")
                if taken_from_bank > 0:
                    taken_from.append(f"🏦 Bank: {taken_from_bank:,}")
        
        save_server_data(data, guild_id, server_data)
        await save_data(data)
        
        embed = discord.Embed(title="💸 Coins Taken", color=0xe74c3c)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Target", value=user.mention, inline=True)
        embed.add_field(name="Requested", value=f"{amount:,} coins", inline=True)
        embed.add_field(name="Actually Taken", value=f"{total_taken:,} coins", inline=True)
        
        if taken_from:
            embed.add_field(name="Taken From", value="\n".join(taken_from), inline=False)
        
        new_wallet = server_data.get("coins", {}).get(user_id, 0)
        new_bank = server_data.get("bank", {}).get(user_id, 0)
        embed.add_field(name="New Balances", value=f"💰 {new_wallet:,} | 🏦 {new_bank:,}", inline=False)
        
        if total_taken < amount:
            embed.set_footer(text=f"⚠️ User didn't have enough coins | Admin: {interaction.user.display_name}")
        else:
            embed.set_footer(text=f"Admin: {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="economy_status", description="Show economy system status (admin only).")
    async def economy_status(self, interaction: discord.Interaction):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        guild_id = str(interaction.guild_id)
        
        try:
            data = await load_data()
            from .database import get_server_data
            server_data = get_server_data(data, guild_id)
        except:
            server_data = {}
        
        # Calculate some basic stats for THIS server
        total_users = len(set(list(server_data.get("coins", {}).keys()) + list(server_data.get("bank", {}).keys())))
        total_coins = sum(server_data.get("coins", {}).values()) + sum(server_data.get("bank", {}).values())
        total_transactions = sum(len(txs) for txs in server_data.get("transactions", {}).values())
        
        embed = discord.Embed(title="📊 Economy Status (This Server)", color=0x2ecc71)
        embed.add_field(name="👥 Total Users", value=f"{total_users:,}", inline=True)
        embed.add_field(name="💰 Total Coins", value=f"{total_coins:,}", inline=True)
        embed.add_field(name="📋 Transactions", value=f"{total_transactions:,}", inline=True)
        embed.add_field(name="🏦 Bank Interest", value="Active", inline=True)
        embed.add_field(name="📈 Stock Market", value="Active", inline=True)
        embed.add_field(name="🎮 Games", value="Active", inline=True)
        
        embed.set_footer(text="Per-server economy system | Each Discord server has separate data")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
