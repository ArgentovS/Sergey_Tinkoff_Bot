from settings import *


router = Router()


@router.message(Command("start"))
async def start_handler(msg: Message):
    await msg.answer(f"Привет {msg.from_user.username}! Я помогу тебе узнать твой ID, просто отправь мне любое сообщение")

@router.message(Command("test_as"))
async def start_handler(msg: Message):
    await msg.answer(f"{msg.bot.actual_shares.message_shedulers}")


@router.message(Command("sa"))
async def start_handler(msg: Message):
    await msg.answer(f"Привет {msg.from_user.username}! Я помогу тебе узнать твой ID, просто отправь мне любое сообщение")


@router.message()
async def message_handler(msg: Message):
    await msg.answer(f"Твой ID: {msg.from_user.id}")
