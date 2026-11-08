from security import expand_loopback_origins


def test_development_allows_127_and_localhost(monkeypatch):
    monkeypatch.setattr("security.IS_PRODUCTION", False)
    origins = expand_loopback_origins(["http://localhost:5173"])
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:5173" in origins


def test_production_does_not_add_loopback_twins(monkeypatch):
    monkeypatch.setattr("security.IS_PRODUCTION", True)
    origins = expand_loopback_origins(["https://jyotish-ai-zeta.vercel.app"])
    assert origins == ["https://jyotish-ai-zeta.vercel.app"]
