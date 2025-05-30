from datetime import datetime, timedelta
import datetime as tz

from dhl import db
from dhl.models import Order
from dhl.service.dto import FedExDTO, DHLDTO
from dhl.service.shipping_tracking_service import renew_fedex_delivery_status, renew_dhl_delivery_status, logger


def renew_order_status():

    try:
        start_datetime = datetime.now(tz.UTC) + timedelta(days=-180)
        end_datetime = datetime.now(tz.UTC)

        order_query_to_be_renewed = db.session.query(Order).filter(
            Order.order_status == 'Delivering',
            Order.created_at >= start_datetime)

        otr_page = order_query_to_be_renewed.paginate(page=1, per_page=30, error_out=False)
        total_page_count = otr_page.pages

        if total_page_count > 0:
            str_start_datetime = start_datetime.strftime('%Y-%m-%d')
            str_end_datetime = end_datetime.strftime('%Y-%m-%d')

            for page in range(1, total_page_count + 1):
                order_portion = order_query_to_be_renewed.paginate(page=page, per_page=30, error_out=False)
                fedex_tracking_pairs = {}
                dhl_tracking_pairs = {}

                for od in order_portion.items:
                    if od.shipping_company == 'FedEx':
                        fedex_tracking_pairs[od.waybill_number] = od.id
                    elif od.shipping_company == 'DHL':
                        dhl_tracking_pairs[od.waybill_number] = od.id

                if len(fedex_tracking_pairs) > 0:
                    renew_fedex_delivery_status(
                        FedExDTO(
                            trackingPairs=fedex_tracking_pairs,
                            beginDate=str_start_datetime,
                            endDate=str_end_datetime
                        )
                    )
                if len(dhl_tracking_pairs) > 0:
                    renew_dhl_delivery_status(
                        DHLDTO(
                            trackingPairs=dhl_tracking_pairs,
                            levelOfDetail='all',
                            trackingView='last-checkpoint'
                        )
                    )
    except Exception as ex:
        db.session.rollback()
        logger.error(f'주문 상태 갱신 중 오류[배송관련] {ex}')
    finally:
        db.session.close()