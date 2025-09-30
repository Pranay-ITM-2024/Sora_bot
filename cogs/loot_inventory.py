"""
Loot & Inventory system cog
"""

import discord
from discord.ext import commands
import random
import datetime
from typing import Dict, List, Optional, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import DataManager, CONSUMABLE_ITEMS, EQUIPABLE_ITEMS, CHEST_TYPES

class LootInventoryCommands(commands.Cog):
    """Loot & Inventory commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='openchest')
    async def openchest(self, ctx, chest_type: str):
        """Open loot chests"""
        if chest_type.lower() not in CHEST_TYPES:
            await ctx.send(f"❌ Invalid chest type! Available: {', '.join(CHEST_TYPES.keys())}")
            return
        
        chest_data = CHEST_TYPES[chest_type.lower()]
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Check if user has enough coins
        if data["coins"].get(user_id, 0) < chest_data["price"]:
            await ctx.send(f"❌ You need {chest_data['price']:,} coins to open a {chest_data['name']}!")
            return
        
        # Check for mimic protection
        mimic_protected = False
        active_effects = data["consumable_effects"].get(user_id, {})
        if "mimic_protection" in active_effects:
            mimic_protected = True
            del data["consumable_effects"][user_id]["mimic_protection"]
            if not data["consumable_effects"][user_id]:
                del data["consumable_effects"][user_id]
        
        # Deduct cost
        data["coins"][user_id] -= chest_data["price"]
        
        # Check for mimic
        if not mimic_protected and random.random() < chest_data["mimic_chance"]:
            # Mimic spawns - lose the chest
            embed = discord.Embed(
                title="💀 Mimic Attack!",
                description=f"A mimic was hiding in the {chest_data['name']}! You lost your coins and the chest disappeared!",
                color=0xff0000
            )
            await DataManager.save_data(data)
            await ctx.send(embed=embed)
            return
        
        # Determine loot
        loot_roll = random.random()
        if loot_roll < chest_data["coin_chance"]:
            # Coins reward
            base_reward = chest_data["price"] * random.uniform(0.5, 2.0)
            coin_reward = int(base_reward)
            data["coins"][user_id] += coin_reward
            
            embed = discord.Embed(
                title="💰 Chest Opened!",
                description=f"You found **{coin_reward:,} coins** in the {chest_data['name']}!",
                color=0xffd700
            )
        else:
            # Item reward
            item_reward = self.get_random_item_from_chest(chest_type.lower())
            if item_reward:
                item_id, quantity = item_reward
                
                # Add to inventory
                if user_id not in data["inventories"]:
                    data["inventories"][user_id] = {}
                data["inventories"][user_id][item_id] = data["inventories"][user_id].get(item_id, 0) + quantity
                
                item_name = "Unknown Item"
                if item_id in CONSUMABLE_ITEMS:
                    item_name = CONSUMABLE_ITEMS[item_id]["name"]
                elif item_id in EQUIPABLE_ITEMS:
                    item_name = EQUIPABLE_ITEMS[item_id]["name"]
                
                embed = discord.Embed(
                    title="🎁 Chest Opened!",
                    description=f"You found **{item_name} x{quantity}** in the {chest_data['name']}!",
                    color=0x00ff00
                )
            else:
                # Fallback to coins if no item found
                coin_reward = int(chest_data["price"] * 0.5)
                data["coins"][user_id] += coin_reward
                
                embed = discord.Embed(
                    title="💰 Chest Opened!",
                    description=f"You found **{coin_reward:,} coins** in the {chest_data['name']}!",
                    color=0xffd700
                )
        
        await DataManager.save_data(data)
        await ctx.send(embed=embed)
    
    def get_random_item_from_chest(self, chest_type: str) -> Optional[tuple]:
        """Get a random item from a chest based on its tier"""
        if chest_type == "common":
            # Common items only
            common_items = ["lucky_potion"]
            item_id = random.choice(common_items)
            return (item_id, 1)
        elif chest_type == "rare":
            # Mix of common and rare items
            items = ["lucky_potion", "mega_lucky_potion", "jackpot_booster", "robbers_mask", "gamblers_charm", "lucky_coin"]
            item_id = random.choice(items)
            return (item_id, 1)
        elif chest_type == "epic":
            # Mix of rare and epic items
            items = ["mega_lucky_potion", "jackpot_booster", "robbers_mask", "insurance_scroll", "golden_dice", "security_dog", "master_lockpick", "shadow_cloak"]
            item_id = random.choice(items)
            return (item_id, 1)
        elif chest_type == "legendary":
            # All items possible, with higher chance for epic/legendary
            items = ["insurance_scroll", "mimic_repellent", "vault_key", "golden_dice", "security_dog", "master_lockpick", "shadow_cloak"]
            item_id = random.choice(items)
            return (item_id, 1)
        
        return None
    
    @commands.command(name='inventory')
    async def inventory(self, ctx):
        """View owned items and equipped items"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Get inventory
        inventory = data["inventories"].get(user_id, {})
        equipped = data["equipped"].get(user_id, {})
        
        # Format inventory
        inventory_text = "**Inventory:**\n"
        if inventory:
            for item_id, quantity in inventory.items():
                item_name = "Unknown Item"
                if item_id in CONSUMABLE_ITEMS:
                    item_name = CONSUMABLE_ITEMS[item_id]["name"]
                elif item_id in EQUIPABLE_ITEMS:
                    item_name = EQUIPABLE_ITEMS[item_id]["name"]
                inventory_text += f"• {item_name} x{quantity}\n"
        else:
            inventory_text += "No items in inventory\n"
        
        # Format equipped items
        equipped_text = "**Equipped Items:**\n"
        if equipped:
            for item_id, quantity in equipped.items():
                if item_id in EQUIPABLE_ITEMS:
                    item_name = EQUIPABLE_ITEMS[item_id]["name"]
                    slot = EQUIPABLE_ITEMS[item_id]["slot"]
                    equipped_text += f"• {item_name} ({slot}) x{quantity}\n"
        else:
            equipped_text += "No items equipped\n"
        
        embed = discord.Embed(
            title=f"🎒 {ctx.author.display_name}'s Inventory",
            description=f"{inventory_text}\n{equipped_text}",
            color=0x0099ff
        )
        
        view = InventoryView(ctx.author, self.bot)
        await ctx.send(embed=embed, view=view)
    
    @commands.command(name='useitem')
    async def useitem(self, ctx, item_name: str):
        """Use a consumable item"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Find item in inventory
        item_id = None
        for item_key, item_data in CONSUMABLE_ITEMS.items():
            if item_data["name"].lower() == item_name.lower():
                item_id = item_key
                break
        
        if not item_id:
            await ctx.send("❌ Item not found!")
            return
        
        inventory = data["inventories"].get(user_id, {})
        if inventory.get(item_id, 0) < 1:
            await ctx.send("❌ You don't have this item!")
            return
        
        # Use the item
        item_data = CONSUMABLE_ITEMS[item_id]
        
        # Initialize effects if needed
        if user_id not in data["consumable_effects"]:
            data["consumable_effects"][user_id] = {}
        
        # Apply effect
        effect_type = item_data["effect"]
        effect_value = item_data["value"]
        
        if effect_type == "gambling_boost":
            data["consumable_effects"][user_id]["gambling_boost"] = effect_value
            await ctx.send(f"✅ Used {item_data['name']}! Your next casino game has +{effect_value*100:.0f}% win chance!")
        elif effect_type == "payout_boost":
            data["consumable_effects"][user_id]["payout_boost"] = effect_value
            await ctx.send(f"✅ Used {item_data['name']}! Your next slots spin has +{effect_value*100:.0f}% payout!")
        elif effect_type == "rob_boost":
            data["consumable_effects"][user_id]["rob_boost"] = effect_value
            await ctx.send(f"✅ Used {item_data['name']}! Your next robbery has +{effect_value*100:.0f}% success chance!")
        elif effect_type == "insurance":
            data["consumable_effects"][user_id]["insurance"] = effect_value
            await ctx.send(f"✅ Used {item_data['name']}! Your next lost bet will be refunded {effect_value*100:.0f}%!")
        elif effect_type == "mimic_protection":
            data["consumable_effects"][user_id]["mimic_protection"] = effect_value
            await ctx.send(f"✅ Used {item_data['name']}! You're protected from the next mimic!")
        
        # Remove item from inventory
        inventory[item_id] -= 1
        if inventory[item_id] <= 0:
            del inventory[item_id]
        
        await DataManager.save_data(data)
    
    @commands.command(name='equip')
    async def equip(self, ctx, item_name: str):
        """Equip an item"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        # Find item in inventory
        item_id = None
        for item_key, item_data in EQUIPABLE_ITEMS.items():
            if item_data["name"].lower() == item_name.lower():
                item_id = item_key
                break
        
        if not item_id:
            await ctx.send("❌ Equipable item not found!")
            return
        
        inventory = data["inventories"].get(user_id, {})
        if inventory.get(item_id, 0) < 1:
            await ctx.send("❌ You don't have this item!")
            return
        
        # Check if slot is already occupied
        item_data = EQUIPABLE_ITEMS[item_id]
        slot = item_data["slot"]
        
        equipped = data["equipped"].get(user_id, {})
        for equipped_item_id, quantity in equipped.items():
            if equipped_item_id in EQUIPABLE_ITEMS and EQUIPABLE_ITEMS[equipped_item_id]["slot"] == slot:
                await ctx.send(f"❌ You already have an item equipped in the {slot} slot! Use `/unequip {slot}` first.")
                return
        
        # Equip the item
        if user_id not in data["equipped"]:
            data["equipped"][user_id] = {}
        
        data["equipped"][user_id][item_id] = data["equipped"][user_id].get(item_id, 0) + 1
        
        # Remove from inventory
        inventory[item_id] -= 1
        if inventory[item_id] <= 0:
            del inventory[item_id]
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="⚔️ Item Equipped!",
            description=f"Equipped **{item_data['name']}** in the **{slot}** slot!\n**Effect:** {self.get_item_effect_description(item_data)}",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='unequip')
    async def unequip(self, ctx, slot: str):
        """Unequip an item back to inventory"""
        data = await DataManager.load_data()
        user_id = str(ctx.author.id)
        
        equipped = data["equipped"].get(user_id, {})
        item_to_unequip = None
        
        # Find item in the specified slot
        for item_id, quantity in equipped.items():
            if item_id in EQUIPABLE_ITEMS and EQUIPABLE_ITEMS[item_id]["slot"] == slot.lower():
                item_to_unequip = item_id
                break
        
        if not item_to_unequip:
            await ctx.send(f"❌ No item equipped in the {slot} slot!")
            return
        
        # Unequip the item
        data["equipped"][user_id][item_to_unequip] -= 1
        if data["equipped"][user_id][item_to_unequip] <= 0:
            del data["equipped"][user_id][item_to_unequip]
        
        # Add back to inventory
        if user_id not in data["inventories"]:
            data["inventories"][user_id] = {}
        data["inventories"][user_id][item_to_unequip] = data["inventories"][user_id].get(item_to_unequip, 0) + 1
        
        item_name = EQUIPABLE_ITEMS[item_to_unequip]["name"]
        
        await DataManager.save_data(data)
        
        embed = discord.Embed(
            title="📦 Item Unequipped!",
            description=f"Unequipped **{item_name}** from the **{slot}** slot and returned it to your inventory.",
            color=0xffa500
        )
        await ctx.send(embed=embed)
    
    def get_item_effect_description(self, item_data):
        """Get a description of the item's effect"""
        effect = item_data["effect"]
        value = item_data["value"]
        
        if effect == "gambling_boost":
            return f"+{value*100:.0f}% gambling win chance"
        elif effect == "slots_boost":
            return f"+{value*100:.0f}% slots payout"
        elif effect == "rob_protection":
            return f"Blocks {int(value)} robbery attempt"
        elif effect == "bank_interest":
            return f"+{value*100:.2f}% bank interest"
        elif effect == "rob_boost":
            return f"+{value*100:.0f}% rob success chance"
        elif effect == "rat_race_boost":
            return f"+{value*100:.0f}% rat race winnings"
        elif effect == "stealth":
            return f"-{value*100:.0f}% chance of being targeted"
        else:
            return "Unknown effect"

