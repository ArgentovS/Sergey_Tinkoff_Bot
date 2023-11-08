from settings import *
from tools.tinkoffAPI import *
from tools.utils import *
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Quotation:
    """
    Тип данных для хрананеия цен
    """
    units: int
    nano: int


@dataclass
class BotCandle:
    """
    Класс для фиксации данных о свечах
    """
    open: Quotation
    high: Quotation
    low: Quotation
    close: Quotation
    volume: int
    time: datetime
    is_complete: bool
    previous_volume: int

