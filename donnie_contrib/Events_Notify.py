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

# Global variables to control notification timing and frequency
NOTIFICATION_TIMINGS = [24, 12]  # Send notifications 24 hours and 12 hours before the event
CHECK_INTERVAL = 60  # How often to check for upcoming events (in minutes)

# Store event data, including the image URL, in a dictionary
event_data_store = {}

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


# Modal for event creation
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

        try:
            # Parse and localize the user's input time (e.g., US/Eastern)
            local_start_time = local_tz.localize(datetime.strptime(self.start_time.value, "%Y-%m-%d %H:%M"))
            local_end_time = local_tz.localize(datetime.strptime(self.end_time.value, "%Y-%m-%d %H:%M"))

            # Ensure the start time is in the future
            if local_start_time < datetime.now(local_tz):
                await interaction.followup.send("❌ The start time cannot be in the past.", ephemeral=True)
                return

            # Convert the start and end times to UTC for the Discord API
            start_time_utc = local_start_time.astimezone(timezone('UTC')).isoformat()
            end_time_utc = local_end_time.astimezone(timezone('UTC')).isoformat()

        except ValueError:
            await interaction.followup.send("❌ Invalid date format. Please use 'YYYY-MM-DD HH:MM'.", ephemeral=True)
            return

        discord_events = DiscordEvents()

        # Send the event creation request to the API with UTC times
        result = await discord_events.create_guild_event(
            guild_id=interaction.guild_id,
            event_name=self.event_name.value,
            start_time=start_time_utc,  # Use UTC times
            end_time=end_time_utc,  # Use UTC times
            location=self.location.value,
            description=self.description.value or "No description provided."
        )

        # Store the event information temporarily, we'll add the image URL later
        event_data_store[interaction.id] = {
            "event_name": self.event_name.value,
            "start_time": start_time_utc,
            "location": self.location.value,
            "description": self.description.value or "No description provided.",
            "image_url": None  # Will be updated later
        }

        await interaction.followup.send(result, ephemeral=True)

        # Ask the user for an image URL after the event is created (ephemeral follow-up)
        await interaction.followup.send("Event created! If you'd like to attach an image, please click the button below.", ephemeral=True, view=ImageInputView(interaction.id))


# View for adding image button
class ImageInputView(discord.ui.View):
    def __init__(self, interaction_id):
        super().__init__()
        self.interaction_id = interaction_id

    @discord.ui.button(label="Add Image", style=discord.ButtonStyle.primary)
    async def add_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ImageModal(self.interaction_id))


# Modal for image submission
class ImageModal(discord.ui.Modal, title="Attach Image URL"):
    def __init__(self, interaction_id):
        super().__init__()
        self.interaction_id = interaction_id

    image_url = discord.ui.TextInput(
        label="Image URL",
        placeholder="Enter a valid image URL",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Handle the image URL submission
        image_url = self.image_url.value

        if image_url.startswith('http'):
            # Update the event's image URL in the data store
            event_data_store[self.interaction_id]["image_url"] = image_url
            await interaction.response.send_message(f"✅ Image URL added: {image_url}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Invalid URL format.", ephemeral=True)


# Class for handling Discord events
class DiscordEvents:
    def __init__(self):
        self.base_api_url = 'https://discord.com/api/v10'
        self.session = aiohttp.ClientSession()
        self.headers = {
            'Authorization': f'Bot {TOKEN}',
            'Content-Type': 'application/json'
        }

    async def create_guild_event(self, guild_id: int, event_name: str, start_time: str, end_time: str, location: str, description: str):
        event_data = {
            "name": event_name,
            "scheduled_start_time": start_time,  # Already in UTC format
            "scheduled_end_time": end_time,  # Already in UTC format
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


@tasks.loop(minutes=CHECK_INTERVAL)  # Use global check interval
async def notification_task():
    discord_events = DiscordEvents()
    now = datetime.utcnow().replace(tzinfo=timezone('UTC'))  # Make 'now' timezone-aware

    events = await discord_events.get_guild_events(GUILD_ID)
    for event in events:
        start_time = parser.parse(event['scheduled_start_time'])
        time_until_event = start_time - now

        # Check if the event has already occurred, and if so, remove it from the event data store
        if time_until_event <= timedelta(0):
            # If the event is in the past, remove it from the store
            event_data_store.pop(event['id'], None)  # Use pop to safely remove without KeyError
            continue  # Skip notifications for past events

        for hours in NOTIFICATION_TIMINGS:  # Use global notification timings
            if timedelta(hours=hours) >= time_until_event > timedelta(hours=hours-1):
                channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
                if channel:
                    # Get event data by matching event ID
                    event_info = event_data_store.get(event['id'])
                    if event_info:
                        embed = discord.Embed(title=f"⏰ Reminder: {event_info['event_name']}", description="Event is coming soon!", color=0x00ff00)
                        embed.add_field(name="Location", value=event_info['location'], inline=False)
                        embed.add_field(name="Description", value=event_info['description'], inline=False)
                        
                        # Add image URL if available
                        if event_info["image_url"]:
                            embed.set_image(url=event_info["image_url"])
                        
                        await channel.send(embed=embed)

    await discord_events.close()


@bot.tree.command(name="update_notifications", description="Update notification times and check frequency")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def update_notifications(interaction: discord.Interaction, timings: str, interval: int):
    # Authorized users only
    if any(role.id in ALLOWED_ROLES_DICT.values() for role in interaction.user.roles):
        global NOTIFICATION_TIMINGS, CHECK_INTERVAL
        try:
            NOTIFICATION_TIMINGS = [int(t) for t in timings.split(',')]
            CHECK_INTERVAL = interval
            notification_task.change_interval(minutes=CHECK_INTERVAL)
            await interaction.response.send_message(f"✅ Notification times updated to {NOTIFICATION_TIMINGS} hours, and check interval set to {CHECK_INTERVAL} minutes.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Invalid format. Use comma-separated values for timings and a number for the interval.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ You don't have permission to update the notifications.", ephemeral=True)


@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    guild = discord.Object(id=GUILD_ID)

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
    if any(role.id in ALLOWED_ROLES_DICT.values() for role in interaction.user.roles):
        await interaction.response.send_modal(EventModal())
    else:
        await interaction.response.send_message("❌ You don't have permission to create events.", ephemeral=True)


# Run the bot
bot.run(TOKEN)
