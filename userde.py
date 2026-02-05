import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from pymongo import MongoClient

BOT_TOKEN = "8500522434:AAEfRD8yG2xIdv0NWH47sUty5mEZUbCqaR4"
ADMIN_ID = 1929943036  # apna Telegram ID

# MongoDB
mongo = MongoClient("mongodb+srv://pifowo6717_db_user:pifowo6717_db_user@cluster0.9j5ea8r.mongodb.net/?appName=Cluster0")
db = mongo["telegram_bot"]
users_col = db["users"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("delete_all_users"))
async def delete_all_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ You are not authorized.")

    count = users_col.count_documents({})
    users_col.delete_many({})

    await message.answer(f"✅ Done!\n🗑 Deleted users: {count}")

@dp.message(Command("delete_user"))
async def delete_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ You are not authorized.")

    try:
        uid = int(message.text.split()[1])
    except:
        return await message.answer("Usage:\n/delete_user USER_ID")

    result = users_col.delete_one({"user_id": uid})

    if result.deleted_count:
        await message.answer(f"✅ User {uid} removed")
    else:
        await message.answer("❌ User not found")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    