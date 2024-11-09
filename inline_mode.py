from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import logging
from sqlalchemy.future import select
from database import session
from models import Product

inline_router = Router()


# Handle inline query (search and no search)
@inline_router.inline_query()
async def user_inline_handler(inline_query: InlineQuery):
    try:
        # Use async session handling correctly
        with session:
            if inline_query.query == "":
                # When query is empty, show all products
                result = session.execute(select(Product))
                products = result.scalars().all()

                inline_list = []
                for i, product in enumerate(products):
                    # Handle missing or invalid image URLs
                    image_url = product.image_url if product.image_url and product.image_url.startswith(
                        ('http://', 'https://')) else 'https://via.placeholder.com/150'

                    inline_list.append(InlineQueryResultArticle(
                        id=str(product.id),
                        title=product.name,
                        input_message_content=InputTextMessageContent(
                            message_text=f"product_{product.id}"
                        ),
                        thumbnail_url=image_url,  # Use the validated image_url
                        description=f"{product.name} - 💵 Narxi: {product.price} so'm",
                    ))
                    if i == 50:  # Limit to 50 results
                        break

                await inline_query.answer(inline_list)

            else:
                # Filter products based on query (case-insensitive search)
                result = session.execute(
                    select(Product).where(Product.name.ilike(f"%{inline_query.query.lower()}%"))
                )
                products = result.scalars().all()

                inline_list = []
                for i, product in enumerate(products):
                    # Handle missing or invalid image URLs
                    image_url = product.image_url if product.image_url and product.image_url.startswith(
                        ('http://', 'https://')) else 'https://via.placeholder.com/150'

                    inline_list.append(InlineQueryResultArticle(
                        id=str(product.id),
                        title=product.name,
                        input_message_content=InputTextMessageContent(
                            message_text=f"product_{product.id}"  # Pass the product ID to the next step
                        ),
                        thumbnail_url=image_url,  # Use the validated image_url
                        description=f"{product.name} - 💵 Narxi: {product.price} so'm",
                    ))
                    if i == 50:
                        break

                await inline_query.answer(inline_list)

    except Exception as e:
        logging.basicConfig(level=logging.ERROR)
        logger = logging.getLogger(__name__)
        logger.error(f"Error handling inline query: {e}")
