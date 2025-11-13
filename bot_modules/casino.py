"""
Casino module: slots, coinflip, blackjack, roulette, ratrace with full item effects
"""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta
from .database import load_data, save_data

def deduct_debt(user_id, amount, data):
    """Deduct outstanding debt from earnings. Returns (remaining_amount, debt_paid)"""
    user_id = str(user_id)
    debt = data.get("debt", {}).get(user_id, 0)
    
    if debt <= 0:
        return amount, 0
    
    if amount >= debt:
        # Can pay off all debt
        remaining = amount - debt
        debt_paid = debt
        data.setdefault("debt", {})[user_id] = 0
    else:
        # Partial debt payment
        remaining = 0
        debt_paid = amount
        data.setdefault("debt", {})[user_id] = debt - amount
    
    return remaining, debt_paid

def get_total_balance(user_id, data):
    """Get user's total balance (wallet + bank)"""
    user_id = str(user_id)
    wallet = data.get("coins", {}).get(user_id, 0)
    bank = data.get("bank", {}).get(user_id, 0)
    return wallet, bank, wallet + bank

def deduct_bet(user_id, bet_amount, data):
    """Deduct bet from wallet first, then bank if needed. Returns success boolean."""
    user_id = str(user_id)
    wallet = data.get("coins", {}).get(user_id, 0)
    bank = data.get("bank", {}).get(user_id, 0)
    total = wallet + bank
    
    if total < bet_amount:
        return False  # Insufficient funds
    
    # Deduct from wallet first
    if wallet >= bet_amount:
        data.setdefault("coins", {})[user_id] = wallet - bet_amount
    else:
        # Take all from wallet, rest from bank
        needed_from_bank = bet_amount - wallet
        data.setdefault("coins", {})[user_id] = 0
        data.setdefault("bank", {})[user_id] = bank - needed_from_bank
    
    return True

def check_cooldown(user_id, command, data, cooldown_seconds=30):
    """Check if user is on cooldown for a command"""
    cooldowns = data.get("cooldowns", {})
    user_cooldowns = cooldowns.get(str(user_id), {})
    
    if command in user_cooldowns:
        last_used = datetime.fromisoformat(user_cooldowns[command])
        if datetime.utcnow() - last_used < timedelta(seconds=cooldown_seconds):
            remaining = cooldown_seconds - (datetime.utcnow() - last_used).seconds
            return remaining
    return 0

def set_cooldown(user_id, command, data):
    """Set cooldown for user command"""
    data.setdefault("cooldowns", {}).setdefault(str(user_id), {})[command] = datetime.utcnow().isoformat()

def track_casino_game(user_id, game_name, won, bet_amount, winnings, data):
    """Track casino game statistics for leaderboards"""
    user_id = str(user_id)
    stats = data.setdefault("casino_stats", {}).setdefault(user_id, {
        "total_games": 0,
        "wins": 0,
        "losses": 0,
        "total_bet": 0,
        "total_won": 0,
        "games": {}
    })
    
    # Update overall stats
    stats["total_games"] += 1
    stats["total_bet"] += bet_amount
    stats["total_won"] += winnings
    
    if won:
        stats["wins"] += 1
    else:
        stats["losses"] += 1
    
    # Update per-game stats
    game_stats = stats["games"].setdefault(game_name, {
        "played": 0,
        "wins": 0,
        "losses": 0,
        "total_bet": 0,
        "total_won": 0
    })
    
    game_stats["played"] += 1
    game_stats["total_bet"] += bet_amount
    game_stats["total_won"] += winnings
    
    if won:
        game_stats["wins"] += 1
    else:
        game_stats["losses"] += 1

async def get_gambling_effects(user_id, data):
    """Calculate gambling bonuses from items"""
    user_id = str(user_id)
    bonuses = {
        "win_chance_bonus": 0.0,
        "payout_bonus": 0.0,
        "insurance": False,
        "active_items": []
    }
    
    # Check consumables (potions)
    consumables = data.get("consumable_effects", {}).get(user_id, {})
    
    # luck_potion from shop: +20% winnings
    if "luck_potion" in consumables:
        bonuses["payout_bonus"] += 0.2  # +20% winnings
        bonuses["active_items"].append("🍀 Luck Potion")
    
    # Legacy items for backward compatibility
    if "mega_lucky_potion" in consumables:
        bonuses["win_chance_bonus"] += 0.5  # +50%
        bonuses["active_items"].append("🍀 Mega Luck Potion")
    if "jackpot_booster" in consumables:
        bonuses["payout_bonus"] += 0.1  # +10%
        bonuses["active_items"].append("💎 Jackpot Booster")
    if "insurance_scroll" in consumables:
        bonuses["insurance"] = True
        bonuses["active_items"].append("🛡️ Insurance")
    
    # Check equipped items
    equipment = data.get("equipment", {}).get(user_id, {})
    
    # lucky_charm from shop: +10% casino winnings (permanent when equipped)
    if equipment.get("accessory") == "lucky_charm":
        bonuses["payout_bonus"] += 0.1  # +10% winnings
        bonuses["active_items"].append("🔮 Lucky Charm")
    
    # Legacy equipment for backward compatibility
    if equipment.get("accessory") == "gamblers_charm":
        bonuses["win_chance_bonus"] += 0.05  # +5%
        bonuses["active_items"].append("🎲 Gamblers Charm")
    elif equipment.get("accessory") == "golden_dice":
        bonuses["payout_bonus"] += 0.1  # +10%
        bonuses["active_items"].append("🎲 Golden Dice")
    
    return bonuses

async def consume_item_effect(user_id, item_key, data):
    """Consume a single-use item effect"""
    user_id = str(user_id)
    consumables = data.get("consumable_effects", {}).get(user_id, {})
    
    if item_key in consumables:
        # Remove the effect (it's been used)
        del consumables[item_key]
        
        if not consumables:
            data.get("consumable_effects", {}).pop(user_id, None)
        
        return True
    return False

def add_transaction(user_id, amount, reason, data, tx_type="credit"):
    """Add transaction record"""
    tx = {
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "type": tx_type,
        "amount": abs(amount),
        "reason": reason
    }
    data.setdefault("transactions", {}).setdefault(str(user_id), []).append(tx)

