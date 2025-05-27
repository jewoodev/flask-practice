from dhl import db


class Orders(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True, info='자동증가')
    order_status = db.Column(db.String(40), nullable=False, server_default="Requested")
    shipping_company = db.Column(db.String(10), nullable=True)