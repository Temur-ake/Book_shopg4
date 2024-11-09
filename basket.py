import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.exc import IntegrityError

from database import session
from models import Product, Basket, User
from keyboard import show_categories

logging.basicConfig(level=logging.INFO)

basket_router = Router()


async def basket_msg(user_telegram_id):
    try:
        user = session.query(User).filter_by(telegram_id=str(user_telegram_id)).first()

        if not user:
            return _("Foydalanuvchi topilmadi.")

        user_id = user.id

        basket_items = session.query(Basket, Product) \
            .join(Product, Product.id == Basket.product_id) \
            .filter(Basket.user_id == user_id) \
            .all()

        if not basket_items:
            return _("Savat bo'sh.")

        msg = _('🛒 Savat \n\n')
        all_sum = 0

        for i, (basket_item, product) in enumerate(basket_items):
            summa = basket_item.quantity * product.price
            msg += f'{i + 1}. {product.name} \n{basket_item.quantity} x {product.price} = {int(summa)} so\'m\n\n'
            all_sum += summa

        msg += _(f'Jami: {int(all_sum)} so\'m')
        return msg

    except Exception as e:
        logging.error(f"Error fetching basket items: {e}")
        return _("Xato yuz berdi. Iltimos, qayta urinib ko\'ring.")


@basket_router.callback_query(F.data.startswith('categoryga'))
async def to_category(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(_('Kategoriyalardan birini tanlang'),
                                  reply_markup=show_categories(callback.from_user.id))


@basket_router.callback_query(F.data.startswith('clear'))
async def clear_basket(callback: CallbackQuery):
    try:
        user_telegram_id = str(callback.from_user.id)

        with session:
            user = session.query(User).filter(
                User.telegram_id == user_telegram_id).first()

        if not user:
            await callback.message.answer(_('Foydalanuvchi topilmadi!'))
            return

        user_id = user.id

        with session:
            session.query(Basket).filter(Basket.user_id == user_id).delete()
            session.commit()

        await callback.message.edit_text(_('Savat tozalandi!'), reply_markup=show_categories(callback.from_user.id))

    except Exception as e:
        logging.error(f"Error clearing basket for user {callback.from_user.id}: {e}")
        await callback.message.answer(_('Xato yuz berdi. Iltimos, qayta urinib ko\'ring.'))


@basket_router.callback_query(F.data.startswith('savatga'))
async def add_to_basket(callback: CallbackQuery):
    data = callback.data[7:]
    product_id = int(data[:-1])
    quantity = int(data[-1])

    try:
        with session:
            user_telegram_id = str(callback.from_user.id)

            user = session.query(User).filter_by(telegram_id=user_telegram_id).first()
            if not user:
                logging.warning(_(f"Bu {user_telegram_id} telegram_id li foydalanuvchi topilmadi !"))
                return

            product = session.query(Product).filter_by(id=product_id).first()
            if not product:
                logging.warning(_(f"Bu {product_id} li mahsulot topilmadi!"))
                await callback.message.answer(_('Ushbu mahsulot topilmadi. Iltimos qayta urinib ko\'ring.'))
                return

            basket_item = session.query(Basket).filter_by(user_id=user.id, product_id=product_id).first()

            if basket_item:
                basket_item.quantity += quantity
                logging.info(
                    f"Updated basket for user {user_telegram_id}: {basket_item.quantity} x Product ID {product_id}")
            else:
                new_item = Basket(
                    user_id=user.id,
                    product_id=product_id,
                    quantity=quantity
                )
                session.add(new_item)
                logging.info(f"Added new item to basket for user {user_telegram_id}: {product_id} x {quantity}")

            session.commit()

        await callback.message.delete()

        await callback.message.answer(_('Mahsulot savatga qo\'shildi ✅'),
                                      reply_markup=show_categories(callback.from_user.id))



    except IntegrityError as e:
        logging.error(f"IntegrityError while adding to basket: {e.orig}")

    except Exception as e:
        logging.error(f"Error while adding to basket: {e}")


@basket_router.callback_query(F.data.startswith('savat'))
async def basket(callback: CallbackQuery):
    msg = await basket_msg(callback.from_user.id)

    ikb = InlineKeyboardBuilder()
    ikb.row(InlineKeyboardButton(text=_('❌ Savatni tozalash'), callback_data='clear'))
    ikb.row(InlineKeyboardButton(text=_('✅ Buyurtmani tasdiqlash'), callback_data='confirm'))
    ikb.row(InlineKeyboardButton(text=_('◀️ orqaga'), callback_data='categoryga'))

    if callback.message.text:
        await callback.message.edit_text(msg, reply_markup=ikb.as_markup())
    elif callback.message.photo:
        photo = callback.message.photo[0].file_id
        media = InputMediaPhoto(media=photo, caption=msg)
        await callback.message.edit_media(media=media, reply_markup=ikb.as_markup())
    else:
        logging.warning("Message doesn't contain a photo or text to edit.")
