''''''
'''
Application development
'''
import asyncio
from loguru import logger
import configparser
import time
from datetime import timedelta
import pandas as pd
import openpyxl
from functools import wraps


'''
Bot development
'''
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router, types, F
from aiogram.types import Message
from aiogram.filters import Command


'''
SQL Database development
'''
import aiomysql
import aiosqlite


'''
Tinkoff API development 
'''
from tinkoff.invest import Client, Instrument, AsyncClient, CandleInterval
from tinkoff.invest.retrying.aio.client import AsyncRetryingClient
from tinkoff.invest.retrying.settings import RetryClientSettings
from tinkoff.invest.utils import now


SQLITE_PATH = ('dbfile/operational.db')  # Путь к базе sqlite
LOG_SCHEDULE_PATH = 'data/logfile/schedule.log'  # Путь к логфайлам

EXCESS_VOLUME = 0.5  # Коэффициент превышения объёма над среднем для отправки данных в бот
USERS = [389726986]  # 6251198210]  #, 228248763, 2022125420]  # Список пользователей чата

TIME_MORNING_MESSAGE = (now() + timedelta(hours=3)).strftime('%H')  # Время отправки пользователям утреннего сообщения

config = configparser.ConfigParser()
config.read('settings/settings.ini')


def config_update():
    with open('settings/settings.ini', 'w', encoding='utf-8') as file:
        config.write(file)
    config.read(file)  # обновляем конфигурацию


if __name__ == "__main__":
    pass