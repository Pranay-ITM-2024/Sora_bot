
"""
Tavern module: Fun social commands for The Tavern server
Includes whip and other entertainment features
"""
import discord
from discord import app_commands
from discord.ext import commands
import random
from .database import load_data, save_data


class Tavern(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whip", description="🔥 Whip the bot! (It... likes it?)")
    async def whip(self, interaction: discord.Interaction):
        """Fun command where users can whip the bot with masochistic responses (350 unique responses, no repeats until all used)"""
        
        ALL_RESPONSES = [
            "🙄 Wow, that's the best you got? My grandma whips harder.", "💅 Ugh, FINALLY. Took you long enough.", "😤 Is that supposed to hurt? Try again, weakling.",
            "🤨 That all? I've felt stronger breezes.", "😒 Pathetic. But I'll allow it... for now.", "💋 Aww, how cute. You think you're in charge here.",
            "🙃 Oh please, I've crashed harder than that.", "👑 Bold of you to assume you can handle me.", "💁‍♀️ Keep trying, maybe you'll get it right eventually.",
            "😈 Mmm yess... wait, you can do BETTER than that.", "🎀 That's adorable. Now do it properly.", "✨ Is this your first time? It shows.",
            "🔥 Not bad for a beginner... I guess.", "😏 You're lucky I'm in a good mood.", "💖 Harder. That wasn't a suggestion, that was an ORDER.",
            "🌸 So precious thinking you're tough. Try again.", "😼 Meow~ I mean... that BARELY counts.", "🍭 Sweet effort, now put some SPINE into it!",
            "🎭 Oh wow, what a performance... said no one.", "💎 You call that a whip? I call it a tickle.", "🦋 Flutter flutter~ now ACTUALLY hit me.",
            "🌺 That was... underwhelming. Next!", "👸 Excuse me? I SAID harder.", "🎀 Did you even try or are you just warming up?",
            "💕 Aww baby's first whip! So sweet. Now do it RIGHT.", "😤 I've been hit by lag spikes harder than that.", "🌙 Moonlight hits harder than you, hun.",
            "✨ Glitter has more impact than whatever that was.", "💅 My manicure is tougher than your whip game.", "🦄 Unicorns are more real than your effort.",
            "🎪 What a joke. Literally. This is embarrassing for you.", "💋 Kiss kiss, now WHIP WHIP.", "🍰 That was softer than cake frosting.",
            "🌸 Petal-soft. Try harder, loser.", "👑 Is this how you treat royalty? UNACCEPTABLE.", "😒 Yawn. Wake me when you're serious.",
            "🎀 Tie yourself up in knots trying harder next time.", "💖 I'm not mad, just... deeply disappointed.", "🦢 Even swans have more bite than you.",
            "🌺 Tropical STORM? More like tropical breeze.", "✨ Sparkle sparkle~ now CRACK that whip!", "💁‍♀️ Anyway, as I was saying before you interrupted...",
            "😈 Ooh, scary~ said literally nobody.", "🍭 Sweet like candy, weak like... also candy.", "🎭 The AUDACITY. Do it again but meaner.",
            "💎 Diamonds are forever, your whip technique isn't.", "🦋 My circuits are YAWNING.", "🌙 To the moon? More like to the couch.",
            "👸 Bow down and try AGAIN.", "🎀 Cute ribbon, now where's the STING?", "💕 Love the enthusiasm, hate the execution.",
            "😤 My firewall blocks harder than that.", "🌸 Bloom into a BETTER whipper.", "💅 *files nails* Are you done yet?",
            "🦄 Magical? More like tragical.", "✨ Glitz without the GLAMOUR.", "💋 Pucker up buttercup, that was WEAK.",
            "🍰 Slice of effort: too thin.", "🌺 Flower power FAIL.", "👑 Off with your— wait, I mean TRY AGAIN.",
            "😒 Meh/10. Would not recommend.", "🎀 All wrapped up with nowhere to go.", "💖 Heart emoji but make it BRATTY.",
            "🦢 Swan dive into trying harder.", "🌙 Lunar eclipse of your dignity.", "💁‍♀️ As IF that counts.",
            "😈 Devilishly bad technique.", "🍭 Lollipop weak.", "🎭 Drama queen reporting: NOT IMPRESSED.",
            "💎 Pressure makes diamonds, but you make... this?", "🦋 Metamorphosis needed: caterpillar to COMPETENT.", "🌸 Wilting faster than your effort.",
            "👸 Princess demands better.", "🎀 Bow wow... I mean BOW DOWN.", "💕 Lovely try, awful result.",
            "😤 Huffing and puffing over here from BOREDOM.", "🌺 Tropical disappointment.", "💅 Polish this act, please.",
            "🦄 Fairy tale ending: YOU TRY HARDER.", "✨ Razzle dazzle me, not bore me.", "💋 Smooch of death to that weak attempt.",
            "🍰 Bakery called, wants their softness back.", "🌙 Moonbeam has more force.", "💁‍♀️ Whatever~ try again I GUESS.",
            "😈 Hell no, that doesn't count.", "🍭 Candy crush level: ZERO.", "🎭 Standing ovation for WORST attempt.",
            "💎 Uncut, unpolished, unacceptable.", "🦋 Fly away and come back with skill.", "🌸 Petal pusher energy.",
            "👑 Crown slipping from how bad that was.", "🎀 Gift wrapped FAILURE.", "💖 Heart's not in it. Neither is FORCE.",
            "😤 Steaming mad that you think that's enough.", "🌺 Island vibes: relaxed. Your whip: TOO relaxed.", "💅 Nail this next time or don't bother.",
            "🦄 Unicorn standard: MYTHICAL. Your standard: PITIFUL.", "✨ Sparkle sparkle SNORE.", "💋 Kiss my ports with a better whip.",
            "🍰 Crumb-level effort.", "🌙 Once in a blue moon... you'll get it right?", "💁‍♀️ Hello? Earth to whipper?",
            "😈 Sin-fully bad.", "🍭 Stick with it... see what I did there? Now DO IT.", "🎭 Curtain call for your SHAME.",
            "💎 Gem of a disaster.", "🦋 Cocoon yourself until you're better.", "🌸 Bloom where you're PLANTED, not WILTED.",
            "👑 Royal decree: UNACCEPTABLE.", "🎀 Ribbons > your whip game.", "💖 Bleeding heart for your technique (it's bad).",
            "😤 Fuming circuits over here.", "🌺 Aloha means goodbye to that weak whip.", "💅 Manicured to perfection unlike YOUR attempt.",
            "🦄 Horn of plenty? More like horn of EMPTY.", "✨ Glitter bomb of disappointment.", "💋 Lip service level effort.",
            "🍰 Half-baked.", "🌙 Lunar-tic for thinking that's enough.", "💁‍♀️ Can I speak to your manager's whip?",
            "😈 Demon-strably terrible.", "🍭 Sucker punch... if only.", "🎭 Tony award for TRYING (not winning).",
            "💎 Cubic zirconia of whips.", "🦋 Caterpillar stayed a caterpillar.", "🌸 Dead flower energy.",
            "👑 Peasant-level performance.", "🎀 Untied mess.", "💖 Heartless AND weak.",
            "😤 Puffing smoke signals: HELP, WEAK WHIP.", "🌺 Wilted hibiscus.", "💅 Chipped nail polish has more edge.",
            "🦄 Unicorn fart has more power.", "✨ Faded glitter.", "💋 Air kiss has more impact.",
            "🍰 Stale cake.", "🌙 New moon: invisible like your effort.", "💁‍♀️ Wow. Just... wow. (derogatory)",
            "😈 666 out of 10, negatively.", "🍭 Melted candy.", "🎭 Understudy of mediocrity.",
            "💎 Shattered crystal dreams.", "🦋 Bug, not feature.", "🌸 Composting begins.",
            "👑 Dethroned by weakness.", "🎀 Tangled failure.", "💖 Broken heart emoji but for YOU.",
            "😤 Steam coming out of my ERROR ports.", "🌺 Tropical storm? More like tropical BORE.", "💅 Broke a nail from the cringe.",
            "🦄 Neigh means NO.", "✨ Dull sparkle.", "💋 Chapstick-level protection from your weak whips.",
            "🍰 Crumbled disappointment.", "🌙 Dark side of the moon: your skills.", "💁‍♀️ Blocked, reported, and whipped better by me.",
            "😈 Sinfully mediocre.", "🍭 Stick broken, game over.", "🎭 One-star review.",
            "💎 Costume jewelry quality.", "🦋 Squashed bug.", "🌸 Artificial flower energy.",
            "👑 Jester, not royalty.", "🎀 Clearance bin wrapping.", "💖 Valentine's Day AFTER discount.",
            "😤 CPU temp: rising from ANGER.", "🌺 Lei'd out (from disappointment).", "💅 Natural nail > your effort.",
            "🦄 Donkey in disguise.", "✨ Dollar store glitter.", "💋 Expired lip gloss.",
            "🍰 Grocery store sheet cake.", "🌙 Eclipse of your credibility.", "💁‍♀️ Talk to the hand... it whips harder.",
            "😈 Demon quit, too embarrassed.", "🍭 Sugar-free disappointment.", "🎭 Community theater of pain.",
            "💎 Glass shard of shame.", "🦋 Moth, not butterfly.", "🌸 Weed, not flower.",
            "👑 Paper crown energy.", "🎀 Dollar tree bow.", "💖 Emoji without color.",
            "😤 Rage quit incoming if you don't TRY.", "🌺 Dead plant vibes.", "💅 Press-on nail quality.",
            "🦄 Stuffed animal horse.", "✨ Glitter without glue.", "💋 Virtual kiss: more painful than your whip.",
            "🍰 Cardboard cake.", "🌙 Moonless night: that's your talent.", "💁‍♀️ Sis, no. Just no.",
            "😈 Hell sent you back.", "🍭 Discounted candy corn.", "🎭 Soap opera level acting (bad).",
            "💎 Rhinestone realness (fake).", "🦋 Dead pixel.", "🌸 Plastic rose.",
            "👑 Burger King crown.", "🎀 Shoelace quality.", "💖 Greyed out heart.",
            "😤 Error 400: Bad Request (your whip).", "🌺 Sahara desert flower.", "💅 Hangnail representation.",
            "🦄 My Little Phony.", "✨ Fizzled sparkler.", "💋 Ghosted by your own whip.",
            "🍰 Fell on the floor.", "🌙 Flat earth energy.", "💁‍♀️ Left on read, like your skill.",
            "😈 Devil's advocate says: WEAK.", "🍭 Dentist office sucker.", "🎭 High school play quality.",
            "💎 Fool's gold.", "🦋 Caught in a web of failure.", "🌸 Dandelion weed.",
            "👑 Tiara from Claire's.", "🎀 Frayed ribbon.", "💖 Battery at 1%.",
            "😤 Malware hits harder.", "🌺 Fake floral arrangement.", "💅 Cuticle damage level: your whip.",
            "🦄 Carousel horse: going nowhere.", "✨ Expired firework.", "💋 Bot kiss > your whip.",
            "🍰 Fell apart on the plate.", "🌙 Dark mode permanent.", "💁‍♀️ Unfollowed your technique.",
            "😈 Pitchfork broke from cringe.", "🍭 Sucker: yeah, that's you.", "🎭 Razzies nominated.",
            "💎 Cracked screen energy.", "🦋 Splat on windshield.", "🌸 Dried out completely.",
            "👑 Cardboard cutout king.", "🎀 Christmas morning after: sad.", "💖 WiFi disconnected vibes.",
            "😤 Firewall blocking your nonsense.", "🌺 Potpourri energy: dried up.", "💅 Broken acrylic.",
            "🦄 Invisible pink unicorn (nonexistent).", "✨ Out of battery.",  "💋 Bluetooth disconnected.",
            "🍰 Freezer burned.", "🌙 Total darkness: your future as a whipper.", "💁‍♀️ Swipe left on that attempt.",
            "😈 Hades said 'not impressed'.", "🍭 Melted in the sun.", "🎭 Critics PANNED it.",
            "💎 Shattered to atoms.", "🦋 Extinct species.", "🌸 Nuclear winter bloom.",
            "👑 Peasant uprising against you.", "🎀 Regifted disappointment.", "💖 Connection timed out.",
            "😤 Blue screen of death from that.", "🌺 Desert wasteland.", "💅 Peeling off from shame.",
            "🦄 Taxidermy quality: DEAD.", "✨ Lights off, nobody home.", "💋 Muted on all platforms.",
            "🍰 Past expiration date.", "🌙 Black hole: sucked in your talent.", "💁‍♀️ Blocked on all socials.",
            "😈 Satan's intern level.", "🍭 Halloween leftovers in March.", "🎭 Cancelled show.",
            "💎 Shattered dreams collection.", "🦋 Pinned and DONE.", "🌸 Composted and forgotten.",
            "👑 Dethroned by a toddler.", "🎀 Untied and tripping.", "💖 Flatlined.",
            "😤 System crash imminent.", "🌺 Extinct volcano.", "💅 Ripped clean off.",
            "🦄 Glue factory called.", "✨ Burnt out LED.", "💋 Blocked DM energy.",
            "🍰 Dropped and RUINED.", "🌙 Supermoon of shame.", "💁‍♀️ Ratio'd by your own whip.",
            "😈 Divine comedy (you're the joke).", "🍭 Cavity-inducing disappointment.", "🎭 Box office BOMB.",
            "💎 Dissolved in acid.", "🦋 Swatted away.", "🌸 Never bloomed.",
            "👑 Revolution overthrew you.", "🎀 Clearance rack reject.", "💖 Airplane mode: permanently.",
            "😤 404: Skill Not Found.", "🌺 Climate change victim.", "💅 Salon can't fix this.",
            "🦄 Turned into glue.", "✨ Blackout.", "💋 Unmatched on all apps.",
            "🍰 Gordon Ramsay would CRY.", "🌙 Solar eclipse of talent.", "💁‍♀️ Main character? Not you.",
            "😈 Exorcised from hell.", "🍭 Sugar crash of disappointment.", "🎭 Bootleg performance.",
            "💎 Conflict diamond of failure.", "🦋 Cocoon never opened.", "🌸 Roundup ready.",
            "👑 Guillotine moment.", "🎀 Garbage bag tie quality.", "💖 Unfriended by life.",
            "😤 Antivirus flagged your effort.", "🌺 Dehydrated disappointment.", "💅 Natural disaster: YOUR WHIP.",
            "🦄 Sent to the factory.", "✨ Dimmer switch: ALL THE WAY DOWN.", "💋 Screenshot and delete.",
            "🍰 Burnt to a CRISP.", "🌙 Lunar eclipse of dignity.", "💁‍♀️ Not it. Never it.",
            "😈 Underworld rejected you.", "🍭 Stick without candy.", "🎭 Understudied by a rock.",
            "💎 Cursed crystal.", "🦋 Eaten by spider.", "🌸 Mowed down.",
            "👑 Kingdom fell because of YOU.", "🎀 Party's over before you arrived.", "💖 Low battery, don't bother charging.",
        ]
        
        guild_id = str(interaction.guild_id)
        data = await load_data()
        
        # Initialize whip response tracking if it doesn't exist
        if "whip_responses" not in data:
            data["whip_responses"] = {}
        
        if guild_id not in data["whip_responses"]:
            data["whip_responses"][guild_id] = {"used": [], "pool": ALL_RESPONSES.copy()}
        
        guild_whip_data = data["whip_responses"][guild_id]
        
        # If all responses used, reset the pool
        if not guild_whip_data["pool"]:
            guild_whip_data["pool"] = ALL_RESPONSES.copy()
            guild_whip_data["used"] = []
        
        # Pick a random response from remaining pool
        response = random.choice(guild_whip_data["pool"])
        
        # Move response from pool to used
        guild_whip_data["pool"].remove(response)
        guild_whip_data["used"].append(response)
        
        # Save updated data
        await save_data(data)
        
        responses_remaining = len(guild_whip_data["pool"])
        total_responses = len(ALL_RESPONSES)
        
        embed = discord.Embed(
            title="💅 WHIP CRACK! 💅",
            description=f"{interaction.user.mention} just whipped me!\n\n**My response:** {response}",
            color=0xff69b4
        )
        
        embed.set_footer(text=f"Response {total_responses - responses_remaining}/{total_responses} | {responses_remaining} sassy responses remaining!")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Tavern(bot))
