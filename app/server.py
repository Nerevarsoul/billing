import logging
import os

import aiopg
from aiohttp import web

from app.sql import *
from app.utils import get, exchange_amount


async def init_pg(app):
    app['conn'] = await aiopg.connect(os.environ.get('DSN'))
    return app


async def close_pg(app):
    app['conn'].close()


async def create_account(request):
    data = await request.json()
    async with app['conn'].cursor() as cursor:
        try:
            await cursor.execute(
                'INSERT INTO accounts (currency, overdraft) VALUES',
                (data.get('currency'), data.get('overdraft'))
            )
            account = await get(cursor)
        except Exception as exc:
            logging.error(exc)
            return web.json_response({'status': 'error', 'message': 'Database error'})
    return web.json_response({'status': 'ok', 'id': account.id})


async def transfer_money(request):
    data = await request.json()
    amount = data.get('amount')
    donor_id = data.get('donor_id')
    recipient_id = data.get('recipient_id')
    async with app['conn'].cursor() as cursor:
        try:
            await cursor.execute('BEGIN transaction;')
            await cursor.execute(FETCH_ACCOUNT, (donor_id,))
            donor_account = await get(cursor)
            await cursor.execute(FETCH_ACCOUNT, (recipient_id,))
            recipient_account = await get(cursor)
            total_amount = exchange_amount(donor_account, recipient_account, amount)
            if donor_account.overdraft or donor_account.balance - total_amount > 0:
                await cursor.execute(
                    UPDATE_BALANCE, (recipient_account.balance + amount, recipient_id)
                )
                await cursor.execute(
                    UPDATE_BALANCE, (donor_account.balance - total_amount, donor_id)
                )
            await cursor.execute('COMMIT transaction;')
        except Exception as exc:
            logging.error(exc)
            return web.json_response({'status': 'error', 'message': 'Database error'})
    return web.json_response({'status': 'ok', 'res': {'currency': recipient_account.currency, 'amount': amount}})


async def request_balance(request):
    data = await request.json()
    id = data.get('id')
    if id:
        async with app['conn'].cursor() as cursor:
            try:
                await cursor.execute(FETCH_ACCOUNT, (id,))
                account = await get(cursor)
            except Exception as exc:
                logging.error(exc)
                return web.json_response({'status': 'error', 'message': 'Database error'})
    else:
        return web.json_response({'status': 'error', 'message': 'account does not exist!'})
    return web.json_response({'status': 'ok', 'res': {'currency': account.currency, 'balance': account.balance}})


if __name__ == '__main__':
    app = web.Application()
    logging.basicConfig(filename='log.log', level=logging.ERROR)
    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)
    app.router.add_post('/create_account', create_account)
    app.router.add_post('/transfer_money', transfer_money)
    app.router.add_get('/request_balance', request_balance)
    web.run_app(app, host='0.0.0.0', port=8080)
