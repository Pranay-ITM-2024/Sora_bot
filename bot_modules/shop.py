"""
Shop module: Simple shop with dropdown menus for easy item selection
"""
import discord
from discord import app_commands
from discord.ext import commands
import random
from .database import load_data, save_data
from .economy import deduct_combined_balance

# 🛒 SHOP CATALOG - Balanced progression system with variety!
SHOP_ITEMS = {
    "🧪 Potions": [
        {
            "key": "luck_potion",
            "name": "🍀 Luck Potion",
            "price": 5000,
            "desc": "+20% success chance on next action (heists, casino)",
            "rarity": "Rare",
            "effect_type": "luck_boost",
            "effect_value": 0.20
        },
        {
            "key": "speed_potion",
            "name": "⚡ Speed Potion",
            "price": 4000,
            "desc": "+15% heist progress per phase",
            "rarity": "Rare",
            "effect_type": "speed_boost",
            "effect_value": 0.15
        },
        {
            "key": "stealth_elixir",
            "name": "🥷 Stealth Elixir",
            "price": 6000,
            "desc": "+25% stealth bonus for next heist",
            "rarity": "Epic",
            "effect_type": "stealth_boost",
            "effect_value": 0.25
        },
        {
            "key": "fortune_tonic",
            "name": "💰 Fortune Tonic",
            "price": 10000,
            "desc": "+30% reward multiplier on next earnings",
            "rarity": "Epic",
            "effect_type": "reward_boost",
            "effect_value": 0.30
        },
        {
            "key": "focus_serum",
            "name": "🎯 Focus Serum",
            "price": 3500,
            "desc": "+10% accuracy on minigames",
            "rarity": "Common",
            "effect_type": "accuracy_boost",
            "effect_value": 0.10
        },
        {
            "key": "energy_drink",
            "name": "⚡ Energy Drink",
            "price": 2000,
            "desc": "+5% to all activities for 1 hour",
            "rarity": "Common",
            "effect_type": "general_boost",
            "effect_value": 0.05
        }
    ],
    "🎁 Chests": [
        {
            "key": "common_chest",
            "name": "📦 Common Chest",
            "price": 1000,
            "desc": "500-2,000 coins or common item | 5% mimic chance",
            "rarity": "Common",
            "min_coins": 500,
            "max_coins": 2000,
            "mimic_chance": 0.05
        },
        {
            "key": "rare_chest",
            "name": "🎁 Rare Chest",
            "price": 5000,
            "desc": "2,000-10,000 coins or rare item | 10% mimic chance",
            "rarity": "Rare",
            "min_coins": 2000,
            "max_coins": 10000,
            "mimic_chance": 0.10
        },
        {
            "key": "epic_chest",
            "name": "💎 Epic Chest",
            "price": 15000,
            "desc": "10,000-50,000 coins or epic item | 15% mimic chance",
            "rarity": "Epic",
            "min_coins": 10000,
            "max_coins": 50000,
            "mimic_chance": 0.15
        },
        {
            "key": "legendary_chest",
            "name": "🏆 Legendary Chest",
            "price": 50000,
            "desc": "50,000-200,000 coins or legendary item | 20% mimic chance",
            "rarity": "Legendary",
            "min_coins": 50000,
            "max_coins": 200000,
            "mimic_chance": 0.20
        },
        {
            "key": "mimic_protection",
            "name": "🛡️ Mimic Protection",
            "price": 2500,
            "desc": "Prevents next chest from being a mimic (1 use)",
            "rarity": "Rare",
            "effect_type": "mimic_shield",
            "effect_value": 1
        }
    ],
    "🎰 Casino Gear": [
        {
            "key": "lucky_charm",
            "name": "🔮 Lucky Charm",
            "price": 25000,
            "desc": "+5% win rate on all casino games (permanent)",
            "rarity": "Epic",
            "slot": "accessory",
            "bonus_type": "casino_luck",
            "bonus_value": 0.05
        },
        {
            "key": "weighted_dice",
            "name": "🎲 Weighted Dice",
            "price": 40000,
            "desc": "+10% better odds in blackjack (permanent)",
            "rarity": "Epic",
            "slot": "tool",
            "bonus_type": "blackjack_boost",
            "bonus_value": 0.10
        },
        {
            "key": "slot_magnet",
            "name": "🧲 Slot Magnet",
            "price": 35000,
            "desc": "+8% slot machine payouts (permanent)",
            "rarity": "Epic",
            "slot": "tool",
            "bonus_type": "slots_boost",
            "bonus_value": 0.08
        },
        {
            "key": "coin_doubler",
            "name": "💰 Coin Doubler",
            "price": 100000,
            "desc": "2x winnings on coinflip (4x total!) (permanent)",
            "rarity": "Legendary",
            "slot": "accessory",
            "bonus_type": "coinflip_double",
            "bonus_value": 2.0
        },
        {
            "key": "card_counter",
            "name": "🃏 Card Counter",
            "price": 50000,
            "desc": "See hints about dealer's cards in blackjack (permanent)",
            "rarity": "Legendary",
            "slot": "accessory",
            "bonus_type": "card_hints",
            "bonus_value": 1
        }
    ],
    "🔧 Heist Gear": [
        {
            "key": "night_vision_goggles",
            "name": "👓 Night Vision Goggles",
            "price": 20000,
            "desc": "-15% detection chance (permanent)",
            "rarity": "Rare",
            "slot": "head",
            "bonus_type": "stealth",
            "bonus_value": 0.15
        },
        {
            "key": "silent_shoes",
            "name": "👟 Silent Shoes",
            "price": 15000,
            "desc": "-20% noise generation (permanent)",
            "rarity": "Rare",
            "slot": "feet",
            "bonus_type": "stealth",
            "bonus_value": 0.20
        },
        {
            "key": "cloaking_device",
            "name": "🌫️ Cloaking Device",
            "price": 50000,
            "desc": "-30% visibility (permanent)",
            "rarity": "Legendary",
            "slot": "accessory",
            "bonus_type": "stealth",
            "bonus_value": 0.30
        },
        {
            "key": "adrenaline_injector",
            "name": "💉 Adrenaline Injector",
            "price": 18000,
            "desc": "+15% heist progress (permanent)",
            "rarity": "Rare",
            "slot": "accessory",
            "bonus_type": "speed",
            "bonus_value": 0.15
        },
        {
            "key": "jetpack",
            "name": "🚀 Jetpack",
            "price": 60000,
            "desc": "+25% escape speed (permanent)",
            "rarity": "Epic",
            "slot": "back",
            "bonus_type": "escape",
            "bonus_value": 0.25
        },
        {
            "key": "turbo_boots",
            "name": "👢 Turbo Boots",
            "price": 25000,
            "desc": "+20% movement speed (permanent)",
            "rarity": "Epic",
            "slot": "feet",
            "bonus_type": "speed",
            "bonus_value": 0.20
        },
        {
            "key": "master_keycard",
            "name": "🔑 Master Keycard",
            "price": 30000,
            "desc": "+20% vault access (permanent)",
            "rarity": "Epic",
            "slot": "tool",
            "bonus_type": "security",
            "bonus_value": 0.20
        },
        {
            "key": "emp_device",
            "name": "📡 EMP Device",
            "price": 45000,
            "desc": "Disables 50% of alarms (permanent)",
            "rarity": "Legendary",
            "slot": "tool",
            "bonus_type": "security",
            "bonus_value": 0.50
        },
        {
            "key": "hacking_kit",
            "name": "💻 Hacking Kit",
            "price": 35000,
            "desc": "+25% tech approach success (permanent)",
            "rarity": "Epic",
            "slot": "tool",
            "bonus_type": "tech",
            "bonus_value": 0.25
        },
        {
            "key": "lockpick_set",
            "name": "🔓 Professional Lockpick Set",
            "price": 12000,
            "desc": "+10% lockpicking success (permanent)",
            "rarity": "Rare",
            "slot": "tool",
            "bonus_type": "lockpick",
            "bonus_value": 0.10
        },
        {
            "key": "thermal_vision",
            "name": "🔥 Thermal Vision",
            "price": 28000,
            "desc": "+15% detection avoidance (permanent)",
            "rarity": "Epic",
            "slot": "head",
            "bonus_type": "detection",
            "bonus_value": 0.15
        },
        {
            "key": "grappling_hook",
            "name": "🪝 Grappling Hook",
            "price": 22000,
            "desc": "+18% escape success (permanent)",
            "rarity": "Rare",
            "slot": "tool",
            "bonus_type": "escape",
            "bonus_value": 0.18
        }
    ]
}


