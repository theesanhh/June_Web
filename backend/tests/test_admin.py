import time
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.auth import COOKIE_NAME, session_digest, set_admin_password
from backend.database import ROOT, open_database
from backend.main import create_app

PASSWORD = 'test-password-only'
BASE_URL = 'http://127.0.0.1:8000'
SESSION = '/api/admin/session'


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db = tmp_path / 'june.sqlite3'
    monkeypatch.setenv('JUNE_DB_PATH', str(db))
    config = Config(str(ROOT / 'backend' / 'alembic.ini'))
    command.upgrade(config, '0001_shop_settings')
    command.upgrade(config, 'head')
    with TestClient(create_app(db_path=db), base_url=BASE_URL) as session_client:
        yield session_client


def test_unconfigured_admin_and_invalid_origin(client: TestClient):
    assert client.get(SESSION).json() == {'configured': False, 'authenticated': False}
    assert client.post(SESSION, json={'password': PASSWORD}).status_code == 409
    assert client.post(SESSION, json={'password': PASSWORD}, headers={'Origin': 'https://other.example'}).status_code == 403
    assert client.get(SESSION, headers={'Host': 'other.example'}).status_code == 403


def test_login_logout_and_expiry(client: TestClient):
    engine = client.app.state.engine
    set_admin_password(engine, PASSWORD)
    with engine.connect() as conn:
        stored_hash = conn.execute(text('SELECT password_hash FROM admin_account')).scalar_one()
        assert PASSWORD not in stored_hash
    assert client.post(SESSION, json={'password': 'incorrect-password'}).status_code == 401

    response = client.post(SESSION, json={'password': PASSWORD}, headers={'Origin': BASE_URL})
    assert response.status_code == 200
    cookie = response.headers['set-cookie']
    assert 'httponly' in cookie.lower()
    assert 'samesite=strict' in cookie.lower()
    assert response.headers['cache-control'] == 'no-store'
    assert client.get(SESSION).json() == {'configured': True, 'authenticated': True}
    token = client.cookies.get(COOKIE_NAME)
    assert token is not None
    with engine.connect() as conn:
        assert conn.execute(text('SELECT token_hash FROM admin_sessions')).scalar_one() == session_digest(token)

    assert client.delete(SESSION, headers={'Origin': BASE_URL}).status_code == 204
    assert client.cookies.get(COOKIE_NAME) is None
    assert not client.get(SESSION, headers={'Cookie': f'{COOKIE_NAME}={token}'}).json()['authenticated']

    assert client.post(SESSION, json={'password': PASSWORD}).status_code == 200
    with engine.begin() as conn:
        conn.execute(text('UPDATE admin_sessions SET expires_at = :expiry'), {'expiry': int(time.time()) - 1})
    assert not client.get(SESSION).json()['authenticated']


def test_setting_new_password_revokes_active_sessions(client: TestClient):
    engine = client.app.state.engine
    new_password = 'á🙂' * 48
    set_admin_password(engine, PASSWORD)
    assert client.post(SESSION, json={'password': PASSWORD}).status_code == 200
    set_admin_password(engine, new_password)
    assert not client.get(SESSION).json()['authenticated']
    assert client.post(SESSION, json={'password': PASSWORD}).status_code == 401
    assert client.post(SESSION, json={'password': new_password}).status_code == 200


def test_session_reports_unmigrated_database(tmp_path: Path):
    db = tmp_path / 'unmigrated.sqlite3'
    engine = open_database(db)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    engine.dispose()
    with TestClient(create_app(db_path=db), base_url=BASE_URL) as client:
        assert client.get(SESSION).status_code == 503
