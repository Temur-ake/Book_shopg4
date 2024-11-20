import asyncio
from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from database import session
from models import User
from filter import IsAdmin, ChatTypeFilter
from state import AdminState
import aiogram.exceptions

# Define the keyboard
manager_panel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Buyurtma Admin Bo'limi"),
         KeyboardButton(text="Mahsulot Admin Bo'limi")],
        [KeyboardButton(text='Reklama')],
    ],
    resize_keyboard=True
)

# Initialize the router
admin_router = Router()

# Define the filters for commands
admin_router.message.filter(ChatTypeFilter([ChatType.PRIVATE]), IsAdmin())


@admin_router.message(CommandStart(), IsAdmin())
async def start_for_admin(message: Message):
    await message.answer('Tanlang', reply_markup=manager_panel_keyboard)


@admin_router.message(F.text == "Mahsulot Admin Bo'limi", IsAdmin())
async def admin(message: Message):
    link = 'http://k.temur.life:8016'
    await message.answer(text=f" Mahsulot Admin Bo'limi ga o'tish {link}")


@admin_router.message(F.text == "Buyurtma Admin Bo'limi", IsAdmin())
async def admin(message: Message):
    link1 = 'https://k.temur.life/admin'
    await message.answer(text=f"Buyurtma Admin Bo'limi ga o'tish {link1}")


@admin_router.message(F.text == "Reklama", IsAdmin())
async def admin(message: Message, state: FSMContext):
    await message.answer("Reklama rasmini kiriting !", reply_markup=manager_panel_keyboard)
    await state.set_state(AdminState.photo)


# Handle photo upload for the ad
@admin_router.message(AdminState.photo, ~F.text, F.photo)
async def admin(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data({"photo": photo})
    await state.set_state(AdminState.title)
    await message.answer("Reklama haqida to'liq malumot bering !", reply_markup=manager_panel_keyboard)


# Handle the title of the ad and send the ad to users
@admin_router.message(AdminState.title, ~F.photo)
async def admin(message: Message, state: FSMContext):
    title = message.text
    await state.update_data({"title": title})

    data = await state.get_data()
    await state.clear()

    # Get users with valid telegram_id
    users = session.query(User).filter(User.telegram_id.isnot(None)).all()

    if not users:
        await message.answer("Hech kimga reklama yuborilmadi. Foydalanuvchilar mavjud emas.")
        return

    tasks = []
    for user in users:
        if user.telegram_id:
            try:
                # Check if the user is a member of the chat (i.e., has not blocked the bot)
                chat_member = await message.bot.get_chat_member(user.telegram_id, user.telegram_id)

                # Skip users who have blocked the bot or left the chat
                if chat_member.status == 'left' or chat_member.status == 'kicked':
                    print(f"User {user.telegram_id} has blocked the bot or left the chat. Skipping.")
                    continue

                # If the user has not blocked the bot, attempt to send the photo
                tasks.append(message.bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=data['photo'],
                    caption=data['title']
                ))

            except aiogram.exceptions.TelegramForbiddenError:
                # Handle the case when the bot is blocked by the user
                print(f"User {user.telegram_id} has blocked the bot. Skipping this user.")
                continue  # Skip this user and continue with the next one

            except aiogram.exceptions.TelegramBadRequest as e:
                # Handle other types of errors (e.g., user not found)
                if "chat not found" in str(e):
                    print(f"User {user.telegram_id} not found. Skipping.")
                else:
                    print(f"Failed to send to user {user.telegram_id}: {e}")
                continue  # Skip this user and continue with the rest
    await message.answer("Reklama yuborildi !")
    # Run all the send tasks concurrently (non-blocked users)
    if tasks:
        await asyncio.gather(*tasks)

    # Notify admin that the ad was sent
