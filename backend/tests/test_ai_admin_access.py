from fastapi.routing import APIRoute

from app.routes.ai_assistant import router
from app.routes.auth import get_current_admin, get_current_user


def test_all_ai_endpoints_require_a_signed_in_user_not_only_the_admin():
    """The AI module is open to every signed-in customer (login still required)."""
    ai_routes = [route for route in router.routes if isinstance(route, APIRoute)]
    assert {route.path for route in ai_routes} == {
        "/api/ai/status",
        "/api/ai/providers",
        "/api/ai/chat",
        "/api/ai/models",
    }
    for route in ai_routes:
        dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
        assert get_current_user in dependency_calls, f"{route.path} is missing sign-in protection"
        assert get_current_admin not in dependency_calls, f"{route.path} should not be admin-only"
