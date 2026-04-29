from collections.abc import Awaitable, Callable
from functools import wraps

from aiogram.fsm.context import FSMContext
from aiogram.types import Message


Handler = Callable[[Message, FSMContext], Awaitable[None]]
CANCEL_WORDS = {"/cancel", "cancel", "отмена"}


def cancelable(handler: Handler) -> Handler:
    @wraps(handler)
    async def wrapper(message: Message, state: FSMContext) -> None:
        text = message.text

        if text is not None and text.strip().lower() in CANCEL_WORDS:
            await state.clear()
            await message.answer("Действие отменено.")
            return

        await handler(message, state)

    return wrapper
