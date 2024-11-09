import logging

from aiogram import F
from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from sqlalchemy.future import select

from _db.database import session
from _db.models import Product, Category, User, Basket
from keyboard import show_categories, main_keyboard_btn
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

logging.basicConfig(level=logging.INFO)

main_router = Router()


@main_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    rkb = main_keyboard_btn()
    msg = _('Assalomu alaykum! Tanlang.')

    with session:
        user = session.execute(select(User).where(User.telegram_id == str(message.from_user.id)))
        user = user.scalar_one_or_none()

        if user is None:
            msg = _('Assalomu alaykum! \nXush kelibsiz!')

            username = message.from_user.username if message.from_user.username else f"user_{message.from_user.id}"

            new_user = User(
                telegram_id=str(message.from_user.id),
                username=username,
                phone_number=None,
                balance=0,
                user_type='user'
            )

            session.add(new_user)
            session.commit()

    await message.answer(text=msg, reply_markup=rkb.as_markup(resize_keyboard=True))


@main_router.message(Command(commands='help'))
async def help_command(message: Message) -> None:
    await message.answer(_('''Buyruqlar:
/start - Botni ishga tushirish
/help - Yordam'''))


@main_router.message(F.text == __('🌐 Tilni almashtirish'))
async def change_language(message: Message) -> None:
    keyboards = InlineKeyboardBuilder()
    keyboards.row(InlineKeyboardButton(text='Uz🇺🇿', callback_data='lang_uz'),
                  InlineKeyboardButton(text='En🇬🇧', callback_data='lang_en'),
                  InlineKeyboardButton(text='Ru🇷🇺', callback_data='lang_ru'))

    await message.answer(_('Tilni tanlang: '), reply_markup=keyboards.as_markup())


@main_router.callback_query(F.data.startswith('lang_'))
async def languages(callback: CallbackQuery, state: FSMContext) -> None:
    lang_code = callback.data.split('lang_')[-1]
    await state.update_data(locale=lang_code)

    lang = _('Uzbek', locale=lang_code) if lang_code == 'uz' else \
        _('Ingiliz', locale=lang_code) if lang_code == 'en' else \
            _('Rus', locale=lang_code)

    await callback.answer(_('{lang} tili tanlandi', locale=lang_code).format(lang=lang))

    rkb = main_keyboard_btn(locale=lang_code)
    msg = _('Assalomu alaykum! Tanlang.', locale=lang_code)
    await callback.message.answer(text=msg, reply_markup=rkb.as_markup(resize_keyboard=True))


@main_router.message(F.text == __('🔵 Biz ijtimoyi tarmoqlarda'))
async def our_social_network(message: Message) -> None:
    ikb = InlineKeyboardBuilder()
    ikb.row(InlineKeyboardButton(text='| 1000 xil Online Bozor |', url='https://t.me/@onlinebozor1000xil'))
    ikb.row(InlineKeyboardButton(text='| 1000 xil Online Bozor Bot |', url='https://t.me/@temurs_book_shop_bot'))
    ikb.row(InlineKeyboardButton(text='| 1000 xil |', url='https://k.temur.life'))
    await message.answer(_('Biz ijtimoiy tarmoqlarda'), reply_markup=ikb.as_markup())


@main_router.message(F.text == __('🛒 Mahsulotlar'))
async def books(message: Message) -> None:
    ikb = show_categories(message.from_user.id)

    await message.answer(_('Kategoriyalardan birini tanlang'), reply_markup=ikb)


@main_router.callback_query(F.data.startswith('orqaga'))
async def back_handler(callback: CallbackQuery):
    with session:
        await callback.message.edit_text(_('Kategoriyalardan birini tanlang'),
                                         reply_markup=show_categories(
                                             callback.from_user.id))


@main_router.message(F.text == __("📞 Biz bilan bog'lanish"))
async def message(message: Message) -> None:
    text = _("""\n
\n
Telegram: @C_W24\n
📞  +{number}\n
🤖 Bot Kozimov Temur (@C_W24) tomonidan tayorlandi.\n""".format(number=998970501655))
    await message.answer(text=text, parse_mode=ParseMode.HTML)


@main_router.message(lambda msg: msg.text.startswith('product_'))
async def answer_inline_query(message: Message):
    product_id = message.text.split('_')[1]

    with session:
        product = session.execute(select(Product).filter(Product.id == product_id)).scalar_one_or_none()

    if product:
        image_url = product.image_url
        if not image_url or not image_url.startswith('http'):
            logging.error(f"Invalid image URL for product {product_id}: {image_url}")
            image_url = 'https://via.placeholder.com/150'

        ikb = InlineKeyboardBuilder()
        ikb.row(
            InlineKeyboardButton(text=_("◀️Orqaga"), callback_data="categoryga"),
            InlineKeyboardButton(text=_('🛒 Savatga qo\'shish'), callback_data=f"savatga_{product_id}_1")
        )

        await message.delete()

        await message.answer_photo(
            photo=image_url,
            caption=f"<b>{product.name}</b>\n\n{product.description}\n\nNarxi: {product.price} so'm",
            reply_markup=ikb.as_markup(parse_mode="HTML")
        )
    else:
        await message.answer(_("Mahsulot topilmadi."))


@main_router.callback_query()
async def product_handler(callback: CallbackQuery):
    with session:
        categories = session.execute(select(Category)).scalars().all()
        category_dict = {category.id: category for category in categories}

        products = session.execute(select(Product)).scalars().all()
        product_dict = {product.id: product for product in products}

        if callback.data.startswith('product-'):
            product_id = int(callback.data.split('-')[1])
            product = product_dict[product_id]

            image_url = product.image_url
            if not image_url or not image_url.startswith('http'):
                logging.error(f"Invalid image URL for product {product_id}: {image_url}")
                image_url = 'https://via.placeholder.com/150'

            ikb = InlineKeyboardBuilder()
            ikb.row(
                InlineKeyboardButton(text=_("◀️Orqaga"), callback_data="categoryga"),
                InlineKeyboardButton(text=_('🛒 Savatga qo\'shish'), callback_data=f"savatga{product_id}{str(1)}")
            )

            await callback.message.delete()

            await callback.message.answer_photo(
                name=product.name,
                photo=image_url,
                caption=f"{product.description}\n\nNarxi: {int(product.price)} so'm",
                reply_markup=ikb.as_markup()
            )

        elif int(callback.data) in category_dict:
            category_id = int(callback.data)
            category_name = category_dict[category_id].name

            ikb = InlineKeyboardBuilder()

            for product in products:
                if product.category_id == category_id:
                    ikb.add(InlineKeyboardButton(text=product.name, callback_data=f'product-{product.id}'))

            basket_items = session.execute(
                select(Basket)
                .join(User, User.id == Basket.user_id)
                .where(User.telegram_id == str(callback.from_user.id))
            ).scalars().all()
            if basket_items:
                total_quantity = sum(item.quantity for item in basket_items)
                ikb.add(InlineKeyboardButton(text=_(f'🛒 Savat ({total_quantity})'), callback_data='savat'))

            ikb.add(InlineKeyboardButton(text=_("◀️ orqaga"), callback_data='orqaga'))
            ikb.adjust(2, repeat=True)

            if callback.message.text != category_name or callback.message.reply_markup != ikb.as_markup():
                await callback.message.edit_text(category_name, reply_markup=ikb.as_markup())
            else:

                logging.info("Message content or markup is the same, skipping edit.")
