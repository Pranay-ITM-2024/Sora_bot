"""
Casino and gambling commands cog
"""

import discord
from discord.ext import commands
import random
import asyncio
import datetime
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import DataManager, EQUIPABLE_ITEMS

class CasinoCommands(commands.Cog):
    """Casino and gambling commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='casino')
    async def casino(self, ctx):
        """Open the casino hub"""
        embed = discord.Embed(
            title="🎰 SORA Casino",
            description="Welcome to the most exciting casino in Discord! Choose your game:",
            color=0xffd700
        )
        embed.add_field(name="🎲 Roulette", value="Bet on numbers, colors, or sections", inline=True)
        embed.add_field(name="🎰 Slots", value="Spin the reels for jackpots!", inline=True)
        embed.add_field(name="🃏 Blackjack", value="Beat the dealer to 21", inline=True)
        embed.add_field(name="🐀 Rat Race", value="Bet on racing rats", inline=True)
        
        view = CasinoView(self.bot)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='roulette')
    async def roulette(self, ctx, bet_amount: int, bet_type: str, *, bet_value: str = ""):
        """Play roulette"""
        if bet_amount < 10 or bet_amount > 1000000:
            await ctx.send("❌ Bet amount must be between 10 and 1,000,000 coins!")
            return
        
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        if data["coins"].get(user_id, 0) < bet_amount:
            await ctx.send("❌ Insufficient funds!")
            return
        
        # Calculate win chance and payout
        if bet_type.lower() in ["red", "black", "even", "odd", "high", "low"]:
            win_chance = 18/37  # Nearly 50%
            payout_multiplier = 2
        elif bet_type.lower() == "dozen":
            win_chance = 12/37
            payout_multiplier = 3
        elif bet_type.lower() == "column":
            win_chance = 12/37
            payout_multiplier = 3
        elif bet_type.lower() == "corner":
            win_chance = 4/37
            payout_multiplier = 9
        elif bet_type.lower() == "street":
            win_chance = 3/37
            payout_multiplier = 12
        elif bet_type.lower() == "split":
            win_chance = 2/37
            payout_multiplier = 18
        elif bet_type.lower() == "straight":
            win_chance = 1/37
            payout_multiplier = 36
        else:
            await ctx.send("❌ Invalid bet type! Use: red, black, even, odd, high, low, dozen, column, corner, street, split, or straight")
            return
        
        # Apply gambling boost from equipped items
        equipped = data["equipped"].get(user_id, {})
        gambling_boost = 0
        for item_id, quantity in equipped.items():
            if item_id in EQUIPABLE_ITEMS and EQUIPABLE_ITEMS[item_id]["effect"] == "gambling_boost":
                gambling_boost += EQUIPABLE_ITEMS[item_id]["value"] * quantity
        
        # Check for active consumable effects
        active_effects = data["consumable_effects"].get(user_id, {})
        if "gambling_boost" in active_effects:
            gambling_boost += active_effects["gambling_boost"]
            del data["consumable_effects"][user_id]["gambling_boost"]
            if not data["consumable_effects"][user_id]:
                del data["consumable_effects"][user_id]
        
        # Apply boost to win chance
        win_chance = min(0.95, win_chance + gambling_boost)
        
        # Spin the wheel
        winning_number = random.randint(0, 36)
        is_red = winning_number in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        is_even = winning_number % 2 == 0 and winning_number != 0
        
        # Check if player won
        won = False
        if bet_type.lower() == "red" and is_red:
            won = True
        elif bet_type.lower() == "black" and not is_red and winning_number != 0:
            won = True
        elif bet_type.lower() == "even" and is_even:
            won = True
        elif bet_type.lower() == "odd" and not is_even and winning_number != 0:
            won = True
        elif bet_type.lower() == "high" and winning_number >= 19:
            won = True
        elif bet_type.lower() == "low" and winning_number <= 18 and winning_number != 0:
            won = True
        elif bet_type.lower() == "straight" and bet_value == str(winning_number):
            won = True
        
        # Update coins
        data["coins"][user_id] -= bet_amount
        if won:
            winnings = int(bet_amount * payout_multiplier)
            data["coins"][user_id] += winnings
            
            embed = discord.Embed(
                title="🎉 Roulette Win!",
                description=f"**Winning Number:** {winning_number}\n**Your Bet:** {bet_type} {bet_value}\n**Bet Amount:** {bet_amount:,} coins\n**Winnings:** {winnings:,} coins\n**Net Profit:** +{winnings - bet_amount:,} coins",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="💸 Roulette Loss",
                description=f"**Winning Number:** {winning_number}\n**Your Bet:** {bet_type} {bet_value}\n**Bet Amount:** {bet_amount:,} coins\n**Result:** Lost {bet_amount:,} coins",
                color=0xff0000
            )
        
        await DataManager.save_data(data)
        await ctx.send(embed=embed)
    
    @commands.command(name='slots')
    async def slots(self, ctx, bet_amount: int):
        """Play slot machine"""
        if bet_amount < 10 or bet_amount > 1000000:
            await ctx.send("❌ Bet amount must be between 10 and 1,000,000 coins!")
            return
        
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        if data["coins"].get(user_id, 0) < bet_amount:
            await ctx.send("❌ Insufficient funds!")
            return
        
        # Apply slots boost from equipped items
        equipped = data["equipped"].get(user_id, {})
        slots_boost = 0
        for item_id, quantity in equipped.items():
            if item_id in EQUIPABLE_ITEMS and EQUIPABLE_ITEMS[item_id]["effect"] == "slots_boost":
                slots_boost += EQUIPABLE_ITEMS[item_id]["value"] * quantity
        
        # Check for active consumable effects
        active_effects = data["consumable_effects"].get(user_id, {})
        payout_boost = 0
        if "payout_boost" in active_effects:
            payout_boost = active_effects["payout_boost"]
            del data["consumable_effects"][user_id]["payout_boost"]
            if not data["consumable_effects"][user_id]:
                del data["consumable_effects"][user_id]
        
        # Spin the reels
        symbols = ["🍒", "🍋", "🍊", "🍇", "🔔", "💎", "7️⃣"]
        reels = [random.choice(symbols) for _ in range(3)]
        
        # Calculate winnings
        winnings = 0
        if reels[0] == reels[1] == reels[2]:
            # Three of a kind
            if reels[0] == "7️⃣":
                winnings = bet_amount * 100  # Jackpot
            elif reels[0] == "💎":
                winnings = bet_amount * 50
            elif reels[0] == "🔔":
                winnings = bet_amount * 25
            elif reels[0] in ["🍇", "🍊"]:
                winnings = bet_amount * 10
            else:
                winnings = bet_amount * 5
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            # Two of a kind
            winnings = bet_amount * 2
        
        # Apply boosts
        winnings = int(winnings * (1 + slots_boost + payout_boost))
        
        # Update coins
        data["coins"][user_id] -= bet_amount
        data["coins"][user_id] += winnings
        
        # Create display
        reel_display = f"{reels[0]} | {reels[1]} | {reels[2]}"
        
        if winnings > bet_amount:
            embed = discord.Embed(
                title="🎰 Slots Win!",
                description=f"**Reels:** {reel_display}\n**Bet Amount:** {bet_amount:,} coins\n**Winnings:** {winnings:,} coins\n**Net Profit:** +{winnings - bet_amount:,} coins",
                color=0x00ff00
            )
        elif winnings > 0:
            embed = discord.Embed(
                title="🎰 Slots Win!",
                description=f"**Reels:** {reel_display}\n**Bet Amount:** {bet_amount:,} coins\n**Winnings:** {winnings:,} coins\n**Net Loss:** -{bet_amount - winnings:,} coins",
                color=0xffa500
            )
        else:
            embed = discord.Embed(
                title="💸 Slots Loss",
                description=f"**Reels:** {reel_display}\n**Bet Amount:** {bet_amount:,} coins\n**Result:** Lost {bet_amount:,} coins",
                color=0xff0000
            )
        
        await DataManager.save_data(data)
        await ctx.send(embed=embed)
    
    @commands.command(name='blackjack')
    async def blackjack(self, ctx, bet_amount: int):
        """Play blackjack"""
        if bet_amount < 10 or bet_amount > 1000000:
            await ctx.send("❌ Bet amount must be between 10 and 1,000,000 coins!")
            return
        
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        if data["coins"].get(user_id, 0) < bet_amount:
            await ctx.send("❌ Insufficient funds!")
            return
        
        # Start new game
        if user_id not in data["active_games"]:
            data["active_games"][user_id] = {}
        
        game_id = f"blackjack_{ctx.message.id}"
        data["active_games"][user_id][game_id] = {
            "type": "blackjack",
            "bet": bet_amount,
            "player_cards": [],
            "dealer_cards": [],
            "player_total": 0,
            "dealer_total": 0,
            "status": "playing"
        }
        
        # Deal initial cards
        player_cards = [random.randint(1, 13) for _ in range(2)]
        dealer_cards = [random.randint(1, 13), random.randint(1, 13)]
        
        data["active_games"][user_id][game_id]["player_cards"] = player_cards
        data["active_games"][user_id][game_id]["dealer_cards"] = dealer_cards
        
        # Calculate totals
        player_total = sum(min(card, 10) for card in player_cards)
        dealer_total = sum(min(card, 10) for card in dealer_cards)
        
        data["active_games"][user_id][game_id]["player_total"] = player_total
        data["active_games"][user_id][game_id]["dealer_total"] = dealer_total
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="🃏 Blackjack",
            description=f"**Your Cards:** {self.format_cards(player_cards)} (Total: {player_total})\n**Dealer Cards:** {self.format_cards([dealer_cards[0], '?'])} (Showing: {min(dealer_cards[0], 10)})",
            color=0x0099ff
        )
        
        view = BlackjackView(ctx.author, game_id)
        await ctx.send(embed=embed, view=view)
    
    def format_cards(self, cards):
        """Format cards for display"""
        formatted = []
        for card in cards:
            if card == '?':
                formatted.append('❓')
            elif card == 1:
                formatted.append('A')
            elif card == 11:
                formatted.append('J')
            elif card == 12:
                formatted.append('Q')
            elif card == 13:
                formatted.append('K')
            else:
                formatted.append(str(card))
        return ' '.join(formatted)
    
    @commands.command(name='rat_race')
    async def rat_race(self, ctx, bet_amount: int, rat_number: int):
        """Bet on racing rats"""
        if bet_amount < 10 or bet_amount > 1000000:
            await ctx.send("❌ Bet amount must be between 10 and 1,000,000 coins!")
            return
        
        if rat_number < 1 or rat_number > 6:
            await ctx.send("❌ Rat number must be between 1 and 6!")
            return
        
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        if data["coins"].get(user_id, 0) < bet_amount:
            await ctx.send("❌ Insufficient funds!")
            return
        
        # Add bet to active games
        if user_id not in data["active_games"]:
            data["active_games"][user_id] = {}
        
        game_id = f"ratrace_{ctx.message.id}"
        data["active_games"][user_id][game_id] = {
            "type": "rat_race",
            "bet": bet_amount,
            "rat": rat_number,
            "status": "betting"
        }
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="🐀 Rat Race Bet Placed!",
            description=f"You bet **{bet_amount:,} coins** on **Rat #{rat_number}**!\n\nRace will start in 30 seconds. Place your bets!",
            color=0xffa500
        )
        
        await ctx.send(embed=embed)
        
        # Start race after delay
        await asyncio.sleep(30)
        await self.run_rat_race(ctx, game_id, rat_number, bet_amount)
    
    async def run_rat_race(self, ctx, game_id, rat_number, bet_amount):
        """Run the actual rat race"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Remove bet from active games
        if user_id in data["active_games"] and game_id in data["active_games"][user_id]:
            del data["active_games"][user_id][game_id]
        
        # Determine winner
        winner = random.randint(1, 6)
        
        # Apply rat race boost from equipped items
        equipped = data["equipped"].get(user_id, {})
        rat_boost = 0
        for item_id, quantity in equipped.items():
            if item_id in EQUIPABLE_ITEMS and EQUIPABLE_ITEMS[item_id]["effect"] == "rat_race_boost":
                rat_boost += EQUIPABLE_ITEMS[item_id]["value"] * quantity
        
        if winner == rat_number:
            # Calculate winnings (5:1 payout)
            base_winnings = bet_amount * 5
            winnings = int(base_winnings * (1 + rat_boost))
            
            data["coins"][user_id] -= bet_amount
            data["coins"][user_id] += winnings
            
            embed = discord.Embed(
                title="🏆 Rat Race Win!",
                description=f"**Winner:** Rat #{winner}\n**Your Bet:** Rat #{rat_number}\n**Bet Amount:** {bet_amount:,} coins\n**Winnings:** {winnings:,} coins\n**Net Profit:** +{winnings - bet_amount:,} coins",
                color=0x00ff00
            )
        else:
            data["coins"][user_id] -= bet_amount
            
            embed = discord.Embed(
                title="💸 Rat Race Loss",
                description=f"**Winner:** Rat #{winner}\n**Your Bet:** Rat #{rat_number}\n**Bet Amount:** {bet_amount:,} coins\n**Result:** Lost {bet_amount:,} coins",
                color=0xff0000
            )
        
        await DataManager.save_data(data)
        await ctx.send(embed=embed)

