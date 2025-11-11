"""
Shop module: Simple shop with dropdown menus for easy item selection
"""
import discord
from discord import app_commands
from discord.ext import commands
import random
from .database import load_data, save_data

# 🛒 SHOP CATALOG - Pre-defined items with clear descriptions!
SHOP_ITEMS = {
    "🧪 Potions": {
        "luck_potion": {
            "name": "🍀 Luck Potion",
            "price": 500,
            "desc": "Increases your casino winnings by 20% for 1 hour",
            "type": "boost"
        },
        "wealth_potion": {
            "name": "💰 Wealth Potion",
            "price": 1000,
            "desc": "Get 2x coins from daily/weekly rewards for 24 hours",
            "type": "boost"
        },
        "xp_boost": {
            "name": "⭐ XP Boost",
            "price": 750,
            "desc": "Earn 50% more coins from all activities for 2 hours",
            "type": "boost"
        }
    },
    "🎁 Chests": {
        "small_chest": {
            "name": "📦 Small Chest",
            "price": 250,
            "desc": "Contains 100-500 random coins when opened",
            "type": "chest"
        },
        "medium_chest": {
            "name": "🎁 Medium Chest",
            "price": 750,
            "desc": "Contains 500-2,000 coins or a random item",
            "type": "chest"
        },
        "large_chest": {
            "name": "🏆 Large Chest",
            "price": 2000,
            "desc": "Contains 2,000-10,000 coins or a rare item",
            "type": "chest"
        }
    },
    "⚔️ Equipment": {
        "lucky_charm": {
            "name": "🔮 Lucky Charm",
            "price": 3000,
            "desc": "Permanent +10% casino winnings (equip to activate)",
            "type": "equipment"
        },
        "piggy_bank": {
            "name": "🐷 Piggy Bank",
            "price": 2500,
            "desc": "Permanent +15% daily/weekly rewards (equip to activate)",
            "type": "equipment"
        },
        "golden_horseshoe": {
            "name": "🌟 Golden Horseshoe",
            "price": 5000,
            "desc": "Permanent +25% rob success rate (equip to activate)",
            "type": "equipment"
        }
    },
    "🔧 Heist Gear": {
        "lockpick_pro": {
            "name": "🔓 Pro Lockpick",
            "price": 3500,
            "desc": "+15% stealth, +10% speed for heists (equip to activate)",
            "type": "equipment"
        },
        "night_vision_goggles": {
            "name": "👓 Night Vision Goggles",
            "price": 4000,
            "desc": "+20% stealth, -15% detection for heists (equip to activate)",
            "type": "equipment"
        },
        "smoke_bomb": {
            "name": "💣 Smoke Bomb",
            "price": 1500,
            "desc": "+25% escape, +10% stealth (consumable, 1 use)",
            "type": "consumable"
        },
        "master_disguise": {
            "name": "🎭 Master Disguise",
            "price": 5000,
            "desc": "+30% stealth, -20% detection for heists (equip to activate)",
            "type": "equipment"
        },
        "getaway_car": {
            "name": "🚗 Getaway Car",
            "price": 7500,
            "desc": "+30% escape, +15% speed for heists (equip to activate)",
            "type": "equipment"
        },
        "hacking_device": {
            "name": "💻 Hacking Device",
            "price": 6000,
            "desc": "+25% security bypass, +10% speed for heists (equip to activate)",
            "type": "equipment"
        },
        "thermal_drill": {
            "name": "🔥 Thermal Drill",
            "price": 4500,
            "desc": "+20% speed, +10% noise for heists (equip to activate)",
            "type": "equipment"
        }
    }
}


