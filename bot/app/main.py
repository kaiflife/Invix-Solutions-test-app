import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.config import settings
from app.handlers import router

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # КРИТИЧНО ДЛЯ STATELESS: храним состояния в Redis, а не в памяти
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    dp.include_router(router)

    # Пока используем long polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
