import datetime

from aiogram import F, Router, Bot
from aiogram.enums import ContentType, ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardButton, ReplyKeyboardMarkup, \
    KeyboardButton, Message, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from basket import to_category, basket_msg
from cons import ADMIN_LIST
from _db.database import session
from _db.models import Order, Basket, User
from keyboard import main_keyboard_btn

order_router = Router()


class BasketState(StatesGroup):
    phone_number = State()


async def order_msg(user_telegram_id, order_num):
    with session:
        user = session.execute(
            select(User).where(User.telegram_id == str(user_telegram_id))
        ).scalar_one_or_none()

        if not user:
            return _("Foydalanuvchi topilmadi .")

        user_id = user.id

        order = session.execute(
            select(Order).where(Order.user_id == user_id, Order.id == order_num)
        ).scalar_one_or_none()

        if not order:
            return _("Buyurtma topilmadi .")

        msg = _(
            f'🔢 Buyurtma raqami: <b>{order_num}</b>\n📆 Buyurtma qilingan sana: <b>{order.date_time}</b>\n🟣 Buyurtma holati: <b>{order.order_status}</b>\n')

        all_sum = 0
        products = order.products

        for i, (product_id, details) in enumerate(products.items()):
            summa = int(details['quantity']) * float(details['price'])
            msg += _(
                f'\n{i + 1}. 🛒 Mahsulot nomi: {details["product_name"]} \n{details["quantity"]} x {details["price"]} = {summa} so\'m\n')
            all_sum += summa

        msg += _(f'\n💸 Umumiy narxi: {all_sum} so\'m')
        return msg


from sqlalchemy import delete, String, cast


async def clear_users_basket(user_telegram_id):
    try:
        with session:
            user = session.execute(
                select(User).where(User.telegram_id == str(user_telegram_id))
            ).scalar_one_or_none()

            if not user:
                print(_(f"Bu telegram_id {user_telegram_id} li  foydalanuvchi topilmadi ."))
                return

            session.execute(
                delete(Basket).where(Basket.user_id == user.id)
            )
            session.commit()

            print(f"Bu {user_telegram_id} id li foydalanuvchi  savatchasi tozlandi.")
    except Exception as e:
        print(f"Error clearing basket for user {user_telegram_id}: {str(e)}")


@order_router.callback_query(F.data.startswith('clear'))
async def clear(callback: CallbackQuery):
    await clear_users_basket(callback.from_user.id)
    await to_category(callback)


@order_router.callback_query(F.data.endswith('confirm'))
async def confirm(callback: CallbackQuery, state: FSMContext):
    rkb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=_('📞 Telefon raqam'), request_contact=True)]],
        resize_keyboard=True
    )
    await callback.message.delete()
    await callback.message.answer(_('Telefon raqamingizni qoldiring (📞 Telefon raqam tugmasini bosing)🔽:'),
                                  reply_markup=rkb)
    await state.set_state(BasketState.phone_number)


@order_router.message(F.content_type == ContentType.CONTACT, BasketState.phone_number)
async def phone_number(message: Message, state: FSMContext):
    phone_number = message.contact.phone_number

    if phone_number.startswith('-'):
        phone_number = phone_number[1:]

    await state.update_data(phone_number=phone_number)

    await message.answer(_('Telefon raqamingiz qabul qilindi!'),
                         reply_markup=ReplyKeyboardRemove())

    user_basket = await basket_msg(message.from_user.id)
    if user_basket == "Savat bo'sh.":
        await message.answer(_('Savatda hech qanday mahsulot yo\'q! Iltimos, mahsulot qo\'shing.'))
        return

    msg = user_basket
    msg += _(f'\nTelefon raqamingiz: {phone_number}\n\n<i>Buyurtma berasizmi?</i>')
    ikb = InlineKeyboardBuilder()
    ikb.row(InlineKeyboardButton(text=_("❌ Yo'q"), callback_data='canceled_order'),
            InlineKeyboardButton(text=_('✅ Ha'), callback_data=f'confirm_order-{phone_number}'))
    await message.answer(msg, reply_markup=ikb.as_markup())


