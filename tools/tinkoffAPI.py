from settings import *
from tools.utils import *
from tools.db import *

INVEST_TOKEN = config['Tinkoff']['api']


# Сопрограмма запроса через ТинькоффАПИ данных об аккаунте пользователя
@timeit
async def get_account():
    async with AsyncClient(INVEST_TOKEN) as client:
        await client.users.get_accounts()


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





# Подпрограмма получения списка figi акций на секциях Мосбиржи
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


# Подпрограмма определения расписаний секций Мосбиржи, на которых торгуются акции
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


# Функция формирования списка задач для асинхронных запросов акций, торгуемых в текущий момент на Мосбирже
@timeit
def get_last_candles(shares_schedules, shares_exchanges, is_trading):
    figis = []  # Список торгуемых в данный момент акций на Мосбирже
    if is_trading:
        for schedule in shares_schedules.keys():
            # Включение figi акций в задачи на запрос свечей (в случае если для них активно расписание)
            if shares_schedules[schedule].end_time >= now() >= shares_schedules[schedule].start_time:
                figis.extend(shares_exchanges[schedule])
        tasks = [asyncio.create_task(get_last_candle(figi)) for figi in figis]
        logger.info(f'\n            Сформировано {len(tasks)} задач для запросов')
        return tasks


# Сопрограмма запросов свечей
async def get_last_candle(figi=None):
    async with AsyncClient(INVEST_TOKEN) as client:
        while True:
            if now().second == 57:
                async for candle in client.get_all_candles(
                    figi=figi,
                    from_=now() - timedelta(minutes=1),
                    interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
                                                            ):
                    pass
                now_time = now()
                try:
                    candle_time, volume, is_complete = candle.time, candle.volume, candle.is_complete
                    print(candle_time, figi, volume, is_complete, now_time,
                          f'время подсчёта: +{now_time-candle.time-timedelta(minutes=1)} сек.')
                    await set_collect_1_min_candels(candle_time,
                                                    figi,
                                                    volume,
                                                    is_complete,
                                                    now_time)

                except:
                    print('1970-01-01 00:00:00+00:00', figi, 0, False, now_time)
                    await set_collect_1_min_candels('1970-01-01 00:00:00+00:00',
                                                    figi,
                                                    0,
                                                    False,
                                                    now_time)
                await asyncio.sleep(1)