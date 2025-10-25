import os
import base64
from pyrogram import Client, filters
from pyrogram.types import Message

# 🔐 Your Telegram Bot API credentials
API_ID = 24436545   # replace with your API_ID
API_HASH = "afa5558d3561cb2241ed836088b56098"
BOT_TOKEN = "7837969823:AAEuB9mKonsxIhea7-_6F_CeOBESIBBXwCo"

app = Client("aar_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

UPLOAD_DIR = "uploads"
ENCODED_FILE = "encoded.txt"
DECODED_FILE = "decoded.aar"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Step 1: /start command
@app.on_message(filters.command("start"))
async def start(_, message: Message):
    await message.reply("👋 Welcome! Send a `.aar` file and use /encode or /decode commands.")


# Step 2: Receive .aar file
@app.on_message(filters.document & filters.private)
async def handle_file(_, message: Message):
    file = message.document
    if not file.file_name.endswith(".aar"):
        await message.reply("❌ Please upload a `.aar` file only.")
        return
    
    file_path = os.path.join(UPLOAD_DIR, file.file_name)
    await message.reply("📥 Downloading file...")
    await app.download_media(message.document, file_path)
    await message.reply(f"✅ File saved as `{file_path}`. Now send /encode or /decode command.")


# Step 3: Encode file to Base64
@app.on_message(filters.command("encode") & filters.private)
async def encode_file(_, message: Message):
    files = os.listdir(UPLOAD_DIR)
    aar_files = [f for f in files if f.endswith(".aar")]

    if not aar_files:
        await message.reply("⚠️ No `.aar` file found to encode. Upload it first.")
        return

    file_path = os.path.join(UPLOAD_DIR, aar_files[-1])
    with open(file_path, "rb") as f:
        encoded_data = base64.b64encode(f.read()).decode()

    with open(ENCODED_FILE, "w") as ef:
        ef.write(encoded_data)

    await message.reply_document(ENCODED_FILE, caption="📤 Here is your Base64 encoded file.")


# Step 4: Decode Base64 to .aar
@app.on_message(filters.command("decode") & filters.private)
async def decode_file(_, message: Message):
    if not os.path.exists(ENCODED_FILE):
        await message.reply("⚠️ Encoded file not found. Run /encode or send encoded text file.")
        return

    with open(ENCODED_FILE, "r") as ef:
        encoded_data = ef.read()

    try:
        decoded_data = base64.b64decode(encoded_data)
    except Exception as e:
        await message.reply(f"❌ Failed to decode: {e}")
        return

    with open(DECODED_FILE, "wb") as df:
        df.write(decoded_data)

    await message.reply_document(DECODED_FILE, caption="📥 Decoded `.aar` file ready!")


# Run the bot
app.run()
