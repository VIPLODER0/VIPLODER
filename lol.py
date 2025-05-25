import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import cv2
import numpy as np
from moviepy.editor import VideoFileClip, VideoClip
import uuid

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token from BotFather
TOKEN = "7754507016:AAEqdRovzYxF4dhGfho-1LgIH64X4gMSHFM"  # Replace with your bot token

# Directory to store videos
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Video Enhancer Bot! 🎥\n"
        "Send me a video, and I'll convert it to high quality and apply automatic effects based on its content.\n"
        "Use /help for more info."
    )

# Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎥 Video Enhancer Bot Help:\n"
        "- Send a video file (up to 20MB due to Telegram limits).\n"
        "- I'll upscale it to high quality (1080p, H.264) and apply effects like brightness or color enhancement based on the video.\n"
        "- Processing may take a few moments. You'll receive the enhanced video once done.\n"
        "Note: For larger videos, consider compressing them before uploading."
    )

# Analyze video to determine suitable effects
def analyze_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("Failed to open video for analysis")
        return None

    brightness_values = []
    saturation_values = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to HSV for analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        brightness = np.mean(hsv[:, :, 2])  # V channel for brightness
        saturation = np.mean(hsv[:, :, 1])  # S channel for saturation
        brightness_values.append(brightness)
        saturation_values.append(saturation)

    cap.release()

    avg_brightness = np.mean(brightness_values) if brightness_values else 100
    avg_saturation = np.mean(saturation_values) if saturation_values else 100

    effects = {}
    # If video is too dark (brightness < 100), increase brightness and contrast
    if avg_brightness < 100:
        effects['brightness'] = 1.2  # Increase brightness by 20%
        effects['contrast'] = 1.3    # Increase contrast by 30%
    # If video is low on color (saturation < 80), boost saturation
    if avg_saturation < 80:
        effects['saturation'] = 1.5  # Increase saturation by 50%

    return effects

# Apply effects to a frame
def apply_effects(frame, effects):
    # Convert frame to float for processing
    frame = frame.astype(float) / 255.0

    # Apply brightness and contrast
    if 'brightness' in effects:
        frame *= effects['brightness']
    if 'contrast' in effects:
        frame = cv2.convertScaleAbs(frame * 255, alpha=effects['contrast'], beta=0) / 255.0

    # Apply saturation in HSV space
    if 'saturation' in effects:
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        hsv[:, :, 1] *= effects['saturation']  # Boost saturation
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)  # Ensure valid range
        frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    # Convert back to uint8
    frame = np.clip(frame * 255, 0, 255).astype(np.uint8)
    return frame

# Process video: Convert to high quality and apply effects
def process_video(input_path, output_path, effects):
    try:
        clip = VideoFileClip(input_path)
        # Resize to 1080p if smaller, maintain aspect ratio
        if clip.h < 1080:
            clip = clip.resize(height=1080)

        # Define a function to process each frame
        def process_frame(frame):
            return apply_effects(frame, effects)

        # Apply effects to the video
        final_clip = clip.fl_image(process_frame)

        # Write output with high-quality settings (H.264, high bitrate)
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            bitrate='8000k',  # High bitrate for quality
            preset='slow',    # Better compression
            ffmpeg_params=['-crf', '18']  # Constant Rate Factor for quality
        )
        clip.close()
        final_clip.close()
        return True
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        return False

# Handle video messages
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video
    if not video:
        await update.message.reply_text("Please send a valid video file.")
        return

    # Download video
    file = await context.bot.get_file(video.file_id)
    video_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.mp4")
    await file.download_to_drive(video_path)

    # Analyze video for effects
    await update.message.reply_text("Analyzing your video...")
    effects = analyze_video(video_path)
    if not effects:
        await update.message.reply_text("Failed to analyze video. Processing with default settings.")
        effects = {}

    # Process video
    await update.message.reply_text("Processing video with effects...")
    output_path = os.path.join(OUTPUT_DIR, f"enhanced_{os.path.basename(video_path)}")
    success = process_video(video_path, output_path, effects)

    if success:
        # Send processed video
        with open(output_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="Here’s your enhanced video! 🎉"
            )
        # Clean up files
        os.remove(video_path)
        os.remove(output_path)
    else:
        await update.message.reply_text("Sorry, an error occurred while processing the video.")
        if os.path.exists(video_path):
            os.remove(video_path)

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text("An error occurred. Please try again.")

def main():
    # Initialize bot
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_error_handler(error_handler)

    # Start bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()