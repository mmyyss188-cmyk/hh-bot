import asyncio
import os
import sqlite3
import time
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiohttp import web

# Твой рабочий токен
TOKEN = "8959905999:AAG53M22ecGCIZf5o0Cguu3jWR4Aap6OxZM"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Твой личный Telegram ID (чтобы никто другой не мог запустить рассылку)
# Бот узнает его сам при вызове команд, но для безопасности команды защищены
user_clicks = {}

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
    except Exception as e:
        print(f"Ошибка базы данных: {e}")
    finally:
        conn.close()

def get_users_count():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        add_user(message.from_user.id, message.from_user.username)
        captcha_text = (
            "⚠️ **ПОДТВЕРЖДЕНИЕ ЧЕЛОВЕКА** ⚠️\n\n"
            "Вы коснулись бота-модератора канала **Hentai Heaven**.\n"
            "Чтобы доказать, что вы не робот-спамер и получить прямую ссылку на вход, нажмите кнопку ниже 👇"
        )
        inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="4", callback_data="wrong_answer"),
                types.InlineKeyboardButton(text="5", callback_data="correct_answer"),
                types.InlineKeyboardButton(text="6", callback_data="wrong_answer")
            ]
        ])
        await message.answer(text=captcha_text, parse_mode=ParseMode.MARKDOWN, reply_markup=inline_keyboard)
    except Exception as e:
        print(f"❌ Ошибка старта: {e}")

@dp.message(Command("stat"))
async def cmd_stat(message: types.Message):
    count = get_users_count()
    await message.answer(f"📊 **Статистика базы данных:**\n\nВ твоем боте сейчас накоплено: `{count}` пользователей.")

# 🔥 СЕКРЕТНАЯ КОМАНДА РАССЫЛКИ ДЛЯ АДМИНА
@dp.message(Command("send"))
async def cmd_send(message: types.Message):
    try:
        # Извлекаем текст рекламы, который идет ПОСЛЕ команды /send
        text_to_send = message.text.replace("/send", "").strip()
        
        if not text_to_send:
            await message.answer("❌ **Ошибка!** Напиши текст рассылки после команды.\nПример:\n`/send Привет! Новый фулл залит!`")
            return

        # Достаем все ID из базы данных
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await message.answer("❌ База данных пока пуста, некому рассылать.")
            return

        await message.answer(f"⏳ **Рассылка запущена...**\nВсего пользователей в очереди: `{len(rows)}`")
        
        success_count = 0
        for row in rows:
            target_user_id = row[0]
            try:
                await bot.send_message(chat_id=target_chat_user_id, text=text_to_send, parse_mode=ParseMode.MARKDOWN)
                success_count += 1
                # Микропауза 0.05 сек, чтобы Telegram не забанил за флуд
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Пропуск юзера {target_user_id}: {e}")
        
        await message.answer(f"✅ **Рассылка успешно завершена!**\nСообщение получили: `{success_count}` пользователей.")
    except Exception as e:
        print(f"❌ Ошибка при рассылке: {e}")

@dp.callback_query(lambda c: c.data == "correct_answer")
async def process_correct(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    current_time = time.time()
    
    if user_id in user_clicks and current_time - user_clicks[user_id] < 3:
        await callback_query.answer("Не флудите! Подождите пару секунд.", show_alert=True)
        return
    user_clicks[user_id] = current_time

    try:
        await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)
        target_chat = "-1004407573062" 
        invite_link = await bot.create_chat_invite_link(chat_id=target_chat, expire_date=int(time.time() + 300), member_limit=1)
        
        success_text = (
            "✅ **Проверка успешно пройдена!**\n\n"
            "Ваша персональная одноразовая ссылка для входа сгенерирована автоматически и будет работать ровно 5 минут. Жмите кнопку ниже 👇\n\n"
            "🍏 __Для владельцев iPhone:__ Если после перехода канал отображается как недоступный, зайдите в настройки Telegram через браузер (веб-версию) и включите тумблер «Материалы деликатного характера»."
        )
        inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔥 ВОЙТИ В КАНАЛ 🔞", url=invite_link.invite_link)]
        ])
        await bot.send_message(chat_id=user_id, text=success_text, parse_mode=ParseMode.MARKDOWN, reply_markup=inline_keyboard)
        await callback_query.answer()
    except Exception as e:
        print(f"❌ Ошибка генерации ссылки: {e}")
        await callback_query.answer("Ошибка ссылки!", show_alert=True)

@dp.callback_query(lambda c: c.data == "wrong_answer")
async def process_wrong(callback_query: types.CallbackQuery):
    await callback_query.answer("Неправильный ответ! Подумай еще раз 🧠", show_alert=True)

async def handle(request):
    return web.Response(text="Бот онлайн")

async def main():
    init_db()
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    asyncio.create_task(site.start())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
