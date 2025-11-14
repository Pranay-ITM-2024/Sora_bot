"""
Loan/Credit system: Take loans based on your wealth, pay EMIs weekly, or face increasing interest
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import logging

from .database import load_data, save_data, get_server_data, save_server_data

class Loan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="creditlimit", description="Check your available credit limit")
    async def credit_limit(self, interaction: discord.Interaction):
        """Check how much you can borrow based on your wealth"""
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        
        data = await load_data()
        server_data = get_server_data(data, guild_id)
        
        # Calculate total wealth
        wallet = server_data.get("coins", {}).get(user_id, 0)
        bank = server_data.get("bank", {}).get(user_id, 0)
        total_wealth = wallet + bank
        
        # Credit limit = total wealth + 10% of total wealth
        credit_limit = int(total_wealth * 1.1)
        
        # Check existing loan
        loans = server_data.get("loans", {})
        existing_loan = loans.get(user_id)
        
        if existing_loan:
            outstanding = existing_loan.get("outstanding", 0)
            available_credit = max(0, credit_limit - outstanding)
        else:
            outstanding = 0
            available_credit = credit_limit
        
        embed = discord.Embed(title="💳 Your Credit Report", color=0x3498db)
        embed.add_field(name="💰 Total Wealth", value=f"{total_wealth:,} coins", inline=True)
        embed.add_field(name="📊 Credit Limit", value=f"{credit_limit:,} coins", inline=True)
        embed.add_field(name="💳 Outstanding Loan", value=f"{outstanding:,} coins", inline=True)
        embed.add_field(name="✅ Available Credit", value=f"{available_credit:,} coins", inline=False)
        
        if existing_loan:
            emi_amount = existing_loan.get("emi_amount", 0)
            missed_payments = existing_loan.get("missed_payments", 0)
            next_payment = existing_loan.get("next_payment_date")
            
            if next_payment:
                next_date = datetime.fromisoformat(next_payment)
                days_left = (next_date - datetime.utcnow()).days
                embed.add_field(name="📅 Next EMI Due", value=f"In {days_left} days", inline=True)
            
            embed.add_field(name="💵 EMI Amount", value=f"{emi_amount:,} coins", inline=True)
            embed.add_field(name="⚠️ Missed Payments", value=f"{missed_payments}", inline=True)
            
            if missed_payments > 0:
                embed.color = 0xe74c3c
                embed.set_footer(text="⚠️ You have missed payments! Interest is accumulating.")
        else:
            embed.set_footer(text="Use /takeloan to borrow money based on your credit limit")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="takeloan", description="Take a loan based on your credit limit")
    @app_commands.describe(amount="Amount to borrow (max: your credit limit)")
    async def take_loan(self, interaction: discord.Interaction, amount: int):
        """Take a loan with weekly EMI payments"""
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        
        if amount <= 0:
            await interaction.response.send_message("❌ Loan amount must be positive!", ephemeral=True)
            return
        
        data = await load_data()
        server_data = get_server_data(data, guild_id)
        
        # Calculate credit limit
        wallet = server_data.get("coins", {}).get(user_id, 0)
        bank = server_data.get("bank", {}).get(user_id, 0)
        total_wealth = wallet + bank
        credit_limit = int(total_wealth * 1.1)
        
        # Check if user already has a loan
        loans = server_data.get("loans", {})
        if user_id in loans:
            await interaction.response.send_message(
                "❌ You already have an active loan! Pay it off with `/payloan` before taking a new one.",
                ephemeral=True
            )
            return
        
        # Check credit limit
        if amount > credit_limit:
            await interaction.response.send_message(
                f"❌ Loan amount exceeds your credit limit!\n"
                f"**Your Credit Limit:** {credit_limit:,} coins\n"
                f"**Requested:** {amount:,} coins\n\n"
                f"Your credit limit is based on your total wealth (💰 + 🏦) plus 10%.",
                ephemeral=True
            )
            return
        
        # Calculate EMI (loan divided into 4 weekly payments)
        emi_amount = int(amount / 4)
        
        # Create loan record
        now = datetime.utcnow()
        next_payment = now + timedelta(days=7)
        
        loan_data = {
            "original_amount": amount,
            "outstanding": amount,
            "emi_amount": emi_amount,
            "payments_made": 0,
            "total_payments": 4,
            "missed_payments": 0,
            "interest_rate": 0.15,  # 15% interest per missed payment
            "next_payment_date": next_payment.isoformat(),
            "taken_date": now.isoformat(),
            "max_debt_multiplier": 1.5
        }
        
        server_data.setdefault("loans", {})[user_id] = loan_data
        
        # Give user the loan money in their wallet
        server_data.setdefault("coins", {})[user_id] = wallet + amount
        
        save_server_data(data, guild_id, server_data)
        await save_data(data)
        
        embed = discord.Embed(title="✅ Loan Approved!", color=0x00ff00)
        embed.description = f"💰 **{amount:,} coins** have been added to your wallet!"
        embed.add_field(name="📊 Loan Amount", value=f"{amount:,} coins", inline=True)
        embed.add_field(name="💵 Weekly EMI", value=f"{emi_amount:,} coins", inline=True)
        embed.add_field(name="📅 Total Payments", value="4 weeks", inline=True)
        embed.add_field(name="📆 First Payment Due", value=f"<t:{int(next_payment.timestamp())}:R>", inline=False)
        embed.add_field(
            name="⚠️ Important",
            value="• Pay your EMI weekly using `/payloan`\n"
                  "• Missing payments adds 15% interest\n"
                  "• If loan reaches 1.5x original amount, it becomes debt\n"
                  "• Debt is deducted from all future earnings!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="payloan", description="Pay your loan EMI or pay off the full amount")
    @app_commands.describe(amount="Amount to pay (leave empty for EMI amount)")
    async def pay_loan(self, interaction: discord.Interaction, amount: int = None):
        """Pay loan EMI or full amount"""
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        
        data = await load_data()
        server_data = get_server_data(data, guild_id)
        
        loans = server_data.get("loans", {})
        if user_id not in loans:
            await interaction.response.send_message("❌ You don't have any active loans!", ephemeral=True)
            return
        
        loan = loans[user_id]
        outstanding = loan.get("outstanding", 0)
        emi_amount = loan.get("emi_amount", 0)
        
        # Default to EMI amount if not specified
        if amount is None:
            amount = emi_amount
        
        if amount <= 0:
            await interaction.response.send_message("❌ Payment amount must be positive!", ephemeral=True)
            return
        
        # Check if user is trying to overpay
        overpay_amount = 0
        if amount > outstanding:
            overpay_amount = amount - outstanding
            amount = outstanding  # Only charge the outstanding amount
        
        # Check if user has enough money
        wallet = server_data.get("coins", {}).get(user_id, 0)
        bank = server_data.get("bank", {}).get(user_id, 0)
        total_money = wallet + bank
        
        if total_money < amount:
            await interaction.response.send_message(
                f"❌ Insufficient funds!\n"
                f"**Required:** {amount:,} coins\n"
                f"**Available:** {total_money:,} coins (💰 {wallet:,} + 🏦 {bank:,})",
                ephemeral=True
            )
            return
        
        # Deduct from wallet first, then bank
        if wallet >= amount:
            server_data.setdefault("coins", {})[user_id] = wallet - amount
        else:
            remaining = amount - wallet
            server_data.setdefault("coins", {})[user_id] = 0
            server_data.setdefault("bank", {})[user_id] = bank - remaining
        
        # Update loan
        loan["outstanding"] = max(0, outstanding - amount)
        loan["payments_made"] = loan.get("payments_made", 0) + 1
        
        # Reset missed payments on successful payment
        missed_before = loan.get("missed_payments", 0)
        loan["missed_payments"] = 0
        
        # Set next payment date
        if loan["outstanding"] > 0:
            next_payment = datetime.utcnow() + timedelta(days=7)
            loan["next_payment_date"] = next_payment.isoformat()
        
        embed = discord.Embed(title="✅ Payment Successful!", color=0x00ff00)
        embed.add_field(name="💵 Amount Paid", value=f"{amount:,} coins", inline=True)
        embed.add_field(name="💳 Outstanding", value=f"{loan['outstanding']:,} coins", inline=True)
        
        # Show overpayment refund if applicable
        if overpay_amount > 0:
            embed.add_field(
                name="💸 Overpayment Refunded", 
                value=f"{overpay_amount:,} coins (not charged)", 
                inline=False
            )
            embed.set_footer(text="You can only pay up to the outstanding amount!")
        
        # Check if loan is fully paid
        if loan["outstanding"] <= 0:
            del loans[user_id]
            embed.add_field(name="🎉 Status", value="**LOAN PAID OFF!**", inline=False)
            embed.color = 0xf1c40f
        else:
            payments_left = max(0, loan["total_payments"] - loan["payments_made"])
            embed.add_field(name="📅 Payments Left", value=f"{payments_left}", inline=True)
            next_date = datetime.fromisoformat(loan["next_payment_date"])
            embed.add_field(name="📆 Next Payment Due", value=f"<t:{int(next_date.timestamp())}:R>", inline=False)
        
        if missed_before > 0:
            embed.add_field(
                name="✅ Penalty Cleared",
                value=f"Your {missed_before} missed payment(s) penalty has been cleared!",
                inline=False
            )
        
        save_server_data(data, guild_id, server_data)
        await save_data(data)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="loanstatus", description="Check your current loan status")
    async def loan_status(self, interaction: discord.Interaction):
        """Check detailed loan status"""
        guild_id = str(interaction.guild_id)
        user_id = str(interaction.user.id)
        
        data = await load_data()
        server_data = get_server_data(data, guild_id)
        
        loans = server_data.get("loans", {})
        if user_id not in loans:
            await interaction.response.send_message("✅ You don't have any active loans!", ephemeral=True)
            return
        
        loan = loans[user_id]
        original = loan.get("original_amount", 0)
        outstanding = loan.get("outstanding", 0)
        emi_amount = loan.get("emi_amount", 0)
        payments_made = loan.get("payments_made", 0)
        total_payments = loan.get("total_payments", 4)
        missed = loan.get("missed_payments", 0)
        
        # Calculate progress
        paid_so_far = original - outstanding
        progress_percent = (paid_so_far / original * 100) if original > 0 else 0
        
        # Check if overdue
        next_payment_date = loan.get("next_payment_date")
        is_overdue = False
        days_overdue = 0
        
        if next_payment_date:
            next_date = datetime.fromisoformat(next_payment_date)
            now = datetime.utcnow()
            if now > next_date:
                is_overdue = True
                days_overdue = (now - next_date).days
        
        embed = discord.Embed(title="💳 Loan Status Report", color=0x3498db)
        
        if is_overdue:
            embed.color = 0xe74c3c
            embed.description = f"⚠️ **PAYMENT OVERDUE BY {days_overdue} DAYS!**"
        
        embed.add_field(name="💰 Original Loan", value=f"{original:,} coins", inline=True)
        embed.add_field(name="💳 Outstanding", value=f"{outstanding:,} coins", inline=True)
        embed.add_field(name="✅ Paid So Far", value=f"{paid_so_far:,} coins ({progress_percent:.1f}%)", inline=True)
        
        embed.add_field(name="💵 EMI Amount", value=f"{emi_amount:,} coins", inline=True)
        embed.add_field(name="📊 Payments", value=f"{payments_made}/{total_payments}", inline=True)
        embed.add_field(name="⚠️ Missed Payments", value=f"{missed}", inline=True)
        
        if next_payment_date and not is_overdue:
            next_date = datetime.fromisoformat(next_payment_date)
            embed.add_field(name="📆 Next Payment Due", value=f"<t:{int(next_date.timestamp())}:R>", inline=False)
        
        # Calculate debt conversion threshold
        max_multiplier = loan.get("max_debt_multiplier", 1.5)
        debt_threshold = int(original * max_multiplier)
        
        embed.add_field(
            name="⚠️ Debt Conversion",
            value=f"If outstanding reaches **{debt_threshold:,} coins** ({max_multiplier}x original), "
                  f"it will be converted to debt!",
            inline=False
        )
        
        if missed > 0:
            embed.add_field(
                name="💡 Tip",
                value="Make a payment with `/payloan` to clear your missed payment penalty!",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Loan(bot))
