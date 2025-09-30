"""
Stock Market system cog
"""

import discord
from discord.ext import commands
import random
import datetime
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import DataManager, STOCK_MARKET

class StockMarketCommands(commands.Cog):
    """Stock Market commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='market')
    async def market(self, ctx):
        """View stock market prices with ASCII trend lines"""
        data = await DataManager.load_data()
        stock_prices = data["stock_prices"]
        
        embed = discord.Embed(
            title="📈 SORA Stock Market",
            description="Current stock prices and trends:",
            color=0x00ff00
        )
        
        for stock_symbol, stock_data in STOCK_MARKET.items():
            current_price = stock_prices.get(stock_symbol, stock_data["base_price"])
            base_price = stock_data["base_price"]
            
            # Calculate price change
            change = current_price - base_price
            change_percent = (change / base_price) * 100
            
            # Generate trend line (simple ASCII)
            trend_line = self.generate_trend_line(stock_symbol, current_price)
            
            # Determine color emoji
            if change > 0:
                trend_emoji = "📈"
                color = 0x00ff00
            elif change < 0:
                trend_emoji = "📉"
                color = 0xff0000
            else:
                trend_emoji = "➡️"
                color = 0xffa500
            
            embed.add_field(
                name=f"{trend_emoji} {stock_symbol} - {stock_data['name']}",
                value=f"**Price:** {current_price:.2f} coins\n"
                      f"**Change:** {change:+.2f} ({change_percent:+.1f}%)\n"
                      f"**Trend:** {trend_line}",
                inline=True
            )
        
        embed.add_field(
            name="How to Trade",
            value="Use `/buy <stock> <amount>` to buy stocks\n"
                  "Use `/sell <stock> <amount>` to sell stocks",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    def generate_trend_line(self, stock_symbol: str, current_price: float) -> str:
        """Generate a simple ASCII trend line based on stock symbol and price"""
        # Use stock symbol and price to create a pseudo-random but consistent trend
        seed = hash(stock_symbol + str(int(current_price)))
        random.seed(seed)
        
        trend_chars = ["_", "‾", "\\", "/", "|"]
        trend_line = ""
        
        for i in range(8):
            trend_line += random.choice(trend_chars)
        
        return trend_line
    
    @commands.command(name='buy')
    async def buy(self, ctx, stock_symbol: str, amount: int):
        """Buy stock"""
        if amount <= 0:
            await ctx.send("❌ Amount must be positive!")
            return
        
        stock_symbol = stock_symbol.upper()
        if stock_symbol not in STOCK_MARKET:
            await ctx.send(f"❌ Invalid stock symbol! Available: {', '.join(STOCK_MARKET.keys())}")
            return
        
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Get current price
        current_price = data["stock_prices"].get(stock_symbol, STOCK_MARKET[stock_symbol]["base_price"])
        total_cost = int(current_price * amount)
        
        # Check if user has enough coins
        if data["coins"].get(user_id, 0) < total_cost:
            await ctx.send(f"❌ Insufficient funds! You need {total_cost:,} coins to buy {amount} shares of {stock_symbol}")
            return
        
        # Buy the stock
        data["coins"][user_id] -= total_cost
        
        # Add to holdings
        if user_id not in data["stock_holdings"]:
            data["stock_holdings"][user_id] = {}
        
        data["stock_holdings"][user_id][stock_symbol] = data["stock_holdings"][user_id].get(stock_symbol, 0) + amount
        
        # Apply market pressure (simplified)
        self.apply_buy_pressure(data, stock_symbol, amount)
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="📈 Stock Purchase Successful!",
            description=f"Bought **{amount} shares** of **{stock_symbol}** at **{current_price:.2f} coins** each\n"
                       f"**Total Cost:** {total_cost:,} coins\n"
                       f"**New Holdings:** {data['stock_holdings'][user_id][stock_symbol]} shares",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='sell')
    async def sell(self, ctx, stock_symbol: str, amount: int):
        """Sell stock"""
        if amount <= 0:
            await ctx.send("❌ Amount must be positive!")
            return
        
        stock_symbol = stock_symbol.upper()
        if stock_symbol not in STOCK_MARKET:
            await ctx.send(f"❌ Invalid stock symbol! Available: {', '.join(STOCK_MARKET.keys())}")
            return
        
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Check if user has enough shares
        user_holdings = data["stock_holdings"].get(user_id, {})
        if user_holdings.get(stock_symbol, 0) < amount:
            await ctx.send(f"❌ Insufficient shares! You only have {user_holdings.get(stock_symbol, 0)} shares of {stock_symbol}")
            return
        
        # Get current price
        current_price = data["stock_prices"].get(stock_symbol, STOCK_MARKET[stock_symbol]["base_price"])
        total_value = int(current_price * amount)
        
        # Sell the stock
        data["coins"][user_id] += total_value
        data["stock_holdings"][user_id][stock_symbol] -= amount
        
        if data["stock_holdings"][user_id][stock_symbol] <= 0:
            del data["stock_holdings"][user_id][stock_symbol]
        
        # Apply market pressure (simplified)
        self.apply_sell_pressure(data, stock_symbol, amount)
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="📉 Stock Sale Successful!",
            description=f"Sold **{amount} shares** of **{stock_symbol}** at **{current_price:.2f} coins** each\n"
                       f"**Total Value:** {total_value:,} coins\n"
                       f"**Remaining Holdings:** {user_holdings.get(stock_symbol, 0) - amount} shares",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    def apply_buy_pressure(self, data: dict, stock_symbol: str, amount: int):
        """Apply buy pressure to stock price"""
        current_price = data["stock_prices"].get(stock_symbol, STOCK_MARKET[stock_symbol]["base_price"])
        volatility = STOCK_MARKET[stock_symbol]["volatility"]
        
        # Simple buy pressure increases price slightly
        price_increase = (amount / 1000) * volatility * 0.1  # Very small impact
        new_price = current_price * (1 + price_increase)
        
        # Keep price within reasonable bounds
        base_price = STOCK_MARKET[stock_symbol]["base_price"]
        min_price = base_price * 0.1
        max_price = base_price * 10
        
        data["stock_prices"][stock_symbol] = max(min_price, min(max_price, new_price))
    
    def apply_sell_pressure(self, data: dict, stock_symbol: str, amount: int):
        """Apply sell pressure to stock price"""
        current_price = data["stock_prices"].get(stock_symbol, STOCK_MARKET[stock_symbol]["base_price"])
        volatility = STOCK_MARKET[stock_symbol]["volatility"]
        
        # Simple sell pressure decreases price slightly
        price_decrease = (amount / 1000) * volatility * 0.1  # Very small impact
        new_price = current_price * (1 - price_decrease)
        
        # Keep price within reasonable bounds
        base_price = STOCK_MARKET[stock_symbol]["base_price"]
        min_price = base_price * 0.1
        max_price = base_price * 10
        
        data["stock_prices"][stock_symbol] = max(min_price, min(max_price, new_price))
    
    @commands.command(name='portfolio')
    async def portfolio(self, ctx):
        """View user's stock portfolio"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        holdings = data["stock_holdings"].get(user_id, {})
        stock_prices = data["stock_prices"]
        
        if not holdings:
            await ctx.send("❌ You don't own any stocks!")
            return
        
        embed = discord.Embed(
            title=f"📊 {ctx.author.display_name}'s Portfolio",
            color=0x0099ff
        )
        
        total_value = 0
        for stock_symbol, shares in holdings.items():
            current_price = stock_prices.get(stock_symbol, STOCK_MARKET[stock_symbol]["base_price"])
            value = current_price * shares
            total_value += value
            
            embed.add_field(
                name=f"{stock_symbol} - {STOCK_MARKET[stock_symbol]['name']}",
                value=f"**Shares:** {shares}\n"
                      f"**Price:** {current_price:.2f} coins\n"
                      f"**Value:** {value:,.0f} coins",
                inline=True
            )
        
        embed.add_field(
            name="Total Portfolio Value",
            value=f"{total_value:,.0f} coins",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StockMarketCommands(bot))
