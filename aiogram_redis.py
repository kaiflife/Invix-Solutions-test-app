from aiogram.fsm.storage.redis import RedisStorage

storage = RedisStorage.from_url("redis://redis:6379/0")
dp = Dispatcher(storage=storage)
