# Discord Event Notification Bot

This Discord bot allows users with specific roles to create scheduled events on a Discord server. The bot automatically sends notifications to a designated channel 24 hours and 12 hours before each event starts. The bot is designed to work efficiently, minimizing API usage while ensuring that event reminders are sent in a timely manner.

## Features

- **Event Creation**: Authorized users can create events directly in the Discord server using a simple command. Events include details such as event name, start time, end time, location, and description.
- **Automated Notifications**: The bot sends reminder notifications 24 hours and 12 hours before the event's start time to a specified channel.
- **Role-Based Access Control**: Only users with specific roles can create events, ensuring that only authorized members can use this feature.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Discord server with the necessary bot permissions (manage events, send messages, etc.)

### Installation

1. **Clone the Repository**: 
   ```bash
   git clone <repository-url>
   cd <repository-directory>
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
   ALLOWED_ROLES=RoleName1=RoleID1,RoleName2=RoleID2
   ```

   - `DISCORD_TOKEN`: The token for your Discord bot.
   - `GUILD_ID`: The ID of your Discord server (guild).
   - `NOTIFICATION_CHANNEL_ID`: The ID of the channel where event notifications should be sent.
   - `ALLOWED_ROLES`: A comma-separated list of roles allowed to create events, formatted as `RoleName=RoleID`. Example: `Admin=123456789012345678,EventOrganizer=987654321098765432`.

### Running the Bot

1. **Run the Bot**:
   ```bash
   python Events_Notify.py
   ```

2. **Bot Commands**:
   - **Create Event**: Type `/events` in your Discord server to open the event creation modal (only available to users with the allowed roles).

### Notification Frequency

The bot checks for upcoming events and sends notifications based on the following schedule:

- **24-Hour Reminder**: Sent approximately 24 hours before the event start time.
- **12-Hour Reminder**: Sent approximately 12 hours before the event start time.

To adjust the frequency of how often the bot checks for upcoming events, modify the `@tasks.loop` decorator in the script:

```python
@tasks.loop(minutes=60)  # Adjust this value to control check frequency
```
### Customizing Notification Times
To adjust the 24-hour and 12-hour notification windows, modify the conditions in the `notification_task` function inside the script. For example, to send notifications 48 hours and 6 hours before the event:
```python
if time_until_event <= timedelta(hours=48) and time_until_event > timedelta(hours=47, minutes=59):
    # 48 hours prior notification
if time_until_event <= timedelta(hours=6) and time_until_event > timedelta(hours=5, minutes=59):
    # 6 hours prior notification
```

### Local Time Zone Adjustment

The bot assumes events are created in the `US/Eastern` time zone. If your organization is in a different time zone, adjust the `local_tz` variable in the script:

```python
local_tz = timezone('Your/TimeZone')
```

Replace 'Your/TimeZone' with the appropriate time zone string. Here are some examples:

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

- The bot needs to remain running continuously to manage event notifications. Consider deploying it on a server or a cloud service to ensure uptime.
- If the bot misses a notification due to downtime, it will resume checking when restarted and will only send notifications for upcoming events within the next 12 or 24 hours.

## Troubleshooting

- **Bot Not Responding**: Ensure the bot has the necessary permissions and that the token and IDs in the `.env` file are correct.
- **Rate Limits**: If you encounter rate limits, consider increasing the check interval in the `@tasks.loop` decorator.

## License

This bot script is licensed under the MIT License. Feel free to modify and use it in your organization.