class PurchaseView(discord.ui.View):
    """Confirmation view for purchasing"""
    def __init__(self, user_id, item_key, item_data, category_name):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.item_key = item_key
        self.item_data = item_data
        self.category_name = category_name
    
    @discord.ui.button(label="✅ Buy Now", style=discord.ButtonStyle.green, row=0)
    async def buy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your purchase!", ephemeral=True)
            return
        
        data = await load_data()
        user_coins = data.get("coins", {}).get(self.user_id, 0)
        
        # Check if user can afford it
        if user_coins < self.item_data['price']:
            needed = self.item_data['price'] - user_coins
            await interaction.response.send_message(
                f"❌ You need **{needed:,} more coins** to buy this item!",
                ephemeral=True
            )
            return
        
        # Purchase the item
        data.setdefault("coins", {})[self.user_id] = user_coins - self.item_data['price']
        data.setdefault("inventories", {}).setdefault(self.user_id, {})[self.item_key] = \
            data["inventories"][self.user_id].get(self.item_key, 0) + 1
        
        await save_data(data)
        
        # Success message
        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"You bought **{self.item_data['name']}**!",
            color=0x00ff00
        )
        
        embed.add_field(
            name="📦 Item",
            value=f"{self.item_data['name']}\n{self.item_data['desc']}",
            inline=False
        )
        
        embed.add_field(
            name="💰 Paid",
            value=f"{self.item_data['price']:,} coins",
            inline=True
        )
        
        embed.add_field(
            name="💼 New Balance",
            value=f"{user_coins - self.item_data['price']:,} coins",
            inline=True
        )
        
        embed.add_field(
            name="📦 Total Owned",
            value=f"{data['inventories'][self.user_id][self.item_key]}x",
            inline=True
        )
        
        # Add usage instructions
        item_type = self.item_data.get('type', '')
        if item_type == "equipment":
            embed.set_footer(text="💡 Use /equip to activate this item's effects!")
        elif item_type == "chest":
            embed.set_footer(text="💡 Use /openchest to open this chest!")
        else:
            embed.set_footer(text="💡 Use /use to activate this item!")
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red, row=0)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your purchase!", ephemeral=True)
            return
        
        # Go back to category view
        view = CategoryView(self.user_id, self.category_name)
        
        data = await load_data()
        user_coins = data.get("coins", {}).get(self.user_id, 0)
        
        embed = discord.Embed(
            title=f"{self.category_name}",
            description=f"**Balance:** {user_coins:,} coins\n\n🛒 **Select an item from the dropdown below to buy:**",
            color=0x3498db
        )
        
        items = SHOP_ITEMS[self.category_name]
        for item_key, item in items.items():
            can_afford = "✅" if user_coins >= item['price'] else "❌"
            embed.add_field(
                name=f"{can_afford} {item['name']} - {item['price']:,} coins",
                value=f"📝 {item['desc']}",
                inline=False
            )
        
        await interaction.response.edit_message(embed=embed, view=view)


class CategoryView(discord.ui.View):
    """View with item dropdown for a specific category"""
    def __init__(self, user_id, category_name):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.category_name = category_name
        
        # Add dropdown with items from this category
        items = SHOP_ITEMS[category_name]
        options = []
        for item_key, item_data in items.items():
            # Truncate description if too long
            desc = item_data['desc']
            if len(desc) > 100:
                desc = desc[:97] + "..."
            
            # Extract emoji from item name
            emoji_part = item_data['name'].split()[0] if item_data['name'] else "🛒"
            
            options.append(
                discord.SelectOption(
                    label=f"{item_data['name']} - {item_data['price']:,} coins",
                    value=item_key,
                    description=desc,
                    emoji=emoji_part
                )
            )
        
        select = discord.ui.Select(
            placeholder="🛒 Choose an item to buy...",
            options=options,
            custom_id="item_select"
        )
        select.callback = self.item_selected
        self.add_item(select)
    
    async def item_selected(self, interaction: discord.Interaction):
        """Handle item selection from dropdown"""
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your shop!", ephemeral=True)
            return
        
        item_key = interaction.data['values'][0]
        items = SHOP_ITEMS[self.category_name]
        item_data = items[item_key]
        
        # Show purchase confirmation
        view = PurchaseView(self.user_id, item_key, item_data, self.category_name)
        
        data = await load_data()
        user_coins = data.get("coins", {}).get(self.user_id, 0)
        can_afford = user_coins >= item_data['price']
        
        embed = discord.Embed(
            title="🛒 Confirm Purchase",
            description=f"**{item_data['name']}**\n\n{item_data['desc']}",
            color=0x00ff00 if can_afford else 0xff0000
        )
        
        embed.add_field(name="💰 Price", value=f"{item_data['price']:,} coins", inline=True)
        embed.add_field(name="💼 Your Balance", value=f"{user_coins:,} coins", inline=True)
        
        if can_afford:
            embed.add_field(name="📊 After Purchase", value=f"{user_coins - item_data['price']:,} coins", inline=True)
            embed.set_footer(text="✅ Click 'Buy Now' to confirm your purchase")
        else:
            embed.add_field(name="❌ Short By", value=f"{item_data['price'] - user_coins:,} coins", inline=True)
            embed.set_footer(text="❌ Not enough coins! Earn more with /daily, /weekly, or casino games")
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="🔙 Back to Categories", style=discord.ButtonStyle.secondary, row=2)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your shop!", ephemeral=True)
            return
        
        data = await load_data()
        user_coins = data.get("coins", {}).get(self.user_id, 0)
        
        embed = discord.Embed(
            title="🛒 SORABOT SHOP",
            description="**Welcome back!** Click a category button to browse items.",
            color=0x00ff00
        )
        
        embed.add_field(
            name="💰 Your Balance",
            value=f"```{user_coins:,} coins```",
            inline=False
        )
        
        embed.add_field(
            name="🧪 Potions",
            value="Temporary boosts for casino, earnings, and rewards",
            inline=True
        )
        
        embed.add_field(
            name="🎁 Chests",
            value="Open for random coins and items",
            inline=True
        )
        
        embed.add_field(
            name="⚔️ Equipment",
            value="Permanent passive bonuses when equipped",
            inline=True
        )
        
        embed.set_footer(text="💡 Select items from dropdown menus - no typing needed!")
        
        view = ShopView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)


