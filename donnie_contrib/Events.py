import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import aiohttp
import base64
import asyncio
from datetime import datetime, timedelta
from pytz import timezone

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
NOTIFICATION_CHANNEL_ID = int(os.getenv('NOTIFICATION_CHANNEL_ID'))
BOT_IMAGE_CHANNEL_ID = int(os.getenv('BOT_IMAGE_CHANNEL_ID'))

# Set up bot intents and bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Allowed roles from .env for permissions
allowed_roles_str = os.getenv('ALLOWED_ROLES')
ALLOWED_ROLES_DICT = {name: int(role_id) for name, role_id in (item.split('=') for item in allowed_roles_str.split(','))}

# Define timezone
local_tz = timezone('US/Eastern')
event_data_store = {}  # Store event data, including image URL and notification timers

# Session initialized in on_ready for proper session handling
aiohttp_session = None

# Notification times (in hours before event start)
NOTIFICATION_TIMES = [18, 6]

class DiscordEvents:
    def __init__(self, session):
        self.base_api_url = 'https://discord.com/api/v10'
        self.session = session
        self.headers = {
            'Authorization': f'Bot {TOKEN}',
            'Content-Type': 'application/json'
        }

    async def create_guild_event(self, guild_id, event_name, start_time, end_time, location, description):
        event_data = {
            "name": event_name,
            "scheduled_start_time": start_time,
            "scheduled_end_time": end_time,
            "privacy_level": 2,
            "entity_type": 3,
            "entity_metadata": {"location": location},
            "description": description
        }
        url = f"{self.base_api_url}/guilds/{guild_id}/scheduled-events"
        async with self.session.post(url, headers=self.headers, json=event_data) as response:
            if response.status == 200:
                event = await response.json()
                return event['id'], f"✅ Event '{event_name}' created successfully!"
            else:
                error = await response.json()
                return None, f"❌ Failed to create event: {error.get('message', 'Unknown error')}"

    async def update_event_cover_image(self, guild_id, event_id, image_url):
        try:
            async with self.session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    encoded_image = f"data:image/png;base64,{base64.b64encode(image_data).decode()}"
                else:
                    print(f"Failed to fetch image from URL. HTTP Status: {response.status}")
                    return

            url = f"{self.base_api_url}/guilds/{guild_id}/scheduled-events/{event_id}"
            json_data = {"image": encoded_image}
            async with self.session.patch(url, headers=self.headers, json=json_data) as response:
                if response.status == 200:
                    print("Cover image updated successfully.")
                else:
                    error = await response.json()
                    print(f"Failed to update cover image. HTTP Status: {response.status}")
                    print(f"Error Details: {error.get('message', 'No message')}")
        except Exception as e:
            print(f"Exception occurred in update_event_cover_image: {e}")

    async def close(self):
        await self.session.close()

# Modal to collect event data
class EventModal(discord.ui.Modal, title="Create a New Event"):
    event_name = discord.ui.TextInput(label="Event Name", max_length=100, required=True)
    start_time = discord.ui.TextInput(label="Start Time", placeholder="YYYY-MM-DD HH:MM", required=True)
    end_time = discord.ui.TextInput(label="End Time", placeholder="YYYY-MM-DD HH:MM", required=True)
    location = discord.ui.TextInput(label="Location", required=True)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.long, max_length=500, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            local_start = local_tz.localize(datetime.strptime(self.start_time.value, "%Y-%m-%d %H:%M"))
            local_end = local_tz.localize(datetime.strptime(self.end_time.value, "%Y-%m-%d %H:%M"))
            if local_start < datetime.now(local_tz):
                await interaction.followup.send("❌ Start time cannot be in the past.", ephemeral=True)
                return
            if local_end <= local_start:
                await interaction.followup.send("❌ End time must be after start time.", ephemeral=True)
                return

            start_time_utc = local_start.astimezone(timezone('UTC')).isoformat()
            end_time_utc = local_end.astimezone(timezone('UTC')).isoformat()

            discord_events = DiscordEvents(aiohttp_session)
            event_id, result = await discord_events.create_guild_event(
                guild_id=interaction.guild_id,
                event_name=self.event_name.value,
                start_time=start_time_utc,
                end_time=end_time_utc,
                location=self.location.value,
                description=self.description.value or "No description provided."
            )

            if event_id:
                event_data_store[interaction.id] = {
                    "event_name": self.event_name.value,
                    "event_id": event_id,
                    "start_time": local_start,
                    "notification_tasks": []  # Store notification tasks for cancellation if needed
                }
                await interaction.followup.send(result, ephemeral=True)
                await interaction.user.send("Event created! Click below to upload a cover image.", view=CoverImageUploadView(interaction.id))
                await schedule_notifications(interaction.id, local_start)
            else:
                await interaction.followup.send(result, ephemeral=True)
        except ValueError:
            await interaction.followup.send("❌ Invalid date format. Use 'YYYY-MM-DD HH:MM'.", ephemeral=True)

