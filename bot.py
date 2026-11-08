import asyncio
import json
import os
import random
import sys
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    WebAppInfo,
)

# Принудительный UTF-8 для Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"bot_token": "", "admin_id": None, "webapp_url": "http://localhost:8085/index.html"}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()
BOT_TOKEN = config.get("bot_token", "").strip()
ADMIN_ID = config.get("admin_id")
WEBAPP_URL = config.get("webapp_url", "http://localhost:8085/index.html").strip()

dp = Dispatcher()

def get_main_keyboard(url: str):
    if url.startswith("https://"):
        booking_btn = InlineKeyboardButton(
            text="✂️ Онлайн-запись в BladeCraft",
            web_app=WebAppInfo(url=url)
        )
    else:
        booking_btn = InlineKeyboardButton(
            text="✂️ Онлайн-запись в BladeCraft (Браузер)",
            url=url
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [booking_btn],
            [
                InlineKeyboardButton(text="💈 Барберы и прайс", callback_data="info_services"),
                InlineKeyboardButton(text="📍 Локация", callback_data="info_location")
            ],
            [
                InlineKeyboardButton(text="📞 Связаться с администратором", callback_data="info_contact")
            ]
        ]
    )

@dp.message(CommandStart())
async def cmd_start(message: types.Message, bot: Bot):
    user_name = message.from_user.first_name

    # Настраиваем постоянную кнопку меню в левом нижнем углу Телеграма (только если HTTPS)
    if WEBAPP_URL.startswith("https://"):
        try:
            await bot.set_chat_menu_button(
                chat_id=message.chat.id,
                menu_button=MenuButtonWebApp(
                    text="Запись ✂️",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            )
        except Exception as e:
            print(f"[!] Не удалось установить MenuButton: {e}")

    welcome_text = (
        f"💈 <b>Добро пожаловать в пространство BladeCraft, {user_name}!</b>\n\n"
        f"Премиальный барбершоп в Новороссийске. Безупречная геометрия фейдов, "
        f"опасное бритье и авторский мужской уход.\n\n"
        f"• <b>Fade / Crop / Classic стрижки</b>\n"
        f"• <b>Моделирование бороды опасной бритвой</b>\n"
        f"• <b>Комплексы и SPA-уход за лицом</b>\n\n"
        f"Нажмите кнопку ниже, чтобы выбрать услугу, мастера и забронировать удобное время:"
    )

    await message.answer(
        text=welcome_text,
        reply_markup=get_main_keyboard(WEBAPP_URL),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data == "info_services")
async def cb_services(callback: types.CallbackQuery):
    text = (
        "💈 <b>Основные услуги BladeCraft:</b>\n\n"
        "• <b>Мужская стрижка</b> — 1 800 ₽ (45 мин)\n"
        "• <b>Моделирование бороды</b> — 1 300 ₽ (35 мин)\n"
        "• <b>Комплекс Стрижка + Борода</b> — 2 700 ₽ (75 мин)\n"
        "• <b>SPA-уход & Black Mask</b> — 1 200 ₽ (30 мин)\n"
        "• <b>Отец + Сын</b> — 3 100 ₽ (60 мин)\n\n"
        "В стоимость включены: премиальное мытье, стайлинг и напитки в зоне отдыха."
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "info_location")
async def cb_location(callback: types.CallbackQuery):
    text = (
        "📍 <b>Локация BladeCraft:</b>\n"
        "г. Новороссийск, Набережная им. Адмирала Серебрякова, 27\n\n"
        "🕒 <b>Режим работы:</b>\n"
        "Ежедневно: с 10:00 до 22:00\n\n"
        "☕ Комфортная лаунж-зона, кофе, прохладительные напитки и удобная парковка."
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "info_contact")
async def cb_contact(callback: types.CallbackQuery):
    text = (
        "📞 <b>Контакты администратора:</b>\n"
        "• Телефон: <code>+7 (999) 000-00-00</code>\n"
        "• Telegram: @qavalerdsg\n\n"
        "Если вы задерживаетесь или хотите перенести запись — напишите нам."
    )
    await callback.message.answer(text, parse_mode=ParseMode.HTML)
    await callback.answer()

# ОБРАБОТЧИК ДАННЫХ ИЗ TELEGRAM MINI APP
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message, bot: Bot):
    raw_data = message.web_app_data.data

    try:
        data = json.loads(raw_data)
        booking_id = data.get("booking_id", f"BC-{random.randint(1000, 9999)}")
        client = data.get("client", message.from_user.first_name)
        phone = data.get("phone", "Не указан")
        services = data.get("services", [])
        master = data.get("master", "Любой свободный мастер")
        datetime_str = data.get("datetime", "Ближайшее время")
        total = data.get("total", 0)
    except Exception as e:
        print(f"[!] Ошибка разбора данных WebApp: {e}")
        booking_id = f"BC-{random.randint(1000, 9999)}"
        client = message.from_user.first_name
        phone = "Не указан"
        services = [raw_data]
        master = "Мастер"
        datetime_str = "По согласованию"
        total = "По прайсу"

    services_str = "\n".join([f"  • {s}" for s in services]) if services else "  • Мужская стрижка"

    # 1. Чек / билет клиенту
    client_receipt = (
        f"✂️ <b>ЗАПИСЬ #{booking_id} УСПЕШНО ОФОРМЛЕНА!</b>\n\n"
        f"👤 <b>Гость:</b> {client} (<code>{phone}</code>)\n"
        f"💈 <b>Барбер:</b> <b>{master}</b>\n"
        f"📅 <b>Дата и время:</b> <b>{datetime_str}</b>\n\n"
        f"📋 <b>Выбранные услуги:</b>\n"
        f"{services_str}\n\n"
        f"💳 <b>Итого к оплате:</b> <b>{total} ₽</b>\n"
        f"📍 <b>Адрес:</b> г. Новороссийск, Набережная им. Адмирала Серебрякова, 27\n\n"
        f"<i>Ждем вас! Приходите за 5–10 минут до визита, чтобы выпить кофе в зоне отдыха.</i>"
    )

    await message.answer(client_receipt, parse_mode=ParseMode.HTML)

    # 2. Уведомление администратору/барберу
    if ADMIN_ID:
        admin_alert = (
            f"🔔 <b>НОВАЯ ЗАПИСЬ #{booking_id}!</b>\n\n"
            f"👤 <b>Клиент:</b> @{message.from_user.username or 'нет_юзернейма'} ({client})\n"
            f"📞 <b>Телефон:</b> <code>{phone}</code>\n"
            f"💈 <b>Мастер:</b> {master}\n"
            f"📅 <b>Время:</b> {datetime_str}\n\n"
            f"📋 <b>Услуги:</b>\n{services_str}\n\n"
            f"💰 <b>Сумма:</b> <b>{total} ₽</b>"
        )
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=admin_alert, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"[!] Не удалось отправить алерт админу: {e}")

async def start_web_server():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()

    async def handle_ping(request):
        return web.Response(text="BladeCraft Bot is running!")

    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[*] Web Health-Check запущен на порту {port}")

async def main():
    if not BOT_TOKEN:
        print("=" * 65)
        print("[!] ОШИБКА: bot_token пустой в файле config.json!")
        print("1. Перейдите в Telegram к @BotFather")
        print("2. Создайте нового бота через команду /newbot")
        print("3. Вставьте полученный токен в config.json в поле 'bot_token'")
        print("=" * 65)
        return

    bot = Bot(token=BOT_TOKEN)
    me = await bot.get_me()
    print("=" * 65)
    print(f" 💈 BladeCraft Telegram Bot запущен: @{me.username} ({me.first_name})")
    print(f" WebApp URL: {WEBAPP_URL}")
    print(" Ожидаю команды и онлайн-записи гостей...")
    print("=" * 65)

    try:
        await start_web_server()
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nBladeCraft Bot остановлен.")
