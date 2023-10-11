from settings import *


# Сформируем базу данных для оперативных переменных
async def set_operation_db():
    async with aiosqlite.connect('data/dbfile/sqlbasa1.db/') as conn:
        cur = await conn.cursor()
        await cur.execute("""CREATE TABLE IF NOT EXISTS schedules 
                                            (datetime_registration TEXT,
                                            dete_schedules TEXT,
                                            is_trading INTEGER,
                                            exchange TEXT,
                                            start_time TEXT,
                                            end_time TEXT);""")

        #await db.execute("INSERT INTO some_table ...")
        await conn.commit()



async def collect_candle(limit=0):
    loop = asyncio.get_event_loop()
    pool = await aiomysql.create_pool(host=config['SQL']['host'],
                                      port=3306,
                                      user = config['SQL']['user'],
                                      password = config['SQL']['password'],
                                      db=config['SQL']['db_name'],
                                      loop=loop)
    async with pool.acquire() as con:
        cur = await con.cursor()
        await cur.execute('SELECT * FROM AKRN')
        if limit:
            rows = cur.fetchmany(limit)
        else:
            rows = cur.fetchall()
        print(rows)
    return rows


async def set_collect_1_min_candels(candle_time, figi, volume, is_complete, now_time):
    loop = asyncio.get_event_loop()
    conn = await aiomysql.connect(host=config['SQL']['host'],
                                    port=config.getint('SQL', 'host'),
                                    user=config['SQL']['user'],
                                    password=config['SQL']['password'],
                                    db=config['SQL']['db_name'],
                                    loop=loop, autocommit=True)
    cur = await conn.cursor()
    async with conn.cursor() as cur:
        #await cur.execute("DROP TABLE IF EXISTS music_style;")
        await cur.execute("""CREATE TABLE IF NOT EXISTS operative_candles 
                                (candle_time DATETIME, figi VARCHAR(12), 
                                volume INTEGER, is_complete VARCHAR(12), 
                                now_time DATETIME(6));""")

        # insert 1 rows
        await cur.execute(f"INSERT INTO operative_candles VALUES "
                          f"('{candle_time}',"
                          f"'{figi}', {volume},"
                          f"'{is_complete}', '{now_time}');")

    conn.close()


if __name__ == '__main__':
    pass