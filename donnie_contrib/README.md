# Discord Event Notification Bot

This Discord bot allows designated users with specific roles to create and manage scheduled events on a Discord server. Notifications are sent to a specified channel, and real-time updates and event cleanup are handled through WebSocket connections for improved efficiency and minimized API usage.

## Features

- **Event Creation**: Authorized users can create events with details like event name, start time, end time, location, and description.
- **Automated Notifications**: The bot can send notifications based on user-defined event times, while continuously updating and cleaning up completed or canceled events in real-time.
- **Role-Based Access Control**: Only users with authorized roles can create events.
- **Real-Time Updates and Cleanup**: Using WebSocket, the bot responds to real-time event changes and automatically removes concluded or canceled events from the database.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- A Discord server with a bot that has the necessary permissions (manage events, send messages, etc.)

### Installation

1. **Clone the Repository**: 
   ```bash
   git clone https://github.com/null404org/scheduled_discord_notifications
   cd scheduled_discord_notifications
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` File**: 
   Create a `.env` file in the root of your project directory and add the following variables:

   ```env
   DISCORD_TOKEN=your-discord-bot-token
   GUILD_ID=your-discord-guild-id
   NOTIFICATION_CHANNEL_ID=channel-id-for-notifications
   BOT_IMAGE_CHANNEL_ID=channel-id-for-image-storage
   ALLOWED_ROLES=RoleName1=RoleID1,RoleName2=RoleID2
   ```

   - `DISCORD_TOKEN`: The token for your Discord bot.
   - `GUILD_ID`: The ID of your Discord server.
   - `NOTIFICATION_CHANNEL_ID`: The ID of the channel where event notifications should be sent.
   - `BOT_IMAGE_CHANNEL_ID`: The ID of a channel where uploaded event images will be stored.
   - `ALLOWED_ROLES`: A comma-separated list of roles permitted to create events. Format: `RoleName=RoleID`.

### Running the Bot

1. **Run the Bot**:
   ```bash
   python Events.py
   ```

2. **Bot Commands**:
   - **Create Event**: Type `/events` in your Discord server to open the event creation modal (only available to users with allowed roles).

### Event Management and Cleanup

- **Real-Time Event Updates**: The bot listens for updates such as event time changes, description edits, and cancellations, and logs them in real time.
- **Automatic Cleanup**: Events are removed from the bot’s database when canceled or concluded to keep the storage efficient.

### Customizing Notification Times
You can adjust the notification times by changing the `NOTIFICATION_TIMINGS` variable in the script:

```python
NOTIFICATION_TIMINGS = [24, 12]  # Time in hours before event start
```

### Local Time Zone Adjustment

The bot assumes events are created in the `US/Eastern` time zone. If your organization is in a different time zone, update the `local_tz` variable in the script:

```python
local_tz = timezone('Your/TimeZone')
```

Examples of time zones:

    North America:
        'America/New_York' – Eastern Time (ET)
        'America/Chicago' – Central Time (CT)
        'America/Denver' – Mountain Time (MT)
        'America/Los_Angeles' – Pacific Time (PT)
        'America/Phoenix' – Arizona Time (MT, no DST)

    Europe:
        'Europe/London' – Greenwich Mean Time (GMT)/British Summer Time (BST)
        'Europe/Paris' – Central European Time (CET)/Central European Summer Time (CEST)

    Asia:
        'Asia/Tokyo' – Japan Standard Time (JST)
        'Asia/Shanghai' – China Standard Time (CST)
        'Asia/Kolkata' – India Standard Time (IST)

    Australia:
        'Australia/Sydney' – Australian Eastern Standard Time (AEST)/Australian Eastern Daylight Time (AEDT)

### Notes

- The bot requires continuous uptime for real-time updates and automated cleanup. Consider deploying it on a server or cloud platform.
- For any missed notifications due to downtime, the bot will automatically resume its tasks upon restarting, with up-to-date data for upcoming events.

## Troubleshooting

- **Bot Not Responding**: Verify that the bot has the necessary permissions and that your `.env` file has the correct token and IDs.
- **Missing Event Data**: Ensure that real-time updates and event logs confirm the storage and cleanup of data as intended. 

## License

This bot is licensed under the MIT License. Feel free to modify and use it in your organization.

