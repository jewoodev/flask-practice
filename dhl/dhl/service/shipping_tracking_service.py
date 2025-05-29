import json

import requests
from datetime import datetime, timedelta
import datetime as tz

from dhl import logger
from dhl.common.common_function import CommonFunc
from dhl.repository import order_repository
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


def update_fedex_delivery_status(dto: FedExDTO):
    try:
        response_json, response = tracking_the_fedex_ship(dto)

        if not response or response.status_code != 200:
            logger.error(f"배송 상태 업데이트 요청에 실패, 응답은 {response_json}")
            logger.error(f'{response}')
            return None, f'error {response.status_code} {response.reason}'

        data = parsing_fedex_response_property(dto, response_json)

        order_repository.commit()
        logger.info(f"배송 추적 응답 => {data}")
        return data, None
    except Exception as ex:
        order_repository.rollback()
        logger.error(f"배송 추적 오류 => {ex}")
        return None, str(ex)


def parsing_fedex_response_property(dto, response_json):
    data = []
    complete_track_results = response_json['output']['completeTrackResults']
    index = -1
    for tracking_number in dto.trackingNumbers:
        index += 1
        # 이번 순서의 complete_track_result를 찾아
        complete_track_result = next(
            filter(lambda i: 'trackingNumber' in i and i['trackingNumber'] == tracking_number, complete_track_results),
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

            if tracking_number and code:
                if code == 'DL' and len(scan_events) > 0:
                    scan_event = next(filter(lambda i: 'eventType' in i and i['eventType'] == 'DL', scan_events), None)
                if not scan_event:
                    data.append(
                        {'order_id': order.id, 'trackingNumber': tracking_number, 'code': code, 'order_status': None})

                else:
                    order = None

                    if dto.orderIds and len(dto.orderIds) > 0:
                        order = order_repository.find_by_id(dto.orderIds[index])
                    if order:
                        completed_date_time = datetime.strptime(scan_event['date'], '%Y-%m-%dT%H:%M:%S%z') \
                            if 'date' in scan_event \
                            else None
                        completed_date_time = completed_date_time.astimezone(completed_date_time.tzinfo.utc) \
                            if completed_date_time else None

                        if order.order_status == 'Delivering':
                            order.order_status = 'Pending_confirmation'
                            order_repository.flush()
                            data.append({'order_id': order.id, 'trackingNumber': tracking_number, 'code': code,
                                         'order_status': 'Pending_confirmation',
                                         'completed_date_time': completed_date_time})
            else:
                code = track_results[0]['error']['code']
                data.append({'order_id': None, 'trackingNumber': tracking_number, 'code': code,
                             'order_status': None, 'completed_date_time': None})
    return data


def tracking_the_fedex_ship(dto: FedExDTO):
    try:
        tracking_info = []
        for tracking_number in dto.trackingNumbers:
            tracking_info.append({"shipDateBegin": dto.beginDate, "shipDateEnd": dto.endDate,
                                  "trackingNumberInfo": {
                "trackingNumber": tracking_number}})
        data = {"includeDetailedScans": True, "trackingInfo": tracking_info}
        return call_fedex_api('/track/v1/trackingnumbers', data)
    except Exception as ex:
        logger.error(ex)

    return None, None


def call_fedex_api(path, data):
    url = CommonFunc.get_config_val('FEDEX_API_URL') + path
    headers = {
        'Content-Type': 'application/json',
        'Authorization': get_cache_token()
    }

    data = json.dumps(data)

    response = requests.post(CommonFunc.get_config_val('FEDEX_API_URL') + path, headers=headers, data=data)
    return json.loads(response.text), response

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

def update_dhl_delivery_status(dto: DHLDTO):
    try:
        response_json, response = tracking_dhl_ship(dto)

        if not response or response.status_code != 200:
            logger.error(f"배송 상태 업데이트 요청에 실패, 응답은 {response_json}")
            logger.error(f'{response}')
            return None, f'error {response.status_code} {response.reason}'

        data = []

        for shipments in response_json['shipments']:
            pieces = shipments['pieces']
            for piece in pieces:
                last_checkpoint = piece['events'][0]
                description = last_checkpoint['description']
                if description == '수취인에게 배달되었습니다.':
                    waybill_number = shipments['shipmentTrackingNumber']
                    order = order_repository.find_by_waybill_number(waybill_number)
                    order.order_status = 'Pending_confirmation'
                    data.append({'shipmentTrackingNumber': waybill_number, 'description': description})

        order_repository.flush()
        order_repository.commit()
        logger.info(f"배송 추적 응답 => {data}")
        return data, None
    except Exception as ex:
        logger.error(f"배송 추적 오류 => {ex}")
        return None, str(ex)

    return None, None


def tracking_dhl_ship(dto: DHLDTO):
    headers = {
        'Authorization': 'Basic ******',
        'Accept-Language': 'kor'
    }

    payload = {
        'shipmentTrackingNumber': dto.shipmentTrackingNumber,
        'trackingView': dto.trackingView,
        'levelOfDetail': dto.levelOfDetail
    }

    response = requests.get('https://express.api.dhl.com/mydhlapi/test/tracking', params=payload, headers=headers)
    return json.loads(response.text), response
