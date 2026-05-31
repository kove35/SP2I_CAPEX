from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4

from app.utils.json_safe import sanitize_for_json


def main():
    obj = {"dt": datetime(2026, 5, 30, 12, 34, 56), "d": date(2026, 5, 30)}
    out = sanitize_for_json(obj)
    print('dt ->', out['dt'])
    print('d  ->', out['d'])

    obj2 = {"price": Decimal('123.45'), "id": uuid4()}
    out2 = sanitize_for_json(obj2)
    print('price ->', out2['price'], type(out2['price']))
    print('id    ->', out2['id'], type(out2['id']))


if __name__ == '__main__':
    main()
