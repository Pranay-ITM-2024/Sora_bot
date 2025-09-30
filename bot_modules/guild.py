"""
Guild module: createguild, joinguild, leaveguild, guildinfo, guildbank, guildkick, guildinvite
"""
import discord
from discord import app_commands
from discord.ext import commands
import json
import aiofiles
from pathlib import Path
import asyncio
from datetime import datetime

DATA_PATH = Path(__file__).parent.parent / "data.json"
_data_lock = asyncio.Lock()

async def load_data():
    """Load data from JSON file with concurrency protection"""
    async with _data_lock:
        try:
            async with aiofiles.open(DATA_PATH, 'r') as f:
                return json.loads(await f.read())
        except:
            return {}

async def save_data(data):
    """Save data to JSON file with atomic writes"""
    async with _data_lock:
        try:
            temp_path = DATA_PATH.with_suffix('.tmp')
            async with aiofiles.open(temp_path, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
            temp_path.replace(DATA_PATH)
        except Exception as e:
            print(f"Error saving data: {e}")

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

def get_user_guild(user_id, data):
    """Get the guild a user belongs to"""
    user_id = str(user_id)
    guild_members = data.get("guild_members", {})
    
    for guild_name, members in guild_members.items():
        if user_id in members:
            return guild_name
    return None

def add_transaction(user_id, amount, reason, data, tx_type="credit"):
    """Add transaction record"""
    tx = {
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "type": tx_type,
        "amount": abs(amount),
        "reason": reason
    }
    data.setdefault("transactions", {}).setdefault(str(user_id), []).append(tx)

def get_guild_bonuses(guild_name, data):
    """Calculate guild bonuses based on rank and bank"""
    guilds = data.get("guilds", {})
    if not guilds or guild_name not in guilds:
        return {}
    
    guild_bank = guilds[guild_name].get("bank", 0)
    member_count = len(data.get("guild_members", {}).get(guild_name, []))
    
    # Calculate rank (richest guild gets best bonuses)
    guild_ranks = sorted(guilds.items(), key=lambda x: x[1].get("bank", 0), reverse=True)
    rank = next((i+1 for i, (name, _) in enumerate(guild_ranks) if name == guild_name), len(guild_ranks))
    
    bonuses = {
        "shop_discount": 0,
        "bank_interest": 0,
        "rob_protection": 0,
        "casino_bonus": 0
    }
    
    # Top 3 guilds get bonuses
    if rank == 1:  # Richest guild
        bonuses["shop_discount"] = 0.10  # 10% shop discount
        bonuses["bank_interest"] = 0.002  # +0.2% bank interest
        bonuses["rob_protection"] = 0.15  # 15% rob protection
        bonuses["casino_bonus"] = 0.05   # 5% casino bonus
    elif rank == 2:  # Second richest
        bonuses["shop_discount"] = 0.05  # 5% shop discount
        bonuses["bank_interest"] = 0.001  # +0.1% bank interest
        bonuses["rob_protection"] = 0.10  # 10% rob protection
        bonuses["casino_bonus"] = 0.03   # 3% casino bonus
    elif rank == 3:  # Third richest
        bonuses["shop_discount"] = 0.03  # 3% shop discount
        bonuses["bank_interest"] = 0.0005  # +0.05% bank interest
        bonuses["rob_protection"] = 0.05  # 5% rob protection
        bonuses["casino_bonus"] = 0.02   # 2% casino bonus
    
    # Additional bonuses for larger guilds
    if member_count >= 10:
        for key in bonuses:
            bonuses[key] *= 1.2  # 20% bonus for large guilds
    
    return bonuses

class GuildBankView(discord.ui.View):
    def __init__(self, user_id, guild_name):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_name = guild_name

    @discord.ui.button(label="Deposit", style=discord.ButtonStyle.green, emoji="📥")
    async def deposit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your guild interface!", ephemeral=True)
            return
        
        modal = GuildDepositModal(self.guild_name)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Withdraw", style=discord.ButtonStyle.red, emoji="📤")
    async def withdraw(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your guild interface!", ephemeral=True)
            return
        
        data = await load_data()
        role = get_guild_role(self.user_id, self.guild_name, data)
        
        if role not in ["Owner", "Moderator"]:
            await interaction.response.send_message("❌ Only guild owners and moderators can withdraw from the guild bank!", ephemeral=True)
            return
        
        modal = GuildWithdrawModal(self.guild_name)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your guild interface!", ephemeral=True)
            return
        
        await self.show_bank_info(interaction)

    async def show_bank_info(self, interaction):
        data = await load_data()
        guild_data = data.get("guilds", {}).get(self.guild_name, {})
        guild_bank = guild_data.get("bank", 0)
        user_coins = data.get("coins", {}).get(self.user_id, 0)
        
        # Get guild bonuses
        bonuses = get_guild_bonuses(self.guild_name, data)
        
        embed = discord.Embed(title=f"🏦 {self.guild_name} Guild Bank", color=0x3498db)
        embed.add_field(name="Guild Bank", value=f"{guild_bank:,} coins", inline=True)
        embed.add_field(name="Your Balance", value=f"{user_coins:,} coins", inline=True)
        embed.add_field(name="Your Role", value=get_guild_role(self.user_id, self.guild_name, data), inline=True)
        
        if any(bonuses.values()):
            bonus_text = []
            if bonuses["shop_discount"] > 0:
                bonus_text.append(f"🛒 Shop: -{bonuses['shop_discount']*100:.1f}%")
            if bonuses["bank_interest"] > 0:
                bonus_text.append(f"🏦 Interest: +{bonuses['bank_interest']*100:.2f}%")
            if bonuses["rob_protection"] > 0:
                bonus_text.append(f"🛡️ Rob Protection: +{bonuses['rob_protection']*100:.1f}%")
            if bonuses["casino_bonus"] > 0:
                bonus_text.append(f"🎰 Casino: +{bonuses['casino_bonus']*100:.1f}%")
            
            embed.add_field(name="🎉 Guild Bonuses", value="\n".join(bonus_text), inline=False)
        
        embed.set_footer(text="💡 Guild rank bonuses update based on total guild bank amount!")
        
        await interaction.response.edit_message(embed=embed, view=self)

class GuildDepositModal(discord.ui.Modal):
    def __init__(self, guild_name):
        super().__init__(title=f"Deposit to {guild_name}")
        self.guild_name = guild_name

    amount = discord.ui.TextInput(
        label="Amount to Deposit",
        placeholder="Enter amount in coins...",
        min_length=1,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            deposit_amount = int(self.amount.value)
            if deposit_amount <= 0:
                await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        data = await load_data()
        
        user_coins = data.get("coins", {}).get(user_id, 0)
        if user_coins < deposit_amount:
            await interaction.response.send_message(f"❌ Insufficient funds! You have {user_coins:,} coins.", ephemeral=True)
            return
        
        # Process deposit
        data.setdefault("coins", {})[user_id] = user_coins - deposit_amount
        data.setdefault("guilds", {}).setdefault(self.guild_name, {})["bank"] = data["guilds"][self.guild_name].get("bank", 0) + deposit_amount
        
        # Add transaction
        add_transaction(user_id, deposit_amount, f"Guild bank deposit to {self.guild_name}", data, "debit")
        
        await save_data(data)
        
        embed = discord.Embed(title="✅ Deposit Successful", color=0x27ae60)
        embed.add_field(name="Deposited", value=f"{deposit_amount:,} coins", inline=True)
        embed.add_field(name="Your Balance", value=f"{user_coins - deposit_amount:,} coins", inline=True)
        embed.add_field(name="Guild Bank", value=f"{data['guilds'][self.guild_name]['bank']:,} coins", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class GuildWithdrawModal(discord.ui.Modal):
    def __init__(self, guild_name):
        super().__init__(title=f"Withdraw from {guild_name}")
        self.guild_name = guild_name

    amount = discord.ui.TextInput(
        label="Amount to Withdraw",
        placeholder="Enter amount in coins...",
        min_length=1,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            withdraw_amount = int(self.amount.value)
            if withdraw_amount <= 0:
                await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        data = await load_data()
        
        guild_bank = data.get("guilds", {}).get(self.guild_name, {}).get("bank", 0)
        if guild_bank < withdraw_amount:
            await interaction.response.send_message(f"❌ Insufficient guild funds! Guild bank has {guild_bank:,} coins.", ephemeral=True)
            return
        
        # Process withdrawal
        user_coins = data.get("coins", {}).get(user_id, 0)
        data.setdefault("coins", {})[user_id] = user_coins + withdraw_amount
        data.setdefault("guilds", {}).setdefault(self.guild_name, {})["bank"] = guild_bank - withdraw_amount
        
        # Add transaction
        add_transaction(user_id, withdraw_amount, f"Guild bank withdrawal from {self.guild_name}", data, "credit")
        
        await save_data(data)
        
        embed = discord.Embed(title="✅ Withdrawal Successful", color=0x27ae60)
        embed.add_field(name="Withdrawn", value=f"{withdraw_amount:,} coins", inline=True)
        embed.add_field(name="Your Balance", value=f"{user_coins + withdraw_amount:,} coins", inline=True)
        embed.add_field(name="Guild Bank", value=f"{guild_bank - withdraw_amount:,} coins", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class GuildManagementView(discord.ui.View):
    def __init__(self, user_id, guild_name):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_name = guild_name

    @discord.ui.button(label="Promote Member", style=discord.ButtonStyle.green, emoji="⬆️")
    async def promote(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your guild interface!", ephemeral=True)
            return
        
        data = await load_data()
        role = get_guild_role(self.user_id, self.guild_name, data)
        
        if role != "Owner":
            await interaction.response.send_message("❌ Only guild owners can promote members!", ephemeral=True)
            return
        
        modal = PromoteMemberModal(self.guild_name)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Kick Member", style=discord.ButtonStyle.red, emoji="👢")
    async def kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your guild interface!", ephemeral=True)
            return
        
        data = await load_data()
        role = get_guild_role(self.user_id, self.guild_name, data)
        
        if role not in ["Owner", "Moderator"]:
            await interaction.response.send_message("❌ Only guild owners and moderators can kick members!", ephemeral=True)
            return
        
        modal = KickMemberModal(self.guild_name, self.user_id)
        await interaction.response.send_modal(modal)

class PromoteMemberModal(discord.ui.Modal):
    def __init__(self, guild_name):
        super().__init__(title=f"Promote Member in {guild_name}")
        self.guild_name = guild_name

    user_id = discord.ui.TextInput(
        label="User ID to Promote",
        placeholder="Enter the user's Discord ID...",
        min_length=17,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        target_id = self.user_id.value.strip()
        
        data = await load_data()
        guild_members = data.get("guild_members", {}).get(self.guild_name, [])
        
        if target_id not in guild_members:
            await interaction.response.send_message("❌ User is not in this guild!", ephemeral=True)
            return
        
        guild_data = data.setdefault("guilds", {}).setdefault(self.guild_name, {})
        moderators = guild_data.setdefault("moderators", [])
        
        if target_id in moderators:
            await interaction.response.send_message("❌ User is already a moderator!", ephemeral=True)
            return
        
        moderators.append(target_id)
        await save_data(data)
        
        embed = discord.Embed(title="✅ Member Promoted", color=0x27ae60)
        embed.description = f"<@{target_id}> has been promoted to moderator!"
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class KickMemberModal(discord.ui.Modal):
    def __init__(self, guild_name, kicker_id):
        super().__init__(title=f"Kick Member from {guild_name}")
        self.guild_name = guild_name
        self.kicker_id = kicker_id

    user_id = discord.ui.TextInput(
        label="User ID to Kick",
        placeholder="Enter the user's Discord ID...",
        min_length=17,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        target_id = self.user_id.value.strip()
        
        data = await load_data()
        guild_members = data.get("guild_members", {}).get(self.guild_name, [])
        
        if target_id not in guild_members:
            await interaction.response.send_message("❌ User is not in this guild!", ephemeral=True)
            return
        
        # Check permissions
        kicker_role = get_guild_role(self.kicker_id, self.guild_name, data)
        target_role = get_guild_role(target_id, self.guild_name, data)
        
        if target_role == "Owner":
            await interaction.response.send_message("❌ Cannot kick the guild owner!", ephemeral=True)
            return
        
        if kicker_role == "Moderator" and target_role == "Moderator":
            await interaction.response.send_message("❌ Moderators cannot kick other moderators!", ephemeral=True)
            return
        
        # Remove from guild
        guild_members.remove(target_id)
        
        # Remove from moderators if applicable
        guild_data = data.get("guilds", {}).get(self.guild_name, {})
        if target_id in guild_data.get("moderators", []):
            guild_data["moderators"].remove(target_id)
        
        await save_data(data)
        
        embed = discord.Embed(title="✅ Member Kicked", color=0xe74c3c)
        embed.description = f"<@{target_id}> has been kicked from the guild!"
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="createguild", description="Create a new guild!")
    @app_commands.describe(name="Name of the guild to create")
    async def createguild(self, interaction: discord.Interaction, name: str):
        user_id = str(interaction.user.id)
        
        if len(name) < 3 or len(name) > 32:
            await interaction.response.send_message("❌ Guild name must be between 3 and 32 characters!", ephemeral=True)
            return
        
        data = await load_data()
        
        # Check if user is already in a guild
        current_guild = get_user_guild(user_id, data)
        if current_guild:
            await interaction.response.send_message(f"❌ You're already in guild **{current_guild}**! Use `/leaveguild` first.", ephemeral=True)
            return
        
        # Check if guild name exists
        if name in data.get("guilds", {}):
            await interaction.response.send_message(f"❌ Guild **{name}** already exists!", ephemeral=True)
            return
        
        # Check creation cost
        creation_cost = 1000
        user_coins = data.get("coins", {}).get(user_id, 0)
        if user_coins < creation_cost:
            await interaction.response.send_message(f"❌ You need {creation_cost:,} coins to create a guild! Your balance: {user_coins:,}", ephemeral=True)
            return
        
        # Create guild
        data.setdefault("guilds", {})[name] = {
            "owner": user_id,
            "created": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "bank": 0,
            "moderators": []
        }
        
        data.setdefault("guild_members", {})[name] = [user_id]
        data.setdefault("coins", {})[user_id] = user_coins - creation_cost
        
        # Add transaction
        add_transaction(user_id, creation_cost, f"Created guild {name}", data, "debit")
        
        await save_data(data)
        
        embed = discord.Embed(title="🏰 Guild Created!", color=0x27ae60)
        embed.add_field(name="Guild Name", value=name, inline=True)
        embed.add_field(name="Owner", value=f"<@{user_id}>", inline=True)
        embed.add_field(name="Cost", value=f"{creation_cost:,} coins", inline=True)
        embed.add_field(name="Your Balance", value=f"{user_coins - creation_cost:,} coins", inline=True)
        embed.description = f"Welcome to **{name}**! You are now the guild owner."
        embed.set_footer(text="Use /guildinvite to invite members!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="joinguild", description="Join an existing guild!")
    @app_commands.describe(name="Name of the guild to join")
    async def joinguild(self, interaction: discord.Interaction, name: str):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        # Check if user is already in a guild
        current_guild = get_user_guild(user_id, data)
        if current_guild:
            await interaction.response.send_message(f"❌ You're already in guild **{current_guild}**! Use `/leaveguild` first.", ephemeral=True)
            return
        
        # Check if guild exists
        if name not in data.get("guilds", {}):
            await interaction.response.send_message(f"❌ Guild **{name}** doesn't exist!", ephemeral=True)
            return
        
        # Check if user has pending invite
        pending_invites = data.get("guild_invites", {}).get(user_id, [])
        if name not in pending_invites:
            await interaction.response.send_message(f"❌ You don't have an invitation to **{name}**! Ask a member to invite you.", ephemeral=True)
            return
        
        # Join guild
        data.setdefault("guild_members", {}).setdefault(name, []).append(user_id)
        
        # Remove invite
        pending_invites.remove(name)
        if not pending_invites:
            data.get("guild_invites", {}).pop(user_id, None)
        
        await save_data(data)
        
        member_count = len(data["guild_members"][name])
        embed = discord.Embed(title="🎉 Joined Guild!", color=0x27ae60)
        embed.add_field(name="Guild", value=name, inline=True)
        embed.add_field(name="Members", value=f"{member_count} members", inline=True)
        embed.add_field(name="Your Role", value="Member", inline=True)
        embed.description = f"Welcome to **{name}**!"
        embed.set_footer(text="Use /guildinfo to see guild details!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leaveguild", description="Leave your current guild.")
    async def leaveguild(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        current_guild = get_user_guild(user_id, data)
        if not current_guild:
            await interaction.response.send_message("❌ You're not in any guild!", ephemeral=True)
            return
        
        role = get_guild_role(user_id, current_guild, data)
        
        # Check if owner is trying to leave
        if role == "Owner":
            member_count = len(data.get("guild_members", {}).get(current_guild, []))
            if member_count > 1:
                await interaction.response.send_message("❌ Guild owners cannot leave! Transfer ownership or kick all members first.", ephemeral=True)
                return
            else:
                # Delete guild if owner leaves and no other members
                data.get("guilds", {}).pop(current_guild, None)
                data.get("guild_members", {}).pop(current_guild, None)
        else:
            # Remove from guild
            guild_members = data.get("guild_members", {}).get(current_guild, [])
            if user_id in guild_members:
                guild_members.remove(user_id)
            
            # Remove from moderators if applicable
            guild_data = data.get("guilds", {}).get(current_guild, {})
            if user_id in guild_data.get("moderators", []):
                guild_data["moderators"].remove(user_id)
        
        await save_data(data)
        
        embed = discord.Embed(title="👋 Left Guild", color=0x95a5a6)
        embed.description = f"You have left **{current_guild}**."
        
        if role == "Owner":
            embed.add_field(name="Guild Status", value="Guild disbanded", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="guildinfo", description="View information about your guild.")
    async def guildinfo(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        current_guild = get_user_guild(user_id, data)
        if not current_guild:
            await interaction.response.send_message("❌ You're not in any guild! Use `/joinguild` or `/createguild`.", ephemeral=True)
            return
        
        guild_data = data.get("guilds", {}).get(current_guild, {})
        guild_members = data.get("guild_members", {}).get(current_guild, [])
        
        # Get guild rank
        guilds = data.get("guilds", {})
        guild_ranks = sorted(guilds.items(), key=lambda x: x[1].get("bank", 0), reverse=True)
        rank = next((i+1 for i, (name, _) in enumerate(guild_ranks) if name == current_guild), len(guild_ranks))
        
        # Get bonuses
        bonuses = get_guild_bonuses(current_guild, data)
        
        embed = discord.Embed(title=f"🏰 {current_guild}", color=0x3498db)
        embed.add_field(name="👑 Owner", value=f"<@{guild_data.get('owner')}>", inline=True)
        embed.add_field(name="👥 Members", value=f"{len(guild_members)}", inline=True)
        embed.add_field(name="🏆 Rank", value=f"#{rank}", inline=True)
        embed.add_field(name="🏦 Guild Bank", value=f"{guild_data.get('bank', 0):,} coins", inline=True)
        embed.add_field(name="📅 Created", value=guild_data.get('created', 'Unknown'), inline=True)
        embed.add_field(name="👤 Your Role", value=get_guild_role(user_id, current_guild, data), inline=True)
        
        # Show moderators
        moderators = guild_data.get("moderators", [])
        if moderators:
            mod_list = [f"<@{mod_id}>" for mod_id in moderators[:5]]
            if len(moderators) > 5:
                mod_list.append(f"... and {len(moderators) - 5} more")
            embed.add_field(name="🛡️ Moderators", value="\n".join(mod_list), inline=False)
        
        # Show bonuses
        if any(bonuses.values()):
            bonus_text = []
            if bonuses["shop_discount"] > 0:
                bonus_text.append(f"🛒 Shop Discount: {bonuses['shop_discount']*100:.1f}%")
            if bonuses["bank_interest"] > 0:
                bonus_text.append(f"🏦 Extra Interest: +{bonuses['bank_interest']*100:.2f}%")
            if bonuses["rob_protection"] > 0:
                bonus_text.append(f"🛡️ Rob Protection: +{bonuses['rob_protection']*100:.1f}%")
            if bonuses["casino_bonus"] > 0:
                bonus_text.append(f"🎰 Casino Bonus: +{bonuses['casino_bonus']*100:.1f}%")
            
            embed.add_field(name="🎉 Active Bonuses", value="\n".join(bonus_text), inline=False)
        
        embed.set_footer(text="💡 Guild rank and bonuses are based on total guild bank amount!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="guildbank", description="Access the guild bank interface.")
    async def guildbank(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        current_guild = get_user_guild(user_id, data)
        if not current_guild:
            await interaction.response.send_message("❌ You're not in any guild!", ephemeral=True)
            return
        
        view = GuildBankView(user_id, current_guild)
        await view.show_bank_info(interaction)

    @app_commands.command(name="guildinvite", description="Invite a user to your guild.")
    @app_commands.describe(user="User to invite to your guild")
    async def guildinvite(self, interaction: discord.Interaction, user: discord.User):
        user_id = str(interaction.user.id)
        target_id = str(user.id)
        
        if user_id == target_id:
            await interaction.response.send_message("❌ You cannot invite yourself!", ephemeral=True)
            return
        
        data = await load_data()
        
        current_guild = get_user_guild(user_id, data)
        if not current_guild:
            await interaction.response.send_message("❌ You're not in any guild!", ephemeral=True)
            return
        
        # Check if target is already in a guild
        target_guild = get_user_guild(target_id, data)
        if target_guild:
            await interaction.response.send_message(f"❌ <@{target_id}> is already in guild **{target_guild}**!", ephemeral=True)
            return
        
        # Check if already invited
        pending_invites = data.get("guild_invites", {}).get(target_id, [])
        if current_guild in pending_invites:
            await interaction.response.send_message(f"❌ <@{target_id}> already has a pending invite to **{current_guild}**!", ephemeral=True)
            return
        
        # Send invite
        data.setdefault("guild_invites", {}).setdefault(target_id, []).append(current_guild)
        await save_data(data)
        
        embed = discord.Embed(title="📨 Guild Invitation Sent", color=0x27ae60)
        embed.add_field(name="Guild", value=current_guild, inline=True)
        embed.add_field(name="Invited User", value=f"<@{target_id}>", inline=True)
        embed.description = f"<@{target_id}> can now join **{current_guild}** using `/joinguild {current_guild}`"
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="guildmanage", description="Access guild management tools (Owner/Moderator only).")
    async def guildmanage(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        current_guild = get_user_guild(user_id, data)
        if not current_guild:
            await interaction.response.send_message("❌ You're not in any guild!", ephemeral=True)
            return
        
        role = get_guild_role(user_id, current_guild, data)
        if role not in ["Owner", "Moderator"]:
            await interaction.response.send_message("❌ Only guild owners and moderators can access management tools!", ephemeral=True)
            return
        
        embed = discord.Embed(title=f"🛠️ Managing {current_guild}", color=0x9b59b6)
        embed.add_field(name="Your Role", value=role, inline=True)
        embed.add_field(name="Permissions", value="Promote members, kick members" if role == "Owner" else "Kick members", inline=True)
        embed.description = "Use the buttons below to manage your guild."
        
        view = GuildManagementView(user_id, current_guild)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Guild(bot))
import discord
from discord import app_commands
from discord.ext import commands

class GuildCommands(commands.Group):
    """Guild command group"""
    
    @app_commands.command(name="create", description="Create a new guild.")
    @app_commands.describe(name="Name of the guild to create")
    async def create(self, interaction: discord.Interaction, name: str):
        embed = discord.Embed(title="🏰 Guild Created!", color=0x2980b9)
        embed.add_field(name="Guild Name", value=name, inline=True)
        embed.add_field(name="Leader", value=interaction.user.mention, inline=True)
        embed.description = f"Successfully created guild **{name}**!"
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="join", description="Join an existing guild.")
    @app_commands.describe(name="Name of the guild to join")
    async def join(self, interaction: discord.Interaction, name: str):
        embed = discord.Embed(title="🤝 Guild Join Request", color=0x27ae60)
        embed.description = f"Sent request to join **{name}**!"
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="leave", description="Leave your current guild.")
    async def leave(self, interaction: discord.Interaction):
        embed = discord.Embed(title="👋 Left Guild", color=0xe74c3c)
        embed.description = "You have left your guild."
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="bank", description="Access guild bank.")
    async def bank(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🏦 Guild Bank", color=0xf39c12)
        embed.add_field(name="Guild Balance", value="10,500 coins", inline=True)
        embed.add_field(name="Interest Rate", value="5% per tick", inline=True)
        embed.description = "Guild bank management (placeholder)"
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="members", description="View guild members.")
    async def members(self, interaction: discord.Interaction):
        embed = discord.Embed(title="👥 Guild Members", color=0x9b59b6)
        embed.description = "Guild members list (placeholder)"
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="top", description="Show richest guilds leaderboard.")
    async def top(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🏆 Richest Guilds", color=0xf1c40f)
        embed.description = "Guild leaderboard (placeholder)"
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Add guild command group
        self.guild_group = GuildCommands(name="guild", description="Guild management commands")
        self.bot.tree.add_command(self.guild_group)

    @app_commands.command(name="guildinfo", description="Show guild system information.")
    async def guildinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🏰 Guild System", description="Create and manage guilds with your friends!", color=0x2980b9)
        
        embed.add_field(
            name="📋 Commands",
            value="`/guild create <name>` - Create a guild\n"
                  "`/guild join <name>` - Join a guild\n"
                  "`/guild leave` - Leave your guild\n"
                  "`/guild bank` - Guild bank management\n"
                  "`/guild members` - View guild members\n"
                  "`/guild top` - Richest guilds leaderboard",
            inline=False
        )
        
        embed.add_field(
            name="💰 Guild Benefits",
            value="• Shared guild bank with 5% interest\n"
                  "• Richest guild gets 10% shop discount\n"
                  "• Social features and cooperation\n"
                  "• Guild-exclusive events (coming soon)",
            inline=False
        )
        
        embed.set_footer(text="Start building your guild empire today!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Guild(bot))
