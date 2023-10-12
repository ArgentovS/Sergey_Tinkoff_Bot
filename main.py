import asyncio
import datetime
from settings import *
from tools import *
from handlers.commands import router as com_rout


# Опрашиваем рынок и рассчитываем параметры изменения свечей
async def start_market_survey(actual_shares, users):
    """
    Сопрограмма запроса рыночных параметров
    :return: параметры свечей
    """
    # Формируем список акций, торгующихся на секциях, по которым текущее время совпадает расписанием
    count_exchange = 0  # Счётчик активных секций внутри диапазона расписания соответствующих секций
    figis = []  # Список figi акций, по которым в текущее время направляются запросы

    for exchanxe in actual_shares.shedulers.keys():

        # Проверяем что текущее время находится внутри диапазона расписания соответствующей секции
        if actual_shares.shedulers[exchanxe][0].start_time <= now() <= actual_shares.shedulers[exchanxe][0].end_time:
            # Формируем запросы по акциям, которые торгуются в соответствующих секциях
            for share in actual_shares.exchanges[exchanxe]:
                figis.append(share.figi)

        # Формируем асинхронные запросы по акциям в активных секциях
        delay_time = 15
        while now().second == delay_time:
            await create_requests_candles(figis, actual_shares, users)
            await asyncio.sleep(1)
            # Проверяем закончился ли торговый день на всех секциях
            if now() >= actual_shares.shedulers[exchanxe][0].end_time:
                count_exchange += 1
            logger.info(f'\n            Торги закончены на {count_exchange} секциях')


    # Проверяем окончание торгового дня
    if len(list(actual_shares.shedulers.keys())) == count_exchange:
        actual_shares.is_trading = False
        logger.info(f'\n            Торги на сегодня закончены')


# Конфигурируем бота
async def start_bot(actual_shares):
    """
    Сопрограмма конфигурации и запуск бота
    :return: NoReturn
    """
    bot = Bot(token=config['Telegram']['api'], parse_mode=ParseMode.HTML)  # создаём экземпляр бота
    dp = Dispatcher(bot=bot, storage=MemoryStorage())  # создаём экземпляр диспетчера
    dp.include_routers(com_rout)  # подключаем роутер к диспетчеру
    logger.debug(f'\n            Роутер  бота включен')
    bot.actual_shares = actual_shares  # создаём ссылку на класс с расписанием внутри бота
    logger.debug(f'\n            Бот бот добавили класс')
    bot.actual_shares.bot = bot  # Создаём ссылку на бот внутри класса
    logger.debug(f'\n            В класс добавил бот')
    await bot.delete_webhook(drop_pending_updates=True)  # игнорируем ранее поданные боту запросы
    logger.debug(f'\n            В боте удалены webhook')
    await dp.start_polling(bot)  # запускаем асинхронного бота
    logger.error(f'\n            Бот остановлен')


# Конфигурируем мониторинг времени и опрос рынка
async def monitoring_exchange(actual_shares):
    """
    Сопрограмма мониторинга расписаний и акций Мосбиржи, запускающаяся по расписанию.
    :param actual_shares: экземпляр класса актуального расписания и параметров акций Мосбиржи.
    :return: NoReturn
    """
    while True:
        time_test_night, time_test_morning = '04', '04'  # время актуализации расписания и выдачи утреннего сообщения
        # Формируем перечень пользователей, которым направляется сообщение
        users = [389726986, 6251198210]  # , 228248763, 2022125420]

        # Проверяем время для запуска ежедневной актуализации расписания и параметров акций Мосбиржи
        if utc3(now()).strftime('%H') == time_test_night:
            await actual_shares.fit()  # Заполняем расписание на последующие дни (в 03:06 ночи каждого дня)
        # Направляем пользователям в чат утреннее сообщение о расписании
        if utc3(now()).strftime('%H') == time_test_morning:
            await one_message(users, actual_shares, actual_shares.message_shedulers)
            while actual_shares.is_trading:
                # Запускаем опрос параметров рынка внутри торгового дня
                await start_market_survey(actual_shares, users)
        logger.info(f'\n            Проведён цикл мониторинга рынка')
        await asyncio.sleep(60*60)


# Запускаем бота и опрос рынка в асинхронном режиме
async def main(actual_shares):
    """
    Сопрограмма конфигурации асинхронных задач
    :param actual_shares: экземпляр класса актуального расписания и параметров акций Мосбиржи.
    :return: NoReturn
    """
    # Конфигурация и запуск бота
    task2 = asyncio.create_task(start_bot(actual_shares))
    # Мониторинг расписаний Мосбиржи и формирование базы
    task1 = asyncio.create_task(monitoring_exchange(actual_shares))
    # Запускаем задачи асинхронно
    await asyncio.gather(task1, task2)


# Запускаем программу
if __name__ == '__main__':

    # Создаём журналы логирования
    logger.add(LOG_SCHEDULE_PATH, rotation="1 MB", enqueue=True)

    # Создаём экземпляр расписания
    actual_shares = ActualInstruments()  # Создан в основном теле, чтобы иметь возможность передавать в любое место

    # Запускаем асинхронные задачи (бот, мониторинг расписания рынка)
    asyncio.run(main(actual_shares))

