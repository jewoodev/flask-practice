from dhl import db
from dhl.models import Order

def insert(order):
    return db.session.add(order)

def find_by_id(id):
    return db.session.query(Order).filter(Order.id == id).first()

def delete_all():
    return db.session.query(Order).delete()

def commit():
    return db.session.commit()

def rollback():
    return db.session.rollback()

def flush():
    return db.session.flush()