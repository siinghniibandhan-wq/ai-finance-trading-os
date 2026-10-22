from fastapi.routing import APIRoute

from app.routes.ai_assistant import router
from app.routes.auth import get_current_admin


def test_all_ai_endpoints_require_server_verified_admin():
    ai_routes = [route for route in router.routes if isinstance(route, APIRoute)]
    assert {route.path for route in ai_routes} == {
        "/api/ai/status",
        "/api/ai/providers",
        "/api/ai/chat",
    }
    for route in ai_routes:
        dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
        assert get_current_admin in dependency_calls, f"{route.path} is missing admin authorization"
