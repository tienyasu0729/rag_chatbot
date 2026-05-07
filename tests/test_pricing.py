from app.services import pricing


def test_get_market_data_uses_priority_window_function(monkeypatch):
    calls = []

    def fake_query(sql, params=None, timeout=None):
        calls.append((sql, params))
        if "COUNT(*) AS comparable_count" in sql:
            return [
                {
                    "comparable_count": 3,
                    "market_min": 100000000,
                    "market_avg": 120000000,
                    "market_max": 140000000,
                }
            ]
        return [
            {
                "id": 1,
                "title": "Toyota Vios",
                "price": 120000000,
                "year": 2020,
                "fuel": "Gasoline",
                "transmission": "AT",
                "origin": "Vietnam",
                "status": "Available",
                "created_at": None,
                "priority_match": 2,
            }
        ]

    monkeypatch.setattr(pricing.sqlserver, "query_positional_readonly", fake_query)

    result = pricing._get_market_data(
        subcategory_name="Toyota Vios",
        year=2020,
        fuel="Gasoline",
        transmission="AT",
        origin="Vietnam",
    )

    assert result["comparable_count"] == 3
    assert result["market_avg"] == 120000000
    assert result["comparables"][0]["priority_match"] == 2
    assert "ROW_NUMBER() OVER (PARTITION BY id ORDER BY priority_match)" in calls[0][0]
    assert "ORDER BY priority_match ASC, created_at DESC" in calls[1][0]


def test_estimate_purchase_price_falls_back_when_llm_fails(monkeypatch):
    monkeypatch.setattr(pricing, "json_completion", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("llm fail")))

    result = pricing.estimate_purchase_price(
        market_data={
            "market_avg": 200000000,
            "market_min": 180000000,
            "market_max": 220000000,
            "comparable_count": 5,
            "comparables": [],
        },
        vehicle_assessment={
            "condition_score": 60,
            "damage_summary": "Mac dinh",
            "risk_flags": ["flag"],
        },
        vehicle_config={"subcategory_name": "Test"},
    )

    assert result["suggested_purchase_price"] == 102000000
    assert result["price_range_min"] == 96900000
    assert result["price_range_max"] == 107100000
