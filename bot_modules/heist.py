"""
Guild Heist System - Sunday-only guild vs guild bank robberies
Multiplayer role-based interactive heist system (2-5 players) or solo heists
Features interactive minigames for each role
"""
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
from .database import load_data, save_data, get_server_data, save_server_data

# ==================== MINIGAME MODALS ====================

class HackingMinigameModal(discord.ui.Modal, title="🔓 Bypass Security System"):
    """Hacker role minigame - solve a code pattern"""
    def __init__(self, callback_func, user_id, role):
        super().__init__()
        self.callback_func = callback_func
        self.user_id = user_id
        self.role = role
        
        # Generate a simple pattern challenge
        self.pattern = [random.randint(1, 9) for _ in range(4)]
        self.answer = str(sum(self.pattern))
        
        self.add_item(discord.ui.TextInput(
            label=f"Crack the Code: {' + '.join(map(str, self.pattern))} = ?",
            placeholder="Enter the sum",
            required=True,
            max_length=3
        ))
    
    async def on_submit(self, interaction: discord.Interaction):
        user_answer = self.children[0].value.strip()
        success = user_answer == self.answer
        await self.callback_func(interaction, self.user_id, self.role, success, "hacking")

class LockpickMinigameModal(discord.ui.Modal, title="🔐 Pick the Lock"):
    """Muscle/Leader role minigame - guess the combination"""
    def __init__(self, callback_func, user_id, role):
        super().__init__()
        self.callback_func = callback_func
        self.user_id = user_id
        self.role = role
        
        # Generate 3-digit code
        self.code = [random.randint(1, 5) for _ in range(3)]
        hint = f"Hint: digits are between 1-5, sum is {sum(self.code)}"
        
        self.add_item(discord.ui.TextInput(
            label=f"Enter 3-digit combination (e.g., 234)",
            placeholder=hint,
            required=True,
            min_length=3,
            max_length=3
        ))
    
    async def on_submit(self, interaction: discord.Interaction):
        user_answer = self.children[0].value.strip()
        try:
            user_code = [int(d) for d in user_answer]
            # Give partial credit if close
            if user_code == self.code:
                success = True
            elif sum(user_code) == sum(self.code):
                success = random.random() < 0.7  # 70% chance if sum is correct
            else:
                success = random.random() < 0.4  # 40% base chance
        except:
            success = False
        
        await self.callback_func(interaction, self.user_id, self.role, success, "lockpick")

class PatternMatchModal(discord.ui.Modal, title="🎯 Match the Pattern"):
    """Scout role minigame - pattern recognition"""
    def __init__(self, callback_func, user_id, role):
        super().__init__()
        self.callback_func = callback_func
        self.user_id = user_id
        self.role = role
        
        # Generate pattern
        symbols = ['🔴', '🔵', '🟢', '🟡']
        pattern_length = 4
        self.pattern = [random.choice(symbols) for _ in range(pattern_length)]
        self.answer = ''.join(self.pattern)
        
        self.add_item(discord.ui.TextInput(
            label=f"Memorize and type: {' '.join(self.pattern)}",
            placeholder="Type the emojis in order (copy-paste allowed)",
            required=True,
            max_length=20
        ))
    
    async def on_submit(self, interaction: discord.Interaction):
        user_answer = self.children[0].value.strip().replace(' ', '')
        # Allow some flexibility
        success = user_answer == self.answer or user_answer in self.answer
        await self.callback_func(interaction, self.user_id, self.role, success, "pattern")

class ReactionSpeedView(discord.ui.View):
    """Driver role minigame - reaction speed test"""
    def __init__(self, callback_func, user_id, role, correct_button):
        super().__init__(timeout=8)
        self.callback_func = callback_func
        self.user_id = user_id
        self.role = role
        self.correct_button = correct_button
        self.start_time = asyncio.get_event_loop().time()
        self.responded = False
        
        # Add 4 buttons, one is correct
        colors = [discord.ButtonStyle.red, discord.ButtonStyle.blurple, discord.ButtonStyle.green, discord.ButtonStyle.grey]
        labels = ["LEFT", "MIDDLE", "RIGHT", "STOP"]
        
        for i in range(4):
            button = discord.ui.Button(
                style=colors[i],
                label=labels[i],
                custom_id=f"speed_{i}"
            )
            button.callback = self.button_callback
            self.add_item(button)
    
    async def button_callback(self, interaction: discord.Interaction):
        if self.responded:
            await interaction.response.send_message("❌ Already responded!", ephemeral=True)
            return
        
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your minigame!", ephemeral=True)
            return
        
        self.responded = True
        button_index = int(interaction.data["custom_id"].split("_")[1])
        reaction_time = asyncio.get_event_loop().time() - self.start_time
        
        # Success if correct button AND fast enough (within 5 seconds)
        success = button_index == self.correct_button and reaction_time < 5.0
        
        await self.callback_func(interaction, self.user_id, self.role, success, "reaction")
        self.stop()
    
    async def on_timeout(self):
        self.responded = True

