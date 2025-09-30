"""
Guild system cog
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

class GuildCommands(commands.Cog):
    """Guild system commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='guild', aliases=['g'])
    async def guild(self, ctx, action: str, *, args: str = ""):
        """Main guild command with subcommands"""
        if action.lower() == "create":
            await self.create_guild(ctx, args)
        elif action.lower() == "join":
            await self.join_guild(ctx, args)
        elif action.lower() == "leave":
            await self.leave_guild(ctx)
        elif action.lower() == "bank":
            await self.guild_bank(ctx)
        elif action.lower() == "members":
            await self.guild_members(ctx)
        elif action.lower() == "top":
            await self.guild_top(ctx)
        else:
            await ctx.send("❌ Invalid guild action! Use: create, join, leave, bank, members, top")
    
    @commands.command(name='guild_create')
    async def create_guild(self, ctx, guild_name: str):
        """Create a guild"""
        if not guild_name:
            await ctx.send("❌ Please provide a guild name!")
            return
        
        if len(guild_name) > 32:
            await ctx.send("❌ Guild name must be 32 characters or less!")
            return
        
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Check if user is already in a guild
        for guild_id, guild_data in data["guilds"].items():
            if user_id in guild_data.get("members", []):
                await ctx.send(f"❌ You're already in the guild '{guild_data['name']}'!")
                return
        
        # Check if guild name already exists
        for guild_data in data["guilds"].values():
            if guild_data["name"].lower() == guild_name.lower():
                await ctx.send("❌ A guild with that name already exists!")
                return
        
        # Create guild
        guild_id = str(len(data["guilds"]) + 1)
        data["guilds"][guild_id] = {
            "name": guild_name,
            "leader": user_id,
            "members": [user_id],
            "bank": 0,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="🏰 Guild Created!",
            description=f"**{ctx.author.display_name}** created the guild **{guild_name}**!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='guild_join')
    async def join_guild(self, ctx, guild_name: str):
        """Join a guild"""
        if not guild_name:
            await ctx.send("❌ Please provide a guild name!")
            return
        
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Check if user is already in a guild
        for guild_id, guild_data in data["guilds"].items():
            if user_id in guild_data.get("members", []):
                await ctx.send(f"❌ You're already in the guild '{guild_data['name']}'!")
                return
        
        # Find guild
        target_guild = None
        target_guild_id = None
        for guild_id, guild_data in data["guilds"].items():
            if guild_data["name"].lower() == guild_name.lower():
                target_guild = guild_data
                target_guild_id = guild_id
                break
        
        if not target_guild:
            await ctx.send("❌ Guild not found!")
            return
        
        # Check guild size limit (max 50 members)
        if len(target_guild["members"]) >= 50:
            await ctx.send("❌ This guild is full!")
            return
        
        # Join guild
        data["guilds"][target_guild_id]["members"].append(user_id)
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="✅ Joined Guild!",
            description=f"**{ctx.author.display_name}** joined the guild **{guild_name}**!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='guild_leave')
    async def leave_guild(self, ctx):
        """Leave a guild"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Find user's guild
        user_guild = None
        user_guild_id = None
        for guild_id, guild_data in data["guilds"].items():
            if user_id in guild_data.get("members", []):
                user_guild = guild_data
                user_guild_id = guild_id
                break
        
        if not user_guild:
            await ctx.send("❌ You're not in any guild!")
            return
        
        # Check if user is the leader
        if user_guild["leader"] == user_id:
            await ctx.send("❌ Guild leaders cannot leave! Transfer leadership first or disband the guild.")
            return
        
        # Leave guild
        data["guilds"][user_guild_id]["members"].remove(user_id)
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="👋 Left Guild!",
            description=f"**{ctx.author.display_name}** left the guild **{user_guild['name']}**!",
            color=0xffa500
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='guild_bank')
    async def guild_bank(self, ctx):
        """Manage guild bank"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Find user's guild
        user_guild = None
        user_guild_id = None
        for guild_id, guild_data in data["guilds"].items():
            if user_id in guild_data.get("members", []):
                user_guild = guild_data
                user_guild_id = guild_id
                break
        
        if not user_guild:
            await ctx.send("❌ You're not in any guild!")
            return
        
        guild_bank = user_guild.get("bank", 0)
        
        embed = discord.Embed(
            title=f"🏦 {user_guild['name']} Guild Bank",
            description=f"**Balance:** {guild_bank:,} coins",
            color=0x0099ff
        )
        
        view = GuildBankView(ctx.author, user_guild_id, self.bot)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='guild_members')
    async def guild_members(self, ctx):
        """View guild members"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Find user's guild
        user_guild = None
        for guild_data in data["guilds"].values():
            if user_id in guild_data.get("members", []):
                user_guild = guild_data
                break
        
        if not user_guild:
            await ctx.send("❌ You're not in any guild!")
            return
        
        # Format members list
        members_text = ""
        for member_id in user_guild["members"]:
            try:
                member = await self.bot.fetch_user(int(member_id))
                member_name = member.display_name
                if member_id == user_guild["leader"]:
                    member_name += " 👑"
                members_text += f"• {member_name}\n"
            except:
                members_text += f"• Unknown User ({member_id})\n"
        
        embed = discord.Embed(
            title=f"👥 {user_guild['name']} Members",
            description=members_text,
            color=0x0099ff
        )
        embed.set_footer(text=f"Total Members: {len(user_guild['members'])}/50")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='guild_top')
    async def guild_top(self, ctx):
        """Show leaderboard of richest guilds"""
        data = await DataManager.load_data()
        
        # Sort guilds by bank balance
        guild_list = []
        for guild_id, guild_data in data["guilds"].items():
            guild_list.append((guild_data["name"], guild_data.get("bank", 0), len(guild_data["members"])))
        
        guild_list.sort(key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title="🏆 Richest Guilds",
            color=0xffd700
        )
        
        for i, (name, bank, members) in enumerate(guild_list[:10]):
            position = i + 1
            medal = "🥇" if position == 1 else "🥈" if position == 2 else "🥉" if position == 3 else f"{position}."
            embed.add_field(
                name=f"{medal} {name}",
                value=f"**Bank:** {bank:,} coins\n**Members:** {members}",
                inline=True
            )
        
        await ctx.send(embed=embed)

class GuildBankView(discord.ui.View):
    def __init__(self, user, guild_id, bot):
        super().__init__(timeout=60)
        self.user = user
        self.guild_id = guild_id
        self.bot = bot
    
    @discord.ui.button(label='Deposit', style=discord.ButtonStyle.blurple)
    async def deposit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This is not your guild bank!", ephemeral=True)
            return
        
        modal = GuildBankModal("deposit", self.guild_id, self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Withdraw', style=discord.ButtonStyle.green)
    async def withdraw(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This is not your guild bank!", ephemeral=True)
            return
        
        modal = GuildBankModal("withdraw", self.guild_id, self.bot)
        await interaction.response.send_modal(modal)

class GuildBankModal(discord.ui.Modal):
    def __init__(self, action, guild_id, bot):
        super().__init__(title=f"Guild Bank {action.title()}")
        self.action = action
        self.guild_id = guild_id
        self.bot = bot
        
        self.amount_input = discord.ui.TextInput(
            label="Amount",
            placeholder="Enter amount to deposit/withdraw...",
            required=True
        )
        self.add_item(self.amount_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value)
            if amount <= 0:
                await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
            return
        
        data = await DataManager.load_data()
        user_id = str(interaction.user.id)
        
        # Check if user is in the guild
        if user_id not in data["guilds"][self.guild_id]["members"]:
            await interaction.response.send_message("❌ You're not in this guild!", ephemeral=True)
            return
        
        if self.action == "deposit":
            wallet = data["coins"].get(user_id, 0)
            if wallet < amount:
                await interaction.response.send_message("❌ Insufficient funds in wallet!", ephemeral=True)
                return
            
            data["coins"][user_id] -= amount
            data["guilds"][self.guild_id]["bank"] = data["guilds"][self.guild_id].get("bank", 0) + amount
            
            embed = discord.Embed(
                title="💳 Guild Deposit Successful!",
                description=f"Deposited **{amount:,} coins** to the guild bank.",
                color=0x00ff00
            )
        else:  # withdraw
            guild_bank = data["guilds"][self.guild_id].get("bank", 0)
            if guild_bank < amount:
                await interaction.response.send_message("❌ Insufficient funds in guild bank!", ephemeral=True)
                return
            
            data["guilds"][self.guild_id]["bank"] -= amount
            data["coins"][user_id] = data["coins"].get(user_id, 0) + amount
            
            embed = discord.Embed(
                title="💸 Guild Withdrawal Successful!",
                description=f"Withdrew **{amount:,} coins** from the guild bank.",
                color=0x00ff00
            )
        
        await DataManager.save_data(data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(GuildCommands(bot))
