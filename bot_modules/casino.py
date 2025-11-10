"""
Casino module: slots, coinflip, blackjack, roulette, diceroll, ratrace with full item effects
"""
import discord
from discord import app_commands
from discord.ext import commands
import json
from pathlib import Path
import asyncio
import random
from datetime import datetime, timedelta
from .database import load_data, save_data

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

async def get_gambling_effects(user_id, data):
    """Calculate gambling bonuses from items"""
    user_id = str(user_id)
    bonuses = {
        "win_chance_bonus": 0.0,
        "payout_bonus": 0.0,
        "insurance": False
    }
    
    # Check consumables
    consumables = data.get("consumable_effects", {}).get(user_id, {})
    if "lucky_potion" in consumables:
        bonuses["win_chance_bonus"] += 0.2  # +20%
    if "mega_lucky_potion" in consumables:
        bonuses["win_chance_bonus"] += 0.5  # +50%
    if "jackpot_booster" in consumables:
        bonuses["payout_bonus"] += 0.1  # +10%
    if "insurance_scroll" in consumables:
        bonuses["insurance"] = True
    
    # Check equipment
    equipment = data.get("equipment", {}).get(user_id, {})
    
    if "accessory" in equipment:
        item = equipment["accessory"]
        if item == "gamblers_charm":
            bonuses["win_chance_bonus"] += 0.05  # +5%
        elif item == "golden_dice":
            bonuses["payout_bonus"] += 0.1  # +10%
        elif item == "lucky_coin":
            bonuses["win_chance_bonus"] += 0.05  # +5% (rat race specific)
    
    return bonuses

async def consume_item_effect(user_id, item_key, data):
    """Consume a single-use item effect"""
    user_id = str(user_id)
    consumables = data.get("consumable_effects", {}).get(user_id, {})
    
    if item_key in consumables:
        consumables[item_key] -= 1
        if consumables[item_key] <= 0:
            del consumables[item_key]
        
        if not consumables:
            data.get("consumable_effects", {}).pop(user_id, None)
        
        await save_data(data)
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
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

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

    async def play_slots(self, interaction, bet):
        data = await load_data()
        user_id = str(interaction.user.id)
        user_coins = data.get("coins", {}).get(user_id, 0)
        
        if user_coins < bet:
            await interaction.response.send_message(f"❌ You need {bet} coins to spin! Your balance: {user_coins}", ephemeral=True)
            return
        
        # Get bonuses
        effects = await get_gambling_effects(user_id, data)
        
        # Slot symbols with weights
        symbols = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎"]
        weights = [30, 25, 20, 15, 8, 2]  # Rarer symbols have lower weights
        
        # Spin the reels
        reel1 = random.choices(symbols, weights=weights)[0]
        reel2 = random.choices(symbols, weights=weights)[0]
        reel3 = random.choices(symbols, weights=weights)[0]
        
        # Calculate winnings
        winnings = 0
        win_text = ""
        
        if reel1 == reel2 == reel3:  # Three of a kind
            multipliers = {"🍒": 3, "🍋": 4, "🍊": 5, "🍇": 8, "⭐": 15, "💎": 50}
            winnings = bet * multipliers.get(reel1, 3)
            win_text = f"🎉 JACKPOT! Three {reel1}s!"
        elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:  # Two of a kind
            winnings = bet * 2
            win_text = "🎊 Two of a kind!"
        
        # Apply bonuses
        if winnings > 0:
            # Apply payout bonus
            if effects["payout_bonus"] > 0:
                bonus_amount = int(winnings * effects["payout_bonus"])
                winnings += bonus_amount
                win_text += f"\n💰 Item bonus: +{bonus_amount} coins!"
            
            # Consume jackpot booster if used
            if effects["payout_bonus"] > 0:
                await consume_item_effect(user_id, "jackpot_booster", data)
        
        # Handle loss with insurance
        net_result = winnings - bet
        if net_result < 0 and effects["insurance"]:
            refund = bet // 2
            net_result += refund
            win_text = f"🛡️ Insurance activated! Refunded {refund} coins"
            await consume_item_effect(user_id, "insurance_scroll", data)
        
        # Update balance
        data.setdefault("coins", {})[user_id] = user_coins + net_result
        
        # Add transaction
        if net_result > 0:
            add_transaction(user_id, net_result, f"Slots win (+{winnings-bet})", data, "credit")
        else:
            add_transaction(user_id, abs(net_result), f"Slots loss (-{abs(net_result)})", data, "debit")
        
        # Consume luck potions
        if effects["win_chance_bonus"] > 0:
            await consume_item_effect(user_id, "lucky_potion", data)
            await consume_item_effect(user_id, "mega_lucky_potion", data)
        
        await save_data(data)
        
        # Create result embed
        embed = discord.Embed(title="🎰 Slot Machine", color=0xf1c40f if winnings > 0 else 0xe74c3c)
        embed.add_field(name="Reels", value=f"[ {reel1} | {reel2} | {reel3} ]", inline=False)
        embed.add_field(name="Bet", value=f"{bet} coins", inline=True)
        embed.add_field(name="Won", value=f"{winnings} coins", inline=True)
        embed.add_field(name="Net", value=f"{'+'if net_result >= 0 else ''}{net_result} coins", inline=True)
        embed.add_field(name="Balance", value=f"{user_coins + net_result:,} coins", inline=True)
        
        if win_text:
            embed.add_field(name="Result", value=win_text, inline=False)
        
        view = SlotsView(user_id)
        await interaction.response.edit_message(embed=embed, view=view)

