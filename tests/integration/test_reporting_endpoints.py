from fastapi.testclient import TestClient

from src.api.main import app


def test_mar_report_endpoint() -> None:
    client = TestClient(app)
    create = client.post(
        "/cases",
        json={
            "alert_id": "a-mar-1",
            "account_id": "acct-mar",
            "symbol": "AAPL",
            "severity": "high",
            "summary": "Possible manipulation",
        },
    )
    assert create.status_code == 200
    case_id = create.json()["id"]

    mar = client.get(f"/reports/mar/{case_id}")
    assert mar.status_code == 200
    assert "<MARReport" in mar.text
