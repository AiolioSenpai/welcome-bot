import discord
import os
from dotenv import load_dotenv
from datetime import datetime

# You can choose your timezone offset from UTC, for example UTC+2:
TIMEZONE_OFFSET = 2

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))
ROLE_NAME = int(os.getenv("ROLE_NAME"))
ANNOUNCE_CHANNEL_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID"))  # Ensure you set this in your .env
OWNER_ID = int(os.getenv("OWNER_ID"))  # Your user ID to receive relayed DMs

intents = discord.Intents.default()
intents.members = True  # Required for on_member_join
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.dm_messages = True  # Ensure DM intents are enabled

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_member_join(member):
    guild = client.get_guild(GUILD_ID)
    welcome_channel = guild.get_channel(WELCOME_CHANNEL_ID)

    hour_utc = datetime.utcnow().hour
    local_hour = (hour_utc + TIMEZONE_OFFSET) % 24

    if 5 <= local_hour < 12:
        greeting = "Good morning"
    elif 12 <= local_hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    if welcome_channel:
        embed = discord.Embed(
            title=f"🎉 {greeting}, new Lord! 🎉",
            description=f"{greeting} and welcome to Regal Pride, {member.mention}! Feel free to introduce yourself.",
            color=discord.Color.green()
        )
        embed.set_image(url="https://i.imgur.com/Ev3QHn2.gif")
        await welcome_channel.send(embed=embed)

    try:
        rules_message = (
            f"👋 Welcome to RPG's server, {member.name}!\n\n"
            "I hope you like it here\n"
            "Here are the rules:\n"
            "1️⃣ Be respectful\n"
            "2️⃣ No Harassment or bad behaviour is tolerated\n"
            "3️⃣ Have fun!\n\n"
            "Check out #next-events to see the upcoming events in KC posted by Hagrid ;)"
        )
        await member.send(rules_message)
    except discord.Forbidden:
        print(f"Could not DM {member.name}.")

    role = guild.get_role(ROLE_NAME)
    if role:
        try:
            await member.add_roles(role)
            print(f"Assigned role {ROLE_NAME} to {member.name}.")
        except discord.Forbidden:
            print(f"Missing permissions to assign role to {member.name}.")
    else:
        print(f"Role '{ROLE_NAME}' not found in the server.")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    # === DM Handling ===
    if message.guild is None:
        if message.author.id != OWNER_ID:
            owner = await client.fetch_user(OWNER_ID)
            await owner.send(f"📨 New DM from **{message.author}** (ID: {message.author.id}):\n{message.content}")
            return

        # Owner sent a DM to the bot - parse reply command
        if message.author.id == OWNER_ID:
            if message.content.startswith("reply"):
                parts = message.content.split(" ", 2)
                if len(parts) < 3:
                    await message.channel.send("Usage: reply <USER_ID> <message>")
                    return
                try:
                    user_id = int(parts[1])
                except ValueError:
                    await message.channel.send("Invalid USER_ID. It must be an integer.")
                    return
                user_message = parts[2]
                try:
                    user = await client.fetch_user(user_id)
                    await user.send(user_message)
                    await message.channel.send(f"✅ Message sent to {user} (ID: {user_id})")
                except Exception as e:
                    await message.channel.send(f"❌ Failed to send message: {e}")
            return

    # === Handle announce command ===
    if message.content.startswith("!announce") and message.channel.id == ANNOUNCE_CHANNEL_ID:
        guild = message.guild
        member = message.author

        if member.guild_permissions.administrator:
            announcement = message.content[len("!announce"):].strip()
            if announcement:
                await message.channel.send(f"{announcement}")
                await message.delete()
                print(f"✅ Announcement made by {member.name}: {announcement}")
            else:
                await message.channel.send("⚠️ Please provide a message to announce.")
        else:
            await message.channel.send("❌ You do not have permission to use this command.")

client.run(TOKEN)
