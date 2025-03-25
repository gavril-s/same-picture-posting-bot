# Same Picture Posting Bot

A Telegram bot that posts a specific picture to a channel at regular intervals. The bot allows the admin to change the channel name, picture, and posting interval through direct messages.

## Features

- Posts a picture to a Telegram channel at regular intervals
- Admin can change the target channel through DM
- Admin can change the picture to post through DM
- Admin can set the posting interval with flexible time format (days, hours, minutes, seconds)
- All settings are stored in a JSON config file

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/gavril-s/same-picture-posting-bot.git
   cd same-picture-posting-bot
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   
   This will install python-telegram-bot with the job-queue extra, which is required for scheduling posts.

4. Create a Telegram bot and get your bot token:
   - Talk to [@BotFather](https://t.me/BotFather) on Telegram
   - Use the `/newbot` command to create a new bot
   - Copy the bot token provided by BotFather

5. Get your Telegram user ID:
   - Talk to [@userinfobot](https://t.me/userinfobot) on Telegram
   - It will reply with your user ID

6. Update the `config.json` file with your bot token and admin ID:
   ```json
   {
       "bot_token": "YOUR_BOT_TOKEN_HERE",
       "admin_id": YOUR_TELEGRAM_USER_ID_HERE,
       "channel_name": "@your_channel_name",
       "picture_path": "pictures/default.jpg",
       "post_interval": "24h",
       "last_post_time": null
   }
   ```

7. Add a picture to the `pictures` directory that you want to post

8. Make sure your bot is an admin in the target channel with permission to post messages

## Usage

1. Run the bot:
   ```
   python main.py
   ```

2. Start a conversation with your bot on Telegram

3. Use the following commands to control the bot:
   - `/start` - Get a list of available commands
   - `/status` - Show current bot settings
   - `/setchannel @channel_name` - Set the target channel
   - `/setinterval 1d12h30m` - Set posting interval
   - `/post` - Post the picture now
   - `/setpicture` - Reply to a photo with this command to set it as the picture to post

## Time Interval Format

The bot supports a flexible time interval format:
- `d` - days
- `h` - hours
- `m` - minutes
- `s` - seconds

Examples:
- `1d` - Once per day
- `12h` - Every 12 hours
- `30m` - Every 30 minutes
- `1d6h30m` - 1 day, 6 hours and 30 minutes
- `90s` - Every 90 seconds

## Configuration

All settings are stored in the `config.json` file:

- `bot_token`: Your Telegram bot token
- `admin_id`: Your Telegram user ID (only this user can control the bot)
- `channel_name`: The target channel where pictures will be posted (must start with @)
- `picture_path`: Path to the picture file to post
- `post_interval`: How often to post the picture
- `last_post_time`: Timestamp of the last post (used to calculate the next post time)

## License

This project is open source and available under the [MIT License](LICENSE).
