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
    if msg.from_user.id == 389726986:
        await msg.answer(f"Переменные бота:\n"
                         f"Торговый период: {msg.bot.actual_shares.flag_period_trading}\n"
                         f"Торговый день: {msg.bot.actual_shares.is_trading}\n"
                         f"Ближайший торговый день: {msg.bot.actual_shares.trading_day}")
    await msg.answer(f"Твой ID: {msg.from_user.id}")
