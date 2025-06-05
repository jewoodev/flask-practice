from datetime import datetime
import datetime as tz

import pytest

from dhl import create_app, db
from dhl.config import TestConfig
from dhl.models import Order
from dhl.service.scheduler import renew_order_status

@pytest.fixture
def app():
    app = create_app(TestConfig)
    app.config.update({
        "TESTING": True,
    })
    return app

@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield
        Order.query.delete()
        db.session.commit()
        db.session.close()

def test_renew_order_status(app, app_ctx):
    orders = []

    fedex_order = Order(
        id=1,
        order_status="Delivering",
        shipping_company="FedEx",
        waybill_number=772624362112,
        created_at=datetime.now(tz.UTC),
        updated_at = datetime.now(tz.UTC)
    )
    orders.append(fedex_order)

    fedex_order2 = Order(
        id=2,
        order_status="Delivering",
        shipping_company="FedEx",
        waybill_number=881689397865,
        created_at=datetime.now(tz.UTC),
        updated_at=datetime.now(tz.UTC)
    )
    orders.append(fedex_order2)

    fedex_order3 = Order(
        id=3,
        order_status="Delivering",
        shipping_company="FedEx",
        waybill_number=881475889777,
        created_at=datetime.now(tz.UTC),
        updated_at=datetime.now(tz.UTC)
    )
    orders.append(fedex_order3)

    fedex_order4 = Order(
        id=4,
        order_status="Delivering",
        shipping_company="FedEx",
        waybill_number=881689506053,
        created_at=datetime.now(tz.UTC),
        updated_at=datetime.now(tz.UTC)
    )
    orders.append(fedex_order4)

    fedex_order5 = Order(
        id=5,
        order_status="Delivering",
        shipping_company="FedEx",
        waybill_number=7779582237606,
        created_at=datetime.now(tz.UTC),
        updated_at=datetime.now(tz.UTC)
    )
    orders.append(fedex_order5)

    db.session.add_all(orders)
    db.session.commit()

    renew_order_status()


    assert Order.query.filter_by(id = 1).first().order_status == 'Pending_confirmation'
    assert Order.query.filter_by(id = 2).first().order_status == 'Pending_confirmation'
    assert Order.query.filter_by(id = 3).first().order_status == 'Pending_confirmation'
    assert Order.query.filter_by(id = 4).first().order_status == 'Pending_confirmation'
    assert Order.query.filter_by(id = 5).first().order_status == 'Pending_confirmation'
