from datetime import datetime
from typing import Iterable

from dhl import db
from dhl.models import Order

def insert(order: Order):
    return db.session.add(order)

def insert_all(orders: Iterable[Order]):
    return db.session.add_all(orders)

def find_by_id(id: int):
    return db.session.query(Order).filter(Order.id == id).first()

def find_by_order_status_and_after(order_status: str, start_datetime: datetime):
    return db.session.query(Order).filter(
        Order.order_status == order_status,
        Order.created_at >= start_datetime
    )

def find_by_waybill_number(waybill_number: str):
    return db.session.query(Order).filter(
        Order.waybill_number == waybill_number
    ).first()

def delete_all():
    return db.session.query(Order).delete()

def commit():
    return db.session.commit()

def rollback():
    return db.session.rollback()

def flush():
    return db.session.flush()

def close():
    return db.session.close()