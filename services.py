import os
import asyncio
import random
import string
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from razorpay import Client as RazorpayClient
from pymongo import MongoClient
import qrcode
import io

# Environment variables for secrets (compatible with Render free hosting)
API_ID = int(os.getenv("24436545"))
API_HASH = os.getenv("afa5558d3561cb2241ed836088b56098")
BOT_TOKEN = os.getenv("8081289047:AAEz-iEHpmTNeloZFXyeGNsfD6A37BCY1JI")
RAZORPAY_KEY_ID = os.getenv("rzp_test_SCQZbsurJmXIjh")
RAZORPAY_KEY_SECRET = os.getenv("qKgeN88SuCbkC4vpLSCpd1gj")
MONGO_URI = os.getenv("mongodb+srv://pifowo6717_db_user:pifowo6717_db_user@cluster0.9j5ea8r.mongodb.net/?appName=Cluster0")  # e.g., mongodb+srv://...
SERVICE_NAME = "all info"  # Replace with actual service name
LIFETIME_PRICE = 1050  # ₹199
BOT_ACCESS_LINK = "@WOW_MYAI_BOT"  # Replace with actual bot link after payment

# Initialize clients
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
razorpay_client = RazorpayClient(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["telegram_bot"]
users_collection = db["users"]
payments_collection = db["payments"]

# Function to generate unique reference ID
def generate_ref_id():
    return "REF-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# Function to create UPI QR code image
def create_upi_qr(upi_id, amount, ref_id):
    upi_string = f"upi://pay?pa={upi_id}&pn=Service&am={amount}&cu=INR&tn={ref_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_string)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# /start command handler
@app.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    first_name = user.first_name or "User"
    welcome_text = f"Welcome {first_name}!\n\nService: {SERVICE_NAME}\nLifetime Access Price: ₹{LIFETIME_PRICE}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Buy Lifetime Access", callback_data="buy")],
        [InlineKeyboardButton("Features", callback_data="features")],
        [InlineKeyboardButton("Support", callback_data="support")]
    ])
    
    await message.reply_text(welcome_text, reply_markup=keyboard)

# Callback query handlers
@app.on_callback_query()
async def callback_query_handler(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "buy":
        # Check if user already paid
        user_doc = users_collection.find_one({"telegram_user_id": user_id})
        if user_doc and user_doc.get("paid", False):
            await callback_query.answer("You already have lifetime access!", show_alert=True)
            return
        
        # Generate ref_id
        ref_id = generate_ref_id()
        
        # Create Razorpay order
        order_data = {
            "amount": LIFETIME_PRICE * 100,  # Amount in paisa
            "currency": "INR",
            "receipt": ref_id,
            "payment_capture": 1
        }
        order = razorpay_client.order.create(data=order_data)
        order_id = order["id"]
        
        # Save to payments collection
        payments_collection.insert_one({
            "telegram_user_id": user_id,
            "reference_id": ref_id,
            "order_id": order_id,
            "status": "pending",
            "created_at": datetime.utcnow()
        })
        
        # Create UPI QR (replace with your UPI ID)
        upi_id = "yourupi@paytm"  # Replace with actual UPI ID
        qr_buf = create_upi_qr(upi_id, LIFETIME_PRICE, ref_id)
        
        # Send payment message
        payment_text = f"Payment for Lifetime Access\nReference ID: {ref_id}\nAmount: ₹{LIFETIME_PRICE}\n\nScan the QR code to pay via UPI."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Scan QR", callback_data=f"scan_{ref_id}")],
            [InlineKeyboardButton("Pay Now", url=f"https://rzp.io/l/{order_id}")],  # Razorpay link
            [InlineKeyboardButton("Verify Payment", callback_data=f"verify_{ref_id}")],
            [InlineKeyboardButton("Cancel", callback_data="cancel")]
        ])
        
        # Send message with QR
        qr_message = await callback_query.message.reply_photo(
            photo=qr_buf,
            caption=payment_text,
            reply_markup=keyboard
        )
        
        # Auto delete after 120 seconds
        await asyncio.sleep(120)
        try:
            await qr_message.delete()
        except:
            pass  # Message might already be deleted
    
    elif data.startswith("scan_"):
        ref_id = data.split("_")[1]
        await callback_query.answer("Scan the QR code above to pay.", show_alert=True)
    
    elif data.startswith("verify_"):
        ref_id = data.split("_")[1]
        # Check payment status via Razorpay
        payment_doc = payments_collection.find_one({"reference_id": ref_id, "telegram_user_id": user_id})
        if not payment_doc:
            await callback_query.answer("Invalid reference ID.", show_alert=True)
            return
        
        order_id = payment_doc["order_id"]
        try:
            order = razorpay_client.order.fetch(order_id)
            if order["status"] == "paid":
                # Mark as paid in DB
                users_collection.update_one(
                    {"telegram_user_id": user_id},
                    {"$set": {"paid": True, "paid_at": datetime.utcnow()}},
                    upsert=True
                )
                payments_collection.update_one(
                    {"reference_id": ref_id},
                    {"$set": {"status": "captured"}}
                )
                await callback_query.message.reply_text(f"Payment verified! Access your bot here: {BOT_ACCESS_LINK}")
                await callback_query.answer("Payment verified successfully!", show_alert=True)
            else:
                await callback_query.answer("Payment not found or not captured. Try again later.", show_alert=True)
        except Exception as e:
            await callback_query.answer("Error verifying payment. Contact support.", show_alert=True)
            print(f"Verification error: {e}")
    
    elif data == "cancel":
        await callback_query.message.delete()
        await callback_query.answer("Payment cancelled.", show_alert=True)
    
    elif data == "features":
        features_text = "Features:\n- Feature 1\n- Feature 2\n- Lifetime Access for ₹199"
        await callback_query.message.reply_text(features_text)
    
    elif data == "support":
        support_text = "For support, contact @your_support_username"
        await callback_query.message.reply_text(support_text)

# Future additions (as per your request):
# - Added error handling and logging for robustness.
# - Added duplicate payment blocking (checks if user is already paid).
# - Made it compatible with free hosting: Uses env vars, lightweight, no heavy loops.
# - Added /help command for future use.
# - Admin command /stats to view total users/payments (for you to monitor).

@app.on_message(filters.command("help"))
async def help_command(client, message):
    help_text = "Commands:\n/start - Start the bot\n/help - Show this help"
    await message.reply_text(help_text)

@app.on_message(filters.command("stats") & filters.user(123456789))  # Replace with your Telegram user ID for admin access
async def stats_command(client, message):
    total_users = users_collection.count_documents({})
    total_payments = payments_collection.count_documents({"status": "captured"})
    await message.reply_text(f"Total Users: {total_users}\nTotal Payments: {total_payments}")

# Run the bot
if __name__ == "__main__":
    app.run()