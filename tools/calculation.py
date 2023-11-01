from settings import *
from tools.utils import *
from tools.db import *
from handlers import *
from tools.data_type import *


# Функция расчёта среднего объёма свечей
def avg_volume(candles):
    volumes = 0
    count = 0
    for candle in candles:
        volumes += candle.volume
        count += 1
    return volumes / count, count


# Функция расчёта среднего 50 пятиминутных свечей
def get_avarage_5_min(candles_5_min, ticker):
    if len(candles_5_min) >= 50:
        return avg_volume(candles_5_min[:50])[0]
    elif len(candles_5_min) > 0:
        logger.info(f' Исторических 5-минутных свечей по тикеру {ticker}: только {len(candles_5_min)}')
        return avg_volume(candles_5_min[:50])[0]
    else:
        logger.info(f' Исторических 5-минутных свечей по тикеру {ticker}: нет')
        return 0


# Функция расчёта накопления объёма текущей 5-минутной свечи из 1-минутных свечей
def get_volumes_1_min(candles_1_min):
    candle = BotCandle(
        candles_1_min[-1-(int(candles_1_min[-1:][0].time.minute)%5):][0].open,
        candles_1_min[-1:][0].high,
        candles_1_min[-1:][0].low,
        candles_1_min[-1:][0].close,
        0,
        candles_1_min[-1:][0].time,
        candles_1_min[-1:][0].is_complete
    )
    for elem in candles_1_min[-1-(int(candle.time.minute)%5):]:
        candle.volume += elem.volume
    return candle
