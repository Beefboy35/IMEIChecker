import asyncio


import aiohttp

from aiogram import Bot, Router, types, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, WebAppData, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from async_lru import alru_cache

from Bot.http_client import get_info, get_services, check_imei

from Bot.utils import main_kb, start_btn, inline_admin_kb, add_to_whitelist, \
    access_check, remove_from_whitelist, check_for_user_in_wl, get_whitelist, format_info

from src.config import settings

router = Router()


class Form(StatesGroup):
    add_user_id = State()
    remove_user_id = State()
    get_service_id = State()
    service_id = State()
    deviceId = State()
WEB_APP_URL = "https://1e8c-185-193-51-54.ngrok-free.app"

@router.message(CommandStart())
@access_check  # декоратор который проверяет находится ли юзер в whitelist (или он админ) или нет, если нет - функционал бота недоступен
async def get_start(msg: types.Message):
    await msg.answer(
        f"Welcome {msg.from_user.full_name}! I can give you some information about your device with IMEI!",
        reply_markup=start_btn())
    web_app = WebAppInfo(url=WEB_APP_URL)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Открыть веб-приложение", web_app=web_app)]])
    await msg.answer("Запустите веб-приложение:", reply_markup=keyboard)



@router.message(F.text.in_(["🏎 Let's go!", "◀️ Back"]))
@access_check
async def get_menu(msg: types.Message):
    await msg.answer("🎇🎇🎇", reply_markup=main_kb(msg.from_user.id))


@router.message(F.text == "👤 Author")
@access_check
async def get_author(msg: types.Message):
    link = f"https://t.me/RealBeefBoy"
    await msg.answer(f"Here is the author's account: {link}")


@router.message(F.text == "🆔 Get ID")
@access_check
async def get_id(msg: types.Message):
    await msg.answer(f"Your ID: {msg.from_user.id}")

@alru_cache(maxsize=1)
async def cached_get_services(api_key: str):
    return await get_services(api_key)

@router.message(F.text == "📑 Services")
@access_check
async def get_imei_acc(msg: types.Message):
    try:
        result = await cached_get_services(settings.LIVE_API_KEY)
        # красиво отображаем список услуг
        await msg.answer(
            f"List of the services:\n {"\n".join([f"{i}. {j.strip("{}")}" for i, j in enumerate(map(str, result), 1)])}"
        )
    except aiohttp.ClientError as e:
        print({"error": f"API request failed: {type(e).__name__}, details: {e}"})
        await msg.answer("Something went wrong")
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}, details: {e}")
        await msg.answer("Something went wrong")


@router.message(F.text == "🖥 Service description")
@access_check
async def get_service_id(msg: types.Message, state: FSMContext):
    await state.set_state(Form.get_service_id)
    await msg.answer("Type service's id:")


@router.message(Form.get_service_id)
@access_check
async def get_extra_info(msg: Message, state: FSMContext):
    try:
        service_id = int(msg.text)
        await state.clear()
        info = await get_info(settings.LIVE_API_KEY, service_id)
        # красиво отображаем описание услуги c помощью format_info()
        await msg.answer(format_info(info))
    except aiohttp.ClientError as e:
        print({"error": f"API request failed: {type(e).__name__}, details: {e}"})
        await msg.answer("Something went wrong")
    except ValueError as v:
        await msg.answer(str(v))
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}, details: {e}")
        await msg.answer("Something went wrong")

# Обработчик для начала процесса проверки IMEI
@router.message(F.text == "✅ Check IMEI")
@access_check
async def preprocessing_imei(msg: Message, state: FSMContext):
    await state.set_state(Form.deviceId)
    await msg.answer("Give me your IMEI:")

# Обработчик для получения IMEI
@router.message(Form.deviceId)
@access_check
async def get_imei(msg: Message, state: FSMContext):
    imei = msg.text
    await state.update_data(deviceId=imei)  # Сохраняем IMEI в состояние
    await state.set_state(Form.service_id)
    await msg.answer("Give me service's id:")

# Обработчик для получения service_id и выполнения проверки IMEI
@router.message(Form.service_id)
@access_check
async def get_info_by_imei(msg: Message, state: FSMContext):
    service_id = msg.text
    if not service_id.isdigit():  # Проверяем, что service_id является числом
        await msg.answer("Service ID must be a number. Please try again.")
        return

    # Получаем сохраненный IMEI из состояния
    data = await state.get_data()
    imei = data.get("deviceId")

    # Выполняем проверку IMEI
    try:
        info = await check_imei(imei, int(service_id), settings.LIVE_API_KEY)
        await msg.answer(str(info))
    except Exception as e:
        print(f"Error: {type(e).__name__}, details: {e}")
        await msg.answer(str(e))
    finally:
        await state.clear()


@router.message(F.text == "⚙️ Admin panel")
@access_check
async def get_admin(msg: types.Message):
    await msg.answer("Welcome admin!", reply_markup=inline_admin_kb())


@router.message(F.text == "🤍 Add user to whitelist")
@access_check
async def user_add(msg: types.Message, state: FSMContext):
    await state.set_state(Form.add_user_id)
    await msg.answer("Type user's id to add:")


@router.message(Form.add_user_id)
@access_check
async def add_by_id(msg: Message, state: FSMContext):
    try:
        if len(msg.text) == 10 and msg.text.isdigit():
            user_id = int(msg.text)
            await state.update_data(name=add_to_whitelist(user_id))
            await state.clear()
            await msg.answer(f"User with id {user_id} added to whitelist")
        else:
            await state.clear()
            await msg.answer("Invalid user id, try again")
    except TypeError as t:
        print(f"ValueError: {t}")
        await msg.answer("ID must be a 10-digit number")
    except Exception as e:
        print(f"Error: {type(e).__name__}, details: {e}")
        await msg.answer(str(e))


@router.message(F.text == "❌ Remove user from whitelist")
@access_check
async def user_remove(msg: types.Message, state: FSMContext):
    await state.set_state(Form.remove_user_id)
    await msg.answer("Type user's id to remove:")


@router.message(Form.remove_user_id)
@access_check
async def remove_by_id(msg: Message, state: FSMContext):
    try:
        if len(msg.text) == 10:
            if check_for_user_in_wl(int(msg.text)):
                await state.update_data(name=remove_from_whitelist(int(msg.text)))
                await state.clear()
                await msg.answer(f"User with id {msg.text} removed from whitelist")
            else:
                await state.clear()
                await msg.answer("User is not in whitelist, try again")
        else:
            await msg.answer("Invalid ID")
    except ValueError as v:
        print(f"ValueError: {v}")
        await msg.answer("ID must be a 10-digit number")


@router.message(F.text == "📖 Get all allowed users")
@access_check
async def get_all_users_in_wl(msg: Message):
    await msg.answer("Here you go🌝")
    await msg.answer(get_whitelist())




@router.message()
@access_check
async def unknown_message(msg: types.Message):
    await msg.answer("Unknown command, please choose one")


async def main():
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
