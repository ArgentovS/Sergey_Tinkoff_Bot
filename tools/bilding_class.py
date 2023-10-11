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
        self.message_shedulers = 'Расписание торгов на сегодня:\n'
        for __exchange in self.shedulers.keys():
            if self.shedulers[__exchange][0].is_trading_day:  # Если текущая дата - дата торгов на Мосбирже
                self.is_trading = True
                self.message_shedulers += (f'\n |  {__exchange}:\n'
                                           f'    c {utc3(self.shedulers[__exchange][0].start_time).strftime("%H-%M")}'
                                           f' до {utc3(self.shedulers[__exchange][0].end_time).strftime("%H-%M")}\n')
        if not self.is_trading:
            for day in range(len(self.shedulers[__exchange])-1, 0, -1):
                self.message_shedulers = (f'Сегодня торгов нет\n'
                                          f'Расписание торгов на {self.shedulers[__exchange][day].date.strftime("%y-%m-%d")}:\n')
                for __exchange in self.shedulers.keys():
                    if self.shedulers[__exchange][day].is_trading_day:
                        self.trading_day = self.shedulers[__exchange][day].date.strftime('%y-%m-%d')
                        self.message_shedulers += (f'\n |  {__exchange}:\n'
                                                   f'    c {utc3(self.shedulers[__exchange][day].start_time).strftime("%H-%M")}'
                                                   f' до {utc3(self.shedulers[__exchange][day].end_time).strftime("%H-%M")}\n')

    def prn_shares(self):
        print(self.shares)
        return self.shares

    def prn_exchanges(self):
        print(self.exchanges)
        return self.exchanges

    def prn_shedulers(self):
        print(self.shedulers)
        return self.shedulers


class AlertGenerator:

    def __init__(self, time_cn=0, volume_cn=0):
        self.__time_cn = time_cn
        self.__volume_cn = volume_cn

    @property
    def time_cn(self):
        return self.__time_cn

    @time_cn.setter
    def time_cn(self, t):
        if t > 0:
            self.__time_cn = t
        else:
            raise ValueError

    @property
    def volume_cn(self):
        return self.__volume_cn

    @volume_cn.setter
    def volume_cn(self, v):
        if v > 0:
            self.volume_cn = v
        else:
            raise ValueError
