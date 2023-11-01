from settings import *
from tools.utils import *
from tools.db import *
from tools.calculation import *
from handlers import *

INVEST_TOKEN = config['Tinkoff']['api']


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


# Сопрограмма запуска списка задач для асинхронных запросов акций, торгуемых в текущий момент на Мосбирже
async def create_requests_candles(actual_shares, figis):
    # Задаём пользовательское ограничение на список наблюдаемых инструментов
    user_figis = ['AFKS', 'AFLT', 'AGRO', 'ALRS', 'CHMF', 'GAZP', 'GTRK', 'IRAO', 'HNFG', 'LKOH', 'MAGN',
                  'MGNT', 'MOEX', 'MTLR', 'MTLRP', 'NLMK', 'NMTP', 'NVTK', 'OGKB', 'PLZL', 'RASP', 'ROLO',
                  'ROSN', 'RTKM', 'RUAL', 'SBER', 'SIBN', 'SNGSP', 'TATN', 'TRMK', 'VTBR', 'YNDX']
    _figis = [elem for elem in figis if elem[1] in user_figis]
    # Асинхронно формируем запросы к ТинькоффАПИ и сообщения в бот
    tasks = [get_last_candles_50for5_5for1(actual_shares, figi) for figi in _figis]
    loop = asyncio.get_event_loop()
    for task in tasks:
        loop.create_task(task)
    logger.info(f'\n            Запущено {len(tasks)} асинхронных задач для запросов свечей')


# Сопрограмма запросов 252 свечей по 1 минуте
async def get_last_candle(actual_shares, figi=None):
    candles = list()  # список полученных свечей
    async with AsyncClient(INVEST_TOKEN) as client:
        try:
            async for candle in client.get_all_candles(figi=figi[0], from_=now()-timedelta(minutes=252),
                                                   to=now(), interval=CandleInterval.CANDLE_INTERVAL_1_MIN):
                candles.append(candle)
        except BaseException as E:
            logger.debug(f'Ошибка выполнения запроса к Тинькофф АПИ {E}')
            pass

        # Формируем текст сообщения если объём вырос на коэффициент
        volumes_penultimate, volume_avg = list(), 1  # Средний объём предпоследних 252 свечей
        for candle in candles[:-1]:
            volumes_penultimate.append(candle.volume)
        volume_avg = sum(volumes_penultimate) / len(volumes_penultimate)
        if candles[-1:][0].volume >= EXCESS_VOLUME * volume_avg and \
                (now() - timedelta(minutes=1)).minute == candles[-1:][0].time.minute:

            volumes_penultimate, volume_avg = list(), 1  # Средний объём предпоследних 252 свечей
            for candle in candles[:-1]:
                volumes_penultimate.append(candle.volume)
            volume_avg = sum(volumes_penultimate) / len(volumes_penultimate)

            text = message_huge_volume(figi, candles, volume_avg)  # Формируем сообщение в телеграм
            print(f'+{now() - candles[-1:][0].time - timedelta(minutes=1) - timedelta(seconds=15)} сек.\n'
                  f'{text}')
            # Отправляем сообщения в телеграм
            await one_message(actual_shares, text)


# Сопрограмма запросов 50 свечей по 5 минут и 5 свечей по 1 минуте
async def get_last_candles_50for5_5for1(actual_shares, figi=None):
    candles_5_min = list()  # список 5 минутных свечей за 15 дней
    candles_1_min = list()  # список 1 минутных текущих свечей
    async with AsyncClient(INVEST_TOKEN) as client:
        try:
            async for candle in client.get_all_candles(figi=figi[0], from_=now() - timedelta(minutes=5),
                                                       to=now(), interval=CandleInterval.CANDLE_INTERVAL_1_MIN):
                candles_1_min.append(candle)
        except BaseException as E:
            logger.debug(f'Ошибка получения 1 минутных свечей для {figi[0]}\n{E}\n'
                         f' Длинна 1-минутного списка {len(candles_1_min)}')
            pass

        if candles_1_min:
            # Запросим исторические 5-минутные свечи
            try:
                async for candle in client.get_all_candles(figi=figi[0], from_=now() - timedelta(days=1),
                                                           to=now(), interval=CandleInterval.CANDLE_INTERVAL_5_MIN):
                    candles_5_min.append(candle)
            except BaseException as E:
                logger.debug(f'Ошибка получения 5 минутных свечей для {figi[0]}\n{E}\n'
                             f' Длинна 5-минутного списка {len(candles_5_min)}')
                pass
            # Расчёт среднего значения свечи по 5 минуткам
            avarage_volume_5_min = get_avarage_5_min(candles_5_min, figi[1])

            # Расчёт накопленных 1 минутных свечей внутри текущей пятиминутки
            candles_1_min = get_volumes_1_min(candles_1_min)

            # Формируем текст сообщения если объём вырос на коэффициент
            if candles_1_min.volume >= EXCESS_VOLUME * avarage_volume_5_min and \
                    (now() - timedelta(minutes=1)).minute == candles_1_min.time.minute:
                text = message_huge_volume(figi, [candles_1_min], avarage_volume_5_min)  # Формируем сообщение в телеграм
                print(f'+{now() - candles_1_min.time - timedelta(minutes=1) - timedelta(seconds=15)} сек.\n'
                      f'{text}')
                # Отправляем сообщения в телеграм
                await one_message(actual_shares, text)


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
                        schedules_message += f' **{calendar.exchange}**'\
                                f' c {(calendar.days[0].start_time+timedelta(hours=3, minutes=0)).strftime("%H:%M")}'\
                                f' до {(calendar.days[0].end_time+timedelta(hours=3, minutes=0)).strftime("%H:%M")}  | '
                        is_trading = True
                    else:
                        schedules_message += f' {calendar.exchange} сегодня нет торгов  | '

        # Логирование сборки расписаний
        logger.info(schedules_message)

        # Формируем список задач для асинхронных запросов свечей по акциям
        return shares_schedules, shares_exchanges, is_trading
