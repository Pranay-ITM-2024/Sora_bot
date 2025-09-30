"""
Shop module: shop, buyitem with interactive UI and full integration
"""
import discord
from discord import app_commands
from discord.ext import commands
import json
import aiofiles
from pathlib import Path
import asyncio

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

def get_rarity_color(rarity):
    """Get color for item rarity"""
    colors = {
        "Common": 0x9e9e9e,
        "Rare": 0x3f51b5,
        "Epic": 0x9c27b0,
        "Legendary": 0xff9800
    }
    return colors.get(rarity, 0x9e9e9e)

async def get_guild_discount(user_id, data):
    """Check if user's guild gets shop discount"""
    user_id = str(user_id)
    user_guild = None
    
    # Find user's guild
    guild_members = data.get("guild_members", {})
    for guild_name, members in guild_members.items():
        if user_id in members:
            user_guild = guild_name
            break
    
    if not user_guild:
        return 0
    
    # Check if this is the richest guild
    guilds = data.get("guilds", {})
    if not guilds:
        return 0
    
    richest_guild = max(guilds.items(), key=lambda x: x[1].get("bank", 0))
    if richest_guild[0] == user_guild:
        return 0.1  # 10% discount
    
    return 0

class ShopCategoryView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.select(
        placeholder="Choose a category to browse...",
        options=[
            discord.SelectOption(label="Consumables", description="Single-use items with temporary effects", emoji="🧪"),
            discord.SelectOption(label="Equipables", description="Gear with passive effects", emoji="⚔️"),
            discord.SelectOption(label="Loot Chests", description="Random reward containers", emoji="🎁"),
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This shop interface is not for you!", ephemeral=True)
            return
        
        category = select.values[0].lower()
        await self.show_category_items(interaction, category)

    async def show_category_items(self, interaction, category):
        data = await load_data()
        shop_items = data.get("shop_items", {})
        user_coins = data.get("coins", {}).get(self.user_id, 0)
        discount = await get_guild_discount(self.user_id, data)
        
        if category == "consumables":
            items = shop_items.get("consumables", {})
            embed = discord.Embed(title="🧪 Consumables Shop", description="Single-use items with powerful temporary effects", color=0x27ae60)
            
        elif category == "equipables":
            items = shop_items.get("equipables", {})
            embed = discord.Embed(title="⚔️ Equipables Shop", description="Gear with permanent passive effects", color=0xe74c3c)
            
        else:  # loot chests
            items = shop_items.get("chests", {})
            embed = discord.Embed(title="🎁 Loot Chests Shop", description="Mysterious containers with random rewards", color=0xf39c12)
        
        embed.add_field(name="💰 Your Balance", value=f"{user_coins:,} coins", inline=True)
        if discount > 0:
            embed.add_field(name="🎉 Guild Discount", value=f"{discount*100:.0f}% OFF!", inline=True)
        
        item_list = []
        for item_key, item_data in items.items():
            price = item_data["price"]
            if discount > 0:
                price = int(price * (1 - discount))
            
            rarity_emoji = {"Common": "⚪", "Rare": "🔵", "Epic": "🟣", "Legendary": "🟡"}
            emoji = rarity_emoji.get(item_data.get("rarity", "Common"), "⚪")
            
            affordable = "✅" if user_coins >= price else "❌"
            
            if category == "consumables":
                effect_desc = f"+{item_data.get('value', 0)*100:.0f}% {item_data.get('effect', '').replace('_', ' ')}"
            elif category == "equipables":
                effect_desc = f"{item_data.get('slot', 'unknown').title()} slot - +{item_data.get('value', 0)*100:.1f}% {item_data.get('effect', '').replace('_', ' ')}"
            else:  # chests
                mimic_chances = {"Common": "5%", "Rare": "10%", "Epic": "15%", "Legendary": "20%"}
                effect_desc = f"Mimic chance: {mimic_chances.get(item_data.get('rarity', 'Common'), '5%')}"
            
            item_list.append(f"{affordable} {emoji} **{item_data['name']}** - {price:,} coins\n    {effect_desc}")
        
        embed.add_field(name="🛒 Available Items", value="\n\n".join(item_list) if item_list else "No items available", inline=False)
        embed.add_field(name="💡 How to Buy", value="Use `/buyitem <item_name>` to purchase any item!", inline=False)
        embed.set_footer(text="Tip: Items integrate with all bot systems - casino, PvP, economy!")
        
        view = ShopCategoryView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

class PurchaseConfirmView(discord.ui.View):
    def __init__(self, user_id, item_key, item_data, final_price, category):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.item_key = item_key
        self.item_data = item_data
        self.final_price = final_price
        self.category = category

    @discord.ui.button(label="Confirm Purchase", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This purchase is not for you!", ephemeral=True)
            return
        
        data = await load_data()
        user_coins = data.get("coins", {}).get(self.user_id, 0)
        
        if user_coins < self.final_price:
            await interaction.response.send_message(f"❌ Insufficient funds! You need {self.final_price - user_coins:,} more coins.", ephemeral=True)
            return
        
        # Process purchase
        data.setdefault("coins", {})[self.user_id] = user_coins - self.final_price
        
        # Add item to inventory
        if self.category == "chests":
            chest_key = self.item_key
        else:
            chest_key = self.item_key
        
        data.setdefault("inventories", {}).setdefault(self.user_id, {})[chest_key] = data["inventories"][self.user_id].get(chest_key, 0) + 1
        
        # Add transaction
        from datetime import datetime
        tx = {
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "type": "debit",
            "amount": self.final_price,
            "reason": f"Purchased {self.item_data['name']}"
        }
        data.setdefault("transactions", {}).setdefault(self.user_id, []).append(tx)
        
        await save_data(data)
        
        embed = discord.Embed(title="🛒 Purchase Successful!", color=get_rarity_color(self.item_data.get("rarity", "Common")))
        embed.add_field(name="Item", value=self.item_data["name"], inline=True)
        embed.add_field(name="Price Paid", value=f"{self.final_price:,} coins", inline=True)
        embed.add_field(name="New Balance", value=f"{user_coins - self.final_price:,} coins", inline=True)
        embed.description = f"**{self.item_data['name']}** has been added to your inventory!"
        embed.set_footer(text="Check /inventory to see your new item!")
        
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel_purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This purchase is not for you!", ephemeral=True)
            return
        
        embed = discord.Embed(title="❌ Purchase Cancelled", color=0x95a5a6)
        embed.description = "No coins were spent."
        await interaction.response.edit_message(embed=embed, view=None)

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="shop", description="Browse the interactive shop with categories and effects.")
    async def shop(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = await load_data()
        user_coins = data.get("coins", {}).get(user_id, 0)
        discount = await get_guild_discount(user_id, data)
        
        embed = discord.Embed(title="🛒 SORABOT Shop", description="Welcome to the ultimate item marketplace!", color=0x27ae60)
        embed.add_field(name="💰 Your Balance", value=f"{user_coins:,} coins", inline=True)
        embed.add_field(name="🎯 Quick Buy", value="Use `/buyitem <name>`", inline=True)
        
        if discount > 0:
            embed.add_field(name="🎉 Guild Bonus", value=f"{discount*100:.0f}% discount active!", inline=True)
        
        embed.add_field(
            name="🧪 Consumables",
            value="• Lucky Potion - +20% casino wins\n• Mega Lucky Potion - +50% casino wins\n• Jackpot Booster - +10% slots payout\n• Robber's Mask - +15% rob success\n• Insurance Scroll - 50% bet refund\n• Mimic Repellent - Blocks mimics",
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Equipables",
            value="• Gambler's Charm - +5% gambling wins\n• Golden Dice - +10% slots payout\n• Security Dog - Blocks robberies\n• Vault Key - +0.25% bank interest\n• Master Lockpick - +10% rob success\n• Lucky Coin - +5% rat race wins\n• Shadow Cloak - -15% rob targeting",
            inline=False
        )
        
        embed.add_field(
            name="🎁 Loot Chests",
            value="• Common Chest - 100 coins (5% mimic)\n• Rare Chest - 300 coins (10% mimic)\n• Epic Chest - 600 coins (15% mimic)\n• Legendary Chest - 1200 coins (20% mimic)",
            inline=False
        )
        
        embed.set_footer(text="💡 All items integrate with casino, PvP, economy, and guild systems!")
        
        view = ShopCategoryView(user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="buyitem", description="Purchase an item directly by name.")
    @app_commands.describe(item="Name of the item to purchase")
    async def buyitem(self, interaction: discord.Interaction, item: str):
        user_id = str(interaction.user.id)
        item_key = item.lower().replace(' ', '_').replace("'", "")
        
        data = await load_data()
        shop_items = data.get("shop_items", {})
        user_coins = data.get("coins", {}).get(user_id, 0)
        discount = await get_guild_discount(user_id, data)
        
        # Find item in shop
        item_data = None
        category = None
        
        for cat_name, cat_items in shop_items.items():
            if item_key in cat_items:
                item_data = cat_items[item_key]
                category = cat_name
                break
        
        if not item_data:
            # Try fuzzy matching
            all_items = {}
            for cat_name, cat_items in shop_items.items():
                for k, v in cat_items.items():
                    all_items[k] = (v, cat_name)
                    # Also add by display name
                    display_key = v.get("name", "").lower().replace(' ', '_').replace("'", "")
                    all_items[display_key] = (v, cat_name)
            
            if item_key in all_items:
                item_data, category = all_items[item_key]
            else:
                await interaction.response.send_message(f"❌ Item '{item}' not found! Use `/shop` to browse available items.", ephemeral=True)
                return
        
        # Calculate final price with discount
        base_price = item_data["price"]
        final_price = int(base_price * (1 - discount))
        
        embed = discord.Embed(title="� Purchase Confirmation", color=get_rarity_color(item_data.get("rarity", "Common")))
        embed.add_field(name="Item", value=item_data["name"], inline=True)
        embed.add_field(name="Category", value=category.title(), inline=True)
        embed.add_field(name="Rarity", value=item_data.get("rarity", "Common"), inline=True)
        
        if discount > 0:
            embed.add_field(name="Base Price", value=f"~~{base_price:,}~~ coins", inline=True)
            embed.add_field(name="Guild Discount", value=f"-{discount*100:.0f}%", inline=True)
            embed.add_field(name="Final Price", value=f"**{final_price:,} coins**", inline=True)
        else:
            embed.add_field(name="Price", value=f"{final_price:,} coins", inline=True)
        
        # Add effect description
        if category == "consumables":
            effect_desc = f"**Effect**: +{item_data.get('value', 0)*100:.0f}% {item_data.get('effect', '').replace('_', ' ')} (next use)"
        elif category == "equipables":
            effect_desc = f"**Slot**: {item_data.get('slot', 'unknown').title()}\n**Effect**: +{item_data.get('value', 0)*100:.1f}% {item_data.get('effect', '').replace('_', ' ')} (passive)"
        else:  # chests
            loot_info = {
                "Common": "70% coins, 25% items, 5% mimic",
                "Rare": "50% coins, 40% items, 10% mimic", 
                "Epic": "30% coins, 60% items, 15% mimic",
                "Legendary": "10% coins, 80% items, 20% mimic"
            }
            rarity = item_data.get("rarity", "Common")
            effect_desc = f"**Contents**: {loot_info.get(rarity, 'Random rewards')}"
        
        embed.add_field(name="Details", value=effect_desc, inline=False)
        
        embed.add_field(name="Your Balance", value=f"{user_coins:,} coins", inline=True)
        affordable = user_coins >= final_price
        embed.add_field(name="After Purchase", value=f"{user_coins - final_price:,} coins" if affordable else "❌ Insufficient funds", inline=True)
        
        if affordable:
            view = PurchaseConfirmView(user_id, item_key, item_data, final_price, category)
            embed.set_footer(text="Confirm your purchase below")
        else:
            view = None
            embed.set_footer(text=f"You need {final_price - user_coins:,} more coins")
            embed.color = 0xe74c3c
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Shop(bot))
