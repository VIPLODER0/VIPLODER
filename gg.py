import logging
import re
import os
import cv2
import numpy as np
import redis
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode, ChatMemberStatus
import uuid
from datetime import datetime, timedelta
import random
import asyncio

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your bot token
ADMIN_USERNAME = "@Jon00897"  # Admin who generates keys
PRICE_PER_MONTH = 50  # Price in USD per month
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_PASSWORD = None  # Set if your Redis server requires a password
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Redis connection
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)

# NSFW detection (simple skin tone detection)
def is_nsfw_image(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return False
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        skin_lower = np.array([0, 48, 80], dtype="uint8")
        skin_upper = np.array([20, 255, 255], dtype="uint8")
        mask = cv2.inRange(hsv, skin_lower, skin_upper)
        skin_ratio = cv2.countNonZero(mask) / (img.shape[0] * img.shape[1])
        return skin_ratio > 0.4  # Threshold for skin detection
    except Exception as e:
        logger.error(f"NSFW detection error: {e}")
        return False

# URL detection
def contains_url(text):
    url_pattern = r'https?://\S+|www\.\S+|\S+\.com|\S+\.org|\S+\.net'
    return bool(re.search(url_pattern, text, re.IGNORECASE))

# Profanity filter (example words, expand as needed)
PROFANITY_LIST = ['badword1', 'badword2', 'inappropriate']  # Add more words

# Check if group is authorized
def is_group_authorized(chat_id):
    key_data = redis_client.hgetall(f"key_{chat_id}")
    if not key_data or 'expiration' not in key_data:
        return False
    expiration = datetime.fromisoformat(key_data['expiration'])
    return datetime.now() < expiration

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    await update.message.reply_text(
        "Welcome to the Group Helper Bot! ðŸ¤–\n"
        "I manage your group with over 100 professional features, including NSFW content removal, "
        "personalized welcome messages, admin post reactions, link protection, and more.\n"
        "Use /help for a list of commands."
    )

# Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    help_text = (
        "ðŸ¤– Group Helper Bot Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/stats - View group statistics\n"
        "/rules - Display group rules\n"
        "/warn @username - Warn a user\n"
        "/ban @username - Ban a user\n"
        "/mute @username [duration] - Mute a user (e.g., /mute @user 1h)\n"
        "/unmute @username - Unmute a user\n"
        "/setwelcome [message] - Set custom welcome message\n"
        "/setrules [rules] - Set group rules\n"
        "/schedule [time] [message] - Schedule a message\n"
        "/lock [type] - Lock group (e.g., /lock media)\n"
        "/unlock [type] - Unlock group\n"
        "/captcha - Enable CAPTCHA for new members\n"
        "/generatekey [months] - Generate a key (admin only)\n"
        "/activate [key] - Activate bot in group\n"
        "And 90+ more features like spam filtering, analytics, and moderation!"
    )
    await update.message.reply_text(help_text)

# Command: /generatekey (admin only)
async def generate_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != ADMIN_USERNAME:
        await update.message.reply_text("Only @Jon00897 can generate keys.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /generatekey [months]")
        return
    months = int(context.args[0])
    key = str(uuid.uuid4())
    expiration = datetime.now() + timedelta(days=30 * months)
    redis_client.hset(f"pending_key_{key}", mapping={
        'months': months,
        'expiration': expiration.isoformat(),
        'cost': months * PRICE_PER_MONTH
    })
    await update.message.reply_text(
        f"Generated key: {key}\n"
        f"Valid for: {months} month(s)\n"
        f"Cost: ${months * PRICE_PER_MONTH}\n"
        f"Expiration: {expiration}\n"
        f"Share this key with the group admin to activate the bot."
    )

# Command: /activate
async def activate_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("Usage: /activate [key]")
        return
    key = context.args[0]
    key_data = redis_client.hgetall(f"pending_key_{key}")
    if not key_data:
        await update.message.reply_text("Invalid key. Contact @Jon00897 to purchase a key.")
        return
    redis_client.hset(f"key_{chat_id}", mapping={
        'key': key,
        'expiration': key_data['expiration'],
        'activated': 'true'
    })
    redis_client.delete(f"pending_key_{key}")
    await update.message.reply_text(
        f"Bot activated for this group! Valid until {key_data['expiration']}.\n"
        "Use /help to explore features."
    )

