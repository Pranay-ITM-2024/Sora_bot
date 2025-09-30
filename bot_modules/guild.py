"""
Guild module: comprehensive guild management with slash commands
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from .database import load_data, save_data

def get_user_guild(user_id, data):
    """Get the guild a user belongs to"""
    user_id = str(user_id)
    for guild_name, members in data.get("guild_members", {}).items():
        if user_id in members:
            return guild_name
    return None

def get_guild_role(user_id, guild_name, data):
    """Get user's role in guild"""
    user_id = str(user_id)
    guild_data = data.get("guilds", {}).get(guild_name, {})
    
    if user_id == guild_data.get("owner"):
        return "Owner"
    elif user_id in guild_data.get("moderators", []):
        return "Moderator"
    elif user_id in data.get("guild_members", {}).get(guild_name, []):
        return "Member"
    return None

class GuildBankView(discord.ui.View):
    def __init__(self, guild_name, user_id):
        super().__init__(timeout=300)
        self.guild_name = guild_name
        self.user_id = user_id

    @discord.ui.button(label="💰 Deposit", style=discord.ButtonStyle.green, emoji="💰")
    async def deposit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your guild interface!", ephemeral=True)
            return
        await interaction.response.send_modal(DepositModal(self.guild_name))

    @discord.ui.button(label="💸 Withdraw", style=discord.ButtonStyle.red, emoji="💸")
    async def withdraw_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This isn't your guild interface!", ephemeral=True)
            return
        await interaction.response.send_modal(WithdrawModal(self.guild_name))

    @discord.ui.button(label="ℹ️ Guild Info", style=discord.ButtonStyle.secondary, emoji="ℹ️")
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await load_data()
        guild_info = data.get("guilds", {}).get(self.guild_name, {})
        members = data.get("guild_members", {}).get(self.guild_name, [])
        
        embed = discord.Embed(
            title=f"🏰 {self.guild_name} Guild Info",
            color=0x0099ff
        )
        embed.add_field(name="👑 Owner", value=f"<@{guild_info.get('owner', 'Unknown')}>", inline=True)
        embed.add_field(name="👥 Members", value=str(len(members)), inline=True)
        embed.add_field(name="💰 Bank Balance", value=f"{guild_info.get('bank', 0):,} coins", inline=True)
        embed.add_field(name="📅 Created", value=guild_info.get('created', 'Unknown')[:10] if guild_info.get('created') else 'Unknown', inline=True)
        embed.add_field(name="📈 Guild Benefits", value="• +5% bank interest\n• Shared treasury\n• Member collaboration", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class DepositModal(discord.ui.Modal, title="💰 Guild Bank Deposit"):
    def __init__(self, guild_name):
        super().__init__()
        self.guild_name = guild_name

    amount = discord.ui.TextInput(
        label="Amount to Deposit",
        placeholder="Enter amount (e.g., 1000)",
        required=True,
        max_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            deposit_amount = int(self.amount.value.replace(",", ""))
            if deposit_amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid positive number!", ephemeral=True)
            return

        data = await load_data()
        user_id = str(interaction.user.id)
        
        # Check if user has enough coins
        user_coins = data.get("coins", {}).get(user_id, 0)
        if user_coins < deposit_amount:
            await interaction.response.send_message(
                f"❌ Insufficient funds! You have {user_coins:,} coins but tried to deposit {deposit_amount:,}.",
                ephemeral=True
            )
            return

        # Check if user is in guild
        user_guild = get_user_guild(user_id, data)
        if user_guild != self.guild_name:
            await interaction.response.send_message("❌ You're not a member of this guild!", ephemeral=True)
            return

        # Process deposit
        data["coins"][user_id] -= deposit_amount
        
        if "guilds" not in data:
            data["guilds"] = {}
        if self.guild_name not in data["guilds"]:
            data["guilds"][self.guild_name] = {"bank": 0, "owner": user_id}
            
        data["guilds"][self.guild_name]["bank"] = data["guilds"][self.guild_name].get("bank", 0) + deposit_amount
        
        # Add to transactions
        if "transactions" not in data:
            data["transactions"] = {}
        if user_id not in data["transactions"]:
            data["transactions"][user_id] = []
        
        data["transactions"][user_id].append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "type": "debit",
            "amount": deposit_amount,
            "reason": f"Guild bank deposit to {self.guild_name}"
        })
        
        await save_data(data)

        embed = discord.Embed(
            title="🏦 Guild Bank Deposit",
            description=f"Successfully deposited **{deposit_amount:,}** coins to **{self.guild_name}** guild bank!",
            color=0x00ff00
        )
        embed.add_field(name="Your New Balance", value=f"{data['coins'][user_id]:,} coins", inline=True)
        embed.add_field(name="Guild Bank Balance", value=f"{data['guilds'][self.guild_name]['bank']:,} coins", inline=True)
        
        await interaction.response.send_message(embed=embed)

