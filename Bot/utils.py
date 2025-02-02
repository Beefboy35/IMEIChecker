import sqlite3
from functools import wraps


from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, \
    Message
from sqlite3 import IntegrityError
from src.config import settings


def main_kb(user_telegram_id: int):
    kb_list = [
        [KeyboardButton(text="🖥 Service description"), KeyboardButton(text="✅ Check IMEI")],
        [KeyboardButton(text="👤 Author"),
        KeyboardButton(text="📑 Services"),
        KeyboardButton(text="🆔 Get ID")]
    ]
    if check_admin(user_telegram_id):
        kb_list.append([KeyboardButton(text="⚙️ Admin panel")])
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list,
                                   resize_keyboard=True,
                                   input_field_placeholder="Choose command:"
    )
    return keyboard

def start_btn():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🏎 Let's go!")]], resize_keyboard=True, one_time_keyboard=True)



def inline_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Author's telegram", url='https://t.me/RealBeefBoy')],
        [InlineKeyboardButton(text="1", web_app=WebAppInfo(url="https://api.imeicheck.net/v1/services"))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def validate_input(msg: Message, expected_length: int = None, is_digit: bool = False) -> bool:
    if expected_length and len(msg.text) != expected_length:
        return False
    if is_digit and not msg.text.isdigit():
        return False
    return True
def inline_admin_kb():
    inline_kb_list = [
        [KeyboardButton(text="🤍 Add user to whitelist"),
         KeyboardButton(text="❌ Remove user from whitelist")],
         [KeyboardButton(text="📖 Get all allowed users"),
        KeyboardButton(text="◀️ Back")]
    ]
    return ReplyKeyboardMarkup(keyboard=inline_kb_list, resize_keyboard=True)

def check_admin(telegram_id: int):
    try:
        if not telegram_id in settings.ADMINS_LIST:
            return False
        return True
    except Exception as e:
       print(f"Error {type(e).__name__}, details: {e}")

def check_for_user_in_wl(telegram_id: int):
    with sqlite3.connect('../telebot.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT telegram_id FROM whitelist WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        if result:
            return True
        return False


def add_to_whitelist(telegram_id: int):
    try:
        with sqlite3.connect('../telebot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO whitelist (telegram_id) VALUES (?)', (telegram_id,))
            conn.commit()

    except sqlite3.IntegrityError:
        print(f"User with telegram_id {telegram_id} is already in the whitelist.")
        raise IntegrityError("User is already in whitelist")

    except Exception as e:
        print(f"{type(e).__name__} error occurred while adding user to whitelist: {e}")




def remove_from_whitelist(telegram_id: int):
    try:
        with sqlite3.connect('../telebot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM whitelist WHERE telegram_id = ?', (telegram_id,))
            conn.commit()
            rows_affected = cursor.rowcount
            if rows_affected > 0:
                print(f"User with id {telegram_id} deleted")
            else:
                print(f"User with id {telegram_id} is not in whitelist")

    except sqlite3.Error as e:
        print(f"Database error while removing user from whitelist: {e}")
    except Exception as e:
        print(f"{type(e).__name__} occurred while removing user from whitelist: {e}")


def get_whitelist():
    try:
        with sqlite3.connect('../telebot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT telegram_id FROM whitelist')
            wl = cursor.fetchall()
            if wl:
                # отображаем список юзеров в whitelist красиво) enumerate позволяет сделать нумерованный список из allowed users
                return "\n".join([f"{j}. {i}" for j, i in enumerate(map(str, [item[0] for item in wl]), 1)])
            else:
                return "Whitelist is empty"
    except sqlite3.Error as e:
        print(f"Database error: {e}")


# декторатор для проверки валидности id юзера

def access_check(func):
    @wraps(func)
    async def wrapper(msg: Message, *args, **kwargs):
        if not check_for_user_in_wl(msg.from_user.id) and msg.from_user.id not in settings.ADMINS_LIST:
            await msg.answer(f"Access denied, you're not in the whitelist. Your ID: {msg.from_user.id}", reply_markup=start_btn())
            return
        return await func(msg, *args, **kwargs)
    return wrapper

def format_info(data):
    """Formats the info dictionary for a Telegram message (plain text)."""
    properties_str = ""
    for key, value in data['properties'].items():
      properties_str += f"{key}: {value}\n"
    message = f"""
Title: {data['title']}
Price: {data['price']}
Description: {data['description']}

Device Properties:
{properties_str}
"""
    return message