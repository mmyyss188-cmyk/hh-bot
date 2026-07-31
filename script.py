import asyncio
import os
import sqlite3
import time
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiohttp import web

# Твой проверенный токен
TOKEN = "8959905999:AAG53M22ecGCIZf5o0Cguu3jWR4Aap6OxZM"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь для защиты от флуда и мульти-клика в оперативной памяти
user_clicks = {}

# Инициализация базы данных SQLite при запуске сервера
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

# Запись каждого нового пользователя в базу данных
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

# Функция для подсчета общего количества людей в базе
def get_users_count():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# 1. Ловим команду /start - выдаем строгую математическую капчу
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        # Автоматически сохраняем юзера в базу данных
        add_user(message.from_user.id, message.from_user.username)
        
        captcha_text = (
            "👋 **Привет! Подтвердите, что вы человек.**\n\n"
            "Чтобы получить доступ к каналу и доказать, что вы не робот-спамер, решите простой пример:\n"
            "Сколько будет **2 + 3**? Выберите правильный ответ ниже 👇"
        )
        
        # Инлайн-кнопки с вариантами ответов (правильный - 5)
        inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="4", callback_data="wrong_answer"),
                types.InlineKeyboardButton(text="5", callback_data="correct_answer"),
                types.InlineKeyboardButton(text="6", callback_data="wrong_answer")
            ]
        ])
        
        await message.answer(text=captcha_text, parse_mode=ParseMode.MARKDOWN, reply_markup=inline_keyboard)
    except Exception as e:
        print(f"❌ Ошибка при отправке старта: {e}")

# Секретная админская команда для проверки статистики базы данных
@dp.message(Command("stat"))
async def cmd_stat(message: types.Message):
    count = get_users_count()
    await message.answer(f"📊 **Статистика базы данных:**\n\nВ твоем боте сейчас накоплено: `{count}` пользователей.")

# 2. Ловим клик по правильному ответу (Капча пройдена)
@dp.callback_query(lambda c: c.data == "correct_answer")
async def process_correct(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    current_time = time.time()
    
    # ТРОТТЛИНГ (Антифлуд): защита от спам-кликов
    if user_id in user_clicks and current_time - user_clicks[user_id] < 3:
        await callback_query.answer("Не флудите! Подождите пару секунд.", show_alert=True)
        return
    user_clicks[user_id] = current_time

    try:
        # УДАЛЕНИЕ СООБЩЕНИЯ (Защита от мульти-клика): стираем капчу сразу
        await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)
        
        # Твой приватный канал Hentai Heaven. Ссылка на него: https://t.me
        # Так как ссылка приватная, мы используем хэш-хвостик 'G1yVgumeG35iNTAy' для создания динамических инвайтов
        target_chat = "+G1yVgumeG35iNTAy" 
        
        # ДИНАМИЧЕСКИЕ ССЫЛКИ: создаем одноразовую ссылку на 5 минут строго для 1 человека
        invite_link = await bot.create_chat_invite_link(
            chat_id=target_chat,
            expire_date=int(time.time() + 300), # Сгорает через 5 минут
            member_limit=1 # Строго 1 вход
        )
        
        # Финальный текст с инструкцией для обхода блокировок на iOS
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
        print(f"❌ Ошибка генерации динамической ссылки: {e}")
        await callback_query.answer("Ошибка! Проверьте, добавлен ли бот в администраторы канала с правами создания ссылок!", show_alert=True)

# 3. Ловим неправильный ответ
@dp.callback_query(lambda c: c.data == "wrong_answer")
async def process_wrong(callback_query: types.CallbackQuery):
    await callback_query.answer("Неправильный ответ! Подумай еще раз 🧠", show_alert=True)

async def handle(request):
    return web.Response(text="Бот онлайн")

async def main():
    # Автоматически создаем таблицу базы данных sqlite при старте
    init_db()
    
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    asyncio.create_task(site.start())
    
    print("🤖 Бот со строгой капчей, БД и динамическими ссылками успешно запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
