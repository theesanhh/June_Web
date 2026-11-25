from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from backend.database import ROOT
from backend.main import create_app


def test_health_reads_migrated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db = tmp_path / 'db' / 'june.sqlite3'
    monkeypatch.setenv('JUNE_DB_PATH', str(db))
    config = Config(str(ROOT / 'backend' / 'alembic.ini'))
    command.upgrade(config, 'head')
    command.upgrade(config, 'head')
    with TestClient(create_app(db_path=db)) as client:
        response = client.get('/api/health')
        assert response.status_code == 200
        assert response.json() == {'status': 'ok', 'database': 'ready', 'shop_name': 'June'}


def test_health_reports_missing_database_without_creating_it(tmp_path: Path):
    db = tmp_path / 'missing.sqlite3'
    with TestClient(create_app(db_path=db)) as client:
        assert client.get('/api/health').status_code == 503
    assert not db.exists()


def test_frontend_is_served_with_api_route(tmp_path: Path):
    dist = tmp_path / 'dist'
    dist.mkdir()
    (dist / 'index.html').write_text('<title>June OMS</title>', encoding='utf-8')
    with TestClient(create_app(db_path=tmp_path / 'missing.sqlite3', dist_dir=dist)) as client:
        assert '<title>June OMS</title>' in client.get('/').text
        assert client.get('/api/health').status_code == 503
