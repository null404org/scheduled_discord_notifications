# Discord Event Notification Bot

This bot helps Discord server admins manage and announce events. Authorized users can create events, schedule reminders, and update event images. The bot handles event management tasks like real-time updates, dynamic notification rescheduling, and automatic cleanup of concluded or canceled events.

---

## Features

- **Event Creation**: Authorized users can create events with details such as name, start time, end time, location, and description.
- **Automated Scheduled Notifications**: Notifications are automatically scheduled to remind members before an event starts, based on customizable intervals.
- **Dynamic Notification Rescheduling**: If event details change (like start time), notifications are dynamically rescheduled to match the updated times.
- **Role-Based Access Control**: Only users with specified roles can create events.
- **Real-Time Updates and Cleanup**: The bot listens for event updates and cancels concluded or canceled events automatically.

---

## Initial Setup Guide

### Prerequisites

1. **Python 3.8 or Higher**: Make sure Python is installed on your system. [Download Python](https://www.python.org/downloads/).
2. **Discord Developer Portal**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications) and create a new application. Under "Bot" settings, add a bot.
   - Save the **Bot Token** and invite the bot to your server with these permissions:
     - **Manage Events**, **Send Messages**, **Embed Links**, **Attach Files**

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

3. **Configure Environment Variables**:
   - Create a `.env` file in the project directory and add the following variables:

     ```plaintext
     DISCORD_TOKEN=your-discord-bot-token
     GUILD_ID=your-discord-guild-id
     NOTIFICATION_CHANNEL_ID=channel-id-for-notifications
     BOT_IMAGE_CHANNEL_ID=channel-id-for-image-storage
     ALLOWED_ROLES=RoleName1=RoleID1,RoleName2=RoleID2
     ```
   - **Explanation**:
     - `DISCORD_TOKEN`: The bot token from the Discord Developer Portal.
     - `GUILD_ID`: The ID of your Discord server.
     - `NOTIFICATION_CHANNEL_ID`: The channel ID for event notifications.
     - `BOT_IMAGE_CHANNEL_ID`: The channel ID for storing event cover images.
     - `ALLOWED_ROLES`: Comma-separated list of roles allowed to create events in `RoleName=RoleID` format.

---

### Running the Bot

1. **Start the Bot**:
   Run the bot using the following command:
   ```bash
   python Events.py
   ```

2. **Using the Bot**:
   - **Create an Event**: Type `/events` in the Discord server to access the event creation form. Only users with allowed roles can use this command.

---

## Feature Documentation

### Scheduled Notifications

- **Automatic Notification Scheduling**: The bot automatically schedules notifications for upcoming events, using the customizable `NOTIFICATION_TIMES` variable to determine intervals before event start.
   - **Default Intervals**: Notifications are set at 18 and 6 hours before the event.
   - To change, modify the `NOTIFICATION_TIMES` variable in the script:
     ```python
     NOTIFICATION_TIMES = [18, 6]  # Adjust intervals as desired
     ```

- **Rescheduling Notifications on Event Changes**: If an event’s start time is updated, the bot will cancel previously scheduled notifications and create new notifications based on the updated time.

### Time Zone Adjustment

Set your local time zone for events by updating the `local_tz` variable:
   ```python
   local_tz = timezone('Your/TimeZone')
   ```
   Example values:
   - **North America**: `America/New_York` (ET), `America/Chicago` (CT), `America/Los_Angeles` (PT)
   - **Europe**: `Europe/London` (GMT/BST), `Europe/Paris` (CET/CEST)
   - **Asia**: `Asia/Tokyo` (JST), `Asia/Kolkata` (IST)

### Event Management and Cleanup

- **Event Creation**: Upon creation, events can include an image upload, details, and are only available to specified roles.
- **Automatic Cleanup**: Events are removed from the bot’s database once they conclude or are canceled, optimizing storage.
- **Real-Time Updates**: The bot listens for updates to events, such as changes in time or cancellations, and applies the changes automatically.

---

## Troubleshooting

- **Bot Not Responding**: Verify that the bot has the correct permissions and check that the `.env` file has accurate information.
- **Event Updates Not Applying**: Ensure the bot runs continuously for real-time updates. Consider deploying on a server or cloud service for uptime.
- **Notification Issues**: Confirm that `NOTIFICATION_TIMES` is configured correctly and that any changes to the start time allow enough lead time for the bot to schedule notifications.

---

## License

This project is licensed under the MIT License. Feel free to customize and use it for your Discord server’s needs.

