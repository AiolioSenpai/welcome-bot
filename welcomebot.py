import discord
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))
ROLE_NAME = os.getenv("ROLE_NAME")

intents = discord.Intents.default()
intents.members = True  # Required for on_member_join
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_member_join(member):
    guild = client.get_guild(GUILD_ID)
    welcome_channel = guild.get_channel(WELCOME_CHANNEL_ID)

    # ✅ 1. Send welcome message in channel
    if welcome_channel:
        embed = discord.Embed(
            title="🎉  Welcome new Lord! 🎉 ",
            description=f"Welcome to Regal Pride, {member.mention}! Feel free to introduce yourself.",
            color=discord.Color.green()
        )
        embed.set_image(url="https://tenor.com/fr/view/dumbledore-cheers-harry-potter-gif-23948582")  
        await welcome_channel.send(embed=embed)

    # ✅ 2. DM the rules/guide
    try:
        rules_message = (
            f"👋 Welcome to RPG's server, {member.name}!\n\n"
            "I hope you like it here\n"
            "Here are the rules:\n"
            "1️⃣ Be respectful\n"
            "2️⃣ No Harressment or bad behaviour is tolerated\n"
            "3️⃣ Have fun!\n\n"
            "Check out #next-events to see the upcoming events in KC posted by Hagrid ;)"
        )
        await member.send(rules_message)
    except discord.Forbidden:
        print(f"Could not DM {member.name}.")

    # ✅ 3. Auto-assign role
    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if role:
        try:
            await member.add_roles(role)
            print(f"Assigned role {ROLE_NAME} to {member.name}.")
        except discord.Forbidden:
            print(f"Missing permissions to assign role to {member.name}.")
    else:
        print(f"Role '{ROLE_NAME}' not found in the server.")

client.run(TOKEN)
