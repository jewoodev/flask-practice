import json

import requests
from datetime import datetime, timedelta
import datetime as tz

from dhl import logger, db
from dhl.common.common_function import CommonFunc
from dhl.models import Order
from dhl.service.dto import FedExDTO, DHLDTO

class FedExToken:
    _access_token = None
    _token_type = None
    _scope = None
    _expireDateTime = None

    def get_refresh_token(self):
        try:
            url = CommonFunc.get_config_val('FEDEX_API_URL') + '/oauth/token'
            headers = {'Content-Type': 'application/x-www-form-urlencoded', }
            data = {'grant_type': 'client_credentials', 'client_id': CommonFunc.get_config_val('FEDEX_API_KEY'),
                    'client_secret': CommonFunc.get_config_val('FEDEX_SECRET_KEY'), }
            response = requests.post(url, headers=headers, data=data)

            response_json = json.loads(response.text) if response and response.status_code == 200 else None

            if response_json and 'access_token' in response_json and 'token_type' in response_json \
                    and 'expires_in' in response_json and 'scope' in response_json:

                access_token = response_json['access_token']
                token_type = response_json['token_type']
                expires_in = response_json['expires_in']
                scope = response_json['scope']
                self._expireDateTime = datetime.now(tz.UTC) + timedelta(seconds=(expires_in - 600))
                self._access_token = access_token
                self._token_type = token_type
                self._scope = scope

                return self.get_token()

            logger.error('Get refresh token failed with invalid response')
            return None

        except Exception as ex:
            logger.error(ex)

    def get_token(self):
        try:
            if (self._access_token and self._token_type and self._expireDateTime and self._expireDateTime >
                    datetime.now(tz.UTC)):
                return self._token_type + ' ' + self._access_token
        except Exception as ex:
            logger.error(ex)

        return None

_token = FedExToken()

def renew_fedex_delivery_status(dto: FedExDTO):
    response_json, response = call_fedex_api(dto)

    if not response or response.status_code != 200:
        logger.error(f"배송 상태 업데이트 요청에 실패, 응답은 {response_json}")
        logger.error(f'{response}')
        return None, f'error {response.status_code} {response.reason}'

    data = check_fedex_response_and_update_order_status(dto, response_json)

    logger.info(f"배송 추적 응답 => {data}")
    return data, None


def check_fedex_response_and_update_order_status(dto: FedExDTO, response_json):
    data = []
    complete_track_results = response_json['output']['completeTrackResults']
    for key in dto.trackingPairs: # 담겨진 trackingPairs를 순회하며 update
        cur_tracking_number = key
        cur_order_id = dto.trackingPairs[key]
        # 이번 순서의 complete_track_result를 찾아
        complete_track_result = next(
            filter(lambda i: 'trackingNumber' in i and i['trackingNumber'] == cur_tracking_number, complete_track_results),
            None)
        if complete_track_result:
            # trackResults 값을 검증, 그 하위의 값들도 검증하여 리턴할 dict에 append한다.
            track_results = complete_track_result['trackResults']
            latest_status_detail = track_results[0]['latestStatusDetail'] \
                if (len(track_results) > 0 and 'latestStatusDetail' in track_results[0]) \
                else None
            scan_events = track_results[0]['scanEvents'] \
                if (track_results[0] and 'scanEvents' in track_results[0]) \
                else None
            code = latest_status_detail['code'] \
                if (latest_status_detail and 'code' in latest_status_detail) \
                else None

            if cur_tracking_number and code:
                if code == 'DL' and len(scan_events) > 0:
                    scan_event = next(filter(lambda i: 'eventType' in i and i['eventType'] == 'DL', scan_events), None)
                    if not scan_event:
                        data.append(
                            {'order_id': None, 'trackingNumber': cur_tracking_number, 'code': code, 'order_status': None})
                    else:
                        order_to_update = Order.query.filter_by(id = cur_order_id).first()

                        if order_to_update:
                            if 'date' in scan_event:
                                completed_date_time = datetime.strptime(scan_event['date'], '%Y-%m-%dT%H:%M:%S%z')
                                completed_date_time = completed_date_time.astimezone(completed_date_time.tzinfo.utc)
                            else:
                                completed_date_time = None

                            if order_to_update.order_status == 'Delivering':
                                order_to_update.order_status = 'Pending_confirmation'
                                data.append({'order_id': order_to_update.id, 'trackingNumber': cur_tracking_number, 'code': code,
                                             'order_status': 'Pending_confirmation',
                                             'completed_date_time': completed_date_time})
            else:
                code = track_results[0]['error']['code']
                data.append({'order_id': None, 'trackingNumber': cur_tracking_number, 'code': code,
                             'order_status': None, 'completed_date_time': None})
    return data

def call_fedex_api(dto: FedExDTO):
    url = CommonFunc.get_config_val('FEDEX_API_URL') + '/track/v1/trackingnumbers'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': get_cache_token()
    }

    body = make_fedex_request_body(dto)

    response = requests.post(url, headers=headers, data=body)
    return json.loads(response.text), response

def make_fedex_request_body(dto: FedExDTO):
    try:
        tracking_info = []
        for tracking_number in dto.trackingPairs:
            tracking_info.append({"shipDateBegin": dto.beginDate, "shipDateEnd": dto.endDate,
                                  "trackingNumberInfo": {
                "trackingNumber": tracking_number}})
        data = {"includeDetailedScans": True, "trackingInfo": tracking_info}
        return json.dumps(data)
    except Exception as ex:
        logger.error(ex)

    return None, None

def get_cache_token():
    try:
        token = _token.get_token() if _token else None
        return token if token else get_token()
    except Exception as ex:
        logger.error(ex)
        return None

def get_token():
    try:
        return _token.get_refresh_token()
    except Exception as ex:
        logger.error(ex)
        return None

def renew_dhl_delivery_status(dto: DHLDTO):
    response_json, response = call_dhl_api(dto)

    if not response or response.status_code != 200:
        logger.error(f"배송 상태 업데이트 요청에 실패, 응답은 {response_json}")
        logger.error(f'{response}')
        return None, f'error {response.status_code} {response.reason}'


    data = check_dhl_response_and_update_delivery_status(dto, response_json)

    logger.info(f"배송 추적 응답 => {data}")
    return data, None

def call_dhl_api(dto: DHLDTO):
    url = CommonFunc.get_config_val('DHL_API_URL')
    headers = {
        'Authorization': 'Basic ' + CommonFunc.get_config_val('DHL_AUTH_KEY'),
        'Accept-Language': 'kor'
    }

    payload = {
        'shipmentTrackingNumber': dto.trackingPairs.keys(),
        'trackingView': dto.trackingView,
        'levelOfDetail': dto.levelOfDetail
    }

    response = requests.get(url, params=payload, headers=headers)
    return json.loads(response.text), response

def check_dhl_response_and_update_delivery_status(dto: DHLDTO, response_json):
    data = []

    for shipment in response_json['shipments']:
        cur_tracking_number = shipment['shipmentTrackingNumber']
        cur_order_id = dto.trackingPairs[cur_tracking_number]
        pieces = shipment['pieces']
        for piece in pieces:
            last_checkpoint = piece['events'][0]
            type_code = last_checkpoint['typeCode']
            if type_code == 'OK':
                waybill_number = shipment['shipmentTrackingNumber']
                order_to_update = Order.query.filter_by(id=cur_order_id).first()
                order_to_update.order_status = 'Pending_confirmation'
                data.append({'shipmentTrackingNumber': waybill_number, 'typeCode': type_code})

    return data
