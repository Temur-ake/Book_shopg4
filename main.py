import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.i18n import I18n, FSMI18nMiddleware
from sqlalchemy import select

from admin import admin_router
from basket import basket_router
from cons import TOKEN
from db.database import session
from db.models import Category, Product
from handlers import main_router
from inline_mode import inline_router
from keyboard import c_lis
from order import order_router

dp = Dispatcher()


async def on_startup(bot: Bot):
    category = select(Category)
    cat = session.execute(category).scalars().first()

    product = session.execute(select(Product))
    pro = product.scalars().first()
    if not cat:
        logging.info("No categories found.")
    if not pro:
        logging.info("No products found.")

    await bot.set_my_commands(c_lis)


async def on_shutdown(bot: Bot):
    await bot.delete_my_commands()


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    i18n = I18n(path='locales')
    dp.update.outer_middleware.register(FSMI18nMiddleware(i18n))
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_routers(
        inline_router,
        admin_router,
        basket_router,
        order_router,
        main_router,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
