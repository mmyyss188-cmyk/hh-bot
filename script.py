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

# ТВОЙ РЕАЛЬНЫЙ ТЕЛЕГРАМ ID
ADMIN_ID = 8288429779

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
    is_new = False
    try:
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (int(user_id),))
        row = cursor.fetchone()
        if row is None:
            cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (int(user_id), username))
            conn.commit()
            is_new = True
    except Exception as e:
        print(f"Ошибка базы данных: {e}")
    finally:
        conn.close()
    return is_new

# Функция для подсчета общего количества людей в базе
def get_users_count():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()
    conn.close()
    return count

# 1. Ловим команду /start - выдаем строгий профессиональный клик-тест
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        # Автоматически сохраняем юзера в базу данных и проверяем, новый ли он
        is_new_user = add_user(message.from_user.id, message.from_user.username)
        
        # Если юзер новый — бот шлет тебе секретный отчет в личку
        if is_new_user:
            username_text = f"@{message.from_user.username}" if message.from_user.username else "Скрыт"
            admin_report = (
                "🔔 <b>НОВЫЙ ПОЛЬЗОВАТЕЛЬ В БОТЕ!</b>\n\n"
                f"👤 <b>Имя:</b> {message.from_user.full_name}\n"
                f"🏷 <b>Юзернейм:</b> {username_text}\n"
                f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n\n"
                f"📊 Всего в базе теперь: <code>{get_users_count()[0]}</code> челиков."
            )
            try:
                await bot.send_message(chat_id=ADMIN_ID, text=admin_report, parse_mode=ParseMode.HTML)
            except Exception as admin_err:
                print(f"Не удалось отправить отчет админу: {admin_err}")

        # Строгий, профессиональный текст без капч-примеров и манипуляций
        captcha_text = (
            "🤖 <b>ВЕРИФИКАЦИЯ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
            "Добро пожаловать. Для получения доступа к приватному ресурсу необходимо подтвердить, что вы являетесь реальным пользователем.\n\n"
            "Пожалуйста, нажмите на кнопку авторизации ниже 👇"
        )
        
        inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ ПОДТВЕРДИТЬ АВТОРИЗАЦИЮ", callback_data="correct_answer")]
        ])
        
        await message.answer(text=captcha_text, parse_mode=ParseMode.HTML, reply_markup=inline_keyboard)
    except Exception as e:
        print(f"❌ Ошибка при отправке старта: {e}")

# 🔥 РОФЛ-КОМАНДА ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ (БЕЗ ОГРАНИЧЕНИЙ ПО ID)
@dp.message(Command("vrotrusy"))
async def cmd_vrotrusy(message: types.Message):
    await message.answer("💦 <b>Вы успешно залили сперму в рот Руслану!</b> 👅", parse_mode=ParseMode.HTML)

# 🔥 СЕКРЕТНОЕ МЕНЮ С ПАНЕЛЬЮ КОМАНД СТРОГО ДЛЯ ТЕБЯ
@dp.message(Command("help_admin_99"))
async def cmd_help(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    help_text = (
        "🛠 <b>СЕКРЕТНАЯ ПАНЕЛЬ УПРАВЛЕНИЯ БОТОМ</b>\n\n"
        "Используйте эти зашифрованные команды:\n\n"
        "📊 <b>Проверить базу данных:</b>\n"
        "<code>/get_backend_stats_77</code> — показывает точное число подписчиков в SQLite.\n\n"
        "📢 <b>Запустить массовую рассылку:</b>\n"
        "<code>/send_premium_key_99x [Текст]</code> — веерный пуш текста по всей базе."
    )
    await message.answer(text=help_text, parse_mode=ParseMode.HTML)

# 🔥 СЕКРЕТНАЯ КОМАНДА СТАТИСТИКИ (РАБОТАЕТ СТРОГО ДЛЯ ТЕБЯ)
@dp.message(Command("get_backend_stats_77"))
async def cmd_stat(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    count = get_users_count()
    await message.answer(f"📊 <b>Статистика базы данных:</b>\n\nВ твоем боте сейчас накоплено: <code>{count[0]}</code> пользователей.", parse_mode=ParseMode.HTML)

# 🔥 СЕКРЕТНАЯ КОМАНДА РАССЫЛКИ (ПОЛНОСТЬЮ ИСПРАВЛЕНА)
@dp.message(Command("send_premium_key_99x"))
async def cmd_send(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        text_to_send = message.text.replace("/send_premium_key_99x", "").strip()
        if not text_to_send:
            await message.answer("❌ <b>Ошибка!</b> Напиши текст рассылки после команды.")
            return

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            await message.answer("❌ База данных пока пуста, некому рассылать.")
            return

        await message.answer(f"⏳ <b>Рассылка запущена...</b>\nВсего пользователей в очереди: <code>{len(rows)}</code>", parse_mode=ParseMode.HTML)
        
        success_count = 0
        for row in rows:
            target_user_id = row[0]
            try:
                await bot.send_message(chat_id=target_user_id, text=text_to_send, parse_mode=ParseMode.HTML)
                success_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Пропуск юзера {target_user_id}: {e}")
        
        await message.answer(f"✅ <b>Рассылка успешно завершена!</b>\nСообщение получили: <code>{success_count}</code> пользователей.", parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"❌ Ошибка при рассылке: {e}")

# 2. Ловим клик по кнопке (Капча пройдена)
@dp.callback_query(lambda c: c.data == "correct_answer")
async def process_correct(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    current_time = time.time()
    
    if user_id in user_clicks and current_time - user_clicks[user_id] < 3:
        await callback_query.answer("Пожалуйста, подождите.", show_alert=True)
        return
    user_clicks[user_id] = current_time

    try:
        await bot.delete_message(chat_id=user_id, message_id=callback_query.message.message_id)
        target_chat = "-1004407573062" 
        invite_link = await bot.create_chat_invite_link(chat_id=target_chat, member_limit=1)
        
        # Строгий нейтральный текст без искусственных дедлайнов
        success_text = (
            "✅ <b>Верификация успешно пройдена</b>\n\n"
            "Ваша персональная ссылка для доступа к каналу сгенерирована. Нажмите на кнопку ниже для перехода 👇"
        )
        
        inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔗 ПЕРЕЙТИ В КАНАЛ", url=invite_link.invite_link)]
        ])
        
        await bot.send_message(chat_id=user_id, text=success_text, parse_mode=ParseMode.HTML, reply_markup=inline_keyboard)
        await callback_query.answer()
    except Exception as e:
        print(f"❌ Ошибка генерации динамической ссылки: {e}")
        await callback_query.answer("Ошибка генерации ссылки доступа.", show_alert=True)

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
