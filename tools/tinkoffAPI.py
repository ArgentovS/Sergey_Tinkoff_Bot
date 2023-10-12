from settings import *
from tools.utils import *
from tools.db import *
from handlers import *

INVEST_TOKEN = config['Tinkoff']['api']


# Сопрограмма определения расписаний секций Мосбиржи, на которых торгуются акции
@timeit
async def get_schedules():
    async with AsyncClient(INVEST_TOKEN) as client:
        calendars = await client.instruments.trading_schedules(from_=now(), to=now())  # Расписания секций текущего дня
        shares_exchanges = await get_exchange_figi_shares()  # Секции со списком акций, торгующиеся на Мосбирже через Тинькофф в текущий день

        shares_schedules = {}  # Расписания секций Мосбиржи
        schedules_message = '\n            Расписание по секциям:   '
        is_trading = False  # Признак наличия расписания в текущий день хотя бы для одной секции торгуемых акций
        for calendar in calendars.exchanges:
            if calendar.exchange in shares_exchanges[0].keys():  # Собираем расписания секций акций Мосбиржи в текущий день
                if calendar.exchange not in list(shares_schedules.keys()):
                    shares_schedules[calendar.exchange] = calendar.days[0]
                    if calendar.days[0].is_trading_day:
                        schedules_message += f' {calendar.exchange}'\
                                f' c {(calendar.days[0].start_time+timedelta(hours=3, minutes=0)).strftime("%H:%M")}'\
                                f' до {(calendar.days[0].end_time+timedelta(hours=3, minutes=0)).strftime("%H:%M")}  | '
                        is_trading = True
                    else:
                        schedules_message += f' {calendar.exchange} сегодня нет торгов  | '

        # Логирование сборки расписаний
        logger.info(schedules_message)

        # Формируем список задач для асинхронных запросов свечей по акциям
        return shares_schedules, shares_exchanges, is_trading


# Сопрограмма запуска списка задач для асинхронных запросов акций, торгуемых в текущий момент на Мосбирже
async def create_requests_candles(users, actual_shares, figis):
    tasks = [get_last_candle(users, actual_shares, figi) for figi in figis]
    loop = asyncio.get_event_loop()
    for task in tasks:
        loop.create_task(task)
    logger.info(f'\n            Запущено {len(tasks)} асинхронных задач для запросов свечей')


# Сопрограмма запросов свечей
async def get_last_candle(users, actual_shares, figi=None):
    async with AsyncClient(INVEST_TOKEN) as client:
            volume_count = 0
            volume_sum = 0
            async for candle in client.get_all_candles(
                    figi=figi[0],
                    from_=now()-timedelta(minutes=252),
                    to=now(),
                    interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
                                                            ):
                try:
                    volume = candle.volume
                    volume_count += 1
                    volume_sum += volume
                    time_c = utc3(candle.time)
                    now_time = utc3(now())
                    if volume_sum:
                        volume_average = volume_sum / volume_count
                        # candle_time, volume, is_complete = candle.time, candle.volume, candle.is_complete
                        # print(time_c, figi, now_time,
                        #       f'время подсчёта: +{now_time-time_c-timedelta(minutes=1)-timedelta(seconds=15)} сек.')
                        # # await set_collect_1_min_candels(candle_time,
                        # #                                 figi,
                        #                                 volume,
                        #                                 is_complete,
                        #                                 now_time)
                except Exception as E:
                    pass
                        #logger.debug(f'Ошибка выполнения запроса {E}')
                    print(f'Ошибка {E}')
                        # print('1970-01-01 00:00:00+00:00', figi, 0, False, now_time)
                        # await set_collect_1_min_candels('1970-01-01 00:00:00+00:00',
                        #                                 figi,
                        #                                 0,
                        #                                 False,
                        #                                 now_time)
            if volume_sum and volume_average*1.5 < volume:
                #logger.info(f'{figi}, Среднее: {volume_average}, Свеча: {volume} время свечи: {time}')
                text = f'Время: {time_c.strftime("%H:%M")} |  Акция: `{figi[1]}` |\n'\
                           f'Средний объём на {volume_count} свечах: {round(volume_average)} |\n'\
                           f'Объём последней свечи: {volume} '\
                           f'(+{round(((volume-volume_average)/volume_average)*100)}%)'
                print(f'+{now_time-time_c-timedelta(minutes=1)-timedelta(seconds=15)} сек.'
                      f'{text}')
                await one_message(users, actual_shares, text)





# Сопрограмма запроса через ТинькоффАПИ данных об аккаунте пользователя
@timeit
async def get_account():
    async with AsyncClient(INVEST_TOKEN) as client:
        await client.users.get_accounts()


# Сопрограмма получения списка figi акций на секциях Мосбиржи
@timeit
async def get_exchange_figi_shares():
    async with AsyncClient(INVEST_TOKEN) as client:
        shares = await client.instruments.shares()  # Список всех активных акций в Тинькофф
        shares_exchanges = {}  # Список всех активных акций на секциях Мосбиржи (торгуемых через Тинькофф)
        for elem in shares.instruments:
            if elem.real_exchange == 1:  # Выбираем акции, торгующиеся на Мосбирже
                # Группируем figi акций по секциям Мосбиржи
                if elem.exchange not in shares_exchanges.keys():
                    shares_exchanges[elem.exchange] = [elem.figi]
                else:
                    shares_exchanges[elem.exchange].append(elem.figi)

        # Логирование сборки акций Мосбиржи
        mos_exchange = [(section, len(shares_exchanges[section])) for section in shares_exchanges.keys()]
        mos_exchange_message = f'На Мосбирже {sum([shares[1] for shares in mos_exchange])} акций'\
                               f' в {len(shares_exchanges)} секциях: {mos_exchange}'
        logger.info('\n            У брокера {len(shares.instruments)} акций. '
                    f'{mos_exchange_message}')

        return shares_exchanges, mos_exchange_message


# Сопрограмма запроса через ТинькоффАПИ расписаний, секций и акций, торгуемых на Мосбирже
async def async_get_schedules():
    async with AsyncClient(INVEST_TOKEN) as client:
        # Запросим параметры акций, которые торгуются на Мосбирже
        shares = await client.instruments.shares()
        morx_exchanges = dict()  # Множество секций Мосбиржи, на котрой торгуются акции

        for share in shares.instruments:
            if share.real_exchange == 1:  # Признак торговли акцией на Мосбирже
                if share.exchange in morx_exchanges.keys():
                    morx_exchanges[share.exchange].append(share)
                else:
                    morx_exchanges[share.exchange] = [share]

        # Запросим параметры расписаний секций Мосбиржи, на которых торгуются акции
        schedules = await client.instruments.trading_schedules(from_=now())
        moex_schedules = dict()  # Словарь расписаний секций акций Мосбиржи на несколько дней вперёд

        for exchange in schedules.exchanges:
            if exchange.exchange in morx_exchanges:
                moex_schedules[exchange.exchange] = exchange.days  # Заполняется данным в формате Тинькофф-АПИ days

    return morx_exchanges, moex_schedules


