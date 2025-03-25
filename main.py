#!/usr/bin/env python3
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from threading import Thread

from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config file path
CONFIG_FILE = 'config.json'

def load_config():
    """Load configuration from JSON file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file {CONFIG_FILE} not found.")
        raise
    except json.JSONDecodeError:
        logger.error(f"Error parsing {CONFIG_FILE}. Make sure it's valid JSON.")
        raise

def save_config(config):
    """Save configuration to JSON file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    logger.info("Config saved successfully.")

def parse_time_interval(interval_str):
    """
    Parse a time interval string like "1d12h30m45s" into seconds.
    Supports days (d), hours (h), minutes (m), and seconds (s).
    """
    if not interval_str:
        return 0
    
    # Regular expression to match time components
    pattern = r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.match(pattern, interval_str)
    
    if not match or not any(match.groups()):
        raise ValueError(f"Invalid time interval format: {interval_str}")
    
    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    seconds = int(match.group(4) or 0)
    
    total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
    return total_seconds

def format_time_interval(seconds):
    """Format seconds into a human-readable time interval string."""
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    result = ""
    if days > 0:
        result += f"{days}d"
    if hours > 0:
        result += f"{hours}h"
    if minutes > 0:
        result += f"{minutes}m"
    if seconds > 0 or not result:
        result += f"{seconds}s"
    
    return result

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    config = load_config()
    
    # Only respond to the admin
    if update.effective_user.id != config['admin_id']:
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    await update.message.reply_text(
        "Welcome to the Same Picture Posting Bot!\n\n"
        "Commands:\n"
        "/status - Show current bot settings\n"
        "/setchannel @channel_name - Set the target channel\n"
        "/setinterval 1d12h30m - Set posting interval\n"
        "/post - Post the picture now\n"
        "/setpicture - Reply to a photo to set it as the picture to post"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current bot settings."""
    config = load_config()
    
    # Only respond to the admin
    if update.effective_user.id != config['admin_id']:
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    interval_seconds = parse_time_interval(config['post_interval'])
    
    status_text = (
        f"📊 Current Bot Settings 📊\n\n"
        f"🔹 Channel: {config['channel_name']}\n"
        f"🔹 Picture: {config['picture_path']}\n"
        f"🔹 Posting interval: {config['post_interval']} ({format_time_interval(interval_seconds)})\n"
    )
    
    if config['last_post_time']:
        last_post = datetime.fromtimestamp(config['last_post_time'])
        next_post = last_post + timedelta(seconds=interval_seconds)
        now = datetime.now()
        
        status_text += (
            f"🔹 Last post: {last_post.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🔹 Next post: {next_post.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        
        if next_post > now:
            time_left = next_post - now
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            status_text += f"🔹 Time until next post: {time_left.days}d {hours}h {minutes}m {seconds}s\n"
    else:
        status_text += "🔹 No posts have been made yet.\n"
    
    await update.message.reply_text(status_text)

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the target channel."""
    config = load_config()
    
    # Only respond to the admin
    if update.effective_user.id != config['admin_id']:
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    if not context.args or not context.args[0].startswith('@'):
        await update.message.reply_text(
            "Please provide a valid channel name starting with @.\n"
            "Example: /setchannel @your_channel_name"
        )
        return
    
    channel_name = context.args[0]
    config['channel_name'] = channel_name
    save_config(config)
    
    await update.message.reply_text(f"Channel set to {channel_name}")

async def set_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the posting interval."""
    config = load_config()
    
    # Only respond to the admin
    if update.effective_user.id != config['admin_id']:
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Please provide a time interval.\n"
            "Examples:\n"
            "/setinterval 1d - Once per day\n"
            "/setinterval 12h - Every 12 hours\n"
            "/setinterval 30m - Every 30 minutes\n"
            "/setinterval 1d6h30m - 1 day, 6 hours and 30 minutes\n"
        )
        return
    
    interval_str = context.args[0]
    
    try:
        seconds = parse_time_interval(interval_str)
        if seconds < 10:  # Minimum 10 seconds
            await update.message.reply_text("Interval must be at least 10 seconds.")
            return
            
        config['post_interval'] = interval_str
        save_config(config)
        
        await update.message.reply_text(
            f"Posting interval set to {interval_str} ({format_time_interval(seconds)})"
        )
    except ValueError as e:
        await update.message.reply_text(str(e))

async def set_picture(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the picture to post."""
    config = load_config()
    
    # Only respond to the admin
    if update.effective_user.id != config['admin_id']:
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    # Check if the message is a reply to a photo
    if update.message.reply_to_message and update.message.reply_to_message.photo:
        photo = update.message.reply_to_message.photo[-1]  # Get the largest photo
        
        # Create pictures directory if it doesn't exist
        os.makedirs('pictures', exist_ok=True)
        
        # Download the photo
        file = await context.bot.get_file(photo.file_id)
        file_path = f"pictures/picture_{int(time.time())}.jpg"
        await file.download_to_drive(file_path)
        
        # Update config
        config['picture_path'] = file_path
        save_config(config)
        
        await update.message.reply_text(f"Picture set to {file_path}")
    else:
        await update.message.reply_text(
            "Please reply to a photo with /setpicture to set it as the picture to post."
        )

async def post_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Post the picture now."""
    config = load_config()
    
    # Only respond to the admin
    if update.effective_user.id != config['admin_id']:
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    try:
        # Check if the picture exists
        if not os.path.exists(config['picture_path']):
            await update.message.reply_text(
                f"Picture not found: {config['picture_path']}\n"
                "Please set a valid picture using /setpicture."
            )
            return
        
        # Post the picture
        with open(config['picture_path'], 'rb') as photo:
            await context.bot.send_photo(
                chat_id=config['channel_name'],
                photo=photo
            )
        
        # Update last post time
        config['last_post_time'] = int(time.time())
        save_config(config)
        
        await update.message.reply_text("Picture posted successfully!")
    except Exception as e:
        await update.message.reply_text(f"Error posting picture: {str(e)}")

async def post_scheduled_picture(context: ContextTypes.DEFAULT_TYPE):
    """Post the scheduled picture to the channel."""
    config = load_config()
    
    try:
        # Check if the picture exists
        if not os.path.exists(config['picture_path']):
            logger.error(f"Picture not found: {config['picture_path']}")
            return
        
        # Post the picture
        with open(config['picture_path'], 'rb') as photo:
            await context.bot.send_photo(
                chat_id=config['channel_name'],
                photo=photo
            )
        
        # Update last post time
        config['last_post_time'] = int(time.time())
        save_config(config)
        
        logger.info(f"Scheduled picture posted to {config['channel_name']}")
    except Exception as e:
        logger.error(f"Error posting scheduled picture: {str(e)}")

def schedule_next_post(application):
    """Schedule the next post based on the config."""
    config = load_config()
    
    # Calculate when to post next
    interval_seconds = parse_time_interval(config['post_interval'])
    
    if config['last_post_time']:
        last_post_time = config['last_post_time']
        next_post_time = last_post_time + interval_seconds
        now = int(time.time())
        
        # If next post time is in the past, post immediately
        if next_post_time <= now:
            delay = 1  # Post after 1 second
        else:
            delay = next_post_time - now
    else:
        # If no posts have been made yet, post after the interval
        delay = interval_seconds
    
    logger.info(f"Scheduling next post in {format_time_interval(delay)}")
    
    # Schedule the job
    application.job_queue.run_once(
        post_scheduled_picture,
        timedelta(seconds=delay)
    )
    
    # Schedule the next post after this one
    application.job_queue.run_once(
        lambda context: schedule_next_post(application),
        timedelta(seconds=delay + 1)  # Schedule 1 second after posting
    )

def main():
    """Start the bot."""
    # Load config
    config = load_config()
    
    # Create the Application
    application = Application.builder().token(config['bot_token']).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("setchannel", set_channel))
    application.add_handler(CommandHandler("setinterval", set_interval))
    application.add_handler(CommandHandler("setpicture", set_picture))
    application.add_handler(CommandHandler("post", post_now))
    
    # Schedule the first post
    schedule_next_post(application)
    
    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