class WithdrawModal(discord.ui.Modal, title="💸 Guild Bank Withdrawal"):
    def __init__(self, guild_name):
        super().__init__()
        self.guild_name = guild_name

    amount = discord.ui.TextInput(
        label="Amount to Withdraw",
        placeholder="Enter amount (e.g., 1000)",
        required=True,
        max_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            withdraw_amount = int(self.amount.value.replace(",", ""))
            if withdraw_amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid positive number!", ephemeral=True)
            return

        data = await load_data()
        user_id = str(interaction.user.id)
        
        # Check if user is in guild
        user_guild = get_user_guild(user_id, data)
        if user_guild != self.guild_name:
            await interaction.response.send_message("❌ You're not a member of this guild!", ephemeral=True)
            return

        # Check guild bank balance
        guild_bank = data.get("guilds", {}).get(self.guild_name, {}).get("bank", 0)
        if guild_bank < withdraw_amount:
            await interaction.response.send_message(
                f"❌ Insufficient guild funds! Guild bank has {guild_bank:,} coins but you tried to withdraw {withdraw_amount:,}.",
                ephemeral=True
            )
            return

        # Process withdrawal
        data["guilds"][self.guild_name]["bank"] -= withdraw_amount
        
        if "coins" not in data:
            data["coins"] = {}
        data["coins"][user_id] = data["coins"].get(user_id, 0) + withdraw_amount
        
        # Add to transactions
        if "transactions" not in data:
            data["transactions"] = {}
        if user_id not in data["transactions"]:
            data["transactions"][user_id] = []
        
        data["transactions"][user_id].append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "type": "credit",
            "amount": withdraw_amount,
            "reason": f"Guild bank withdrawal from {self.guild_name}"
        })
        
        await save_data(data)

        embed = discord.Embed(
            title="🏦 Guild Bank Withdrawal",
            description=f"Successfully withdrew **{withdraw_amount:,}** coins from **{self.guild_name}** guild bank!",
            color=0x00ff00
        )
        embed.add_field(name="Your New Balance", value=f"{data['coins'][user_id]:,} coins", inline=True)
        embed.add_field(name="Guild Bank Balance", value=f"{data['guilds'][self.guild_name]['bank']:,} coins", inline=True)
        
        await interaction.response.send_message(embed=embed)

