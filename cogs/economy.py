"""
Core economy commands cog
"""

import discord
from discord.ext import commands
import random
import datetime
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import DataManager, EQUIPABLE_ITEMS

class EconomyCommands(commands.Cog):
    """Core economy commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='balance')
    async def balance(self, ctx):
        """Check wallet & bank balance"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        wallet = data["coins"].get(user_id, 0)
        bank = data["bank"].get(user_id, 0)
        
        embed = discord.Embed(
            title="💰 Balance",
            description=f"**Wallet:** {wallet:,} coins\n**Bank:** {bank:,} coins\n**Total:** {wallet + bank:,} coins",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='daily')
    async def daily(self, ctx):
        """Claim daily reward"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        today = datetime.date.today().isoformat()
        
        if data["last_daily"].get(user_id) == today:
            await ctx.send("❌ You've already claimed your daily reward today!")
            return
        
        # Check for equipped items that might boost daily reward
        equipped = data["equipped"].get(user_id, {})
        boost = 0
        for item_id, quantity in equipped.items():
            if item_id in EQUIPABLE_ITEMS and EQUIPABLE_ITEMS[item_id]["effect"] == "daily_boost":
                boost += EQUIPABLE_ITEMS[item_id]["value"] * quantity
        
        base_amount = data["config"]["daily_amount"]
        amount = int(base_amount * (1 + boost))
        
        # Update data
        data["coins"][user_id] = data["coins"].get(user_id, 0) + amount
        data["last_daily"][user_id] = today
        
        # Add transaction
        if user_id not in data["transactions"]:
            data["transactions"][user_id] = []
        data["transactions"][user_id].append({
            "time": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "type": "credit",
            "amount": amount,
            "reason": f"Daily claim{' (+bonus)' if boost > 0 else ''}"
        })
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"You received **{amount:,} coins**!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='weekly')
    async def weekly(self, ctx):
        """Claim weekly reward"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        now = datetime.datetime.utcnow()
        
        last_weekly = data["last_weekly"].get(user_id)
        if last_weekly:
            last_weekly_dt = datetime.datetime.fromisoformat(last_weekly)
            if (now - last_weekly_dt).days < 7:
                days_left = 7 - (now - last_weekly_dt).days
                await ctx.send(f"❌ You must wait {days_left} more days to claim your weekly reward!")
                return
        
        amount = data["config"]["weekly_amount"]
        
        # Update data
        data["coins"][user_id] = data["coins"].get(user_id, 0) + amount
        data["last_weekly"][user_id] = now.isoformat()
        
        # Add transaction
        if user_id not in data["transactions"]:
            data["transactions"][user_id] = []
        data["transactions"][user_id].append({
            "time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "type": "credit",
            "amount": amount,
            "reason": "Weekly claim"
        })
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="🎊 Weekly Reward Claimed!",
            description=f"You received **{amount:,} coins**!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='pay')
    async def pay(self, ctx, member: discord.Member, amount: int):
        """Send coins directly to another user"""
        if amount <= 0:
            await ctx.send("❌ Amount must be positive!")
            return
        
        data = await DataManager.load_data()
        sender_id = str(ctx.author.id)
        receiver_id = str(member.id)
        
        if data["coins"].get(sender_id, 0) < amount:
            await ctx.send("❌ Insufficient funds!")
            return
        
        # Transfer coins
        data["coins"][sender_id] = data["coins"].get(sender_id, 0) - amount
        data["coins"][receiver_id] = data["coins"].get(receiver_id, 0) + amount
        
        # Add transactions
        for user_id, tx_type, reason in [(sender_id, "debit", f"Payment to {member.display_name}"), 
                                       (receiver_id, "credit", f"Payment from {ctx.author.display_name}")]:
            if user_id not in data["transactions"]:
                data["transactions"][user_id] = []
            data["transactions"][user_id].append({
                "time": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "type": tx_type,
                "amount": amount,
                "reason": reason
            })
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="💸 Payment Sent!",
            description=f"**{ctx.author.display_name}** sent **{amount:,} coins** to **{member.display_name}**!",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='request')
    async def request(self, ctx, member: discord.Member, amount: int):
        """Request money from another user"""
        if amount <= 0:
            await ctx.send("❌ Amount must be positive!")
            return
        
        data = await DataManager.load_data()
        requester_id = str(ctx.author.id)
        target_id = str(member.id)
        
        # Check if target has enough money
        if data["coins"].get(target_id, 0) < amount:
            await ctx.send(f"❌ {member.display_name} doesn't have enough coins!")
            return
        
        embed = discord.Embed(
            title="💰 Money Request",
            description=f"**{ctx.author.display_name}** is requesting **{amount:,} coins** from **{member.display_name}**",
            color=0xffa500
        )
        
        view = RequestView(ctx.author, member, amount)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='rob')
    async def rob(self, ctx, member: discord.Member):
        """Attempt to rob another user"""
        data = await DataManager.load_data()
        robber_id = str(ctx.author.id)
        target_id = str(member.id)
        
        # Check cooldown
        last_rob = data["cooldowns"].get(f"rob_{robber_id}")
        if last_rob:
            last_rob_dt = datetime.datetime.fromisoformat(last_rob)
            cooldown_hours = data["config"]["rob_cooldown_hours"]
            if (datetime.datetime.utcnow() - last_rob_dt).total_seconds() < cooldown_hours * 3600:
                await ctx.send(f"❌ You're on cooldown! Wait {cooldown_hours} hours between robberies.")
                return
        
        # Check if target has money to rob
        target_coins = data["coins"].get(target_id, 0)
        if target_coins < 100:
            await ctx.send(f"❌ {member.display_name} doesn't have enough coins to rob!")
            return
        
        # Check for security dog protection
        target_equipped = data["equipped"].get(target_id, {})
        if "security_dog" in target_equipped:
            await ctx.send(f"🛡️ {member.display_name}'s Security Dog blocked your robbery attempt!")
            data["cooldowns"][f"rob_{robber_id}"] = datetime.datetime.utcnow().isoformat()
            await DataManager.save_data(data)
            return
        
        # Calculate success rate with equipped items
        base_success_rate = data["config"]["rob_success_rate"]
        robber_equipped = data["equipped"].get(robber_id, {})
        success_boost = 0
        for item_id, quantity in robber_equipped.items():
            if item_id in EQUIPABLE_ITEMS and EQUIPABLE_ITEMS[item_id]["effect"] == "rob_boost":
                success_boost += EQUIPABLE_ITEMS[item_id]["value"] * quantity
        
        # Check for active consumable effects
        active_effects = data["consumable_effects"].get(robber_id, {})
        if "rob_boost" in active_effects:
            success_boost += active_effects["rob_boost"]
            del data["consumable_effects"][robber_id]["rob_boost"]
            if not data["consumable_effects"][robber_id]:
                del data["consumable_effects"][robber_id]
        
        success_rate = min(0.8, base_success_rate + success_boost)
        
        if random.random() < success_rate:
            # Successful robbery
            max_steal_percent = data["config"]["rob_max_steal_percent"]
            steal_amount = min(target_coins, int(target_coins * max_steal_percent))
            
            data["coins"][target_id] -= steal_amount
            data["coins"][robber_id] = data["coins"].get(robber_id, 0) + steal_amount
            
            embed = discord.Embed(
                title="🎭 Robbery Successful!",
                description=f"**{ctx.author.display_name}** successfully robbed **{steal_amount:,} coins** from **{member.display_name}**!",
                color=0xff0000
            )
        else:
            # Failed robbery - pay fine
            fine_percent = data["config"]["rob_fine_percent"]
            robber_coins = data["coins"].get(robber_id, 0)
            fine_amount = min(robber_coins, int(target_coins * fine_percent))
            
            data["coins"][robber_id] -= fine_amount
            data["coins"][target_id] += fine_amount
            
            embed = discord.Embed(
                title="🚔 Robbery Failed!",
                description=f"**{ctx.author.display_name}** was caught and fined **{fine_amount:,} coins**! The fine was given to **{member.display_name}**.",
                color=0xff0000
            )
        
        # Set cooldown
        data["cooldowns"][f"rob_{robber_id}"] = datetime.datetime.utcnow().isoformat()
        await DataManager.save_data(data)
        await ctx.send(embed=embed)
    
    @commands.command(name='bank')
    async def bank(self, ctx):
        """View bank and manage deposits/withdrawals"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        wallet = data["coins"].get(user_id, 0)
        bank = data["bank"].get(user_id, 0)
        
        embed = discord.Embed(
            title="🏦 Bank Account",
            description=f"**Wallet:** {wallet:,} coins\n**Bank:** {bank:,} coins",
            color=0x0099ff
        )
        
        view = BankView(ctx.author, self.bot)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='profile')
    async def profile(self, ctx):
        """Show user stats, guild, inventory, and equipped items"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        wallet = data["coins"].get(user_id, 0)
        bank = data["bank"].get(user_id, 0)
        total = wallet + bank
        
        # Get guild info
        guild_name = "None"
        for guild_id, guild_data in data["guilds"].items():
            if user_id in guild_data.get("members", []):
                guild_name = guild_data["name"]
                break
        
        # Get equipped items
        equipped = data["equipped"].get(user_id, {})
        equipped_text = "None"
        if equipped:
            equipped_list = []
            for item_id, quantity in equipped.items():
                if item_id in EQUIPABLE_ITEMS:
                    equipped_list.append(f"{EQUIPABLE_ITEMS[item_id]['name']} (x{quantity})")
            equipped_text = "\n".join(equipped_list) if equipped_list else "None"
        
        # Get inventory count
        inventory = data["inventories"].get(user_id, {})
        total_items = sum(inventory.values())
        
        embed = discord.Embed(
            title=f"👤 {ctx.author.display_name}'s Profile",
            color=0x00ff00
        )
        embed.add_field(name="💰 Wealth", value=f"**Total:** {total:,} coins\nWallet: {wallet:,}\nBank: {bank:,}", inline=True)
        embed.add_field(name="🏰 Guild", value=guild_name, inline=True)
        embed.add_field(name="🎒 Inventory", value=f"{total_items} items", inline=True)
        embed.add_field(name="⚔️ Equipped Items", value=equipped_text[:1024], inline=False)
        
        await ctx.send(embed=embed)

