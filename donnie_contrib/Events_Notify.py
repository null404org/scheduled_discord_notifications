import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import os
import aiohttp
from datetime import datetime, timedelta
from dateutil import parser
from pytz import timezone

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
NOTIFICATION_CHANNEL_ID = int(os.getenv('NOTIFICATION_CHANNEL_ID'))

# Parse ALLOWED_ROLES into a dictionary
allowed_roles_str = os.getenv('ALLOWED_ROLES')
ALLOWED_ROLES_DICT = {name: int(role_id) for name, role_id in (item.split('=') for item in allowed_roles_str.split(','))}

# Adjust Local Time Zone to your own (e.g., 'US/Eastern')
local_tz = timezone('US/Eastern')

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class EventModal(discord.ui.Modal, title="Create a New Event"):
    event_name = discord.ui.TextInput(
        label="Event Name",
        placeholder="Enter the event name",
        max_length=100,
        required=True
    )
    start_time = discord.ui.TextInput(
        label="Start Time",
        placeholder="YYYY-MM-DD HH:MM (24h format)",
        required=True
    )
    end_time = discord.ui.TextInput(
        label="End Time",
        placeholder="YYYY-MM-DD HH:MM (24h format)",
        required=True
    )
    location = discord.ui.TextInput(
        label="Location",
        placeholder="Enter the event location",
        required=True
    )
    description = discord.ui.TextInput(
        label="Description",
        placeholder="Enter a brief description of the event",
        style=discord.TextStyle.long,
        max_length=500,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        discord_events = DiscordEvents()
        result = await discord_events.create_guild_event(
            guild_id=interaction.guild_id,
            event_name=self.event_name.value,
            start_time=self.start_time.value,
            end_time=self.end_time.value,
            location=self.location.value,
            description=self.description.value or "No description provided."
        )
        await interaction.followup.send(result, ephemeral=True)
        await discord_events.close()

class DiscordEvents:
    def __init__(self):
        self.base_api_url = 'https://discord.com/api/v10'
        self.session = aiohttp.ClientSession()
        self.headers = {
            'Authorization': f'Bot {TOKEN}',
            'Content-Type': 'application/json'
        }

    def format_datetime(self, date_str: str) -> str:
        try:
            local_time = local_tz.localize(datetime.strptime(date_str, "%Y-%m-%d %H:%M"))
            return local_time.astimezone(timezone('UTC')).isoformat()
        except ValueError:
            raise ValueError(
                f"Invalid date format: '{date_str}'. Please use 'YYYY-MM-DD HH:MM' format."
            )

    async def create_guild_event(self, guild_id: int, event_name: str, start_time: str, end_time: str, location: str, description: str):
        try:
            start_iso = self.format_datetime(start_time)
            end_iso = self.format_datetime(end_time)
        except ValueError as e:
            return str(e)

        event_data = {
            "name": event_name,
            "scheduled_start_time": start_iso,
            "scheduled_end_time": end_iso,
            "privacy_level": 2,  # GUILD_ONLY
            "entity_type": 3,    # EXTERNAL
            "entity_metadata": {
                "location": location
            },
            "description": description
        }

        url = f"{self.base_api_url}/guilds/{guild_id}/scheduled-events"

        async with self.session.post(url, headers=self.headers, json=event_data) as response:
            if 200 <= response.status < 300:
                event = await response.json()
                return f"✅ Event '{event_name}' created successfully!"
            else:
                error = await response.json()
                return f"❌ Failed to create event: {error.get('message', 'Unknown error')}"

    async def get_guild_events(self, guild_id: int):
        url = f"{self.base_api_url}/guilds/{guild_id}/scheduled-events"
        async with self.session.get(url, headers=self.headers) as response:
            if 200 <= response.status < 300:
                return await response.json()
            else:
                return []

    async def close(self):
        await self.session.close()

@tasks.loop(minutes=1) #modify to check less often to preserve resources/ rate limits (e.g. minutes=60)
async def notification_task():
    discord_events = DiscordEvents()
    now = datetime.utcnow().replace(tzinfo=timezone('UTC'))  # Make 'now' timezone-aware

    events = await discord_events.get_guild_events(GUILD_ID)
    for event in events:
        # Parse the event start time, which includes timezone info
        start_time = parser.parse(event['scheduled_start_time'])
        time_until_event = start_time - now

        if time_until_event <= timedelta(hours=24) and time_until_event > timedelta(hours=23, minutes=59):
            # 24 hours prior notification
            channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
            if channel:
                await channel.send(f"⏰ Reminder: The event '{event['name']}' is starting in 24 hours!")

        elif time_until_event <= timedelta(hours=12) and time_until_event > timedelta(hours=11, minutes=59):
            # 12 hours prior notification
            channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
            if channel:
                await channel.send(f"⏰ Reminder: The event '{event['name']}' is starting in 12 hours!")

    await discord_events.close()

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')

    guild = discord.Object(id=GUILD_ID)

    # Sync the new command for the guild
    try:
        print("Syncing commands...")
        await bot.tree.sync(guild=guild)
        print("Commands synced successfully.")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    notification_task.start()  # Start the notification task

@bot.tree.command(name="events", description="Create a new scheduled event")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def create_event(interaction: discord.Interaction):
    # Check if the user has one of the allowed roles by ID
    if any(role.id in ALLOWED_ROLES_DICT.values() for role in interaction.user.roles):
        await interaction.response.send_modal(EventModal())
    else:
        await interaction.response.send_message("❌ You don't have permission to create events.", ephemeral=True)

# Run the bot
bot.run(TOKEN)
