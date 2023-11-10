from settings import *


def timeit(func):
    """
    Декоратор для измерения времени работы асинхронной и синхронной функции.
    :return: datetime
    """

    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def measure_time(*args, **kw):
            start_time = time.time()
            result = await func(*args, **kw)

            logger.info(f'Время выполнения асинхронной функции {func.__qualname__}:'
                        f' {(time.time() - start_time):.6f} сек.\n')
            return result

    else:

        @wraps(func)
        def measure_time(*args, **kw):
            start_time = time.time()
            result = func(*args, **kw)

            logger.info(f'Время выполнения синхронной функции {func.__qualname__}:'
                        f' {(time.time() - start_time):.6f} сек.\n')
            return result

    return measure_time


def utc3(utc0):
    """
    Функция перевода времени в Московский часовой пояс
    :return: datetime UTC+3
    """
    return utc0 + timedelta(hours=3)


def what_time(actual_shares):
    """
    Функция для определения торговый ли день.
    :return: str
    """
    actual_shares.flag_period_trading = False  # Флаг периода торговли
    if actual_shares.is_trading:
        for exchanxe in actual_shares.shedulers.keys():
            if actual_shares.shedulers[exchanxe][0].start_time <= now() <= actual_shares.shedulers[exchanxe][0].end_time:
                actual_shares.flag_period_trading = True
    return actual_shares.flag_period_trading

