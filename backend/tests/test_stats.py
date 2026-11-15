from tests.conftest import login


def test_requires_login(client):
    assert client.get("/api/stats").status_code == 401


def test_stats_empty(client):
    login(client)
    assert client.get("/api/stats").json() == {"totalRecipients": 0, "sent": 0, "pending": 0, "failed": 0, "gmailConnected": False, "gmailEmail": None}
