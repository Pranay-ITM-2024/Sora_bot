"""
Market module: stocks, buystock, sellstock with full integration and item effects
"""
import discord
from discord import app_commands
from discord.ext import commands
import json
import aiofiles
from pathlib import Path
import asyncio
import random
from datetime import datetime, timedelta

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

def get_stock_data():
    """Get stock market data with realistic companies and sectors"""
    return {
        "TECH": {
            "name": "TechCorp Industries",
            "sector": "Technology",
            "base_price": 150,
            "volatility": 0.15,
            "description": "Leading technology and software company"
        },
        "BANK": {
            "name": "Global Banking Corp",
            "sector": "Financial",
            "base_price": 80,
            "volatility": 0.08,
            "description": "International banking and financial services"
        },
        "MINE": {
            "name": "Mining Dynamics Ltd",
            "sector": "Materials",
            "base_price": 45,
            "volatility": 0.25,
            "description": "Gold and precious metals mining"
        },
        "FOOD": {
            "name": "FoodChain Global",
            "sector": "Consumer Goods",
            "base_price": 60,
            "volatility": 0.12,
            "description": "International food and beverage company"
        },
        "ENERGY": {
            "name": "PowerGen Solutions",
            "sector": "Energy",
            "base_price": 90,
            "volatility": 0.20,
            "description": "Renewable energy and power generation"
        },
        "HEALTH": {
            "name": "MediCore Pharmaceuticals",
            "sector": "Healthcare",
            "base_price": 120,
            "volatility": 0.10,
            "description": "Medical research and pharmaceuticals"
        },
        "AUTO": {
            "name": "AutoDrive Motors",
            "sector": "Automotive",
            "base_price": 70,
            "volatility": 0.18,
            "description": "Electric vehicle manufacturing"
        },
        "RETAIL": {
            "name": "ShopSmart Retail",
            "sector": "Retail",
            "base_price": 35,
            "volatility": 0.14,
            "description": "Global retail and e-commerce"
        }
    }

def calculate_stock_price(symbol, data):
    """Calculate current stock price based on market conditions"""
    stock_info = get_stock_data().get(symbol)
    if not stock_info:
        return 0
    
    base_price = stock_info["base_price"]
    volatility = stock_info["volatility"]
    
    # Get or initialize price history
    market_data = data.get("stock_market", {})
    price_history = market_data.get("price_history", {}).get(symbol, [])
    
    # If no history, start at base price
    if not price_history:
        return base_price
    
    # Get last price
    last_price = price_history[-1]["price"]
    
    # Calculate price change (random walk with mean reversion)
    change_percent = random.gauss(0, volatility)
    
    # Mean reversion towards base price
    if last_price > base_price * 1.5:
        change_percent -= 0.05  # Pressure to go down
    elif last_price < base_price * 0.5:
        change_percent += 0.05  # Pressure to go up
    
    new_price = max(1, last_price * (1 + change_percent))
    return round(new_price, 2)

def update_stock_prices(data):
    """Update all stock prices"""
    market_data = data.setdefault("stock_market", {})
    price_history = market_data.setdefault("price_history", {})
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    for symbol in get_stock_data().keys():
        new_price = calculate_stock_price(symbol, data)
        
        history = price_history.setdefault(symbol, [])
        history.append({
            "price": new_price,
            "timestamp": timestamp
        })
        
        # Keep only last 24 hours of data (assume updates every hour)
        if len(history) > 24:
            history.pop(0)

def get_portfolio_value(user_id, data):
    """Calculate total portfolio value"""
    user_id = str(user_id)
    portfolio = data.get("stock_portfolios", {}).get(user_id, {})
    
    total_value = 0
    for symbol, shares in portfolio.items():
        current_price = calculate_stock_price(symbol, data)
        total_value += shares * current_price
    
    return total_value

def add_transaction(user_id, amount, reason, data, tx_type="credit"):
    """Add transaction record"""
    tx = {
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "type": tx_type,
        "amount": abs(amount),
        "reason": reason
    }
    data.setdefault("transactions", {}).setdefault(str(user_id), []).append(tx)

