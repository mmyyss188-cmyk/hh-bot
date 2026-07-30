import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiohttp import web

# Твой токен от BotFather
TOKEN = "8959905999:AAG53M22ecGCIZf5o0Cguu3jWR4Aap6OxZM"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.chat_join_request()
async def approve_request(update: types.ChatJoinRequest):
    try:
        # 1. Бот автоматом одобряет заявку
        await update.approve()
        
        # 2. Нормальный живой текст без ощущения спама
        welcome_text = (
            "👋 **Здарова! В канал тебя впустили, заявка одобрена.**\n\n"
            "Чтобы чат не потерялся в куче твоих диалогов, нажимай кнопку ниже и переходи сразу к просмотру.\n\n"
            "Там уже лежат сочные анимации от MapleStar, залетай. 🔞"
        )
        
        # 3. Твоя реальная рабочая ссылка на канал
        inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="👉 НАЧАТЬ ПРОСМОТР 🔞", url="https://t.me/+G1yVgumeG35iNTAy")]
        ])
        
        await bot.send_message(
            chat_id=update.from_user.id, 
            text=welcome_text, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=inline_keyboard
        )
        print(f"🚀 Одобрен юзер: {update.from_user.id}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def handle(request):
    return web.Response(text="Бот онлайн")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    asyncio.create_task(site.start())
    
    print("🤖 Бот успешно запущен в облаке...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
