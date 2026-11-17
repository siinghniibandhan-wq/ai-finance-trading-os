"""Order Flow snapshot must remain behind the existing bearer-session auth."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.auth import get_current_user
from app.routes.order_flow import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_order_flow_snapshot_rejects_anonymous_requests():
    response = client.get("/api/order-flow/snapshot?symbol=NIFTY")

    assert response.status_code == 401
