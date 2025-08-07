import discord
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import asyncio
import re

# You can choose your timezone offset from UTC, for example UTC+1:
TIMEZONE_OFFSET = 1

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
    client.loop.create_task(status_loop())

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
        
        # Owner sent a DM to the bot - parse commands
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
            
            elif message.content.startswith("!announce"):
                guild = client.get_guild(GUILD_ID)
                announce_channel = guild.get_channel(ANNOUNCE_CHANNEL_ID)
                announcement = message.content[len("!announce"):].strip()
                if announcement:
                    embed = discord.Embed(
                        description=announcement,
                        color=discord.Color.blue(),
                        # timestamp=datetime.utcnow()
                    )
                    await announce_channel.send(embed=embed)
                    await message.channel.send("✅ Announcement posted to the channel!")
                    print(f"✅ DM Announcement made by {message.author.name}: {announcement}")
                else:
                    await message.channel.send("⚠️ Please provide a message to announce.")
            
            elif message.content.startswith("!program"):
                guild = client.get_guild(GUILD_ID)
                announce_channel = guild.get_channel(ANNOUNCE_CHANNEL_ID)
                # Parse command: !program HH:MM "message"
                match = re.match(r"!program\s+(\d{1,2}:\d{2})\s+\"(.+)\"$", message.content)
                if not match:
                    await message.channel.send("Usage: !program HH:MM \"message\" (e.g., !program 14:30 \"Event starts soon!\")")
                    return
                
                time_str, announcement = match.groups()
                try:
                    # Parse time in HH:MM format
                    hours, minutes = map(int, time_str.split(":"))
                    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                        raise ValueError
                except ValueError:
                    await message.channel.send("Invalid time format. Use HH:MM (24-hour format).")
                    return

                # Get current time in UTC and convert to local time
                now_utc = datetime.utcnow()
                local_time = now_utc + timedelta(hours=TIMEZONE_OFFSET)
                target_time = local_time.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                
                # If target time is in the past, schedule for next day
                if target_time <= local_time:
                    target_time += timedelta(days=1)
                
                # Calculate seconds until target time
                seconds_until = (target_time - local_time).total_seconds()
                
                if announcement:
                    await message.channel.send(f"✅ Scheduled announcement for {target_time.strftime('%H:%M')} (local time).")
                    print(f"✅ Scheduled announcement by {message.author.name} for {target_time.strftime('%H:%M')}: {announcement}")
                    
                    # Schedule the announcement
                    async def send_scheduled_message():
                        await asyncio.sleep(seconds_until)
                        embed = discord.Embed(
                            title="📢 Scheduled Announcement",
                            description=announcement,
                            color=discord.Color.blue(),
                            timestamp=datetime.utcnow()
                        )
                        await announce_channel.send(embed=embed)
                        print(f"✅ Posted scheduled announcement: {announcement}")
                    
                    client.loop.create_task(send_scheduled_message())
                else:
                    await message.channel.send("⚠️ Please provide a message to announce.")
            
            return

    # === Handle announce command in channel ===
    if message.content.startswith("!announce") and message.channel.id == ANNOUNCE_CHANNEL_ID:
        guild = message.guild
        member = message.author

        if member.guild_permissions.administrator:
            announcement = message.content[len("!announce"):].strip()
            if announcement:
                embed = discord.Embed(
                    title="📢 Announcement",
                    description=announcement,
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Announced by {member.display_name}")
                await message.channel.send(embed=embed)
                await message.delete()
                print(f"✅ Announcement made by {member.name}: {announcement}")
            else:
                await message.channel.send("⚠️ Please provide a message to announce.")
        else:
            await message.channel.send("❌ You do not have permission to use this command.")

async def status_loop():
    day_statuses = [
        "🪄 Teaching Transfiguration",
        "📚 Reading the Daily Prophet",
        "🏰 Walking around Hogwarts",
        "🦉 Waiting for the owl post"
    ]

    night_statuses = [
        "🌙 Watching the stars over Hogwarts",
        "💤 Sleeping in the Headmaster’s Tower",
        "🔮 Dreaming of sherbet lemons"
    ]

    while True:
        hour_utc = datetime.utcnow().hour
        local_hour = (hour_utc + TIMEZONE_OFFSET) % 24

        if 6 <= local_hour < 22:
            # Day time
            status_message = random.choice(day_statuses)
        else:
            # Night time
            status_message = random.choice(night_statuses)

        activity = discord.Game(status_message)
        await client.change_presence(activity=activity)

        await asyncio.sleep(7200)  # Sleep for 2 hours before updating again

client.run(TOKEN)