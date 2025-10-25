import telebot
import requests
import json
import os
from dotenv import load_dotenv

# .env फाइल से टोकन लोड करें
load_dotenv()
BOT_TOKEN = os.getenv("8018753837:AAG_eL3C8iUEm4XxUxfBtbcs-mcf0j7EmPg")  # .env फाइल से टोकन पढ़ता है

# बॉट शुरू करें
bot = telebot.TeleBot(BOT_TOKEN)

# बाकी कोड...
def GOJO(user_input):
    url = "https://api.binjie.fun/api/generateStream"
    payload = json.dumps({
        "prompt": user_input,
        "network": True,
        "system": "",
        "withoutContext": False,
        "stream": False
    }, ensure_ascii=False).encode('utf-8')
    
    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Build/RKQ1.201004.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'sec-ch-ua': "\"Not)A;Brand\";v=\"99\", \"Android WebView\";v=\"127\", \"Chromium\";v=\"127\"",
        'sec-ch-ua-platform': "\"Android\"",
        'sec-ch-ua-mobile': "?1",
        'origin': "https://chat18.aichatos8.com",
        'sec-fetch-site': "cross-site",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://chat18.aichatos8.com/",
        'accept-language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6",
        'priority': "u=1, i"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.content.decode('utf-8')
    except requests.exceptions.RequestException as e:
        return f"API से संपर्क में त्रुटि: {str(e)}"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_input = message.text
    try:
        response = GOJO(user_input)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"त्रुटि: {str(e)}")

try:
    bot.polling()
except Exception as e:
    print(f"बॉट पोलिंग में त्रुटि: {str(e)}")