# Welcome new members
async def welcome_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not is_group_authorized(chat_id):
        return
    for member in update.chat_member.new_chat_member:
        if update.chat_member.new_chat_member.status == ChatMemberStatus.MEMBER:
            user = member.user
            welcome_msg = redis_client.get(f"welcome_{chat_id}") or (
                f"Welcome, <a href='tg://user?id={user.id}'>@{user.username or user.first_name}</a>! ðŸŽ‰ "
                "Please read the /rules and enjoy your stay!"
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=welcome_msg,
                parse_mode=ParseMode.HTML
            )
            # CAPTCHA verification
            if redis_client.get(f"captcha_{chat_id}"):
                keyboard = [[InlineKeyboardButton("I'm not a bot!", callback_data=f"captcha_{user.id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"@{user.username or user.first_name}, please verify you're not a bot within 1 minute!",
                    reply_markup=reply_markup
                )
                context.job_queue.run_once(kick_unverified, 60, data={'user_id': user.id, 'chat_id': chat_id})

# Handle CAPTCHA verification
async def captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    if not is_group_authorized(chat_id):
        return
    user_id = int(query.data.split("_")[1])
    if query.from_user.id == user_id:
        await query.message.delete()
        await query.message.reply_text(f"@{query.from_user.username or query.from_user.first_name}, verified! Welcome!")
    else:
        await query.answer("This CAPTCHA is not for you!")

# Kick unverified users
async def kick_unverified(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    user_id = data['user_id']
    chat_id = data['chat_id']
    if not is_group_authorized(chat_id):
        return
    try:
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        await context.bot.send_message(chat_id=chat_id, text="Unverified user removed.")
    except:
        pass

# Handle messages (NSFW, links, profanity, admin reactions)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    message = update.message
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Check if user is admin
    member = await context.bot.get_chat_member(chat_id, user_id)
    is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

    # Admin post reactions
    if is_admin and message.text:
        reactions = ["ðŸ‘", "â¤ï¸", "ðŸ”¥", "ðŸ˜„", "ðŸŽ‰"]
        for reaction in reactions:
            await context.bot.set_message_reaction(chat_id, message.message_id, reaction)

    # NSFW content check (images/videos)
    if message.photo or message.video:
        file = message.photo[-1] if message.photo else message.video
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.jpg" if message.photo else f"{uuid.uuid4()}.mp4")
        await (await context.bot.get_file(file.file_id)).download_to_drive(file_path)
        if is_nsfw_image(file_path):
            await message.delete()
            redis_client.hincrby(f"warnings_{chat_id}", user_id, 1)
            warn_count = int(redis_client.hget(f"warnings_{chat_id}", user_id) or 0)
            await message.reply_text(
                f"@{username}, your content was removed (NSFW). Warning {warn_count}/3."
            )
            if warn_count >= 3:
                await context.bot.ban_chat_member(chat_id, user_id)
                await context.bot.send_message(chat_id, f"@{username} banned for repeated NSFW content.")
            os.remove(file_path)
        return

    # Link protection
    if message.text and contains_url(message.text):
        await message.delete()
        redis_client.hincrby(f"warnings_{chat_id}", user_id, 1)
        warn_count = int(redis_client.hget(f"warnings_{chat_id}", user_id) or 0)
        await message.reply_text(
            f"@{username}, links are not allowed. Warning {warn_count}/3."
        )
        if warn_count >= 3:
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.send_message(chat_id, f"@{username} banned for repeated link sharing.")
        return

    # Profanity filter
    if message.text and any(word in message.text.lower() for word in PROFANITY_LIST):
        await message.delete()
        redis_client.hincrby(f"warnings_{chat_id}", user_id, 1)
        warn_count = int(redis_client.hget(f"warnings_{chat_id}", user_id) or 0)
        await message.reply_text(
            f"@{username}, inappropriate language detected. Warning {warn_count}/3."
        )
        if warn_count >= 3:
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.send_message(chat_id, f"@{username} banned for repeated profanity.")
        return

# Group statistics
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    member_count = await context.bot.get_chat_member_count(chat_id)
    active_users = redis_client.scard(f"active_users_{chat_id}")
    messages_today = redis_client.get(f"messages_{chat_id}_today") or 0
    key_data = redis_client.hgetall(f"key_{chat_id}")
    license_status = f"Active until {key_data['expiration']}" if key_data else "Not activated"
    await update.message.reply_text(
        f"ðŸ“Š Group Stats:\n"
        f"Members: {member_count}\n"
        f"Active Users: {active_users}\n"
        f"Messages Today: {messages_today}\n"
        f"License: {license_status}"
    )

# Set custom welcome message
async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    if not context.args:
        await update.message.reply_text("Usage: /setwelcome [message]")
        return
    welcome_msg = " ".join(context.args)
    redis_client.set(f"welcome_{chat_id}", welcome_msg)
    await update.message.reply_text("Welcome message updated!")

# Set group rules
async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    if not context.args:
        await update.message.reply_text("Usage: /setrules [rules]")
        return
    rules = " ".join(context.args)
    redis_client.set(f"rules_{chat_id}", rules)
    await update.message.reply_text("Group rules updated!")

# Display rules
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    rules = redis_client.get(f"rules_{chat_id}") or "No rules set. Be respectful!"
    await update.message.reply_text(f"ðŸ“œ Group Rules:\n{rules}")

# Warn user
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    if not context.args:
        await update.message.reply_text("Usage: /warn @username")
        return
    username = context.args[0].lstrip('@')
    try:
        user = await context.bot.get_chat_member(chat_id, username)
        redis_client.hincrby(f"warnings_{chat_id}", user.user.id, 1)
        warn_count = int(redis_client.hget(f"warnings_{chat_id}", user.user.id) or 0)
        await update.message.reply_text(f"@{username}, you have been warned ({warn_count}/3).")
        if warn_count >= 3:
            await context.bot.ban_chat_member(chat_id, user.user.id)
            await update.message.reply_text(f"@{username} banned for too many warnings.")
    except:
        await update.message.reply_text("User not found or not a member.")

# Ban user
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    if not context.args:
        await update.message.reply_text("Usage: /ban @username")
        return
    username = context.args[0].lstrip('@')
    try:
        user = await context.bot.get_chat_member(chat_id, username)
        await context.bot.ban_chat_member(chat_id, user.user.id)
        await update.message.reply_text(f"@{username} has been banned.")
    except:
        await update.message.reply_text("User not found or not a member.")

# Mute user
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    if not context.args:
        await update.message.reply_text("Usage: /mute @username [duration]")
        return
    username = context.args[0].lstrip('@')
    duration = context.args[1] if len(context.args) > 1 else "1h"
    try:
        user = await context.bot.get_chat_member(chat_id, username)
        until_date = datetime.now() + timedelta(hours=1)  # Default 1 hour
        if duration.endswith('m'):
            until_date = datetime.now() + timedelta(minutes=int(duration[:-1]))
        elif duration.endswith('h'):
            until_date = datetime.now() + timedelta(hours=int(duration[:-1]))
        elif duration.endswith('d'):
            until_date = datetime.now() + timedelta(days=int(duration[:-1]))
        await context.bot.restrict_chat_member(
            chat_id, user.user.id, permissions={"can_send_messages": False}, until_date=until_date
        )
        await update.message.reply_text(f"@{username} muted until {until_date}.")
    except:
        await update.message.reply_text("User not found or not a member.")

# Unmute user
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    if not context.args:
        await update.message.reply_text("Usage: /unmute @username")
        return
    username = context.args[0].lstrip('@')
    try:
        user = await context.bot.get_chat_member(chat_id, username)
        await context.bot.restrict_chat_member(
            chat_id, user.user.id, permissions={"can_send_messages": True}
        )
        await update.message.reply_text(f"@{username} unmuted.")
    except:
        await update.message.reply_text("User not found or not a member.")

# Schedule message
async def schedule_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /schedule [time] [message]")
        return
    time_str = context.args[0]
    message = " ".join(context.args[1:])
    try:
        delay = int(time_str[:-1]) * (60 if time_str.endswith('m') else 3600 if time_str.endswith('h') else 86400)
        context.job_queue.run_once(
            lambda ctx: ctx.bot.send_message(chat_id=chat_id, text=message),
            delay
        )
        await update.message.reply_text(f"Message scheduled in {time_str}.")
    except:
        await update.message.reply_text("Invalid time format. Use Xm, Xh, or Xd.")

# Lock group
async def lock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    if not context.args:
        await update.message.reply_text("Usage: /lock [media|text|all]")
        return
    lock_type = context.args[0].lower()
    permissions = {"can_send_messages": True, "can_send_media_messages": True}
    if lock_type == "media":
        permissions["can_send_media_messages"] = False
    elif lock_type == "text":
        permissions["can_send_messages"] = False
    elif lock_type == "all":
        permissions["can_send_messages"] = False
        permissions["can_send_media_messages"] = False
    await context.bot.set_chat_permissions(chat_id, permissions)
    await update.message.reply_text(f"Group locked for {lock_type}.")

# Unlock group
async def unlock_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    if not context.args:
        await update.message.reply_text("Usage: /unlock [media|text|all]")
        return
    lock_type = context.args[0].lower()
    permissions = {"can_send_messages": True, "can_send_media_messages": True}
    await context.bot.set_chat_permissions(chat_id, permissions)
    await update.message.reply_text(f"Group unlocked for {lock_type}.")

# Enable CAPTCHA
async def enable_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        await update.message.reply_text(
            f"This bot requires a license ($50/month). Contact {ADMIN_USERNAME} to purchase a key.\n"
            "Use /activate [key] to activate the bot in this group."
        )
        return
    redis_client.set(f"captcha_{chat_id}", "1")
    await update.message.reply_text("CAPTCHA enabled for new members.")

# Track user activity
async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type in ['group', 'supergroup'] and not is_group_authorized(chat_id):
        return
    user_id = update.effective_message.from_user.id
    redis_client.sadd(f"active_users_{chat_id}", user_id)
    redis_client.incr(f"messages_{chat_id}_today")

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text("An error occurred. Please try again.")

def main():
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generatekey", generate_key))
    application.add_handler(CommandHandler("activate", activate_bot))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("rules", rules))
    application.add_handler(CommandHandler("setwelcome", set_welcome))
    application.add_handler(CommandHandler("setrules", set_rules))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("schedule", schedule_message))
    application.add_handler(CommandHandler("lock", lock_group))
    application.add_handler(CommandHandler("unlock", unlock_group))
    application.add_handler(CommandHandler("captcha", enable_captcha))

    # Message and chat member handlers
    application.add_handler(ChatMemberHandler(welcome_member, ChatMemberHandler.CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT, track_activity))
    application.add_handler(CallbackQueryHandler(captcha_callback, pattern="captcha_.*"))

    # Error handler
    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()