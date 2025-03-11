import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, MessageHandler

# Telegram Bot Token
TOKEN = "7516323992:AAE3l8RPyTjiGOMqiPorwnj1kAbNGhPjH1Y"

# Websites list with search URLs
MOVIE_SITES = {
   "Vegamovies": "https://vegamoviesz.org/search?q=dual+audio+",
    "HDHub4U": "https://hdhub4u.tv/search?q=dual+audio+",
    "TheMoviesFlix": "https://themoviesflix.am/search?q=dual+audio+",
    "9xFlix": "https://9xflix.wine/m/hindi-movies/search?q=dual+audio+",
    "BollyFlix": "https://bollyflix.boats/?s=",
    "Filmy4wap": "https://filmy4wap.skin/?s=",
    "Filmyzilla": "https://filmyzilla.com.co/?s=",
    "KatMovieHD": "https://katmoviehd.se/?s=",
    "MoviesVerse": "https://moviesverse.skin/?s=",
    "MoviesMod": "https://moviesmod.skin/?s=",
    "OKJatt": "https://okjatt.autos/?s=",
    "SkymoviesHD": "https://skymovieshd.autos/?s=",
    "DesireMovies": "https://desiremovies.autos/?s=",
    "MLWBD": "https://mlwbd.autos/?s=",
    "HDMoviesHub": "https://hdmovieshub.autos/?s=",
}

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context) -> None:
    await update.message.reply_text("🎬 **Movie Downloader Bot** 🎬\n\nKoi bhi movie ka naam likho, mai uska download link dhoondh kar dunga!")

def search_movie(movie_name):
    results = []
    
    for site_name, site_url in MOVIE_SITES.items():
        search_url = site_url + movie_name.replace(" ", "+")
        response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Example scraping logic (adjust according to the website structure)
            links = soup.find_all("a", href=True)
            for link in links:
                if "download" in link.text.lower() or "movie" in link.text.lower():
                    results.append(f"🎥 {site_name}: [Download Link]({link['href']})")
                    break  # Get only the first result from each site
    
    return results if results else None

async def handle_message(update: Update, context) -> None:
    movie_name = update.message.text
    await update.message.reply_text(f"🔍 **Searching for:** {movie_name}...")

    download_links = search_movie(movie_name)
    
    if download_links:
        message = "\n".join(download_links)
        await update.message.reply_text(f"✅ **Movie Found!**\n{message}", parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await update.message.reply_text("❌ **Sorry, movie nahi mili.** Try another name!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
    