class CoverImageUploadView(discord.ui.View):
    def __init__(self, interaction_id):
        super().__init__()
        self.interaction_id = interaction_id

    @discord.ui.button(label="Upload Cover Image", style=discord.ButtonStyle.primary)
    async def upload_cover_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Please upload an image as a reply.", ephemeral=True)

async def schedule_notifications(event_id, start_time):
    """Schedules notifications at defined intervals before the event."""
    for hours in NOTIFICATION_TIMES:
        notify_time = start_time - timedelta(hours=hours)
        if notify_time > datetime.now(local_tz):
            task = asyncio.create_task(schedule_notification_task(event_id, notify_time, hours))
            event_data_store[event_id]["notification_tasks"].append(task)

async def schedule_notification_task(event_id, notify_time, hours):
    """Waits until the specified time to send a notification."""
    await asyncio.sleep((notify_time - datetime.now(local_tz)).total_seconds())
    await send_notification(event_id, hours)

async def send_notification(event_id, hours):
    """Sends a reminder for the event if it's still scheduled."""
    event_data = event_data_store.get(event_id)
    if event_data:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        await channel.send(f"Reminder: '{event_data['event_name']}' starts in {hours} hours!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if isinstance(message.channel, discord.DMChannel) and message.attachments:
        last_interaction_id = list(event_data_store.keys())[-1]
        event_id = event_data_store[last_interaction_id]["event_id"]

        bot_image_channel = bot.get_channel(BOT_IMAGE_CHANNEL_ID)
        if bot_image_channel:
            image_message = await bot_image_channel.send(file=await message.attachments[0].to_file())
            image_url = image_message.attachments[0].url

            discord_events = DiscordEvents(aiohttp_session)
            await discord_events.update_event_cover_image(GUILD_ID, event_id, image_url)
            await message.channel.send("✅ Cover image uploaded and set for the event!")

@bot.event
async def on_ready():
    global aiohttp_session
    aiohttp_session = aiohttp.ClientSession()
    print(f'Bot connected as {bot.user}')
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("Commands synced successfully.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.event
async def on_scheduled_event_update(before, after):
    print(f"Scheduled event updated: {before.name} -> {after.name}")

    if before.start_time != after.start_time:
        print(f"Event start time changed from {before.start_time} to {after.start_time}")
        for task in event_data_store.get(after.id, {}).get("notification_tasks", []):
            task.cancel()
        event_data_store[after.id]["notification_tasks"] = []
        await schedule_notifications(after.id, after.start_time.astimezone(local_tz))

    if before.end_time != after.end_time:
        print(f"Event end time changed from {before.end_time} to {after.end_time}")
    
    if before.status != after.status:
        if after.status == discord.ScheduledEventStatus.canceled:
            print(f"Event '{after.name}' has been canceled.")
            if event_data_store.pop(after.id, None):
                print(f"Event '{after.name}' removed from data store (Reason: Canceled)")

    if after.end_time and after.end_time < datetime.now().astimezone(timezone('UTC')):
        if event_data_store.pop(after.id, None):
            print(f"Event '{after.name}' has concluded and been removed from data store.")

@bot.tree.command(name="events", description="Create a new scheduled event")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def create_event(interaction: discord.Interaction):
    if any(role.id in ALLOWED_ROLES_DICT.values() for role in interaction.user.roles):
        await interaction.response.send_modal(EventModal())
    else:
        await interaction.response.send_message("❌ You don't have permission to create events.", ephemeral=True)

async def on_shutdown():
    await aiohttp_session.close()
    print("Session closed")

try:
    bot.run(TOKEN)
finally:
    asyncio.run(on_shutdown())
