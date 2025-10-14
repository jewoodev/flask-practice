import base64
import uuid

import requests

# 1. Access Token 받기
client_id = 'your id'
client_secret = 'your secret'
credentials = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()

response = requests.post(
    "https://onlinetools.ups.com/security/v1/oauth/token",
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {credentials}"
    },
    data={
        "grant_type": "client_credentials"
    }
)

# 응답 확인
print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")

if response.status_code != 200:
    print(f"Error: {response.text}")
    exit()

token_data = response.json()
access_token = token_data['access_token']

print(f"Access Token: {access_token}")

# 2. Tracking API 호출
inquiry_number = "1ZT617T70390595200"  # 실제 운송장 번호로 변경

tracking_response = requests.get(
    f"https://onlinetools.ups.com/api/track/v1/details/{inquiry_number}",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "transId": str(uuid.uuid4()),  # 필수: 고유 식별자
        "transactionSrc": "testing"     # 필수: 클라이언트/소스 애플리케이션 식별
    },
    params={
        "locale": "en_US",              # 선택: 기본값 en_US
        "returnSignature": "false",     # 선택: 서명 이미지 포함 여부
        "returnMilestones": "false",    # 선택: 마일스톤 반환 여부
        "returnPOD": "false"            # 선택: 배송 증명 반환 여부
    }
)

tracking_json = tracking_response.json()

shipment = tracking_json['trackResponse']['shipment'][0]
package = shipment['package'][0]
current_status = package['currentStatus']['code']

print(f"Current Status: {current_status}")

# 배송 완료
delivered_codes = ['011', '026', '143', '144', '161']

# 배송 출발 (배송 기사가 배송 중)
out_for_delivery_codes = ['006', '021', '037', '060', '061', '062', '089', '091', '146', '162']

# 배송 중 (운송 중)
in_transit_codes = [
    '005', '010', '025', '039', '044', '045', '047', '071', '072', '073', '074',
    '087', '158', '159', '164', '165'
]

# 통관/보관 중
clearance_codes = ['012', '014', '016', '092', '123', '124', '125', '126', '134']

# 배송 준비 중
pending_codes = ['000', '003', '038', '079', '080', '157', '160', '166', '167', '168', '169']

result = "null"
if current_status in delivered_codes:
    result = "배송완료"
elif current_status in out_for_delivery_codes:
    result = "배송 중"
elif current_status in in_transit_codes:
    result = "배송 중"
elif current_status in clearance_codes:
    result = "배송 중"

print(f"Status Code: {result}")