class PurchaseView(discord.ui.View):
    """Confirmation view for purchasing"""
    def __init__(self, user_id, guild_id, item_key, item_data, category_name):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.guild_id = guild_id
        self.item_key = item_key
        self.item_data = item_data
        self.category_name = category_name
    
    @discord.ui.button(label="✅ Buy Now", style=discord.ButtonStyle.green, row=0)
    async def buy_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your purchase!", ephemeral=True)
            return
        
        data = await load_data()
        from .database import get_server_data, save_server_data
        server_data = get_server_data(data, self.guild_id)
        
        price = self.item_data['price']
        
        # Try to deduct from wallet + bank combined
        success, message, from_wallet, from_bank = deduct_combined_balance(self.user_id, price, server_data)
        
        if not success:
            await interaction.response.send_message(message, ephemeral=True)
            return
        
        # Purchase the item - add to inventory
        if "inventories" not in server_data:
            server_data["inventories"] = {}
        if self.user_id not in server_data["inventories"]:
            server_data["inventories"][self.user_id] = {}
        
        current_count = server_data["inventories"][self.user_id].get(self.item_key, 0)
        server_data["inventories"][self.user_id][self.item_key] = current_count + 1
        
        save_server_data(data, self.guild_id, server_data)
        await save_data(data)
        
        # Get new balances
        new_wallet = server_data.get("coins", {}).get(self.user_id, 0)
        new_bank = server_data.get("bank", {}).get(self.user_id, 0)
        
        # Success message
        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"You bought **{self.item_data['name']}**!\n\n{message}",
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
            value=f"💰 {new_wallet:,} | 🏦 {new_bank:,}",
            inline=True
        )
        
        embed.add_field(
            name="📦 Total Owned",
            value=f"{server_data['inventories'][self.user_id][self.item_key]}x",
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
        view = CategoryView(self.user_id, self.guild_id, self.category_name)
        
        data = await load_data()
        from .database import get_server_data
        server_data = get_server_data(data, self.guild_id)
        
        user_coins = server_data.get("coins", {}).get(self.user_id, 0)
        
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
    def __init__(self, user_id, guild_id, category_name):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.guild_id = guild_id
        self.category_name = category_name
        
        # Add dropdown with items from this category
        items = SHOP_ITEMS[self.category_name]
        options = []
        for item_data in items:
            # Truncate description if too long
            desc = item_data['desc']
            if len(desc) > 100:
                desc = desc[:97] + "..."
            
            # Extract emoji from item name
            emoji_part = item_data['name'].split()[0] if item_data['name'] else "🛒"
            
            # Add rarity indicator
            rarity_emoji = {"Common": "⚪", "Rare": "🔵", "Epic": "🟣", "Legendary": "🟡"}.get(item_data.get('rarity', 'Common'), "⚪")
            
            options.append(
                discord.SelectOption(
                    label=f"{item_data['name']} - {item_data['price']:,} coins",
                    value=item_data['key'],
                    description=f"{rarity_emoji} {desc}",
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
        item_data = next((item for item in items if item['key'] == item_key), None)
        
        if not item_data:
            await interaction.response.send_message("❌ Item not found!", ephemeral=True)
            return
        
        # Show purchase confirmation
        view = PurchaseView(self.user_id, self.guild_id, item_key, item_data, self.category_name)
        
        data = await load_data()
        from .database import get_server_data
        server_data = get_server_data(data, self.guild_id)
        
        user_wallet = server_data.get("coins", {}).get(self.user_id, 0)
        user_bank = server_data.get("bank", {}).get(self.user_id, 0)
        user_total = user_wallet + user_bank
        can_afford = user_total >= item_data['price']
        
        embed = discord.Embed(
            title="🛒 Confirm Purchase",
            description=f"**{item_data['name']}**\n\n{item_data['desc']}",
            color=0x00ff00 if can_afford else 0xff0000
        )
        
        embed.add_field(name="💰 Price", value=f"{item_data['price']:,} coins", inline=True)
        embed.add_field(name="💼 Your Balance", value=f"💰 {user_wallet:,} | 🏦 {user_bank:,}\nTotal: {user_total:,}", inline=True)
        
        if can_afford:
            embed.add_field(name="📊 Payment", value="Will use wallet + bank if needed", inline=True)
            embed.set_footer(text="✅ Click 'Buy Now' to confirm (uses wallet first, then bank)")
        else:
            embed.add_field(name="❌ Short By", value=f"{item_data['price'] - user_total:,} coins", inline=True)
            embed.set_footer(text="❌ Not enough coins! Earn more with /daily, /weekly, or casino games")
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="🔙 Back to Categories", style=discord.ButtonStyle.secondary, row=2)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your shop!", ephemeral=True)
            return
        
        from .database import get_server_data
        data = await load_data()
        server_data = get_server_data(data, str(self.guild_id))
        user_coins = server_data.get("coins", {}).get(self.user_id, 0)
        
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
            value="Consumable boosts: luck, speed, stealth, fortune (6 types)",
            inline=True
        )
        
        embed.add_field(
            name="🎁 Chests",
            value="Random rewards: Common to Legendary (+ Mimic Protection)",
            inline=True
        )
        
        embed.add_field(
            name="🎰 Casino Gear",
            value="Permanent casino bonuses: slots, blackjack, coinflip (5 items)",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Heist Gear",
            value="Heist equipment: stealth, speed, security bypass (12 items)",
            inline=True
        )
        
        embed.set_footer(text="💡 Select items from dropdown menus - no typing needed!")
        
        view = ShopView(self.user_id, self.guild_id)
        await interaction.response.edit_message(embed=embed, view=view)


class ShopView(discord.ui.View):
    """Main shop view with category buttons"""
    def __init__(self, user_id, guild_id):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.guild_id = guild_id
    
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
    
    @discord.ui.button(label="🎰 Casino Gear", style=discord.ButtonStyle.primary, row=0)
    async def casino_gear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your shop!", ephemeral=True)
            return
        await self.show_category(interaction, "🎰 Casino Gear")
    
    @discord.ui.button(label="🔧 Heist Gear", style=discord.ButtonStyle.primary, row=1)
    async def heist_gear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ Not your shop!", ephemeral=True)
            return
        await self.show_category(interaction, "🔧 Heist Gear")
    
    async def show_category(self, interaction, category_name):
        """Show items in category with dropdown"""
        data = await load_data()
        from .database import get_server_data
        server_data = get_server_data(data, self.guild_id)
        
        user_coins = server_data.get("coins", {}).get(self.user_id, 0)
        
        items = SHOP_ITEMS[category_name]
        item_count = len(items)
        
        embed = discord.Embed(
            title=f"{category_name}",
            description=f"**Balance:** {user_coins:,} coins | **Items:** {item_count}\n\n🛒 **Select an item from the dropdown below to buy:**",
            color=0x3498db
        )
        
        # Discord has a 25 field limit, so we'll show items up to that limit
        for idx, item in enumerate(items[:24]):  # Leave 1 field for safety
            can_afford = "✅" if user_coins >= item['price'] else "❌"
            rarity_emoji = {"Common": "⚪", "Rare": "🔵", "Epic": "🟣", "Legendary": "🟡"}.get(item.get('rarity', 'Common'), "⚪")
            embed.add_field(
                name=f"{can_afford} {item['name']} - {item['price']:,} coins",
                value=f"{rarity_emoji} {item.get('rarity', 'Common')} | {item['desc'][:100]}",
                inline=False
            )
        
        if item_count > 24:
            embed.add_field(
                name="📋 More Items",
                value=f"Use the dropdown below to see all {item_count} items!",
                inline=False
            )
        
        embed.set_footer(text="💡 Just select from the dropdown - no typing required!")
        
        view = CategoryView(self.user_id, self.guild_id, category_name)
        await interaction.response.edit_message(embed=embed, view=view)


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shop", description="Browse the shop with easy dropdown menus!")
    async def shop(self, interaction: discord.Interaction):
        """Show the main shop"""
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id)
        
        data = await load_data()
        from .database import get_server_data
        server_data = get_server_data(data, guild_id)
        
        user_coins = server_data.get("coins", {}).get(user_id, 0)
        
        embed = discord.Embed(
            title="🛒 SORABOT SHOP - UPGRADED!",
            description="**Welcome to the NEW shop!** 29 unique items across 4 categories.\n\n💡 **Easy shopping:** Click category → Select from dropdown → Buy!\n⚪ Common | 🔵 Rare | 🟣 Epic | 🟡 Legendary",
            color=0x00ff00
        )
        
        embed.add_field(
            name="💰 Your Balance",
            value=f"```{user_coins:,} coins```",
            inline=False
        )
        
        embed.add_field(
            name="🧪 Potions (6 items)",
            value="Luck, Speed, Stealth, Fortune, Focus, Energy\n💰 2k-10k coins",
            inline=True
        )
        
        embed.add_field(
            name="🎁 Chests (5 items)",
            value="Common, Rare, Epic, Legendary + Protection\n💰 1k-50k coins",
            inline=True
        )
        
        embed.add_field(
            name="🎰 Casino Gear (5 items)",
            value="Lucky Charm, Dice, Magnet, Doubler, Counter\n💰 25k-100k coins",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Heist Gear (12 items)",
            value="Night Vision, Silent Shoes, EMP, Jetpack +more\n💰 12k-60k coins",
            inline=True
        )
        
        embed.set_footer(text="💡 All equipment is PERMANENT and REUSABLE! Start with potions for quick boosts.")
        
        view = ShopView(user_id, guild_id)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Shop(bot))