class MathChallengeModal(discord.ui.Modal, title="🧮 Quick Calculation"):
    """Leader role minigame - mental math"""
    def __init__(self, callback_func, user_id, role):
        super().__init__()
        self.callback_func = callback_func
        self.user_id = user_id
        self.role = role
        
        # Generate math problem
        num1 = random.randint(10, 50)
        num2 = random.randint(10, 50)
        operation = random.choice(['+', '-', '*'])
        
        if operation == '+':
            self.answer = num1 + num2
        elif operation == '-':
            self.answer = num1 - num2
        else:  # multiplication
            num1 = random.randint(5, 15)
            num2 = random.randint(5, 15)
            self.answer = num1 * num2
        
        self.problem = f"{num1} {operation} {num2}"
        
        self.add_item(discord.ui.TextInput(
            label=f"Solve: {self.problem} = ?",
            placeholder="Enter the answer",
            required=True,
            max_length=5
        ))
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_answer = int(self.children[0].value.strip())
            success = user_answer == self.answer
        except:
            success = False
        
        await self.callback_func(interaction, self.user_id, self.role, success, "math")

# ==================== HEIST SYSTEM ====================

# Heist roles and their tasks
HEIST_ROLES = {
    "Leader": {
        "emoji": "👔",
        "description": "Coordinates the team and makes critical decisions",
        "tasks": ["Coordinate", "Adapt", "Command"],
        "bonus_type": "coordination"
    },
    "Hacker": {
        "emoji": "💻",
        "description": "Disables security systems and cameras",
        "tasks": ["Bypass Security", "Disable Alarms", "Loop Cameras"],
        "bonus_type": "security"
    },
    "Muscle": {
        "emoji": "💪",
        "description": "Breaks into the vault and handles obstacles",
        "tasks": ["Break Vault", "Clear Path", "Force Entry"],
        "bonus_type": "speed"
    },
    "Driver": {
        "emoji": "🚗",
        "description": "Manages the escape and getaway",
        "tasks": ["Plan Escape", "Ready Vehicle", "Drive Away"],
        "bonus_type": "escape"
    },
    "Scout": {
        "emoji": "👁️",
        "description": "Monitors surroundings and detects threats",
        "tasks": ["Watch Guards", "Check Routes", "Monitor Police"],
        "bonus_type": "stealth"
    }
}

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
        "noise": 0,
        "coordination": 0
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

def get_team_bonuses(team_members, data):
    """Calculate combined team bonuses from all members' gear"""
    team_bonuses = {
        "stealth": 0,
        "speed": 0,
        "escape": 0,
        "detection": 0,
        "security": 0,
        "coordination": 0
    }
    
    for member_id in team_members:
        member_bonuses = get_heist_gear_bonuses(str(member_id), data)
        for bonus_type, value in member_bonuses.items():
            if bonus_type != "noise":  # Noise doesn't stack positively
                team_bonuses[bonus_type] += value * 0.6  # 60% effectiveness when in team
    
    return team_bonuses

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

