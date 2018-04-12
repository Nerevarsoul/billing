import asyncio
import os

import aiopg


async def create_db():
    async with aiopg.connect(os.environ.get('DSN')) as conn:
        async with conn.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE accounts ("
                "id integer primary key autoincrement, "
                "currency text, "
                "balance integer default 0, "
                "overdraft boolean default 0"
                ")"
            )
            cursor.execute(
                "CREATE TABLE accounts ("
                "id integer primary key autoincrement, "
                "donor_id integer, "
                "recipient_id integer, "
                "amount decimal"
                ")"
            )


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_db())
