import asyncio
import os
import sqlite3
import time
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# Твой проверенный токен
TOKEN = "8959905999:AAG53M22ecGCIZf5o0Cguu3jWR4Aap6OxZM"

# ТВОЙ РЕАЛЬНЫЙ ТЕЛЕГРАМ ID
ADMIN_ID = 8288429779

bot = Bot(token=TOKEN)
# Подключаем хранилище для состояний, чтобы бот ждал текст
dp = Dispatcher(storage=MemoryStorage())

# Состояние ожидания ответа
class CaptchaState(StatesGroup):
    waiting_for_answer = State()

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

# 1. Ловим команду /start - просим НАПИСАТЬ ответ текстом
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
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

        # Просим написать ответ руками
        captcha_msg = await message.answer(
            "👋 **Привет! Подтвердите, что вы человек.**\n\n"
            "Чтобы получить доступ к каналу и доказать, что вы не робот-спамер, напишите ответ текстом:\n"
            "Сколько будет **2 + 3**? Отправьте правильную цифру сообщением 👇"
        )
        
        # Переводим юзера в режим ожидания ответа
        await state.set_state(CaptchaState.waiting_for_answer)
        # Запоминаем ID сообщения капчи, чтобы потом его стереть
        await state.update_data(captcha_msg_id=captcha_msg.message_id)
        
    except Exception as e:
        print(f"❌ Ошибка при отправке старта: {e}")

# ХЕНДЛЕР ПРОВЕРКИ ТЕКСТОВОГО ОТВЕТА
@dp.message(CaptchaState.waiting_for_answer)
async def process_captcha_text(message: types.Message, state: FSMContext):
    user_answer = message.text.strip()
    user_id = message.from_user.id

    # Если ввели правильную цифру 5
    if user_answer in ["5", "пять", "Пять"]:
        try:
            data = await state.get_data()
            captcha_msg_id = data.get("captcha_msg_id")
            
            # Удаляем и вопрос бота, и ответ юзера для идеальной чистоты
            try:
                await bot.delete_message(chat_id=user_id, message_id=captcha_msg_id)
                await bot.delete_message(chat_id=user_id, message_id=message.message_id)
            except:
                pass
            
            # Закрываем состояние ожидания
            await state.clear()
            
            # Генерируем динамическую одноразовую ссылку
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
            
        except Exception as e:
            print(f"❌ Ошибка генерации текстовой ссылки: {e}")
    else:
        # Если написал бред — просим подумать еще раз
        await message.answer("❌ **Неправильный ответ!** Подумайте еще раз и отправьте правильную цифру:")

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

# 🔥 СЕКРЕТНАЯ КОМАНДА РАССЫЛКИ (ПОЛНОСТЬЮ ИСПРАВЛЕНА)
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
            target_user_id = row
            try:
                await bot.send_message(chat_id=target_user_id, text=text_to_send, parse_mode=ParseMode.MARKDOWN)
                success_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                print(f"Пропуск юзера {target_user_id}: {e}")
        
        await message.answer(f"✅ **Рассылка успешно завершена!**\nСообщение получили: `{success_count}` пользователей.")
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
