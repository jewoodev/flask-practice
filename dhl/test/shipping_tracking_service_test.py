import logging
from unittest.mock import patch, MagicMock

import pytest
from humanfriendly.usage import render_usage

from dhl import db, create_app
from dhl.config import TestConfig
from dhl.models import (Order)
from dhl.repository import order_repository
from dhl.service.shipping_tracking_service import update_delivery_status

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def app():
    app = create_app(TestConfig)
    app.config.update({
        "TESTING": True,
    })
    db.init_app(app)
    return app

@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield
        order_repository.delete_all()
        order_repository.commit()

def test_log(app, app_ctx):
    logger.debug("debug msg")
    logger.info("info msg")

    assert True

def test_update_delivery_status_success(app, app_ctx):
    # 테스트용 주문 데이터 생성
    test_order = Order(
        id=1,
        order_status="Delivering",
        shipping_company="FedEx"
    )
    order_repository.insert(test_order)
    order_repository.commit()

    tracking_numbers = ['881445844117']
    order_ids = [1]  # 테스트용 주문 ID

    result, error = update_delivery_status(tracking_numbers, '2025-05-01', '2025-05-27', order_ids)

    # 검증
    assert result != []
    assert error is None

    # 주문 상태 업데이트 확인
    updated_order = Order.query.get(1)
    assert updated_order.order_status == "Pending_confirmation"

def test_update_delivery_status_invalid_tracking(app, app_ctx):
    # 테스트용 주문 데이터 생성
    test_order = Order(
        id=1,
        order_status="Delivering",
        shipping_company="FedEx"
    )
    order_repository.insert(test_order)
    order_repository.commit()

    tracking_numbers = ['invalid_number']
    order_ids = [1]

    # 잘못된 운송장 번호로 배송 추적
    result, error = update_delivery_status(tracking_numbers, '2025-05-01', '2025-05-27', order_ids)

    result_code = result[0]['code']

    # 검증
    assert result_code == 'TRACKING.TRACKINGNUMBER.INVALID'
    assert error is None

    # 주문 상태가 변경되지 않았는지 확인
    order = Order.query.get(1)
    assert order.order_status == "Delivering"

def test_update_delivery_status_invalid_date_format(app, app_ctx):
    # 테스트용 주문 데이터 생성
    test_order = Order(
        id=1,
        order_status="Delivering",
        shipping_company="FedEx"
    )
    order_repository.insert(test_order)
    order_repository.commit()

    tracking_numbers = ['881445844117']
    order_ids = [1]

    # 잘못된 날짜 형식으로 테스트
    result, error = update_delivery_status(tracking_numbers, 'invalid-date', '2025-05-27', order_ids)

    # 검증
    assert result is None
    assert error == "'output'"

    # 주문 상태가 변경되지 않았는지 확인
    order = Order.query.get(1)
    assert order.order_status == "Delivering"
