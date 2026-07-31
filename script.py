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

# 1. Ловим команду /start - выдаем строгую математическую капчу
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        # Автоматически сохраняем юзера в базу данных и проверяем, новый ли он
        is_new_user = add_user(message.from_user.id, message.from_user.username)
        
        # Если юзер новый — бот шлет тебе секретный отчет в личку!
        if is_new_user:
            username_text = f"@{message.from_user.username}" if message.from_user.username else "Скрыт"
            admin_report = (
                "🔔 **НОВЫЙ ПОЛЬЗОВАТЕЛЬ В БОТЕ!**\n\n"
                 f"👤 **Имя:** {message.from_user.full_name}\n"
                 f"🏷 **Юзернейм:** {username_text}\n"
                 f"🆔 **ID:** `{message.from_user.id}`\n\n"
                 f"📊 Всего в базе теперь: `{get_users_count()}` челиков."
            )
            try:
                await bot.send_message(chat_id=ADMIN_ID, text=admin_report, parse_mode=ParseMode.MARKDOWN)
            except Exception as admin_err:
                print(f"Не удалось отправить отчет админу: {admin_err}")

        captcha_text = (
            "👋 **Привет! Подтвердите, что вы человек.**\n\n"
            "Чтобы получить доступ к каналу и доказать, что вы не робот-спамер, решите простой пример:\n"
            "Сколько будет **2 + 3**? Выберите правильный ответ ниже 👇"
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
        print(f"❌ Ошибка при отправке старта: {e}")

# 🔥 РОФЛ-КОМАНДА ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ (БЕЗ ОГРАНИЧЕНИЙ ПО ID)
@dp.message(Command("vrotrusy"))
async def cmd_vrotrusy(message: types.Message):
    await message.answer("💦 **Вы успешно залили сперму в рот Руслану!** 👅")

# 🔥 СЕКРЕТНОЕ МЕНЮ С ПАНЕЛЬЮ КОМАНД СТРОГО ДЛЯ ТЕБЯ
@dp.message(Command("help_admin_99"))
async def cmd_help(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    help_text = (
        "🛠 **СЕКРЕТНАЯ ПАНЕЛЬ УПРАВЛЕНИЯ БОТОМ** 🛠\n\n"
        "Скопируй и используй эти зашифрованные команды:\n\n"
        "📊 **Проверить базу данных:**\n"
        "`/get_backend_stats_77` — показывает точное число подписчиков в SQLite.\n\n"
        "📢 **Запустить массовую рассылку:**\n"
        "`/send_premium_key_99x [Текст]` — веерный пуш текста по всей базе. Текст писать через один пробел на той же строчке.\n\n"
        "🤫 Кнопка `/help_admin_99` доступна только твоему ID."
    )
    await message.answer(text=help_text, parse_mode=ParseMode.MARKDOWN)

# 🔥 СЕКРЕТНАЯ КОМАНДА СТАТИСТИКИ (РАБОТАЕТ СТРОГО ДЛЯ ТЕБЯ)
@dp.message(Command("get_backend_stats_77"))
async def cmd_stat(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    count = get_users_count()
    await message.answer(f"📊 **Статистика базы данных:**\n\nВ твоем боте сейчас накоплено: `{count}` пользователей.")

# 🔥 СЕКРЕТНАЯ КОМАНДА РАССЫЛКИ (ПОЛНОСТЬЮ ЗАШИФРОВАНА И ЗАЩИЩЕНА)
@dp.message(Command("send_premium_key_99x"))
async def cmd_send(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        text_to_send = message.text.replace("/send_premium_key_99x", "").strip()
        if not text_to_send:
            await message.answer("❌ **Ошибка!** Напиши текст рассылки после команды.\nПример:\n`/send_premium_key_99x Текст`")
            return

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
            target_user_id = row[0]  # Исправлено извлечение ID из кортежа
            try:
                await bot.send_message(chat_id=target_user_id, text=text_to_send, parse_mode=ParseMode.MARKDOWN)
                success_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Пропуск юзера {target_user_id}: {e}")
        
        await message.answer(f"✅ **Рассылка успешно завершена!**\nСообщение получили: `{success_count}` пользователей.")
    except Exception as e:
        print(f"❌ Ошибка при рассылке: {e}")

# 2. Ловим клик по правильному ответу (Капча пройдена)
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
            "🍏 __Для владельцев iPhone:__ Если после перехода канал отображается как недоступный, зайдите в настройки Telegram через браузер (веб-версию) and включите тумблер «Материалы деликатного характера»."
        )
        
        inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔥 ВОЙТИ В КАНАЛ 🔞", url=invite_link.invite_link)]
        ])
        
        await bot.send_message(chat_id=user_id, text=success_text, parse_mode=ParseMode.MARKDOWN, reply_markup=inline_keyboard)
        await callback_query.answer()
    except Exception as e:
        print(f"❌ Ошибка генерации динамической ссылки: {e}")
        await callback_query.answer("Ошибка ссылки!", show_alert=True)

# 3. Ловим неправильный ответ
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
    
    print("🤖 Бот со всей админ-логикой успешно запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
