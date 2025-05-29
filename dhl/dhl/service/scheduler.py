from datetime import datetime, timedelta
import datetime as tz

from flask import app

from dhl.repository import order_repository
from dhl.service.dto import FedExDTO, DHLDTO
from dhl.service.shipping_tracking_service import update_fedex_delivery_status, update_dhl_delivery_status, logger


def renew_order_status():

    try:
        start_datetime = datetime.now(tz.UTC) + timedelta(days=-180)
        end_datetime = datetime.now(tz.UTC)

        order = order_repository.find_by_order_status_and_after('Delivering', start_datetime)

        search_tmp = order.paginate(page=1, per_page=30, error_out=False)
        total_page_count = search_tmp.pages

        if total_page_count > 0:
            str_start_datetime = start_datetime.strftime('%Y-%m-%d')
            str_end_datetime = end_datetime.strftime('%Y-%m-%d')

            for page in range(1, total_page_count + 1):
                order_portion = order.paginate(page=page, per_page=30, error_out=False)
                fedex_tracking_numbers = []
                fedex_order_id_list = []
                dhl_tracking_numbers = []
                dhl_order_id_list = []

                for od in order_portion.items:
                    if od.shipping_company == 'FedEx':
                        fedex_tracking_numbers.append(od.waybill_number)
                        fedex_order_id_list.append(od.id)
                    elif od.shipping_company == 'DHL':
                        dhl_tracking_numbers.append(od.waybill_number)
                        dhl_order_id_list.append(od.id)

                if len(fedex_tracking_numbers) > 0:
                    update_fedex_delivery_status(
                        FedExDTO(
                            trackingNumbers=fedex_tracking_numbers,
                            beginDate=str_start_datetime,
                            endDate=str_end_datetime,
                            orderIds=fedex_order_id_list
                        )
                    )
                if len(dhl_tracking_numbers) > 0:
                    update_dhl_delivery_status(
                        DHLDTO(
                            shipmentTrackingNumber=dhl_tracking_numbers,
                            levelOfDetail='all',
                            trackingView="last-checkpoint"
                        )
                    )
    except Exception as ex:
        order_repository.rollback()
        logger.error(f'주문 상태 갱신 중 오류[배송관련] {ex}')
    finally:
        order_repository.close()