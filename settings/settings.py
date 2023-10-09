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


'''
Logging development
'''
from loguru import logger

'''
Other libs
'''
import configparser
import asyncio
import time
from datetime import timedelta
import pandas as pd
import openpyxl
from functools import wraps

SQLITE_PATH = ('dbfile/operational.db')
LOG_SCHEDULE_PATH = 'data/logfile/schedule.log'

config = configparser.ConfigParser()
config.read('settings/settings.ini')


def config_update():
    with open('settings/settings.ini', 'w', encoding='utf-8') as file:
        config.write(file)
    config.read(file)  # обновляем конфигурацию

import logging
logging.basicConfig(
    level=logging.INFO,
    filename='data/logs.log',
    format="%(asctime)s - %(module)s\n[%(levelname)s] %(funcName)s:\n %(lineno)d - %(message)s",
    datefmt='%H:%M:%S',
    encoding="utf-8"
)

if __name__ == "__main__":
    pass
    # try:
    #     print(config['Telegram']['api'])
    # except:
    #     print('не записался')
    #
    # print(config.sections())
    # print(config.items('Telegram'))
    # #config['Telegram']['username'] = 'кто-то'
    # # config_update()
