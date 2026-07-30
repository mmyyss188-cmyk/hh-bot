import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiohttp import web

# Твой токен от BotFather
TOKEN = "8959905999:AAG53M22ecGCIZf5o0Cguu3jWR4Aap6OxZM"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 1. Ловим команду /start, когда челик заходит прямо в бота
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        captcha_text = (
            "⚠️ **ПОДТВЕРЖДЕНИЕ ЧЕЛОВЕКА** ⚠️\n\n"
            "Вы коснулись бота-модератора канала **Hentai Heaven**.\n"
            "Чтобы доказать, что вы не робот-спамер и получить прямую ссылку на вход, нажмите кнопку ниже 👇"
        )
        
        # Кнопка проверки (Капча)
        inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🤖 Я НЕ РОБОТ (ПРОЙТИ ПРОВЕРКУ)", callback_data="pass_captcha")]
        ])
        
        await message.answer(
            text=captcha_text, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=inline_keyboard
        )
        print(f"⏳ Выслана капча юзеру в ЛС: {message.from_user.id}")
    except Exception as e:
        print(f"❌ Ошибка при отправке капчи: {e}")

# 2. Ловим клик по кнопке проверки и выдаем прямую ссылку на канал
@dp.callback_query(lambda c: c.data == "pass_captcha")
async def process_captcha(callback_query: types.CallbackQuery):
    try:
        # Удаляем сообщение с капчей, чтобы чат выглядел красиво
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
        
        success_text = (
            "✅ **Проверка успешно пройдена!**\n\n"
            "Жми на кнопку ниже, чтобы войти в канал напрямую без всяких ожиданий и сразу перейти к просмотру сочных анимаций MapleStar! 👇🔞"
        )
        
        # Твоя реальная прямая ссылка на канал (без заявок)
        inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔥 ВХОД В HENTAI HEAVEN 🔞", url="https://t.me/+G1yVgumeG35iNTAy")]
        ])
        
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text=success_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=inline_keyboard
        )
        print(f"🚀 Юзер {callback_query.from_user.id} прошел капчу напрямую через старт!")
        
        await callback_query.answer()
    except Exception as e:
        print(f"❌ Ошибка при прохождении капчи: {e}")

async def handle(request):
    return web.Response(text="Бот онлайн")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    asyncio.create_task(site.start())
    
    print("🤖 Бот с прямой капчей через /start запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