class CasinoView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot
    
    @discord.ui.button(label='Roulette', style=discord.ButtonStyle.primary, emoji='🎲')
    async def roulette(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = GameModal("roulette", self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Slots', style=discord.ButtonStyle.primary, emoji='🎰')
    async def slots(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = GameModal("slots", self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Blackjack', style=discord.ButtonStyle.primary, emoji='🃏')
    async def blackjack(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = GameModal("blackjack", self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Rat Race', style=discord.ButtonStyle.primary, emoji='🐀')
    async def rat_race(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RatRaceModal(self.bot)
        await interaction.response.send_modal(modal)

class GameModal(discord.ui.Modal):
    def __init__(self, game_type, bot):
        super().__init__(title=f"{game_type.title()} Game")
        self.game_type = game_type
        self.bot = bot
        
        self.bet_input = discord.ui.TextInput(
            label="Bet Amount",
            placeholder="Enter amount to bet...",
            required=True
        )
        self.add_item(self.bet_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            bet_amount = int(self.bet_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
            return
        
        if self.game_type == "roulette":
            await interaction.response.send_message("❌ Roulette requires additional parameters. Use `/roulette <amount> <bet_type> [bet_value]`", ephemeral=True)
        elif self.game_type == "slots":
            # Execute slots command
            from discord.ext import commands
            ctx = await self.bot.get_context(interaction.message)
            await ctx.invoke(self.bot.get_command('slots'), bet_amount)
        elif self.game_type == "blackjack":
            # Execute blackjack command
            ctx = await self.bot.get_context(interaction.message)
            await ctx.invoke(self.bot.get_command('blackjack'), bet_amount)

class RatRaceModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Rat Race Bet")
        self.bot = bot
        
        self.bet_input = discord.ui.TextInput(
            label="Bet Amount",
            placeholder="Enter amount to bet...",
            required=True
        )
        self.add_item(self.bet_input)
        
        self.rat_input = discord.ui.TextInput(
            label="Rat Number (1-6)",
            placeholder="Enter rat number to bet on...",
            required=True
        )
        self.add_item(self.rat_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            bet_amount = int(self.bet_input.value)
            rat_number = int(self.rat_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Please enter valid numbers!", ephemeral=True)
            return
        
        # Execute rat race command
        ctx = await self.bot.get_context(interaction.message)
        await ctx.invoke(self.bot.get_command('rat_race'), bet_amount, rat_number)

class BlackjackView(discord.ui.View):
    def __init__(self, user, game_id):
        super().__init__(timeout=60)
        self.user = user
        self.game_id = game_id
    
    @discord.ui.button(label='Hit', style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
            return
        
        # Handle hit logic here
        await interaction.response.send_message("Hit logic not implemented yet!", ephemeral=True)
    
    @discord.ui.button(label='Stand', style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
            return
        
        # Handle stand logic here
        await interaction.response.send_message("Stand logic not implemented yet!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CasinoCommands(bot))
