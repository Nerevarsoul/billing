from collections import namedtuple

from app.constants import EXCHANGE_MAP

Account = namedtuple('Account', 'id currency balance overdraft',)

async def get(cursor):
    res = []
    async for row in cursor:
        res.append(Account(row[0]))
    return res[0]


def exchange_amount(donor, recipient, amount):
    if donor.currency == recipient.currency:
        return amount
    else:
        return amount * EXCHANGE_MAP[f'{donor.currency}_{recipient.currency}']
