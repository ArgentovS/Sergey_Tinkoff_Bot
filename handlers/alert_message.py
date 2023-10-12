from settings import *
from tools.utils import *


@timeit
# Сопрограмма направления сообщения пользователям
async def one_message(users, actual_shares, text):
    """
    Сопрограмма отправки одиночного сообщения в чат
    :return: NoReturn
    """
    async def message_to_bot(user_id, actual_shares, text):
        await actual_shares.bot.send_message(chat_id=user_id, text=text)

    tasks = [message_to_bot(user_id, actual_shares, text) for user_id in users]
    loop = asyncio.get_event_loop()
    for task in tasks:
        loop.create_task(task)
    logger.info(f'\n            Отправлены сообщения {len(users)} пользователям')