async def get_trading_bonuses(user_id, data):
    """Get trading bonuses from equipment"""
    user_id = str(user_id)
    bonuses = {
        "fee_reduction": 0.0,
        "profit_bonus": 0.0
    }
    
    equipment = data.get("equipment", {}).get(user_id, {})
    
    # Check for trading-related equipment
    if "accessory" in equipment:
        item = equipment["accessory"]
        if item == "traders_monocle":  # Hypothetical trading item
            bonuses["fee_reduction"] = 0.5  # 50% fee reduction
            bonuses["profit_bonus"] = 0.05  # 5% profit bonus
    
    return bonuses

class StockTradingView(discord.ui.View):
    def __init__(self, user_id, symbol):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.symbol = symbol

    @discord.ui.button(label="Buy Shares", style=discord.ButtonStyle.green, emoji="📈")
    async def buy_shares(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your trading interface!", ephemeral=True)
            return
        
        modal = BuyStockModal(self.symbol)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Sell Shares", style=discord.ButtonStyle.red, emoji="📉")
    async def sell_shares(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your trading interface!", ephemeral=True)
            return
        
        data = await load_data()
        portfolio = data.get("stock_portfolios", {}).get(self.user_id, {})
        
        if self.symbol not in portfolio or portfolio[self.symbol] <= 0:
            await interaction.response.send_message(f"❌ You don't own any {self.symbol} shares!", ephemeral=True)
            return
        
        modal = SellStockModal(self.symbol)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Refresh Price", style=discord.ButtonStyle.secondary, emoji="�")
    async def refresh_price(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your trading interface!", ephemeral=True)
            return
        
        await self.show_stock_info(interaction)

    async def show_stock_info(self, interaction):
        data = await load_data()
        stock_info = get_stock_data().get(self.symbol)
        
        if not stock_info:
            await interaction.response.send_message("❌ Stock not found!", ephemeral=True)
            return
        
        current_price = calculate_stock_price(self.symbol, data)
        user_coins = data.get("coins", {}).get(self.user_id, 0)
        
        # Get user's shares
        portfolio = data.get("stock_portfolios", {}).get(self.user_id, {})
        shares_owned = portfolio.get(self.symbol, 0)
        
        # Calculate position value
        position_value = shares_owned * current_price
        
        # Get price history for trend
        price_history = data.get("stock_market", {}).get("price_history", {}).get(self.symbol, [])
        trend = "📊"
        if len(price_history) >= 2:
            prev_price = price_history[-2]["price"]
            if current_price > prev_price:
                trend = "📈 +"
            elif current_price < prev_price:
                trend = "📉 "
            change = ((current_price - prev_price) / prev_price) * 100
            trend += f"{change:.2f}%"
        
        embed = discord.Embed(title=f"📊 {stock_info['name']} ({self.symbol})", color=0x3498db)
        embed.add_field(name="Current Price", value=f"{current_price:.2f} coins", inline=True)
        embed.add_field(name="Sector", value=stock_info["sector"], inline=True)
        embed.add_field(name="24h Change", value=trend, inline=True)
        
        embed.add_field(name="Your Balance", value=f"{user_coins:,} coins", inline=True)
        embed.add_field(name="Shares Owned", value=f"{shares_owned:,}", inline=True)
        embed.add_field(name="Position Value", value=f"{position_value:.2f} coins", inline=True)
        
        embed.add_field(name="Description", value=stock_info["description"], inline=False)
        
        # Trading fees
        trading_fee = max(1, int(current_price * 0.01))  # 1% fee, minimum 1 coin
        bonuses = await get_trading_bonuses(self.user_id, data)
        if bonuses["fee_reduction"] > 0:
            reduced_fee = int(trading_fee * (1 - bonuses["fee_reduction"]))
            embed.add_field(name="Trading Fee", value=f"~~{trading_fee}~~ {reduced_fee} coins per share", inline=True)
        else:
            embed.add_field(name="Trading Fee", value=f"{trading_fee} coins per share", inline=True)
        
        embed.set_footer(text="💡 Prices update based on market conditions and player activity")
        
        await interaction.response.edit_message(embed=embed, view=self)

class BuyStockModal(discord.ui.Modal):
    def __init__(self, symbol):
        super().__init__(title=f"Buy {symbol} Shares")
        self.symbol = symbol

    shares = discord.ui.TextInput(
        label="Number of Shares to Buy",
        placeholder="Enter number of shares...",
        min_length=1,
        max_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            share_count = int(self.shares.value)
            if share_count <= 0:
                await interaction.response.send_message("❌ Number of shares must be positive!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        data = await load_data()
        
        current_price = calculate_stock_price(self.symbol, data)
        trading_fee = max(1, int(current_price * 0.01))  # 1% fee per share
        
        # Apply fee reduction bonus
        bonuses = await get_trading_bonuses(user_id, data)
        if bonuses["fee_reduction"] > 0:
            trading_fee = int(trading_fee * (1 - bonuses["fee_reduction"]))
        
        total_cost = (current_price * share_count) + (trading_fee * share_count)
        user_coins = data.get("coins", {}).get(user_id, 0)
        
        if user_coins < total_cost:
            await interaction.response.send_message(f"❌ Insufficient funds! You need {total_cost:.2f} coins. Your balance: {user_coins:,}", ephemeral=True)
            return
        
        # Process purchase
        data.setdefault("coins", {})[user_id] = user_coins - total_cost
        data.setdefault("stock_portfolios", {}).setdefault(user_id, {})[self.symbol] = data["stock_portfolios"][user_id].get(self.symbol, 0) + share_count
        
        # Update stock prices (simulate market impact)
        update_stock_prices(data)
        
        # Add transaction
        add_transaction(user_id, total_cost, f"Bought {share_count} {self.symbol} shares", data, "debit")
        
        await save_data(data)
        
        embed = discord.Embed(title="✅ Purchase Successful", color=0x27ae60)
        embed.add_field(name="Stock", value=f"{get_stock_data()[self.symbol]['name']} ({self.symbol})", inline=True)
        embed.add_field(name="Shares Bought", value=f"{share_count:,}", inline=True)
        embed.add_field(name="Price per Share", value=f"{current_price:.2f} coins", inline=True)
        embed.add_field(name="Trading Fees", value=f"{trading_fee * share_count:.2f} coins", inline=True)
        embed.add_field(name="Total Cost", value=f"{total_cost:.2f} coins", inline=True)
        embed.add_field(name="New Balance", value=f"{user_coins - total_cost:,} coins", inline=True)
        
        total_shares = data["stock_portfolios"][user_id][self.symbol]
        embed.add_field(name="Total Shares Owned", value=f"{total_shares:,} {self.symbol}", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class SellStockModal(discord.ui.Modal):
    def __init__(self, symbol):
        super().__init__(title=f"Sell {symbol} Shares")
        self.symbol = symbol

    shares = discord.ui.TextInput(
        label="Number of Shares to Sell",
        placeholder="Enter number of shares...",
        min_length=1,
        max_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            share_count = int(self.shares.value)
            if share_count <= 0:
                await interaction.response.send_message("❌ Number of shares must be positive!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
            return
        
        user_id = str(interaction.user.id)
        data = await load_data()
        
        portfolio = data.get("stock_portfolios", {}).get(user_id, {})
        shares_owned = portfolio.get(self.symbol, 0)
        
        if shares_owned < share_count:
            await interaction.response.send_message(f"❌ You only own {shares_owned} {self.symbol} shares!", ephemeral=True)
            return
        
        current_price = calculate_stock_price(self.symbol, data)
        trading_fee = max(1, int(current_price * 0.01))  # 1% fee per share
        
        # Apply fee reduction bonus
        bonuses = await get_trading_bonuses(user_id, data)
        if bonuses["fee_reduction"] > 0:
            trading_fee = int(trading_fee * (1 - bonuses["fee_reduction"]))
        
        gross_proceeds = current_price * share_count
        total_fees = trading_fee * share_count
        net_proceeds = gross_proceeds - total_fees
        
        # Apply profit bonus
        if bonuses["profit_bonus"] > 0 and net_proceeds > 0:
            bonus_amount = net_proceeds * bonuses["profit_bonus"]
            net_proceeds += bonus_amount
        
        # Process sale
        user_coins = data.get("coins", {}).get(user_id, 0)
        data.setdefault("coins", {})[user_id] = user_coins + net_proceeds
        
        # Update portfolio
        portfolio[self.symbol] -= share_count
        if portfolio[self.symbol] <= 0:
            del portfolio[self.symbol]
        
        # Update stock prices (simulate market impact)
        update_stock_prices(data)
        
        # Add transaction
        add_transaction(user_id, net_proceeds, f"Sold {share_count} {self.symbol} shares", data, "credit")
        
        await save_data(data)
        
        embed = discord.Embed(title="✅ Sale Successful", color=0x27ae60)
        embed.add_field(name="Stock", value=f"{get_stock_data()[self.symbol]['name']} ({self.symbol})", inline=True)
        embed.add_field(name="Shares Sold", value=f"{share_count:,}", inline=True)
        embed.add_field(name="Price per Share", value=f"{current_price:.2f} coins", inline=True)
        embed.add_field(name="Gross Proceeds", value=f"{gross_proceeds:.2f} coins", inline=True)
        embed.add_field(name="Trading Fees", value=f"{total_fees:.2f} coins", inline=True)
        embed.add_field(name="Net Proceeds", value=f"{net_proceeds:.2f} coins", inline=True)
        embed.add_field(name="New Balance", value=f"{user_coins + net_proceeds:,} coins", inline=True)
        
        remaining_shares = portfolio.get(self.symbol, 0)
        embed.add_field(name="Remaining Shares", value=f"{remaining_shares:,} {self.symbol}", inline=True)
        
        if bonuses["profit_bonus"] > 0:
            embed.set_footer(text=f"🎉 Equipment bonus applied: +{bonuses['profit_bonus']*100:.1f}% profit!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class StockSelectView(discord.ui.View):
    """Improved dropdown view for stock selection"""
    
    def __init__(self, user_id: str, action: str, data: dict):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.action = action
        self.data = data
        
        # Create dropdown with current stock info
        self._create_dropdown()
    
    def _create_dropdown(self):
        """Create dropdown with live stock prices"""
        stock_data = get_stock_data()
        options = []
        
        emojis = {
            "TECH": "💻", "BANK": "🏦", "MINE": "⛏️", "FOOD": "🍔",
            "ENERGY": "⚡", "HEALTH": "🏥", "AUTO": "🚗", "RETAIL": "🛒"
        }
        
        for symbol, stock_info in stock_data.items():
            current_price = calculate_stock_price(symbol, self.data)
            base_price = stock_info["base_price"]
            change_percent = ((current_price - base_price) / base_price) * 100
            
            # Create description with live data
            description = f"{stock_info['sector']} • ${current_price:.1f} ({change_percent:+.1f}%)"
            
            options.append(discord.SelectOption(
                label=f"{stock_info['name']} ({symbol})",
                description=description[:100],  # Discord character limit
                emoji=emojis.get(symbol, "📊"),
                value=symbol
            ))
        
        select = discord.ui.Select(
            placeholder="🔍 Select a stock to view details and trade...",
            min_values=1,
            max_values=1,
            options=options
        )
        select.callback = self.stock_select
        self.add_item(select)
    
    async def stock_select(self, interaction: discord.Interaction):
        """Handle stock selection from dropdown"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your trading session!", ephemeral=True)
            return
            
        symbol = interaction.data.get('values', [])[0]
        
        # For sell action, verify user owns the stock
        if self.action == "sell":
            portfolio = self.data.get("stock_portfolios", {}).get(self.user_id, {})
            
            if symbol not in portfolio or portfolio[symbol] <= 0:
                stock_name = get_stock_data()[symbol]['name']
                await interaction.response.send_message(
                    f"❌ You don't own any {stock_name} ({symbol}) shares!\n"
                    f"💡 Use `/buystock` to purchase stocks first.", 
                    ephemeral=True
                )
                return
        
        # Create trading view for selected stock
        view = StockTradingView(self.user_id, symbol)
        await view.show_stock_info(interaction)
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

class Market(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stocks", description="View the stock market with live prices!")
    async def stocks(self, interaction: discord.Interaction):
        data = await load_data()
        user_id = str(interaction.user.id)
        
        # Update prices
        update_stock_prices(data)
        await save_data(data)
        
        user_coins = data.get("coins", {}).get(user_id, 0)
        portfolio_value = get_portfolio_value(user_id, data)
        total_wealth = user_coins + portfolio_value
        
        embed = discord.Embed(title="📈 SORABOT Stock Exchange", description="Live market prices and trading", color=0x2ecc71)
        embed.add_field(name="💰 Your Cash", value=f"{user_coins:,} coins", inline=True)
        embed.add_field(name="📊 Portfolio Value", value=f"{portfolio_value:.2f} coins", inline=True)
        embed.add_field(name="💎 Total Wealth", value=f"{total_wealth:.2f} coins", inline=True)
        
        # Show all stocks
        stock_data = get_stock_data()
        stock_list = []
        
        for symbol, info in stock_data.items():
            current_price = calculate_stock_price(symbol, data)
            
            # Get price trend
            price_history = data.get("stock_market", {}).get("price_history", {}).get(symbol, [])
            trend_emoji = "📊"
            if len(price_history) >= 2:
                prev_price = price_history[-2]["price"]
                if current_price > prev_price:
                    trend_emoji = "�"
                elif current_price < prev_price:
                    trend_emoji = "📉"
            
            # Check user's position
            portfolio = data.get("stock_portfolios", {}).get(user_id, {})
            shares = portfolio.get(symbol, 0)
            position_indicator = f" (You own: {shares})" if shares > 0 else ""
            
            stock_list.append(f"{trend_emoji} **{symbol}** - {current_price:.2f} coins\n    {info['name']} • {info['sector']}{position_indicator}")
        
        embed.add_field(name="📋 Available Stocks", value="\n\n".join(stock_list), inline=False)
        embed.add_field(name="💡 How to Trade", value="Use `/buystock` or `/sellstock` with interactive menus to trade!", inline=False)
        embed.set_footer(text="🔄 Prices update in real-time based on market conditions!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="buystock", description="Buy shares using an interactive stock selection menu!")
    async def buystock(self, interaction: discord.Interaction):
        """Buy stocks with interactive dropdown selection"""
        user_id = str(interaction.user.id)
        data = await load_data()
        
        # Create informative embed
        embed = discord.Embed(
            title="📈 Buy Stocks",
            description="Choose a stock from the dropdown menu below to view details and make a purchase:",
            color=0x00ff00
        )
        
        # Add user's financial info
        user_coins = data.get('coins', {}).get(user_id, 0)
        user_bank = data.get('bank', {}).get(user_id, 0)
        total_funds = user_coins + user_bank
        
        embed.add_field(name="💰 Available Funds", value=f"🪙 Wallet: {user_coins:,}\n🏦 Bank: {user_bank:,}\n💎 Total: {total_funds:,}", inline=True)
        
        # Show portfolio value if user has stocks
        portfolio = data.get("stock_portfolios", {}).get(user_id, {})
        if portfolio:
            total_value = 0
            for symbol, shares in portfolio.items():
                if shares > 0:
                    current_price = calculate_stock_price(symbol, data)
                    total_value += shares * current_price
            
            embed.add_field(name="📊 Portfolio Value", value=f"💼 {total_value:,.0f} coins", inline=True)
        
        embed.add_field(name="💡 Trading Tips", 
                       value="• Research before investing\n• Diversify your portfolio\n• Buy low, sell high", 
                       inline=False)
        
        embed.set_footer(text="💡 Click the dropdown below to select a stock!")
        
        # Create view with live stock data
        view = StockSelectView(user_id, "buy", data)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="sellstock", description="Sell shares using an interactive stock selection menu!")
    async def sellstock(self, interaction: discord.Interaction):
        """Sell stocks with interactive dropdown selection"""
        user_id = str(interaction.user.id)
        data = await load_data()
        portfolio = data.get("stock_portfolios", {}).get(user_id, {})
        
        # Check if user has any stocks
        owned_stocks = [(symbol, shares) for symbol, shares in portfolio.items() if shares > 0]
        
        if not owned_stocks:
            embed = discord.Embed(
                title="📉 No Stocks to Sell",
                description="You don't own any stocks yet!",
                color=0xff9900
            )
            embed.add_field(name="💡 Get Started", value="Use `/buystock` to purchase stocks first!", inline=False)
            embed.add_field(name="🔍 View Market", value="Use `/stocks` to see available stocks!", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create informative embed
        embed = discord.Embed(
            title="📉 Sell Stocks",
            description="Choose a stock from the dropdown menu below to view details and sell shares:",
            color=0xff4444
        )
        
        # Show portfolio overview
        total_value = 0
        portfolio_text = ""
        
        for symbol, shares in owned_stocks:
            stock_info = get_stock_data()[symbol]
            current_price = calculate_stock_price(symbol, data)
            value = shares * current_price
            total_value += value
            
            # Price change indicator
            base_price = stock_info["base_price"]
            change = current_price - base_price
            change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            
            portfolio_text += f"{change_emoji} **{symbol}**: {shares} shares • ${value:,.0f}\n"
        
        embed.add_field(name="📊 Your Portfolio", value=portfolio_text[:1024], inline=False)
        embed.add_field(name="💰 Total Value", value=f"💼 {total_value:,.0f} coins", inline=True)
        
        embed.add_field(name="💡 Selling Tips", 
                       value="• Monitor market trends\n• Consider timing\n• Keep some long-term holds", 
                       inline=False)
        
        embed.set_footer(text="💡 Click the dropdown below to select a stock to sell!")
        
        # Create view with live stock data
        view = StockSelectView(user_id, "sell", data)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="portfolio", description="View your stock portfolio with performance!")
    async def portfolio(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await load_data()
        
        portfolio = data.get("stock_portfolios", {}).get(user_id, {})
        
        if not portfolio:
            embed = discord.Embed(title="📊 Your Portfolio", description="You don't own any stocks yet!", color=0x95a5a6)
            embed.add_field(name="💡 Get Started", value="Use `/stocks` to view available stocks and `/buystock` to start investing!", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user_coins = data.get("coins", {}).get(user_id, 0)
        total_value = 0
        positions = []
        
        stock_data = get_stock_data()
        
        for symbol, shares in portfolio.items():
            if shares <= 0:
                continue
                
            stock_info = stock_data.get(symbol, {})
            current_price = calculate_stock_price(symbol, data)
            position_value = shares * current_price
            total_value += position_value
            
            # Calculate performance (simplified - would need purchase price tracking for real P&L)
            avg_price = stock_info.get("base_price", current_price)  # Simplified
            total_cost = shares * avg_price
            profit_loss = position_value - total_cost
            profit_percent = (profit_loss / total_cost) * 100 if total_cost > 0 else 0
            
            performance_emoji = "📈" if profit_loss > 0 else "📉" if profit_loss < 0 else "📊"
            
            positions.append(f"{performance_emoji} **{symbol}** • {shares:,} shares\n    ${current_price:.2f} each • Value: {position_value:.2f} coins\n    P&L: {'+'if profit_loss >= 0 else ''}{profit_loss:.2f} ({profit_percent:+.1f}%)")
        
        total_wealth = user_coins + total_value
        
        embed = discord.Embed(title="📊 Your Portfolio", color=0x3498db)
        embed.add_field(name="💰 Cash Balance", value=f"{user_coins:,} coins", inline=True)
        embed.add_field(name="📈 Portfolio Value", value=f"{total_value:.2f} coins", inline=True)
        embed.add_field(name="💎 Total Wealth", value=f"{total_wealth:.2f} coins", inline=True)
        
        if positions:
            embed.add_field(name="🏭 Your Positions", value="\n\n".join(positions), inline=False)
        
        # Show trading bonuses
        bonuses = await get_trading_bonuses(user_id, data)
        if any(bonuses.values()):
            bonus_text = []
            if bonuses["fee_reduction"] > 0:
                bonus_text.append(f"📉 Trading Fees: -{bonuses['fee_reduction']*100:.0f}%")
            if bonuses["profit_bonus"] > 0:
                bonus_text.append(f"📈 Profit Bonus: +{bonuses['profit_bonus']*100:.1f}%")
            
            embed.add_field(name="🎉 Active Bonuses", value="\n".join(bonus_text), inline=False)
        
        embed.set_footer(text="💡 Use /stocks to see market overview and trade more stocks!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Market(bot))
