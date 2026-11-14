from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Union


# ============================================================
# Trade Event
# ============================================================

@dataclass
class TradeEvent:
    """
    주식 실시간 체결 이벤트.
    Kiwoom WebSocket 0B 데이터를 정규화한다.
    """

    code: str
    timestamp: datetime

    price: int
    change: int
    change_pct: float

    best_ask: Optional[int] = None
    best_bid: Optional[int] = None

    # + : 매수체결
    # - : 매도체결
    volume: int = 0

    cum_volume: int = 0
    cum_turnover: int = 0

    # 원 단위
    # price * abs(volume)
    trade_turnover: int = 0

    large_order_net_flow: int = 0

    execution_strength: float = 0.0

    sell_execution_qty: Optional[int] = None
    buy_execution_qty: Optional[int] = None

    single_sell_execution_qty: Optional[int] = None
    single_buy_execution_qty: Optional[int] = None

    net_buy_execution_qty: Optional[int] = None

    # Kiwoom FID 1313 원본 값
    instant_turnover: Optional[int] = None

    # FID 311, 단위 억원
    market_cap_100m: Optional[int] = None

    market_session: Optional[str] = None
    exchange_type: Optional[str] = None

    source_timestamp: Optional[datetime] = None
    received_timestamp: Optional[datetime] = None


# ============================================================
# Orderbook Event
# ============================================================

@dataclass
class OrderbookEvent:
    """
    주식 10단 호가 이벤트.
    Kiwoom WebSocket 0D 데이터를 정규화한다.
    """

    code: str
    timestamp: datetime

    ask_prices: list[int] = field(default_factory=list)
    bid_prices: list[int] = field(default_factory=list)

    ask_qty: list[int] = field(default_factory=list)
    bid_qty: list[int] = field(default_factory=list)

    total_ask_qty: int = 0
    total_bid_qty: int = 0

    source_timestamp: Optional[datetime] = None
    received_timestamp: Optional[datetime] = None

    @property
    def best_ask(self) -> Optional[int]:
        if not self.ask_prices:
            return None

        return self.ask_prices[0]

    @property
    def best_bid(self) -> Optional[int]:
        if not self.bid_prices:
            return None

        return self.bid_prices[0]

    @property
    def top5_ask_qty(self) -> int:
        return sum(self.ask_qty[:5])

    @property
    def top5_bid_qty(self) -> int:
        return sum(self.bid_qty[:5])

    @property
    def bid_ask_depth_ratio(self) -> Optional[float]:
        """
        상위 5단 매수잔량 / 상위 5단 매도잔량.
        """

        ask_qty = self.top5_ask_qty

        if ask_qty <= 0:
            return None

        return self.top5_bid_qty / ask_qty

    @property
    def spread_bps(self) -> Optional[float]:
        """
        Bid-Ask Spread를 basis point 단위로 계산한다.

        spread_bps
        =
        (best_ask - best_bid)
        / mid_price
        * 10000
        """

        best_ask = self.best_ask
        best_bid = self.best_bid

        if best_ask is None or best_bid is None:
            return None

        if best_ask <= 0 or best_bid <= 0:
            return None

        mid_price = (
            best_ask + best_bid
        ) / 2.0

        if mid_price <= 0:
            return None

        return (
            (best_ask - best_bid)
            / mid_price
            * 10000.0
        )


# ============================================================
# Order Event
# ============================================================

@dataclass
class OrderEvent:
    """
    주문 접수 / 확인 / 상태 변경 이벤트.

    OrderEvent만으로 Position을 생성하지 않는다.
    """

    order_id: str
    code: str
    timestamp: datetime

    status: str
    side: str

    quantity: int
    price: int

    remaining_qty: Optional[int] = None
    original_order_id: Optional[str] = None

    source_timestamp: Optional[datetime] = None
    received_timestamp: Optional[datetime] = None


# ============================================================
# Fill Event
# ============================================================

@dataclass
class FillEvent:
    """
    실제 체결 이벤트.

    Position은 실제 FillEvent 이후에만 갱신한다.
    """

    order_id: str
    code: str
    timestamp: datetime

    side: str

    fill_price: int
    fill_qty: int
    remaining_qty: int

    # Kiwoom 00 FID 909
    # 실제 체결을 식별하기 위한 체결번호.
    execution_no: Optional[str] = None

    source_timestamp: Optional[datetime] = None
    received_timestamp: Optional[datetime] = None


