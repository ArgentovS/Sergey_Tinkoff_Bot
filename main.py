from settings import *
from tools import *
from handlers.commands import router as com_rout


# Конфигурируем бота
async def start_bot(actual_shares):
    bot = Bot(token=config['Telegram']['api'], parse_mode=ParseMode.HTML)  # создаём экземпляр бота
    dp = Dispatcher(bot=bot, storage=MemoryStorage())  # создаём экземпляр диспетчера
    dp.include_routers(com_rout)  # подключаем роутер к диспетчеру
    bot.actual_shares = actual_shares  # создаём внутри бота ссылку на класс с расписанием
    bot.actual_shares.bot = bot  # Создаём ссылку на бот внутри класса
    logger.debug(f'\n            Бот запущен')
    await dp.start_polling(bot, polling_timeout=45)  # запускаем асинхронного бота
    logger.error(f'\n            Бот остановлен')


# Опрашиваем рынок и рассчитываем параметры изменения свечей
async def start_market_survey(actual_shares):
    while actual_shares.is_trading:
        figis = []  # Список figi инсрументы, по которым направляются запросы
        for exchanxe in actual_shares.shedulers.keys():
            if actual_shares.shedulers[exchanxe][0].start_time <= now() <= actual_shares.shedulers[exchanxe][0].end_time:
                for share in actual_shares.exchanges[exchanxe]:
                    figis.append((share.figi,
                                  share.ticker,
                                  share.min_price_increment))  # Формируем список активных инструментов
        await asyncio.sleep(1)
        flag_end_time = False
        delay_time = 15
        if len(figis) and now().second == delay_time:
            await create_requests_candles(actual_shares, figis)  # Формируем асинхронные запросы по инструментам
            await asyncio.sleep(3)
        elif not len(figis) and now().second == delay_time:
            for exchanxe in actual_shares.shedulers.keys():
                if now() >= actual_shares.shedulers[exchanxe][0].end_time:
                    flag_end_time = True
            if flag_end_time:
                actual_shares.is_trading = False
            logger.info(f'\n            Торги на секциях закончены')
            logger.info(f'\n            {len(figis)}, флаг окончания дня: {flag_end_time}, '
                        f'признак торгового дня: {actual_shares.is_trading}')


# Запускаем мониторинг времени и опрос рынка в определ>нное время
async def monitoring_exchange(actual_shares):
    # Определение времении актуализации расписания и времени утреннего сообщения
    time_test_night = utc3(now()).strftime('%H')
    logger.info(f'\n            Мониторинг перезапущен')
    while True:
        if utc3(now()).strftime('%H') == time_test_night:
            await actual_shares.fit()  # Актуализируем расписания инструментов Мосбиржи в определённое время
            await asyncio.sleep(3)
        if utc3(now()).strftime('%H') == TIME_MORNING_MESSAGE and actual_shares.is_trading:
            await one_message(actual_shares, actual_shares.message_shedulers)  # Направляем утреннее сообщение
            await asyncio.sleep(3)
            logger.debug(f'\n            Зпапущен цикл мониторинга рынка start_market_survey(actual_shares)')
            await start_market_survey(actual_shares)  # Запускаем опрос параметров рынка внутри торгового дня
        logger.info(f'\n            Проведён цикл мониторинга рынка.\n'
                    f'              Признак торгового дня {actual_shares.is_trading}\n'
                    f'              Опредлелённый час время {utc3(now()).strftime("%H")}\n'
                    f'              Заданный час {TIME_MORNING_MESSAGE}')
        await asyncio.sleep(51*60)


# Запускаем бота и опрос рынка в асинхронном режиме
async def main(actual_shares):
    task1 = asyncio.create_task(start_bot(actual_shares))  # Конфигурация и запуск бота
    task2 = asyncio.create_task(monitoring_exchange(actual_shares))  # Мониторинг расписаний Мосбиржи
    await asyncio.gather(task1, task2)  # Запуск задач асинхронно


# Запускаем программу
if __name__ == '__main__':
    logger.add(LOG_SCHEDULE_PATH, rotation="1 MB", enqueue=True)  # Создание журнала логирования
    actual_shares = ActualInstruments()  # Создание экземпляра класса расписания в основном теле
    asyncio.run(main(actual_shares))  # Запуск задач асинхронно (бот, мониторинг расписания рынка)