class HeistMemberSelectView(discord.ui.View):
    """View for guild leader to select heist team members"""
    def __init__(self, leader_id, guild_name, target_guild, target_amount, guild_members, bot, discord_guild_id):
        super().__init__(timeout=120)
        self.leader_id = str(leader_id)
        self.guild_name = guild_name
        self.target_guild = target_guild
        self.target_amount = target_amount
        self.guild_members = guild_members
        self.bot = bot
        self.discord_guild_id = str(discord_guild_id)
        self.selected_members = [str(leader_id)]  # Leader is always included
        
        # Add member selection dropdown
        self.add_member_select()
    
    def add_member_select(self):
        """Add dropdown for selecting guild members"""
        options = []
        
        # Add all guild members except leader (max 24 to leave room for leader)
        for member_id in self.guild_members[:24]:
            if member_id != self.leader_id:
                try:
                    options.append(
                        discord.SelectOption(
                            label=f"Member {member_id[-4:]}",  # Show last 4 digits
                            value=member_id,
                            description="Guild member",
                            emoji="👤"
                        )
                    )
                except:
                    pass
        
        if options:
            select = discord.ui.Select(
                placeholder="Select team members (1-4 additional members)...",
                min_values=1,
                max_values=min(4, len(options)),  # Max 4 additional members (leader makes 5 total)
                options=options,
                custom_id="member_select"
            )
            select.callback = self.member_selected
            self.add_item(select)
    
    async def member_selected(self, interaction: discord.Interaction):
        """Handle member selection"""
        if str(interaction.user.id) != self.leader_id:
            await interaction.response.send_message("❌ Only the leader can select team members!", ephemeral=True)
            return
        
        # Update selected members (leader + selected)
        self.selected_members = [self.leader_id] + interaction.data["values"]
        
        await interaction.response.send_message(
            f"✅ Selected {len(self.selected_members)} members for the heist team!",
            ephemeral=True
        )
    
    @discord.ui.button(label="Confirm Team & Proceed", style=discord.ButtonStyle.success, emoji="✅", row=4)
    async def confirm_team(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.leader_id:
            await interaction.response.send_message("❌ Only the leader can confirm!", ephemeral=True)
            return
        
        if len(self.selected_members) < 2:
            await interaction.response.send_message("❌ Select at least 1 additional member (2 total minimum)!", ephemeral=True)
            return
        
        # Create team dict for role selection
        team = {member_id: None for member_id in self.selected_members}
        
        # Move to role selection
        role_view = HeistRoleSelectView(self.leader_id, self.guild_name, self.target_guild, self.target_amount, team, self.discord_guild_id)
        embed = role_view.create_role_select_embed()
        await interaction.response.edit_message(embed=embed, view=role_view)

class HeistRoleSelectView(discord.ui.View):
    """View for selecting roles for heist team"""
    def __init__(self, leader_id, guild_name, target_guild, target_amount, team, discord_guild_id):
        super().__init__(timeout=120)
        self.leader_id = str(leader_id)
        self.guild_name = guild_name
        self.target_guild = target_guild
        self.target_amount = target_amount
        self.team = team  # user_id: role (None initially)
        self.discord_guild_id = str(discord_guild_id)
        self.add_role_selects()
    
    def add_role_selects(self):
        """Add dropdown for each team member"""
        for user_id in self.team.keys():
            select = discord.ui.Select(
                placeholder=f"Select role for <@{user_id}>",
                options=[
                    discord.SelectOption(
                        label=role,
                        value=f"{user_id}:{role}",
                        emoji=HEIST_ROLES[role]["emoji"],
                        description=HEIST_ROLES[role]["description"]
                    ) for role in HEIST_ROLES.keys()
                ],
                custom_id=f"role_select_{user_id}"
            )
            select.callback = self.role_selected
            self.add_item(select)
        
        # Add confirm button
        confirm_button = discord.ui.Button(label="Confirm Roles & Start", style=discord.ButtonStyle.success, emoji="✅", row=4)
        confirm_button.callback = self.confirm_roles
        self.add_item(confirm_button)
    
    async def role_selected(self, interaction: discord.Interaction):
        """Handle role selection"""
        select_value = interaction.data["values"][0]
        user_id, role = select_value.split(":")
        
        # Check if role is already taken
        if role in self.team.values():
            await interaction.response.send_message(f"❌ {role} role is already taken!", ephemeral=True)
            return
        
        # Assign role
        self.team[user_id] = role
        await interaction.response.send_message(f"✅ Assigned **{role}** role!", ephemeral=True)
    
    async def confirm_roles(self, interaction: discord.Interaction):
        """Confirm roles and start heist"""
        if str(interaction.user.id) != self.leader_id:
            await interaction.response.send_message("❌ Only the leader can confirm roles!", ephemeral=True)
            return
        
        # Check all roles assigned
        if None in self.team.values():
            await interaction.response.send_message("❌ All team members must have a role assigned!", ephemeral=True)
            return
        
        # Set GUILD cooldown (one heist per guild per Sunday)
        data = await load_data()
        server_data = get_server_data(data, self.discord_guild_id)
        server_data.setdefault("cooldowns", {}).setdefault("guild_heist", {})[self.guild_name] = datetime.utcnow().isoformat()
        save_server_data(data, self.discord_guild_id, server_data)
        await save_data(data)
        
        # Start multiplayer heist
        heist_view = MultiplayerHeistView(self.leader_id, self.guild_name, self.target_guild, self.target_amount, self.team, self.discord_guild_id)
        embed = await heist_view.create_phase_embed()
        await interaction.response.edit_message(embed=embed, view=heist_view)
    
    def create_role_select_embed(self):
        """Create role selection embed"""
        embed = discord.Embed(
            title="🎭 HEIST ROLE SELECTION",
            description=f"**Leader:** <@{self.leader_id}>\nAssign roles to each team member!",
            color=0x9b59b6
        )
        
        # Show available roles
        roles_text = ""
        for role_name, role_info in HEIST_ROLES.items():
            roles_text += f"{role_info['emoji']} **{role_name}**: {role_info['description']}\n"
        
        embed.add_field(name="Available Roles", value=roles_text, inline=False)
        embed.set_footer(text="Select a role for each member using the dropdowns, then confirm!")
        
        return embed

class MultiplayerHeistView(discord.ui.View):
    """Multiplayer heist gameplay with role-based tasks"""
    def __init__(self, leader_id, guild_name, target_guild, target_amount, team, discord_guild_id):
        super().__init__(timeout=300)
        self.leader_id = str(leader_id)
        self.guild_name = guild_name
        self.target_guild = target_guild
        self.target_amount = target_amount
        self.team = team  # user_id: role
        self.discord_guild_id = str(discord_guild_id)
        self.phase = 1
        self.noise_level = 0
        self.team_progress = {uid: 0 for uid in team.keys()}  # Individual progress
        self.failed_members = set()
        self.completed = False
        
    async def create_phase_embed(self):
        """Create the heist phase display"""
        data = await load_data()
        server_data = get_server_data(data, self.discord_guild_id)
        team_bonuses = get_team_bonuses(self.team.keys(), server_data)
        
        # Calculate team progress (average)
        total_progress = sum(self.team_progress.values())
        avg_progress = total_progress // len(self.team)
        
        # Progress bar
        progress_bar = "🟩" * (avg_progress // 10) + "⬜" * ((100 - avg_progress) // 10)
        noise_bar = "🔴" * (self.noise_level // 20) + "⬜" * ((100 - self.noise_level) // 20)
        
        phase_names = ["🚪 Entry", "🔓 Vault Breach", "🏃 Escape"]
        
        embed = discord.Embed(
            title=f"🏦 MULTIPLAYER HEIST - Phase {self.phase}/3: {phase_names[self.phase-1]}",
            description=f"**Target:** {self.target_guild} Guild Bank\n**Amount:** {self.target_amount:,} coins\n**Team Size:** {len(self.team)} players",
            color=0xff6b35
        )
        
        embed.add_field(
            name="📊 Team Progress",
            value=f"{progress_bar} {avg_progress}%",
            inline=False
        )
        
        embed.add_field(
            name="🔊 Noise Level",
            value=f"{noise_bar} {self.noise_level}%",
            inline=False
        )
        
        # Show individual tasks
        task_text = ""
        for user_id, role in self.team.items():
            role_info = HEIST_ROLES[role]
            task = role_info["tasks"][self.phase - 1]
            progress = self.team_progress[user_id]
            status = "❌" if user_id in self.failed_members else "🔄" if progress < 100 else "✅"
            task_text += f"{role_info['emoji']} <@{user_id}> ({role}): {task} {status} {progress}%\n"
        
        embed.add_field(name="� Team Tasks", value=task_text, inline=False)
        
        if team_bonuses["stealth"] > 0:
            embed.add_field(name="🥷 Team Stealth", value=f"+{team_bonuses['stealth']*100:.0f}%", inline=True)
        if team_bonuses["speed"] > 0:
            embed.add_field(name="⚡ Team Speed", value=f"+{team_bonuses['speed']*100:.0f}%", inline=True)
        
        embed.set_footer(text="⚠️ If ANY member fails their task, the entire heist fails!")
        
        return embed
    
    @discord.ui.button(label="Complete Task", style=discord.ButtonStyle.primary, emoji="⚡", row=0)
    async def complete_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        
        # Check if user is in team
        if user_id not in self.team:
            await interaction.response.send_message("❌ You're not part of this heist!", ephemeral=True)
            return
        
        # Check if already failed
        if user_id in self.failed_members:
            await interaction.response.send_message("❌ You've already failed your task!", ephemeral=True)
            return
        
        # Check if already completed
        if self.team_progress[user_id] >= 100:
            await interaction.response.send_message("✅ You've already completed your task!", ephemeral=True)
            return
        
        # Launch role-specific minigame
        role = self.team[user_id]
        
        if role == "Hacker":
            modal = HackingMinigameModal(self.minigame_callback, user_id, role)
            await interaction.response.send_modal(modal)
        elif role == "Leader":
            modal = MathChallengeModal(self.minigame_callback, user_id, role)
            await interaction.response.send_modal(modal)
        elif role == "Muscle":
            modal = LockpickMinigameModal(self.minigame_callback, user_id, role)
            await interaction.response.send_modal(modal)
        elif role == "Scout":
            modal = PatternMatchModal(self.minigame_callback, user_id, role)
            await interaction.response.send_modal(modal)
        elif role == "Driver":
            # Driver gets a reaction speed test (button-based)
            correct_button = random.randint(0, 3)
            button_names = ["LEFT", "MIDDLE", "RIGHT", "STOP"]
            
            speed_view = ReactionSpeedView(self.minigame_callback, user_id, role, correct_button)
            
            await interaction.response.send_message(
                f"🚗 **QUICK!** Press the **{button_names[correct_button]}** button!",
                view=speed_view,
                ephemeral=True
            )
    
    async def minigame_callback(self, interaction: discord.Interaction, user_id, role, success, minigame_type):
        """Handle minigame results and update heist progress"""
        data = await load_data()
        role_info = HEIST_ROLES[role]
        bonus_type = role_info["bonus_type"]
        
        # Get bonuses
        personal_bonuses = get_heist_gear_bonuses(user_id, data)
        team_bonuses = get_team_bonuses(self.team.keys(), data)
        role_bonus = personal_bonuses.get(bonus_type, 0) + team_bonuses.get(bonus_type, 0) * 0.3
        
        if success:
            # Success! Progress increases
            progress_gain = random.randint(25, 40) + int(role_bonus * 50)
            self.team_progress[user_id] = min(100, self.team_progress[user_id] + progress_gain)
            
            # Add noise based on action
            noise_gain = random.randint(5, 15) - int(personal_bonuses.get("stealth", 0) * 20)
            self.noise_level = max(0, min(100, self.noise_level + noise_gain))
            
            minigame_names = {
                "hacking": "hacked the system",
                "lockpick": "picked the lock",
                "pattern": "spotted the guards",
                "reaction": "drove away quickly",
                "math": "made the right call"
            }
            
            await interaction.response.send_message(
                f"✅ Success! You {minigame_names.get(minigame_type, 'completed the task')}!\n"
                f"Progress: +{progress_gain}% | Noise: +{max(0, noise_gain)}%",
                ephemeral=True
            )
        else:
            # Failure! Entire heist fails
            self.failed_members.add(user_id)
            await self.fail_heist(interaction, user_id, role)
            return
        
        # Check if phase complete (all members at 100%)
        if all(progress >= 100 for progress in self.team_progress.values()):
            self.phase += 1
            if self.phase > 3:
                # Heist complete!
                await self.complete_heist(interaction)
                return
            else:
                # Reset progress for next phase
                self.team_progress = {uid: 0 for uid in self.team.keys()}
        
        # Update display
        embed = await self.create_phase_embed()
        
        # Get the original message
        original_message = interaction.message if hasattr(interaction, 'message') else None
        if not original_message:
            # Find the message from the interaction's channel
            async for msg in interaction.channel.history(limit=20):
                if msg.author.id == interaction.client.user.id and msg.embeds:
                    if "MULTIPLAYER HEIST" in msg.embeds[0].title:
                        original_message = msg
                        break
        
        if original_message:
            await original_message.edit(embed=embed, view=self)
    
    async def fail_heist(self, interaction, failed_user_id, failed_role):
        """Handle multiplayer heist failure"""
        data = await load_data()
        server_data = get_server_data(data, self.discord_guild_id)
        
        # Calculate penalty (split among team)
        total_penalty = int(self.target_amount * 0.3)  # 30% of attempted steal
        penalty_per_person = total_penalty // len(self.team)
        
        total_paid = 0
        penalty_details = []
        
        # Charge each team member
        for user_id in self.team.keys():
            user_coins = server_data.get("coins", {}).get(user_id, 0)
            user_bank = server_data.get("bank", {}).get(user_id, 0)
            total_money = user_coins + user_bank
            
            # Take penalty
            if total_money >= penalty_per_person:
                if user_coins >= penalty_per_person:
                    server_data.setdefault("coins", {})[user_id] = user_coins - penalty_per_person
                else:
                    server_data.setdefault("coins", {})[user_id] = 0
                    server_data.setdefault("bank", {})[user_id] = user_bank - (penalty_per_person - user_coins)
                total_paid += penalty_per_person
                penalty_details.append(f"<@{user_id}>: -{penalty_per_person:,} coins")
            else:
                # Can't afford full penalty - add debt
                debt_amount = penalty_per_person - total_money
                server_data.setdefault("coins", {})[user_id] = 0
                server_data.setdefault("bank", {})[user_id] = 0
                server_data.setdefault("debt", {})[user_id] = server_data.get("debt", {}).get(user_id, 0) + debt_amount
                total_paid += total_money
                penalty_details.append(f"<@{user_id}>: -{total_money:,} coins + {debt_amount:,} debt")
        
        # Pay to target guild's bank
        target_guild_data = server_data.get("guilds", {}).get(self.target_guild, {})
        target_guild_data["bank"] = target_guild_data.get("bank", 0) + total_paid
        server_data.setdefault("guilds", {})[self.target_guild] = target_guild_data
        
        save_server_data(data, self.discord_guild_id, server_data)
        await save_data(data, force=True)
        
        embed = discord.Embed(
            title="🚨 HEIST FAILED!",
            description=f"**<@{failed_user_id}>** ({failed_role}) failed their task!\n\nThe entire heist has been compromised!",
            color=0xff0000
        )
        embed.add_field(name=f"⚠️ Phase {self.phase} Failure", value=f"Task: {HEIST_ROLES[failed_role]['tasks'][self.phase-1]}", inline=False)
        embed.add_field(name="💸 Team Penalties", value="\n".join(penalty_details), inline=False)
        embed.add_field(name="🏦 Target Compensation", value=f"+{total_paid:,} coins to **{self.target_guild}**", inline=False)
        embed.set_footer(text="Better luck next time! Remember: One failure ruins it for everyone!")
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def complete_heist(self, interaction):
        """Handle successful multiplayer heist completion"""
        data = await load_data()
        server_data = get_server_data(data, self.discord_guild_id)
        
        # Check if target guild still has the money
        target_guild_data = server_data.get("guilds", {}).get(self.target_guild, {})
        current_target_bank = target_guild_data.get("bank", 0)
        
        actual_stolen = min(self.target_amount, current_target_bank)
        
        # Deduct from target guild
        target_guild_data["bank"] = current_target_bank - actual_stolen
        server_data.setdefault("guilds", {})[self.target_guild] = target_guild_data
        
        # Add to attacker's guild
        attacker_guild_data = server_data.get("guilds", {}).get(self.guild_name, {})
        attacker_guild_data["bank"] = attacker_guild_data.get("bank", 0) + actual_stolen
        server_data.setdefault("guilds", {})[self.guild_name] = attacker_guild_data
        
        # Distribute personal rewards (10% split among team)
        total_personal_reward = int(actual_stolen * 0.1)
        reward_per_person = total_personal_reward // len(self.team)
        
        reward_details = []
        for user_id in self.team.keys():
            server_data.setdefault("coins", {})[user_id] = server_data.get("coins", {}).get(user_id, 0) + reward_per_person
            reward_details.append(f"<@{user_id}>: +{reward_per_person:,} coins")
        
        save_server_data(data, self.discord_guild_id, server_data)
        await save_data(data, force=True)
        
        embed = discord.Embed(
            title="💰 HEIST SUCCESSFUL!",
            description=f"Your team successfully robbed the **{self.target_guild}** guild bank!",
            color=0x00ff00
        )
        embed.add_field(name="🏦 Guild Earnings", value=f"+{actual_stolen:,} coins", inline=False)
        embed.add_field(name="💎 Team Rewards", value="\n".join(reward_details), inline=False)
        embed.add_field(name="⭐ Efficiency", value=f"{100 - self.noise_level}%", inline=True)
        embed.add_field(name="👥 Team Size", value=f"{len(self.team)} players", inline=True)
        embed.set_footer(text="🎉 Perfect teamwork! Clean getaway!")
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class SoloHeistView(discord.ui.View):
    """Solo heist gameplay for single player"""
    def __init__(self, user_id, guild_name, target_guild, target_amount, discord_guild_id):
        super().__init__(timeout=180)
        self.user_id = str(user_id)
        self.guild_name = guild_name
        self.target_guild = target_guild
        self.target_amount = target_amount
        self.discord_guild_id = str(discord_guild_id)
        self.phase = 1
        self.noise_level = 0
        self.progress = 0
    
    async def create_solo_embed(self):
        """Create solo heist display"""
        data = await load_data()
        server_data = get_server_data(data, self.discord_guild_id)
        bonuses = get_heist_gear_bonuses(self.user_id, server_data)
        
        progress_bar = "🟩" * (self.progress // 10) + "⬜" * ((100 - self.progress) // 10)
        noise_bar = "🔴" * (self.noise_level // 20) + "⬜" * ((100 - self.noise_level) // 20)
        
        phase_names = ["🚪 Entry", "🔓 Vault Breach", "🏃 Escape"]
        
        embed = discord.Embed(
            title=f"🏦 SOLO HEIST - Phase {self.phase}/3: {phase_names[self.phase-1]}",
            description=f"**Target:** {self.target_guild} Guild Bank\n**Amount:** {self.target_amount:,} coins",
            color=0xff6b35
        )
        
        embed.add_field(name="📊 Progress", value=f"{progress_bar} {self.progress}%", inline=False)
        embed.add_field(name="🔊 Noise Level", value=f"{noise_bar} {self.noise_level}%", inline=False)
        
        if bonuses["stealth"] > 0:
            embed.add_field(name="🥷 Stealth", value=f"+{bonuses['stealth']*100:.0f}%", inline=True)
        if bonuses["speed"] > 0:
            embed.add_field(name="⚡ Speed", value=f"+{bonuses['speed']*100:.0f}%", inline=True)
        
        embed.set_footer(text="Choose your approach wisely!")
        
        return embed
    
    @discord.ui.button(label="🤫 Stealth", style=discord.ButtonStyle.primary, row=0)
    async def stealth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your heist!", ephemeral=True)
            return
        
        # Stealth approach uses pattern matching (Scout-style)
        modal = PatternMatchModal(self.solo_minigame_callback, self.user_id, "stealth")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="💨 Fast", style=discord.ButtonStyle.danger, row=0)
    async def fast_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your heist!", ephemeral=True)
            return
        
        # Fast approach uses reaction speed (Driver-style)
        correct_button = random.randint(0, 3)
        button_names = ["LEFT", "MIDDLE", "RIGHT", "STOP"]
        
        speed_view = ReactionSpeedView(self.solo_minigame_callback, self.user_id, "fast", correct_button)
        
        await interaction.response.send_message(
            f"💨 **RUSH!** Press the **{button_names[correct_button]}** button NOW!",
            view=speed_view,
            ephemeral=True
        )
    
    @discord.ui.button(label="🛠️ Tech", style=discord.ButtonStyle.secondary, row=0)
    async def tech_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your heist!", ephemeral=True)
            return
        
        # Tech approach uses hacking/lockpicking
        if random.choice([True, False]):
            modal = HackingMinigameModal(self.solo_minigame_callback, self.user_id, "tech")
        else:
            modal = LockpickMinigameModal(self.solo_minigame_callback, self.user_id, "tech")
        
        await interaction.response.send_modal(modal)
    
    async def solo_minigame_callback(self, interaction: discord.Interaction, user_id, approach, success, minigame_type):
        """Handle solo minigame results"""
        data = await load_data()
        bonuses = get_heist_gear_bonuses(self.user_id, data)
        
        if success:
            # Calculate progress and noise based on approach
            if approach == "stealth":
                noise_increase = random.randint(5, 15) - int(bonuses.get("stealth", 0) * 20)
                progress_increase = random.randint(15, 25) + int(bonuses.get("speed", 0) * 10)
            elif approach == "fast":
                noise_increase = random.randint(20, 35) - int(bonuses.get("noise", 0) * 15)
                progress_increase = random.randint(30, 45) + int(bonuses.get("speed", 0) * 20)
            else:  # tech
                noise_increase = random.randint(10, 20) - int(bonuses.get("security", 0) * 25)
                progress_increase = random.randint(20, 35) + int(bonuses.get("security", 0) * 30)
            
            self.noise_level = max(0, min(100, self.noise_level + noise_increase))
            self.progress += progress_increase
            
            await interaction.response.send_message(
                f"✅ Success! Progress: +{progress_increase}% | Noise: +{max(0, noise_increase)}%",
                ephemeral=True
            )
            
            await self.check_solo_phase(interaction)
        else:
            # Failed minigame = detected
            await interaction.response.send_message(
                f"❌ Failed! You made too much noise and were detected!",
                ephemeral=True
            )
            await self.fail_solo_heist(interaction)
    
    async def check_solo_phase(self, interaction):
        """Check phase progression and detection"""
        # Detection check
        detection_chance = (self.noise_level / 100) * 0.8
        data = await load_data()
        bonuses = get_heist_gear_bonuses(self.user_id, data)
        detection_chance -= bonuses.get("detection", 0)
        
        if random.random() < detection_chance:
            await self.fail_solo_heist(interaction)
            return
        
        # Phase completion
        if self.progress >= 100:
            self.progress = 0
            self.phase += 1
            
            if self.phase > 3:
                await self.complete_solo_heist(interaction)
                return
        
        # Update display - find the original heist message
        embed = await self.create_solo_embed()
        
        # Try to find the heist message
        original_message = None
        async for msg in interaction.channel.history(limit=20):
            if msg.author.id == interaction.client.user.id and msg.embeds:
                if "SOLO HEIST" in msg.embeds[0].title:
                    original_message = msg
                    break
        
        if original_message:
            await original_message.edit(embed=embed, view=self)
    
    async def fail_solo_heist(self, interaction):
        """Handle solo heist failure"""
        data = await load_data()
        
        penalty = int(self.target_amount * 0.3)
        
        user_coins = data.get("coins", {}).get(self.user_id, 0)
        user_bank = data.get("bank", {}).get(self.user_id, 0)
        total_money = user_coins + user_bank
        
        if total_money >= penalty:
            if user_coins >= penalty:
                data.setdefault("coins", {})[self.user_id] = user_coins - penalty
            else:
                data.setdefault("coins", {})[self.user_id] = 0
                data.setdefault("bank", {})[self.user_id] = user_bank - (penalty - user_coins)
            paid = penalty
        else:
            debt_amount = penalty - total_money
            data.setdefault("coins", {})[self.user_id] = 0
            data.setdefault("bank", {})[self.user_id] = 0
            data.setdefault("debt", {})[self.user_id] = data.get("debt", {}).get(self.user_id, 0) + debt_amount
            paid = total_money
        
        target_guild_data = data.get("guilds", {}).get(self.target_guild, {})
        target_guild_data["bank"] = target_guild_data.get("bank", 0) + paid
        data.setdefault("guilds", {})[self.target_guild] = target_guild_data
        
        await save_data(data, force=True)
        
        embed = discord.Embed(
            title="🚨 HEIST FAILED!",
            description=f"You were detected during Phase {self.phase}!",
            color=0xff0000
        )
        embed.add_field(name="💸 Penalty", value=f"-{penalty:,} coins", inline=True)
        embed.add_field(name="� Paid to Target", value=f"+{paid:,} coins to {self.target_guild}", inline=True)
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def complete_solo_heist(self, interaction):
        """Handle solo heist success"""
        data = await load_data()
        server_data = get_server_data(data, self.discord_guild_id)
        
        target_guild_data = server_data.get("guilds", {}).get(self.target_guild, {})
        current_target_bank = target_guild_data.get("bank", 0)
        
        actual_stolen = min(self.target_amount, current_target_bank)
        
        target_guild_data["bank"] = current_target_bank - actual_stolen
        server_data.setdefault("guilds", {})[self.target_guild] = target_guild_data
        
        attacker_guild_data = server_data.get("guilds", {}).get(self.guild_name, {})
        attacker_guild_data["bank"] = attacker_guild_data.get("bank", 0) + actual_stolen
        server_data.setdefault("guilds", {})[self.guild_name] = attacker_guild_data
        
        personal_reward = int(actual_stolen * 0.1)
        server_data.setdefault("coins", {})[self.user_id] = server_data.get("coins", {}).get(self.user_id, 0) + personal_reward
        
        save_server_data(data, self.discord_guild_id, server_data)
        await save_data(data, force=True)
        
        embed = discord.Embed(
            title="💰 HEIST SUCCESSFUL!",
            description=f"You successfully robbed the **{self.target_guild}** guild bank!",
            color=0x00ff00
        )
        embed.add_field(name="Guild Earnings", value=f"+{actual_stolen:,} coins", inline=True)
        embed.add_field(name="Personal Cut", value=f"+{personal_reward:,} coins", inline=True)
        embed.add_field(name="Efficiency", value=f"{100 - self.noise_level}%", inline=True)
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class HeistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="heist", description="🏦 Plan a guild heist! (Sundays only - Guild Leaders only)")
    @app_commands.describe(target_guild="The guild to target", amount="Amount to steal (0 = max 50%)")
    async def heist(self, interaction: discord.Interaction, target_guild: str, amount: int = 0):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        data = await load_data()
        server_data = get_server_data(data, guild_id)
        
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
        
        # Get user's guild
        user_guild = None
        guild_members = []
        for guild_name, members in server_data.get("guild_members", {}).items():
            if user_id in members:
                user_guild = guild_name
                guild_members = members
                break
        
        if not user_guild:
            await interaction.response.send_message("❌ You must be in a guild to participate in heists!", ephemeral=True)
            return
        
        # Check if user is guild leader
        guild_data = server_data.get("guilds", {}).get(user_guild, {})
        guild_owner = guild_data.get("owner")
        
        if str(guild_owner) != user_id:
            await interaction.response.send_message(
                "❌ **Only the guild leader can initiate heists!**\n"
                f"Your guild leader is <@{guild_owner}>",
                ephemeral=True
            )
            return
        
        # Check guild cooldown (1 heist per Sunday per GUILD, not per user)
        guild_cooldowns = server_data.get("cooldowns", {}).get("guild_heist", {})
        last_guild_heist = guild_cooldowns.get(user_guild)
        
        if last_guild_heist:
            last_time = datetime.fromisoformat(last_guild_heist)
            # Check if it's the same Sunday
            if last_time.date() == now.date() and last_time.weekday() == 6:
                await interaction.response.send_message(
                    f"⏰ Your guild **{user_guild}** has already done a heist today!\n"
                    "**One heist per Sunday per guild.**",
                    ephemeral=True
                )
                return
        
        # Mark target guild as heist-attempted (unlocks withdrawal)
        withdrawal_locks = server_data.get("withdrawal_locks", {})
        if target_guild in withdrawal_locks:
            withdrawal_locks[target_guild]["heist_attempted"] = True
            withdrawal_locks[target_guild]["locked"] = False
            server_data["withdrawal_locks"] = withdrawal_locks
            save_server_data(data, guild_id, server_data)
            await save_data(data)
        
        # Check target guild exists
        if target_guild not in server_data.get("guilds", {}):
            await interaction.response.send_message(f"❌ Guild **{target_guild}** doesn't exist!", ephemeral=True)
            return
        
        # Can't heist your own guild
        if target_guild == user_guild:
            await interaction.response.send_message("❌ You can't heist your own guild!", ephemeral=True)
            return
        
        # Get target guild bank
        target_guild_data = server_data.get("guilds", {}).get(target_guild, {})
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
        bonuses = get_heist_gear_bonuses(user_id, server_data)
        difficulty, steal_percent = calculate_heist_difficulty(target_amount, target_bank, bonuses)
        
        embed = discord.Embed(
            title="🏦 HEIST PLANNING",
            description=f"Planning to rob **{target_guild}** guild bank!\n\n**Choose your approach:**\n🥷 **Solo Heist** - Go alone, higher risk\n👥 **Multiplayer** - Team up with 2-5 guild members",
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
        
        embed.set_footer(text="⚠️ Leader Only - Select team members for multiplayer heists!")
        
        view = HeistConfirmView(user_id, user_guild, target_guild, target_amount, guild_members, self.bot, guild_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class HeistConfirmView(discord.ui.View):
    def __init__(self, user_id, guild_name, target_guild, target_amount, guild_members, bot, discord_guild_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.guild_name = guild_name
        self.target_guild = target_guild
        self.target_amount = target_amount
        self.guild_members = guild_members
        self.bot = bot
        self.discord_guild_id = str(discord_guild_id)
    
    @discord.ui.button(label="Solo Heist", style=discord.ButtonStyle.primary, emoji="🥷", row=0)
    async def solo_heist(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your heist!", ephemeral=True)
            return
        
        # Set guild cooldown
        data = await load_data()
        server_data = get_server_data(data, self.discord_guild_id)
        server_data.setdefault("cooldowns", {}).setdefault("guild_heist", {})[self.guild_name] = datetime.utcnow().isoformat()
        save_server_data(data, self.discord_guild_id, server_data)
        await save_data(data)
        
        # Start solo heist
        heist_view = SoloHeistView(self.user_id, self.guild_name, self.target_guild, self.target_amount, self.discord_guild_id)
        embed = await heist_view.create_solo_embed()
        await interaction.response.edit_message(embed=embed, view=heist_view)
    
    @discord.ui.button(label="Multiplayer Heist (2-5 players)", style=discord.ButtonStyle.success, emoji="👥", row=0)
    async def multiplayer_heist(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This isn't your heist!", ephemeral=True)
            return
        
        # Start member selection phase (leader selects who participates)
        member_select_view = HeistMemberSelectView(
            self.user_id, 
            self.guild_name, 
            self.target_guild, 
            self.target_amount, 
            self.guild_members,
            self.bot,
            self.discord_guild_id
        )
        
        embed = discord.Embed(
            title="👥 SELECT HEIST TEAM",
            description=f"**Leader:** <@{self.user_id}>\n**Target:** {self.target_guild} Guild Bank\n**Amount:** {self.target_amount:,} coins\n\n"
                       "**As the guild leader, select which members will participate in this heist.**",
            color=0xff9500
        )
        embed.add_field(
            name="� Instructions", 
            value="1. Use the dropdown to select 1-4 additional members\n"
                  "2. You (leader) are automatically included\n"
                  "3. Click 'Confirm Team & Proceed' when ready\n"
                  "4. Next step: Assign roles to each member",
            inline=False
        )
        embed.set_footer(text="⏰ You have 2 minutes to select your team")
        
        await interaction.response.edit_message(embed=embed, view=member_select_view)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌", row=1)
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