# ============================================================
# Balance Event
# ============================================================

@dataclass
class BalanceEvent:
    """
    계좌 종목별 잔고 이벤트.
    """

    code: str
    timestamp: datetime

    quantity: int
    average_price: float
    available_quantity: int

    source_timestamp: Optional[datetime] = None
    received_timestamp: Optional[datetime] = None


# ============================================================
# Market Event
# ============================================================

@dataclass
class MarketEvent:
    """
    장 운영 상태 이벤트.

    market_operation_code는 Kiwoom FID 215 원본값을 보존한다.
    market_status는 우리가 이해할 수 있는 문자열로 정규화한다.

    공식 문서에 의미가 명확하지 않은 코드는 임의로 추정하지 않는다.
    """

    timestamp: datetime

    market_status: str

    # Kiwoom FID 215 원본 코드
    market_operation_code: Optional[str] = None

    # Kiwoom FID 214
    # 장시작예상잔여시간 원본 HHMMSS 문자열
    remaining_time: Optional[str] = None

    source_timestamp: Optional[datetime] = None
    received_timestamp: Optional[datetime] = None

# ============================================================
# VI Event
# ============================================================

@dataclass
class VIEvent:
    """
    VI 발동 / 해제 이벤트.

    Kiwoom 1h 실시간 데이터를 정규화한다.

    VI 관련 상태코드는 의미를 임의로 해석하지 않고
    원본 문자열을 최대한 보존한다.
    """

    code: str
    timestamp: datetime

    # FID 9068
    vi_status: str

    # FID 1221
    trigger_price: Optional[int] = None

    # 기존 Interface 호환용
    release_status: Optional[str] = None

    # FID 1224
    release_time: Optional[str] = None

    # FID 1225
    application_type: Optional[str] = None

    # FID 1236
    static_reference_price: Optional[int] = None

    # FID 1237
    dynamic_reference_price: Optional[int] = None

    # FID 1238
    static_deviation_pct: Optional[float] = None

    # FID 1239
    dynamic_deviation_pct: Optional[float] = None

    # FID 1489
    trigger_change_pct: Optional[float] = None

    # FID 9069
    trigger_direction: Optional[str] = None

    # FID 1490
    trigger_count: Optional[int] = None

    # FID 9008
    market_scope: Optional[str] = None

    # FID 9075
    pre_market_type: Optional[str] = None

    # FID 1223
    execution_time: Optional[str] = None

    source_timestamp: Optional[datetime] = None
    received_timestamp: Optional[datetime] = None

# ============================================================
# Stock Information Event
# ============================================================

@dataclass
class StockInfoEvent:
    """
    Kiwoom 0g 주식종목정보 이벤트.

    공식 0g 원본 정보를 최대한 그대로 보존한다.

    주의:
    margin_display / stock_info의 세부 의미를
    확인하기 전까지 관리종목/투자경고 등의
    판정에 직접 사용하지 않는다.
    """

    code: str
    timestamp: datetime

    # FID 297
    arbitrary_extension: Optional[str] = None

    # FID 592 / 593
    pre_open_arbitrary_extension: Optional[str] = None
    post_close_arbitrary_extension: Optional[str] = None

    # FID 305 / 306 / 307
    upper_limit_price: Optional[int] = None
    lower_limit_price: Optional[int] = None
    base_price: Optional[int] = None

    # FID 689
    early_elw_event: Optional[str] = None

    # FID 594
    currency_unit: Optional[str] = None

    # FID 382 원본
    margin_display: Optional[str] = None

    # 382가 숫자/퍼센트 형식이면 파싱한 값.
    # 의미가 불명확하면 None 유지.
    margin_rate: Optional[float] = None

    # FID 370 원본
    stock_info: Optional[str] = None

    source_timestamp: Optional[datetime] = None
    received_timestamp: Optional[datetime] = None

# ============================================================
# Unified Event
# ============================================================

KiwoomEvent = Union[
    TradeEvent,
    OrderbookEvent,
    OrderEvent,
    FillEvent,
    BalanceEvent,
    MarketEvent,
    VIEvent,
    StockInfoEvent,
]
