"""
Inventory & Loot module: openchest, inventory, useitem, equip, unequip
"""
import discord
from discord import app_commands
from discord.ext import commands
import random
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

class InventoryView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.select(
        placeholder="Filter items by category...",
        options=[
            discord.SelectOption(label="All Items", description="Show all items", emoji="📦"),
            discord.SelectOption(label="Consumables", description="Single-use items", emoji="🧪"),
            discord.SelectOption(label="Equipables", description="Gear and equipment", emoji="⚔️"),
            discord.SelectOption(label="Chests", description="Loot containers", emoji="🎁"),
        ]
    )
    async def filter_items(self, interaction: discord.Interaction, select: discord.ui.Select):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ This is not your inventory!", ephemeral=True)
            return
        
        filter_type = select.values[0]
        await self.update_inventory_display(interaction, filter_type)

    async def update_inventory_display(self, interaction, filter_type="All Items"):
        data = await load_data()
        user_inventory = data.get("inventories", {}).get(self.user_id, {})
        user_equipped = data.get("equipped", {}).get(self.user_id, {})
        shop_items = data.get("shop_items", {})
        
        embed = discord.Embed(title=f"🎒 {interaction.user.display_name}'s Inventory", color=0x8e44ad)
        
        # Show equipped items
        if user_equipped:
            equipped_text = []
            for slot, item_key in user_equipped.items():
                # Find item details
                item_name = item_key.replace('_', ' ').title()
                for category in shop_items.get("equipables", {}).values():
                    if item_key in category:
                        item_name = category[item_key]["name"]
                        break
                equipped_text.append(f"**{slot.title()}**: {item_name}")
            embed.add_field(name="⚔️ Equipped", value="\n".join(equipped_text) or "None", inline=False)
        
        # Filter and show inventory items
        filtered_items = []
        for item_key, quantity in user_inventory.items():
            item_category = self.get_item_category(item_key, shop_items)
            if filter_type == "All Items" or filter_type.lower() in item_category.lower():
                item_name = self.get_item_name(item_key, shop_items)
                rarity = self.get_item_rarity(item_key, shop_items)
                emoji = self.get_category_emoji(item_category)
                filtered_items.append(f"{emoji} **{item_name}** x{quantity} ({rarity})")
        
        items_text = "\n".join(filtered_items[:15]) if filtered_items else "No items found"
        if len(filtered_items) > 15:
            items_text += f"\n... and {len(filtered_items) - 15} more items"
        
        embed.add_field(name=f"📦 {filter_type}", value=items_text, inline=False)
        embed.set_footer(text="Use /useitem, /equip, /unequip to manage items")
        
        await interaction.response.edit_message(embed=embed, view=self)

    def get_item_category(self, item_key, shop_items):
        """Determine item category"""
        for category, items in shop_items.items():
            if item_key in items or any(item_key in sub_items for sub_items in items.values() if isinstance(sub_items, dict)):
                return category
        return "unknown"

    def get_item_name(self, item_key, shop_items):
        """Get display name for item"""
        for category in shop_items.values():
            if isinstance(category, dict):
                for items in category.values():
                    if isinstance(items, dict) and item_key in items:
                        return items[item_key].get("name", item_key.replace('_', ' ').title())
        return item_key.replace('_', ' ').title()

    def get_item_rarity(self, item_key, shop_items):
        """Get item rarity"""
        for category in shop_items.values():
            if isinstance(category, dict):
                for items in category.values():
                    if isinstance(items, dict) and item_key in items:
                        return items[item_key].get("rarity", "Common")
        return "Common"

    def get_category_emoji(self, category):
        """Get emoji for category"""
        emojis = {
            "consumables": "🧪",
            "equipables": "⚔️",
            "chests": "🎁"
        }
        return emojis.get(category, "📦")

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="inventory", description="View your items and equipped gear with filtering options.")
    async def inventory(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        view = InventoryView(user_id)
        await view.update_inventory_display(interaction)

    @app_commands.command(name="openchest", description="Open a loot chest for random rewards.")
    @app_commands.describe(chest="Type of chest to open (common, rare, epic, legendary)")
    async def openchest(self, interaction: discord.Interaction, chest: str):
        user_id = str(interaction.user.id)
        chest_key = f"{chest.lower()}_chest"
        
        data = await load_data()
        user_inventory = data.get("inventories", {}).get(user_id, {})
        
        if chest_key not in user_inventory or user_inventory[chest_key] <= 0:
            await interaction.response.send_message(f"❌ You don't have any {chest} chests!", ephemeral=True)
            return
        
        loot_tables = data.get("loot_tables", {})
        chest_data = loot_tables.get(chest.lower(), {})
        
        # Check for mimic protection
        user_effects = await self.get_user_effects(user_id, data)
        has_mimic_protection = "mimic_protection" in user_effects
        
        # Roll for mimic
        mimic_chance = chest_data.get("mimic_chance", 0.1)
        is_mimic = random.random() < mimic_chance and not has_mimic_protection
        
        # Remove chest from inventory
        data.setdefault("inventories", {}).setdefault(user_id, {})[chest_key] -= 1
        if data["inventories"][user_id][chest_key] <= 0:
            del data["inventories"][user_id][chest_key]
        
        if is_mimic:
            # Mimic attack
            wallet = data.get("coins", {}).get(user_id, 0)
            coins_lost = random.randint(1, min(100, int(wallet * 0.2))) if wallet > 0 else 0
            
            if coins_lost > 0:
                data.setdefault("coins", {})[user_id] = wallet - coins_lost
            
            embed = discord.Embed(title="🧌 MIMIC ATTACK!", color=0xff0000)
            embed.description = f"The {chest} chest was a mimic! It stole {coins_lost} coins from you!"
            embed.set_footer(text="💡 Tip: Mimic Repellent can protect against this!")
            
        else:
            # Normal chest rewards
            coin_chance = chest_data.get("coin_chance", 0.7)
            
            if random.random() < coin_chance:
                # Coin reward
                coin_ranges = {
                    "common": (50, 200),
                    "rare": (150, 500),
                    "epic": (400, 1000),
                    "legendary": (800, 2500)
                }
                min_coins, max_coins = coin_ranges.get(chest.lower(), (50, 200))
                coins_gained = random.randint(min_coins, max_coins)
                
                data.setdefault("coins", {})[user_id] = data.get("coins", {}).get(user_id, 0) + coins_gained
                
                embed = discord.Embed(title=f"✨ {chest.title()} Chest Opened!", color=get_rarity_color(chest.title()))
                embed.description = f"You found {coins_gained:,} coins!"
                
            else:
                # Item reward
                items_by_rarity = {
                    "common": ["lucky_potion"],
                    "rare": ["mega_lucky_potion", "robbers_mask", "gamblers_charm", "lucky_coin"],
                    "epic": ["insurance_scroll", "golden_dice", "security_dog", "master_lockpick", "shadow_cloak"],
                    "legendary": ["vault_key", "mimic_repellent"]
                }
                
                chest_tier = chest.lower()
                possible_items = []
                if chest_tier in ["common"]:
                    possible_items = items_by_rarity["common"]
                elif chest_tier in ["rare"]:
                    possible_items = items_by_rarity["common"] + items_by_rarity["rare"]
                elif chest_tier in ["epic"]:
                    possible_items = items_by_rarity["rare"] + items_by_rarity["epic"]
                else:  # legendary
                    possible_items = items_by_rarity["epic"] + items_by_rarity["legendary"]
                
                if possible_items:
                    item_key = random.choice(possible_items)
                    data.setdefault("inventories", {}).setdefault(user_id, {})[item_key] = data["inventories"][user_id].get(item_key, 0) + 1
                    
                    # Get item name
                    item_name = self.get_item_name(item_key, data.get("shop_items", {}))
                    
                    embed = discord.Embed(title=f"✨ {chest.title()} Chest Opened!", color=get_rarity_color(chest.title()))
                    embed.description = f"You found: **{item_name}**!"
                    embed.add_field(name="🎁 Item Added", value="Check your inventory!", inline=False)
        
        # Consume mimic protection if used
        if has_mimic_protection and is_mimic:
            await self.consume_effect(user_id, "mimic_protection", data)
        
        await save_data(data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="useitem", description="Use a consumable item.")
    @app_commands.describe(item="Name of the consumable item to use")
    async def useitem(self, interaction: discord.Interaction, item: str):
        user_id = str(interaction.user.id)
        item_key = item.lower().replace(' ', '_')
        
        data = await load_data()
        user_inventory = data.get("inventories", {}).get(user_id, {})
        
        if item_key not in user_inventory or user_inventory[item_key] <= 0:
            await interaction.response.send_message(f"❌ You don't have any {item}!", ephemeral=True)
            return
        
        # Check if item is consumable
        shop_items = data.get("shop_items", {})
        consumables = shop_items.get("consumables", {})
        
        if item_key not in consumables:
            await interaction.response.send_message("❌ This item is not consumable!", ephemeral=True)
            return
        
        item_data = consumables[item_key]
        effect_type = item_data.get("effect")
        effect_value = item_data.get("value")
        
        # Remove item from inventory
        data.setdefault("inventories", {}).setdefault(user_id, {})[item_key] -= 1
        if data["inventories"][user_id][item_key] <= 0:
            del data["inventories"][user_id][item_key]
        
        # Apply effect
        data.setdefault("consumable_effects", {}).setdefault(user_id, {})[effect_type] = effect_value
        
        await save_data(data)
        
        embed = discord.Embed(title="� Item Used", color=get_rarity_color(item_data.get("rarity", "Common")))
        embed.add_field(name="Item", value=item_data["name"], inline=True)
        embed.add_field(name="Effect", value=f"{effect_type.replace('_', ' ').title()}: +{effect_value*100:.0f}%", inline=True)
        embed.description = "Effect will be applied to your next applicable action!"
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="equip", description="Equip an item for passive effects.")
    @app_commands.describe(item="Name of the item to equip")
    async def equip(self, interaction: discord.Interaction, item: str):
        user_id = str(interaction.user.id)
        item_key = item.lower().replace(' ', '_')
        
        data = await load_data()
        user_inventory = data.get("inventories", {}).get(user_id, {})
        
        if item_key not in user_inventory or user_inventory[item_key] <= 0:
            await interaction.response.send_message(f"❌ You don't have any {item}!", ephemeral=True)
            return
        
        # Check if item is equipable
        shop_items = data.get("shop_items", {})
        equipables = shop_items.get("equipables", {})
        
        if item_key not in equipables:
            await interaction.response.send_message("❌ This item is not equipable!", ephemeral=True)
            return
        
        item_data = equipables[item_key]
        slot = item_data.get("slot")
        
        # Check if slot is already occupied
        user_equipped = data.get("equipped", {}).get(user_id, {})
        if slot in user_equipped:
            # Unequip current item
            current_item = user_equipped[slot]
            data.setdefault("inventories", {}).setdefault(user_id, {})[current_item] = user_inventory.get(current_item, 0) + 1
        
        # Remove item from inventory and equip it
        data.setdefault("inventories", {}).setdefault(user_id, {})[item_key] -= 1
        if data["inventories"][user_id][item_key] <= 0:
            del data["inventories"][user_id][item_key]
        
        data.setdefault("equipped", {}).setdefault(user_id, {})[slot] = item_key
        
        await save_data(data)
        
        embed = discord.Embed(title="⚔️ Item Equipped", color=get_rarity_color(item_data.get("rarity", "Common")))
        embed.add_field(name="Item", value=item_data["name"], inline=True)
        embed.add_field(name="Slot", value=slot.title(), inline=True)
        embed.add_field(name="Effect", value=f"{item_data['effect'].replace('_', ' ').title()}: +{item_data['value']*100:.1f}%", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unequip", description="Unequip an item from a slot.")
    @app_commands.describe(slot="Equipment slot to unequip (trinket, armor, weapon, bank_mod)")
    async def unequip(self, interaction: discord.Interaction, slot: str):
        user_id = str(interaction.user.id)
        slot = slot.lower()
        
        data = await load_data()
        user_equipped = data.get("equipped", {}).get(user_id, {})
        
        if slot not in user_equipped:
            await interaction.response.send_message(f"❌ No item equipped in {slot} slot!", ephemeral=True)
            return
        
        item_key = user_equipped[slot]
        
        # Move item back to inventory
        data.setdefault("inventories", {}).setdefault(user_id, {})[item_key] = data["inventories"][user_id].get(item_key, 0) + 1
        
        # Remove from equipped
        del data["equipped"][user_id][slot]
        if not data["equipped"][user_id]:
            del data["equipped"][user_id]
        
        await save_data(data)
        
        # Get item name
        item_name = self.get_item_name(item_key, data.get("shop_items", {}))
        
        embed = discord.Embed(title="📤 Item Unequipped", color=0x95a5a6)
        embed.add_field(name="Item", value=item_name, inline=True)
        embed.add_field(name="Slot", value=slot.title(), inline=True)
        embed.description = "Item returned to inventory."
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def get_user_effects(self, user_id, data):
        """Get all active effects for a user"""
        effects = {}
        
        # Consumable effects
        consumable_effects = data.get("consumable_effects", {}).get(user_id, {})
        effects.update(consumable_effects)
        
        return effects

    async def consume_effect(self, user_id, effect_type, data):
        """Remove a consumable effect after use"""
        if user_id in data.get("consumable_effects", {}):
            data["consumable_effects"][user_id].pop(effect_type, None)
            if not data["consumable_effects"][user_id]:
                del data["consumable_effects"][user_id]

    def get_item_name(self, item_key, shop_items):
        """Get display name for item"""
        for category in shop_items.values():
            if isinstance(category, dict):
                for items in category.values():
                    if isinstance(items, dict) and item_key in items:
                        return items[item_key].get("name", item_key.replace('_', ' ').title())
        return item_key.replace('_', ' ').title()

async def setup(bot):
    await bot.add_cog(Inventory(bot))