class InventoryView(discord.ui.View):
    def __init__(self, user, bot):
        super().__init__(timeout=60)
        self.user = user
        self.bot = bot
    
    @discord.ui.button(label='Use Item', style=discord.ButtonStyle.blurple)
    async def use_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This is not your inventory!", ephemeral=True)
            return
        
        modal = UseItemModal(self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Equip Item', style=discord.ButtonStyle.green)
    async def equip_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This is not your inventory!", ephemeral=True)
            return
        
        modal = EquipItemModal(self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Unequip Item', style=discord.ButtonStyle.red)
    async def unequip_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This is not your inventory!", ephemeral=True)
            return
        
        modal = UnequipItemModal(self.bot)
        await interaction.response.send_modal(modal)

class UseItemModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Use Item")
        self.bot = bot
        
        self.item_input = discord.ui.TextInput(
            label="Item Name",
            placeholder="Enter the name of the item to use...",
            required=True
        )
        self.add_item(self.item_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        item_name = self.item_input.value
        # Execute useitem command
        from discord.ext import commands
        ctx = await self.bot.get_context(interaction.message)
        await ctx.invoke(self.bot.get_command('useitem'), item_name)

class EquipItemModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Equip Item")
        self.bot = bot
        
        self.item_input = discord.ui.TextInput(
            label="Item Name",
            placeholder="Enter the name of the item to equip...",
            required=True
        )
        self.add_item(self.item_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        item_name = self.item_input.value
        # Execute equip command
        from discord.ext import commands
        ctx = await self.bot.get_context(interaction.message)
        await ctx.invoke(self.bot.get_command('equip'), item_name)

class UnequipItemModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Unequip Item")
        self.bot = bot
        
        self.slot_input = discord.ui.TextInput(
            label="Slot (trinket, weapon, armor, bank_mod)",
            placeholder="Enter the slot to unequip...",
            required=True
        )
        self.add_item(self.slot_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        slot = self.slot_input.value
        # Execute unequip command
        from discord.ext import commands
        ctx = await self.bot.get_context(interaction.message)
        await ctx.invoke(self.bot.get_command('unequip'), slot)

async def setup(bot):
    await bot.add_cog(LootInventoryCommands(bot))
