import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Telegram Bot Token (BotFather se le)
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Websites ka list jahan movies available ho sakti hain
MOVIE_SITES = [
    "https://examplemoviesite1.com/search?q=",
    "https://examplemoviesite2.com/search?q=",
]

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hello! Movie ka naam likho, mai download link dhoondhunga.")

def search_movie(movie_name):
    for site in MOVIE_SITES:
        search_url = site + movie_name.replace(" ", "+")
        response = requests.get(search_url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # Example: Movie link ko extract karne ka tareeka (Website ke HTML par depend karega)
            links = soup.find_all("a", href=True)
            for link in links:
                if "download" in link.text.lower():
                    return link["href"]

    return None

def handle_message(update: Update, context: CallbackContext) -> None:
    movie_name = update.message.text
    update.message.reply_text(f"🔍 Searching for: {movie_name}...")

    download_link = search_movie(movie_name)
    
    if download_link:
        update.message.reply_text(f"✅ Movie Found!\nDownload here: {download_link}")
    else:
        update.message.reply_text("❌ Sorry, movie nahi mili. Try another name!")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
