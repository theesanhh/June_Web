import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL

ROOT = Path(__file__).resolve().parents[1]


def database_path() -> Path:
    return Path(os.environ.get('JUNE_DB_PATH', ROOT / 'data' / 'june.sqlite3')).resolve()


def open_database(path: Path) -> Engine:
    return create_engine(URL.create('sqlite', database=str(path)), hide_parameters=True)
