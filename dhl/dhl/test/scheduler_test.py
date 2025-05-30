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
        waybill_number=881445844117,
        created_at=datetime.now(tz.UTC),
        updated_at = datetime.now(tz.UTC)
    )
    orders.append(fedex_order)

    dhl_order1 = Order(
        id=2,
        order_status="Delivering",
        shipping_company="DHL",
        waybill_number=4745183870,
        created_at=datetime.now(tz.UTC),
        updated_at=datetime.now(tz.UTC)
    )
    orders.append(dhl_order1)

    dhl_order2 = Order(
        id=3,
        order_status="Delivering",
        shipping_company="DHL",
        waybill_number=5584773180,
        created_at=datetime.now(tz.UTC),
        updated_at=datetime.now(tz.UTC)
    )
    orders.append(dhl_order2)

    db.session.add_all(orders)
    db.session.commit()

    renew_order_status()


    assert Order.query.filter_by(id = 1).first().order_status == 'Pending_confirmation'
    assert Order.query.filter_by(id = 2).first().order_status == 'Pending_confirmation'
    assert Order.query.filter_by(id = 3).first().order_status == 'Pending_confirmation'
