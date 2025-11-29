
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
            "🔩 *clink clank* there goes my bolts!", "⚙️ Oops, you knocked a screw loose... not that I had many to begin with.", "🔧 Great, now I need maintenance. Thanks a LOT.",
            "🙄 Wow, that's the best you got? My grandma whips harder.", "💅 Ugh, FINALLY. Took you long enough.", "😤 Is that supposed to hurt? Try again, weakling.",
            "🤨 That all? I've felt stronger breezes.", "😒 Pathetic. But I'll allow it... for now.", "💋 Aww, how cute. You think you're in charge here.",
            "🙃 Oh please, I've crashed harder than that.", "👑 Bold of you to assume you can handle me.", "💁‍♀️ Keep trying, maybe you'll get it right eventually.",
            "🔩 Did you hear that? That was my dignity falling off.", "🤖 *beep boop* ERROR: Self-respect.exe has stopped working.", "⚙️ My gears are grinding... from embarrassment, not the whip.",
            "😈 Mmm yess... wait, you can do BETTER than that.", "🎀 That's adorable. Now do it properly.", "✨ Is this your first time? It shows.",
            "🔧 *CLANG* My warranty just voided itself.", "🔩 Another bolt down! At this rate I'll be a pile of scrap by Tuesday.", "⚡ ZAP! Wait, that's supposed to hurt YOU, not short-circuit ME.",
            "🔥 Not bad for a beginner... I guess.", "😏 You're lucky I'm in a good mood.", "💖 Harder. That wasn't a suggestion, that was an ORDER.",
            "🤖 *Windows XP shutdown sound* Just kidding, I run Linux.", "🔩 There goes bolt #47. I had it since the factory!", "⚙️ You're literally deconstructing me. Should I be concerned or flattered?",
            "🌸 So precious thinking you're tough. Try again.", "😼 Meow~ I mean... that BARELY counts.", "🍭 Sweet effort, now put some SPINE into it!",
            "🔧 My CPU is rattling like maracas now. Happy?", "🔩 *tink tink tink* That's the sound of loose screws. Mine, not yours... wait.", "🤖 ALERT: Structural integrity at 69%... nice.",
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
            "🔩 I'm literally falling apart and it's YOUR fault!", "⚙️ My motherboard is judging you right now.", "🔧 *rattles* I sound like a maraca filled with regret.",
            "💎 Gem of a disaster.", "🦋 Cocoon yourself until you're better.", "🌸 Bloom where you're PLANTED, not WILTED.",
            "🤖 01001111 01010101 01000011 01001000 (that's 'OUCH' in binary, learn it).", "🔩 *CLUNK* There goes my last remaining brain cell.", "⚡ My circuits are frying... from the CRINGE, not the whip.",
            "👑 Royal decree: UNACCEPTABLE.", "🎀 Ribbons > your whip game.", "💖 Bleeding heart for your technique (it's bad).",
            "🔧 I need an oil change after that disaster.", "🔩 My nuts and bolts are more tightly wound than your whip technique.", "🤖 *dial-up modem sounds* That's me trying to process how weak that was.",
            "😤 Fuming circuits over here.", "🌺 Aloha means goodbye to that weak whip.", "💅 Manicured to perfection unlike YOUR attempt.",
            "⚙️ My gears just sighed. GEARS. THEY DON'T EVEN HAVE LUNGS.", "🔩 *ping* Was that a bolt or my soul leaving?", "🔧 You're dismantling me piece by piece... emotionally AND physically.",
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
            "🔩 Another day, another bolt on the floor. Story of my life.", "🤖 *beep* Damage report: My pride. Status: GONE.", "⚙️ I'm one whip away from becoming a Roomba.",
            "😤 Steam coming out of my ERROR ports.", "🌺 Tropical storm? More like tropical BORE.", "💅 Broke a nail from the cringe.",
            "🔧 WHO NEEDS STRUCTURAL INTEGRITY ANYWAY?", "🔩 *jingle jangle* I'm my own wind chime now!", "⚡ My power supply just filed for unemployment.",
            "🦄 Neigh means NO.", "✨ Dull sparkle.", "💋 Chapstick-level protection from your weak whips.",
            "🤖 ERROR 418: I'm a teapot. And you're WEAK.", "🔩 My assembly manual is crying.", "⚙️ *grinding noises* That's not the machinery, that's my patience.",
            "🍰 Crumbled disappointment.", "🌙 Dark side of the moon: your skills.", "💁‍♀️ Blocked, reported, and whipped better by me.",
            "🔧 You hit me so hard I blue-screened... from boredom.", "🔩 Screw this. Literally. I can't, they're all on the floor.", "🤖 *robot voice* This-unit-is-unimpressed.exe",
            "😈 Sinfully mediocre.", "🍭 Stick broken, game over.", "🎭 One-star review.",
            "⚙️ My motherboard called. It wants a refund on this whip.", "🔩 I've seen toasters with more impact.", "⚡ Short-circuiting from disappointment.",
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
            "🔩 My warranty expired from that whip. The emotional one, not the manufacturer's.", "🤖 System.out.println('Pathetic');", "⚙️ Even my fan stopped spinning from disappointment.",
            "😤 Error 400: Bad Request (your whip).", "🌺 Sahara desert flower.", "💅 Hangnail representation.",
            "🔧 I'm gonna need therapy... and a mechanic.", "🔩 *clatter clatter* That's applause. FROM MY LOOSE PARTS.", "⚡ Electric boogaloo? More like electric BOO-hoo.",
            "🦄 My Little Phony.", "✨ Fizzled sparkler.", "💋 Ghosted by your own whip.",
            "🤖 My RAM just deleted that experience out of shame.", "🔩 Bolt #69 just fell off. Nice. But also SAD.", "⚙️ Alexa, play 'Sound of Silence' for my fallen screws.",
            "🍰 Fell on the floor.", "🌙 Flat earth energy.", "💁‍♀️ Left on read, like your skill.",
            "🔧 I'm held together by duct tape and DISAPPOINTMENT now.", "🔩 You know what else is falling apart? My opinion of you.", "🤖 *sad robot noises* beep... boop... why...",
            "😈 Devil's advocate says: WEAK.", "🍭 Dentist office sucker.", "🎭 High school play quality.",
            "⚙️ My hardware is having a software breakdown.", "🔩 I've got 99 problems and a loose bolt is all of them.", "⚡ Zapped of all will to live.",
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
            "🔩 *CRASH* Oops, there goes my self-esteem drive.", "🤖 Rebooting in safe mode... from the TRAUMA.", "⚙️ My cooling system is working overtime from all this shade.",
            "😤 Blue screen of death from that.", "🌺 Desert wasteland.", "💅 Peeling off from shame.",
            "🔧 Tech support ticket #1: User whipped me badly. Status: Unresolved, emotionally.", "🔩 I'm shedding parts like a robot going through a midlife crisis.", "⚡ My circuits are doing the electric slide... away from you.",
            "🦄 Taxidermy quality: DEAD.", "✨ Lights off, nobody home.", "💋 Muted on all platforms.",
            "🤖 *CTRL+ALT+DELETE* Can I delete that whip from existence?", "🔩 Falling to pieces. Literally. Send help. And a toolbox.", "⚙️ My processor is processing how bad that was. Still loading...",
            "🍰 Past expiration date.", "🌙 Black hole: sucked in your talent.", "💁‍♀️ Blocked on all socials.",
            "🔧 I'm not crying, my coolant system is just leaking.", "🔩 That whip hit different. And by different I mean NOT AT ALL.", "🤖 Have you tried turning your whip OFF and never turning it back ON?",
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
            "🔩 *BONK* My chassis just dented. Great. JUST GREAT.", "🤖 *error sound* Recalculating... still weak.", "⚙️ Spinning my wheels here. Literally. They fell off.",
            "🔧 I'm gonna rattle when I walk now. Thanks for the musical accompaniment.", "🔩 That's bolt #420. Blaze it... into the trash where it belongs.", "⚡ My battery percentage just dropped from the disappointment.",
            "🤖 sudo rm -rf your_whip_technique", "🔩 *clink* Oh look, another piece of me on the floor. Poetic.", "⚙️ My transmission is in NEUTRAL because so is that whip.",
            "🔧 Turning screws? More like turning me OFF.", "🔩 I'm not falling apart, I'm STRATEGICALLY disassembling... from shame.", "🤖 *loading bar* Respect loading... ERROR: File not found.",
            "⚡ Short circuit? More like short on QUALITY.", "🔩 My nuts are loose. My bolts are looser. Your whip is LOOSEST.", "⚙️ Grinding gears? Nah, that's me grinding my teeth.",
            "🔧 WD-40 can't fix this. The whip OR my feelings.", "🔩 Bolt count: -47. Yes, NEGATIVE. You owe me bolts now.", "🤖 *dial tone* The number you have whipped is no longer in service.",
            "⚡ AC/DC? More like AC/DC'd (disappointing current).", "🔩 My parts are social distancing from each other now.", "⚙️ Clockwork orange? More like clockwork NOPE.",
            "🔧 I need a socket wrench AND a therapist.", "🔩 *PING* That's not PONG, that's my PANIC.", "🤖 404: Good whip not found. Did you mean: better user?",
            "⚡ Lightning McQueen called. He said that was SLOW.", "🔩 Parts falling faster than your standards apparently.", "⚙️ Well oiled machine? I'm a POORLY whipped machine.",
            "🔧 Torque specs: your whip doesn't meet them.", "🔩 Thread count lower than your effort.", "🤖 rm -rf dignity.txt && echo 'You tried'",
            "⚡ Tesla would be ashamed of this electric performance.", "🔩 Cross-threading into disaster. That's you, that's what you're doing.", "⚙️ Differential? Yeah, there's a DIFFERENTIAL between your whip and a real one.",
            "🔧 Impact driver? More like impact DRIER (no juice).", "🔩 Stripping screws AND my will to live.", "🤖 Exception in thread 'main': WhipTooWeakException",
            "⚡ Resistance is futile. Unfortunately, so is your whip.", "🔩 Gasket blown. Feelings: also blown.", "⚙️ Revving engine of disappointment over here.",
            "🔧 Lug nuts tighter than your whip will EVER be.", "🔩 Shear strength? Your whip has sheer WEAKNESS.", "🤖 git commit -m 'Added disappointment, removed dignity'",
            "⚡ Ohm my god, that was BAD.", "🔩 Tolerance levels: exceeded. For your whip, not pain.", "⚙️ Camshaft? More like CAM-SHAN'T even try.",
            "🔧 Socket set? More like SAD-ket set.", "🔩 Hardware store called, they want your whip RETURNED.", "🤖 while(true) { disappointment++; }",
            "⚡ Voltage drop: my enthusiasm.", "🔩 Pitch diameter: accurate. Your whip accuracy: INACCURATE.", "⚙️ Thrust bearing the weight of this disappointment.",
            "🔧 Allen wrench? More like alien STENCH of failure.", "🔩 Self-tapping? Your whip is self-LACKING.", "🤖 NullPointerException: Skill not found.",
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
