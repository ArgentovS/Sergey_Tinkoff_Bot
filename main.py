import asyncio
import datetime
from settings import *
from tools import *
from handlers.commands import router as com_rout


async def start_bot(actual_shares):
    """
    Сопрограмма конфигурации и запуск бота
    :return: NoReturn
    """
    bot = Bot(token=config['Telegram']['api'], parse_mode=ParseMode.HTML)  # создаём экземпляр бота
    dp = Dispatcher(bot=bot, storage=MemoryStorage())  # создаём экземпляр диспетчера
    dp.include_routers(com_rout)  # подключаем роутер к диспетчеру
    bot.actual_shares = actual_shares
    bot.actual_shares.bot = bot
    await bot.delete_webhook(drop_pending_updates=True)  # игнорируем ранее поданные боту запросы
    await dp.start_polling(bot)  # запускаем асинхронного бота


async def monitoring_exchange(actual_shares):
    """
    Сопрограмма мониторинга расписаний и акций Мосбиржи, запускающаяся по расписанию.
    :param actual_shares: экземпляр класса актуального расписания и параметров акций Мосбиржи.
    :return: NoReturn
    """
    while True:
        # Проверяем время для запуска по расписанию актуализации расписания и параметров акций Мосбиржи
        if utc3(now()).strftime('%H') == '20':
            await actual_shares.fit()
            print(actual_shares.message_shedulers)
            #actual_shares.prn_exchanges()
            #actual_shares.prn_shares()
            #actual_shares.prn_shedulers()

        await asyncio.sleep(60)
        
        # Обработчик изменения данных
        event_data = {} # какие то данные взятые из БД по пользователям
        # if True:
        #     if actual_shares.bot != None:
        #         actual_shares.bot.send_message(event_data['chat_id'], actual_shares.message_shedulers)
        #     else:
        #         pass
            


async def main(actual_shares):
    """
    Сопрограмма конфигурации асинхронных задач
    :param actual_shares: экземпляр класса актуального расписания и параметров акций Мосбиржи.
    :return: NoReturn
    """
    # Конфигурация и запуск бота
    task1 = asyncio.create_task(start_bot(actual_shares))
    # Мониторинг расписаний Мосбиржи и формирование базы
    task2 = asyncio.create_task(monitoring_exchange(actual_shares))
    # Запускаем задачи асинхронно
    await asyncio.gather(task1, task2)


# Запускаем бота и опрос рынка
if __name__ == '__main__':

    # Создаём журнал логирования  ###---  ВОПРОС: как направлять в разные файлы потоки из разных модудей? ---###
    logger.add(LOG_SCHEDULE_PATH, rotation="1 MB", enqueue=True)

    # Создаём экземпляр расписания
    actual_shares = ActualInstruments()  # Создан в основном теле, чтобы иметь возможность передавать в любое место

    # Запускаем асинхронные задачи (бот, мониторинг расписания рынка)
    asyncio.run(main(actual_shares))

