from aiogram.types import KeyboardButton, InlineKeyboardButton, BotCommand, WebAppInfo
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy.future import select

from database import session
from models import Category, Basket, User


def show_categories(user_id):
    ikb = InlineKeyboardBuilder()

    categories = session.execute(select(Category)).scalars().all()

    for category in categories:
        ikb.add(InlineKeyboardButton(text=category.name, callback_data=str(category.id)))

    ikb.add(InlineKeyboardButton(text=_('🔍 Qidirish'), switch_inline_query_current_chat=''))

    user = session.query(User).filter_by(telegram_id=str(user_id)).first()

    if not user:
        return _("Foydalanuvchi topilmadi.")

    user_id = user.id

    basket_items = session.query(Basket) \
        .filter(Basket.user_id == user_id) \
        .all()

    basket_count = len(basket_items)

    if basket_count > 0:
        ikb.add(InlineKeyboardButton(text=f'🛒 Savat ({basket_count})', callback_data='savat'))

    ikb.adjust(2, repeat=True)

    return ikb.as_markup()


def main_keyboard_btn(**kwargs):
    main_keyboard = ReplyKeyboardBuilder()
    main_keyboard.row(KeyboardButton(text=_('🛒 Mahsulotlar', **kwargs)),
                      KeyboardButton(text=_('📃 Mening buyurtmalarim', **kwargs))
                      )
    main_keyboard.row(
        KeyboardButton(text=_('🔵 Biz ijtimoyi tarmoqlarda', **kwargs)),
        KeyboardButton(text=_('📞 Biz bilan bog\'lanish', **kwargs))
    )
    main_keyboard.row(KeyboardButton(text=_('🌐 Tilni almashtirish', **kwargs)))
    main_keyboard.row(KeyboardButton(text=_('🔉 Sayt Orqali Buyurtma'), web_app=WebAppInfo(url='https://k.temur.life')))
    return main_keyboard


c_lis = [
    BotCommand(command='start', description='Botni boshlash'),
    BotCommand(command='help', description='Yordam'),
]