class ShopView(discord.ui.View):
    """Main shop view with category buttons"""
    def __init__(self, user_id):
        super().__init__(timeout=180)
        self.user_id = user_id
    
    @discord.ui.button(label="🧪 Potions", style=discord.ButtonStyle.primary, row=0)
    async def potions_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your shop!", ephemeral=True)
            return
        await self.show_category(interaction, "🧪 Potions")
    
    @discord.ui.button(label="🎁 Chests", style=discord.ButtonStyle.primary, row=0)
    async def chests_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your shop!", ephemeral=True)
            return
        await self.show_category(interaction, "🎁 Chests")
    
    @discord.ui.button(label="⚔️ Equipment", style=discord.ButtonStyle.primary, row=0)
    async def equipment_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your shop!", ephemeral=True)
            return
        await self.show_category(interaction, "⚔️ Equipment")
    
    async def show_category(self, interaction, category_name):
        """Show items in category with dropdown"""
        data = await load_data()
        user_coins = data.get("coins", {}).get(self.user_id, 0)
        
        embed = discord.Embed(
            title=f"{category_name}",
            description=f"**Balance:** {user_coins:,} coins\n\n🛒 **Select an item from the dropdown below to buy:**",
            color=0x3498db
        )
        
        items = SHOP_ITEMS[category_name]
        for item_key, item in items.items():
            can_afford = "✅" if user_coins >= item['price'] else "❌"
            embed.add_field(
                name=f"{can_afford} {item['name']} - {item['price']:,} coins",
                value=f"📝 {item['desc']}",
                inline=False
            )
        
        embed.set_footer(text="💡 Just select from the dropdown - no typing required!")
        
        view = CategoryView(self.user_id, category_name)
        await interaction.response.edit_message(embed=embed, view=view)


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shop", description="Browse the shop with easy dropdown menus!")
    async def shop(self, interaction: discord.Interaction):
        """Show the main shop"""
        user_id = str(interaction.user.id)
        data = await load_data()
        user_coins = data.get("coins", {}).get(user_id, 0)
        
        embed = discord.Embed(
            title="🛒 SORABOT SHOP",
            description="**Welcome!** Click a category button, then select items from the dropdown.\n\n💡 **No typing needed - just click and select!**",
            color=0x00ff00
        )
        
        embed.add_field(
            name="💰 Your Balance",
            value=f"```{user_coins:,} coins```",
            inline=False
        )
        
        embed.add_field(
            name="🧪 Potions",
            value="Temporary boosts for casino, earnings, and rewards",
            inline=True
        )
        
        embed.add_field(
            name="🎁 Chests",
            value="Open for random coins and items",
            inline=True
        )
        
        embed.add_field(
            name="⚔️ Equipment",
            value="Permanent passive bonuses when equipped",
            inline=True
        )
        
        embed.set_footer(text="💡 Click a button above to get started!")
        
        view = ShopView(user_id)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Shop(bot))
