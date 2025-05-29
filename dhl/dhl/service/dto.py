from dataclasses import dataclass


@dataclass
class FedExDTO:
    trackingNumbers: list[str]
    beginDate: str
    endDate: str
    orderIds: list[int]

@dataclass
class DHLDTO:
    shipmentTrackingNumber: list[str]
    levelOfDetail: str
    trackingView: str