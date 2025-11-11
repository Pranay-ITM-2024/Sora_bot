"""
Guild Heist System - Sunday-only guild vs guild bank robberies
Interactive mini-game with risk/reward mechanics
"""
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
from .database import load_data, save_data

# Heist gear bonuses
HEIST_GEAR = {
    "lockpick_pro": {"stealth": 0.15, "speed": 0.10},
    "night_vision_goggles": {"stealth": 0.20, "detection": -0.15},
    "smoke_bomb": {"escape": 0.25, "stealth": 0.10},
    "master_disguise": {"stealth": 0.30, "detection": -0.20},
    "getaway_car": {"escape": 0.30, "speed": 0.15},
    "hacking_device": {"security": 0.25, "speed": 0.10},
    "thermal_drill": {"speed": 0.20, "noise": 0.10},
}

def get_heist_gear_bonuses(user_id, data):
    """Calculate total bonuses from equipped heist gear"""
    equipped = data.get("equipment", {}).get(str(user_id), {})
    inventory = data.get("inventories", {}).get(str(user_id), {})
    
    bonuses = {
        "stealth": 0,
        "speed": 0,
        "escape": 0,
        "detection": 0,
        "security": 0,
        "noise": 0
    }
    
    # Check equipped gear
    for slot, item in equipped.items():
        if item in HEIST_GEAR:
            for bonus_type, value in HEIST_GEAR[item].items():
                bonuses[bonus_type] += value
    
    # Check consumable items in inventory
    for item, count in inventory.items():
        if count > 0 and item in HEIST_GEAR:
            for bonus_type, value in HEIST_GEAR[item].items():
                bonuses[bonus_type] += value * 0.5  # Consumables give 50% bonus
    
    return bonuses

def calculate_heist_difficulty(target_amount, target_guild_bank, bonuses):
    """Calculate heist difficulty based on steal amount and bonuses"""
    # Base difficulty increases with percentage of bank being stolen
    steal_percent = target_amount / max(target_guild_bank, 1)
    base_difficulty = min(0.9, 0.3 + (steal_percent * 0.6))
    
    # Apply bonuses
    stealth_reduction = bonuses.get("stealth", 0) * 0.5
    security_reduction = bonuses.get("security", 0) * 0.3
    
    final_difficulty = max(0.15, base_difficulty - stealth_reduction - security_reduction)
    return final_difficulty, steal_percent

