import telebot
import requests
import json
bot = telebot.TeleBot(input("8018753837:AAEOtjfr3-mZw8PTH02p77gSEg1Rtk7Kosc"))
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
  'accept-language': "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
  'priority': "u=1, i"

    }

    response = requests.post(url, data=payload, headers=headers)
    return response.content.decode('utf-8')
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_input = message.text
    bot.reply_to(message, "That's enough")
    JACKING_GOD = GOJO(user_input)
    bot.reply_to(message, JACKING_GOD)
bot.polling()
