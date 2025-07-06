import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pytube import YouTube
import instaloader
import re

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token from BotFather
TOKEN = "7917489800:AAHO99sbhcfefg4itZj4rj6akBKkO9hvKqc"  # Replace with your bot token

# Function to check if URL is YouTube or Instagram
def is_youtube_url(url):
    return "youtube.com" in url or "youtu.be" in url

def is_instagram_url(url):
    return "instagram.com" in url

# Function to download YouTube video
async def download_youtube_video(url, chat_id):
    try:
        yt = YouTube(url)
        # Get the highest resolution stream (up to 720p for reasonable file size)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            return None, "No suitable video stream found."
        
        # Download video
        filename = f"video_{chat_id}.mp4"
        stream.download(filename=filename)
        return filename, None
    except Exception as e:
        logger.error(f"Error downloading YouTube video: {e}")
        return None, f"Error downloading YouTube video: {str(e)}"

# Function to download Instagram Reel
async def download_instagram_reel(url, chat_id):
    try:
        L = instaloader.Instaloader()
        # Extract shortcode from Instagram URL
        shortcode = re.search(r'reel/([A-Za-z0-9_-]+)', url)
        if not shortcode:
            return None, "Invalid Instagram Reel URL."
        
        shortcode = shortcode.group(1)
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if not post.is_video:
            return None, "The provided URL is not a video."
        
        # Download video
        filename = f"video_{chat_id}.mp4"
        L.download_post(post, target=filename)
        # Find the downloaded video file
        for file in os.listdir():
            if file.endswith(".mp4") and str(chat_id) in file:
                return file, None
        return None, "Failed to find downloaded video."
    except Exception as e:
        logger.error(f"Error downloading Instagram Reel: {e}")
        return None, f"Error downloading Instagram Reel: {str(e)}"

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a YouTube video/Shorts or Instagram Reel URL, and I'll download it for you!"
    )

# Message handler for URLs
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id

    await update.message.reply_text("Processing your request... Please wait.")

    if is_youtube_url(url):
        filename, error = await download_youtube_video(url, chat_id)
    elif is_instagram_url(url):
        filename, error = await download_instagram_reel(url, chat_id)
    else:
        await update.message.reply_text("Please provide a valid YouTube or Instagram URL.")
        return

    if error:
        await update.message.reply_text(error)
        return

    if filename and os.path.exists(filename):
        try:
            # Send video file
            with open(filename, 'rb') as video:
                await update.message.reply_video(video=video)
            # Clean up
            os.remove(filename)
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            await update.message.reply_text(f"Error sending video: {str(e)}")
    else:
        await update.message.reply_text("Failed to download the video.")

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    await update.message.reply_text("An error occurred. Please try again later.")

def main():
    # Initialize the bot
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
