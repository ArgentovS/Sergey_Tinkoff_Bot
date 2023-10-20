from settings import *
from tools.tinkoffAPI import *


class ActualInstruments:
    """
    Класс загружающий актуальные расписания торгов на Мосбирже, а также соответствующие секции и акции
    """
    def __init__(self):
        self.is_trading = False  # Признак того что в текущий день торги проводятся (по умолчанию False)
        self.trading_day = now().strftime('%y-%m-%d')  # Ближайшая дата торгов (по умолчанию текущая дата)
        self.bot: Bot = None

    @timeit
    async def fit(self):
        """
        Метод получения актуального расписаний, секций и аккций Мосбиржи
        :return: сообщение с расписанием
        """
        self.__all_params = await async_get_schedules()  # Асинхронный запрос в Тинкофф АПИ
        self.exchanges = self.__all_params[0]  # Словарь секций торговли акциями на Мосбирже со списком акций
        self.shedulers = self.__all_params[1]  # Словарь секций акций Мосбиржи с расписаниями торгов на несколько дней

        # Формируем сообщение о расписании торгов на сегодня или на ближайший торговый день (ЕГО НАДО ПЕРЕДАТЬ В БОТ!)
        self.message_shedulers = '<b>Расписание торгов на сегодня</b>'
        for __exchange in self.shedulers.keys():
            if self.shedulers[__exchange][0].is_trading_day:  # Если текущая дата - дата торгов на Мосбирже
                self.is_trading = True
                self.message_shedulers += (f'\n <u>{__exchange}:</u>\n'
                                           f'    c {utc3(self.shedulers[__exchange][0].start_time).strftime("%H-%M")}'
                                           f' до {utc3(self.shedulers[__exchange][0].end_time).strftime("%H-%M")}\n'
                                           f'    ({len(self.exchanges[__exchange])} акций)')
        if not self.is_trading:
            for day in range(len(self.shedulers[__exchange])-1, 0, -1):
                self.message_shedulers = (f'Сегодня торгов нет\n'
                                          f'\n<b>Расписание торгов на {self.shedulers[__exchange][day].date.strftime("%y-%m-%d")}</b>')
                for __exchange in self.shedulers.keys():
                    if self.shedulers[__exchange][day].is_trading_day:
                        self.trading_day = self.shedulers[__exchange][day].date.strftime('%y-%m-%d')
                        self.message_shedulers += (f'\n <u>{__exchange}:</u>\n'
                                                   f'    c {utc3(self.shedulers[__exchange][day].start_time).strftime("%H-%M")}'
                                                   f' до {utc3(self.shedulers[__exchange][day].end_time).strftime("%H-%M")}\n'
                                                   f'    ({len(self.exchanges[__exchange])} акций)')
        logger.info(f'\n            Получены актуальные расписания на '
                    f'{now().strftime("%y-%m-%d %H:%M:%S")} UTC+00\n'
                    f'{self.message_shedulers}')