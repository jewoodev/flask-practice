import unittest
import logging
from unittest.mock import patch, MagicMock

import pytest

from dhl import db, create_app
from dhl.config import TestConfig
from dhl.models import (Orders)
from dhl.service.manage_shipping_tracking import update_delivery_status

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def app():
    app = create_app(TestConfig)
    app.app_context().push()

    app.config.update({
        "TESTING": True,
    })
    db.init_app(app)

    yield app

    db.session.query(Orders).delete()
    db.session.commit()

def test_log():
    logger.debug("debug msg")
    logger.info("info msg")

    assert True

def test_update_delivery_status_success(app):
    # 테스트용 주문 데이터 생성
    test_order = Orders(
        id=1,
        order_status="Requested",
        shipping_company="FedEx"
    )
    db.session.add(test_order)
    db.session.commit()

    tracking_numbers = ['881445844117']
    order_ids = [1]  # 테스트용 주문 ID

    result, error = update_delivery_status(tracking_numbers, '2025-05-01', '2025-05-27', order_ids)

    logger.debug(f"Update delivery status response is {result}")

    # 검증
    assert result is not None
    assert error is None

    # 주문 상태 업데이트 확인
    updated_order = Orders.query.get(1)
    assert updated_order.order_status == "Delivered"

def test_update_delivery_status_api_error(app):
    # 테스트용 주문 데이터 생성
    test_order = Orders(
        id=1,
        order_status="Requested",
        shipping_company="FedEx"
    )
    db.session.add(test_order)
    db.session.commit()

    # Mock API error response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason = 'Not Found'

    expected_return_value = (None, mock_response)

    tracking_numbers = ['881445844117']
    order_ids = [1]

    result, error = update_delivery_status(tracking_numbers, '2025-05-01', '2025-05-27', order_ids)
    logger.error(f'test_update_delivery_status_api_error {error}')

    # 검증
    assert result is None
    assert error is not None

    # 주문 상태가 변경되지 않았는지 확인
    order = Orders.query.get(1)
    assert order.order_status == "Requested"

def test_update_delivery_status_invalid_tracking(app):
    # 테스트용 주문 데이터 생성
    test_order = Orders(
        id=1,
        order_status="Requested",
        shipping_company="FedEx"
    )
    db.session.add(test_order)
    db.session.commit()

    tracking_numbers = ['invalid_number']
    order_ids = [1]

    result, error = update_delivery_status(tracking_numbers, '2025-05-01', '2025-05-27', order_ids)
    logger.error(f'test_update_delivery_status_invalid_tracking error {error}')

    # 검증
    assert result is None
    assert error is not None

    # 주문 상태가 변경되지 않았는지 확인
    order = Orders.query.get(1)
    assert order.order_status == "Requested"

def test_update_delivery_status_invalid_date_format(app):
    # 테스트용 주문 데이터 생성
    test_order = Orders(
        id=1,
        order_status="Requested",
        shipping_company="FedEx"
    )
    db.session.add(test_order)
    db.session.commit()

    tracking_numbers = ['881445844117']
    order_ids = [1]

    # 잘못된 날짜 형식으로 테스트
    result, error = update_delivery_status(tracking_numbers, 'invalid-date', '2025-05-27', order_ids)
    logger.error(f'test_update_delivery_status_invalid_date_format {error}')

    # 검증
    assert result is None
    assert error is not None
