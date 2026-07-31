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

# 1. Ловим команду /start - МГНОВЕННО генерируем динамическую ссылку на 10 минут
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        # Автоматически сохраняем юзера в базу данных и проверяем, новый ли он
        is_new_user = add_user(message.from_user.id, message.from_user.username)
        
        # Если юзер новый — бот шлет тебе секретный отчет в личку
        if is_new_user:
            username_text = f"@{message.from_user.username}" if message.from_user.username else "Скрыт"
            admin_report = (
                "🔔 <b>Новый пользователь зафиксирован</b>\n\n"
                f"👤 <b>Имя:</b> {message.from_user.full_name}\n"
                f"🏷 <b>Юзернейм:</b> {username_text}\n"
                f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n\n"
                f"📊 Всего в базе данных: <code>{get_users_count()}</code>."
            )
            try:
                await bot.send_message(chat_id=ADMIN_ID, text=admin_report, parse_mode=ParseMode.HTML)
            except Exception as admin_err:
                print(f"Не удалось отправить отчет админу: {admin_err}")

        # Твой цифровой ID закрытого канала Hentai Heaven
        target_chat = "-1004407573062" 
        
        # ДИНАМИЧЕСКИЕ ССЫЛКИ: генерируем ссылку на 10 минут (600 секунд) для 1 человека
        invite_link = await bot.create_chat_invite_link(
            chat_id=target_chat,
            expire_date=int(time.time() + 600), # 10 минут
            member_limit=1 # Только 1 вход
        )

        # Строгий технический текст без капса, давления и лишних эмодзи
        welcome_text = (
            "Заявка на вступление в Hentai Heaven принята.\n\n"
            "Для перехода в канал используйте персональную одноразовую ссылку. "
            "Она будет автоматически аннулирована через 10 минут."
        )
        
        inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔗 Перейти в канал", url=invite_link.invite_link)]
        ])
        
        await message.answer(text=welcome_text, parse_mode=ParseMode.HTML, reply_markup=inline_keyboard)
    except Exception as e:
        print(f"❌ Ошибка генерации динамической ссылки: {e}")
        await message.answer("Ошибка генерации ссылки доступа. Пожалуйста, обратитесь к администратору.", parse_mode=ParseMode.HTML)

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
        "🛠 <b>Панель управления ботом</b>\n\n"
        "Список зашифрованных команд:\n\n"
        "📊 <b>Проверить базу данных:</b>\n"
        "<code>/get_backend_stats_77</code> — показывает число подписчиков.\n\n"
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
    await message.answer(f"📊 <b>Статистика базы данных:</b>\n\nНакоплено пользователей: <code>{count}</code>.", parse_mode=ParseMode.HTML)

# 🔥 СЕКРЕТНАЯ КОМАНДА РАССЫЛКИ (ПОЛНОСТЬЮ ИСПРАВЛЕНА)
@dp.message(Command("send_premium_key_99x"))
async def cmd_send(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        text_to_send = message.text.replace("/send_premium_key_99x", "").strip()
        if not text_to_send:
            await message.answer("❌ <b>Ошибка!</b> Напишите текст рассылки после команды.")
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