class HeistPhaseView(discord.ui.View):
    """Interactive heist gameplay view"""
    def __init__(self, user_id, guild_name, target_guild, target_amount):
        super().__init__(timeout=180)
        self.user_id = str(user_id)
        self.guild_name = guild_name
        self.target_guild = target_guild
        self.target_amount = target_amount
        self.phase = 1
        self.noise_level = 0
        self.progress = 0
        self.detected = False
        self.completed = False
        
    async def update_heist_display(self, interaction):
        """Update the heist progress display"""
        data = await load_data()
        bonuses = get_heist_gear_bonuses(self.user_id, data)
        
        # Progress bar
        progress_bar = "🟩" * (self.progress // 10) + "⬜" * ((100 - self.progress) // 10)
        noise_bar = "🔴" * (self.noise_level // 20) + "⬜" * ((100 - self.noise_level) // 20)
        
        embed = discord.Embed(
            title=f"🏦 HEIST IN PROGRESS - Phase {self.phase}/3",
            description=f"**Target:** {self.target_guild} Guild Bank\n**Amount:** {self.target_amount:,} coins",
            color=0xff6b35
        )
        
        embed.add_field(
            name="📊 Progress",
            value=f"{progress_bar} {self.progress}%",
            inline=False
        )
        
        embed.add_field(
            name="🔊 Noise Level",
            value=f"{noise_bar} {self.noise_level}%",
            inline=False
        )
        
        if self.phase == 1:
            embed.add_field(
                name="🚪 Phase 1: Entry",
                value="Choose your approach to enter the vault!",
                inline=False
            )
        elif self.phase == 2:
            embed.add_field(
                name="🔓 Phase 2: Cracking the Vault",
                value="Bypass the security systems!",
                inline=False
            )
        elif self.phase == 3:
            embed.add_field(
                name="🏃 Phase 3: Escape",
                value="Get out before you're caught!",
                inline=False
            )
        
        if bonuses["stealth"] > 0:
            embed.add_field(name="🥷 Stealth Bonus", value=f"+{bonuses['stealth']*100:.0f}%", inline=True)
        if bonuses["speed"] > 0:
            embed.add_field(name="⚡ Speed Bonus", value=f"+{bonuses['speed']*100:.0f}%", inline=True)
        
        embed.set_footer(text="⚠️ Higher noise = Higher detection risk!")
        
        return embed
    
    @discord.ui.button(label="🤫 Stealth Approach", style=discord.ButtonStyle.primary, row=0)
    async def stealth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your heist!", ephemeral=True)
            return
        
        data = await load_data()
        bonuses = get_heist_gear_bonuses(self.user_id, data)
        
        # Stealth: Low noise, slower progress
        noise_increase = random.randint(5, 15) - int(bonuses.get("stealth", 0) * 20)
        progress_increase = random.randint(15, 25) + int(bonuses.get("speed", 0) * 10)
        
        self.noise_level = max(0, min(100, self.noise_level + noise_increase))
        self.progress += progress_increase
        
        await self.check_phase_completion(interaction, "stealth")
    
    @discord.ui.button(label="💨 Fast Approach", style=discord.ButtonStyle.danger, row=0)
    async def fast_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your heist!", ephemeral=True)
            return
        
        data = await load_data()
        bonuses = get_heist_gear_bonuses(self.user_id, data)
        
        # Fast: High noise, faster progress
        noise_increase = random.randint(20, 35) - int(bonuses.get("noise", 0) * 15)
        progress_increase = random.randint(30, 45) + int(bonuses.get("speed", 0) * 20)
        
        self.noise_level = max(0, min(100, self.noise_level + noise_increase))
        self.progress += progress_increase
        
        await self.check_phase_completion(interaction, "fast")
    
    @discord.ui.button(label="🛠️ Tech Approach", style=discord.ButtonStyle.secondary, row=0)
    async def tech_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your heist!", ephemeral=True)
            return
        
        data = await load_data()
        bonuses = get_heist_gear_bonuses(self.user_id, data)
        
        # Tech: Medium noise, medium progress, bonus from gear
        noise_increase = random.randint(10, 20) - int(bonuses.get("security", 0) * 25)
        progress_increase = random.randint(20, 35) + int(bonuses.get("security", 0) * 30)
        
        self.noise_level = max(0, min(100, self.noise_level + noise_increase))
        self.progress += progress_increase
        
        await self.check_phase_completion(interaction, "tech")
    
    async def check_phase_completion(self, interaction, approach):
        """Check if phase is complete and handle detection"""
        # Detection check
        detection_chance = (self.noise_level / 100) * 0.8
        
        data = await load_data()
        bonuses = get_heist_gear_bonuses(self.user_id, data)
        detection_chance -= bonuses.get("detection", 0)
        
        if random.random() < detection_chance:
            self.detected = True
            await self.fail_heist(interaction, "detected")
            return
        
        # Phase completion
        if self.progress >= 100:
            self.progress = 0
            self.phase += 1
            
            if self.phase > 3:
                # Heist complete!
                await self.complete_heist(interaction)
                return
        
        # Update display
        embed = await self.update_heist_display(interaction)
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def fail_heist(self, interaction, reason):
        """Handle heist failure"""
        data = await load_data()
        
        # Calculate penalty
        penalty = int(self.target_amount * 0.3)  # 30% of attempted steal
        
        user_coins = data.get("coins", {}).get(self.user_id, 0)
        user_bank = data.get("bank", {}).get(self.user_id, 0)
        total_money = user_coins + user_bank
        
        # Take penalty
        if total_money >= penalty:
            if user_coins >= penalty:
                data.setdefault("coins", {})[self.user_id] = user_coins - penalty
            else:
                data.setdefault("coins", {})[self.user_id] = 0
                data.setdefault("bank", {})[self.user_id] = user_bank - (penalty - user_coins)
        else:
            # Can't afford full penalty - add debt
            debt_amount = penalty - total_money
            data.setdefault("coins", {})[self.user_id] = 0
            data.setdefault("bank", {})[self.user_id] = 0
            data.setdefault("debt", {})[self.user_id] = data.get("debt", {}).get(self.user_id, 0) + debt_amount
        
        # Add to target guild's bank
        target_guild_data = data.get("guilds", {}).get(self.target_guild, {})
        target_guild_data["bank"] = target_guild_data.get("bank", 0) + min(penalty, total_money)
        data.setdefault("guilds", {})[self.target_guild] = target_guild_data
        
        await save_data(data, force=True)
        
        embed = discord.Embed(
            title="🚨 HEIST FAILED!",
            description=f"You were caught during Phase {self.phase}!",
            color=0xff0000
        )
        embed.add_field(name="Reason", value="🚔 Detected by security!" if reason == "detected" else "❌ Operation failed", inline=False)
        embed.add_field(name="Penalty", value=f"-{penalty:,} coins", inline=True)
        embed.add_field(name="Target Compensation", value=f"+{min(penalty, total_money):,} coins to {self.target_guild}", inline=True)
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def complete_heist(self, interaction):
        """Handle successful heist completion"""
        data = await load_data()
        
        # Check if target guild still has the money
        target_guild_data = data.get("guilds", {}).get(self.target_guild, {})
        current_target_bank = target_guild_data.get("bank", 0)
        
        actual_stolen = min(self.target_amount, current_target_bank)
        
        # Deduct from target guild
        target_guild_data["bank"] = current_target_bank - actual_stolen
        data.setdefault("guilds", {})[self.target_guild] = target_guild_data
        
        # Add to attacker's guild
        attacker_guild_data = data.get("guilds", {}).get(self.guild_name, {})
        attacker_guild_data["bank"] = attacker_guild_data.get("bank", 0) + actual_stolen
        data.setdefault("guilds", {})[self.guild_name] = attacker_guild_data
        
        # Add personal reward (10% of stolen amount)
        personal_reward = int(actual_stolen * 0.1)
        data.setdefault("coins", {})[self.user_id] = data.get("coins", {}).get(self.user_id, 0) + personal_reward
        
        await save_data(data, force=True)
        
        embed = discord.Embed(
            title="💰 HEIST SUCCESSFUL!",
            description=f"You successfully robbed the **{self.target_guild}** guild bank!",
            color=0x00ff00
        )
        embed.add_field(name="Guild Earnings", value=f"+{actual_stolen:,} coins", inline=True)
        embed.add_field(name="Personal Cut", value=f"+{personal_reward:,} coins", inline=True)
        embed.add_field(name="Efficiency", value=f"{100 - self.noise_level}%", inline=True)
        embed.set_footer(text="🎉 Clean getaway! The perfect heist!")
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class HeistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="heist", description="🏦 Plan a guild heist! (Sundays only)")
    @app_commands.describe(target_guild="The guild to target", amount="Amount to steal (0 = max 50%)")
    async def heist(self, interaction: discord.Interaction, target_guild: str, amount: int = 0):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        # Check if it's Sunday
        now = datetime.utcnow()
        if now.weekday() != 6:  # 6 = Sunday
            days_until_sunday = (6 - now.weekday()) % 7
            if days_until_sunday == 0:
                days_until_sunday = 7
            await interaction.response.send_message(
                f"🚫 Heists are only available on **Sundays**!\nNext heist day in: **{days_until_sunday} days**",
                ephemeral=True
            )
            return
        
        # Check cooldown (1 heist per Sunday per user)
        cooldowns = data.get("cooldowns", {}).get("heist", {})
        last_heist = cooldowns.get(user_id)
        
        if last_heist:
            last_time = datetime.fromisoformat(last_heist)
            # Check if it's the same Sunday
            if last_time.date() == now.date() and last_time.weekday() == 6:
                await interaction.response.send_message(
                    "⏰ You've already done a heist today! One heist per Sunday per person.",
                    ephemeral=True
                )
                return
        
        # Get user's guild
        user_guild = None
        for guild_name, members in data.get("guild_members", {}).items():
            if user_id in members:
                user_guild = guild_name
                break
        
        if not user_guild:
            await interaction.response.send_message("❌ You must be in a guild to participate in heists!", ephemeral=True)
            return
        
        # Check target guild exists
        if target_guild not in data.get("guilds", {}):
            await interaction.response.send_message(f"❌ Guild **{target_guild}** doesn't exist!", ephemeral=True)
            return
        
        # Can't heist your own guild
        if target_guild == user_guild:
            await interaction.response.send_message("❌ You can't heist your own guild!", ephemeral=True)
            return
        
        # Get target guild bank
        target_guild_data = data.get("guilds", {}).get(target_guild, {})
        target_bank = target_guild_data.get("bank", 0)
        
        if target_bank < 1000:
            await interaction.response.send_message(
                f"❌ **{target_guild}** doesn't have enough in their bank to heist! (Minimum: 1,000 coins)",
                ephemeral=True
            )
            return
        
        # Determine target amount
        if amount <= 0:
            target_amount = int(target_bank * 0.5)  # Default to 50% of bank
        else:
            target_amount = min(amount, int(target_bank * 0.75))  # Max 75%
        
        if target_amount < 100:
            await interaction.response.send_message("❌ Minimum heist amount is 100 coins!", ephemeral=True)
            return
        
        # Calculate difficulty and show preview
        bonuses = get_heist_gear_bonuses(user_id, data)
        difficulty, steal_percent = calculate_heist_difficulty(target_amount, target_bank, bonuses)
        
        embed = discord.Embed(
            title="🏦 HEIST PLANNING",
            description=f"Planning to rob **{target_guild}** guild bank!",
            color=0xff9500
        )
        embed.add_field(name="🎯 Target", value=f"{target_guild}", inline=True)
        embed.add_field(name="💰 Target Bank", value=f"{target_bank:,} coins", inline=True)
        embed.add_field(name="💎 Steal Amount", value=f"{target_amount:,} coins ({steal_percent*100:.1f}%)", inline=True)
        embed.add_field(name="⚠️ Difficulty", value=f"{'🟢 Easy' if difficulty < 0.4 else '🟡 Medium' if difficulty < 0.7 else '🔴 Hard'} ({difficulty*100:.0f}%)", inline=True)
        embed.add_field(name="💸 Penalty on Fail", value=f"{int(target_amount * 0.3):,} coins (30%)", inline=True)
        
        if bonuses["stealth"] > 0 or bonuses["speed"] > 0:
            bonus_text = []
            if bonuses["stealth"] > 0:
                bonus_text.append(f"🥷 Stealth: +{bonuses['stealth']*100:.0f}%")
            if bonuses["speed"] > 0:
                bonus_text.append(f"⚡ Speed: +{bonuses['speed']*100:.0f}%")
            if bonuses["escape"] > 0:
                bonus_text.append(f"🏃 Escape: +{bonuses['escape']*100:.0f}%")
            embed.add_field(name="🎁 Your Bonuses", value="\n".join(bonus_text), inline=False)
        
        embed.set_footer(text="✅ Click Start Heist to begin! You have 3 minutes per phase.")
        
        view = HeistConfirmView(user_id, user_guild, target_guild, target_amount)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class HeistConfirmView(discord.ui.View):
    def __init__(self, user_id, guild_name, target_guild, target_amount):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.guild_name = guild_name
        self.target_guild = target_guild
        self.target_amount = target_amount
    
    @discord.ui.button(label="Start Heist", style=discord.ButtonStyle.success, emoji="🏦")
    async def start_heist(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your heist!", ephemeral=True)
            return
        
        # Set cooldown
        data = await load_data()
        data.setdefault("cooldowns", {}).setdefault("heist", {})[self.user_id] = datetime.utcnow().isoformat()
        await save_data(data)
        
        # Start heist gameplay
        heist_view = HeistPhaseView(self.user_id, self.guild_name, self.target_guild, self.target_amount)
        embed = await heist_view.update_heist_display(interaction)
        await interaction.response.edit_message(embed=embed, view=heist_view)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_heist(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your heist!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="❌ Heist Cancelled",
            description="You decided to call off the heist.",
            color=0x808080
        )
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(HeistCog(bot))