class SlotsView(discord.ui.View):
    def __init__(self, user_id, guild_id):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_id = guild_id

    @discord.ui.button(label="Spin Again (10 coins)", style=discord.ButtonStyle.primary, emoji="🎰")
    async def spin_again(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your slot machine!", ephemeral=True)
            return
        
        await self.play_slots(interaction, 10)

    @discord.ui.button(label="Big Spin (50 coins)", style=discord.ButtonStyle.danger, emoji="💎")
    async def big_spin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your slot machine!", ephemeral=True)
            return
        
        await self.play_slots(interaction, 50)
    
    @discord.ui.button(label="📊 Paytable", style=discord.ButtonStyle.secondary, emoji="📋", row=1)
    async def show_paytable(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show the mathematical paytable"""
        from .slots_math import get_slot_machine
        slot_machine = get_slot_machine()
        
        embed = discord.Embed(
            title="🎰 Slot Machine Paytable",
            description=slot_machine.get_paytable(),
            color=0xf1c40f
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def play_slots(self, interaction, bet):
        from .slots_math import get_slot_machine
        from .database import get_server_data, save_server_data
        
        guild_id = str(self.guild_id)
        data = await load_data()
        server_data = get_server_data(data, guild_id)
        user_id = str(interaction.user.id)
        
        # Check balance
        wallet = server_data.get("coins", {}).get(user_id, 0)
        bank = server_data.get("bank", {}).get(user_id, 0)
        total = wallet + bank
        
        if total < bet:
            await interaction.response.send_message(
                f"❌ Insufficient funds!\n💰 Wallet: {wallet:,} | 🏦 Bank: {bank:,}\n**Need:** {bet:,} coins",
                ephemeral=True
            )
            return
        
        # Deduct bet from wallet first, then bank
        if wallet >= bet:
            server_data.setdefault("coins", {})[user_id] = wallet - bet
        else:
            remaining = bet - wallet
            server_data.setdefault("coins", {})[user_id] = 0
            server_data.setdefault("bank", {})[user_id] = bank - remaining
        
        # Get item bonuses
        effects = await get_gambling_effects(user_id, server_data)
        bonus_multiplier = 1.0 + effects.get("payout_bonus", 0.0)
        
        # Get the mathematical slot machine
        slot_machine = get_slot_machine()
        
        # Spin the reels (5 reels now!)
        result, winnings, details = slot_machine.spin(bet, bonus_multiplier)
        
        # Handle insurance on losses
        net_result = winnings - bet
        insurance_activated = False
        if net_result < 0 and effects.get("insurance", False):
            refund = bet // 2
            winnings += refund
            net_result += refund
            insurance_activated = True
            # Consume insurance item
            inventory = server_data.get("inventories", {}).get(user_id, {})
            if "insurance_scroll" in inventory and inventory["insurance_scroll"] > 0:
                inventory["insurance_scroll"] -= 1
        
        # Add winnings to wallet
        if winnings > 0:
            current_wallet = server_data.get("coins", {}).get(user_id, 0)
            server_data.setdefault("coins", {})[user_id] = current_wallet + winnings
            
            # Consume bonus items on wins
            inventory = server_data.get("inventories", {}).get(user_id, {})
            for item in ["luck_potion", "jackpot_booster", "mega_lucky_potion"]:
                if item in inventory and inventory[item] > 0:
                    inventory[item] -= 1
        
        # Track casino stats
        stats = server_data.setdefault("casino_stats", {}).setdefault(user_id, {
            "slots_played": 0, "slots_won": 0, "total_wagered": 0, "total_won": 0
        })
        stats["slots_played"] = stats.get("slots_played", 0) + 1
        if winnings > 0:
            stats["slots_won"] = stats.get("slots_won", 0) + 1
        stats["total_wagered"] = stats.get("total_wagered", 0) + bet
        stats["total_won"] = stats.get("total_won", 0) + winnings
        
        save_server_data(data, guild_id, server_data)
        await save_data(data, force=True)
        
        # Get new balance
        new_wallet = server_data.get("coins", {}).get(user_id, 0)
        new_bank = server_data.get("bank", {}).get(user_id, 0)
        
        # Create result embed
        is_big_win = details["win_type"] in ["MEGA JACKPOT", "JACKPOT", "BIG WIN"]
        embed = discord.Embed(
            title="🎰 Mathematical Slot Machine (94.8% RTP)",
            color=0xFFD700 if is_big_win else (0x00ff00 if winnings > 0 else 0xe74c3c)
        )
        
        # Display 5 reels
        reels_display = " | ".join(result)
        embed.add_field(name="🎰 Reels", value=f"[ {reels_display} ]", inline=False)
        
        # Win details
        if details["win"]:
            win_msg = f"**{details['win_type']}!**\n"
            win_msg += f"{details['symbol']} × {details['matches']}"
            
            if details["bonus_applied"]:
                win_msg += f"\n💎 Bonus: +{details['bonus_amount']:,} coins"
            
            if details["free_spins_triggered"]:
                win_msg += f"\n🎰 **{details['free_spins_count']} FREE SPINS!** 🎰"
            
            embed.add_field(name="✨ Result", value=win_msg, inline=False)
        elif insurance_activated:
            embed.add_field(name="🛡️ Insurance", value="Activated! 50% refund", inline=False)
        
        # Stats
        embed.add_field(name="💵 Bet", value=f"{bet:,}", inline=True)
        embed.add_field(name="🎁 Won", value=f"{winnings:,}", inline=True)
        embed.add_field(name="📊 Net", value=f"{'+'if net_result >= 0 else ''}{net_result:,}", inline=True)
        embed.add_field(name="💰 Wallet", value=f"{new_wallet:,}", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{new_bank:,}", inline=True)
        
        # Add scatter info if present
        if details["scatter_count"] > 0:
            scatter_msg = f"{details['scatter_count']} scatter symbols"
            if details["free_spins_triggered"]:
                scatter_msg += f" → {details['free_spins_count']} FREE SPINS!"
            embed.add_field(name="🎰 Scatters", value=scatter_msg, inline=False)
        
        embed.set_footer(text="📊 Mathematically fair • 94.8% RTP • Provably balanced")
        
        view = SlotsView(user_id, guild_id)
        await interaction.response.edit_message(embed=embed, view=view)
        
        # Send public announcement for big wins
        if is_big_win:
            try:
                announcement = discord.Embed(
                    title=f"🎰💰 {details['win_type']}! 💰🎰",
                    description=f"**{interaction.user.mention}** hit a massive win!",
                    color=0xFFD700
                )
                announcement.add_field(name="🎰 Reels", value=f"[ {reels_display} ]", inline=False)
                announcement.add_field(name="💵 Bet", value=f"{bet:,} coins", inline=True)
                announcement.add_field(name="🎁 Won", value=f"**{winnings:,} coins!**", inline=True)
                announcement.add_field(name="✨ Win", value=f"{details['symbol']} × {details['matches']}", inline=True)
                announcement.set_thumbnail(url=interaction.user.display_avatar.url)
                announcement.set_footer(text="🎰 94.8% RTP • Mathematically balanced")
                
                await interaction.followup.send(embed=announcement)
            except Exception as e:
                print(f"Failed to send jackpot announcement: {e}")

# ============================================
# RAT RACE SYSTEM - Multiplayer Live Racing
# ============================================

class RatStats:
    """Individual rat with randomized stats"""
    def __init__(self, rat_id, name, emoji):
        self.id = rat_id
        self.name = name
        self.emoji = emoji
        self.position = 0
        self.forfeited = False
        
        # Randomized stats (0-100)
        self.speed = random.randint(40, 100)  # Affects movement probability
        self.stamina = random.randint(40, 100)  # Affects consistency
        self.luck = random.randint(40, 100)  # Affects random events
        
    def get_stat_bar(self, stat_value):
        """Visual stat bar"""
        filled = int(stat_value / 10)
        return "█" * filled + "░" * (10 - filled)
    
    def get_stats_display(self):
        """Formatted stat display"""
        return (
            f"**Speed:** {self.get_stat_bar(self.speed)} `{self.speed}`\n"
            f"**Stamina:** {self.get_stat_bar(self.stamina)} `{self.stamina}`\n"
            f"**Luck:** {self.get_stat_bar(self.luck)} `{self.luck}`"
        )
    
    def move(self):
        """Calculate movement for this turn"""
        if self.forfeited:
            return 0
        
        # Base movement chance (speed affects probability)
        speed_factor = self.speed / 100
        stamina_factor = self.stamina / 100
        
        # Randomize movement (0, 1, or 2 spaces)
        roll = random.random()
        
        if roll < 0.2 * stamina_factor:  # Stand still
            return 0
        elif roll < 0.5 + (0.3 * speed_factor):  # Move 1
            return 1
        else:  # Move 2
            return 2

class RatRaceLobby:
    """Manages a single race instance"""
    def __init__(self, host_id, guild_id):
        self.host_id = host_id
        self.guild_id = guild_id
        self.race_id = f"{host_id}_{datetime.utcnow().timestamp()}"
        self.rats = self._generate_rats()
        self.bets = {}  # {user_id: {"rat_id": int, "amount": int, "user_name": str}}
        self.started = False
        self.finished = False
        self.finish_order = []
        self.forfeited_rat = None
        self.race_length = 20
        
    def _generate_rats(self):
        """Generate 6 rats with random stats"""
        rat_templates = [
            ("Speedy", "🐭"),
            ("Whiskers", "🐀"),
            ("Nibbles", "🐁"),
            ("Flash", "🐭"),
            ("Chomper", "🐀"),
            ("Dash", "🐁")
        ]
        return [RatStats(i+1, name, emoji) for i, (name, emoji) in enumerate(rat_templates)]
    
    def add_bet(self, user_id, user_name, rat_id, amount):
        """Add a bet to the race"""
        self.bets[user_id] = {
            "rat_id": rat_id,
            "amount": amount,
            "user_name": user_name
        }
    
    def get_rat(self, rat_id):
        """Get rat by ID"""
        return self.rats[rat_id - 1]
    
    def forfeit_random_rat(self):
        """Randomly forfeit one rat (20% chance)"""
        if random.random() < 0.2 and not self.forfeited_rat:
            available_rats = [r for r in self.rats if not r.forfeited and r.position < self.race_length]
            if available_rats:
                rat = random.choice(available_rats)
                rat.forfeited = True
                self.forfeited_rat = rat.id
                return rat
        return None
    
    def move_rats(self):
        """Move all rats one turn"""
        for rat in self.rats:
            if not rat.forfeited and rat.position < self.race_length:
                movement = rat.move()
                rat.position += movement
                
                # Check if finished
                if rat.position >= self.race_length and rat.id not in self.finish_order:
                    self.finish_order.append(rat.id)
        
        # Check if race is over (top 3 finished or all rats done)
        if len(self.finish_order) >= 3 or all(r.position >= self.race_length or r.forfeited for r in self.rats):
            self.finished = True
    
    def get_track_visual(self):
        """Generate visual race track"""
        track_lines = []
        for rat in self.rats:
            # Get bettors on this rat
            bettors = [b["user_name"] for uid, b in self.bets.items() if b["rat_id"] == rat.id]
            bettor_text = f" 💰{len(bettors)}" if bettors else ""
            
            if rat.forfeited:
                track = f"{rat.emoji} ❌ **FORFEITED** - {rat.name}{bettor_text}"
            else:
                pos = min(rat.position, self.race_length)
                track_bar = "▓" * pos + rat.emoji + "░" * (self.race_length - pos)
                status = " 🏆" if rat.id in self.finish_order else ""
                track = f"`{track_bar}` **{rat.name}**{status}{bettor_text}"
            
            track_lines.append(track)
        
        return "\n".join(track_lines)
    
    def calculate_payouts(self):
        """Calculate winnings for all bettors"""
        payouts = {}  # {user_id: amount}
        
        for user_id, bet_info in self.bets.items():
            rat_id = bet_info["rat_id"]
            bet_amount = bet_info["amount"]
            
            # Check placement
            if rat_id in self.finish_order:
                placement = self.finish_order.index(rat_id) + 1
                
                if placement == 1:
                    winnings = bet_amount * 5
                elif placement == 2:
                    winnings = bet_amount * 2
                elif placement == 3:
                    winnings = int(bet_amount * 1.5)
                else:
                    winnings = 0
                
                payouts[user_id] = {
                    "bet": bet_amount,
                    "winnings": winnings,
                    "net": winnings - bet_amount,
                    "placement": placement
                }
            else:
                # Lost
                payouts[user_id] = {
                    "bet": bet_amount,
                    "winnings": 0,
                    "net": -bet_amount,
                    "placement": None
                }
        
        return payouts

# Global race lobbies
active_race_lobbies = {}

class RatRaceStartView(discord.ui.View):
    """Initial view to start a race"""
    def __init__(self):
        super().__init__(timeout=300)
    
    @discord.ui.button(label="Start New Race", style=discord.ButtonStyle.primary, emoji="🏁")
    async def start_race(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        # Create new lobby
        lobby = RatRaceLobby(user_id, guild_id)
        active_race_lobbies[lobby.race_id] = lobby
        
        # Show betting interface
        view = RatRaceBettingView(lobby)
        embed = self._create_lobby_embed(lobby, interaction.user.display_name)
        
        await interaction.response.edit_message(embed=embed, view=view)
        
        # Start countdown timer
        await asyncio.sleep(30)
        
        # Start race if there are bets
        if lobby.race_id in active_race_lobbies and lobby.bets:
            await self._start_race_sequence(interaction, lobby)
        elif lobby.race_id in active_race_lobbies:
            # No bets, cancel race
            del active_race_lobbies[lobby.race_id]
            cancel_embed = discord.Embed(
                title="❌ Race Cancelled",
                description="No bets were placed. Race has been cancelled.",
                color=0xe74c3c
            )
            await interaction.edit_original_response(embed=cancel_embed, view=None)
    
    def _create_lobby_embed(self, lobby, host_name):
        """Create the betting lobby embed"""
        embed = discord.Embed(
            title="🏁 RAT RACE - Betting Open!",
            description=f"**Host:** {host_name}\n**Race ID:** `{lobby.race_id[-8:]}`\n\n⏰ **30 seconds to place bets!**",
            color=0xffc300
        )
        
        # Show rat stats
        for rat in lobby.rats:
            embed.add_field(
                name=f"{rat.emoji} #{rat.id} - {rat.name}",
                value=rat.get_stats_display(),
                inline=True
            )
        
        # Show current bets
        if lobby.bets:
            bet_list = "\n".join([
                f"• **{b['user_name']}** bet **{b['amount']}** on **Rat #{b['rat_id']}**"
                for b in lobby.bets.values()
            ])
            embed.add_field(name="💰 Current Bets", value=bet_list, inline=False)
        else:
            embed.add_field(name="💰 Current Bets", value="*No bets yet...*", inline=False)
        
        embed.set_footer(text="Select a rat and enter your bet below!")
        return embed
    
    async def _start_race_sequence(self, interaction, lobby):
        """Run the live race sequence"""
        from .database import get_server_data, save_server_data
        
        lobby.started = True
        
        # Deduct all bets (from wallet + bank) - use server_data
        data = await load_data()
        server_data = get_server_data(data, lobby.guild_id)
        
        for user_id, bet_info in lobby.bets.items():
            bet_amount = bet_info["amount"]
            
            # Deduct from wallet first, then bank
            wallet = server_data.get("coins", {}).get(user_id, 0)
            bank = server_data.get("bank", {}).get(user_id, 0)
            
            if wallet >= bet_amount:
                server_data.setdefault("coins", {})[user_id] = wallet - bet_amount
            else:
                remaining = bet_amount - wallet
                server_data.setdefault("coins", {})[user_id] = 0
                server_data.setdefault("bank", {})[user_id] = bank - remaining
        
        save_server_data(data, lobby.guild_id, server_data)
        await save_data(data, force=True)
        
        # Starting embed
        start_embed = discord.Embed(
            title="🏁 RAT RACE - STARTING!",
            description="🚦 **3... 2... 1... GO!**",
            color=0x3498db
        )
        await interaction.edit_original_response(embed=start_embed, view=None)
        await asyncio.sleep(2)
        
        # Race loop
        turn = 0
        while not lobby.finished:
            turn += 1
            lobby.move_rats()
            
            # Check for forfeit (only once per race)
            forfeited = lobby.forfeit_random_rat()
            forfeit_text = f"\n\n⚠️ **{forfeited.emoji} {forfeited.name} has forfeited!**" if forfeited else ""
            
            # Create race update embed
            race_embed = discord.Embed(
                title=f"🏁 RAT RACE - Turn {turn}",
                description=f"**Live Race in Progress!**{forfeit_text}\n\n{lobby.get_track_visual()}",
                color=0x3498db
            )
            
            # Show finish order if any
            if lobby.finish_order:
                positions = []
                for i, rat_id in enumerate(lobby.finish_order[:3]):
                    rat = lobby.get_rat(rat_id)
                    medal = ["🥇", "🥈", "🥉"][i]
                    positions.append(f"{medal} {rat.emoji} **{rat.name}**")
                race_embed.add_field(name="🏆 Finished", value="\n".join(positions), inline=False)
            
            race_embed.set_footer(text=f"🎯 Race Length: {lobby.race_length} spaces")
            
            await interaction.edit_original_response(embed=race_embed)
            await asyncio.sleep(2)  # 2 second delay between turns
        
        # Race finished - show results and pay out
        await self._show_results(interaction, lobby)
    
    async def _show_results(self, interaction, lobby):
        """Show final results and distribute winnings"""
        from .database import get_server_data, save_server_data
        
        data = await load_data()
        server_data = get_server_data(data, lobby.guild_id)
        payouts = lobby.calculate_payouts()
        
        # Distribute winnings - use server_data
        for user_id, payout_info in payouts.items():
            if payout_info["winnings"] > 0:
                current_coins = server_data.get("coins", {}).get(user_id, 0)
                server_data.setdefault("coins", {})[user_id] = current_coins + payout_info["winnings"]
        
        # Track casino stats
        for user_id, payout_info in payouts.items():
            bet_info = lobby.bets[user_id]
            stats = server_data.setdefault("casino_stats", {}).setdefault(user_id, {
                "ratrace_played": 0, "ratrace_won": 0, "total_wagered": 0, "total_won": 0
            })
            stats["ratrace_played"] = stats.get("ratrace_played", 0) + 1
            if payout_info["winnings"] > 0:
                stats["ratrace_won"] = stats.get("ratrace_won", 0) + 1
            stats["total_wagered"] = stats.get("total_wagered", 0) + bet_info["amount"]
            stats["total_won"] = stats.get("total_won", 0) + payout_info["winnings"]
        
        save_server_data(data, lobby.guild_id, server_data)
        await save_data(data, force=True)
        
        # Create results embed
        results_embed = discord.Embed(
            title="🏁 RAT RACE - FINISHED!",
            description="**Final Results**",
            color=0x27ae60
        )
        
        # Show final track
        results_embed.add_field(name="📊 Final Track", value=lobby.get_track_visual(), inline=False)
        
        # Show winners
        if lobby.finish_order:
            positions = []
            for i, rat_id in enumerate(lobby.finish_order[:3]):
                rat = lobby.get_rat(rat_id)
                medal = ["🥇 1st", "🥈 2nd", "🥉 3rd"][i]
                multiplier = ["5x", "2x", "1.5x"][i]
                positions.append(f"{medal} - {rat.emoji} **{rat.name}** ({multiplier})")
            results_embed.add_field(name="🏆 Podium", value="\n".join(positions), inline=False)
        
        # Show payouts
        payout_lines = []
        for user_id, payout_info in payouts.items():
            bet_data = lobby.bets[user_id]
            rat = lobby.get_rat(bet_data["rat_id"])
            
            if payout_info["net"] > 0:
                result_emoji = "💰"
                result_text = f"+{payout_info['net']} coins"
            else:
                result_emoji = "❌"
                result_text = f"{payout_info['net']} coins"
            
            payout_lines.append(
                f"{result_emoji} **{bet_data['user_name']}** - {rat.emoji} Rat #{rat.id} - {result_text}"
            )
        
        results_embed.add_field(name="💵 Payouts", value="\n".join(payout_lines), inline=False)
        results_embed.set_footer(text="Thanks for racing! Start another race anytime! 🏁")
        
        await interaction.edit_original_response(embed=results_embed)
        
        # Cleanup lobby
        if lobby.race_id in active_race_lobbies:
            del active_race_lobbies[lobby.race_id]

class RatRaceBettingView(discord.ui.View):
    """View for placing bets during betting phase"""
    def __init__(self, lobby):
        super().__init__(timeout=30)
        self.lobby = lobby
        
        # Add rat selection dropdown
        options = [
            discord.SelectOption(
                label=f"Rat #{rat.id} - {rat.name}",
                value=str(rat.id),
                emoji=rat.emoji,
                description=f"Speed: {rat.speed} | Stamina: {rat.stamina} | Luck: {rat.luck}"
            )
            for rat in lobby.rats
        ]
        
        select = discord.ui.Select(
            placeholder="Choose your rat...",
            options=options,
            custom_id="rat_select"
        )
        select.callback = self.rat_selected
        self.add_item(select)
        
        self.selected_rat = None
    
    async def rat_selected(self, interaction: discord.Interaction):
        """Handle rat selection"""
        self.selected_rat = int(interaction.data["values"][0])
        
        # Show bet amount modal
        modal = BetAmountModal(self.lobby, self.selected_rat)
        await interaction.response.send_modal(modal)

class BetAmountModal(discord.ui.Modal, title="Place Your Bet"):
    """Modal for entering bet amount"""
    def __init__(self, lobby, rat_id):
        super().__init__()
        self.lobby = lobby
        self.rat_id = rat_id
        
        self.bet_input = discord.ui.TextInput(
            label="Bet Amount",
            placeholder="Enter amount of coins to bet...",
            required=True,
            min_length=1,
            max_length=10
        )
        self.add_item(self.bet_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        from .database import get_server_data
        
        try:
            bet_amount = int(self.bet_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
            return
        
        if bet_amount < 10:
            await interaction.response.send_message("❌ Minimum bet is 10 coins!", ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        data = await load_data()
        server_data = get_server_data(data, guild_id)
        
        # Check total balance (wallet + bank) - use server_data
        wallet = server_data.get("coins", {}).get(user_id, 0)
        bank = server_data.get("bank", {}).get(user_id, 0)
        total = wallet + bank
        
        if total < bet_amount:
            await interaction.response.send_message(
                f"❌ Insufficient funds!\n💰 Wallet: {wallet:,} | 🏦 Bank: {bank:,}\n**Need:** {bet_amount:,} coins",
                ephemeral=True
            )
            return
        
        # Check if already bet
        if user_id in self.lobby.bets:
            await interaction.response.send_message(
                "❌ You already placed a bet on this race!",
                ephemeral=True
            )
            return
        
        # Add bet
        rat = self.lobby.get_rat(self.rat_id)
        self.lobby.add_bet(user_id, interaction.user.display_name, self.rat_id, bet_amount)
        
        await interaction.response.send_message(
            f"✅ Bet placed! **{bet_amount} coins** on {rat.emoji} **{rat.name}**\nGood luck! 🍀",
            ephemeral=True
        )

class BlackjackView(discord.ui.View):
    def __init__(self, user_id, guild_id, bet, player_hand, dealer_hand, deck):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.guild_id = guild_id
        self.bet = bet
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.deck = deck

    def calculate_hand_value(self, hand):
        """Calculate blackjack hand value"""
        value = 0
        aces = 0
        for card in hand:
            if card in ['J', 'Q', 'K']:
                value += 10
            elif card == 'A':
                aces += 1
                value += 11
            else:
                value += int(card)
        
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value

    def format_hand(self, hand, hide_first=False):
        """Format hand for display"""
        if hide_first:
            return f"[??] {' '.join(hand[1:])}"
        return ' '.join(hand)

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary, emoji="🎯")
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
            return
        
        # Draw card
        if self.deck:
            card = self.deck.pop()
            self.player_hand.append(card)
        
        player_value = self.calculate_hand_value(self.player_hand)
        
        if player_value > 21:
            # Bust
            await self.end_game(interaction, "bust")
        else:
            # Continue game
            embed = discord.Embed(title="🃏 Blackjack", color=0x3498db)
            embed.add_field(name="Your Hand", value=f"{self.format_hand(self.player_hand)} (Value: {player_value})", inline=False)
            embed.add_field(name="Dealer Hand", value=f"{self.format_hand(self.dealer_hand, hide_first=True)}", inline=False)
            embed.add_field(name="Bet", value=f"{self.bet} coins", inline=True)
            
            if player_value == 21:
                await self.stand(interaction, button)
            else:
                await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary, emoji="✋")
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
            return
        
        # Dealer plays
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        while dealer_value < 17 and self.deck:
            card = self.deck.pop()
            self.dealer_hand.append(card)
            dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        player_value = self.calculate_hand_value(self.player_hand)
        
        # Determine winner
        if dealer_value > 21:
            result = "dealer_bust"
        elif player_value > dealer_value:
            result = "player_win"
        elif dealer_value > player_value:
            result = "dealer_win"
        else:
            result = "tie"
        
        await self.end_game(interaction, result)

    async def end_game(self, interaction, result):
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, self.guild_id)
        
        user_id = str(interaction.user.id)
        effects = await get_gambling_effects(user_id, server_data)
        
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        # Calculate winnings (bet already deducted)
        winnings = 0
        if result in ["player_win", "dealer_bust"]:
            if len(self.player_hand) == 2 and player_value == 21:  # Blackjack
                winnings = int(self.bet * 2.5)
                result_text = "🎉 BLACKJACK!"
            else:
                winnings = self.bet * 2
                result_text = "🎊 You win!"
        elif result == "tie":
            winnings = self.bet  # Return bet
            result_text = "🤝 Push (tie)"
        else:  # bust or dealer_win
            result_text = "😔 You lose!"
            
            # Apply insurance (refund to wallet)
            if effects["insurance"]:
                refund = self.bet // 2
                winnings = refund
                result_text += f"\n🛡️ Insurance: +{refund} coins"
                await consume_item_effect(user_id, "insurance_scroll", server_data)
        
        # Add winnings to wallet
        if winnings > 0:
            current_wallet = server_data.get("coins", {}).get(user_id, 0)
            server_data.setdefault("coins", {})[user_id] = current_wallet + winnings
            add_transaction(user_id, winnings, "Blackjack win", server_data, "credit")
        
        # Consume effects
        if winnings > self.bet and effects["win_chance_bonus"] > 0:
            await consume_item_effect(user_id, "lucky_potion", server_data)
            await consume_item_effect(user_id, "mega_lucky_potion", server_data)
        
        # Track casino stats
        won = winnings > 0
        track_casino_game(user_id, "blackjack", won, self.bet, winnings, server_data)
        
        save_server_data(data, self.guild_id, server_data)
        await save_data(data, force=True)
        
        # Get new balance for display
        new_wallet, new_bank, new_total = get_total_balance(user_id, server_data)
        net_result = winnings - self.bet
        
        embed = discord.Embed(title="🃏 Blackjack - Game Over", color=0x27ae60 if net_result > 0 else 0xe74c3c)
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Your Hand", value=f"{self.format_hand(self.player_hand)} (Value: {player_value})", inline=False)
        embed.add_field(name="Dealer Hand", value=f"{self.format_hand(self.dealer_hand)} (Value: {dealer_value})", inline=False)
        embed.add_field(name="Result", value=result_text, inline=False)
        embed.add_field(name="Bet", value=f"{self.bet} coins", inline=True)
        embed.add_field(name="Won", value=f"{winnings} coins", inline=True)
        embed.add_field(name="Net", value=f"{'+'if net_result >= 0 else ''}{net_result} coins", inline=True)
        embed.add_field(name="💰 Wallet", value=f"{new_wallet:,} coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{new_bank:,} coins", inline=True)
        
        # First, edit the ephemeral message to remove buttons
        try:
            await interaction.response.edit_message(content="Game finished! See results below.", embed=None, view=None)
        except:
            # If response already sent, try to edit the message directly
            try:
                await interaction.message.edit(content="Game finished! See results below.", embed=None, view=None)
            except:
                pass
        
        # Send public result message
        await interaction.channel.send(embed=embed)

class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="casino", description="Open the casino hub.")
    async def casino(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎰 Casino Hub", description="Welcome to the casino! Choose your game:", color=0xffc300)
        embed.add_field(name="🎯 Roulette", value="`/roulette` - Spin the wheel of fortune!", inline=False)
        embed.add_field(name="🎰 Slots", value="`/slots` - Try your luck on the slot machine!", inline=False)
        embed.add_field(name="🪙 Coinflip", value="`/coinflip` - Double or nothing!", inline=False)
        embed.add_field(name="🃏 Blackjack", value="`/blackjack` - Beat the dealer at 21!", inline=False)
        embed.add_field(name="🏁 Rat Race", value="`/ratrace` - Multiplayer live racing!", inline=False)
        embed.set_footer(text="💡 Tip: Use items like luck_potion to boost your chances!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="roulette", description="Spin the roulette wheel!")
    @app_commands.describe(bet="Amount to bet", choice="red, black, green, or a number (0-36)")
    async def roulette(self, interaction: discord.Interaction, bet: int, choice: str):
        if bet < 10:
            await interaction.response.send_message("❌ Minimum bet is 10 coins!", ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, guild_id)
        
        # Check total balance (wallet + bank)
        wallet, bank, total = get_total_balance(user_id, server_data)
        if total < bet:
            await interaction.response.send_message(
                f"❌ You don't have enough coins! You need {bet} coins but have:\n💰 Wallet: {wallet:,} | 🏦 Bank: {bank:,} | Total: {total:,}",
                ephemeral=True
            )
            return
        
        # Deduct bet from wallet first, then bank
        if not deduct_bet(user_id, bet, server_data):
            await interaction.response.send_message("❌ Failed to deduct bet!", ephemeral=True)
            return
        
        add_transaction(user_id, bet, "Roulette bet", server_data, tx_type="debit")
        
        # Get gambling effects
        effects = await get_gambling_effects(user_id, server_data)
        
        # Roulette logic
        result = random.randint(0, 36)
        color = "green" if result == 0 else "red" if result % 2 == 1 else "black"
        
        won = False
        winnings = 0
        
        # Check win conditions
        choice_lower = choice.lower()
        if choice_lower == color:
            won = True
            winnings = bet * 2
        elif choice_lower.isdigit() and int(choice_lower) == result:
            won = True
            winnings = bet * 35
        
        # Apply gambling effects and add to wallet
        if won and winnings > 0:
            winnings = int(winnings * (1 + effects["payout_bonus"]))
            current_wallet = server_data.get("coins", {}).get(user_id, 0)
            server_data.setdefault("coins", {})[user_id] = current_wallet + winnings
            add_transaction(user_id, winnings, "Roulette win", server_data, tx_type="credit")
            
            # Consume luck potions on win
            if effects["payout_bonus"] > 0:
                await consume_item_effect(user_id, "luck_potion", server_data)
        
        # Track casino stats
        track_casino_game(user_id, "roulette", won, bet, winnings, server_data)
        
        # Save data
        save_server_data(data, guild_id, server_data)
        await save_data(data, force=True)
        
        # Get new balance for display
        new_wallet, new_bank, new_total = get_total_balance(user_id, server_data)
        net_result = winnings - bet
        
        # Create embed
        embed = discord.Embed(
            title="🎯 Roulette Result", 
            color=0x00ff00 if won else 0xff0000
        )
        embed.add_field(name="Spin Result", value=f"**{result}** ({color})", inline=True)
        embed.add_field(name="Your Bet", value=f"{bet} on {choice}", inline=True)
        
        if won:
            embed.add_field(name="Outcome", value=f"✅ Won {winnings:,} coins!", inline=False)
            if effects["payout_bonus"] > 0:
                embed.add_field(name="🍀 Luck Bonus", value=f"+{effects['payout_bonus']*100:.0f}% payout", inline=True)
        else:
            embed.add_field(name="Outcome", value=f"❌ Lost {bet:,} coins", inline=False)
        
        embed.add_field(name="Net", value=f"{'+'if net_result >= 0 else ''}{net_result:,} coins", inline=True)
        embed.add_field(name="💰 Wallet", value=f"{new_wallet:,} coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{new_bank:,} coins", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="slots", description="Play slot machine with item bonuses!")
    @app_commands.describe(bet="Amount to bet (default: 10)")
    async def slots(self, interaction: discord.Interaction, bet: int = 10):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        if bet < 1:
            await interaction.response.send_message("❌ Minimum bet is 1 coin!", ephemeral=True)
            return
        
        data = await load_data()
        from .database import get_server_data
        server_data = get_server_data(data, guild_id)
        
        # Check cooldown
        cooldown = check_cooldown(user_id, "slots", server_data, 10)
        if cooldown > 0:
            await interaction.response.send_message(f"⏰ Cooldown active! Wait {cooldown} seconds.", ephemeral=True)
            return
        
        user_coins = server_data.get("coins", {}).get(user_id, 0)
        if user_coins < bet:
            await interaction.response.send_message(f"❌ You need {bet} coins! Your balance: {user_coins}", ephemeral=True)
            return
        
        set_cooldown(user_id, "slots", server_data)
        from .database import save_server_data
        save_server_data(data, guild_id, server_data)
        await save_data(data)
        
        embed = discord.Embed(title="🎰 Slot Machine", description="Choose your bet amount:", color=0xf1c40f)
        embed.add_field(name="Your Balance", value=f"{user_coins:,} coins", inline=True)
        embed.add_field(name="Current Bet", value=f"{bet} coins", inline=True)
        
        # Show active effects
        effects = await get_gambling_effects(user_id, server_data)
        if effects["win_chance_bonus"] > 0:
            embed.add_field(name="🍀 Luck Bonus", value=f"+{effects['win_chance_bonus']*100:.0f}%", inline=True)
        if effects["payout_bonus"] > 0:
            embed.add_field(name="💰 Payout Bonus", value=f"+{effects['payout_bonus']*100:.0f}%", inline=True)
        if effects["insurance"]:
            embed.add_field(name="🛡️ Insurance", value="50% refund on loss", inline=True)
        
        embed.set_footer(text="🎲 Payouts: 💎x50, ⭐x15, 🍇x8, 🍊x5, 🍋x4, 🍒x3")
        
        view = SlotsView(user_id, guild_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="coinflip", description="Flip a coin and double your money!")
    @app_commands.describe(bet="Amount to bet", choice="Choose heads or tails")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip(self, interaction: discord.Interaction, bet: int, choice: str):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        if bet < 1:
            await interaction.response.send_message("❌ Minimum bet is 1 coin!", ephemeral=True)
            return
        
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, guild_id)
        
        # Check cooldown
        cooldown = check_cooldown(user_id, "coinflip", server_data, 15)
        if cooldown > 0:
            await interaction.response.send_message(f"⏰ Cooldown active! Wait {cooldown} seconds.", ephemeral=True)
            return
        
        # Check total balance (wallet + bank)
        wallet, bank, total = get_total_balance(user_id, server_data)
        if total < bet:
            await interaction.response.send_message(
                f"❌ Insufficient funds!\n💰 Wallet: {wallet:,} | 🏦 Bank: {bank:,}\n**Need:** {bet:,} coins",
                ephemeral=True
            )
            return
        
        # Deduct bet from wallet/bank
        deduct_bet(user_id, bet, server_data)
        
        # Get effects and calculate win chance
        effects = await get_gambling_effects(user_id, server_data)
        base_chance = 0.5
        win_chance = min(0.95, base_chance + effects["win_chance_bonus"])  # Cap at 95%
        
        # Flip coin
        result = "heads" if random.random() < win_chance else "tails"
        won = (choice == result)
        
        winnings = 0
        if won:
            winnings = bet * 2
            # Add winnings to wallet
            current_wallet = server_data.get("coins", {}).get(user_id, 0)
            server_data.setdefault("coins", {})[user_id] = current_wallet + winnings
            result_text = f"🎉 You won! The coin landed on {result}!"
            color = 0x27ae60
            add_transaction(user_id, winnings, "Coinflip win", server_data, "credit")
        else:
            result_text = f"😔 You lost! The coin landed on {result}."
            color = 0xe74c3c
            
            # Apply insurance (refund to wallet)
            if effects["insurance"]:
                refund = bet // 2
                current_wallet = server_data.get("coins", {}).get(user_id, 0)
                server_data.setdefault("coins", {})[user_id] = current_wallet + refund
                result_text += f"\n🛡️ Insurance activated! Refunded {refund} coins"
                await consume_item_effect(user_id, "insurance_scroll", server_data)
        
        # Consume luck effects
        if won and effects["win_chance_bonus"] > 0:
            await consume_item_effect(user_id, "lucky_potion", server_data)
            await consume_item_effect(user_id, "mega_lucky_potion", server_data)
        
        # Track casino stats
        track_casino_game(user_id, "coinflip", won, bet, winnings, server_data)
        
        set_cooldown(user_id, "coinflip", server_data)
        save_server_data(data, guild_id, server_data)
        await save_data(data, force=True)
        
        # Show result
        new_wallet, new_bank, new_total = get_total_balance(user_id, server_data)
        net_result = winnings - bet
        
        coin_emoji = "🪙" if result == "heads" else "🔄"
        embed = discord.Embed(title=f"{coin_emoji} Coinflip", color=color)
        embed.add_field(name="Your Choice", value=choice.title(), inline=True)
        embed.add_field(name="Result", value=result.title(), inline=True)
        embed.add_field(name="Outcome", value="WIN" if won else "LOSS", inline=True)
        embed.add_field(name="Bet", value=f"{bet} coins", inline=True)
        embed.add_field(name="Net", value=f"{'+'if net_result >= 0 else ''}{net_result} coins", inline=True)
        embed.add_field(name="💰 Wallet", value=f"{new_wallet:,} coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"{new_bank:,} coins", inline=True)
        embed.description = result_text
        
        if effects["win_chance_bonus"] > 0:
            embed.set_footer(text=f"🍀 You had {win_chance*100:.1f}% win chance!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="blackjack", description="Play blackjack against the dealer!")
    @app_commands.describe(bet="Amount to bet")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        if bet < 1:
            await interaction.response.send_message("❌ Minimum bet is 1 coin!", ephemeral=True)
            return
        
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, guild_id)
        
        # Check cooldown
        cooldown = check_cooldown(user_id, "blackjack", server_data, 20)
        if cooldown > 0:
            await interaction.response.send_message(f"⏰ Cooldown active! Wait {cooldown} seconds.", ephemeral=True)
            return
        
        # Check total balance (wallet + bank)
        wallet, bank, total = get_total_balance(user_id, server_data)
        if total < bet:
            await interaction.response.send_message(
                f"❌ Insufficient funds!\n💰 Wallet: {wallet:,} | 🏦 Bank: {bank:,}\n**Need:** {bet:,} coins",
                ephemeral=True
            )
            return
        
        # Deduct bet from wallet/bank
        deduct_bet(user_id, bet, server_data)
        
        # Create deck and deal initial hands
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [rank for rank in ranks for _ in suits]
        random.shuffle(deck)
        
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        
        view = BlackjackView(user_id, guild_id, bet, player_hand, dealer_hand, deck)
        player_value = view.calculate_hand_value(player_hand)
        
        embed = discord.Embed(title="🃏 Blackjack", color=0x3498db)
        embed.add_field(name="Your Hand", value=f"{view.format_hand(player_hand)} (Value: {player_value})", inline=False)
        embed.add_field(name="Dealer Hand", value=f"{view.format_hand(dealer_hand, hide_first=True)}", inline=False)
        embed.add_field(name="Bet", value=f"{bet} coins", inline=True)
        
        # Check for blackjack
        if player_value == 21:
            embed.description = "🎉 BLACKJACK! You got 21!"
            await view.stand(interaction, None)
        else:
            embed.set_footer(text="🎯 Hit to draw another card, ✋ Stand to stop")
            set_cooldown(user_id, "blackjack", server_data)
            save_server_data(data, guild_id, server_data)
            await save_data(data)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="ratrace", description="🏁 Start or join a multiplayer rat race!")
    async def ratrace(self, interaction: discord.Interaction):
        """Start a new multiplayer rat race"""
        view = RatRaceStartView()
        embed = discord.Embed(
            title="🏁 RAT RACE - Multiplayer Betting",
            description="**Welcome to the Rat Racing Arena!**\n\nClick **Start New Race** to begin!\nOther players can join and bet on the same race.",
            color=0xffc300
        )
        embed.add_field(
            name="� How It Works",
            value=(
                "• Host starts a race with 6 random rats\n"
                "• Each rat has unique randomized stats\n"
                "• Multiple players can bet on different rats\n"
                "• Race runs live with real-time updates\n"
                "• Rats move 0-2 spaces per turn\n"
                "• One random rat may forfeit each race\n"
                "• First to finish line (20 spaces) wins!"
            ),
            inline=False
        )
        embed.add_field(
            name="💰 Payouts",
            value="🥇 1st Place: **5x** your bet\n🥈 2nd Place: **2x** your bet\n🥉 3rd Place: **1.5x** your bet",
            inline=True
        )
        embed.add_field(
            name="⏱️ Betting Phase",
            value="30 seconds to place bets\nRace starts automatically",
            inline=True
        )
        embed.set_footer(text="💡 Tip: Watch rat stats when betting!")
        
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Casino(bot))
