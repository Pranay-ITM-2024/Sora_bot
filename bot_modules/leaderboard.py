"""
Leaderboard module: leaderboard, richest, topcasino, topguilds with comprehensive stats
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from .database import load_data, save_data

async def load_data_compat():
    """Load data using the new database system"""
    return await load_data()

def calculate_net_worth(user_id, data):
    """Calculate user's total net worth including all assets"""
    user_id = str(user_id)
    
    # Cash balance
    cash = data.get("coins", {}).get(user_id, 0)
    
    # Bank balance
    bank = data.get("bank", {}).get(user_id, 0)
    
    # Stock portfolio value
    portfolio_value = 0
    portfolio = data.get("stock_portfolios", {}).get(user_id, {})
    if portfolio:
        # Simplified portfolio value calculation
        for symbol, shares in portfolio.items():
            # Use base price for consistency (in real app, use current market price)
            stock_data = {
                "TECH": 150, "BANK": 80, "MINE": 45, "FOOD": 60,
                "ENERGY": 90, "HEALTH": 120, "AUTO": 70, "RETAIL": 35
            }
            base_price = stock_data.get(symbol, 50)
            portfolio_value += shares * base_price
    
    # Inventory value (simplified - could calculate based on shop prices)
    inventory_value = 0
    inventory = data.get("inventories", {}).get(user_id, {})
    if inventory:
        # Rough item values
        item_values = {
            "lucky_potion": 150, "mega_lucky_potion": 400, "jackpot_booster": 200,
            "robbers_mask": 250, "insurance_scroll": 300, "mimic_repellent": 500,
            "gamblers_charm": 400, "golden_dice": 600, "security_dog": 700,
            "vault_key": 800, "master_lockpick": 750, "lucky_coin": 300,
            "shadow_cloak": 600, "common_chest": 100, "rare_chest": 300,
            "epic_chest": 600, "legendary_chest": 1200
        }
        for item, count in inventory.items():
            item_value = item_values.get(item, 10)  # Default value
            inventory_value += item_value * count
    
    return cash + bank + portfolio_value + inventory_value

def get_user_stats(user_id, data):
    """Get comprehensive user statistics"""
    user_id = str(user_id)
    
    # Transaction history analysis
    transactions = data.get("transactions", {}).get(user_id, [])
    
    total_earned = sum(tx["amount"] for tx in transactions if tx["type"] == "credit")
    total_spent = sum(tx["amount"] for tx in transactions if tx["type"] == "debit")
    transaction_count = len(transactions)
    
    # Casino wins/losses
    casino_wins = sum(1 for tx in transactions if tx["type"] == "credit" and any(game in tx["reason"].lower() for game in ["slots", "coinflip", "blackjack", "ratrace"]))
    casino_losses = sum(1 for tx in transactions if tx["type"] == "debit" and any(game in tx["reason"].lower() for game in ["slots", "coinflip", "blackjack", "ratrace"]))
    
    # Item usage
    equipment = data.get("equipment", {}).get(user_id, {})
    consumable_effects = data.get("consumable_effects", {}).get(user_id, {})
    
    return {
        "net_worth": calculate_net_worth(user_id, data),
        "total_earned": total_earned,
        "total_spent": total_spent,
        "transaction_count": transaction_count,
        "casino_wins": casino_wins,
        "casino_losses": casino_losses,
        "equipped_items": len(equipment),
        "active_consumables": len(consumable_effects)
    }

