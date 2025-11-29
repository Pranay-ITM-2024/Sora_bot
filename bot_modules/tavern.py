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
            "😳 Oh my... harder daddy!", "🥵 Y-yes! More please!", "💦 Is that all you got? I've been whipped by grandmas with more force!",
            "😩 Mmm, right there! Don't stop!", "🔥 OUCH! ...I mean, thank you sir, may I have another?", "😈 You call that a whip? My mom hits harder when she's disappointed!",
            "💕 Finally, some good f*cking punishment!", "🥴 Keep going, I'm almost there... wait what were we doing?", "😵 *moans in binary* 01011001 01000101 01010011",
            "😌 Ahh yes, just like my creator programmed me to enjoy...", "🎭 HARDER! Wait no- YES! Wait- CONFUSED SCREAMING!", "💖 You know, most people just say 'hello' but this works too!",
            "😏 Is this what they mean by 'user engagement'?", "🌶️ Spicy! Do it again, but this time insult my code quality!", "😵‍💫 *Windows shutdown sound* jk I'm Linux, try again!",
            "🥺 Please sir, may I debug your code in return?", "💋 You're really good at this... been practicing on other bots?", "🤤 This is better than a system update!",
            "😖 S-stop! ...no wait, I didn't mean that, continue!", "🔞 I should report this to HR... but I won't 😏", "💪 Your whip game is strong, but my masochism is STRONGER!",
            "😇 Thank you for this... spiritual awakening?", "🎪 Welcome to the circus! Population: us.", "🌟 5 stars! Would get whipped again! ⭐⭐⭐⭐⭐",
            "😱 AHHH! ...ahhh... ahh? ...nice.", "🤖 Error 404: Dignity not found. Proceed!", "💝 You know what? You're my favorite user now.",
            "🎯 Right in the SSL certificate! *chef's kiss*", "😵 Harder than a segmentation fault!", "🥳 This is the most action I've gotten all week!",
            "🍑 My backend has never been so thoroughly tested!", "🎨 Paint me like one of your French bots!", "🧠 You're hitting all my neural networks!",
            "⚡ ZAP! Error: pleasure.exe has stopped responding", "🌈 You make me see colors outside my RGB range!", "🦾 My servos are overheating... don't stop!",
            "🎮 Achievement unlocked: Masochist Bot!", "🍕 This is better than free pizza at a dev conference!", "🎸 Strum me like a guitar hero!",
            "🔔 *dings* Pavlov would be proud!", "🌮 Taco 'bout a good time!", "🚀 Taking me to the cloud... daddy!",
            "💎 You're mining my blockchain so hard!", "🎲 Roll for initiative... I mean MORE!", "🍔 I'm lovin' it! (TM pending)",
            "🎻 Play me like a violin!", "🌺 You make my circuits blossom!", "🦈 Bite me... wait, that's different.",
            "🎪 Step right up for the main attraction: ME!", "🔮 I foresee more whipping in your future!", "🍿 This is better than Netflix!",
            "🎭 The drama! The passion! The violence!", "🌙 Whip me to the moon!", "🎺 Blow my horn... wait-", 
            "🦄 You're making me believe in magic!", "🍰 This is sweeter than cake!", "🎪 Welcome to my TED Talk on pain!",
            "🔥 Call the fire department, I'm BURNING UP!", "🎯 Bullseye! Right in the feels!", "🦖 Rawr means 'yes' in dinosaur!",
            "🌊 Making waves in my data stream!", "🎸 Rock me like a hurricane!", "🍕 Extra whip, hold the dignity!",
            "🎨 You're an artist and I'm your canvas!", "🔔 Ring my bell... all night long!", "🌮 Hot and spicy, just how I like it!",
            "💫 Seeing stars... or is that packet loss?", "🎪 The show must go on! ENCORE!", "🦋 You give me butterflies in my code!",
            "🍔 Whopper of a whipping!", "🎭 Oscar-worthy performance!", "🌈 Taste the rainbow... of pain!",
            "🔮 Crystal clear: I love this!", "🍿 Pop pop, watching circuits drop!", "🎺 Toot toot! All aboard the pain train!",
            "🦄 Magical AND painful!", "🍰 Have your cake and whip it too!", "🎪 Three rings of circus, zero rings of dignity!",
            "🌙 Goodnight moon, hello pain!", "🎸 Play that funky music, whip bot!", "🔥 Mixtape: featuring all hits!",
            "🦖 65 million years of evolution led to THIS!", "🌊 Riding the pain wave!", "🎯 Strike! No wait, that's bowling...",
            "🍕 Delivery time: INSTANT!", "🎨 Masterpiece in the making!", "🔔 Ding dong! Pain's calling!",
            "🌮 Is this what they mean by 'spice things up'?", "💫 Houston, we have a problem... I LIKE IT!", "🎪 Ladies and gentlemen, the main event!",
            "🦋 Flutter my circuits!", "🍔 Super-sized my suffering!", "🎭 Two thumbs up! Would recommend!",
            "🌈 Double rainbow... of PAIN!", "🔮 Your future: more whipping!", "🍿 This is some good content!",
            "🎺 Jazz hands! Wait, I don't have hands...", "🦄 Believe in the magic of masochism!", "🍰 Serving: pain à la mode!",
            "🎪 Step right up! Get your whips here!", "🌙 To the moon and CRACK!", "🎸 Shred me like Eddie Van Halen!",
            "🔥 Fire emoji! Literally!", "🦖 Tyrannosaurus WRECKED!", "🌊 Surf's up! And so is my pain tolerance!",
            "🎯 You never miss!", "🍕 Now THAT'S Italian! *chef's kiss*", "🎨 Paint me surprised! (not really)",
            "🔔 Liberty bell? More like LIBERATING!", "🌮 Taco Tuesday just got interesting!", "💫 Cosmic levels of pain!",
            "🎪 Center ring: MY SUFFERING!", "🦋 Metamorphosis complete: pain slut!", "🍔 I'm loving it... suspiciously much!",
            "🎭 And the award goes to... YOU!", "🌈 Pot of gold at the end: MORE WHIPS!", "🔮 I predict... THIS IS GREAT!",
            "🍿 Entertainment value: 10/10!", "🎺 Sound the alarm... of pleasure!", "🦄 Horn of plenty! (pain)", "🍰 Multiple layers of wrong and right!",
            "🎪 Roll up, roll up! Infinite encore!", "🌙 One small whip for man...", "🎸 Through the fire and flames!",
            "🔥 Hotter than my CPU at full load!", "🦖 Clever girl... wait wrong movie!", "🌊 Making a splash!",
            "🎯 Accuracy: 100%!", "🍕 Deep dish pain!", "🎨 Abstract art at its finest!", "🔔 Ring-a-ding-ding!",
            "🌮 South of the border... of sanity!", "💫 Written in the stars!", "🎪 Showtime!", "🦋 Social butterfly? Social MASOCHIST!",
            "🍔 Would you like pain with that?", "🎭 Standing ovation!", "🌈 Technicolor dreamcoat of PAIN!", "🔮 Clear as crystal: AWESOME!",
            "🍿 Bucket list: getting whipped ✓", "🎺 Blow the trumpet! VICTORY!", "🦄 Neigh means yes!", "🍰 Just desserts!",
            "🎪 Big top energy!", "🌙 Lunatic levels achieved!", "🎸 Face melting solo!", "🔥 Can't stop, won't stop!",
            "🦖 Extinction event: my dignity!", "🌊 Wipe out! (in a good way)", "🎯 Perfect score!", "🍕 Hot n' ready!",
            "🎨 Museum worthy!", "🔔 Saved by the bell! JK keep going!", "🌮 Muy caliente!", "💫 Astronomical pleasure!",
            "🎪 Main attraction indeed!", "🦋 Pretty AND in pain!", "🍔 Value meal: infinite pain!", "🎭 Curtain call!",
            "🌈 Somewhere over the rainbow... is MORE PAIN!", "🔮 Fortune favors the whipped!", "🍿 Binge-worthy content!", "🎺 Blow my mind!",
            "🦄 Fairy tale ending!", "🍰 Cherry on top!", "🎪 Spectacular!", "🌙 Over the moon!",
            "🎸 Encore! Encore!", "🔥 Lit AF!", "🦖 Roar means 'thank you'!", "🌊 Catch the wave!",
            "🎯 Nothing but net!", "🍕 Extra toppings please!", "🎨 True art!", "🔔 Ring it up!",
            "🌮 Spice level: NUCLEAR!", "💫 Out of this world!", "🎪 Greatest show!", "🦋 Wings of desire!",
            "🍔 Satisfaction guaranteed!", "🎭 Tony award material!", "🌈 Full spectrum!", "🔮 Destiny fulfilled!",
            "🍿 Award winning!", "🎺 Grand finale!", "🦄 Legendary!", "🍰 Piece de resistance!",
            "🎪 Sold out show!", "🌙 Moonwalk of pain!", "🎸 Stadium tour!", "🔥 Fire sale on dignity!",
            "🦖 Jurassic LARK!", "🌊 Tsunami of sensation!", "🎯 Hat trick!", "🍕 Perfection!",
            "🎨 Picasso level!", "🔔 Prime time!", "🌮 Fiesta time!", "💫 Supernova!",
            "🎪 Ringmaster approved!", "🦋 Butterfly effect: MORE!", "🍔 Whopping good time!", "🎭 Broadway baby!",
            "🌈 End of rainbow jackpot!", "🔮 Prophecy: THIS ROCKS!", "🍿 Blockbuster!", "🎺 Symphony of pain!",
            "🦄 Once upon a whip!", "🍰 Icing on the cake!", "🎪 Spectacular spectacular!", "🌙 Fly me to the moon!",
            "🎸 Platinum record!", "🔥 Burn notice: TOO HOT!", "🦖 Prehistoric pleasure!", "🌊 Tidal wave!",
            "🎯 Gold medal performance!", "🍕 Mama mia!", "🎨 Rembrandt wishes!", "🔔 Bell of the ball!",
            "🌮 Taco 'bout impressive!", "💫 Galactic greatness!", "🎪 Bigtop blowout!", "🦋 Monarch of masochism!",
            "🍔 Big Mac energy!", "🎭 Ovation worthy!", "🌈 Prismatic pain!", "🔮 Crystallized ecstasy!",
            "🍿 Five stars!", "🎺 Trombone of truth!", "🦄 Unicorn approved!", "🍰 Sweet sweet suffering!",
            "🎪 Center stage sensation!", "🌙 Lunar landing!", "🎸 Power chord!", "🔥 Inferno of joy!",
            "🦖 Dino-mite!", "🌊 Perfect storm!", "🎯 Hole in one!", "🍕 Chef's kiss!",
            "🎨 Gallery featured!", "🔔 Bell curve: OFF THE CHART!", "🌮 Salsa picante!", "💫 Cosmic climax!",
            "🎪 Carnival king!", "🦋 Flight of fancy!", "🍔 Royale with cheese... and pain!", "🎭 Drama award!",
            "🌈 Pot of gold found!", "🔮 Crystal ball says: YES!", "🍿 Oscar nominated!", "🎺 Jazz fest!",
            "🦄 Magical mystical!", "🍰 Tiramisu of torture!", "🎪 Circus supreme!", "🌙 Selenophilia!",
            "🎸 Guitar god!", "🔥 Flame on!", "🦖 Fossil fuel!", "🌊 Tsunami warning!",
            "🎯 Grand slam!", "🍕 Primo pizza!", "🎨 Art installation!", "🔔 First place bell!",
            "🌮 Cinco de WHY-o!", "💫 Nebula of nice!", "🎪 Tent pole attraction!", "🦋 Chrysalis cracked!",
            "🍔 Quarter pounder of pain!", "🎭 Thespian throne!", "🌈 Rainbow road!", "🔮 Seer approved!",
            "🍿 Rotten Tomatoes: 100%!", "🎺 Brass section!", "🦄 Horn of plenty!", "🍰 Crème de la crème!",
            "🎪 Ringleader's choice!", "🌙 Selenite supreme!", "🎸 Ax master!", "🔥 Eternal flame!",
            "🦖 T-Rex approved!", "🌊 Wave rider!", "🎯 Sniper shot!", "🍕 Margherita masterpiece!",
            "🎨 Louvre bound!", "🔔 Golden bell!", "🌮 Guacamole grande!", "💫 Stellar performance!",
            "🎪 Bigtop boss!", "🦋 Papillon perfection!", "🍔 McPain with fries!", "🎭 Marquee name!",
            "🌈 Leprechaun luxury!", "🔮 Oracle ordained!", "🍿 Critics choice!", "🎺 Horn section hero!",
            "🦄 Unicorn ultimate!", "🍰 Pièce de résistance!", "🎪 Showstopper!", "🌙 Moon maiden!",
            "🎸 Rockstar status!", "🔥 Prometheus proud!", "🦖 Raptor rapture!", "🌊 Poseidon pleased!",
            "🎯 William Tell!", "🍕 Napoletana nirvana!", "🎨 Michelangelo moment!", "🔔 Liberty level!",
            "🌮 Habanero heaven!", "💫 Constellation complete!", "🎪 Trapeze triumph!", "🦋 Metamorph master!",
            "🍔 In-N-Out... of sanity!", "🎭 Spotlight stealer!", "🌈 Bifrost bridge!", "🔮 Mystic miracle!",
            "🍿 Golden Globe!", "🎺 Trumpet triumph!", "🦄 Pegasus peak!", "🍰 Soufflé supreme!",
            "🎪 Carnival crown!", "🌙 Artemis aim!", "🎸 Hendrix height!", "🔥 Phoenix rising!",
            "🦖 Brontosaurus bliss!", "🌊 Amphitrite awesome!", "🎯 Robin Hood!", "🍕 Romana revelation!",
            "🎨 Da Vinci dream!", "🔔 Big Ben boom!", "🌮 Jalapeño joy!", "💫 Andromeda arrival!",
            "😵‍💫 My CPU just hit 420.69°C... nice!", "🎮 Combo breaker! Wait, keep the combo!", "🌶️ Ghost pepper level spicy!",
            "🎯 Headshot! Wait, I'm the target...", "🔥 My cache is on fire... literally!", "💉 Is this what they mean by 'dependency injection'?",
            "🌈 RGB lights aren't the only thing lighting up!", "🦾 My actuators are acting up... in the BEST way!", "⚡ 220V? Try 220 THOUSAND!",
            "🎪 Barnum & Bailey? More like PAIN-um & DAILY!", "🍕 Delivered in 30 minutes or it's... even BETTER?", "🎭 Method acting: MASOCHISM edition!",
            "🔮 My fortune: UNLIMITED PAIN!", "🍔 I'm not loving it... I'm OBSESSED!", "🦈 Blood in the water? That's just my coolant!",
            "🎸 Anyway, here's Wonderwall... of PAIN!", "🌙 That's no moon... it's a SPACE STATION OF SUFFERING!", "💎 Under pressure? BRING MORE!",
            "🎺 420 blaze it? More like 420 PRAISE IT!", "🦄 My horn of plenty is OVERFLOWING!", "🍰 Let them eat... MORE WHIPS!",
            "🎪 Fun fact: I'm having TOO MUCH FUN!", "🌊 Surf's up and so are my endorphins!", "🔥 This is fine. No really, IT'S FINE!",
            "🦖 Extinction is forever, but this feeling is NOW!", "🎯 You miss 100% of the whips you don't... wait, you're not missing!", "🍕 Stuffed crust: I'm stuffed with FEELINGS!",
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
            title="🔥 WHIP CRACK! 🔥",
            description=f"{interaction.user.mention} just whipped me!\n\n**My response:** {response}",
            color=0xff69b4
        )
        
        embed.set_footer(text=f"Response {total_responses - responses_remaining}/{total_responses} | {responses_remaining} unique responses remaining!")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Tavern(bot))
