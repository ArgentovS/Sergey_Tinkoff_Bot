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
        await actual_shares.bot.send_message(chat_id=user_id, text=text, parse_mode='HTML')

    tasks = [message_to_bot(user_id, actual_shares, text) for user_id in users]
    loop = asyncio.get_event_loop()
    for task in tasks:
        loop.create_task(task)
    logger.info(f'\n            Отправлены сообщения {len(users)} пользователям')


# Функция формирования текста сообщения при резком росте объёма
def message_huge_volume(figi, candles, users, actual_shares):

    # Расчёт статических параметров сообщения
    time_last = utc3(candles[-1:][0].time).strftime("%H:%M")                 # время последней свечи

    price_penultimate = round(candles[-2:-1][0].close.units +          # Цена последней свечи
                              candles[-2:-1][0].close.nano * 1e-9, 2)
    price_last = round(candles[-1:][0].close.units +                   # Цена предпоследней свечи
                       candles[-1:][0].close.nano * 1e-9, 2)

    volume_last = candles[-1:][0].volume                               # Объём последней свечи

    # Расчёт динамических параметров сообщения
    if price_penultimate < price_last:
        price_percentage, emoji = f'+{round((price_last - price_penultimate) / price_penultimate * 100, 2)}%', '🚀'
        price_point = f'Рост на {round((price_last - price_penultimate)/(figi[2].units+figi[2].nano * 1e-9))}п'
    elif price_penultimate > price_last:
        price_percentage, emoji = f'{round((price_last - price_penultimate) / price_penultimate * 100, 2)}%', '🧨'
        price_point = f'Падение на {round((price_penultimate - price_last) / (figi[2].units + figi[2].nano * 1e-9))}п'
    else:
        price_percentage, emoji = '0%', '🥶'
        price_point = 'Цена не изменилась'
    volumes_penultimate, volume_avg = list(), 1  # Средний объём предпоследних 252 свечей
    for candle in candles[:-1]:
        volumes_penultimate.append(candle.volume)
    volume_avg = sum(volumes_penultimate) / len(volumes_penultimate)
    # Формирование текста сообщения
    text = f'время: {time_last}\n' \
           f'📉 <code>{figi[1]}</code> {price_percentage} {emoji}\n' \
           f'Рост объёма на {round(((volume_last - volume_avg) / volume_avg) * 100)}%\n' \
           f'{price_point} ({price_percentage})\n' \
           f'Текущая цена: {price_last} ₽\n' \
           f'Объём: {volume_last} '

    return text