class BlackjackView(discord.ui.View):
    def __init__(self, user_id, bet, player_hand, dealer_hand, deck):
        super().__init__(timeout=300)
        self.user_id = user_id
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
        user_id = str(interaction.user.id)
        user_coins = data.get("coins", {}).get(user_id, 0)
        effects = await get_gambling_effects(user_id, data)
        
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        # Calculate winnings
        if result in ["player_win", "dealer_bust"]:
            if len(self.player_hand) == 2 and player_value == 21:  # Blackjack
                winnings = int(self.bet * 2.5)
                result_text = "🎉 BLACKJACK!"
            else:
                winnings = self.bet * 2
                result_text = "🎊 You win!"
        elif result == "tie":
            winnings = self.bet
            result_text = "🤝 Push (tie)"
        else:  # bust or dealer_win
            winnings = 0
            result_text = "😔 You lose!"
            
            # Apply insurance
            if effects["insurance"]:
                refund = self.bet // 2
                winnings = refund
                result_text += f"\n🛡️ Insurance: +{refund} coins"
                await consume_item_effect(user_id, "insurance_scroll", data)
        
        net_result = winnings - self.bet
        data.setdefault("coins", {})[user_id] = user_coins + net_result
        
        # Add transaction
        if net_result > 0:
            add_transaction(user_id, net_result, "Blackjack win", data, "credit")
        elif net_result < 0:
            add_transaction(user_id, abs(net_result), "Blackjack loss", data, "debit")
        
        # Consume effects
        if winnings > self.bet and effects["win_chance_bonus"] > 0:
            await consume_item_effect(user_id, "lucky_potion", data)
            await consume_item_effect(user_id, "mega_lucky_potion", data)
        
        await save_data(data)
        
        embed = discord.Embed(title="🃏 Blackjack - Game Over", color=0x27ae60 if net_result > 0 else 0xe74c3c)
        embed.add_field(name="Your Hand", value=f"{self.format_hand(self.player_hand)} (Value: {player_value})", inline=False)
        embed.add_field(name="Dealer Hand", value=f"{self.format_hand(self.dealer_hand)} (Value: {dealer_value})", inline=False)
        embed.add_field(name="Result", value=result_text, inline=False)
        embed.add_field(name="Bet", value=f"{self.bet} coins", inline=True)
        embed.add_field(name="Won", value=f"{winnings} coins", inline=True)
        embed.add_field(name="Net", value=f"{'+'if net_result >= 0 else ''}{net_result} coins", inline=True)
        embed.add_field(name="Balance", value=f"{user_coins + net_result:,} coins", inline=True)
        
        await interaction.response.edit_message(embed=embed, view=None)

