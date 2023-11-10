from settings import *
from tools.utils import *


@timeit
# Сопрограмма направления сообщения пользователям
async def one_message(actual_shares, text):
    async def message_to_bot(user_id, actual_shares, text):
        await actual_shares.bot.send_message(chat_id=user_id, text=text, parse_mode='HTML')

    tasks = [message_to_bot(user_id, actual_shares, text) for user_id in USERS]
    loop = asyncio.get_event_loop()
    for task in tasks:
        loop.create_task(task)
    logger.info(f'\n            Сообщения отправлены {len(USERS)} пользователям')


# Функция формирования текста сообщения при резком росте объёма
def message_huge_volume(figi, candles, volume_avg):

    # Расчёт статических параметров сообщения
    time_last = utc3(candles[-1:][0].time).strftime("%H:%M")          # время последней свечи

    min_price_increment = figi[2].units + figi[2].nano * 1e-9         # Минимальный шаг цены
    price_penultimate = round(candles[-1:][0].open.units +            # Цена предпоследней свечи
                              candles[-1:][0].open.nano * 1e-9, len(str(1 + min_price_increment % 1)[2:]))
    price_last = round(candles[-1:][0].close.units +                  # Цена последней свечи
                       candles[-1:][0].close.nano * 1e-9, len(str(1 + min_price_increment % 1)[2:]))

    volume_last = candles[-1:][0].volume                              # Объём последней свечи

    # Расчёт динамических параметров сообщения
    if price_penultimate < price_last:
        emoji_1 = '📈'
        price_percentage = f'+{round((price_last - price_penultimate) / price_penultimate * 100, 2)}%'
        emoji_2 = '🚀'
        price_point = f'Рост на {round((price_last - price_penultimate)/ min_price_increment)}п'
    elif price_penultimate > price_last:
        emoji_1 = '📉'
        price_percentage = f'{round((price_last - price_penultimate) / price_penultimate * 100, 2)}%'
        emoji_2 = '🧨'
        price_point = f'Падение на {round((price_penultimate - price_last) /  min_price_increment)}п'
    else:
        emoji_1 = '🌫'
        price_percentage, emoji_2 = '0%', '🥶'
        price_point = 'Цена не изменилась'

    # Формирование текста сообщения
    text = f'{emoji_1} <code>{figi[1]}</code> {price_percentage} {emoji_2}\n' \
           f'Рост объёма на {round(((volume_last - volume_avg) / volume_avg) * 100)}%\n' \
           f'{price_point} ({price_percentage})\n' \
           f'Текущая цена: {price_last} ₽\n' \
           f'Объём: {volume_last}\n' \
           f'время: {time_last}'
    return text
