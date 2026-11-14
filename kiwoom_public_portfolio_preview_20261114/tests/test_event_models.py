from datetime import datetime

from modules.event_models import (
    TradeEvent,
    OrderbookEvent,
    FillEvent,
    MarketEvent,
    VIEvent,
)


def main() -> None:
    now = datetime.now()

    trade = TradeEvent(
        code="005930",
        timestamp=now,
        price=75000,
        change=500,
        change_pct=0.67,
        volume=100,
        cum_volume=12345678,
        cum_turnover=925925850000,
	trade_turnover=7500000,
        execution_strength=121.5,
        best_ask=75100,
        best_bid=75000,
        received_timestamp=now,
    )

    orderbook = OrderbookEvent(
        code="005930",
        timestamp=now,
        ask_prices=[
            75100,
            75200,
            75300,
            75400,
            75500,
            75600,
            75700,
            75800,
            75900,
            76000,
        ],
        bid_prices=[
            75000,
            74900,
            74800,
            74700,
            74600,
            74500,
            74400,
            74300,
            74200,
            74100,
        ],
        ask_qty=[
            100,
            110,
            120,
            130,
            140,
            150,
            160,
            170,
            180,
            190,
        ],
        bid_qty=[
            200,
            210,
            220,
            230,
            240,
            250,
            260,
            270,
            280,
            290,
        ],
        total_ask_qty=1450,
        total_bid_qty=2450,
        received_timestamp=now,
    )

    fill = FillEvent(
        order_id="TEST_ORDER_001",
        code="005930",
        timestamp=now,
        side="BUY",
        fill_price=75000,
        fill_qty=3,
        remaining_qty=2,
        received_timestamp=now,
    )

    market = MarketEvent(
        timestamp=now,
        market_status="OPEN",
        received_timestamp=now,
    )

    vi = VIEvent(
        code="005930",
        timestamp=now,
        vi_status="TRIGGERED",
        trigger_price=78000,
        trigger_direction="UP",
        trigger_count=1,
        received_timestamp=now,
    )

    print("=" * 60)
    print("Event Model Test")
    print("=" * 60)

    print(
        "[TradeEvent]",
        trade.code,
        trade.price,
        trade.execution_strength,
    )

    print(
        "[OrderbookEvent]",
        "best_ask=",
        orderbook.best_ask,
        "best_bid=",
        orderbook.best_bid,
    )

    print(
        "[OrderbookEvent]",
        "top5_ask_qty=",
        orderbook.top5_ask_qty,
        "top5_bid_qty=",
        orderbook.top5_bid_qty,
    )

    print(
        "[OrderbookEvent]",
        "bid_ask_depth_ratio=",
        round(orderbook.bid_ask_depth_ratio or 0.0, 4),
    )

    print(
        "[FillEvent]",
        fill.side,
        fill.fill_price,
        fill.fill_qty,
        fill.remaining_qty,
    )

    print(
        "[MarketEvent]",
        market.market_status,
    )

    print(
        "[VIEvent]",
        vi.vi_status,
        vi.trigger_price,
        vi.trigger_direction,
    )

    print("[RESULT] Event Model 정상")


if __name__ == "__main__":
    main()