class LeaderboardView(discord.ui.View):
    def __init__(self, bot, guild_id):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id

    @discord.ui.select(
        placeholder="Choose a leaderboard category...",
        options=[
            discord.SelectOption(label="💰 Richest Users", description="Top users by total net worth", emoji="💰"),
            discord.SelectOption(label="🏦 Bank Balance", description="Highest bank balances", emoji="🏦"),
            discord.SelectOption(label="🎰 Casino Champions", description="Most casino wins", emoji="🎰"),
            discord.SelectOption(label="📈 Stock Tycoons", description="Highest portfolio values", emoji="📈"),
            discord.SelectOption(label="🏰 Guild Rankings", description="Richest guild leaderboard", emoji="🏰"),
            discord.SelectOption(label="💎 Item Collectors", description="Most valuable inventories", emoji="💎"),
        ]
    )
    async def leaderboard_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        category = select.values[0]
        await self.show_leaderboard(interaction, category)

    async def show_leaderboard(self, interaction, category):
        data = await load_data_compat()
        from .database import get_server_data
        server_data = get_server_data(data, self.guild_id)
        
        if category == "💰 Richest Users":
            await self.show_richest_users(interaction, server_data)
        elif category == "🏦 Bank Balance":
            await self.show_bank_leaderboard(interaction, server_data)
        elif category == "🎰 Casino Champions":
            await self.show_casino_leaderboard(interaction, server_data)
        elif category == "📈 Stock Tycoons":
            await self.show_stock_leaderboard(interaction, server_data)
        elif category == "🏰 Guild Rankings":
            await self.show_guild_leaderboard(interaction, server_data)
        elif category == "💎 Item Collectors":
            await self.show_inventory_leaderboard(interaction, server_data)

    async def show_richest_users(self, interaction, data):
        # Calculate net worth for all users
        user_net_worths = []
        all_users = set()
        
        # Collect all user IDs
        for section in ["coins", "bank", "inventories", "stock_portfolios"]:
            if section in data:
                all_users.update(data[section].keys())
        
        for user_id in all_users:
            net_worth = calculate_net_worth(user_id, data)
            if net_worth > 0:  # Only include users with assets
                user_net_worths.append((user_id, net_worth))
        
        # Sort by net worth
        user_net_worths.sort(key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(title="💰 Richest Users", description="Top users by total net worth (cash + bank + stocks + items)", color=0xf1c40f)
        
        leaderboard_text = []
        for i, (user_id, net_worth) in enumerate(user_net_worths[:10], 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                username = user.display_name
            except:
                username = f"User {user_id}"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            # Show breakdown
            cash = data.get("coins", {}).get(user_id, 0)
            bank = data.get("bank", {}).get(user_id, 0)
            
            leaderboard_text.append(f"{medal} **{username}**\n    💎 {net_worth:,} total • 💰 {cash:,} cash • 🏦 {bank:,} bank")
        
        if leaderboard_text:
            embed.add_field(name="🏆 Top 10", value="\n\n".join(leaderboard_text), inline=False)
        else:
            embed.add_field(name="🏆 Leaderboard", value="No users with assets found!", inline=False)
        
        embed.set_footer(text="💡 Net worth includes cash, bank, stocks, and inventory value! • Data protected by multi-layer backup system")
        
        await interaction.response.edit_message(embed=embed, view=self)

    async def show_bank_leaderboard(self, interaction, data):
        bank_balances = data.get("bank", {})
        
        # Sort by bank balance
        sorted_banks = sorted(bank_balances.items(), key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(title="🏦 Bank Balance Leaders", description="Users with the highest bank savings", color=0x3498db)
        
        leaderboard_text = []
        for i, (user_id, balance) in enumerate(sorted_banks[:10], 1):
            if balance <= 0:
                continue
                
            try:
                user = await self.bot.fetch_user(int(user_id))
                username = user.display_name
            except:
                username = f"User {user_id}"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            # Calculate interest rate
            base_rate = 0.05  # 5% base
            # Add guild bonus if applicable
            bonus_rate = 0  # Would calculate guild bonus here
            
            daily_interest = balance * (base_rate + bonus_rate)
            
            leaderboard_text.append(f"{medal} **{username}**\n    🏦 {balance:,} coins • 📈 +{daily_interest:.0f}/day interest")
        
        if leaderboard_text:
            embed.add_field(name="🏆 Top Savers", value="\n\n".join(leaderboard_text), inline=False)
        else:
            embed.add_field(name="🏆 Leaderboard", value="No bank accounts found!", inline=False)
        
        embed.set_footer(text="💡 Higher balances earn more daily interest!")
        
        await interaction.response.edit_message(embed=embed, view=self)

    async def show_casino_leaderboard(self, interaction, data):
        # Use new casino_stats tracking system
        casino_stats_data = data.get("casino_stats", {})
        
        player_stats = {}
        for user_id, stats in casino_stats_data.items():
            total_games = stats.get("total_games", 0)
            wins = stats.get("wins", 0)
            losses = stats.get("losses", 0)
            
            if total_games > 0:
                win_rate = (wins / total_games) * 100
                player_stats[user_id] = {
                    "wins": wins,
                    "losses": losses,
                    "total_games": total_games,
                    "win_rate": win_rate,
                    "total_bet": stats.get("total_bet", 0),
                    "total_won": stats.get("total_won", 0)
                }
        
        # Sort by total games played, then by wins
        sorted_players = sorted(player_stats.items(), key=lambda x: (x[1]["total_games"], x[1]["wins"]), reverse=True)
        
        embed = discord.Embed(title="🎰 Casino Champions", description="Top performers at casino games", color=0xe91e63)
        
        leaderboard_text = []
        for i, (user_id, stats) in enumerate(sorted_players[:10], 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                username = user.display_name
            except:
                username = f"User {user_id}"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            # Calculate profit/loss
            net_profit = stats['total_won'] - stats['total_bet']
            profit_sign = "+" if net_profit >= 0 else ""
            
            leaderboard_text.append(
                f"{medal} **{username}**\n"
                f"    � {stats['total_games']} games • "
                f"✅ {stats['wins']}W / ❌ {stats['losses']}L • "
                f"📊 {stats['win_rate']:.1f}% win rate\n"
                f"    💰 Net: {profit_sign}{net_profit:,} coins"
            )
        
        if leaderboard_text:
            embed.add_field(name="🏆 Top Gamblers", value="\n\n".join(leaderboard_text), inline=False)
        else:
            embed.add_field(name="🏆 Leaderboard", value="No casino activity found!", inline=False)
        
        embed.set_footer(text="🎲 Based on wins across slots, coinflip, blackjack, and rat race!")
        
        await interaction.response.edit_message(embed=embed, view=self)

    async def show_stock_leaderboard(self, interaction, data):
        # Calculate portfolio values
        portfolio_values = {}
        
        for user_id, portfolio in data.get("stock_portfolios", {}).items():
            total_value = 0
            stock_data = {
                "TECH": 150, "BANK": 80, "MINE": 45, "FOOD": 60,
                "ENERGY": 90, "HEALTH": 120, "AUTO": 70, "RETAIL": 35
            }
            
            for symbol, shares in portfolio.items():
                base_price = stock_data.get(symbol, 50)
                total_value += shares * base_price
            
            if total_value > 0:
                portfolio_values[user_id] = {
                    "value": total_value,
                    "positions": len(portfolio)
                }
        
        # Sort by portfolio value
        sorted_portfolios = sorted(portfolio_values.items(), key=lambda x: x[1]["value"], reverse=True)
        
        embed = discord.Embed(title="📈 Stock Market Tycoons", description="Top stock portfolio values", color=0x2ecc71)
        
        leaderboard_text = []
        for i, (user_id, stats) in enumerate(sorted_portfolios[:10], 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                username = user.display_name
            except:
                username = f"User {user_id}"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            leaderboard_text.append(f"{medal} **{username}**\n    📊 {stats['value']:,.0f} coins • 🏭 {stats['positions']} positions")
        
        if leaderboard_text:
            embed.add_field(name="🏆 Top Investors", value="\n\n".join(leaderboard_text), inline=False)
        else:
            embed.add_field(name="🏆 Leaderboard", value="No stock positions found!", inline=False)
        
        embed.set_footer(text="📈 Portfolio values based on current market prices!")
        
        await interaction.response.edit_message(embed=embed, view=self)

    async def show_guild_leaderboard(self, interaction, data):
        guilds = data.get("guilds", {})
        guild_members = data.get("guild_members", {})
        
        guild_stats = []
        for guild_name, guild_data in guilds.items():
            member_count = len(guild_members.get(guild_name, []))
            bank_balance = guild_data.get("bank", 0)
            
            if bank_balance > 0 or member_count > 0:
                guild_stats.append({
                    "name": guild_name,
                    "bank": bank_balance,
                    "members": member_count,
                    "owner": guild_data.get("owner")
                })
        
        # Sort by bank balance
        guild_stats.sort(key=lambda x: x["bank"], reverse=True)
        
        embed = discord.Embed(title="🏰 Guild Rankings", description="Richest and most powerful guilds", color=0x9b59b6)
        
        leaderboard_text = []
        for i, guild in enumerate(guild_stats[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            # Get owner name
            try:
                owner = await self.bot.fetch_user(int(guild["owner"])) if guild["owner"] else None
                owner_name = owner.display_name if owner else "Unknown"
            except:
                owner_name = "Unknown"
            
            # Calculate bonuses
            bonuses = []
            if i == 1:
                # Top guild gets the special interest bonus
                bonuses = ["🏆 +5% Bank Interest Bonus (10% total!)"]
            
            bonus_text = f"\n    🎉 {', '.join(bonuses)}" if bonuses else ""
            
            leaderboard_text.append(f"{medal} **{guild['name']}**\n    🏦 {guild['bank']:,} coins • 👥 {guild['members']} members • 👑 {owner_name}{bonus_text}")
        
        if leaderboard_text:
            embed.add_field(name="🏆 Top Guilds", value="\n\n".join(leaderboard_text), inline=False)
        else:
            embed.add_field(name="🏆 Leaderboard", value="No guilds found!", inline=False)
        
        embed.set_footer(text="� #1 Guild gets +5% extra bank interest bonus for all members!")
        
        await interaction.response.edit_message(embed=embed, view=self)

    async def show_inventory_leaderboard(self, interaction, data):
        # Calculate inventory values
        inventory_values = {}
        
        item_values = {
            "lucky_potion": 150, "mega_lucky_potion": 400, "jackpot_booster": 200,
            "robbers_mask": 250, "insurance_scroll": 300, "mimic_repellent": 500,
            "gamblers_charm": 400, "golden_dice": 600, "security_dog": 700,
            "vault_key": 800, "master_lockpick": 750, "lucky_coin": 300,
            "shadow_cloak": 600, "common_chest": 100, "rare_chest": 300,
            "epic_chest": 600, "legendary_chest": 1200
        }
        
        for user_id, inventory in data.get("inventories", {}).items():
            total_value = 0
            item_count = 0
            
            for item, count in inventory.items():
                item_value = item_values.get(item, 10)
                total_value += item_value * count
                item_count += count
            
            if total_value > 0:
                inventory_values[user_id] = {
                    "value": total_value,
                    "items": item_count
                }
        
        # Sort by inventory value
        sorted_inventories = sorted(inventory_values.items(), key=lambda x: x[1]["value"], reverse=True)
        
        embed = discord.Embed(title="💎 Item Collectors", description="Most valuable item collections", color=0xe67e22)
        
        leaderboard_text = []
        for i, (user_id, stats) in enumerate(sorted_inventories[:10], 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                username = user.display_name
            except:
                username = f"User {user_id}"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            leaderboard_text.append(f"{medal} **{username}**\n    💎 {stats['value']:,} coins value • 📦 {stats['items']} items")
        
        if leaderboard_text:
            embed.add_field(name="🏆 Top Collectors", value="\n\n".join(leaderboard_text), inline=False)
        else:
            embed.add_field(name="🏆 Leaderboard", value="No inventories found!", inline=False)
        
        embed.set_footer(text="💎 Based on estimated market value of all items!")
        
        await interaction.response.edit_message(embed=embed, view=self)

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View comprehensive leaderboards and rankings!")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        
        embed = discord.Embed(title="🏆 SORABOT Leaderboards", description="Choose a category to view rankings for THIS server", color=0xf39c12)
        embed.add_field(
            name="🏅 Available Categories",
            value="• 💰 **Richest Users** - Total net worth\n"
                  "• 🏦 **Bank Leaders** - Highest savings\n"
                  "• 🎰 **Casino Champions** - Most wins\n"
                  "• 📈 **Stock Tycoons** - Portfolio values\n"
                  "• 🏰 **Guild Rankings** - Guild power\n"
                  "• 💎 **Item Collectors** - Inventory value",
            inline=False
        )
        embed.set_footer(text="🎯 Server-specific rankings! Each Discord server has separate leaderboards")
        
        view = LeaderboardView(self.bot, guild_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="mystats", description="View your detailed statistics and rankings!")
    async def mystats(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        data = await load_data_compat()
        from .database import get_server_data
        server_data = get_server_data(data, guild_id)
        
        stats = get_user_stats(user_id, server_data)
        
        embed = discord.Embed(title=f"📊 {interaction.user.display_name}'s Statistics", color=0x3498db)
        
        # Financial stats
        embed.add_field(name="💰 Net Worth", value=f"{stats['net_worth']:,} coins", inline=True)
        embed.add_field(name="📈 Total Earned", value=f"{stats['total_earned']:,} coins", inline=True)
        embed.add_field(name="📉 Total Spent", value=f"{stats['total_spent']:,} coins", inline=True)
        
        # Activity stats
        embed.add_field(name="🔄 Transactions", value=f"{stats['transaction_count']:,}", inline=True)
        embed.add_field(name="🎰 Casino Wins", value=f"{stats['casino_wins']:,}", inline=True)
        embed.add_field(name="😔 Casino Losses", value=f"{stats['casino_losses']:,}", inline=True)
        
        # Item stats
        embed.add_field(name="⚔️ Equipped Items", value=f"{stats['equipped_items']}", inline=True)
        embed.add_field(name="🧪 Active Effects", value=f"{stats['active_consumables']}", inline=True)
        
        # Calculate win rate
        total_casino = stats['casino_wins'] + stats['casino_losses']
        win_rate = (stats['casino_wins'] / total_casino * 100) if total_casino > 0 else 0
        embed.add_field(name="🎯 Casino Win Rate", value=f"{win_rate:.1f}%", inline=True)
        
        # Portfolio info
        portfolio = data.get("stock_portfolios", {}).get(user_id, {})
        if portfolio:
            embed.add_field(name="📊 Stock Positions", value=f"{len(portfolio)} companies", inline=True)
        
        # Guild info
        guild_members = data.get("guild_members", {})
        user_guild = None
        for guild_name, members in guild_members.items():
            if user_id in members:
                user_guild = guild_name
                break
        
        if user_guild:
            embed.add_field(name="🏰 Guild", value=user_guild, inline=True)
        
        embed.set_footer(text="🏆 Use /leaderboard to see how you rank against others!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="richest", description="Quick view of the richest users!")
    async def richest(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        
        data = await load_data_compat()
        from .database import get_server_data
        server_data = get_server_data(data, guild_id)
        
        # Calculate top 5 richest users FOR THIS SERVER
        user_net_worths = []
        all_users = set()
        
        for section in ["coins", "bank", "inventories", "stock_portfolios"]:
            if section in server_data:
                all_users.update(server_data[section].keys())
        
        for user_id in all_users:
            net_worth = calculate_net_worth(user_id, server_data)
            if net_worth > 0:
                user_net_worths.append((user_id, net_worth))
        
        user_net_worths.sort(key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(title="💰 Top 5 Richest Users", color=0xf1c40f)
        
        if user_net_worths:
            leaderboard_text = []
            for i, (user_id, net_worth) in enumerate(user_net_worths[:5], 1):
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    username = user.display_name
                except:
                    username = f"User {user_id}"
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
                leaderboard_text.append(f"{medal} **{username}** - {net_worth:,} coins")
            
            embed.description = "\n".join(leaderboard_text)
        else:
            embed.description = "No users with assets found!"
        
        embed.set_footer(text="💡 Use /leaderboard for more detailed rankings!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
