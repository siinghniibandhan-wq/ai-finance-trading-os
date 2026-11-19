from app.routes.market_overview import router


def test_market_overview_http_endpoint_remains_registered():
    """The Market Overview function must remain reachable by its existing API path."""
    matching_routes = [
        route
        for route in router.routes
        if getattr(route, "path", None) == "/"
        and "GET" in getattr(route, "methods", set())
    ]

    assert len(matching_routes) == 1