@order_router.callback_query(F.data.endswith('canceled_order'))
async def canceled_order(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(_('❌ Buyurtma bekor qilindi'))
    rkb = main_keyboard_btn()
    await callback.message.answer(_('Asosiy menyu'), reply_markup=rkb.as_markup())


@order_router.callback_query(F.data.startswith('confirm_order'))
async def confirm_order(callback: CallbackQuery, bot: Bot):
    await callback.message.delete()

    user_telegram_id = callback.from_user.id

    with session:
        user = session.query(User).filter(cast(User.telegram_id, String) == str(user_telegram_id)).first()

    if not user:
        await callback.message.answer(_('Foydalanuvchi topilmadi!'))
        return

    user_id = user.id

    with session:
        basket_items = session.execute(
            select(Basket)
            .options(joinedload(Basket.product))
            .where((Basket.user_id) == user_id)
        ).scalars().all()

    if not basket_items:
        await callback.message.answer(_('Savatda hech qanday mahsulot yo\'q! Iltimos, mahsulot qo\'shing.'))
        return

    products_data = {}
    total_quantity = 0

    for item in basket_items:
        product = item.product
        product_name = product.name
        price = product.price
        quantity = item.quantity
        product_id = product.id

        if quantity is None or quantity <= 0:
            continue

        products_data[product_id] = {
            'product_name': product_name,
            'quantity': quantity,
            'price': price
        }

        total_quantity += quantity

    if not products_data:
        await callback.message.answer(_('Savatda hech qanday to\'g\'ri mahsulot yo\'q!'))
        return

    with session:
        order = Order(
            user_id=user_id,
            date_time=datetime.datetime.now(),
            order_status='yangi',
            products=products_data,
            phone_number=callback.data[14:],
            quantity=total_quantity
        )
        session.add(order)
        session.commit()

        order = session.execute(
            select(Order).where(Order.user_id == user_id, Order.id == order.id)
        ).scalar_one()

    ikb = InlineKeyboardBuilder()
    ikb.row(
        InlineKeyboardButton(text=_("❌ Yo'q"),
                             callback_data=f'from_admin_canceled_order-{user_telegram_id}-{order.id}'),
        InlineKeyboardButton(text=_('✅ Ha'),
                             callback_data=f'from_admin_order_accept-{user_telegram_id}-{order.id}')
    )

    msg = await order_msg(user_telegram_id, order.id)

    await bot.send_message(
        ADMIN_LIST[0],
        msg + _(
            f"\n\nKlient: +{int(callback.data[14:])} <a href='tg://user?id={callback.from_user.id}'>{callback.from_user.full_name}</a>\nBuyurtmani qabul qilasizmi"),
        parse_mode=ParseMode.HTML,
        reply_markup=ikb.as_markup()
    )

    await callback.message.answer(
        _('✅ Hurmatli mijoz! Buyurtmangiz uchun tashakkur.\nBuyurtma raqami: {orders_num}').format(orders_num=order.id),
        reply_markup=main_keyboard_btn().as_markup(resize_keyboard=True)
    )

    await clear_users_basket(user_telegram_id)


@order_router.callback_query(F.data.startswith('from_admin'))
async def order_accept_canceled(callback: CallbackQuery, bot: Bot):
    user_order = callback.data.split('-')[1:]

    if len(user_order) != 2:
        await callback.message.answer(_('❌ Invalid data received.'))
        return

    user_id, order_id = user_order

    with session:
        user = session.execute(
            select(User).where(User.telegram_id == str(user_id))
        ).scalar_one_or_none()

        if not user:
            await callback.message.answer(_('❌ Bunday foydalanuvchi topilmadi.'))
            return

        order = session.execute(
            select(Order).where(Order.user_id == user.id, Order.id == order_id)
        ).scalar_one_or_none()

        if not order:
            await callback.message.answer(_('❌ Bunday buyurtma topilmadi.'))
            return

        if callback.data.startswith('from_admin_order_accept'):
            order.order_status = 'qabul_qilindi'
            session.commit()

            await bot.send_message(
                user_id,
                _('<i>🎉 Sizning {order_num} raqamli buyurtmangizni admin qabul qildi.</i>').format(order_num=order_id)
            )

            await clear_users_basket(user_id)

            await callback.message.edit_reply_markup()

        else:
            if order:
                session.delete(order)
                session.commit()

            await bot.send_message(
                user_id,
                _('<i>❌ Sizning {order_num} raqamli buyurtmangiz admin tomonidan bekor qilindi.</i>').format(
                    order_num=order_id)
            )

            await callback.message.edit_reply_markup()


@order_router.message(F.text == __('📃 Mening buyurtmalarim'))
async def my_orders(message: Message):
    with session:
        user = session.execute(
            select(User).where(User.telegram_id == str(message.from_user.id))
        ).scalar_one_or_none()

        if not user:
            await message.answer(_('❌ Foydalanuvchi topilmadi!'))
            return

        user_id = user.id

        orders = session.execute(select(Order).where(Order.user_id == user_id))
        user_orders = orders.scalars().all()

        if not user_orders:
            await message.answer(_('🤷‍♂️ Sizda hali buyurtmalar mavjud emas. Yoki bekor qilingan'))
        else:
            for order in user_orders:
                ikb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=_('❌ bekor qilish'),
                                          callback_data=f'from_user_canceled_order-{order.id}')]])
                order_msg_text = await order_msg(message.from_user.id, order.id)
                await message.answer(order_msg_text, reply_markup=ikb)


@order_router.callback_query(F.data.startswith('from_user_canceled_order'))
async def canceled_order(callback: CallbackQuery, bot: Bot):
    await callback.message.delete()
    order_num = callback.data.split('from_user_canceled_order')[-1]

    escaped_order_num = order_num.replace('-', r'')

    with session:
        session.execute(delete(Order).where(Order.id == order_num))
        session.commit()

        await callback.message.answer(_(f'{escaped_order_num} raqamli buyurtmangiz bekor qilindi'))

        await bot.send_message(
            ADMIN_LIST[0],
            f'{escaped_order_num} raqamli buyurtma bekor qilindi\n\nZakaz egasi {callback.from_user.mention_markdown(callback.from_user.full_name)}',
            parse_mode=ParseMode.MARKDOWN_V2
        )
