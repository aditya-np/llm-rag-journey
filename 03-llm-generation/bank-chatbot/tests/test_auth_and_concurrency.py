from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


def test_auth_resolves_demo_token_to_profile():
    settings = Settings()
    assert settings.demo_tokens["demo-token-alex"] == "CUST-1001"
    assert settings.demo_tokens["demo-token-customer-1052"] == "CUST-1052"


def test_concurrent_customer_reads_do_not_cross_profiles(monkeypatch, tmp_path):
    import importlib
    main_module = importlib.import_module("app.main")

    async def skip_warmup(_settings):
        return True

    monkeypatch.setattr(main_module, "warm_up_model", skip_warmup)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'concurrent.sqlite3'}")
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            directory = client.get("/v1/auth/demo-profiles", headers={"Authorization": "Bearer demo-token-alex"})
            assert directory.status_code == 200
            assert len(directory.json()) == 52
            assert all(set(profile) == {"id", "name"} for profile in directory.json())

            def fetch(number):
                token = f"demo-token-customer-{number}"
                response = client.get("/v1/accounts", headers={"Authorization": f"Bearer {token}"})
                assert response.status_code == 200
                return number, response.json()

            with ThreadPoolExecutor(max_workers=12) as pool:
                rows = list(pool.map(fetch, range(1003, 1053)))
            for number, accounts in rows:
                assert len(accounts) == 1
                assert accounts[0]["customer_id"] == f"CUST-{number}"
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def test_missing_token_is_rejected(monkeypatch, tmp_path):
    import importlib
    main_module = importlib.import_module("app.main")

    async def skip_warmup(_settings):
        return True

    monkeypatch.setattr(main_module, "warm_up_model", skip_warmup)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'unauthenticated.sqlite3'}")
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.get("/v1/accounts")
        assert response.status_code == 401
    finally:
        get_settings.cache_clear()
