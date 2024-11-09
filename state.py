from aiogram.fsm.state import StatesGroup, State
import aiohttp


class FormState(StatesGroup):
    category = State()
    product_name = State()
    product_price = State()
    product_image = State()
    product_text = State()
    product_category = State()
    delete_category = State()
    show_category = State()
    delete_product = State()


class AdminState(StatesGroup):
    title = State()
    photo = State()
    end = State()


async def make_url(img_bytes):
    url = 'https://telegra.ph/upload'
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data={'file': img_bytes}) as response:
            if response.status == 200:
                data = await response.json()
                image_url = "https://telegra.ph" + data[0]['src']
                return image_url
            else:
                print(f"Error uploading file: {response.status}")
                return None
