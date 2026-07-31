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

# Твой рабочий токен
TOKEN = "8959905999:AAG53M22ecGCIZf5o0Cguu3jWR4Aap6OxZM"

bot = Bot(token=TOKEN)
# Подключаем MemoryStorage для работы состояний FSM
dp = Dispatcher(storage=MemoryStorage())

# 1. Объявляем состояния (ТЗ твоего друга)
class CaptchaState(StatesGroup):
    waiting_for_answer = State()

# Инициализация БД
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        print(f"Ошибка БД: {e}")
    finally:
        conn.close()

# Команда /start - включает режим ожидания ответа
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    try:
        add_user(message.from_user.id, message.from_user.username)
        
        # Строгий текстовый призыв
        msg = await message.answer(
            "👋 **Привет! Чтобы войти в канал, напиши текстом: сколько будет 2 + 3?**\n\n"
            "Отправь правильную цифру ответным сообщением 👇"
        )
        
        # Включаем состояние ожидания (ТЗ твоего друга)
        await state.set_state(CaptchaState.waiting_for_answer)
        # Запоминаем ID сообщения, чтобы потом удалить его для чистоты чата
        await state.update_data(captcha_msg_id=msg.message_id)
    except Exception as e:
        print(f"❌ Ошибка старта: {e}")

# Хендлер ловит ТЕКСТОВЫЙ ответ от юзера
@dp.message(CaptchaState.waiting_for_answer)
async def process_captcha_text(message: types.Message, state: FSMContext):
    user_answer = message.text.strip()
    user_id = message.from_user.id

    # Проверяем ответ (ловим и цифру 5, и слово пять)
    if user_answer in ["5", "пять", "Пять", "five"]:
        try:
            data = await state.get_data()
            captcha_msg_id = data.get("captcha_msg_id")
            
            # Чистим чат (удаляем вопрос и ответ юзера)
            try:
                await bot.delete_message(chat_id=user_id, message_id=captcha_msg_id)
                await bot.delete_message(chat_id=user_id, message_id=message.message_id)
            except:
                pass
            
            # Закрываем состояние FSM
            await state.clear()
            
            # Генерируем одноразовую ссылку
            target_chat = "-1004407573062" 
            invite_link = await bot.create_chat_invite_link(chat_id=target_chat, expire_date=int(time.time() + 300), member_limit=1)
            
            success_text = (
                "✅ **Проверка успешно пройдена!**\n\n"
                "Ваша персональная ссылка сгенерирована на 5 минут. Жмите кнопку ниже 👇\n\n"
                "🍏 __Для владельцев iPhone:__ Если канал недоступен, включите тумблер «Материалы деликатного характера» в веб-версии Telegram."
            )
            
            inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔥 ВОЙТИ В КАНАЛ 🔞", url=invite_link.invite_link)]
            ])
            
            await bot.send_message(chat_id=user_id, text=success_text, parse_mode=ParseMode.MARKDOWN, reply_markup=inline_keyboard)
            
        except Exception as e:
            print(f"❌ Ошибка FSM генерации: {e}")
    else:
        # Если пишет любую другую фигню — просим подумать еще раз
        await message.answer("❌ Неправильно! Подумай еще раз и напиши правильную цифру:")

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
    
    print("🤖 Бот с текстовым FSM запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