class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="slots", description="Play slot machine with item bonuses!")
    @app_commands.describe(bet="Amount to bet (default: 10)")
    async def slots(self, interaction: discord.Interaction, bet: int = 10):
        user_id = str(interaction.user.id)
        
        if bet < 1:
            await interaction.response.send_message("❌ Minimum bet is 1 coin!", ephemeral=True)
            return
        
        data = await load_data()
        
        # Check cooldown
        cooldown = check_cooldown(user_id, "slots", data, 10)
        if cooldown > 0:
            await interaction.response.send_message(f"⏰ Cooldown active! Wait {cooldown} seconds.", ephemeral=True)
            return
        
        user_coins = data.get("coins", {}).get(user_id, 0)
        if user_coins < bet:
            await interaction.response.send_message(f"❌ You need {bet} coins! Your balance: {user_coins}", ephemeral=True)
            return
        
        set_cooldown(user_id, "slots", data)
        await save_data(data)
        
        embed = discord.Embed(title="🎰 Slot Machine", description="Choose your bet amount:", color=0xf1c40f)
        embed.add_field(name="Your Balance", value=f"{user_coins:,} coins", inline=True)
        embed.add_field(name="Current Bet", value=f"{bet} coins", inline=True)
        
        # Show active effects
        effects = await get_gambling_effects(user_id, data)
        if effects["win_chance_bonus"] > 0:
            embed.add_field(name="🍀 Luck Bonus", value=f"+{effects['win_chance_bonus']*100:.0f}%", inline=True)
        if effects["payout_bonus"] > 0:
            embed.add_field(name="💰 Payout Bonus", value=f"+{effects['payout_bonus']*100:.0f}%", inline=True)
        if effects["insurance"]:
            embed.add_field(name="🛡️ Insurance", value="50% refund on loss", inline=True)
        
        embed.set_footer(text="🎲 Payouts: 💎x50, ⭐x15, 🍇x8, 🍊x5, 🍋x4, 🍒x3")
        
        view = SlotsView(user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="coinflip", description="Flip a coin and double your money!")
    @app_commands.describe(bet="Amount to bet", choice="Choose heads or tails")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip(self, interaction: discord.Interaction, bet: int, choice: str):
        user_id = str(interaction.user.id)
        
        if bet < 1:
            await interaction.response.send_message("❌ Minimum bet is 1 coin!", ephemeral=True)
            return
        
        data = await load_data()
        
        # Check cooldown
        cooldown = check_cooldown(user_id, "coinflip", data, 15)
        if cooldown > 0:
            await interaction.response.send_message(f"⏰ Cooldown active! Wait {cooldown} seconds.", ephemeral=True)
            return
        
        user_coins = data.get("coins", {}).get(user_id, 0)
        if user_coins < bet:
            await interaction.response.send_message(f"❌ You need {bet} coins! Your balance: {user_coins}", ephemeral=True)
            return
        
        # Get effects and calculate win chance
        effects = await get_gambling_effects(user_id, data)
        base_chance = 0.5
        win_chance = min(0.95, base_chance + effects["win_chance_bonus"])  # Cap at 95%
        
        # Flip coin
        result = "heads" if random.random() < win_chance else "tails"
        won = (choice == result)
        
        if won:
            winnings = bet * 2
            net_result = bet
            result_text = f"🎉 You won! The coin landed on {result}!"
            color = 0x27ae60
        else:
            winnings = 0
            net_result = -bet
            result_text = f"😔 You lost! The coin landed on {result}."
            color = 0xe74c3c
            
            # Apply insurance
            if effects["insurance"]:
                refund = bet // 2
                net_result += refund
                result_text += f"\n🛡️ Insurance activated! Refunded {refund} coins"
                await consume_item_effect(user_id, "insurance_scroll", data)
        
        # Update balance
        data.setdefault("coins", {})[user_id] = user_coins + net_result
        
        # Add transaction
        if net_result > 0:
            add_transaction(user_id, net_result, "Coinflip win", data, "credit")
        else:
            add_transaction(user_id, abs(net_result), "Coinflip loss", data, "debit")
        
        # Consume luck effects
        if won and effects["win_chance_bonus"] > 0:
            await consume_item_effect(user_id, "lucky_potion", data)
            await consume_item_effect(user_id, "mega_lucky_potion", data)
        
        set_cooldown(user_id, "coinflip", data)
        await save_data(data)
        
        # Show result
        coin_emoji = "🪙" if result == "heads" else "🔄"
        embed = discord.Embed(title=f"{coin_emoji} Coinflip", color=color)
        embed.add_field(name="Your Choice", value=choice.title(), inline=True)
        embed.add_field(name="Result", value=result.title(), inline=True)
        embed.add_field(name="Outcome", value="WIN" if won else "LOSS", inline=True)
        embed.add_field(name="Bet", value=f"{bet} coins", inline=True)
        embed.add_field(name="Net", value=f"{'+'if net_result >= 0 else ''}{net_result} coins", inline=True)
        embed.add_field(name="Balance", value=f"{user_coins + net_result:,} coins", inline=True)
        embed.description = result_text
        
        if effects["win_chance_bonus"] > 0:
            embed.set_footer(text=f"🍀 You had {win_chance*100:.1f}% win chance!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="blackjack", description="Play blackjack against the dealer!")
    @app_commands.describe(bet="Amount to bet")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        user_id = str(interaction.user.id)
        
        if bet < 1:
            await interaction.response.send_message("❌ Minimum bet is 1 coin!", ephemeral=True)
            return
        
        data = await load_data()
        
        # Check cooldown
        cooldown = check_cooldown(user_id, "blackjack", data, 20)
        if cooldown > 0:
            await interaction.response.send_message(f"⏰ Cooldown active! Wait {cooldown} seconds.", ephemeral=True)
            return
        
        user_coins = data.get("coins", {}).get(user_id, 0)
        if user_coins < bet:
            await interaction.response.send_message(f"❌ You need {bet} coins! Your balance: {user_coins}", ephemeral=True)
            return
        
        # Create deck and deal initial hands
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [rank for rank in ranks for _ in suits]
        random.shuffle(deck)
        
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        
        view = BlackjackView(user_id, bet, player_hand, dealer_hand, deck)
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
            set_cooldown(user_id, "blackjack", data)
            await save_data(data)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="ratrace", description="Bet on rat races with lucky coin bonus!")
    @app_commands.describe(bet="Amount to bet", rat="Choose your rat (1-6)")
    @app_commands.choices(rat=[
        app_commands.Choice(name="Rat 1 🐭", value=1),
        app_commands.Choice(name="Rat 2 🐀", value=2),
        app_commands.Choice(name="Rat 3 🐁", value=3),
        app_commands.Choice(name="Rat 4 🐭", value=4),
        app_commands.Choice(name="Rat 5 🐀", value=5),
        app_commands.Choice(name="Rat 6 🐁", value=6)
    ])
    async def ratrace(self, interaction: discord.Interaction, bet: int, rat: int):
        user_id = str(interaction.user.id)
        
        if bet < 1:
            await interaction.response.send_message("❌ Minimum bet is 1 coin!", ephemeral=True)
            return
        
        data = await load_data()
        
        # Check cooldown
        cooldown = check_cooldown(user_id, "ratrace", data, 25)
        if cooldown > 0:
            await interaction.response.send_message(f"⏰ Cooldown active! Wait {cooldown} seconds.", ephemeral=True)
            return
        
        user_coins = data.get("coins", {}).get(user_id, 0)
        if user_coins < bet:
            await interaction.response.send_message(f"❌ You need {bet} coins! Your balance: {user_coins}", ephemeral=True)
            return
        
        # Get effects
        effects = await get_gambling_effects(user_id, data)
        
        # Check for lucky coin bonus (rat race specific)
        equipment = data.get("equipment", {}).get(user_id, {})
        has_lucky_coin = equipment.get("accessory") == "lucky_coin"
        
        # Simulate race
        rat_names = ["🐭 Squeaky", "🐀 Whiskers", "🐁 Nibbles", "🐭 Speedy", "🐀 Chomper", "🐁 Dash"]
        winner = random.randint(1, 6)
        
        # Apply lucky coin effect
        if has_lucky_coin and random.random() < 0.05:  # 5% bonus chance
            winner = rat
        
        if rat == winner:
            winnings = bet * 6  # 6:1 payout
            if has_lucky_coin:
                bonus = int(winnings * 0.05)  # 5% bonus
                winnings += bonus
            net_result = winnings - bet
            result_text = f"🎉 {rat_names[rat-1]} wins the race!"
            if has_lucky_coin:
                result_text += f"\n🪙 Lucky coin bonus: +{bonus} coins!"
            color = 0x27ae60
        else:
            winnings = 0
            net_result = -bet
            result_text = f"😔 {rat_names[winner-1]} won the race!"
            color = 0xe74c3c
            
            # Apply insurance
            if effects["insurance"]:
                refund = bet // 2
                net_result += refund
                result_text += f"\n🛡️ Insurance activated! Refunded {refund} coins"
                await consume_item_effect(user_id, "insurance_scroll", data)
        
        # Update balance
        data.setdefault("coins", {})[user_id] = user_coins + net_result
        
        # Add transaction
        if net_result > 0:
            add_transaction(user_id, net_result, "Rat race win", data, "credit")
        else:
            add_transaction(user_id, abs(net_result), "Rat race loss", data, "debit")
        
        set_cooldown(user_id, "ratrace", data)
        await save_data(data)
        
        # Create race visualization
        race_track = "🏁" + "━" * 10 + "🏁"
        rat_positions = [random.randint(1, 8) for _ in range(6)]
        rat_positions[winner-1] = 10  # Winner at finish line
        
        race_visual = []
        for i, pos in enumerate(rat_positions):
            track = "━" * pos + rat_names[i].split()[0] + "━" * (10-pos)
            if i == rat-1:  # User's rat
                track = track.replace("━", "═")  # Highlight user's rat
            race_visual.append(track)
        
        embed = discord.Embed(title="🏁 Rat Race Results", color=color)
        embed.add_field(name="Race Track", value="🏁" + "\n🏁".join(race_visual) + "\n🏁", inline=False)
        embed.add_field(name="Your Rat", value=rat_names[rat-1], inline=True)
        embed.add_field(name="Winner", value=rat_names[winner-1], inline=True)
        embed.add_field(name="Outcome", value="WIN" if rat == winner else "LOSS", inline=True)
        embed.add_field(name="Bet", value=f"{bet} coins", inline=True)
        embed.add_field(name="Net", value=f"{'+'if net_result >= 0 else ''}{net_result} coins", inline=True)
        embed.add_field(name="Balance", value=f"{user_coins + net_result:,} coins", inline=True)
        embed.description = result_text
        
        if has_lucky_coin:
            embed.set_footer(text="🪙 Lucky Coin equipped - bonus chances active!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Casino(bot))
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="casino", description="Open the casino hub.")
    async def casino(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎰 Casino Hub", description="Welcome to the casino! Choose your game:", color=0xffc300)
        embed.add_field(name="🎯 Roulette", value="`/roulette` - Spin the wheel of fortune!", inline=False)
        embed.add_field(name="🎰 Slots", value="`/slots` - Try your luck on the slot machine!", inline=False)
        embed.add_field(name="🃏 Blackjack", value="`/blackjack` - Beat the dealer at 21!", inline=False)
        embed.add_field(name="🐭 Rat Race", value="`/rat_race` - Bet on racing rats!", inline=False)
        embed.set_footer(text="💡 Tip: Use items like Lucky Potion to boost your chances!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="roulette", description="Spin the roulette wheel.")
    @app_commands.describe(bet="Amount to bet", choice="red, black, green, or a number (0-36)")
    async def roulette(self, interaction: discord.Interaction, bet: int, choice: str):
        if bet < 10:
            await interaction.response.send_message("❌ Minimum bet is 10 coins!", ephemeral=True)
            return
        
        user = interaction.user
        data = await load_data()
        
        # Initialize user data
        if str(user.id) not in data["coins"]:
            data["coins"][str(user.id)] = 0
        
        # Check if user has enough coins
        if data["coins"][str(user.id)] < bet:
            await interaction.response.send_message(
                f"❌ You don't have enough coins! You need {bet} coins but only have {data['coins'][str(user.id)]}.",
                ephemeral=True
            )
            return
        
        # Deduct bet
        data["coins"][str(user.id)] -= bet
        add_transaction(user.id, bet, "Roulette bet", data, tx_type="debit")
        
        # Roulette logic
        result = random.randint(0, 36)
        color = "green" if result == 0 else "red" if result % 2 == 1 else "black"
        
        won = False
        payout = 0
        
        if choice.lower() == color:
            won = True
            payout = bet * 2
        elif choice.isdigit() and int(choice) == result:
            won = True
            payout = bet * 35
        
        # Add winnings
        if won:
            data["coins"][str(user.id)] += payout
            add_transaction(user.id, payout, "Roulette win", data, tx_type="credit")
        
        # Save data
        await save_data(data, force=True)
        
        embed = discord.Embed(
            title="🎯 Roulette Result", 
            color=0x00ff00 if won else 0xff0000
        )
        embed.add_field(name="Result", value=f"{result} ({color})", inline=True)
        embed.add_field(name="Your Bet", value=f"{bet} on {choice}", inline=True)
        
        if won:
            embed.add_field(name="Outcome", value=f"✅ Won {payout} coins!", inline=True)
            embed.add_field(name="New Balance", value=f"💰 {data['coins'][str(user.id)]} coins", inline=False)
        else:
            embed.add_field(name="Outcome", value=f"❌ Lost {bet} coins", inline=True)
            embed.add_field(name="New Balance", value=f"💰 {data['coins'][str(user.id)]} coins", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="slots", description="Spin the slot machine.")
    @app_commands.describe(bet="Amount to bet on slots")
    async def slots(self, interaction: discord.Interaction, bet: int):
        if bet < 10:
            await interaction.response.send_message("❌ Minimum bet is 10 coins!", ephemeral=True)
            return
        
        user = interaction.user
        data = await load_data()
        
        # Initialize user data
        if str(user.id) not in data["coins"]:
            data["coins"][str(user.id)] = 0
        
        # Check if user has enough coins
        if data["coins"][str(user.id)] < bet:
            await interaction.response.send_message(
                f"❌ You don't have enough coins! You need {bet} coins but only have {data['coins'][str(user.id)]}.",
                ephemeral=True
            )
            return
        
        # Deduct bet
        data["coins"][str(user.id)] -= bet
        add_transaction(user.id, bet, "Slots bet", data, tx_type="debit")
        
        # Slots logic
        symbols = ["🍒", "🍋", "🍊", "🍇", "🔔", "💎", "🍀"]
        result = [random.choice(symbols) for _ in range(3)]
        
        # Calculate winnings
        payout = 0
        if result[0] == result[1] == result[2]:  # Triple match
            if result[0] == "💎":
                payout = bet * 50  # Jackpot
            elif result[0] == "🍀":
                payout = bet * 25
            else:
                payout = bet * 10
        elif result[0] == result[1] or result[1] == result[2]:  # Double match
            payout = bet * 2
        
        # Add winnings
        if payout > 0:
            data["coins"][str(user.id)] += payout
            add_transaction(user.id, payout, "Slots win", data, tx_type="credit")
        
        # Save data
        await save_data(data, force=True)
        
        embed = discord.Embed(
            title="🎰 Slot Machine", 
            color=0x00ff00 if payout > 0 else 0xff0000
        )
        embed.add_field(name="Result", value=" ".join(result), inline=False)
        embed.add_field(name="Bet", value=f"{bet} coins", inline=True)
        
        if payout > 0:
            embed.add_field(name="Payout", value=f"✅ Won {payout} coins!", inline=True)
            if payout >= bet * 25:
                embed.add_field(name="🎉 JACKPOT!", value="Amazing win!", inline=False)
        else:
            embed.add_field(name="Payout", value=f"❌ Lost {bet} coins", inline=True)
        
        embed.add_field(name="New Balance", value=f"💰 {data['coins'][str(user.id)]} coins", inline=False)
        
        await interaction.response.send_message(embed=embed)

    # Add more game commands here

async def setup(bot):
    await bot.add_cog(Casino(bot))
