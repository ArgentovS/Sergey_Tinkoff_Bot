from settings import *
from tools.db import *

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(collect_candle(loop, 5))
