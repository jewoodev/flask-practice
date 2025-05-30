from dataclasses import dataclass


@dataclass
class FedExDTO:
    trackingPairs: dict[int] # 운송장 번호를 Key로, 그 운송장 번호에 매칭되는 Order의 id를 Value로 갖는 dict
    beginDate: str
    endDate: str

@dataclass
class DHLDTO:
    trackingPairs: dict[int] # 운송장 번호를 Key로, 그 운송장 번호에 매칭되는 Order의 id를 Value로 갖는 dict
    levelOfDetail: str
    trackingView: str