import json
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.client.default import DefaultBotProperties
from collections import defaultdict
import asyncio
import os
from dotenv import load_dotenv
import sys
import atexit

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "-1001234567890"))
SHEVA = os.getenv("SHEVA")
STATS_FILE = "stats.json"



LOCKFILE = "bot.lock"

# Проверка наличия lock-файла
if os.path.exists(LOCKFILE):
    print("⚠️ Бот уже запущен! Завершаю работу.")
    sys.exit()

# Создаём lock-файл
with open(LOCKFILE, "w") as f:
    f.write("running")

# Удаляем lock при выходе
@atexit.register
def cleanup():
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)
        print("🧹 Lock-файл удалён. Бот завершён корректно.")


# Хранилище статистики

# stats = defaultdict(lambda: {"messages": 0, "reactions": 0})
stats = defaultdict(lambda: {"messages": 0})


def save_stats():
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)


def load_stats():
    global stats
    try:
        with open(STATS_FILE, "r") as f:
            data = json.load(f)
            # stats = defaultdict(lambda: {"messages": 0, "reactions": 0}, data)
            stats = defaultdict(lambda: {"messages": 0}, data)

    except FileNotFoundError:
        pass


# Инициализация бота
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


# Команда /start (для тестов в личке)
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("По голове себе постучи..")

    file_id = SHEVA.split("/d/")[1].split("/")[0]
    direct_link = f"https://drive.google.com/uc?export=download&id={file_id}"
    await bot.send_photo(chat_id=GROUP_ID, photo=direct_link)

    # with open("sheva.jpg", "rb") as f:
    #     photo_bytes = f.read()
    #
    # photo = BufferedInputFile(photo_bytes, filename="sheva.jpg")
    # await bot.send_photo(chat_id=GROUP_ID, photo=photo)
    # photo = InputFile("sheva.jpg")
    # await bot.send_photo(GROUP_ID, photo=photo)
    # await bot.send_photo(GROUP_ID, photo='sheva.jpg')

@dp.message(Command("nuchotam"))
async def send_sheva_photo(message: types.Message):
    # sorted_stats = sorted(stats.items(), key=lambda x: x[1]["messages"] + x[1]["reactions"], reverse=True)
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]["messages"], reverse=True)

    if not sorted_stats:
        message = "ВЫ ЧО ПОАХУЕВАЛИ? Чат мертв... никто не писал... СТАТИСТИКИ НЕ БУДЕТ"
        await bot.send_message(GROUP_ID, message)
        return

    report = "<b>📊 ТОП участников за неделю:</b>\n\n"
    for i, (user_id, data) in enumerate(sorted_stats[:5]):
        try:
            user = await bot.get_chat_member(GROUP_ID, int(user_id))
            name = user.user.full_name
        except:
            name = f"Пользователь {user_id}"
        # report += f"{i + 1}. {name} — 💬 {data['messages']} | ❤️ {data['reactions']}\n"
        report += f"{i + 1}. {name} — 💬 {data['messages']}\n"

    await bot.send_message(GROUP_ID, report)


# Обработка входящих сообщений
@dp.message()
async def handle_messages(message: types.Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return

    user_id = str(message.from_user.id)
    stats[user_id]["messages"] += 1
    user = str(message.from_user.first_name)
    print(user, " wrote, new count - ", stats[user_id]["messages"])
    save_stats()

# @dp.edited_message()
# async def on_message_edited(message: types.Message):
#     if message.reactions:
#         print(message.reactions)
#         # message.

# Храним просмотренные сообщения
# seen_messages = set()
#
# async def check_reactions():
#     try:
#         bot.
#         messages = await bot.get_chat_history(chat_id=GROUP_ID, limit=100)
#         for msg in messages:
#             if msg.message_id in seen_messages:
#                 continue
#             seen_messages.add(msg.message_id)
#
#             # Кто автор?
#             if not msg.from_user or not msg.reactions:
#                 continue
#
#             user_id = str(msg.from_user.id)
#             count = 0
#             for r in msg.reactions:
#                 if isinstance(r.type, ReactionTypeEmoji):
#                     count += r.count
#
#             if user_id not in user_stats:
#                 user_stats[user_id] = {"reactions_received": 0}
#             user_stats[user_id]["reactions_received"] += count
#     except Exception as e:
#         print("Ошибка при проверке реакций:", e)

# Рассылка отчета по топу
async def send_weekly_report():
    # sorted_stats = sorted(stats.items(), key=lambda x: x[1]["messages"] + x[1]["reactions"], reverse=True)
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]["messages"], reverse=True)


    if not sorted_stats:
        message = "ВЫ ЧО ПОАХУЕВАЛИ? Чат мертв... никто не писал... СТАТИСТИКИ НЕ БУДЕТ"
        await bot.send_message(GROUP_ID, message)
        return

    report = "<b>📊 ТОП участников за неделю:</b>\n\n"
    for i, (user_id, data) in enumerate(sorted_stats[:5]):
        try:
            user = await bot.get_chat_member(GROUP_ID, int(user_id))
            name = user.user.full_name
        except:
            name = f"Пользователь {user_id}"
        # report += f"{i + 1}. {name} — 💬 {data['messages']} | ❤️ {data['reactions']}\n"
        report += f"{i + 1}. {name} — 💬 {data['messages']}\n"


    await bot.send_message(GROUP_ID, report)

    # Очистить статистику
    stats.clear()
    save_stats()


# Планировщик
def setup_scheduler():
    scheduler = AsyncIOScheduler(timezone=pytz.timezone('Etc/GMT+6'))
    # scheduler.add_job(send_weekly_report, "cron", day_of_week="mon", hour=10, minute=0)
    scheduler.add_job(send_weekly_report, 'interval', minutes=120)
    scheduler.start()


async def main():
    load_stats()
    setup_scheduler()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
