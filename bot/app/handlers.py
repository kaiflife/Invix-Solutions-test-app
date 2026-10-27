import logging

import aiohttp
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from app.config import settings

logger = logging.getLogger(__name__)
router = Router()


class AddProduct(StatesGroup):
    waiting_for_photo = State()


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids_list


def get_main_keyboard(user_is_admin: bool) -> InlineKeyboardMarkup:
    """Генерирует главную клавиатуру (каталог + опционально кнопка админа)."""
    buttons = [
        [
            InlineKeyboardButton(
                text="🛍 Открыть каталог", web_app=WebAppInfo(url=settings.webapp_url)
            )
        ]
    ]
    if user_is_admin:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="➕ Создать товар", callback_data="create_product"
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_products_count() -> int:
    """Запрашивает количество товаров у API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.api_url}/api/products") as response:
                if response.status == 200:
                    products = await response.json()
                    return len(products)
    except Exception as e:
        logger.error(f"Ошибка при проверке товаров: {e}")
    return 0


async def send_catalog_message(message: Message):
    """Централизованная отправка сообщения с каталогом."""
    user_is_admin = is_admin(message.from_user.id)
    count = await get_products_count()

    if count > 0:
        text = "У меня есть товар! Откройте каталог, чтобы посмотреть ассортимент."
    else:
        text = "У меня пока нет товаров в каталоге."

    await message.answer(text, reply_markup=get_main_keyboard(user_is_admin))


# --- ОБРАБОТЧИКИ ---


@router.message(CommandStart())
async def cmd_start(message: Message):
    await send_catalog_message(message)


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message, state: FSMContext):
    # Если пользователь просто пишет (и мы не ждем от него фото)
    if await state.get_state() is None:
        await send_catalog_message(message)


@router.callback_query(F.data == "create_product")
async def process_create_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав.", show_alert=True)
        return

    await state.set_state(AddProduct.waiting_for_photo)
    await callback.answer()

    # Отправляем сообщение и сразу удаляем предыдущую клавиатуру (опционально)
    await callback.message.answer(
        "Отправьте фото товара с названием в подписи (caption)."
    )


@router.message(AddProduct.waiting_for_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    title = message.caption
    if not title:
        await message.answer(
            "❌ Пожалуйста, отправьте фото с подписью (названием товара)."
        )
        return

    photo = message.photo[-1]  # Берем максимальное качество
    await message.answer("⏳ Загружаю товар...")

    try:
        # 1. Получаем информацию о файле
        file_info = await message.bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{settings.bot_token}/{file_info.file_path}"

        url = f"{settings.api_url}/api/products"

        # 2. Используем aiohttp для стриминга файла напрямую в наш API
        # Это экономит RAM, так как файл не загружается целиком в память бота
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as tg_response:
                if tg_response.status != 200:
                    raise Exception("Не удалось скачать файл из Telegram")

                # Формируем multipart-запрос
                form = aiohttp.FormData()
                form.add_field("title", title)
                # Передаем поток (tg_response.content), а не байты
                form.add_field(
                    "image",
                    tg_response.content,
                    filename="photo.jpg",
                    content_type="image/jpeg",
                )

                async with session.post(url, data=form) as api_response:
                    if api_response.status == 200:
                        await message.answer(f"✅ Товар «{title}» успешно добавлен!")
                        await state.clear()
                    else:
                        error_text = await api_response.text()
                        await message.answer(f"❌ Ошибка сервера: {error_text}")

    except Exception as e:
        logger.error(f"Ошибка при загрузке фото: {e}")
        await message.answer(f"❌ Ошибка соединения: {str(e)}")