class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="guild_create", description="Create a new guild!")
    @app_commands.describe(name="Name of the guild to create")
    async def guild_create(self, interaction: discord.Interaction, name: str):
        user_id = str(interaction.user.id)
        
        if len(name) < 3 or len(name) > 32:
            await interaction.response.send_message("❌ Guild name must be between 3 and 32 characters!", ephemeral=True)
            return
        
        # Check for valid characters
        if not name.replace(" ", "").replace("-", "").replace("_", "").isalnum():
            await interaction.response.send_message("❌ Guild name can only contain letters, numbers, spaces, hyphens, and underscores!", ephemeral=True)
            return
        
        data = await load_data()
        
        # Check if user is already in a guild
        current_guild = get_user_guild(user_id, data)
        if current_guild:
            await interaction.response.send_message(f"❌ You're already in guild **{current_guild}**! Use `/guild_leave` first.", ephemeral=True)
            return
        
        # Check if guild name exists
        if name in data.get("guilds", {}):
            await interaction.response.send_message(f"❌ Guild **{name}** already exists!", ephemeral=True)
            return
        
        # Create guild
        if "guilds" not in data:
            data["guilds"] = {}
        if "guild_members" not in data:
            data["guild_members"] = {}

        data["guilds"][name] = {
            "owner": user_id,
            "bank": 0,
            "created": datetime.now().isoformat(),
            "moderators": []
        }
        data["guild_members"][name] = [user_id]

        await save_data(data)

        embed = discord.Embed(
            title="🏰 Guild Created!",
            description=f"Successfully created guild **{name}**!",
            color=0x00ff00
        )
        embed.add_field(name="👑 Owner", value=f"<@{user_id}>", inline=True)
        embed.add_field(name="👥 Members", value="1", inline=True)
        embed.add_field(name="💰 Bank Balance", value="0 coins", inline=True)
        embed.add_field(name="🎉 Next Steps", value="• Invite members with `/guild_invite`\n• Deposit coins with `/guild_bank`\n• View info with `/guild_info`", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="guild_join", description="Join an existing guild!")
    @app_commands.describe(name="Name of the guild to join")
    async def guild_join(self, interaction: discord.Interaction, name: str):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        # Check if user is already in a guild
        current_guild = get_user_guild(user_id, data)
        if current_guild:
            await interaction.response.send_message(f"❌ You're already in guild **{current_guild}**! Use `/guild_leave` first.", ephemeral=True)
            return

        # Check if guild exists
        if name not in data.get("guilds", {}):
            await interaction.response.send_message(f"❌ Guild **{name}** doesn't exist!", ephemeral=True)
            return

        # Join guild
        if "guild_members" not in data:
            data["guild_members"] = {}
        if name not in data["guild_members"]:
            data["guild_members"][name] = []

        data["guild_members"][name].append(user_id)
        await save_data(data)

        embed = discord.Embed(
            title="🏰 Joined Guild!",
            description=f"Successfully joined guild **{name}**!",
            color=0x00ff00
        )
        embed.add_field(name="👥 Members", value=str(len(data["guild_members"][name])), inline=True)
        embed.add_field(name="💰 Guild Bank", value=f"{data['guilds'][name].get('bank', 0):,} coins", inline=True)
        embed.add_field(name="📈 Benefits", value="• +5% bank interest\n• Access to guild bank\n• Member collaboration", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="guild_leave", description="Leave your current guild!")
    async def guild_leave(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        # Find user's guild
        user_guild = get_user_guild(user_id, data)
        if not user_guild:
            await interaction.response.send_message("❌ You're not in any guild!", ephemeral=True)
            return

        # Check if user is owner
        if data.get("guilds", {}).get(user_guild, {}).get("owner") == user_id:
            await interaction.response.send_message("❌ You can't leave your own guild! Transfer ownership first or disband the guild.", ephemeral=True)
            return

        # Leave guild
        data["guild_members"][user_guild].remove(user_id)
        await save_data(data)

        embed = discord.Embed(
            title="🚪 Left Guild",
            description=f"Successfully left guild **{user_guild}**.",
            color=0xff0000
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="guild_bank", description="Access your guild's bank!")
    async def guild_bank(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        # Find user's guild
        user_guild = get_user_guild(user_id, data)
        if not user_guild:
            await interaction.response.send_message("❌ You're not in any guild!", ephemeral=True)
            return

        guild_info = data.get("guilds", {}).get(user_guild, {})
        guild_bank = guild_info.get("bank", 0)
        member_count = len(data.get("guild_members", {}).get(user_guild, []))

        embed = discord.Embed(
            title=f"🏦 {user_guild} Guild Bank",
            color=0x0099ff
        )
        embed.add_field(name="💰 Bank Balance", value=f"{guild_bank:,} coins", inline=True)
        embed.add_field(name="👥 Members", value=str(member_count), inline=True)
        embed.add_field(name="👑 Owner", value=f"<@{guild_info.get('owner', 'Unknown')}>", inline=True)
        
        # Add interest bonus info
        embed.add_field(name="📈 Guild Benefits", value="• +5% bank interest\n• Shared guild treasury\n• Member collaboration\n• Use buttons below to manage funds", inline=False)

        view = GuildBankView(user_guild, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="guild_members", description="View your guild's member list!")
    async def guild_members(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        # Find user's guild
        user_guild = get_user_guild(user_id, data)
        if not user_guild:
            await interaction.response.send_message("❌ You're not in any guild!", ephemeral=True)
            return

        members = data.get("guild_members", {}).get(user_guild, [])
        guild_info = data.get("guilds", {}).get(user_guild, {})

        embed = discord.Embed(
            title=f"👥 {user_guild} Members",
            color=0x0099ff
        )

        member_list = []
        for i, member_id in enumerate(members, 1):
            try:
                member = await self.bot.fetch_user(int(member_id))
                name = member.display_name if member else f"User {member_id}"
            except:
                name = f"User {member_id}"
            
            role = "👑 Owner" if member_id == guild_info.get("owner") else "👤 Member"
            member_list.append(f"{i}. {name} - {role}")

        embed.description = "\n".join(member_list) if member_list else "No members found"
        embed.add_field(name="📊 Guild Stats", value=f"**Members:** {len(members)}\n**Bank:** {guild_info.get('bank', 0):,} coins", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="guild_top", description="View the richest guilds leaderboard!")
    async def guild_top(self, interaction: discord.Interaction):
        data = await load_data()
        guilds = data.get("guilds", {})
        
        if not guilds:
            await interaction.response.send_message("❌ No guilds exist yet!", ephemeral=True)
            return

        # Sort guilds by bank balance
        sorted_guilds = sorted(guilds.items(), key=lambda x: x[1].get("bank", 0), reverse=True)

        embed = discord.Embed(
            title="🏆 Top Guilds by Bank Balance",
            color=0xffd700
        )

        description = []
        for i, (guild_name, guild_data) in enumerate(sorted_guilds[:10], 1):
            bank_balance = guild_data.get("bank", 0)
            member_count = len(data.get("guild_members", {}).get(guild_name, []))
            
            try:
                owner = await self.bot.fetch_user(int(guild_data.get("owner", 0)))
                owner_name = owner.display_name if owner else "Unknown"
            except:
                owner_name = "Unknown"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            description.append(f"{medal} **{guild_name}**\n    💰 {bank_balance:,} coins • 👥 {member_count} members • 👑 {owner_name}")

        embed.description = "\n\n".join(description) if description else "No guilds found"
        embed.set_footer(text="🎉 Top guilds get special bonuses and recognition!")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="guild_info", description="View detailed information about your guild!")
    async def guild_info(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        # Find user's guild
        user_guild = get_user_guild(user_id, data)
        if not user_guild:
            await interaction.response.send_message("❌ You're not in any guild!", ephemeral=True)
            return

        guild_info = data.get("guilds", {}).get(user_guild, {})
        members = data.get("guild_members", {}).get(user_guild, [])
        
        embed = discord.Embed(
            title=f"ℹ️ {user_guild} Guild Information",
            color=0x0099ff
        )
        
        try:
            owner = await self.bot.fetch_user(int(guild_info.get("owner", 0)))
            owner_name = owner.display_name if owner else "Unknown"
        except:
            owner_name = "Unknown"
        
        embed.add_field(name="👑 Owner", value=owner_name, inline=True)
        embed.add_field(name="👥 Members", value=str(len(members)), inline=True)
        embed.add_field(name="💰 Bank Balance", value=f"{guild_info.get('bank', 0):,} coins", inline=True)
        embed.add_field(name="📅 Created", value=guild_info.get('created', 'Unknown')[:10] if guild_info.get('created') else 'Unknown', inline=True)
        embed.add_field(name="🎯 Your Role", value=get_guild_role(user_id, user_guild, data) or "Member", inline=True)
        embed.add_field(name="📈 Guild Benefits", value="• +5% bank interest for all members\n• Shared treasury for cooperation\n• Member networking and collaboration\n• Leaderboard recognition", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Guild(bot))