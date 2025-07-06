import os
from pyrogram import Client, filters
import yt_dlp
import instaloader

# Replace with your credentials
API_ID = "24436545"
API_HASH = "afa5558d3561cb2241ed836088b56098"
BOT_TOKEN = "7917489800:AAGMsgg7pqeGvZekoL6w-0dWuvKJeba2kp0"

# Bot Setup
bot = Client("video_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Download YouTube (Supports up to 4K)
def download_youtube(url):
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'bestvideo[height<=2160]+bestaudio/best',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# Download Instagram
def download_instagram(url):
    L = instaloader.Instaloader(dirname_pattern='downloads', save_metadata=False)
    shortcode = url.split("/")[-2]
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    L.download_post(post, target=shortcode)
    for file in os.listdir(shortcode):
        if file.endswith(".mp4"):
            return os.path.join(shortcode, file)
    return None

# File Cleanup
def cleanup(file_path):
    try:
        os.remove(file_path)
        folder = os.path.dirname(file_path)
        if os.path.exists(folder) and os.path.isdir(folder) and not folder.startswith("downloads"):
            os.rmdir(folder)
    except Exception as e:
        print("Cleanup error:", e)

# Main Handler
@bot.on_message(filters.private & filters.text)
async def download_handler(client, message):
    url = message.text.strip()

    if "youtube.com" in url or "youtu.be" in url:
        await message.reply("📥 Downloading YouTube video (up to 4K)...")
        try:
            file_path = download_youtube(url)

            # Check size limit
            if os.path.getsize(file_path) > 2 * 1024 * 1024 * 1024:
                await message.reply("❌ File too large for Telegram (limit: 2GB). Try lower resolution.")
                cleanup(file_path)
                return

            await message.reply_video(video=file_path)
            cleanup(file_path)

        except Exception as e:
            await message.reply(f"❌ YouTube download failed: {e}")

    elif "instagram.com" in url:
        await message.reply("📥 Downloading Instagram video...")
        try:
            file_path = download_instagram(url)
            if file_path:
                if os.path.getsize(file_path) > 2 * 1024 * 1024 * 1024:
                    await message.reply("❌ File too large for Telegram (limit: 2GB).")
                    cleanup(file_path)
                    return
                await message.reply_video(video=file_path)
                cleanup(file_path)
            else:
                await message.reply("❌ Could not find video in the post.")
        except Exception as e:
            await message.reply(f"❌ Instagram download failed: {e}")
    else:
        await message.reply("⚠️ Please send a valid YouTube or Instagram video link.")

# Start Bot
print("🤖 Bot is running...")
bot.run()