class RequestView(discord.ui.View):
    def __init__(self, requester, target, amount):
        super().__init__(timeout=60)
        self.requester = requester
        self.target = target
        self.amount = amount
    
    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            await interaction.response.send_message("❌ Only the requested user can respond!", ephemeral=True)
            return
        
        data = await DataManager.load_data()
        requester_id = str(self.requester.id)
        target_id = str(self.target.id)
        
        if data["coins"].get(target_id, 0) < self.amount:
            await interaction.response.send_message("❌ You don't have enough coins!")
            return
        
        # Transfer coins
        data["coins"][target_id] -= self.amount
        data["coins"][requester_id] = data["coins"].get(requester_id, 0) + self.amount
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="✅ Request Accepted!",
            description=f"**{self.target.display_name}** sent **{self.amount:,} coins** to **{self.requester.display_name}**!",
            color=0x00ff00
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label='Decline', style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            await interaction.response.send_message("❌ Only the requested user can respond!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="❌ Request Declined",
            description=f"**{self.target.display_name}** declined the money request.",
            color=0xff0000
        )
        await interaction.response.edit_message(embed=embed, view=None)

class BankView(discord.ui.View):
    def __init__(self, user, bot):
        super().__init__(timeout=60)
        self.user = user
        self.bot = bot
    
    @discord.ui.button(label='Deposit', style=discord.ButtonStyle.blurple)
    async def deposit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This is not your bank!", ephemeral=True)
            return
        
        modal = BankModal("deposit", self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Withdraw', style=discord.ButtonStyle.green)
    async def withdraw(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This is not your bank!", ephemeral=True)
            return
        
        modal = BankModal("withdraw", self.bot)
        await interaction.response.send_modal(modal)

class BankModal(discord.ui.Modal):
    def __init__(self, action, bot):
        super().__init__(title=f"Bank {action.title()}")
        self.action = action
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
        
        if self.action == "deposit":
            wallet = data["coins"].get(user_id, 0)
            if wallet < amount:
                await interaction.response.send_message("❌ Insufficient funds in wallet!", ephemeral=True)
                return
            
            data["coins"][user_id] -= amount
            data["bank"][user_id] = data["bank"].get(user_id, 0) + amount
            
            embed = discord.Embed(
                title="💳 Deposit Successful!",
                description=f"Deposited **{amount:,} coins** to your bank account.",
                color=0x00ff00
            )
        else:  # withdraw
            bank = data["bank"].get(user_id, 0)
            if bank < amount:
                await interaction.response.send_message("❌ Insufficient funds in bank!", ephemeral=True)
                return
            
            data["bank"][user_id] -= amount
            data["coins"][user_id] = data["coins"].get(user_id, 0) + amount
            
            embed = discord.Embed(
                title="💸 Withdrawal Successful!",
                description=f"Withdrew **{amount:,} coins** from your bank account.",
                color=0x00ff00
            )
        
        await DataManager.save_data(data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(EconomyCommands(bot))
