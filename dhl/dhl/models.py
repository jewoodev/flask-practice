from dhl import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_status = db.Column(db.String(40), nullable=False, server_default="Requested")
    shipping_company = db.Column(db.String(10), nullable=True)
    waybill_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)